"""Servicio de gestión del Maestro de Personal (Trabajadores II.EE. y Sede).

Permite listar, buscar, filtrar, crear, editar, activar/desactivar trabajadores
y consultar su historial de participación en planillas.
"""
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re
from psycopg.errors import CheckViolation, ForeignKeyViolation, UniqueViolation

from cafae.auth import AuthService
from cafae.security import AccessError, UserError


def _clean_str(val, name, min_len=0, max_len=255, required=False):
    if val is None:
        if required:
            raise UserError(f'El campo "{name}" es obligatorio.')
        return None
    cleaned = str(val).strip()
    if not cleaned:
        if required:
            raise UserError(f'El campo "{name}" no puede estar vacío.')
        return None
    if any(ord(c) < 32 and c not in '\r\n\t' for c in cleaned):
        raise UserError(f'El campo "{name}" contiene caracteres inválidos.')
    if len(cleaned) < min_len or len(cleaned) > max_len:
        raise UserError(f'El campo "{name}" debe tener entre {min_len} y {max_len} caracteres.')
    return cleaned


def parse_monto(value, name='Importe') -> Decimal:
    """Convierte de forma segura y estricta una entrada a Decimal(12,2) >= 0. Rechaza float."""
    if isinstance(value, float):
        raise UserError(f'El monto "{name}" no puede provenir de un tipo float impreciso.')
    if value is None or (isinstance(value, str) and not value.strip()):
        return Decimal('0.00')
    try:
        val_str = str(value).strip().replace(',', '')
        d = Decimal(val_str).quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    except (InvalidOperation, TypeError, ValueError):
        raise UserError(f'El campo "{name}" no es un número monetario válido.')
    if not d.is_finite():
        raise UserError(f'El campo "{name}" contiene un valor no finito.')
    if d < Decimal('0.00'):
        raise UserError(f'El campo "{name}" no puede ser negativo.')
    if d > Decimal('999999999.99'):
        raise UserError(f'El campo "{name}" excede el límite permitido.')
    return d


def validate_dni(dni: str) -> str:
    cleaned = str(dni).strip() if dni else ''
    if not re.fullmatch(r'^[0-9]{8}$', cleaned):
        raise UserError('El DNI debe contener exactamente 8 dígitos numéricos.')
    return cleaned


