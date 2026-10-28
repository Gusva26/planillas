"""Prueba integral de punta a punta (Etapa 17) para el Sistema de Planillas CAFAE UGEL Chepén.
Ejecuta el ciclo de vida administrativo completo contra una base PostgreSQL aislada.
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
from cafae.auditoria import AuditoriaService
from cafae.catalogos import CatalogoService
from cafae.documentos.boletas import generar_boleta_pdf, generar_cuadernillo_boletas_pdf
from cafae.documentos.excel_planillas import generar_excel_planilla
from cafae.documentos.pdf_planillas import generar_pdf_planilla
from cafae.documentos.remuneraciones import generar_excel_remuneraciones
from cafae.importaciones import ImportacionService
from cafae.planillas import PlanillaService
from cafae.reportes import ReporteService
from cafae.trabajadores import TrabajadorService
from cafae.security import AccessError, UserError

if not os.environ.get('CAFAE_DB_NAME', '').startswith('cafae_test_'):
    raise SystemExit('Estas pruebas requieren una base cafae_test_* aislada.')

AUTH = AuthService()
CAT = CatalogoService(AUTH)
TRAB = TrabajadorService(AUTH)
PLAN = PlanillaService(AUTH)
IMP = ImportacionService(AUTH)
REP = ReporteService(AUTH)
AUD = AuditoriaService(AUTH)

ADMIN_PWD = secrets.token_urlsafe(24)


class TestFlujoIntegral(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            AUTH.bootstrap('admin_integral', 'Administrador Integral', ADMIN_PWD)
        except UserError:
            pass

    def setUp(self):
        self.origin = uuid.uuid4().hex
        self.admin_token = AUTH.login('admin_integral', ADMIN_PWD, self.origin)

    def test_flujo_completo_sistema(self):
        # 1. Crear usuarios secundarios
        u_operador = 'oper_' + uuid.uuid4().hex[:8]
        pwd_oper = secrets.token_urlsafe(24)
        AUTH.create_user(self.admin_token, u_operador, 'Operador Planillas', 'PLANILLAS', pwd_oper)
        tok_temp = AUTH.login(u_operador, pwd_oper, self.origin)
        pwd_oper_new = secrets.token_urlsafe(24)
        AUTH.change_password(tok_temp, pwd_oper, pwd_oper_new)
        token_operador = AUTH.login(u_operador, pwd_oper_new, self.origin)

        # 2. Catálogos base
        n_id = CAT.create_nivel(self.admin_token, f'Secundaria {uuid.uuid4().hex[:4]}')
        m_id = CAT.create_meta(self.admin_token, f'M{uuid.uuid4().hex[:3]}', 'Educación Secundaria')
        CAT.set_nivel_meta(self.admin_token, n_id, m_id)
        cat_id = CAT.create_categoria(self.admin_token, 'A1', 'Profesional')

        inst_id = CAT.create_institucion(
            self.admin_token, '0098765', 'I.E. San José de Chepén', n_id, 'Chepén'
        )
        area_id = CAT.create_area_sede(self.admin_token, 'Dirección de Gestión Pedagógica', meta_id=m_id)

        firmas_ids = []
        for i in range(1, 5):
            fid = CAT.create_firma(self.admin_token, f'Autoridad Institucional {i}', f'Cargo Oficial {i}')
            firmas_ids.append(fid)

        # 3. Personal (Maestro de trabajadores)
        dni_1 = '00112233'
        dni_2 = '00445566'
        t1 = TRAB.create_trabajador(token_operador, {
            'dni': dni_1, 'apellidos': 'Vargas Llosa', 'nombres': 'Mario',
            'tipo': 'IIEE', 'institucion_id': inst_id, 'nivel_id': n_id,
            'categoria_id': cat_id, 'importe': Decimal('1350.00'),
            'cuenta_multired': '00123456789'
        })
        t2 = TRAB.create_trabajador(token_operador, {
            'dni': dni_2, 'apellidos': 'Arguedas Altamirano', 'nombres': 'José María',
            'tipo': 'SEDE', 'area_id': area_id, 'nivel_id': n_id,
            'categoria_id': cat_id, 'importe': Decimal('1800.00'),
            'cuenta_multired': '00987654321'
        })

        # 4. Crear Planilla Setiembre 2026 desde Maestro (II.EE.)
        pln_iiee = PLAN.crear_desde_maestro(token_operador, 2026, 9, 'IIEE')
        p_id = pln_iiee['planilla_id']
        v1_id = pln_iiee['version_id']
        self.assertEqual(pln_iiee['trabajadores_copiados'], 1)

        # 5. Edición de descuentos y licencias
        detalles = PLAN.get_detalle_version(token_operador, v1_id)
        row_t1 = detalles[0]['id']

        # Cada inserción de hijos (detalle, descuentos, firmas) ejecuta
        # bloquear_edicion() y sube revision_edicion. El contrato de creación
        # ya devuelve la revisión vigente: el cliente no debe asumir 1.
        revision_actual = pln_iiee['revision_edicion']
        self.assertGreater(revision_actual, 1)
        self.assertEqual(
            revision_actual,
            PLAN.get_planilla_version(token_operador, p_id)['revision_edicion'],
        )

        PLAN.guardar_edicion_lote(token_operador, v1_id, revision_esperada=revision_actual, cambios=[{
            'detalle_id': row_t1,
            'importe': Decimal('1350.00'),
            'dias_licencia': 3,  # Licencia 3 días: 1350/30*3 = 135.00
            'PICHINCHA': Decimal('200.00'),
            'SUB_CAFAE': Decimal('50.00')
        }])

        det_edit = PLAN.get_detalle_version(token_operador, v1_id)
        # Descuentos: 135.00 + 200.00 + 50.00 = 385.00; Neto = 965.00
        self.assertEqual(det_edit[0]['monto_licencia'], Decimal('135.00'))
        self.assertEqual(det_edit[0]['total_descuentos'], Decimal('385.00'))
        self.assertEqual(det_edit[0]['neto'], Decimal('965.00'))

        # 6. Cierre formal por Administrador (4 firmas requeridas para II.EE.)
        v1_info = PLAN.get_planilla_version(self.admin_token, p_id)
        cierre = PLAN.cerrar_version(self.admin_token, v1_id, revision_esperada=v1_info['revision_edicion'], firmas_ids=firmas_ids[:4])
        self.assertEqual(cierre['total_importe'], Decimal('1350.00'))
        self.assertEqual(cierre['total_descuentos'], Decimal('385.00'))
        self.assertEqual(cierre['total_neto'], Decimal('965.00'))

        # 7. Emisión y generación de Documentos Oficiales
        v1_cerrada = PLAN.get_planilla_version(self.admin_token, p_id)
        filas_cerradas = PLAN.get_detalle_version(self.admin_token, v1_id)
        firmas_obj = [{'nombre_completo': f'Autoridad {i}', 'cargo': f'Cargo {i}'} for i in range(1, 5)]

        # Generar PDF Oficial de Planilla
        pdf_bytes = generar_pdf_planilla(v1_cerrada, filas_cerradas, firmas_obj)
        self.assertTrue(pdf_bytes.startswith(b'%PDF'))

        # Generar Excel Oficial de Planilla
        xlsx_bytes = generar_excel_planilla(v1_cerrada, filas_cerradas, firmas_obj)
        self.assertTrue(len(xlsx_bytes) > 1000)

        # Generar Hoja de Remuneraciones (suma exclusiva de importe bruto = 1350.00)
        rem_bytes = generar_excel_remuneraciones(v1_cerrada, filas_cerradas)
        self.assertTrue(len(rem_bytes) > 1000)

        # Generar Boleta de Pago Individual
        boleta_bytes = generar_boleta_pdf(filas_cerradas[0], v1_cerrada)
        self.assertTrue(boleta_bytes.startswith(b'%PDF'))

        # Generar Cuadernillo Mensual de Boletas
        cuadernillo_bytes = generar_cuadernillo_boletas_pdf(filas_cerradas, v1_cerrada)
        self.assertTrue(cuadernillo_bytes.startswith(b'%PDF'))

        # 8. Reapertura administrativa con motivo justificado
        reap = PLAN.reabrir_version(self.admin_token, v1_id, motivo='Ajuste por mandato judicial de asignación')
        self.assertEqual(reap['nuevo_numero'], 2)
        v2_id = reap['nueva_version_id']

        # La versión 2 está abierta y la versión 1 permanece cerrada
        v2_info = PLAN.get_planilla_version(self.admin_token, p_id, version_numero=2)
        self.assertEqual(v2_info['estado'], 'BORRADOR')
        v1_check = PLAN.get_planilla_version(self.admin_token, p_id, version_numero=1)
        self.assertEqual(v1_check['estado'], 'CERRADA')

        # 9. Consultar reportes sin mezclar históricos
        rep_resumen = REP.reporte_resumen_mensual(self.admin_token, v1_id)
        self.assertEqual(rep_resumen['total_importe'], Decimal('1350.00'))
        self.assertEqual(rep_resumen['total_neto'], Decimal('965.00'))

        # 10. Consultar auditoría administrativa (listado paginado)
        pagina = AUD.list_eventos(self.admin_token)
        self.assertEqual(
            set(pagina), {'items', 'total', 'limite', 'desplazamiento'}
        )
        self.assertGreater(pagina['total'], 0)
        self.assertEqual(len(pagina['items']), min(pagina['limite'], pagina['total']))

        primera = AUD.list_eventos(self.admin_token, limite=1)
        segunda = AUD.list_eventos(self.admin_token, limite=1, desplazamiento=1)
        self.assertEqual(len(primera['items']), 1)
        self.assertEqual(primera['total'], pagina['total'])
        self.assertNotEqual(primera['items'][0]['id'], segunda['items'][0]['id'])


if __name__ == '__main__':
    unittest.main()
