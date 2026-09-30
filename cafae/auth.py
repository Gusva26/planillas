"""Autenticación local. Toda operación pública recibe un token, nunca un rol del cliente."""
import secrets
import uuid
from contextlib import contextmanager

from psycopg.errors import UniqueViolation

from cafae.db import transaction
from cafae.security import (AccessError, DUMMY_HASH, HASHER, PERMISSIONS, ROLES,
                            SessionError, UserError, digest, hash_password,
                            normalize_username, validate_name, verify_password)

ADMIN_LOCK = 82609200
LOGIN_ERROR = 'No se pudo iniciar sesión. Revisa tus datos o vuelve a intentarlo más tarde.'
PUBLIC_USER_FIELDS = 'u.id,u.usuario,u.nombre_completo,r.codigo AS rol,u.activo,u.debe_cambiar_password,u.revision'


class AuthService:
    def __init__(self, settings=None):
        self.settings = settings

    def _transaction(self):
        return transaction(self.settings)

    @staticmethod
    def _event(conn, action, result='EXITO', user_id=None, description='Operación de acceso'):
        conn.execute('''INSERT INTO auditoria(usuario_id,usuario_nombre,accion,entidad,entidad_id,
            descripcion,resultado,correlacion)
            VALUES(%s,(SELECT nombre_completo FROM usuarios WHERE id=%s),%s,'acceso',%s,%s,%s,%s)''',
                     (user_id, user_id, action, user_id, description, result, uuid.uuid4()))

    @staticmethod
    def _actor(conn, user_id):
        conn.execute("SELECT set_config('cafae.usuario_id',%s,true)", (str(user_id),))
        conn.execute("SELECT set_config('cafae.correlacion',%s,true)", (str(uuid.uuid4()),))

    def bootstrap(self, username, name, password):
        """Solo para el comando local; no se expone desde la interfaz web."""
        username, name = normalize_username(username), validate_name(name)
        encoded = hash_password(password)
        with self._transaction() as conn:
            conn.execute('SELECT pg_advisory_xact_lock(%s)', (ADMIN_LOCK,))
            if conn.execute('SELECT EXISTS(SELECT 1 FROM usuarios) AS existe').fetchone()['existe']:
                raise UserError('Ya existen usuarios. El primer administrador no puede crearse de nuevo.')
            user_id = conn.execute('''INSERT INTO usuarios(usuario,nombre_completo,password_hash,rol_id,debe_cambiar_password)
                SELECT %s,%s,%s,id,false FROM roles WHERE codigo='ADMINISTRADOR' RETURNING id''',
                                   (username, name, encoded)).fetchone()['id']
            self._event(conn, 'ADMINISTRADOR_INICIAL', user_id=user_id)
            return user_id

    def login(self, username, password, origin='local'):
        # Origen lo proporciona el servidor (IP de la conexión), nunca un campo del formulario.
        normalized = username.strip().lower()[:256]
        buckets = sorted([(digest('cuenta:' + normalized), 5), (digest('origen:' + origin[:256]), 30)])
        token = None
        with self._transaction() as conn:
            blocked = False
            for key, limit in buckets:
                conn.execute('INSERT INTO acceso_intentos(clave) VALUES(%s) ON CONFLICT DO NOTHING', (key,))
                conn.execute('SELECT clave FROM acceso_intentos WHERE clave=%s FOR UPDATE', (key,))
                row = conn.execute('''UPDATE acceso_intentos SET
                    fallos=CASE WHEN inicio <= now()-interval '15 minutes' THEN 0 ELSE fallos END,
                    inicio=CASE WHEN inicio <= now()-interval '15 minutes' THEN now() ELSE inicio END
                    WHERE clave=%s RETURNING fallos''', (key,)).fetchone()
                blocked = blocked or row['fallos'] >= limit
            if blocked:
                self._event(conn, 'LOGIN_LIMITADO', 'RECHAZADO')
            else:
                user = conn.execute('''SELECT u.* FROM usuarios u
                    WHERE lower(btrim(usuario))=%s FOR UPDATE''', (normalized,)).fetchone()
                correct = verify_password(user['password_hash'] if user else DUMMY_HASH, password)
                if user and user['activo'] and correct:
                    self._actor(conn, user['id'])
                    if HASHER.check_needs_rehash(user['password_hash']):
                        conn.execute('UPDATE usuarios SET password_hash=%s WHERE id=%s',
                                     (hash_password(password), user['id']))
                    token = secrets.token_urlsafe(32)
                    conn.execute('''INSERT INTO sesiones(usuario_id,token_hash,expira_en)
                        VALUES(%s,%s,now()+interval '8 hours')''', (user['id'], digest(token)))
                    # El éxito reinicia la cuenta, pero no permite eludir el límite por origen.
                    conn.execute('UPDATE acceso_intentos SET fallos=0,inicio=now() WHERE clave=%s',
                                 (digest('cuenta:' + normalized),))
                    self._event(conn, 'LOGIN', user_id=user['id'])
                else:
                    for key, _ in buckets:
                        conn.execute('UPDATE acceso_intentos SET fallos=fallos+1 WHERE clave=%s', (key,))
                    self._event(conn, 'LOGIN', 'RECHAZADO')
        if token is None:
            raise AccessError(LOGIN_ERROR)
        return token

    @contextmanager
    def authorized(self, token, permission=None, *, allow_password_change=False, admin_mutation=False):
        """Valida y bloquea identidad antes de trabajar; autorización válida hasta el commit."""
        user = None
        try:
            with self._transaction() as conn:
                if admin_mutation:
                    conn.execute('SELECT pg_advisory_xact_lock(%s)', (ADMIN_LOCK,))
                if not isinstance(token, str) or not 32 <= len(token) <= 128:
                    raise SessionError('Inicia sesión para continuar.')
                user = conn.execute(f'''SELECT {PUBLIC_USER_FIELDS} FROM usuarios u JOIN roles r ON r.id=u.rol_id
                    JOIN sesiones s ON s.usuario_id=u.id WHERE s.token_hash=%s FOR UPDATE OF u''',
                                    (digest(token),)).fetchone()
                session = conn.execute('''SELECT id FROM sesiones WHERE token_hash=%s
                    AND revocada_en IS NULL AND expira_en>clock_timestamp()
                    AND ultimo_acceso_en>clock_timestamp()-interval '30 minutes' FOR UPDATE''',
                                       (digest(token),)).fetchone()
                if not user or not user['activo'] or not session:
                    raise SessionError('Tu sesión venció o fue revocada. Inicia sesión nuevamente.')
                if user['debe_cambiar_password'] and not allow_password_change:
                    raise AccessError('Debes cambiar tu contraseña antes de continuar.')
                if permission and user['rol'] not in PERMISSIONS.get(permission, frozenset()):
                    raise AccessError('Tu rol no permite realizar esta operación.')
                self._actor(conn, user['id'])
                conn.execute('UPDATE sesiones SET ultimo_acceso_en=clock_timestamp() WHERE id=%s', (session['id'],))
                yield conn, user
        except AccessError:
            # Fuera de la transacción abortada para conservar evidencia del rechazo.
            with self._transaction() as conn:
                self._event(conn, 'ACCESO_DENEGADO', 'RECHAZADO', user['id'] if user else None)
            raise

    def current_user(self, token):
        with self.authorized(token, allow_password_change=True) as (_, user):
            return user

    def require_permission(self, token, permission):
        with self.authorized(token, permission) as (_, user):
            return user

    @contextmanager
    def data_transaction(self, token, permission):
        """Entrada para futuros servicios de negocio: permiso y rol SQL en la misma transacción."""
        roles = {'ADMINISTRADOR': 'cafae_admin', 'PLANILLAS': 'cafae_operador', 'CONSULTA': 'cafae_consulta'}
        with self.authorized(token, permission) as (conn, user):
            # El identificador proviene exclusivamente de esta lista interna.
            conn.execute('SET LOCAL ROLE ' + roles[user['rol']])
            yield conn, user

    def logout(self, token):
        if not isinstance(token, str) or len(token) > 128:
            return
        with self._transaction() as conn:
            row = conn.execute('''UPDATE sesiones SET revocada_en=now()
                WHERE token_hash=%s AND revocada_en IS NULL RETURNING usuario_id''', (digest(token),)).fetchone()
            if row:
                self._event(conn, 'LOGOUT', user_id=row['usuario_id'])

    def list_users(self, token):
        with self.authorized(token, 'usuarios') as (conn, _):
            return conn.execute(f'''SELECT {PUBLIC_USER_FIELDS} FROM usuarios u JOIN roles r ON r.id=u.rol_id
                ORDER BY lower(u.usuario)''').fetchall()

    def create_user(self, token, username, name, role, temporary_password):
        username, name = normalize_username(username), validate_name(name)
        if role not in ROLES:
            raise UserError('Selecciona un rol válido.')
        encoded = hash_password(temporary_password)
        try:
            with self.authorized(token, 'usuarios', admin_mutation=True) as (conn, _):
                return conn.execute('''INSERT INTO usuarios(usuario,nombre_completo,password_hash,rol_id,debe_cambiar_password)
                    SELECT %s,%s,%s,id,true FROM roles WHERE codigo=%s RETURNING id''',
                                    (username, name, encoded, role)).fetchone()['id']
        except UniqueViolation:
            raise UserError('Ese nombre de usuario ya existe.') from None

    def update_user(self, token, user_id, revision, name, role, active):
        name = validate_name(name)
        if role not in ROLES or not isinstance(active, bool):
            raise UserError('Selecciona un rol y estado válidos.')
        with self.authorized(token, 'usuarios', admin_mutation=True) as (conn, _):
            target = self._target(conn, user_id, revision)
            if target['activo'] and target['rol'] == 'ADMINISTRADOR' and (not active or role != 'ADMINISTRADOR'):
                count = conn.execute('''SELECT count(*) AS n FROM usuarios u JOIN roles r ON r.id=u.rol_id
                    WHERE u.activo AND r.codigo='ADMINISTRADOR' ''').fetchone()['n']
                if count <= 1:
                    raise UserError('Debes conservar al menos un administrador activo.')
            conn.execute('''UPDATE usuarios SET nombre_completo=%s,rol_id=(SELECT id FROM roles WHERE codigo=%s),
                activo=%s WHERE id=%s''', (name, role, active, user_id))

    @staticmethod
    def _target(conn, user_id, revision):
        target = conn.execute(f'''SELECT {PUBLIC_USER_FIELDS} FROM usuarios u JOIN roles r ON r.id=u.rol_id
            WHERE u.id=%s FOR UPDATE OF u''', (user_id,)).fetchone()
        if not target:
            raise UserError('No se encontró la cuenta seleccionada.')
        if target['revision'] != revision:
            raise UserError('La cuenta cambió. Actualiza la pantalla antes de guardar.')
        return target

    def reset_password(self, token, user_id, revision, temporary_password):
        encoded = hash_password(temporary_password)
        with self.authorized(token, 'usuarios', admin_mutation=True) as (conn, actor):
            self._target(conn, user_id, revision)
            conn.execute('UPDATE usuarios SET password_hash=%s,debe_cambiar_password=true WHERE id=%s',
                         (encoded, user_id))
            self._event(conn, 'RESTABLECER_PASSWORD', user_id=actor['id'],
                        description=f'Acceso restablecido para cuenta {user_id}')

    def change_password(self, token, current_password, new_password):
        encoded = hash_password(new_password)
        with self.authorized(token, allow_password_change=True, admin_mutation=True) as (conn, user):
            old_hash = conn.execute('SELECT password_hash FROM usuarios WHERE id=%s', (user['id'],)).fetchone()['password_hash']
            if not verify_password(old_hash, current_password):
                raise AccessError('La contraseña actual no es correcta.')
            if verify_password(old_hash, new_password):
                raise UserError('Elige una contraseña diferente de la actual.')
            conn.execute('UPDATE usuarios SET password_hash=%s,debe_cambiar_password=false WHERE id=%s', (encoded, user['id']))
            self._event(conn, 'CAMBIAR_PASSWORD', user_id=user['id'])
