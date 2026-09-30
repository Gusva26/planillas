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
                     accion=None, resultado=None, limite=100):
        sql = '''SELECT a.id, a.fecha_hora, a.usuario_id, a.usuario_nombre,
                        a.accion, a.entidad, a.entidad_id, a.descripcion,
                        a.resultado, a.correlacion,
                        (SELECT count(*) FROM auditoria_cambios c WHERE c.auditoria_id = a.id) AS total_cambios
                 FROM auditoria a
                 WHERE 1=1'''
        params = []
        if entidad:
            sql += ' AND a.entidad = %s'
            params.append(entidad)
        if usuario_id:
            sql += ' AND a.usuario_id = %s'
            params.append(int(usuario_id))
        if accion:
            sql += ' AND a.accion ILIKE %s'
            params.append(f'%{accion.strip()}%')
        if resultado:
            sql += ' AND a.resultado = %s'
            params.append(resultado)

        sql += ' ORDER BY a.fecha_hora DESC LIMIT %s'
        params.append(min(int(limite), 500))

        with self.auth.data_transaction(token, 'auditoria') as (conn, _):
            return conn.execute(sql, params).fetchall()

    def get_cambios(self, token, auditoria_id):
        auditoria_id = int(auditoria_id)
        sql = '''SELECT id, auditoria_id, entidad, entidad_id, campo, valor_anterior, valor_nuevo
                 FROM auditoria_cambios
                 WHERE auditoria_id = %s
                 ORDER BY id ASC'''
        with self.auth.data_transaction(token, 'auditoria') as (conn, _):
            return conn.execute(sql, (auditoria_id,)).fetchall()
