"""Servicio de Dashboard y los 9 Reportes Administrativos Obligatorios (Etapa 16).
Garantiza que cada cifra provenga de la versión exacta seleccionada sin mezclar históricos.
"""
from decimal import Decimal
from cafae.auth import AuthService
from cafae.security import UserError


class ReporteService:
    def __init__(self, auth_service=None):
        self.auth = auth_service or AuthService()

    # =========================================================================
    # DASHBOARD
    # =========================================================================
    def get_dashboard_summary(self, token):
        """Retorna las métricas institucionales de II.EE. y Sede para el Dashboard."""
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            # Última versión de IIEE
            pln_iiee = conn.execute(
                '''SELECT p.id, per.anio, per.mes, p.tipo, pv.id AS version_id,
                          pv.numero, pv.estado, pv.total_trabajadores, pv.total_importe,
                          pv.total_descuentos, pv.total_neto, pv.cerrada_en
                   FROM planillas p
                   JOIN periodos per ON per.id = p.periodo_id
                   JOIN planilla_versiones pv ON pv.id = (
                       SELECT id FROM planilla_versiones WHERE planilla_id = p.id ORDER BY numero DESC LIMIT 1
                   )
                   WHERE p.tipo = 'IIEE'
                   ORDER BY per.anio DESC, per.mes DESC LIMIT 1'''
            ).fetchone()

            # Última versión de SEDE
            pln_sede = conn.execute(
                '''SELECT p.id, per.anio, per.mes, p.tipo, pv.id AS version_id,
                          pv.numero, pv.estado, pv.total_trabajadores, pv.total_importe,
                          pv.total_descuentos, pv.total_neto, pv.cerrada_en
                   FROM planillas p
                   JOIN periodos per ON per.id = p.periodo_id
                   JOIN planilla_versiones pv ON pv.id = (
                       SELECT id FROM planilla_versiones WHERE planilla_id = p.id ORDER BY numero DESC LIMIT 1
                   )
                   WHERE p.tipo = 'SEDE'
                   ORDER BY per.anio DESC, per.mes DESC LIMIT 1'''
            ).fetchone()

            tot_trab_activos = conn.execute(
                'SELECT count(*) AS total FROM trabajadores WHERE activo = true'
            ).fetchone()['total']

            tot_iiee = conn.execute(
                'SELECT count(*) AS total FROM instituciones WHERE activo = true'
            ).fetchone()['total']

            # Alertas accionables (netos negativos en versiones abiertas)
            alertas = conn.execute(
                '''SELECT count(*) AS total FROM planilla_detalle pd
                   JOIN planilla_versiones pv ON pv.id = pd.version_id
                   WHERE pv.estado <> 'CERRADA' AND pd.neto < 0'''
            ).fetchone()['total']

            return {
                'iiee': pln_iiee,
                'sede': pln_sede,
                'trabajadores_activos': tot_trab_activos,
                'instituciones_activas': tot_iiee,
                'alertas_neto_negativo': alertas
            }

    # =========================================================================
    # LOS 9 REPORTES OBLIGATORIOS
    # =========================================================================
    # 1. Resumen mensual
    def reporte_resumen_mensual(self, token, version_id):
        sql = '''SELECT pv.numero, pv.estado, pv.origen, p.tipo, per.anio, per.mes,
                        count(pd.id) AS total_personas,
                        COALESCE(sum(pd.importe), 0.00) AS total_importe,
                        COALESCE(sum(pd.monto_licencia), 0.00) AS total_licencia,
                        COALESCE(sum(pd.total_descuentos), 0.00) AS total_descuentos,
                        COALESCE(sum(pd.neto), 0.00) AS total_neto
                 FROM planilla_versiones pv
                 JOIN planillas p ON p.id = pv.planilla_id
                 JOIN periodos per ON per.id = p.periodo_id
                 LEFT JOIN planilla_detalle pd ON pd.version_id = pv.id
                 WHERE pv.id = %s
                 GROUP BY pv.id, pv.numero, pv.estado, pv.origen, p.tipo, per.anio, per.mes'''
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, (version_id,)).fetchone()

    # 2. Importe por institución
    def reporte_importe_por_institucion(self, token, version_id):
        sql = '''SELECT pd.institucion_id,
                        COALESCE(pd.institucion_nombre, 'SIN INSTITUCIÓN') AS institucion_nombre,
                        pd.codigo_modular,
                        count(pd.id) AS cantidad_trabajadores,
                        sum(pd.importe) AS total_importe,
                        sum(pd.total_descuentos) AS total_descuentos,
                        sum(pd.neto) AS total_neto
                 FROM planilla_detalle pd
                 WHERE pd.version_id = %s
                 GROUP BY pd.institucion_id, pd.institucion_nombre, pd.codigo_modular
                 ORDER BY total_importe DESC'''
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, (version_id,)).fetchall()

    # 3. Importe por meta (Hoja de Trabajo de Remuneraciones Oficial)
    def reporte_importe_por_meta(self, token, version_id):
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            curr_v = conn.execute('''
                SELECT p.id AS planilla_id, p.periodo_id, p.tipo, per.anio, per.mes, pv.numero
                FROM planilla_versiones pv
                JOIN planillas p ON p.id = pv.planilla_id
                JOIN periodos per ON per.id = p.periodo_id
                WHERE pv.id = %s
            ''', (version_id,)).fetchone()
            if not curr_v:
                raise UserError('Versión no encontrada.')

            # Consultar exclusivamente las metas presentes en esta versión de planilla seleccionada
            rows = conn.execute('''
                SELECT 
                    COALESCE(NULLIF(btrim(pd.meta_codigo), ''), 'S/M') AS meta_codigo,
                    COALESCE(pd.meta_descripcion, 'Sin Descripción') AS meta_descripcion,
                    count(pd.id) AS cantidad_trabajadores,
                    sum(pd.importe) AS total_importe
                FROM planilla_detalle pd
                WHERE pd.version_id = %s
                GROUP BY pd.meta_codigo, pd.meta_descripcion
                ORDER BY pd.meta_codigo ASC
            ''', (version_id,)).fetchall()

            tipo = curr_v['tipo']
            metas_map = {}
            for r in rows:
                m = str(r['meta_codigo']).strip().lstrip('0')
                imp = float(r['total_importe'] or 0.0)
                metas_map[m] = metas_map.get(m, 0.0) + imp

            if tipo == 'SEDE':
                # Sede Central: agrupa los fondos de la meta de Gestión
                gestion = sum(float(r['total_importe'] or 0.0) for r in rows)
                meta_num = '33'
                for r in rows:
                    cod = str(r['meta_codigo']).strip().lstrip('0')
                    if cod in ('1', '33'):
                        meta_num = '33' if cod == '33' else '01'

                return {
                    'tipo': 'SEDE',
                    'anio': curr_v['anio'],
                    'mes': curr_v['mes'],
                    'gestion': gestion,
                    'meta_gestion': meta_num,
                    'total_general': gestion,
                    'metas_lista': [dict(r) for r in rows]
                }
            else:
                # II.EE.: agrupa los fondos de cada meta educativa encontrada en la planilla
                inicial = metas_map.get('11', 0.0)
                primaria = metas_map.get('12', 0.0)
                secundaria = metas_map.get('14', 0.0)
                basica_sub = inicial + primaria + secundaria

                eba_inicial = metas_map.get('43', 0.0)
                eba_avanzado = metas_map.get('44', 0.0)
                eba_sub = eba_inicial + eba_avanzado

                esp_inicial = metas_map.get('29', 0.0)
                esp_primaria = metas_map.get('30', 0.0)
                esp_sub = esp_inicial + esp_primaria

                tec_prod = metas_map.get('42', 0.0)

                # Identificar metas adicionales que no pertenezcan al estándar
                codigos_estandar = {'11', '12', '14', '43', '44', '29', '30', '42'}
                otras_metas = []
                for r in rows:
                    m = str(r['meta_codigo']).strip().lstrip('0')
                    if m not in codigos_estandar:
                        otras_metas.append({
                            'meta_codigo': r['meta_codigo'],
                            'meta_descripcion': r['meta_descripcion'],
                            'importe': float(r['total_importe'] or 0.0)
                        })

                total_general = sum(float(r['total_importe'] or 0.0) for r in rows)

                return {
                    'tipo': 'IIEE',
                    'anio': curr_v['anio'],
                    'mes': curr_v['mes'],
                    'gestion': 0.0,
                    'basica_sub': basica_sub,
                    'inicial': inicial,
                    'primaria': primaria,
                    'secundaria': secundaria,
                    'eba_sub': eba_sub,
                    'eba_inicial': eba_inicial,
                    'eba_avanzado': eba_avanzado,
                    'esp_sub': esp_sub,
                    'esp_inicial': esp_inicial,
                    'esp_primaria': esp_primaria,
                    'tec_prod': tec_prod,
                    'otras_metas': otras_metas,
                    'total_general': total_general,
                    'metas_lista': [dict(r) for r in rows]
                }

    # 4. Descuentos por entidad
    def reporte_descuentos_por_entidad(self, token, version_id):
        sql = '''SELECT td.codigo, td.nombre AS entidad_nombre,
                        count(pd.id) FILTER (WHERE pd.monto > 0) AS trabajadores_afectados,
                        COALESCE(sum(pd.monto), 0.00) AS total_descontado
                 FROM tipos_descuento td
                 LEFT JOIN planilla_descuentos pd ON pd.tipo_descuento_id = td.id
                      AND pd.detalle_id IN (SELECT id FROM planilla_detalle WHERE version_id = %s)
                 GROUP BY td.id, td.codigo, td.nombre, td.orden
                 ORDER BY td.orden ASC'''
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, (version_id,)).fetchall()

    # 5. Neto por institución
    def reporte_neto_por_institucion(self, token, version_id):
        sql = '''SELECT COALESCE(pd.institucion_nombre, pd.area_nombre, 'GENERAL') AS nombre_entidad,
                        count(pd.id) AS personas,
                        sum(pd.importe) AS importe,
                        sum(pd.total_descuentos) AS descuentos,
                        sum(pd.neto) AS liquido_neto
                 FROM planilla_detalle pd
                 WHERE pd.version_id = %s
                 GROUP BY pd.institucion_nombre, pd.area_nombre
                 ORDER BY liquido_neto DESC'''
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, (version_id,)).fetchall()

    # 6. Trabajadores por nivel
    def reporte_trabajadores_por_nivel(self, token, version_id):
        sql = '''SELECT COALESCE(pd.nivel_nombre, 'SIN NIVEL') AS nivel_nombre,
                        count(pd.id) AS total_trabajadores,
                        sum(pd.importe) AS total_importe
                 FROM planilla_detalle pd
                 WHERE pd.version_id = %s
                 GROUP BY pd.nivel_nombre
                 ORDER BY total_trabajadores DESC'''
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, (version_id,)).fetchall()

    # 7. Trabajadores por situación
    def reporte_trabajadores_por_situacion(self, token, version_id):
        sql = '''SELECT COALESCE(pd.situacion, 'NO ESPECIFICADA') AS situacion_laboral,
                        count(pd.id) AS total_trabajadores,
                        sum(pd.importe) AS total_importe
                 FROM planilla_detalle pd
                 WHERE pd.version_id = %s
                 GROUP BY pd.situacion
                 ORDER BY total_trabajadores DESC'''
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, (version_id,)).fetchall()

    # 8. Licencias sin goce
    def reporte_licencias_sin_goce(self, token, version_id):
        sql = '''SELECT pd.dni, pd.apellidos, pd.nombres,
                        COALESCE(pd.institucion_nombre, pd.area_nombre) AS adscripcion,
                        pd.importe, pd.dias_licencia, pd.monto_licencia, pd.neto
                 FROM planilla_detalle pd
                 WHERE pd.version_id = %s AND pd.dias_licencia > 0
                 ORDER BY pd.dias_licencia DESC, pd.apellidos ASC'''
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, (version_id,)).fetchall()

    # 9. Comparación mensual
    def reporte_comparacion_mensual(self, token, version_id_1, version_id_2):
        sql = '''SELECT pv.id AS version_id, p.tipo, per.anio, per.mes, pv.numero,
                        COALESCE(pv.total_trabajadores, (SELECT count(*) FROM planilla_detalle WHERE version_id = pv.id)) AS total_trabajadores,
                        COALESCE(pv.total_importe, (SELECT sum(importe) FROM planilla_detalle WHERE version_id = pv.id)) AS total_importe,
                        COALESCE(pv.total_descuentos, (SELECT sum(total_descuentos) FROM planilla_detalle WHERE version_id = pv.id)) AS total_descuentos,
                        COALESCE(pv.total_neto, (SELECT sum(neto) FROM planilla_detalle WHERE version_id = pv.id)) AS total_neto
                 FROM planilla_versiones pv
                 JOIN planillas p ON p.id = pv.planilla_id
                 JOIN periodos per ON per.id = p.periodo_id
                 WHERE pv.id IN (%s, %s)
                 ORDER BY per.anio ASC, per.mes ASC, pv.numero ASC'''
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, (version_id_1, version_id_2)).fetchall()

    def reporte_comparativo_mes_anterior(self, token, version_id):
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            curr = conn.execute(
                '''SELECT p.id AS planilla_id, p.tipo, per.anio, per.mes, pv.numero
                   FROM planilla_versiones pv
                   JOIN planillas p ON p.id = pv.planilla_id
                   JOIN periodos per ON per.id = p.periodo_id
                   WHERE pv.id = %s''', (version_id,)
            ).fetchone()
            if not curr:
                raise UserError('Versión no encontrada.')

            prev = conn.execute(
                '''SELECT pv.id
                   FROM planilla_versiones pv
                   JOIN planillas p ON p.id = pv.planilla_id
                   JOIN periodos per ON per.id = p.periodo_id
                   WHERE p.tipo = %s AND (per.anio < %s OR (per.anio = %s AND per.mes < %s) OR (p.id = %s AND pv.numero < %s))
                   ORDER BY per.anio DESC, per.mes DESC, pv.numero DESC LIMIT 1''',
                (curr['tipo'], curr['anio'], curr['anio'], curr['mes'], curr['planilla_id'], curr['numero'])
            ).fetchone()

            v_prev_id = prev['id'] if prev else version_id
            sql = '''SELECT pv.id AS version_id, p.tipo, per.anio, per.mes, pv.numero,
                            COALESCE(pv.total_trabajadores, (SELECT count(*) FROM planilla_detalle WHERE version_id = pv.id)) AS total_trabajadores,
                            COALESCE(pv.total_importe, (SELECT sum(importe) FROM planilla_detalle WHERE version_id = pv.id)) AS total_importe,
                            COALESCE(pv.total_descuentos, (SELECT sum(total_descuentos) FROM planilla_detalle WHERE version_id = pv.id)) AS total_descuentos,
                            COALESCE(pv.total_neto, (SELECT sum(neto) FROM planilla_detalle WHERE version_id = pv.id)) AS total_neto
                     FROM planilla_versiones pv
                     JOIN planillas p ON p.id = pv.planilla_id
                     JOIN periodos per ON per.id = p.periodo_id
                     WHERE pv.id IN (%s, %s)
                     ORDER BY per.anio ASC, per.mes ASC, pv.numero ASC'''
            return conn.execute(sql, (v_prev_id, version_id)).fetchall()

    # General de Descuentos Detallado
    def reporte_general_descuentos(self, token, version_id):
        sql = '''SELECT pd.dni, pd.apellidos, pd.nombres,
                        COALESCE(pd.institucion_nombre, pd.area_nombre, 'SIN ASIGNACIÓN') AS adscripcion,
                        pd.importe,
                        COALESCE((SELECT monto FROM planilla_descuentos WHERE detalle_id = pd.id AND tipo_descuento_id = 1), 0.00) AS pichincha,
                        COALESCE((SELECT monto FROM planilla_descuentos WHERE detalle_id = pd.id AND tipo_descuento_id = 2), 0.00) AS caja_sullana,
                        COALESCE((SELECT monto FROM planilla_descuentos WHERE detalle_id = pd.id AND tipo_descuento_id = 3), 0.00) AS sub_cafae,
                        COALESCE((SELECT monto FROM planilla_descuentos WHERE detalle_id = pd.id AND tipo_descuento_id = 4), 0.00) AS brenta,
                        COALESCE((SELECT monto FROM planilla_descuentos WHERE detalle_id = pd.id AND tipo_descuento_id = 5), 0.00) AS sitrase,
                        COALESCE((SELECT monto FROM planilla_descuentos WHERE detalle_id = pd.id AND tipo_descuento_id = 6), 0.00) AS sitase,
                        pd.monto_licencia AS licencia,
                        COALESCE((SELECT monto FROM planilla_descuentos WHERE detalle_id = pd.id AND tipo_descuento_id = 7), 0.00) AS otros,
                        pd.total_descuentos,
                        pd.neto
                 FROM planilla_detalle pd
                 WHERE pd.version_id = %s
                 ORDER BY pd.apellidos ASC, pd.nombres ASC'''
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, (version_id,)).fetchall()

    # Modalidad de Pago
    def reporte_modalidad_pago(self, token, version_id):
        sql = '''SELECT COALESCE(pd.tipo_pago, 'CUENTA') AS modalidad,
                        count(pd.id) AS cantidad_personas,
                        sum(pd.importe) AS total_importe,
                        sum(pd.total_descuentos) AS total_descuentos,
                        sum(pd.neto) AS total_neto
                 FROM planilla_detalle pd
                 WHERE pd.version_id = %s
                 GROUP BY pd.tipo_pago
                 ORDER BY cantidad_personas DESC'''
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, (version_id,)).fetchall()

    # Padrón Alfabético
    def reporte_padron_alfabetico(self, token, version_id):
        sql = '''SELECT pd.dni, pd.apellidos, pd.nombres,
                        COALESCE(pd.institucion_nombre, pd.area_nombre, 'SIN ASIGNACIÓN') AS adscripcion,
                        pd.cargo, pd.categoria, pd.cuenta_multired, pd.importe, pd.total_descuentos, pd.neto
                 FROM planilla_detalle pd
                 WHERE pd.version_id = %s
                 ORDER BY pd.apellidos ASC, pd.nombres ASC'''
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, (version_id,)).fetchall()
