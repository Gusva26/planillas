"""Servicio de gestión de catálogos institucionales y presupuestarios.

Solo ADMINISTRADOR puede crear, editar o cambiar estado de catálogos.
Todos los roles autenticados pueden consultar los catálogos autorizados.
"""
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from psycopg.errors import CheckViolation, ForeignKeyViolation, UniqueViolation

from cafae.auth import AuthService
from cafae.security import AccessError, UserError


def _clean_text(val, name, min_len=1, max_len=200, required=True):
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


class CatalogoService:
    def __init__(self, auth_service=None):
        self.auth = auth_service or AuthService()

    # =========================================================================
    # A. NIVELES
    # =========================================================================
    def list_niveles(self, token, solo_activos=False):
        sql = '''SELECT id, nombre, activo, creado_en, actualizado_en
                 FROM niveles'''
        if solo_activos:
            sql += ' WHERE activo = true'
        sql += ' ORDER BY nombre ASC'
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql).fetchall()

    def get_nivel(self, token, nivel_id):
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute('SELECT * FROM niveles WHERE id = %s', (nivel_id,)).fetchone()

    def create_nivel(self, token, nombre):
        nombre = _clean_text(nombre, 'Nombre del nivel', 1, 100)
        try:
            with self.auth.data_transaction(token, 'catalogos') as (conn, _):
                row = conn.execute(
                    'INSERT INTO niveles(nombre) VALUES (%s) RETURNING id',
                    (nombre,)
                ).fetchone()
                return row['id']
        except UniqueViolation:
            raise UserError(f'Ya existe un nivel con el nombre "{nombre}".')

    def update_nivel(self, token, nivel_id, nombre, activo):
        nombre = _clean_text(nombre, 'Nombre del nivel', 1, 100)
        activo = bool(activo)
        try:
            with self.auth.data_transaction(token, 'catalogos') as (conn, _):
                res = conn.execute(
                    'UPDATE niveles SET nombre = %s, activo = %s WHERE id = %s RETURNING id',
                    (nombre, activo, nivel_id)
                ).fetchone()
                if not res:
                    raise UserError('Nivel no encontrado.')
        except UniqueViolation:
            raise UserError(f'Ya existe otro nivel con el nombre "{nombre}".')

    # =========================================================================
    # B. PARTIDAS PRESUPUESTARIAS
    # =========================================================================
    def list_partidas(self, token, solo_activos=False):
        sql = '''SELECT id, codigo, descripcion, activo, creado_en, actualizado_en
                 FROM partidas_presupuestarias'''
        if solo_activos:
            sql += ' WHERE activo = true'
        sql += ' ORDER BY codigo ASC'
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql).fetchall()

    def get_partida(self, token, partida_id):
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute('SELECT * FROM partidas_presupuestarias WHERE id = %s', (partida_id,)).fetchone()

    def create_partida(self, token, codigo, descripcion):
        codigo = _clean_text(codigo, 'Código de partida', 1, 40)
        descripcion = _clean_text(descripcion, 'Descripción de partida', 1, 500)
        try:
            with self.auth.data_transaction(token, 'catalogos') as (conn, _):
                row = conn.execute(
                    'INSERT INTO partidas_presupuestarias(codigo, descripcion) VALUES (%s, %s) RETURNING id',
                    (codigo, descripcion)
                ).fetchone()
                return row['id']
        except UniqueViolation:
            raise UserError(f'Ya existe una partida con el código "{codigo}".')

    def update_partida(self, token, partida_id, codigo, descripcion, activo):
        codigo = _clean_text(codigo, 'Código de partida', 1, 40)
        descripcion = _clean_text(descripcion, 'Descripción de partida', 1, 500)
        activo = bool(activo)
        try:
            with self.auth.data_transaction(token, 'catalogos') as (conn, _):
                res = conn.execute(
                    '''UPDATE partidas_presupuestarias
                       SET codigo = %s, descripcion = %s, activo = %s
                       WHERE id = %s RETURNING id''',
                    (codigo, descripcion, activo, partida_id)
                ).fetchone()
                if not res:
                    raise UserError('Partida no encontrada.')
        except UniqueViolation:
            raise UserError(f'Ya existe otra partida con el código "{codigo}".')

    # =========================================================================
    # C. PROGRAMAS PRESUPUESTARIOS (Árbol jerárquico)
    # =========================================================================
    def list_programas(self, token, solo_activos=False):
        sql = '''SELECT p.id, p.padre_id, p.codigo, p.nombre, p.orden, p.activo,
                        p.creado_en, p.actualizado_en,
                        padre.codigo AS padre_codigo, padre.nombre AS padre_nombre
                 FROM programas p
                 LEFT JOIN programas padre ON padre.id = p.padre_id'''
        if solo_activos:
            sql += ' WHERE p.activo = true'
        sql += ' ORDER BY p.orden ASC, p.codigo ASC'
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql).fetchall()

    def get_arbol_programas(self, token, solo_activos=False):
        programas = self.list_programas(token, solo_activos=solo_activos)
        by_id = {p['id']: dict(p, hijos=[]) for p in programas}
        raices = []
        for p in programas:
            pid = p['padre_id']
            if pid and pid in by_id:
                by_id[pid]['hijos'].append(by_id[p['id']])
            else:
                raices.append(by_id[p['id']])
        return raices

    def create_programa(self, token, codigo, nombre, orden=0, padre_id=None):
        codigo = _clean_text(codigo, 'Código de programa', 1, 30)
        nombre = _clean_text(nombre, 'Nombre del programa', 1, 180)
        orden = int(orden)
        if orden < 0:
            raise UserError('El orden debe ser mayor o igual a 0.')
        padre_id = int(padre_id) if padre_id else None

        try:
            with self.auth.data_transaction(token, 'catalogos') as (conn, _):
                if padre_id:
                    padre = conn.execute('SELECT id FROM programas WHERE id = %s', (padre_id,)).fetchone()
                    if not padre:
                        raise UserError('El programa padre especificado no existe.')
                row = conn.execute(
                    '''INSERT INTO programas(codigo, nombre, orden, padre_id)
                       VALUES (%s, %s, %s, %s) RETURNING id''',
                    (codigo, nombre, orden, padre_id)
                ).fetchone()
                return row['id']
        except UniqueViolation:
            raise UserError(f'Ya existe un programa con el código "{codigo}".')
        except CheckViolation as exc:
            if 'Ciclo en programas' in str(exc) or 'ck_programas_padre' in str(exc):
                raise UserError('No se permiten referencias circulares en el árbol de programas.')
            raise UserError('Datos inválidos para el programa.')

    def update_programa(self, token, programa_id, codigo, nombre, orden, padre_id, activo):
        codigo = _clean_text(codigo, 'Código de programa', 1, 30)
        nombre = _clean_text(nombre, 'Nombre del programa', 1, 180)
        orden = int(orden)
        if orden < 0:
            raise UserError('El orden debe ser mayor o igual a 0.')
        programa_id = int(programa_id)
        padre_id = int(padre_id) if padre_id else None
        if padre_id == programa_id:
            raise UserError('Un programa no puede ser su propio padre.')
        activo = bool(activo)

        try:
            with self.auth.data_transaction(token, 'catalogos') as (conn, _):
                if padre_id:
                    padre = conn.execute('SELECT id FROM programas WHERE id = %s', (padre_id,)).fetchone()
                    if not padre:
                        raise UserError('El programa padre especificado no existe.')
                res = conn.execute(
                    '''UPDATE programas
                       SET codigo = %s, nombre = %s, orden = %s, padre_id = %s, activo = %s
                       WHERE id = %s RETURNING id''',
                    (codigo, nombre, orden, padre_id, activo, programa_id)
                ).fetchone()
                if not res:
                    raise UserError('Programa no encontrado.')
        except UniqueViolation:
            raise UserError(f'Ya existe otro programa con el código "{codigo}".')
        except CheckViolation as exc:
            if 'Ciclo en programas' in str(exc):
                raise UserError('No se pueden crear ciclos en la jerarquía de programas.')
            raise UserError('Los datos del programa no cumplen las restricciones del sistema.')

    # =========================================================================
    # D. METAS PRESUPUESTARIAS
    # =========================================================================
    def list_metas(self, token, solo_activos=False):
        sql = '''SELECT m.id, m.codigo, m.descripcion, m.programa_id, m.partida_id,
                        m.activo, m.creado_en, m.actualizado_en,
                        p.codigo AS programa_codigo, p.nombre AS programa_nombre,
                        pp.codigo AS partida_codigo, pp.descripcion AS partida_descripcion
                 FROM metas m
                 LEFT JOIN programas p ON p.id = m.programa_id
                 LEFT JOIN partidas_presupuestarias pp ON pp.id = m.partida_id'''
        if solo_activos:
            sql += ' WHERE m.activo = true'
        sql += ' ORDER BY m.codigo ASC'
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql).fetchall()

    def get_meta(self, token, meta_id):
        sql = '''SELECT m.id, m.codigo, m.descripcion, m.programa_id, m.partida_id,
                        m.activo, m.creado_en, m.actualizado_en,
                        p.codigo AS programa_codigo, p.nombre AS programa_nombre,
                        pp.codigo AS partida_codigo
                 FROM metas m
                 LEFT JOIN programas p ON p.id = m.programa_id
                 LEFT JOIN partidas_presupuestarias pp ON pp.id = m.partida_id
                 WHERE m.id = %s'''
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, (meta_id,)).fetchone()

    def create_meta(self, token, codigo, descripcion, programa_id=None, partida_id=None):
        codigo = _clean_text(codigo, 'Código de meta', 1, 30)
        descripcion = _clean_text(descripcion, 'Descripción de la meta', 1, 500)
        programa_id = int(programa_id) if programa_id else None
        partida_id = int(partida_id) if partida_id else None

        try:
            with self.auth.data_transaction(token, 'catalogos') as (conn, _):
                if programa_id and not conn.execute('SELECT 1 FROM programas WHERE id = %s', (programa_id,)).fetchone():
                    raise UserError('El programa seleccionado no existe.')
                if partida_id and not conn.execute('SELECT 1 FROM partidas_presupuestarias WHERE id = %s', (partida_id,)).fetchone():
                    raise UserError('La partida presupuestaria seleccionada no existe.')
                row = conn.execute(
                    '''INSERT INTO metas(codigo, descripcion, programa_id, partida_id)
                       VALUES (%s, %s, %s, %s) RETURNING id''',
                    (codigo, descripcion, programa_id, partida_id)
                ).fetchone()
                return row['id']
        except UniqueViolation:
            raise UserError(f'Ya existe una meta con el código "{codigo}".')
        except ForeignKeyViolation:
            raise UserError('El programa o partida seleccionado no es válido.')

    def update_meta(self, token, meta_id, codigo, descripcion, programa_id, partida_id, activo):
        codigo = _clean_text(codigo, 'Código de meta', 1, 30)
        descripcion = _clean_text(descripcion, 'Descripción de la meta', 1, 500)
        programa_id = int(programa_id) if programa_id else None
        partida_id = int(partida_id) if partida_id else None
        activo = bool(activo)

        try:
            with self.auth.data_transaction(token, 'catalogos') as (conn, _):
                if programa_id and not conn.execute('SELECT 1 FROM programas WHERE id = %s', (programa_id,)).fetchone():
                    raise UserError('El programa seleccionado no existe.')
                if partida_id and not conn.execute('SELECT 1 FROM partidas_presupuestarias WHERE id = %s', (partida_id,)).fetchone():
                    raise UserError('La partida seleccionada no existe.')
                res = conn.execute(
                    '''UPDATE metas
                       SET codigo = %s, descripcion = %s, programa_id = %s, partida_id = %s, activo = %s
                       WHERE id = %s RETURNING id''',
                    (codigo, descripcion, programa_id, partida_id, activo, meta_id)
                ).fetchone()
                if not res:
                    raise UserError('Meta no encontrada.')
        except UniqueViolation:
            raise UserError(f'Ya existe otra meta con el código "{codigo}".')
        except ForeignKeyViolation:
            raise UserError('El programa o partida seleccionado no es válido.')

    # =========================================================================
    # E. RELACIÓN NIVEL - META
    # =========================================================================
    def list_nivel_metas(self, token):
        sql = '''SELECT nm.nivel_id, nm.meta_id, nm.actualizado_en,
                        n.nombre AS nivel_nombre, n.activo AS nivel_activo,
                        m.codigo AS meta_codigo, m.descripcion AS meta_descripcion, m.activo AS meta_activo
                 FROM nivel_metas nm
                 JOIN niveles n ON n.id = nm.nivel_id
                 JOIN metas m ON m.id = nm.meta_id
                 ORDER BY n.nombre ASC'''
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql).fetchall()

    def set_nivel_meta(self, token, nivel_id, meta_id):
        nivel_id = int(nivel_id)
        meta_id = int(meta_id)
        try:
            with self.auth.data_transaction(token, 'catalogos') as (conn, _):
                if not conn.execute('SELECT 1 FROM niveles WHERE id = %s', (nivel_id,)).fetchone():
                    raise UserError('El nivel seleccionado no existe.')
                if not conn.execute('SELECT 1 FROM metas WHERE id = %s', (meta_id,)).fetchone():
                    raise UserError('La meta seleccionada no existe.')
                conn.execute(
                    '''INSERT INTO nivel_metas(nivel_id, meta_id, actualizado_en)
                       VALUES (%s, %s, now())
                       ON CONFLICT (nivel_id) DO UPDATE SET meta_id = EXCLUDED.meta_id, actualizado_en = now()''',
                    (nivel_id, meta_id)
                )
        except ForeignKeyViolation:
            raise UserError('El nivel o meta seleccionado no es válido.')

    def remove_nivel_meta(self, token, nivel_id):
        nivel_id = int(nivel_id)
        with self.auth.data_transaction(token, 'catalogos') as (conn, _):
            conn.execute('DELETE FROM nivel_metas WHERE nivel_id = %s', (nivel_id,))

    def resolver_meta_institucion(self, token, institucion_id):
        """Resolución de meta: toma la meta propia de la IE si existe; si no, la del nivel asociado."""
        sql = '''SELECT inst.id AS institucion_id, inst.nombre AS institucion_nombre,
                        COALESCE(inst.meta_id, nm.meta_id) AS meta_resuelta_id,
                        m.codigo AS meta_codigo, m.descripcion AS meta_descripcion,
                        CASE WHEN inst.meta_id IS NOT NULL THEN 'INSTITUCION' ELSE 'NIVEL' END AS origen_resolucion
                 FROM instituciones inst
                 LEFT JOIN nivel_metas nm ON nm.nivel_id = inst.nivel_id
                 LEFT JOIN metas m ON m.id = COALESCE(inst.meta_id, nm.meta_id)
                 WHERE inst.id = %s'''
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, (institucion_id,)).fetchone()

    def resolver_meta_area(self, token, area_id):
        """Resolución de meta para área de Sede."""
        sql = '''SELECT a.id AS area_id, a.nombre AS area_nombre,
                        a.meta_id AS meta_resuelta_id,
                        m.codigo AS meta_codigo, m.descripcion AS meta_descripcion,
                        'AREA' AS origen_resolucion
                 FROM areas_sede a
                 LEFT JOIN metas m ON m.id = a.meta_id
                 WHERE a.id = %s'''
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, (area_id,)).fetchone()

    # =========================================================================
    # F. INSTITUCIONES EDUCATIVAS
    # =========================================================================
    def list_instituciones(self, token, solo_activas=False, query=None, nivel_id=None):
        sql = '''SELECT i.id, i.codigo_modular, i.nombre, i.nivel_id, i.distrito,
                        i.meta_id, i.observaciones, i.activo, i.creado_en, i.actualizado_en,
                        n.nombre AS nivel_nombre,
                        m.codigo AS meta_codigo, m.descripcion AS meta_descripcion,
                        nm.meta_id AS nivel_meta_id,
                        mn.codigo AS nivel_meta_codigo
                 FROM instituciones i
                 JOIN niveles n ON n.id = i.nivel_id
                 LEFT JOIN metas m ON m.id = i.meta_id
                 LEFT JOIN nivel_metas nm ON nm.nivel_id = i.nivel_id
                 LEFT JOIN metas mn ON mn.id = nm.meta_id
                 WHERE 1=1'''
        params = []
        if solo_activas:
            sql += ' AND i.activo = true'
        if nivel_id:
            sql += ' AND i.nivel_id = %s'
            params.append(int(nivel_id))
        if query and query.strip():
            clean_q = f'%{query.strip()}%'
            sql += ' AND (i.codigo_modular ILIKE %s OR i.nombre ILIKE %s OR i.distrito ILIKE %s)'
            params.extend([clean_q, clean_q, clean_q])
        sql += ' ORDER BY i.nombre ASC'
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, params).fetchall()

    def get_institucion(self, token, inst_id):
        sql = '''SELECT i.*, n.nombre AS nivel_nombre, m.codigo AS meta_codigo
                 FROM instituciones i
                 JOIN niveles n ON n.id = i.nivel_id
                 LEFT JOIN metas m ON m.id = i.meta_id
                 WHERE i.id = %s'''
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, (inst_id,)).fetchone()

    def create_institucion(self, token, codigo_modular, nombre, nivel_id, distrito,
                           meta_id=None, observaciones=None):
        codigo_modular = _clean_text(codigo_modular, 'Código modular', 1, 30)
        nombre = _clean_text(nombre, 'Nombre de la institución', 1, 240)
        distrito = _clean_text(distrito, 'Distrito', 1, 120)
        observaciones = _clean_text(observaciones, 'Observaciones', 0, 1000, required=False)
        nivel_id = int(nivel_id)
        meta_id = int(meta_id) if meta_id else None

        try:
            with self.auth.data_transaction(token, 'catalogos') as (conn, _):
                if not conn.execute('SELECT 1 FROM niveles WHERE id = %s', (nivel_id,)).fetchone():
                    raise UserError('El nivel seleccionado no existe.')
                if meta_id and not conn.execute('SELECT 1 FROM metas WHERE id = %s', (meta_id,)).fetchone():
                    raise UserError('La meta seleccionada no existe.')
                row = conn.execute(
                    '''INSERT INTO instituciones(codigo_modular, nombre, nivel_id, distrito, meta_id, observaciones)
                       VALUES (%s, %s, %s, %s, %s, %s) RETURNING id''',
                    (codigo_modular, nombre, nivel_id, distrito, meta_id, observaciones)
                ).fetchone()
                return row['id']
        except UniqueViolation:
            raise UserError(f'Ya existe una institución con el código modular "{codigo_modular}".')
        except ForeignKeyViolation:
            raise UserError('El nivel o meta seleccionado no es válido.')

    def update_institucion(self, token, inst_id, codigo_modular, nombre, nivel_id, distrito,
                           meta_id, observaciones, activo):
        codigo_modular = _clean_text(codigo_modular, 'Código modular', 1, 30)
        nombre = _clean_text(nombre, 'Nombre de la institución', 1, 240)
        distrito = _clean_text(distrito, 'Distrito', 1, 120)
        observaciones = _clean_text(observaciones, 'Observaciones', 0, 1000, required=False)
        nivel_id = int(nivel_id)
        meta_id = int(meta_id) if meta_id else None
        activo = bool(activo)

        try:
            with self.auth.data_transaction(token, 'catalogos') as (conn, _):
                if not conn.execute('SELECT 1 FROM niveles WHERE id = %s', (nivel_id,)).fetchone():
                    raise UserError('El nivel seleccionado no existe.')
                if meta_id and not conn.execute('SELECT 1 FROM metas WHERE id = %s', (meta_id,)).fetchone():
                    raise UserError('La meta seleccionada no existe.')
                res = conn.execute(
                    '''UPDATE instituciones
                       SET codigo_modular = %s, nombre = %s, nivel_id = %s, distrito = %s,
                           meta_id = %s, observaciones = %s, activo = %s
                       WHERE id = %s RETURNING id''',
                    (codigo_modular, nombre, nivel_id, distrito, meta_id, observaciones, activo, inst_id)
                ).fetchone()
                if not res:
                    raise UserError('Institución no encontrada.')
        except UniqueViolation:
            raise UserError(f'Ya existe otra institución con el código modular "{codigo_modular}".')
        except ForeignKeyViolation:
            raise UserError('El nivel o meta seleccionado no es válido.')

    # =========================================================================
    # G. ÁREAS DE SEDE
    # =========================================================================
    def list_areas_sede(self, token, solo_activas=False):
        sql = '''SELECT a.id, a.nombre, a.meta_id, a.activo, a.creado_en, a.actualizado_en,
                        m.codigo AS meta_codigo, m.descripcion AS meta_descripcion
                 FROM areas_sede a
                 LEFT JOIN metas m ON m.id = a.meta_id'''
        if solo_activas:
            sql += ' WHERE a.activo = true'
        sql += ' ORDER BY a.nombre ASC'
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql).fetchall()

    def get_area_sede(self, token, area_id):
        sql = '''SELECT a.*, m.codigo AS meta_codigo FROM areas_sede a
                 LEFT JOIN metas m ON m.id = a.meta_id WHERE a.id = %s'''
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, (area_id,)).fetchone()

    def create_area_sede(self, token, nombre, meta_id=None):
        nombre = _clean_text(nombre, 'Nombre del área', 1, 150)
        meta_id = int(meta_id) if meta_id else None
        try:
            with self.auth.data_transaction(token, 'catalogos') as (conn, _):
                if meta_id and not conn.execute('SELECT 1 FROM metas WHERE id = %s', (meta_id,)).fetchone():
                    raise UserError('La meta seleccionada no existe.')
                row = conn.execute(
                    'INSERT INTO areas_sede(nombre, meta_id) VALUES (%s, %s) RETURNING id',
                    (nombre, meta_id)
                ).fetchone()
                return row['id']
        except UniqueViolation:
            raise UserError(f'Ya existe un área con el nombre "{nombre}".')
        except ForeignKeyViolation:
            raise UserError('La meta seleccionada no es válida.')

    def update_area_sede(self, token, area_id, nombre, meta_id, activo):
        nombre = _clean_text(nombre, 'Nombre del área', 1, 150)
        meta_id = int(meta_id) if meta_id else None
        activo = bool(activo)
        try:
            with self.auth.data_transaction(token, 'catalogos') as (conn, _):
                if meta_id and not conn.execute('SELECT 1 FROM metas WHERE id = %s', (meta_id,)).fetchone():
                    raise UserError('La meta seleccionada no existe.')
                res = conn.execute(
                    'UPDATE areas_sede SET nombre = %s, meta_id = %s, activo = %s WHERE id = %s RETURNING id',
                    (nombre, meta_id, activo, area_id)
                ).fetchone()
                if not res:
                    raise UserError('Área de Sede no encontrada.')
        except UniqueViolation:
            raise UserError(f'Ya existe otra área con el nombre "{nombre}".')
        except ForeignKeyViolation:
            raise UserError('La meta seleccionada no es válida.')

    # =========================================================================
    # H. CARGOS
    # =========================================================================
    def list_cargos(self, token, solo_activos=False):
        sql = 'SELECT id, nombre, activo, creado_en, actualizado_en FROM cargos'
        if solo_activos:
            sql += ' WHERE activo = true'
        sql += ' ORDER BY nombre ASC'
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql).fetchall()

    def create_cargo(self, token, nombre):
        nombre = _clean_text(nombre, 'Nombre del cargo', 1, 150)
        try:
            with self.auth.data_transaction(token, 'catalogos') as (conn, _):
                row = conn.execute('INSERT INTO cargos(nombre) VALUES (%s) RETURNING id', (nombre,)).fetchone()
                return row['id']
        except UniqueViolation:
            raise UserError(f'Ya existe un cargo con el nombre "{nombre}".')

    def update_cargo(self, token, cargo_id, nombre, activo):
        nombre = _clean_text(nombre, 'Nombre del cargo', 1, 150)
        activo = bool(activo)
        try:
            with self.auth.data_transaction(token, 'catalogos') as (conn, _):
                res = conn.execute(
                    'UPDATE cargos SET nombre = %s, activo = %s WHERE id = %s RETURNING id',
                    (nombre, activo, cargo_id)
                ).fetchone()
                if not res:
                    raise UserError('Cargo no encontrado.')
        except UniqueViolation:
            raise UserError(f'Ya existe otro cargo con el nombre "{nombre}".')

    # =========================================================================
    # I. CATEGORÍAS REMUNERATIVAS
    # =========================================================================
    def list_categorias(self, token, solo_activas=False):
        sql = 'SELECT id, codigo, descripcion, activo, creado_en, actualizado_en FROM categorias'
        if solo_activas:
            sql += ' WHERE activo = true'
        sql += ' ORDER BY codigo ASC'
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql).fetchall()

    def create_categoria(self, token, codigo, descripcion):
        codigo = _clean_text(codigo, 'Código de categoría', 1, 50)
        descripcion = _clean_text(descripcion, 'Descripción de categoría', 1, 150)
        try:
            with self.auth.data_transaction(token, 'catalogos') as (conn, _):
                row = conn.execute(
                    'INSERT INTO categorias(codigo, descripcion) VALUES (%s, %s) RETURNING id',
                    (codigo, descripcion)
                ).fetchone()
                return row['id']
        except UniqueViolation:
            raise UserError(f'Ya existe una categoría con el código "{codigo}".')

    def update_categoria(self, token, categoria_id, codigo, descripcion, activo):
        codigo = _clean_text(codigo, 'Código de categoría', 1, 50)
        descripcion = _clean_text(descripcion, 'Descripción de categoría', 1, 150)
        activo = bool(activo)
        try:
            with self.auth.data_transaction(token, 'catalogos') as (conn, _):
                res = conn.execute(
                    'UPDATE categorias SET codigo = %s, descripcion = %s, activo = %s WHERE id = %s RETURNING id',
                    (codigo, descripcion, activo, categoria_id)
                ).fetchone()
                if not res:
                    raise UserError('Categoría no encontrada.')
        except UniqueViolation:
            raise UserError(f'Ya existe otra categoría con el código "{codigo}".')

    # =========================================================================
    # J. SITUACIONES LABORALES
    # =========================================================================
    def list_situaciones(self, token, solo_activas=False):
        sql = 'SELECT id, nombre, activo, creado_en, actualizado_en FROM situaciones'
        if solo_activas:
            sql += ' WHERE activo = true'
        sql += ' ORDER BY nombre ASC'
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql).fetchall()

    def create_situacion(self, token, nombre):
        nombre = _clean_text(nombre, 'Nombre de la situación laboral', 1, 120)
        try:
            with self.auth.data_transaction(token, 'catalogos') as (conn, _):
                row = conn.execute('INSERT INTO situaciones(nombre) VALUES (%s) RETURNING id', (nombre,)).fetchone()
                return row['id']
        except UniqueViolation:
            raise UserError(f'Ya existe una situación laboral con el nombre "{nombre}".')

    def update_situacion(self, token, situacion_id, nombre, activo):
        nombre = _clean_text(nombre, 'Nombre de la situación laboral', 1, 120)
        activo = bool(activo)
        try:
            with self.auth.data_transaction(token, 'catalogos') as (conn, _):
                res = conn.execute(
                    'UPDATE situaciones SET nombre = %s, activo = %s WHERE id = %s RETURNING id',
                    (nombre, activo, situacion_id)
                ).fetchone()
                if not res:
                    raise UserError('Situación laboral no encontrada.')
        except UniqueViolation:
            raise UserError(f'Ya existe otra situación laboral con el nombre "{nombre}".')

    # =========================================================================
    # K. SUBTIPOS DE TRABAJADOR
    # =========================================================================
    def list_subtipos(self, token, solo_activos=False):
        sql = 'SELECT id, nombre, activo, creado_en, actualizado_en FROM subtipos_trabajador'
        if solo_activos:
            sql += ' WHERE activo = true'
        sql += ' ORDER BY nombre ASC'
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql).fetchall()

    def create_subtipo(self, token, nombre):
        nombre = _clean_text(nombre, 'Nombre del subtipo', 1, 120)
        try:
            with self.auth.data_transaction(token, 'catalogos') as (conn, _):
                row = conn.execute('INSERT INTO subtipos_trabajador(nombre) VALUES (%s) RETURNING id', (nombre,)).fetchone()
                return row['id']
        except UniqueViolation:
            raise UserError(f'Ya existe un subtipo con el nombre "{nombre}".')

    def update_subtipo(self, token, subtipo_id, nombre, activo):
        nombre = _clean_text(nombre, 'Nombre del subtipo', 1, 120)
        activo = bool(activo)
        try:
            with self.auth.data_transaction(token, 'catalogos') as (conn, _):
                res = conn.execute(
                    'UPDATE subtipos_trabajador SET nombre = %s, activo = %s WHERE id = %s RETURNING id',
                    (nombre, activo, subtipo_id)
                ).fetchone()
                if not res:
                    raise UserError('Subtipo no encontrado.')
        except UniqueViolation:
            raise UserError(f'Ya existe otro subtipo con el nombre "{nombre}".')

    # =========================================================================
    # L. FIRMAS MAESTRAS
    # =========================================================================
    def list_firmas(self, token, solo_activas=False):
        sql = 'SELECT id, nombre_completo, cargo, activo, creado_en, actualizado_en FROM firmas'
        if solo_activas:
            sql += ' WHERE activo = true'
        sql += ' ORDER BY id ASC'
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql).fetchall()

    def create_firma(self, token, nombre_completo, cargo):
        nombre_completo = _clean_text(nombre_completo, 'Nombre de la firma', 1, 200)
        cargo = _clean_text(cargo, 'Cargo de la firma', 1, 200)
        with self.auth.data_transaction(token, 'catalogos') as (conn, _):
            row = conn.execute(
                'INSERT INTO firmas(nombre_completo, cargo) VALUES (%s, %s) RETURNING id',
                (nombre_completo, cargo)
            ).fetchone()
            return row['id']

    def update_firma(self, token, firma_id, nombre_completo, cargo, activo):
        nombre_completo = _clean_text(nombre_completo, 'Nombre de la firma', 1, 200)
        cargo = _clean_text(cargo, 'Cargo de la firma', 1, 200)
        activo = bool(activo)
        with self.auth.data_transaction(token, 'catalogos') as (conn, _):
            res = conn.execute(
                'UPDATE firmas SET nombre_completo = %s, cargo = %s, activo = %s WHERE id = %s RETURNING id',
                (nombre_completo, cargo, activo, firma_id)
            ).fetchone()
            if not res:
                raise UserError('Firma no encontrada.')

    # =========================================================================
    # M. CONFIGURACIÓN E IDENTIDAD INSTITUCIONAL
    # =========================================================================
    def get_configuracion(self, token):
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            row = conn.execute('''SELECT c.*, a.nombre_original AS logo_nombre
                                  FROM configuracion_institucional c
                                  LEFT JOIN archivos a ON a.id = c.logo_archivo_id
                                  WHERE c.id = 1''').fetchone()
            if not row:
                return {
                    'id': 1,
                    'nombre_institucion': 'UGEL CHEPÉN',
                    'nombre_sistema': 'Sistema de Gestión de Planillas CAFAE',
                    'zona_horaria': 'America/Lima',
                    'logo_archivo_id': None,
                    'logo_nombre': None,
                    'actualizado_en': None,
                }
            return row

    def update_configuracion(self, token, nombre_institucion, nombre_sistema,
                             zona_horaria='America/Lima', logo_archivo_id=None):
        nombre_institucion = _clean_text(nombre_institucion, 'Nombre de la institución', 2, 200)
        nombre_sistema = _clean_text(nombre_sistema, 'Nombre del sistema', 2, 200)
        zona_horaria = _clean_text(zona_horaria, 'Zona horaria', 1, 80)
        try:
            ZoneInfo(zona_horaria)
        except (ZoneInfoNotFoundError, ValueError):
            raise UserError(f'Zona horaria inválida: "{zona_horaria}".')

        logo_archivo_id = int(logo_archivo_id) if logo_archivo_id else None

        with self.auth.data_transaction(token, 'catalogos') as (conn, user):
            if logo_archivo_id:
                if not conn.execute('SELECT 1 FROM archivos WHERE id = %s', (logo_archivo_id,)).fetchone():
                    raise UserError('El archivo de logotipo no existe.')
            conn.execute(
                '''INSERT INTO configuracion_institucional(id, nombre_institucion, nombre_sistema,
                                                         zona_horaria, logo_archivo_id, actualizado_por, actualizado_en)
                   VALUES (1, %s, %s, %s, %s, %s, now())
                   ON CONFLICT (id) DO UPDATE SET
                       nombre_institucion = EXCLUDED.nombre_institucion,
                       nombre_sistema = EXCLUDED.nombre_sistema,
                       zona_horaria = EXCLUDED.zona_horaria,
                       logo_archivo_id = EXCLUDED.logo_archivo_id,
                       actualizado_por = EXCLUDED.actualizado_por,
                       actualizado_en = now()''',
                (nombre_institucion, nombre_sistema, zona_horaria, logo_archivo_id, user['id'])
            )
