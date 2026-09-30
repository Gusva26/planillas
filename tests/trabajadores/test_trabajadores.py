"""Pruebas unitarias y de integración para el Maestro de Trabajadores (Etapa 4).
Se ejecuta contra una base aislada cafae_test_*.
"""
from datetime import date
from decimal import Decimal
import os
import secrets
import sys
import unittest
import uuid

sys.path.insert(0, '/app')

from cafae.auth import AuthService
from cafae.catalogos import CatalogoService
from cafae.trabajadores import TrabajadorService, parse_monto
from cafae.security import AccessError, UserError

if not os.environ.get('CAFAE_DB_NAME', '').startswith('cafae_test_'):
    raise SystemExit('Estas pruebas requieren una base cafae_test_* aislada.')

AUTH = AuthService()
CAT = CatalogoService(AUTH)
TRAB = TrabajadorService(AUTH)
ADMIN_PWD = secrets.token_urlsafe(24)


class TestTrabajadores(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            AUTH.bootstrap('admin_trab', 'Administrador Personal', ADMIN_PWD)
        except UserError:
            pass

    def setUp(self):
        self.origin = uuid.uuid4().hex
        self.admin_token = AUTH.login('admin_trab', ADMIN_PWD, self.origin)

        # Crear catálogos base para vincular
        self.nivel_id = CAT.create_nivel(self.admin_token, f'Nivel {uuid.uuid4().hex[:6]}')
        self.inst_id = CAT.create_institucion(
            self.admin_token, f'0{uuid.uuid4().int % 9000000 + 1000000}',
            'Colegio Nacional', self.nivel_id, 'Chepén'
        )
        self.area_id = CAT.create_area_sede(self.admin_token, f'Área {uuid.uuid4().hex[:6]}')
        self.cargo_id = CAT.create_cargo(self.admin_token, f'Cargo {uuid.uuid4().hex[:6]}')
        self.cat_id = CAT.create_categoria(self.admin_token, f'C_{uuid.uuid4().hex[:4]}', 'Cat Desc')
        self.sit_id = CAT.create_situacion(self.admin_token, f'Sit {uuid.uuid4().hex[:4]}')
        self.sub_id = CAT.create_subtipo(self.admin_token, f'Sub {uuid.uuid4().hex[:4]}')

    def create_user(self, role):
        username = 'u_' + uuid.uuid4().hex[:10]
        temp_pwd = secrets.token_urlsafe(24)
        AUTH.create_user(self.admin_token, username, f'Usuario {role}', role, temp_pwd)
        token = AUTH.login(username, temp_pwd, self.origin)
        new_pwd = secrets.token_urlsafe(24)
        AUTH.change_password(token, temp_pwd, new_pwd)
        return AUTH.login(username, new_pwd, self.origin)

    # -------------------------------------------------------------------------
    # 1. Permisos
    # -------------------------------------------------------------------------
    def test_permisos_maestro_trabajadores(self):
        token_planillas = self.create_user('PLANILLAS')
        token_consulta = self.create_user('CONSULTA')

        # Consulta puede listar
        lista = TRAB.list_trabajadores(token_consulta)
        self.assertIsInstance(lista, list)

        # Planillas puede registrar trabajador
        dni = f'0{uuid.uuid4().int % 9000000 + 1000000}'
        tid = TRAB.create_trabajador(token_planillas, {
            'dni': dni,
            'apellidos': 'Pérez',
            'nombres': 'Juan',
            'tipo': 'IIEE',
            'institucion_id': self.inst_id,
            'cargo_id': self.cargo_id,
            'importe': Decimal('1350.00')
        })
        self.assertGreater(tid, 0)

        # Consulta NO puede registrar trabajador
        with self.assertRaises(AccessError):
            TRAB.create_trabajador(token_consulta, {
                'dni': f'0{uuid.uuid4().int % 9000000 + 1000000}',
                'apellidos': 'Gómez',
                'nombres': 'Ana',
                'tipo': 'IIEE',
                'institucion_id': self.inst_id
            })

    # -------------------------------------------------------------------------
    # 2. Validación de DNI y ceros a la izquierda
    # -------------------------------------------------------------------------
    def test_validacion_dni(self):
        # DNI con 8 dígitos comenzando con cero
        dni_con_cero = '00234567'
        tid = TRAB.create_trabajador(self.admin_token, {
            'dni': dni_con_cero,
            'apellidos': 'Alva',
            'nombres': 'Carlos',
            'tipo': 'IIEE',
            'institucion_id': self.inst_id,
            'importe': Decimal('1200.00')
        })
        t = TRAB.get_trabajador(self.admin_token, tid)
        self.assertEqual(t['dni'], '00234567')

        # DNI duplicado
        with self.assertRaises(UserError) as ctx:
            TRAB.create_trabajador(self.admin_token, {
                'dni': dni_con_cero,
                'apellidos': 'Otro',
                'nombres': 'Nombre',
                'tipo': 'IIEE',
                'institucion_id': self.inst_id
            })
        self.assertIn('Ya existe', str(ctx.exception))

        # DNI con longitud menor a 8 o caracteres no numéricos
        with self.assertRaises(UserError):
            TRAB.create_trabajador(self.admin_token, {
                'dni': '1234567',  # 7 dígitos
                'apellidos': 'Test',
                'nombres': 'Corto',
                'tipo': 'IIEE',
                'institucion_id': self.inst_id
            })

        with self.assertRaises(UserError):
            TRAB.create_trabajador(self.admin_token, {
                'dni': '1234567A',  # Letra
                'apellidos': 'Test',
                'nombres': 'Letra',
                'tipo': 'IIEE',
                'institucion_id': self.inst_id
            })

    # -------------------------------------------------------------------------
    # 3. Separación estricta IIEE vs SEDE
    # -------------------------------------------------------------------------
    def test_separacion_iiee_sede(self):
        # IIEE con área_id debe ser rechazado
        with self.assertRaises(UserError):
            TRAB.create_trabajador(self.admin_token, {
                'dni': f'0{uuid.uuid4().int % 9000000 + 1000000}',
                'apellidos': 'Error',
                'nombres': 'IIEE',
                'tipo': 'IIEE',
                'institucion_id': self.inst_id,
                'area_id': self.area_id
            })

        # SEDE con institucion_id debe ser rechazado
        with self.assertRaises(UserError):
            TRAB.create_trabajador(self.admin_token, {
                'dni': f'0{uuid.uuid4().int % 9000000 + 1000000}',
                'apellidos': 'Error',
                'nombres': 'Sede',
                'tipo': 'SEDE',
                'area_id': self.area_id,
                'institucion_id': self.inst_id
            })

        # SEDE correcto
        dni_sede = f'0{uuid.uuid4().int % 9000000 + 1000000}'
        t_sede_id = TRAB.create_trabajador(self.admin_token, {
            'dni': dni_sede,
            'apellidos': 'Funcionario',
            'nombres': 'UGEL',
            'tipo': 'SEDE',
            'area_id': self.area_id,
            'cargo_id': self.cargo_id,
            'importe': Decimal('1800.00')
        })
        t_sede = TRAB.get_trabajador(self.admin_token, t_sede_id)
        self.assertEqual(t_sede['tipo'], 'SEDE')
        self.assertEqual(t_sede['area_id'], self.area_id)
        self.assertIsNone(t_sede['institucion_id'])

    # -------------------------------------------------------------------------
    # 4. Manejo estricto de dinero (Decimal)
    # -------------------------------------------------------------------------
    def test_manejo_monetario_decimal(self):
        # Float rechazado
        with self.assertRaises(UserError):
            parse_monto(1350.55)

        # Monto negativo rechazado
        with self.assertRaises(UserError):
            parse_monto(Decimal('-10.00'))

        # Monto válido
        m = parse_monto('1350.50')
        self.assertEqual(m, Decimal('1350.50'))

        # Trabajador con importe
        dni = f'0{uuid.uuid4().int % 9000000 + 1000000}'
        tid = TRAB.create_trabajador(self.admin_token, {
            'dni': dni,
            'apellidos': 'Rosas',
            'nombres': 'Elena',
            'tipo': 'IIEE',
            'institucion_id': self.inst_id,
            'importe': Decimal('1450.75')
        })
        t = TRAB.get_trabajador(self.admin_token, tid)
        self.assertEqual(t['importe'], Decimal('1450.75'))

    # -------------------------------------------------------------------------
    # 5. Fechas laborales y coherencia
    # -------------------------------------------------------------------------
    def test_fechas_laborales(self):
        dni = f'0{uuid.uuid4().int % 9000000 + 1000000}'
        # Fecha término anterior a ingreso -> error
        with self.assertRaises(UserError):
            TRAB.create_trabajador(self.admin_token, {
                'dni': dni,
                'apellidos': 'Fechas',
                'nombres': 'Invertidas',
                'tipo': 'IIEE',
                'institucion_id': self.inst_id,
                'fecha_ingreso': date(2026, 5, 1),
                'fecha_termino': date(2026, 4, 30)
            })

        # Fechas correctas
        tid = TRAB.create_trabajador(self.admin_token, {
            'dni': dni,
            'apellidos': 'Fechas',
            'nombres': 'Correctas',
            'tipo': 'IIEE',
            'institucion_id': self.inst_id,
            'fecha_ingreso': date(2026, 1, 1),
            'fecha_termino': date(2026, 12, 31)
        })
        t = TRAB.get_trabajador(self.admin_token, tid)
        self.assertEqual(t['fecha_ingreso'], date(2026, 1, 1))
        self.assertEqual(t['fecha_termino'], date(2026, 12, 31))

    # -------------------------------------------------------------------------
    # 6. Activación, desactivación y búsquedas
    # -------------------------------------------------------------------------
    def test_activacion_y_busquedas(self):
        dni = f'0{uuid.uuid4().int % 9000000 + 1000000}'
        tid = TRAB.create_trabajador(self.admin_token, {
            'dni': dni,
            'apellidos': 'Buscable Apellido',
            'nombres': 'Buscable Nombre',
            'tipo': 'SEDE',
            'area_id': self.area_id,
            'importe': Decimal('1500.00'),
            'activo': True
        })

        # Búsqueda por DNI
        res_dni = TRAB.list_trabajadores(self.admin_token, query=dni)
        self.assertEqual(len(res_dni), 1)
        self.assertEqual(res_dni[0]['id'], tid)

        # Desactivar
        TRAB.set_activo(self.admin_token, tid, False)
        t_inactivo = TRAB.get_trabajador(self.admin_token, tid)
        self.assertFalse(t_inactivo['activo'])

        # Solo activos no debe contenerlo
        activos = TRAB.list_trabajadores(self.admin_token, solo_activos=True)
        self.assertFalse(any(x['id'] == tid for x in activos))

        # Reactivar
        TRAB.set_activo(self.admin_token, tid, True)
        activos_rec = TRAB.list_trabajadores(self.admin_token, solo_activos=True)
        self.assertTrue(any(x['id'] == tid for x in activos_rec))


if __name__ == '__main__':
    unittest.main()
