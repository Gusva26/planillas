"""Servicio de gestión y ciclo de vida de planillas CAFAE.

Cubre:
- Creación desde maestro (solo activos, descuentos iniciales en cero).
- Copia desde mes inmediatamente anterior (mismo tipo, copia histórica fiel).
- Edición mensual por lote con control de revisión y concurrencia.
- Limpieza completa de descuentos (mantiene importes base).
- Revisión de consistencia y alertas de neto negativo.
- Cierre transaccional seguro (solo administrador, bloqueo FOR UPDATE).
- Reapertura versionada (nueva versión editable, cierre previo inmutable).
- Consulta de historial de versiones y detalle de personal.
"""
from decimal import Decimal
from psycopg.errors import SerializationFailure, UniqueViolation

from cafae.auth import AuthService
from cafae.calculos import CONCEPTOS_DESCUENTO, a_decimal, calcular_liquidacion_trabajador
from cafae.security import AccessError, UserError

VERSION_CALCULO = 'decimal-half-up-v1'


class PlanillaService:
    def __init__(self, auth_service=None):
        self.auth = auth_service or AuthService()

    # =========================================================================
    # A. PERIODOS Y PLANILLAS LÓGICAS
    # =========================================================================
    def obtener_o_crear_periodo(self, conn, anio: int, mes: int) -> int:
        anio, mes = int(anio), int(mes)
        if not (1900 <= anio <= 9999 and 1 <= mes <= 12):
            raise UserError('Año o mes inválido.')
        existente = conn.execute(
            'SELECT id FROM periodos WHERE anio = %s AND mes = %s',
            (anio, mes)
        ).fetchone()
        if existente:
            return existente['id']
        row = conn.execute(
            '''INSERT INTO periodos(anio, mes)
               VALUES (%s, %s)
               ON CONFLICT (anio, mes) DO NOTHING
               RETURNING id''',
            (anio, mes)
        ).fetchone()
        if row:
            return row['id']
        return conn.execute(
            'SELECT id FROM periodos WHERE anio = %s AND mes = %s',
            (anio, mes)
        ).fetchone()['id']

    def list_planillas(self, token, anio=None, mes=None, tipo=None):
        """Lista las planillas con el estado y totales de su última versión."""
        sql = '''SELECT p.id, p.tipo, p.cantidad_firmas, p.creada_en,
                        per.anio, per.mes,
                        pv.id AS version_id, pv.numero AS version_numero,
                        pv.estado AS version_estado, pv.origen AS version_origen,
                        pv.revision_edicion,
                        pv.total_trabajadores, pv.total_importe, pv.total_descuentos, pv.total_neto,
                        pv.cerrada_en, u_cerr.nombre_completo AS cerrada_por_nombre,
                        u_crea.nombre_completo AS creada_por_nombre
                 FROM planillas p
                 JOIN periodos per ON per.id = p.periodo_id
                 JOIN planilla_versiones pv ON pv.id = (
                     SELECT id FROM planilla_versiones WHERE planilla_id = p.id ORDER BY numero DESC LIMIT 1
                 )
                 JOIN usuarios u_crea ON u_crea.id = p.creada_por
                 LEFT JOIN usuarios u_cerr ON u_cerr.id = pv.cerrada_por
                 WHERE 1=1'''
        params = []
        if anio:
            sql += ' AND per.anio = %s'
            params.append(int(anio))
        if mes:
            sql += ' AND per.mes = %s'
            params.append(int(mes))
        if tipo:
            if tipo not in ('IIEE', 'SEDE'):
                raise UserError('Tipo de planilla inválido.')
            sql += ' AND p.tipo = %s'
            params.append(tipo)

        sql += ' ORDER BY per.anio DESC, per.mes DESC, p.tipo ASC'
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, params).fetchall()

    def get_planilla_version(self, token, planilla_id, version_numero=None):
        """Retorna los datos de una versión específica o la última si no se indica número."""
        sql = '''SELECT pv.*, p.tipo, p.cantidad_firmas, per.anio, per.mes
                 FROM planilla_versiones pv
                 JOIN planillas p ON p.id = pv.planilla_id
                 JOIN periodos per ON per.id = p.periodo_id
                 WHERE pv.planilla_id = %s'''
        params = [int(planilla_id)]
        if version_numero:
            sql += ' AND pv.numero = %s'
            params.append(int(version_numero))
        else:
            sql += ' ORDER BY pv.numero DESC LIMIT 1'

        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, params).fetchone()

    def list_versiones_planilla(self, token, planilla_id):
        """Lista todas las versiones de una planilla lógica para ver su historial."""
        sql = '''SELECT pv.*, u.nombre_completo AS creada_por_nombre,
                        uc.nombre_completo AS cerrada_por_nombre
                 FROM planilla_versiones pv
                 JOIN usuarios u ON u.id = pv.creada_por
                 LEFT JOIN usuarios uc ON uc.id = pv.cerrada_por
                 WHERE pv.planilla_id = %s
                 ORDER BY pv.numero ASC'''
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, (int(planilla_id),)).fetchall()

    # =========================================================================
    # B. CREACIÓN DE PLANILLAS (MAESTRO Y COPIA)
    # =========================================================================
    def crear_desde_maestro(self, token, anio: int, mes: int, tipo: str) -> dict:
        anio, mes = int(anio), int(mes)
        if tipo not in ('IIEE', 'SEDE'):
            raise UserError('Tipo de planilla inválido (debe ser IIEE o SEDE).')

        try:
            with self.auth.data_transaction(token, 'editar_planillas') as (conn, user):
                # 1. Periodo y Planilla lógica
                periodo_id = self.obtener_o_crear_periodo(conn, anio, mes)
                if conn.execute('SELECT 1 FROM planillas WHERE periodo_id = %s AND tipo = %s', (periodo_id, tipo)).fetchone():
                    raise UserError(f'Ya existe una planilla de {tipo} registrada para el periodo {anio}-{mes:02d}.')

                p_row = conn.execute(
                    'INSERT INTO planillas(periodo_id, tipo, creada_por) VALUES (%s, %s, %s) RETURNING id',
                    (periodo_id, tipo, user['id'])
                ).fetchone()
                planilla_id = p_row['id']

                # 2. Versión 1 en estado BORRADOR
                v_row = conn.execute(
                    '''INSERT INTO planilla_versiones(planilla_id, numero, estado, origen, version_calculo, creada_por)
                       VALUES (%s, 1, 'BORRADOR', 'MAESTRO', %s, %s) RETURNING id, revision_edicion''',
                    (planilla_id, VERSION_CALCULO, user['id'])
                ).fetchone()
                version_id = v_row['id']

                # 3. Copiar programas activos a planilla_programas (copia histórica)
                conn.execute(
                    '''INSERT INTO planilla_programas(version_id, programa_id, padre_id, codigo, nombre, orden)
                       SELECT %s, id, padre_id, codigo, nombre, orden
                       FROM programas WHERE activo = true
                       ORDER BY orden ASC''',
                    (version_id,)
                )

                # 4. Copiar firmas vigentes a planilla_firmas
                max_firmas = 4 if tipo == 'IIEE' else 3
                conn.execute(
                    '''INSERT INTO planilla_firmas(version_id, posicion, firma_id, nombre_completo, cargo)
                       SELECT %s, row_number() OVER (ORDER BY id ASC), id, nombre_completo, cargo
                       FROM firmas WHERE activo = true
                       ORDER BY id ASC LIMIT %s''',
                    (version_id, max_firmas)
                )

                # 5. Obtener trabajadores activos del tipo correspondiente y copiar a planilla_detalle
                # Solo personal activo en el maestro
                trabajadores = conn.execute(
                    '''SELECT t.*,
                              i.nombre AS inst_nombre, i.codigo_modular AS inst_mod, i.distrito AS inst_dist,
                              a.nombre AS ar_nombre,
                              n.nombre AS niv_nombre,
                              COALESCE(i.meta_id, a.meta_id, nm.meta_id) AS meta_resuelta_id,
                              m.codigo AS m_cod, m.descripcion AS m_desc,
                              pp.codigo AS p_partida_cod,
                              c.nombre AS car_nombre,
                              cat.codigo AS cat_cod, cat.descripcion AS cat_desc,
                              s.nombre AS sit_nombre,
                              sub.nombre AS sub_nombre
                       FROM trabajadores t
                       LEFT JOIN instituciones i ON i.id = t.institucion_id
                       LEFT JOIN areas_sede a ON a.id = t.area_id
                       LEFT JOIN niveles n ON n.id = t.nivel_id
                       LEFT JOIN nivel_metas nm ON nm.nivel_id = t.nivel_id
                       LEFT JOIN metas m ON m.id = COALESCE(i.meta_id, a.meta_id, nm.meta_id)
                       LEFT JOIN partidas_presupuestarias pp ON pp.id = m.partida_id
                       LEFT JOIN cargos c ON c.id = t.cargo_id
                       LEFT JOIN categorias cat ON cat.id = t.categoria_id
                       LEFT JOIN situaciones s ON s.id = t.situacion_id
                       LEFT JOIN subtipos_trabajador sub ON sub.id = t.subtipo_id
                       WHERE t.tipo = %s AND t.activo = true
                       ORDER BY t.apellidos ASC, t.nombres ASC''',
                    (tipo,)
                ).fetchall()

                orden = 1
                for t in trabajadores:
                    # Snapshot en planilla_detalle (dias_licencia=0, neto=importe inicial)
                    d_row = conn.execute(
                        '''INSERT INTO planilla_detalle(
                               version_id, trabajador_id, orden, dni, apellidos, nombres,
                               institucion_id, institucion_nombre, codigo_modular, distrito,
                               area_id, area_nombre, nivel_id, nivel_nombre,
                               meta_id, meta_codigo, meta_descripcion, partida_codigo,
                               subtipo, cargo, situacion, categoria, categoria_descripcion,
                               fecha_nacimiento, ley, regimen_laboral, jornada_laboral,
                               cuenta_multired, importe, dias_licencia, monto_licencia,
                               total_descuentos, neto,
                               regimen_pensionario, fecha_ingreso, fecha_termino,
                               tiempo_servicio_texto, leyenda_permanente, tipo_pago, numero_cheque
                           ) VALUES (
                               %s, %s, %s, %s, %s, %s,
                               %s, %s, %s, %s,
                               %s, %s, %s, %s,
                               %s, %s, %s, %s,
                               %s, %s, %s, %s, %s,
                               %s, %s, %s, %s,
                               %s, %s, 0, 0,
                               0, %s,
                               %s, %s, %s,
                               %s, %s, %s, %s
                           ) RETURNING id''',
                        (
                            version_id, t['id'], orden, t['dni'], t['apellidos'], t['nombres'],
                            t['institucion_id'], t['inst_nombre'], t['inst_mod'], t['inst_dist'],
                            t['area_id'], t['ar_nombre'], t['nivel_id'], t['niv_nombre'],
                            t['meta_resuelta_id'], t['m_cod'], t['m_desc'], t['p_partida_cod'],
                            t['sub_nombre'], t['car_nombre'], t['sit_nombre'], t['cat_cod'], t['cat_desc'],
                            t['fecha_nacimiento'], t['ley'], t['regimen_laboral'], t['jornada_laboral'],
                            t['cuenta_multired'], t['importe'], t['importe'],
                            t['regimen_pensionario'], t['fecha_ingreso'], t['fecha_termino'],
                            t['tiempo_servicio_texto'], t['leyenda_permanente'], t['tipo_pago'], t['numero_cheque']
                        )
                    ).fetchone()
                    detalle_id = d_row['id']

                    # Insertar los 7 conceptos en 0.00
                    conn.execute(
                        '''INSERT INTO planilla_descuentos(detalle_id, tipo_descuento_id, monto, actualizado_por)
                           SELECT %s, id, 0.00, %s FROM tipos_descuento''',
                        (detalle_id, user['id'])
                    )
                    orden += 1

                return {
                    'planilla_id': planilla_id,
                    'version_id': version_id,
                    'trabajadores_copiados': len(trabajadores)
                }
        except UniqueViolation:
            raise UserError(f'Ya existe una planilla de {tipo} registrada para el periodo {anio}-{mes:02d}.')

    def copiar_mes_anterior(self, token, anio: int, mes: int, tipo: str, version_fuente_id=None) -> dict:
        anio, mes = int(anio), int(mes)
        if tipo not in ('IIEE', 'SEDE'):
            raise UserError('Tipo de planilla inválido.')

        # Calcular mes inmediatamente anterior (incluye cruce Dic -> Ene)
        if mes == 1:
            ant_anio, ant_mes = anio - 1, 12
        else:
            ant_anio, ant_mes = anio, mes - 1

        with self.auth.data_transaction(token, 'editar_planillas') as (conn, user):
            # 1. Buscar periodo y planilla anterior
            if not version_fuente_id:
                ant_p = conn.execute(
                    '''SELECT pv.id AS version_id, pv.estado
                       FROM planillas p
                       JOIN periodos per ON per.id = p.periodo_id
                       JOIN planilla_versiones pv ON pv.planilla_id = p.id
                       WHERE per.anio = %s AND per.mes = %s AND p.tipo = %s
                       ORDER BY pv.numero DESC LIMIT 1''',
                    (ant_anio, ant_mes, tipo)
                ).fetchone()
                if not ant_p:
                    raise UserError(
                        f'No se encontró una planilla previa de {tipo} en el mes anterior ({ant_anio}-{ant_mes:02d}) para copiar.'
                    )
                version_fuente_id = ant_p['version_id']
            else:
                version_fuente_id = int(version_fuente_id)

            # Verificar que no exista planilla en el periodo destino
            periodo_id = self.obtener_o_crear_periodo(conn, anio, mes)
            if conn.execute('SELECT 1 FROM planillas WHERE periodo_id = %s AND tipo = %s', (periodo_id, tipo)).fetchone():
                raise UserError(f'Ya existe una planilla de {tipo} registrada para el periodo {anio}-{mes:02d}.')

            # Crear planilla lógica
            p_row = conn.execute(
                'INSERT INTO planillas(periodo_id, tipo, creada_por) VALUES (%s, %s, %s) RETURNING id',
                (periodo_id, tipo, user['id'])
            ).fetchone()
            planilla_id = p_row['id']

            # Crear versión 1 con origen 'COPIA'
            v_row = conn.execute(
                '''INSERT INTO planilla_versiones(
                       planilla_id, numero, estado, origen, fuente_version_id, version_calculo, creada_por
                   ) VALUES (
                       %s, 1, 'BORRADOR', 'COPIA', %s, %s, %s
                   ) RETURNING id''',
                (planilla_id, version_fuente_id, VERSION_CALCULO, user['id'])
            ).fetchone()
            version_id = v_row['id']

            # Copiar programas de la versión fuente
            conn.execute(
                '''INSERT INTO planilla_programas(version_id, programa_id, padre_id, codigo, nombre, orden)
                   SELECT %s, programa_id, padre_id, codigo, nombre, orden
                   FROM planilla_programas WHERE version_id = %s''',
                (version_id, version_fuente_id)
            )

            # Copiar firmas de la versión fuente
            conn.execute(
                '''INSERT INTO planilla_firmas(version_id, posicion, firma_id, nombre_completo, cargo)
                   SELECT %s, posicion, firma_id, nombre_completo, cargo
                   FROM planilla_firmas WHERE version_id = %s''',
                (version_id, version_fuente_id)
            )

            # Copiar planilla_detalle desde la versión fuente
            detalles_fuente = conn.execute(
                '''SELECT * FROM planilla_detalle WHERE version_id = %s ORDER BY orden ASC''',
                (version_fuente_id,)
            ).fetchall()

            for d in detalles_fuente:
                # Copiar detalle: días de licencia en 0, monto_licencia en 0
                d_row = conn.execute(
                    '''INSERT INTO planilla_detalle(
                           version_id, trabajador_id, orden, dni, apellidos, nombres,
                           institucion_id, institucion_nombre, codigo_modular, distrito,
                           area_id, area_nombre, nivel_id, nivel_nombre,
                           meta_id, meta_codigo, meta_descripcion, partida_codigo,
                           subtipo, cargo, situacion, categoria, categoria_descripcion,
                           fecha_nacimiento, ley, regimen_laboral, jornada_laboral,
                           cuenta_multired, importe, dias_licencia, monto_licencia,
                           total_descuentos, neto,
                           regimen_pensionario, fecha_ingreso, fecha_termino,
                           tiempo_servicio_texto, leyenda_permanente, tipo_pago, numero_cheque
                       ) VALUES (
                           %s, %s, %s, %s, %s, %s,
                           %s, %s, %s, %s,
                           %s, %s, %s, %s,
                           %s, %s, %s, %s,
                           %s, %s, %s, %s, %s,
                           %s, %s, %s, %s,
                           %s, %s, 0, 0,
                           0, %s,
                           %s, %s, %s,
                           %s, %s, %s, %s
                       ) RETURNING id''',
                    (
                        version_id, d['trabajador_id'], d['orden'], d['dni'], d['apellidos'], d['nombres'],
                        d['institucion_id'], d['institucion_nombre'], d['codigo_modular'], d['distrito'],
                        d['area_id'], d['area_nombre'], d['nivel_id'], d['nivel_nombre'],
                        d['meta_id'], d['meta_codigo'], d['meta_descripcion'], d['partida_codigo'],
                        d['subtipo'], d['cargo'], d['situacion'], d['categoria'], d['categoria_descripcion'],
                        d['fecha_nacimiento'], d['ley'], d['regimen_laboral'], d['jornada_laboral'],
                        d['cuenta_multired'], d['importe'], d['importe'],
                        d['regimen_pensionario'], d['fecha_ingreso'], d['fecha_termino'],
                        d['tiempo_servicio_texto'], d['leyenda_permanente'], d['tipo_pago'], d['numero_cheque']
                    )
                ).fetchone()
                nuevo_detalle_id = d_row['id']

                # Copiar descuentos del trabajador desde la versión fuente
                conn.execute(
                    '''INSERT INTO planilla_descuentos(detalle_id, tipo_descuento_id, monto, actualizado_por)
                       SELECT %s, tipo_descuento_id, monto, %s
                       FROM planilla_descuentos
                       WHERE detalle_id = %s''',
                    (nuevo_detalle_id, user['id'], d['id'])
                )

            return {
                'planilla_id': planilla_id,
                'version_id': version_id,
                'trabajadores_copiados': len(detalles_fuente)
            }

    # =========================================================================
    # C. CONSULTA DE DETALLE Y FILAS CON DESCUENTOS
    # =========================================================================
    def get_detalle_version(self, token, version_id, institucion_id=None, area_id=None, query=None):
        version_id = int(version_id)
        sql = '''SELECT pd.id, pd.version_id, pd.trabajador_id, pd.orden, pd.dni, pd.apellidos, pd.nombres,
                        pd.institucion_id, pd.institucion_nombre, pd.codigo_modular, pd.distrito,
                        pd.area_id, pd.area_nombre, pd.nivel_id, pd.nivel_nombre,
                        pd.meta_id, pd.meta_codigo, pd.meta_descripcion, pd.partida_codigo,
                        pd.subtipo, pd.cargo, pd.situacion, pd.categoria, pd.categoria_descripcion,
                        COALESCE(pd.fecha_nacimiento, t.fecha_nacimiento) AS fecha_nacimiento,
                        COALESCE(pd.ley, t.ley, '276') AS ley,
                        COALESCE(pd.regimen_laboral, t.regimen_laboral, '276') AS regimen_laboral,
                        COALESCE(pd.jornada_laboral, t.jornada_laboral, '40') AS jornada_laboral,
                        COALESCE(pd.cuenta_multired, t.cuenta_multired) AS cuenta_multired,
                        pd.importe, pd.dias_licencia, pd.monto_licencia, pd.total_descuentos, pd.neto,
                        COALESCE(pd.regimen_pensionario, t.regimen_pensionario) AS regimen_pensionario,
                        COALESCE(pd.fecha_ingreso, t.fecha_ingreso) AS fecha_ingreso,
                        COALESCE(pd.fecha_termino, t.fecha_termino) AS fecha_termino,
                        COALESCE(pd.tiempo_servicio_texto, t.tiempo_servicio_texto) AS tiempo_servicio_texto,
                        COALESCE(pd.leyenda_permanente, t.leyenda_permanente) AS leyenda_permanente,
                        COALESCE(pd.tipo_pago, t.tipo_pago, 'CUENTA') AS tipo_pago,
                        COALESCE(pd.numero_cheque, t.numero_cheque) AS numero_cheque,
                        COALESCE(pich.monto, 0.00) AS pichincha,
                        COALESCE(sull.monto, 0.00) AS caja_sullana,
                        COALESCE(subc.monto, 0.00) AS sub_cafae,
                        COALESCE(bren.monto, 0.00) AS brenta,
                        COALESCE(sitr.monto, 0.00) AS sitrase,
                        COALESCE(fent.monto, 0.00) AS sitase_fentase,
                        COALESCE(otro.monto, 0.00) AS otros
                 FROM planilla_detalle pd
                 LEFT JOIN trabajadores t ON t.id = pd.trabajador_id
                 LEFT JOIN planilla_descuentos pich ON pich.detalle_id = pd.id AND pich.tipo_descuento_id = 1
                 LEFT JOIN planilla_descuentos sull ON sull.detalle_id = pd.id AND sull.tipo_descuento_id = 2
                 LEFT JOIN planilla_descuentos subc ON subc.detalle_id = pd.id AND subc.tipo_descuento_id = 3
                 LEFT JOIN planilla_descuentos bren ON bren.detalle_id = pd.id AND bren.tipo_descuento_id = 4
                 LEFT JOIN planilla_descuentos sitr ON sitr.detalle_id = pd.id AND sitr.tipo_descuento_id = 5
                 LEFT JOIN planilla_descuentos fent ON fent.detalle_id = pd.id AND fent.tipo_descuento_id = 6
                 LEFT JOIN planilla_descuentos otro ON otro.detalle_id = pd.id AND otro.tipo_descuento_id = 7
                 WHERE pd.version_id = %s'''
        params = [version_id]
        if institucion_id:
            sql += ' AND pd.institucion_id = %s'
            params.append(int(institucion_id))
        if area_id:
            sql += ' AND pd.area_id = %s'
            params.append(int(area_id))
        if query and query.strip():
            clean_q = f'%{query.strip()}%'
            sql += ' AND (pd.dni ILIKE %s OR pd.apellidos ILIKE %s OR pd.nombres ILIKE %s)'
            params.extend([clean_q, clean_q, clean_q])

        sql += ' ORDER BY pd.orden ASC'
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, params).fetchall()

    list_lineas_edicion = get_detalle_version

    # =========================================================================
    # D. EDICIÓN POR LOTE Y LIMPIEZA
    # =========================================================================
    def guardar_edicion_lote(self, token, version_id, revision_esperada: int, cambios: list[dict]):
        version_id = int(version_id)
        revision_esperada = int(revision_esperada)

        with self.auth.data_transaction(token, 'editar_planillas') as (conn, user):
            # 1. Bloquear y verificar revisión de concurrencia
            conn.execute('SELECT bloquear_edicion(%s, %s)', (version_id, revision_esperada))

            # Mapeo de tipos de descuento a IDs
            tipos = {r['codigo']: r['id'] for r in conn.execute('SELECT id, codigo FROM tipos_descuento').fetchall()}

            for c in cambios:
                detalle_id = int(c['detalle_id'])
                dias_lic = int(c.get('dias_licencia', 0))
                if not (0 <= dias_lic <= 30):
                    raise UserError('Los días de licencia deben estar entre 0 y 30.')

                imp_val = c.get('importe')
                if imp_val is not None:
                    imp = a_decimal(imp_val, 'Importe')
                    conn.execute(
                        '''UPDATE planilla_detalle
                           SET importe = %s, dias_licencia = %s
                           WHERE id = %s AND version_id = %s''',
                        (imp, dias_lic, detalle_id, version_id)
                    )
                else:
                    conn.execute(
                        '''UPDATE planilla_detalle
                           SET dias_licencia = %s
                           WHERE id = %s AND version_id = %s''',
                        (dias_lic, detalle_id, version_id)
                    )

                # Actualizar los 7 descuentos
                descs_dict = c.get('descuentos', {}) if isinstance(c.get('descuentos'), dict) else {}
                for cod, t_id in tipos.items():
                    raw_desc = c.get(cod) if cod in c else descs_dict.get(cod)
                    if raw_desc is not None:
                        monto = a_decimal(raw_desc, f'Descuento {cod}')
                        if monto < Decimal('0.00'):
                            raise UserError(f'El descuento {cod} no puede ser negativo.')
                        conn.execute(
                            '''UPDATE planilla_descuentos
                               SET monto = %s, actualizado_por = %s
                               WHERE detalle_id = %s AND tipo_descuento_id = %s''',
                            (monto, user['id'], detalle_id, t_id)
                        )

            # Obtener nueva revisión
            nueva_rev = conn.execute(
                'SELECT revision_edicion FROM planilla_versiones WHERE id = %s', (version_id,)
            ).fetchone()['revision_edicion']
            return {'revision_edicion': nueva_rev, 'filas_actualizadas': len(cambios)}

    def limpiar_descuentos(self, token, version_id, revision_esperada: int, concepto_codigo: str = None):
        """Pone a cero los descuentos (específico o todos) y licencias."""
        version_id = int(version_id)
        revision_esperada = int(revision_esperada)

        with self.auth.data_transaction(token, 'editar_planillas') as (conn, user):
            conn.execute('SELECT bloquear_edicion(%s, %s)', (version_id, revision_esperada))

            if concepto_codigo:
                tipo = conn.execute('SELECT id FROM tipos_descuento WHERE codigo = %s', (concepto_codigo,)).fetchone()
                if tipo:
                    conn.execute(
                        '''UPDATE planilla_descuentos SET monto = 0.00, actualizado_por = %s
                           WHERE tipo_descuento_id = %s
                             AND detalle_id IN (SELECT id FROM planilla_detalle WHERE version_id = %s)''',
                        (user['id'], tipo['id'], version_id)
                    )
            else:
                # Días de licencia a cero
                conn.execute(
                    'UPDATE planilla_detalle SET dias_licencia = 0 WHERE version_id = %s',
                    (version_id,)
                )
                # 7 descuentos a cero
                conn.execute(
                    '''UPDATE planilla_descuentos SET monto = 0.00, actualizado_por = %s
                       WHERE detalle_id IN (SELECT id FROM planilla_detalle WHERE version_id = %s)''',
                    (user['id'], version_id)
                )

            nueva_rev = conn.execute(
                'SELECT revision_edicion FROM planilla_versiones WHERE id = %s', (version_id,)
            ).fetchone()['revision_edicion']
            return {'revision_edicion': nueva_rev}

    limpiar_todos_descuentos = limpiar_descuentos

    def cambiar_estado(self, token, version_id, nuevo_estado: str):
        version_id = int(version_id)
        if nuevo_estado not in ('BORRADOR', 'EN_REVISION'):
            raise UserError('Estado no válido para transición de edición.')

        with self.auth.data_transaction(token, 'editar_planillas') as (conn, _):
            res = conn.execute(
                '''UPDATE planilla_versiones
                   SET estado = %s
                   WHERE id = %s AND estado <> 'CERRADA' RETURNING id''',
                (nuevo_estado, version_id)
            ).fetchone()
            if not res:
                raise UserError('No se puede cambiar el estado de una versión cerrada o inexistente.')

    # =========================================================================
    # E. CIERRE TRANSACCIONAL (SOLO ADMINISTRADOR)
    # =========================================================================
    def cerrar_version(self, token, version_id, revision_esperada: int, firmas_ids: list[int]):
        """Cierre formal de planilla con verificación de firmas, netos y revisión."""
        version_id = int(version_id)
        revision_esperada = int(revision_esperada)

        with self.auth.data_transaction(token, 'cerrar_planilla') as (conn, user):
            v_info = conn.execute(
                '''SELECT pv.*, p.tipo, p.cantidad_firmas
                   FROM planilla_versiones pv
                   JOIN planillas p ON p.id = pv.planilla_id
                   WHERE pv.id = %s FOR UPDATE''',
                (version_id,)
            ).fetchone()
            if not v_info:
                raise UserError('Versión de planilla no encontrada.')
            if v_info['estado'] == 'CERRADA':
                raise UserError('La versión de planilla ya se encuentra cerrada.')

            if v_info['revision_edicion'] != revision_esperada:
                raise UserError('La planilla fue modificada por otro usuario. Vuelva a revisar antes de cerrar.')

            # 1. Validar que no existan netos negativos
            negativos = conn.execute(
                '''SELECT count(*) AS total FROM planilla_detalle
                   WHERE version_id = %s AND neto < 0''',
                (version_id,)
            ).fetchone()['total']
            if negativos > 0:
                raise UserError(
                    f'No se puede cerrar la planilla: existen {negativos} trabajador(es) con líquido neto negativo.'
                )

            # 2. Validar cantidad y validez de firmas (4 IIEE, 3 Sede)
            cant_requerida = v_info['cantidad_firmas']
            if len(firmas_ids) != cant_requerida:
                raise UserError(
                    f'La planilla de {v_info["tipo"]} requiere exactamente {cant_requerida} firmas. Se recibieron {len(firmas_ids)}.'
                )

            # Actualizar planilla_firmas con las firmas seleccionadas
            conn.execute('DELETE FROM planilla_firmas WHERE version_id = %s', (version_id,))
            for pos, f_id in enumerate(firmas_ids, start=1):
                f_obj = conn.execute('SELECT nombre_completo, cargo FROM firmas WHERE id = %s', (int(f_id),)).fetchone()
                if not f_obj:
                    raise UserError(f'La firma con ID {f_id} no existe en el catálogo.')
                conn.execute(
                    '''INSERT INTO planilla_firmas(version_id, posicion, firma_id, nombre_completo, cargo)
                       VALUES (%s, %s, %s, %s, %s)''',
                    (version_id, pos, f_id, f_obj['nombre_completo'], f_obj['cargo'])
                )

            # 3. Invocar cafae.cerrar_planilla(...) con la revisión fresca tras asignar firmas
            rev_post_firmas = conn.execute(
                'SELECT revision_edicion FROM planilla_versiones WHERE id = %s', (version_id,)
            ).fetchone()['revision_edicion']

            try:
                conn.execute(
                    'SELECT cerrar_planilla(%s, %s, %s)',
                    (version_id, rev_post_firmas, user['id'])
                )
            except SerializationFailure:
                raise UserError('La planilla fue modificada por otro usuario. Vuelva a revisar antes de cerrar.')

            # Retornar datos consolidados del cierre
            cerrada = conn.execute('SELECT * FROM planilla_versiones WHERE id = %s', (version_id,)).fetchone()
            return {
                'version_id': version_id,
                'total_trabajadores': cerrada['total_trabajadores'],
                'total_importe': cerrada['total_importe'],
                'total_descuentos': cerrada['total_descuentos'],
                'total_neto': cerrada['total_neto'],
                'cerrada_en': cerrada['cerrada_en']
            }

    # =========================================================================
    # F. REAPERTURA DE PLANILLA (SOLO ADMINISTRADOR)
    # =========================================================================
    def reabrir_version(self, token, version_cerrada_id: int, motivo: str) -> dict:
        version_cerrada_id = int(version_cerrada_id)
        motivo = str(motivo).strip() if motivo else ''
        if not motivo or len(motivo) < 5:
            raise UserError('Debe ingresar un motivo justificado para la reapertura (mínimo 5 caracteres).')

        with self.auth.data_transaction(token, 'reabrir_planilla') as (conn, user):
            # Obtener datos de la versión cerrada
            cerrada = conn.execute(
                '''SELECT * FROM planilla_versiones WHERE id = %s FOR UPDATE''',
                (version_cerrada_id,)
            ).fetchone()
            if not cerrada or cerrada['estado'] != 'CERRADA':
                raise UserError('Solo se pueden reabrir versiones formalmente cerradas.')

            planilla_id = cerrada['planilla_id']

            # Verificar que no exista otra versión abierta para esta planilla
            abierta = conn.execute(
                '''SELECT 1 FROM planilla_versiones WHERE planilla_id = %s AND estado <> 'CERRADA' ''',
                (planilla_id,)
            ).fetchone()
            if abierta:
                raise UserError('Ya existe una versión abierta en edición para esta planilla.')

            # Siguiente número de versión
            nuevo_numero = cerrada['numero'] + 1

            # Crear versión nueva en estado BORRADOR con origen REAPERTURA
            v_nueva = conn.execute(
                '''INSERT INTO planilla_versiones(
                       planilla_id, numero, estado, origen, fuente_version_id, motivo_reapertura,
                       version_calculo, creada_por
                   ) VALUES (
                       %s, %s, 'BORRADOR', 'REAPERTURA', %s, %s, %s, %s
                   ) RETURNING id''',
                (planilla_id, nuevo_numero, version_cerrada_id, motivo, VERSION_CALCULO, user['id'])
            ).fetchone()
            nueva_version_id = v_nueva['id']

            # Copiar programas y firmas históricas a la nueva versión
            conn.execute(
                '''INSERT INTO planilla_programas(version_id, programa_id, padre_id, codigo, nombre, orden)
                   SELECT %s, programa_id, padre_id, codigo, nombre, orden
                   FROM planilla_programas WHERE version_id = %s''',
                (nueva_version_id, version_cerrada_id)
            )

            conn.execute(
                '''INSERT INTO planilla_firmas(version_id, posicion, firma_id, nombre_completo, cargo)
                   SELECT %s, posicion, firma_id, nombre_completo, cargo
                   FROM planilla_firmas WHERE version_id = %s''',
                (nueva_version_id, version_cerrada_id)
            )

            # Copiar filas y descuentos íntegros de la versión cerrada
            filas_cerradas = conn.execute(
                'SELECT * FROM planilla_detalle WHERE version_id = %s ORDER BY orden ASC',
                (version_cerrada_id,)
            ).fetchall()

            for fc in filas_cerradas:
                nd_row = conn.execute(
                    '''INSERT INTO planilla_detalle(
                           version_id, trabajador_id, orden, dni, apellidos, nombres,
                           institucion_id, institucion_nombre, codigo_modular, distrito,
                           area_id, area_nombre, nivel_id, nivel_nombre,
                           meta_id, meta_codigo, meta_descripcion, partida_codigo,
                           subtipo, cargo, situacion, categoria, categoria_descripcion,
                           fecha_nacimiento, ley, regimen_laboral, jornada_laboral,
                           cuenta_multired, importe, dias_licencia, monto_licencia,
                           total_descuentos, neto,
                           regimen_pensionario, fecha_ingreso, fecha_termino,
                           tiempo_servicio_texto, leyenda_permanente, tipo_pago, numero_cheque
                       ) VALUES (
                           %s, %s, %s, %s, %s, %s,
                           %s, %s, %s, %s,
                           %s, %s, %s, %s,
                           %s, %s, %s, %s,
                           %s, %s, %s, %s, %s,
                           %s, %s, %s, %s,
                           %s, %s, %s, %s,
                           %s, %s,
                           %s, %s, %s,
                           %s, %s, %s, %s
                       ) RETURNING id''',
                    (
                        nueva_version_id, fc['trabajador_id'], fc['orden'], fc['dni'], fc['apellidos'], fc['nombres'],
                        fc['institucion_id'], fc['institucion_nombre'], fc['codigo_modular'], fc['distrito'],
                        fc['area_id'], fc['area_nombre'], fc['nivel_id'], fc['nivel_nombre'],
                        fc['meta_id'], fc['meta_codigo'], fc['meta_descripcion'], fc['partida_codigo'],
                        fc['subtipo'], fc['cargo'], fc['situacion'], fc['categoria'], fc['categoria_descripcion'],
                        fc['fecha_nacimiento'], fc['ley'], fc['regimen_laboral'], fc['jornada_laboral'],
                        fc['cuenta_multired'], fc['importe'], fc['dias_licencia'], fc['monto_licencia'],
                        fc['total_descuentos'], fc['neto'],
                        fc['regimen_pensionario'], fc['fecha_ingreso'], fc['fecha_termino'],
                        fc['tiempo_servicio_texto'], fc['leyenda_permanente'], fc['tipo_pago'], fc['numero_cheque']
                    )
                ).fetchone()
                nuevo_det_id = nd_row['id']

                # Copiar descuentos
                conn.execute(
                    '''INSERT INTO planilla_descuentos(detalle_id, tipo_descuento_id, monto, actualizado_por)
                       SELECT %s, tipo_descuento_id, monto, %s
                       FROM planilla_descuentos
                       WHERE detalle_id = %s''',
                    (nuevo_det_id, user['id'], fc['id'])
                )

            return {
                'nueva_version_id': nueva_version_id,
                'nuevo_numero': nuevo_numero,
                'filas_copiadas': len(filas_cerradas)
            }
