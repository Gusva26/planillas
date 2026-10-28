"""Servicio de Auditoría Administrativa (Etapa 15).
Permite consultar el registro append-only de eventos y los cambios específicos por campo.
Solo accesible para ADMINISTRADOR.
"""
from cafae.auth import AuthService
from cafae.security import AccessError, UserError


class AuditoriaService:
    def __init__(self, auth_service=None):
        self.auth = auth_service or AuthService()

    def list_eventos(self, token, entidad=None, usuario_id=None,
                     accion=None, resultado=None, limite=100, desplazamiento=0):
        """Devuelve una página de eventos y el total que cumple el filtro."""
        filtros = ['1=1']
        params = []
        if entidad:
            filtros.append('a.entidad = %s')
            params.append(entidad)
        if usuario_id:
            filtros.append('a.usuario_id = %s')
            params.append(int(usuario_id))
        if accion:
            filtros.append('a.accion ILIKE %s')
            params.append(f'%{accion.strip()}%')
        if resultado:
            filtros.append('a.resultado = %s')
            params.append(resultado)

        where = ' AND '.join(filtros)
        limite = min(int(limite), 500)
        desplazamiento = max(int(desplazamiento), 0)

        sql = f'''SELECT a.id, a.fecha_hora, a.usuario_id, a.usuario_nombre,
                        a.accion, a.entidad, a.entidad_id, a.descripcion,
                        a.resultado, a.correlacion,
                        (SELECT count(*) FROM auditoria_cambios c WHERE c.auditoria_id = a.id) AS total_cambios
                 FROM auditoria a
                 WHERE {where}
                 ORDER BY a.fecha_hora DESC, a.id DESC
                 LIMIT %s OFFSET %s'''
        sql_total = f'SELECT count(*) AS total FROM auditoria a WHERE {where}'

        with self.auth.data_transaction(token, 'auditoria') as (conn, _):
            total = conn.execute(sql_total, params).fetchone()['total']
            filas = conn.execute(sql, [*params, limite, desplazamiento]).fetchall()

        return {
            'items': [
                {**dict(fila), 'correlacion': str(fila['correlacion'])}
                for fila in filas
            ],
            'total': int(total),
            'limite': limite,
            'desplazamiento': desplazamiento,
        }

    def get_cambios(self, token, auditoria_id):
        auditoria_id = int(auditoria_id)
        sql = '''SELECT id, auditoria_id, entidad, entidad_id, campo, valor_anterior, valor_nuevo
                 FROM auditoria_cambios
                 WHERE auditoria_id = %s
                 ORDER BY id ASC'''
        with self.auth.data_transaction(token, 'auditoria') as (conn, _):
            return conn.execute(sql, (auditoria_id,)).fetchall()
