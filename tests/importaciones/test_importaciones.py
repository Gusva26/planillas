"""Pruebas completas para el módulo de Importaciones de Descuentos (Etapa 7).
Se ejecuta contra base de datos aislada cafae_test_*.
"""
from decimal import Decimal
import io
import os
import openpyxl
import secrets
import sys
import unittest
import uuid

sys.path.insert(0, '/app')

from cafae.auth import AuthService
from cafae.catalogos import CatalogoService
from cafae.importaciones import ImportacionService
from cafae.planillas import PlanillaService
from cafae.trabajadores import TrabajadorService
from cafae.security import UserError

if not os.environ.get('CAFAE_DB_NAME', '').startswith('cafae_test_'):
    raise SystemExit('Estas pruebas requieren una base cafae_test_* aislada.')

AUTH = AuthService()
CAT = CatalogoService(AUTH)
TRAB = TrabajadorService(AUTH)
PLAN = PlanillaService(AUTH)
IMP = ImportacionService(AUTH)
ADMIN_PWD = secrets.token_urlsafe(24)


def crear_excel_descuentos(filas: list[tuple]) -> bytes:
    """Crea un archivo Excel en memoria con columnas DNI, NOMBRES, MONTO."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Descuentos"
    ws.append(["DNI", "TRABAJADOR", "MONTO"])
    for r in filas:
        ws.append(list(r))
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


class TestImportaciones(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            AUTH.bootstrap('admin_imp', 'Administrador Importaciones', ADMIN_PWD)
        except UserError:
            pass

    def setUp(self):
        self.origin = uuid.uuid4().hex
        self.admin_token = AUTH.login('admin_imp', ADMIN_PWD, self.origin)

        # Base para crear planilla
        self.nivel_id = CAT.create_nivel(self.admin_token, f'Niv {uuid.uuid4().hex[:6]}')
        self.inst_id = CAT.create_institucion(
            self.admin_token, f'0{uuid.uuid4().int % 9000000 + 1000000}',
            'Colegio Importaciones', self.nivel_id, 'Chepén'
        )

        self.dni_1 = f'0{uuid.uuid4().int % 9000000 + 1000000}'
        self.dni_2 = f'0{uuid.uuid4().int % 9000000 + 1000000}'
        self.dni_3 = f'0{uuid.uuid4().int % 9000000 + 1000000}'

        TRAB.create_trabajador(self.admin_token, {
            'dni': self.dni_1, 'apellidos': 'Sánchez Quispe', 'nombres': 'Raúl',
            'tipo': 'IIEE', 'institucion_id': self.inst_id, 'importe': Decimal('1350.00')
        })
        TRAB.create_trabajador(self.admin_token, {
            'dni': self.dni_2, 'apellidos': 'Gómez Díaz', 'nombres': 'Silvia',
            'tipo': 'IIEE', 'institucion_id': self.inst_id, 'importe': Decimal('1350.00')
        })
        TRAB.create_trabajador(self.admin_token, {
            'dni': self.dni_3, 'apellidos': 'Paredes Rojas', 'nombres': 'Jorge',
            'tipo': 'IIEE', 'institucion_id': self.inst_id, 'importe': Decimal('1350.00')
        })

        # Crear planilla
        res_pln = PLAN.crear_desde_maestro(self.admin_token, 2026, 8, 'IIEE')
        self.planilla_id = res_pln['planilla_id']
        self.version_id = res_pln['version_id']

    # -------------------------------------------------------------------------
    # Casos IMP-01 a IMP-06: Extracción, clasificación y duplicados
    # -------------------------------------------------------------------------
    def test_extraccion_y_clasificacion_completa(self):
        dni_no_existe = '99999999'
        filas_data = [
            (self.dni_1, 'Sánchez Quispe, Raúl', 150.00),         # IDENTIFICADO
            (self.dni_2, 'Nombre Completamente Distinto', 120.00),# REVISAR (IMP-06)
            (dni_no_existe, 'Persona Fantasma', 50.00),          # NO_ENCONTRADO (IMP-05)
            ('12345', 'DNI Corto', 30.00),                       # NO_ENCONTRADO
            (self.dni_3, 'Paredes Rojas, Jorge', -10.00),         # MONTO_INVALIDO
            (self.dni_3, 'Paredes Rojas, Jorge', 80.00),          # DNI_DUPLICADO (IMP-04)
            (self.dni_3, 'Paredes Rojas, Jorge', 90.00),          # DNI_DUPLICADO (IMP-04)
        ]
        excel_bytes = crear_excel_descuentos(filas_data)

        # Procesar para tipo 1 (PICHINCHA)
        res = IMP.procesar_archivo_importacion(
            self.admin_token, self.version_id, 1, 'descuentos_pichincha.xlsx', excel_bytes
        )
        imp_id = res['importacion_id']
        self.assertGreater(imp_id, 0)
        self.assertEqual(res['filas_duplicadas'], 2)  # Las 2 apariciones válidas de dni_3

        filas_db = IMP.list_filas_importacion(self.admin_token, imp_id)
        estados = [f['estado'] for f in filas_db]

        self.assertIn('IDENTIFICADO', estados)
        self.assertIn('REVISAR', estados)
        self.assertIn('NO_ENCONTRADO', estados)
        self.assertIn('MONTO_INVALIDO', estados)
        self.assertIn('DNI_DUPLICADO', estados)

        # Fila identificada debe estar seleccionada por defecto
        f_id = next(f for f in filas_db if f['dni_normalizado'] == self.dni_1)
        self.assertTrue(f_id['seleccionado'])

        # Fila en REVISAR debe estar sin seleccionar por defecto
        f_rev = next(f for f in filas_db if f['dni_normalizado'] == self.dni_2)
        self.assertFalse(f_rev['seleccionado'])

    # -------------------------------------------------------------------------
    # Casos IMP-07, IMP-08, IMP-09, IMP-12: Modalidades y Aplicación
    # -------------------------------------------------------------------------
    def test_aplicacion_modalidades_reemplazar_y_actualizar(self):
        # 1. Preparar un archivo limpio con 2 trabajadores
        filas = [
            (self.dni_1, 'Sánchez Quispe, Raúl', 250.00),
            (self.dni_2, 'Gómez Díaz, Silvia', 180.00),
        ]
        excel_bytes = crear_excel_descuentos(filas)

        res_imp = IMP.procesar_archivo_importacion(
            self.admin_token, self.version_id, 1, 'pichincha.xlsx', excel_bytes
        )
        imp_id = res_imp['importacion_id']

        # IMP-12: Si desmarcamos todo y tratamos de aplicar -> debe rechazar
        IMP.cambiar_seleccion_fila(self.admin_token, imp_id, 1, seleccionado=False)
        IMP.cambiar_seleccion_fila(self.admin_token, imp_id, 2, seleccionado=False)
        with self.assertRaises(UserError):
            IMP.aplicar_importacion(self.admin_token, imp_id, modo='ACTUALIZAR', revision_esperada=1)

        # Volvemos a seleccionar fila 1
        IMP.cambiar_seleccion_fila(self.admin_token, imp_id, 1, seleccionado=True)

        # IMP-08: Aplicar en modo ACTUALIZAR
        res_ap = IMP.aplicar_importacion(self.admin_token, imp_id, modo='ACTUALIZAR', revision_esperada=1)
        self.assertEqual(res_ap['registros_aplicados'], 1)
        self.assertEqual(res_ap['total_aplicado'], Decimal('250.00'))

        # Comprobar en planilla_detalle
        det = PLAN.get_detalle_version(self.admin_token, self.version_id)
        d1 = next(x for x in det if x['dni'] == self.dni_1)
        self.assertEqual(d1['pichincha'], Decimal('250.00'))

        # IMP-09: Reintento de aplicar la misma importación debe ser rechazado por idempotencia
        with self.assertRaises(UserError):
            IMP.aplicar_importacion(self.admin_token, imp_id, modo='ACTUALIZAR', revision_esperada=res_ap['nueva_revision'])


if __name__ == '__main__':
    unittest.main()