class TrabajadorService:
    def __init__(self, auth_service=None):
        self.auth = auth_service or AuthService()

    def list_trabajadores(self, token, tipo=None, solo_activos=False, query=None,
                          institucion_id=None, area_id=None, nivel_id=None,
                          cargo_id=None, situacion_id=None, categoria_id=None):
        sql = '''SELECT t.id, t.dni, t.apellidos, t.nombres, t.tipo,
                        t.institucion_id, t.area_id, t.nivel_id, t.subtipo_id,
                        t.cargo_id, t.situacion_id, t.categoria_id,
                        t.fecha_nacimiento, t.ley, t.regimen_laboral, t.jornada_laboral,
                        t.cuenta_multired, t.importe, t.activo, t.creado_en, t.actualizado_en,
                        t.regimen_pensionario, t.fecha_ingreso, t.fecha_termino,
                        t.tiempo_servicio_texto, t.leyenda_permanente, t.tipo_pago, t.numero_cheque,
                        i.nombre AS institucion_nombre, i.codigo_modular AS institucion_codigo_modular,
                        a.nombre AS area_nombre,
                        n.nombre AS nivel_nombre,
                        c.nombre AS cargo_nombre,
                        cat.codigo AS categoria_codigo, cat.descripcion AS categoria_descripcion,
                        s.nombre AS situacion_nombre,
                        sub.nombre AS subtipo_nombre
                 FROM trabajadores t
                 LEFT JOIN instituciones i ON i.id = t.institucion_id
                 LEFT JOIN areas_sede a ON a.id = t.area_id
                 LEFT JOIN niveles n ON n.id = t.nivel_id
                 LEFT JOIN cargos c ON c.id = t.cargo_id
                 LEFT JOIN categorias cat ON cat.id = t.categoria_id
                 LEFT JOIN situaciones s ON s.id = t.situacion_id
                 LEFT JOIN subtipos_trabajador sub ON sub.id = t.subtipo_id
                 WHERE 1=1'''
        params = []
        if tipo:
            if tipo not in ('IIEE', 'SEDE'):
                raise UserError('Tipo de trabajador inválido (debe ser IIEE o SEDE).')
            sql += ' AND t.tipo = %s'
            params.append(tipo)
        if solo_activos:
            sql += ' AND t.activo = true'
        if institucion_id:
            sql += ' AND t.institucion_id = %s'
            params.append(int(institucion_id))
        if area_id:
            sql += ' AND t.area_id = %s'
            params.append(int(area_id))
        if nivel_id:
            sql += ' AND t.nivel_id = %s'
            params.append(int(nivel_id))
        if cargo_id:
            sql += ' AND t.cargo_id = %s'
            params.append(int(cargo_id))
        if situacion_id:
            sql += ' AND t.situacion_id = %s'
            params.append(int(situacion_id))
        if categoria_id:
            sql += ' AND t.categoria_id = %s'
            params.append(int(categoria_id))
        if query and query.strip():
            clean_q = f'%{query.strip()}%'
            sql += ''' AND (t.dni ILIKE %s OR t.apellidos ILIKE %s OR t.nombres ILIKE %s
                            OR i.nombre ILIKE %s OR i.codigo_modular ILIKE %s OR a.nombre ILIKE %s)'''
            params.extend([clean_q, clean_q, clean_q, clean_q, clean_q, clean_q])

        sql += ' ORDER BY t.apellidos ASC, t.nombres ASC'
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, params).fetchall()

    def get_trabajador(self, token, trabajador_id):
        sql = '''SELECT t.*,
                        i.nombre AS institucion_nombre, i.codigo_modular AS institucion_codigo_modular,
                        a.nombre AS area_nombre,
                        n.nombre AS nivel_nombre,
                        c.nombre AS cargo_nombre,
                        cat.codigo AS categoria_codigo, cat.descripcion AS categoria_descripcion,
                        s.nombre AS situacion_nombre,
                        sub.nombre AS subtipo_nombre
                 FROM trabajadores t
                 LEFT JOIN instituciones i ON i.id = t.institucion_id
                 LEFT JOIN areas_sede a ON a.id = t.area_id
                 LEFT JOIN niveles n ON n.id = t.nivel_id
                 LEFT JOIN cargos c ON c.id = t.cargo_id
                 LEFT JOIN categorias cat ON cat.id = t.categoria_id
                 LEFT JOIN situaciones s ON s.id = t.situacion_id
                 LEFT JOIN subtipos_trabajador sub ON sub.id = t.subtipo_id
                 WHERE t.id = %s'''
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, (trabajador_id,)).fetchone()

    def get_trabajador_by_dni(self, token, dni):
        dni = validate_dni(dni)
        sql = 'SELECT * FROM trabajadores WHERE dni = %s'
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, (dni,)).fetchone()

    def create_trabajador(self, token, datos: dict) -> int:
        dni = validate_dni(datos.get('dni'))
        apellidos = _clean_str(datos.get('apellidos'), 'Apellidos', 1, 150, required=True)
        nombres = _clean_str(datos.get('nombres'), 'Nombres', 1, 150, required=True)
        tipo = _clean_str(datos.get('tipo'), 'Tipo de personal', required=True)
        if tipo not in ('IIEE', 'SEDE'):
            raise UserError('El tipo de personal debe ser "IIEE" o "SEDE".')

        institucion_id = int(datos['institucion_id']) if datos.get('institucion_id') else None
        area_id = int(datos['area_id']) if datos.get('area_id') else None

        if tipo == 'IIEE':
            if area_id is not None:
                raise UserError('Un trabajador de II.EE. no puede tener asignada un área de Sede.')
            if not institucion_id:
                raise UserError('Debe seleccionar la Institución Educativa de adscripción.')
        else:  # SEDE
            if institucion_id is not None:
                raise UserError('Un trabajador de Sede no puede tener asignada una Institución Educativa.')
            if not area_id:
                raise UserError('Debe seleccionar el Área de Sede de adscripción.')

        nivel_id = int(datos['nivel_id']) if datos.get('nivel_id') else None
        subtipo_id = int(datos['subtipo_id']) if datos.get('subtipo_id') else None
        cargo_id = int(datos['cargo_id']) if datos.get('cargo_id') else None
        situacion_id = int(datos['situacion_id']) if datos.get('situacion_id') else None
        categoria_id = int(datos['categoria_id']) if datos.get('categoria_id') else None

        fecha_nac = datos.get('fecha_nacimiento')
        if fecha_nac and not isinstance(fecha_nac, date):
            raise UserError('La fecha de nacimiento no es válida.')

        fecha_ing = datos.get('fecha_ingreso')
        if fecha_ing and not isinstance(fecha_ing, date):
            raise UserError('La fecha de ingreso no es válida.')

        fecha_ter = datos.get('fecha_termino')
        if fecha_ter and not isinstance(fecha_ter, date):
            raise UserError('La fecha de término no es válida.')

        if fecha_ing and fecha_ter and fecha_ter < fecha_ing:
            raise UserError('La fecha de término no puede ser anterior a la fecha de ingreso.')

        ley = _clean_str(datos.get('ley'), 'Ley', 0, 120)
        regimen_lab = _clean_str(datos.get('regimen_laboral'), 'Régimen laboral', 0, 120)
        jornada = _clean_str(datos.get('jornada_laboral'), 'Jornada laboral', 0, 60)
        cuenta = _clean_str(datos.get('cuenta_multired'), 'Cuenta Multired', 0, 60)
        tipo_pago = _clean_str(datos.get('tipo_pago'), 'Tipo de pago') or 'CUENTA'
        if tipo_pago not in ('CUENTA', 'CHEQUE'):
            raise UserError('El tipo de pago debe ser "CUENTA" o "CHEQUE".')
        num_cheque = _clean_str(datos.get('numero_cheque'), 'Número de cheque', 0, 60)
        if tipo_pago == 'CHEQUE' and not num_cheque:
            raise UserError('Debe ingresar el número de cheque para la modalidad CHEQUE.')

        importe = parse_monto(datos.get('importe', Decimal('0.00')), 'Importe')
        regimen_pen = _clean_str(datos.get('regimen_pensionario'), 'Régimen pensionario', 0, 120)
        tiempo_serv = _clean_str(datos.get('tiempo_servicio_texto'), 'Tiempo de servicio', 0, 60)
        leyenda_perm = _clean_str(datos.get('leyenda_permanente'), 'Leyenda permanente', 0, 1000)
        activo = bool(datos.get('activo', True))

        try:
            with self.auth.data_transaction(token, 'trabajadores') as (conn, _):
                # Validar existencia de FKs
                if institucion_id and not conn.execute('SELECT 1 FROM instituciones WHERE id = %s', (institucion_id,)).fetchone():
                    raise UserError('La institución seleccionada no existe.')
                if area_id and not conn.execute('SELECT 1 FROM areas_sede WHERE id = %s', (area_id,)).fetchone():
                    raise UserError('El área seleccionada no existe.')
                if nivel_id and not conn.execute('SELECT 1 FROM niveles WHERE id = %s', (nivel_id,)).fetchone():
                    raise UserError('El nivel seleccionado no existe.')
                if cargo_id and not conn.execute('SELECT 1 FROM cargos WHERE id = %s', (cargo_id,)).fetchone():
                    raise UserError('El cargo seleccionado no existe.')
                if categoria_id and not conn.execute('SELECT 1 FROM categorias WHERE id = %s', (categoria_id,)).fetchone():
                    raise UserError('La categoría seleccionada no existe.')
                if situacion_id and not conn.execute('SELECT 1 FROM situaciones WHERE id = %s', (situacion_id,)).fetchone():
                    raise UserError('La situación laboral seleccionada no existe.')
                if subtipo_id and not conn.execute('SELECT 1 FROM subtipos_trabajador WHERE id = %s', (subtipo_id,)).fetchone():
                    raise UserError('El subtipo seleccionado no existe.')

                row = conn.execute(
                    '''INSERT INTO trabajadores(
                           dni, apellidos, nombres, tipo, institucion_id, area_id, nivel_id,
                           subtipo_id, cargo_id, situacion_id, categoria_id, fecha_nacimiento,
                           ley, regimen_laboral, jornada_laboral, cuenta_multired, importe, activo,
                           regimen_pensionario, fecha_ingreso, fecha_termino, tiempo_servicio_texto,
                           leyenda_permanente, tipo_pago, numero_cheque
                       ) VALUES (
                           %s, %s, %s, %s, %s, %s, %s,
                           %s, %s, %s, %s, %s,
                           %s, %s, %s, %s, %s, %s,
                           %s, %s, %s, %s,
                           %s, %s, %s
                       ) RETURNING id''',
                    (
                        dni, apellidos, nombres, tipo, institucion_id, area_id, nivel_id,
                        subtipo_id, cargo_id, situacion_id, categoria_id, fecha_nac,
                        ley, regimen_lab, jornada, cuenta, importe, activo,
                        regimen_pen, fecha_ing, fecha_ter, tiempo_serv,
                        leyenda_perm, tipo_pago, num_cheque
                    )
                ).fetchone()
                return row['id']
        except UniqueViolation:
            raise UserError(f'Ya existe un trabajador registrado con el DNI "{dni}".')
        except CheckViolation as exc:
            if 'ck_fechas_laborales' in str(exc):
                raise UserError('La fecha de término laboral no puede ser anterior a la de ingreso.')
            raise UserError('Los datos del trabajador no cumplen las restricciones del sistema.')
        except ForeignKeyViolation:
            raise UserError('Una de las relaciones seleccionadas (institución, área, nivel, cargo, etc.) no es válida.')

    def update_trabajador(self, token, trabajador_id, datos: dict) -> None:
        trabajador_id = int(trabajador_id)
        dni = validate_dni(datos.get('dni'))
        apellidos = _clean_str(datos.get('apellidos'), 'Apellidos', 1, 150, required=True)
        nombres = _clean_str(datos.get('nombres'), 'Nombres', 1, 150, required=True)
        tipo = _clean_str(datos.get('tipo'), 'Tipo de personal', required=True)
        if tipo not in ('IIEE', 'SEDE'):
            raise UserError('El tipo de personal debe ser "IIEE" o "SEDE".')

        institucion_id = int(datos['institucion_id']) if datos.get('institucion_id') else None
        area_id = int(datos['area_id']) if datos.get('area_id') else None

        if tipo == 'IIEE':
            if area_id is not None:
                raise UserError('Un trabajador de II.EE. no puede tener asignada un área de Sede.')
            if not institucion_id:
                raise UserError('Debe seleccionar la Institución Educativa de adscripción.')
        else:
            if institucion_id is not None:
                raise UserError('Un trabajador de Sede no puede tener asignada una Institución Educativa.')
            if not area_id:
                raise UserError('Debe seleccionar el Área de Sede de adscripción.')

        nivel_id = int(datos['nivel_id']) if datos.get('nivel_id') else None
        subtipo_id = int(datos['subtipo_id']) if datos.get('subtipo_id') else None
        cargo_id = int(datos['cargo_id']) if datos.get('cargo_id') else None
        situacion_id = int(datos['situacion_id']) if datos.get('situacion_id') else None
        categoria_id = int(datos['categoria_id']) if datos.get('categoria_id') else None

        fecha_nac = datos.get('fecha_nacimiento')
        if fecha_nac and not isinstance(fecha_nac, date):
            raise UserError('La fecha de nacimiento no es válida.')

        fecha_ing = datos.get('fecha_ingreso')
        if fecha_ing and not isinstance(fecha_ing, date):
            raise UserError('La fecha de ingreso no es válida.')

        fecha_ter = datos.get('fecha_termino')
        if fecha_ter and not isinstance(fecha_ter, date):
            raise UserError('La fecha de término no es válida.')

        if fecha_ing and fecha_ter and fecha_ter < fecha_ing:
            raise UserError('La fecha de término no puede ser anterior a la fecha de ingreso.')

        ley = _clean_str(datos.get('ley'), 'Ley', 0, 120)
        regimen_lab = _clean_str(datos.get('regimen_laboral'), 'Régimen laboral', 0, 120)
        jornada = _clean_str(datos.get('jornada_laboral'), 'Jornada laboral', 0, 60)
        cuenta = _clean_str(datos.get('cuenta_multired'), 'Cuenta Multired', 0, 60)
        tipo_pago = _clean_str(datos.get('tipo_pago'), 'Tipo de pago') or 'CUENTA'
        if tipo_pago not in ('CUENTA', 'CHEQUE'):
            raise UserError('El tipo de pago debe ser "CUENTA" o "CHEQUE".')
        num_cheque = _clean_str(datos.get('numero_cheque'), 'Número de cheque', 0, 60)
        if tipo_pago == 'CHEQUE' and not num_cheque:
            raise UserError('Debe ingresar el número de cheque para la modalidad CHEQUE.')

        importe = parse_monto(datos.get('importe', Decimal('0.00')), 'Importe')
        regimen_pen = _clean_str(datos.get('regimen_pensionario'), 'Régimen pensionario', 0, 120)
        tiempo_serv = _clean_str(datos.get('tiempo_servicio_texto'), 'Tiempo de servicio', 0, 60)
        leyenda_perm = _clean_str(datos.get('leyenda_permanente'), 'Leyenda permanente', 0, 1000)
        activo = bool(datos.get('activo', True))

        try:
            with self.auth.data_transaction(token, 'trabajadores') as (conn, _):
                res = conn.execute(
                    '''UPDATE trabajadores SET
                           dni = %s, apellidos = %s, nombres = %s, tipo = %s,
                           institucion_id = %s, area_id = %s, nivel_id = %s,
                           subtipo_id = %s, cargo_id = %s, situacion_id = %s, categoria_id = %s,
                           fecha_nacimiento = %s, ley = %s, regimen_laboral = %s,
                           jornada_laboral = %s, cuenta_multired = %s, importe = %s, activo = %s,
                           regimen_pensionario = %s, fecha_ingreso = %s, fecha_termino = %s,
                           tiempo_servicio_texto = %s, leyenda_permanente = %s,
                           tipo_pago = %s, numero_cheque = %s
                       WHERE id = %s RETURNING id''',
                    (
                        dni, apellidos, nombres, tipo,
                        institucion_id, area_id, nivel_id,
                        subtipo_id, cargo_id, situacion_id, categoria_id,
                        fecha_nac, ley, regimen_lab,
                        jornada, cuenta, importe, activo,
                        regimen_pen, fecha_ing, fecha_ter,
                        tiempo_serv, leyenda_perm,
                        tipo_pago, num_cheque,
                        trabajador_id
                    )
                ).fetchone()
                if not res:
                    raise UserError('Trabajador no encontrado.')
        except UniqueViolation:
            raise UserError(f'Ya existe otro trabajador registrado con el DNI "{dni}".')
        except CheckViolation as exc:
            if 'ck_fechas_laborales' in str(exc):
                raise UserError('La fecha de término laboral no puede ser anterior a la de ingreso.')
            raise UserError('Los datos del trabajador no cumplen las restricciones del sistema.')
        except ForeignKeyViolation:
            raise UserError('Una de las relaciones seleccionadas no es válida.')

    def set_activo(self, token, trabajador_id, activo: bool) -> None:
        trabajador_id = int(trabajador_id)
        activo = bool(activo)
        with self.auth.data_transaction(token, 'trabajadores') as (conn, _):
            res = conn.execute(
                'UPDATE trabajadores SET activo = %s WHERE id = %s RETURNING id',
                (activo, trabajador_id)
            ).fetchone()
            if not res:
                raise UserError('Trabajador no encontrado.')

    def historial_planillas(self, token, trabajador_id):
        """Consulta el historial de todas las planillas en las que participó el trabajador."""
        trabajador_id = int(trabajador_id)
        sql = '''SELECT p.id AS planilla_id, per.anio, per.mes, p.tipo,
                        pv.numero AS version_numero, pv.estado AS version_estado,
                        pd.id AS detalle_id, pd.importe, pd.total_descuentos, pd.neto,
                        pd.dias_licencia, pd.monto_licencia,
                        COALESCE(pd.institucion_nombre, pd.area_nombre) AS adscripcion_historica,
                        pd.categoria AS categoria_historica,
                        pd.cuenta_multired AS cuenta_historica,
                        pv.cerrada_en, u.nombre_completo AS cerrado_por_nombre
                 FROM planilla_detalle pd
                 JOIN planilla_versiones pv ON pv.id = pd.version_id
                 JOIN planillas p ON p.id = pv.planilla_id
                 JOIN periodos per ON per.id = p.periodo_id
                 LEFT JOIN usuarios u ON u.id = pv.cerrada_por
                 WHERE pd.trabajador_id = %s
                 ORDER BY per.anio DESC, per.mes DESC, pv.numero DESC'''
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, (trabajador_id,)).fetchall()
