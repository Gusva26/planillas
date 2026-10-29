"""Se ejecuta solo mediante scripts/test_auth.py, en una base temporal."""
import concurrent.futures
import os
from pathlib import Path
import secrets
import sys
import unittest
import uuid

sys.path.insert(0, '/app')
from psycopg.errors import CheckViolation, InsufficientPrivilege

from cafae.auth import AuthService, LOGIN_ERROR
from cafae.db import transaction
from cafae.security import (AccessError, PERMISSIONS, SessionError, UserError, digest,
                            hash_password, verify_password)

if not os.environ.get('CAFAE_DB_NAME', '').startswith('cafae_test_'):
    raise SystemExit('Estas pruebas requieren una base cafae_test_* aislada.')

SERVICE = AuthService()
PASSWORD = secrets.token_urlsafe(24)
ADMIN_ID = None


class Authentication(unittest.TestCase):
    def setUp(self):
        self.origin = uuid.uuid4().hex
        self.admin = SERVICE.login('admin_pruebas', PASSWORD, self.origin)

    def new_user(self, role='CONSULTA', *, changed=True):
        username = 'u_' + uuid.uuid4().hex[:12]
        password = secrets.token_urlsafe(24)
        user_id = SERVICE.create_user(self.admin, username, 'Persona sintética', role, password)
        token = SERVICE.login(username, password, self.origin)
        if changed:
            new = secrets.token_urlsafe(24)
            SERVICE.change_password(token, password, new)
            password = new
            token = SERVICE.login(username, password, self.origin)
        return user_id, username, password, token

    def row(self, user_id):
        return next(u for u in SERVICE.list_users(self.admin) if u['id'] == user_id)

    def test_hash_argon2_salt_y_verificacion(self):
        one, two = hash_password(PASSWORD), hash_password(PASSWORD)
        self.assertTrue(one.startswith('$argon2id$'))
        self.assertNotEqual(one, two)
        self.assertTrue(verify_password(one, PASSWORD))
        self.assertFalse(verify_password(one, secrets.token_urlsafe(24)))
        self.assertFalse(verify_password('hash_invalido', PASSWORD))
        for password in ('', 'x' * 11, 'x' * 129, ' ' * 12):
            with self.assertRaises(UserError):
                hash_password(password)

    def test_bootstrap_solo_una_vez(self):
        with self.assertRaises(UserError):
            SERVICE.bootstrap('otro_admin', 'Segundo', PASSWORD)

    def test_login_normalizado_y_token_solo_hash(self):
        token = SERVICE.login('  ADMIN_PRUEBAS  ', PASSWORD, self.origin)
        self.assertEqual(SERVICE.current_user(token)['id'], ADMIN_ID)
        with transaction() as conn:
            row = conn.execute('SELECT token_hash FROM sesiones WHERE token_hash=%s', (digest(token),)).fetchone()
            self.assertNotEqual(row['token_hash'], token)
        self.assertNotIn('password_hash', SERVICE.current_user(token))
        self.assertNotIn('password_hash', SERVICE.list_users(token)[0])

    def test_error_generico_e_inyeccion(self):
        for username in ('inexistente', 'admin_pruebas', "' OR 1=1 --"):
            with self.assertRaises(AccessError) as ctx:
                SERVICE.login(username, secrets.token_urlsafe(24), self.origin)
            self.assertEqual(str(ctx.exception), LOGIN_ERROR)

    def test_limite_intentos_por_cuenta(self):
        _, username, password, _ = self.new_user()
        for _ in range(5):
            with self.assertRaises(AccessError):
                SERVICE.login(username, secrets.token_urlsafe(24), uuid.uuid4().hex)
        with self.assertRaises(AccessError):
            SERVICE.login(username, password, self.origin)
        with transaction() as conn:
            conn.execute("UPDATE acceso_intentos SET inicio=now()-interval '16 minutes' WHERE clave=%s",
                         (digest('cuenta:' + username),))
        self.assertTrue(SERVICE.login(username, password, self.origin))

    def test_limite_por_origen_aunque_cambie_cuenta(self):
        with transaction() as conn:
            conn.execute('INSERT INTO acceso_intentos(clave,fallos) VALUES(%s,30) ON CONFLICT(clave) DO UPDATE SET fallos=30', (digest('origen:' + self.origin),))
        with self.assertRaises(AccessError):
            SERVICE.login('admin_pruebas', PASSWORD, self.origin)

    def test_logout_revoca(self):
        SERVICE.logout(self.admin)
        with self.assertRaises(SessionError):
            SERVICE.current_user(self.admin)

    def test_vencimiento_absoluto(self):
        with transaction() as conn:
            conn.execute("UPDATE sesiones SET creada_en=now()-interval '10 hours',expira_en=now()-interval '1 hour' WHERE token_hash=%s", (digest(self.admin),))
        with self.assertRaises(SessionError):
            SERVICE.current_user(self.admin)

    def test_vencimiento_inactividad(self):
        with transaction() as conn:
            conn.execute("UPDATE sesiones SET ultimo_acceso_en=now()-interval '31 minutes' WHERE token_hash=%s", (digest(self.admin),))
        with self.assertRaises(SessionError):
            SERVICE.current_user(self.admin)

    def test_token_falso(self):
        for value in (None, '', secrets.token_urlsafe(32)):
            with self.assertRaises(SessionError):
                SERVICE.current_user(value)

    def test_cambio_obligatorio_y_revocacion_de_todas(self):
        user_id, username, password, token = self.new_user(changed=False)
        second = SERVICE.login(username, password, self.origin)
        with self.assertRaises(AccessError):
            SERVICE.require_permission(token, 'consultar')
        new = secrets.token_urlsafe(24)
        SERVICE.change_password(token, password, new)
        for old in (token, second):
            with self.assertRaises(SessionError):
                SERVICE.current_user(old)
        new_token = SERVICE.login(username, new, self.origin)
        self.assertFalse(SERVICE.current_user(new_token)['debe_cambiar_password'])
        self.assertEqual(SERVICE.require_permission(new_token, 'consultar')['id'], user_id)

    def test_cambio_exige_password_actual_y_diferente(self):
        _, _, password, token = self.new_user()
        with self.assertRaises(AccessError):
            SERVICE.change_password(token, secrets.token_urlsafe(24), secrets.token_urlsafe(24))
        with self.assertRaises(UserError):
            SERVICE.change_password(token, password, password)
        self.assertTrue(SERVICE.current_user(token))

    def test_roles_en_servicio_sin_depender_de_ui(self):
        for role in ('CONSULTA', 'PLANILLAS'):
            _, _, _, token = self.new_user(role)
            for permission, roles in PERMISSIONS.items():
                if role in roles:
                    self.assertEqual(SERVICE.require_permission(token, permission)['rol'], role)
                else:
                    with self.assertRaises(AccessError):
                        SERVICE.require_permission(token, permission)
            with self.assertRaises(AccessError):
                SERVICE.create_user(token, 'intruso', 'Intruso', 'ADMINISTRADOR', PASSWORD)
            with self.assertRaises(AccessError):
                SERVICE.list_users(token)
            with self.assertRaises(AccessError):
                SERVICE.require_permission(token, 'permiso_inventado')

    def test_rol_sql_restringido_en_operacion(self):
        for role, sql_role in [('CONSULTA', 'cafae_consulta'), ('PLANILLAS', 'cafae_operador')]:
            _, _, _, token = self.new_user(role)
            with SERVICE.data_transaction(token, 'consultar') as (conn, _):
                self.assertEqual(conn.execute('SELECT current_user AS rol').fetchone()['rol'], sql_role)
            with self.assertRaises(InsufficientPrivilege):
                with SERVICE.data_transaction(token, 'consultar') as (conn, _):
                    conn.execute('SELECT password_hash FROM usuarios')
        with transaction() as conn:
            flags = conn.execute("SELECT rolsuper,rolcreatedb,rolcreaterole,rolinherit FROM pg_roles WHERE rolname='cafae_service'").fetchone()
            self.assertFalse(any(flags.values()))

    def test_desactivacion_revoca_y_rechaza_login(self):
        user_id, username, password, token = self.new_user()
        row = self.row(user_id)
        SERVICE.update_user(self.admin, user_id, row['revision'], row['nombre_completo'], row['rol'], False)
        with self.assertRaises(SessionError):
            SERVICE.current_user(token)
        with self.assertRaises(AccessError) as ctx:
            SERVICE.login(username, password, self.origin)
        self.assertEqual(str(ctx.exception), LOGIN_ERROR)

    def test_cambio_rol_revoca_sesion_vieja(self):
        user_id, username, password, token = self.new_user('PLANILLAS')
        row = self.row(user_id)
        SERVICE.update_user(self.admin, user_id, row['revision'], row['nombre_completo'], 'CONSULTA', True)
        with self.assertRaises(SessionError):
            SERVICE.require_permission(token, 'editar_planillas')
        new = SERVICE.login(username, password, self.origin)
        with self.assertRaises(AccessError):
            SERVICE.require_permission(new, 'editar_planillas')

    def test_restablecer_password(self):
        user_id, username, password, token = self.new_user()
        temporary = secrets.token_urlsafe(24)
        SERVICE.reset_password(self.admin, user_id, self.row(user_id)['revision'], temporary)
        with self.assertRaises(SessionError):
            SERVICE.current_user(token)
        with self.assertRaises(AccessError):
            SERVICE.login(username, password, self.origin)
        new = SERVICE.login(username, temporary, self.origin)
        self.assertTrue(SERVICE.current_user(new)['debe_cambiar_password'])

    def test_ultimo_admin_protegido_servicio_y_sql(self):
        row = self.row(ADMIN_ID)
        for role, active in [('CONSULTA', True), ('ADMINISTRADOR', False)]:
            with self.assertRaises(UserError):
                SERVICE.update_user(self.admin, ADMIN_ID, row['revision'], row['nombre_completo'], role, active)
        with self.assertRaises(CheckViolation):
            with transaction() as conn:
                conn.execute('UPDATE usuarios SET activo=false WHERE id=%s', (ADMIN_ID,))

    def test_revision_evitar_sobrescritura(self):
        user_id, _, _, _ = self.new_user()
        row = self.row(user_id)
        SERVICE.update_user(self.admin, user_id, row['revision'], 'Nuevo nombre', 'CONSULTA', True)
        with self.assertRaises(UserError):
            SERVICE.update_user(self.admin, user_id, row['revision'], 'Nombre obsoleto', 'CONSULTA', True)
        self.assertEqual(self.row(user_id)['nombre_completo'], 'Nuevo nombre')

    def test_usuario_duplicado_normalizado(self):
        with self.assertRaises(UserError):
            SERVICE.create_user(self.admin, ' ADMIN_PRUEBAS ', 'Duplicado', 'CONSULTA', PASSWORD)

    def test_auditoria_sin_secretos_y_rechazos_persistidos(self):
        with self.assertRaises(AccessError):
            SERVICE.login('inexistente_audit', PASSWORD, self.origin)
        with SERVICE.data_transaction(self.admin, 'auditoria') as (conn, _):
            self.assertTrue(conn.execute("SELECT EXISTS(SELECT 1 FROM auditoria WHERE accion='LOGIN' AND resultado='RECHAZADO') AS ok").fetchone()['ok'])
            self.assertFalse(conn.execute("SELECT EXISTS(SELECT 1 FROM auditoria_cambios WHERE campo IN ('password_hash','token_hash')) AS existe").fetchone()['existe'])
            self.assertFalse(conn.execute('SELECT EXISTS(SELECT 1 FROM auditoria WHERE descripcion LIKE %s) AS existe', ('%' + PASSWORD + '%',)).fetchone()['existe'])

    def test_dos_guardados_concurrentes(self):
        user_id, _, _, _ = self.new_user()
        row = self.row(user_id)
        def write(name):
            try:
                SERVICE.update_user(self.admin, user_id, row['revision'], name, 'CONSULTA', True)
                return 'ok'
            except UserError:
                return 'conflicto'
        with concurrent.futures.ThreadPoolExecutor(2) as pool:
            results = list(pool.map(write, ['Nombre uno', 'Nombre dos']))
        self.assertCountEqual(results, ['ok', 'conflicto'])

    def test_dos_admin_concurrentes_conservan_uno_activo(self):
        second_id, username, password, second = self.new_user('ADMINISTRADOR')
        primary_row, second_row = self.row(ADMIN_ID), self.row(second_id)
        def deactivate(args):
            token, row = args
            try:
                SERVICE.update_user(token, row['id'], row['revision'], row['nombre_completo'], row['rol'], False)
                return 'ok'
            except UserError:
                return 'rechazado'
        try:
            with concurrent.futures.ThreadPoolExecutor(2) as pool:
                results = list(pool.map(deactivate, [(self.admin, primary_row), (second, second_row)]))
            self.assertCountEqual(results, ['ok', 'rechazado'])
            with transaction() as conn:
                count = conn.execute("SELECT count(*) AS n FROM usuarios u JOIN roles r ON r.id=u.rol_id WHERE u.activo AND r.codigo='ADMINISTRADOR'").fetchone()['n']
                self.assertEqual(count, 1)
        finally:
            with transaction() as conn:
                primary_active = conn.execute('SELECT activo FROM usuarios WHERE id=%s', (ADMIN_ID,)).fetchone()['activo']
            if not primary_active:
                survivor = SERVICE.login(username, password, self.origin)
                row = next(u for u in SERVICE.list_users(survivor) if u['id'] == ADMIN_ID)
                SERVICE.update_user(survivor, ADMIN_ID, row['revision'], row['nombre_completo'], 'ADMINISTRADOR', True)
            self.admin = SERVICE.login('admin_pruebas', PASSWORD, self.origin)
            row = self.row(second_id)
            SERVICE.update_user(self.admin, second_id, row['revision'], row['nombre_completo'], 'ADMINISTRADOR', False)


if __name__ == '__main__':
    # Dos arranques locales simultáneos: exactamente uno crea el administrador.
    def bootstrap(_):
        try:
            return SERVICE.bootstrap('admin_pruebas', 'Administrador sintético', PASSWORD)
        except UserError:
            return None
    with concurrent.futures.ThreadPoolExecutor(2) as pool:
        results = list(pool.map(bootstrap, range(2)))
    assert sum(value is not None for value in results) == 1
    ADMIN_ID = next(value for value in results if value is not None)
    print('OK: bootstrap simultáneo permite un solo administrador inicial', flush=True)
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(Authentication))
    if not result.wasSuccessful():
        sys.exit(1)
