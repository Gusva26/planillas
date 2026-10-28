"""Pruebas completas para Motor de Cálculos (Etapa 6) y Ciclo de Planillas (Etapas 5 y 8).
Se ejecuta contra base de datos aislada cafae_test_*.
"""
from decimal import Decimal
import os
import secrets
import sys
import unittest
import uuid

sys.path.insert(0, '/app')

from cafae.auth import AuthService
from cafae.calculos import (calcular_licencia, calcular_liquidacion_trabajador,
                            calcular_totales_planilla)
from cafae.catalogos import CatalogoService
from cafae.planillas import PlanillaService
from cafae.trabajadores import TrabajadorService
from cafae.security import AccessError, UserError

if not os.environ.get('CAFAE_DB_NAME', '').startswith('cafae_test_'):
    raise SystemExit('Estas pruebas requieren una base cafae_test_* aislada.')

AUTH = AuthService()
CAT = CatalogoService(AUTH)
TRAB = TrabajadorService(AUTH)
PLAN = PlanillaService(AUTH)
ADMIN_PWD = secrets.token_urlsafe(24)


class TestPlanillasYCAlculos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            AUTH.bootstrap('admin_pln', 'Administrador Planillas', ADMIN_PWD)
        except UserError:
            pass

    def setUp(self):
        self.origin = uuid.uuid4().hex
        self.admin_token = AUTH.login('admin_pln', ADMIN_PWD, self.origin)

        # Catálogos base
        self.nivel_id = CAT.create_nivel(self.admin_token, f'Niv {uuid.uuid4().hex[:6]}')
        # El cierre exige meta_codigo y categoria en cada fila del detalle.
        meta_id = CAT.create_meta(self.admin_token, f'M{uuid.uuid4().hex[:4]}', 'Educación Primaria')
        CAT.set_nivel_meta(self.admin_token, self.nivel_id, meta_id)
        self.categoria_id = CAT.create_categoria(
            self.admin_token, f'A{uuid.uuid4().hex[:4]}', 'Profesional')
        self.inst_id = CAT.create_institucion(
            self.admin_token, f'0{uuid.uuid4().int % 9000000 + 1000000}',
            'Colegio Primaria', self.nivel_id, 'Chepén'
        )
        self.area_id = CAT.create_area_sede(self.admin_token, f'Área {uuid.uuid4().hex[:6]}')

        # Firmas (al menos 4 para IIEE y 3 para Sede)
        self.firmas = []
        for i in range(1, 5):
            fid = CAT.create_firma(self.admin_token, f'Autoridad {i}', f'Cargo {i}')
            self.firmas.append(fid)

        # Trabajadores activos e inactivos
        self.t1_id = TRAB.create_trabajador(self.admin_token, {
            'dni': f'0{uuid.uuid4().int % 9000000 + 1000000}',
            'apellidos': 'Torres',
            'nombres': 'Luis',
            'tipo': 'IIEE',
            'institucion_id': self.inst_id,
            'nivel_id': self.nivel_id,
            'categoria_id': self.categoria_id,
            'importe': Decimal('1350.00'),
            'cuenta_multired': '00123456789',
            'activo': True
        })
        self.t2_id = TRAB.create_trabajador(self.admin_token, {
            'dni': f'0{uuid.uuid4().int % 9000000 + 1000000}',
            'apellidos': 'Inactivo',
            'nombres': 'Pedro',
            'tipo': 'IIEE',
            'institucion_id': self.inst_id,
            'nivel_id': self.nivel_id,
            'categoria_id': self.categoria_id,
            'importe': Decimal('1350.00'),
            'cuenta_multired': '00987654321',
            'activo': False
        })
        self.t_sede_id = TRAB.create_trabajador(self.admin_token, {
            'dni': f'0{uuid.uuid4().int % 9000000 + 1000000}',
            'apellidos': 'Castro',
            'nombres': 'María',
            'tipo': 'SEDE',
            'area_id': self.area_id,
            'nivel_id': self.nivel_id,
            'categoria_id': self.categoria_id,
            'importe': Decimal('1800.00'),
            'cuenta_multired': '00555666777',
            'activo': True
        })

    def create_user(self, role):
        username = 'u_' + uuid.uuid4().hex[:10]
        temp_pwd = secrets.token_urlsafe(24)
        AUTH.create_user(self.admin_token, username, f'Usuario {role}', role, temp_pwd)
        token = AUTH.login(username, temp_pwd, self.origin)
        new_pwd = secrets.token_urlsafe(24)
        AUTH.change_password(token, temp_pwd, new_pwd)
        return AUTH.login(username, new_pwd, self.origin)

    # -------------------------------------------------------------------------
    # 1. Casos CAL-01 a CAL-07: Motor de Cálculos Monetarios
    # -------------------------------------------------------------------------
    def test_cal_01_descuentos_y_neto(self):
        # CAL-01: Importe 1350.00; Pichincha 735.45; SITASE/FENTASE 10.00 -> Desc: 745.45, Neto: 604.55
        res = calcular_liquidacion_trabajador(
            importe=Decimal('1350.00'),
            dias_licencia=0,
            descuentos={'PICHINCHA': Decimal('735.45'), 'SITASE_FENTASE': Decimal('10.00')}
        )
        self.assertEqual(res['total_descuentos'], Decimal('745.45'))
        self.assertEqual(res['neto'], Decimal('604.55'))
        self.assertFalse(res['es_neto_negativo'])

    def test_cal_02_y_cal_03_licencias(self):
        # CAL-02: Importe 1350.00; Licencia 3 días -> 135.00, Neto 1215.00
        lic_3 = calcular_licencia(Decimal('1350.00'), 3)
        self.assertEqual(lic_3, Decimal('135.00'))
        res_3 = calcular_liquidacion_trabajador(Decimal('1350.00'), 3, {})
        self.assertEqual(res_3['monto_licencia'], Decimal('135.00'))
        self.assertEqual(res_3['neto'], Decimal('1215.00'))

        # CAL-03: Licencia 0 días = 0.00; Licencia 30 días = 1350.00
        self.assertEqual(calcular_licencia(Decimal('1350.00'), 0), Decimal('0.00'))
        self.assertEqual(calcular_licencia(Decimal('1350.00'), 30), Decimal('1350.00'))

    def test_cal_04_dias_invalidos(self):
        # CAL-04: Días negativos o > 30 deben ser rechazados
        with self.assertRaises(UserError):
            calcular_licencia(Decimal('1350.00'), -1)
        with self.assertRaises(UserError):
            calcular_licencia(Decimal('1350.00'), 31)

    def test_cal_05_neto_negativo(self):
        # CAL-05: Descuentos mayores al importe
        res = calcular_liquidacion_trabajador(
            importe=Decimal('1000.00'),
            dias_licencia=0,
            descuentos={'PICHINCHA': Decimal('1200.00')}
        )
        self.assertEqual(res['neto'], Decimal('-200.00'))
        self.assertTrue(res['es_neto_negativo'])

    # -------------------------------------------------------------------------
    # 2. Creación desde Maestro (PER-01, PER-02, PER-03)
    # -------------------------------------------------------------------------
    def test_creacion_desde_maestro_y_unicidad(self):
        # PER-03: Solo activos incluidos, descuentos iniciales en 0.00.
        # El maestro es global y cada test deja trabajadores activos, así que
        # se verifica la inclusión/exclusión por DNI, no un conteo fijo.
        res = PLAN.crear_desde_maestro(self.admin_token, 2026, 9, 'IIEE')

        v_id = res['version_id']
        det = PLAN.get_detalle_version(self.admin_token, v_id)
        self.assertEqual(res['trabajadores_copiados'], len(det))

        dnis = {fila['dni'] for fila in det}
        self.assertIn(TRAB.get_trabajador(self.admin_token, self.t1_id)['dni'], dnis)
        self.assertNotIn(TRAB.get_trabajador(self.admin_token, self.t2_id)['dni'], dnis)

        fila_t1 = next(f for f in det
                       if f['dni'] == TRAB.get_trabajador(self.admin_token, self.t1_id)['dni'])
        self.assertEqual(fila_t1['importe'], Decimal('1350.00'))
        self.assertEqual(fila_t1['total_descuentos'], Decimal('0.00'))
        self.assertEqual(fila_t1['neto'], Decimal('1350.00'))

        # PER-01: Duplicado del mismo periodo y tipo rechazado
        with self.assertRaises(UserError):
            PLAN.crear_desde_maestro(self.admin_token, 2026, 9, 'IIEE')

        # PER-02: Crear SEDE en el mismo periodo está permitido y aislado
        res_sede = PLAN.crear_desde_maestro(self.admin_token, 2026, 9, 'SEDE')
        self.assertGreater(res_sede['planilla_id'], 0)

    # -------------------------------------------------------------------------
    # 3. Edición Masiva por Lote y Limpieza (PER-06, CLR-01)
    # -------------------------------------------------------------------------
    def test_edicion_lote_y_limpieza(self):
        res = PLAN.crear_desde_maestro(self.admin_token, 2026, 10, 'IIEE')
        v_id = res['version_id']
        det = PLAN.get_detalle_version(self.admin_token, v_id)
        row_id = det[0]['id']

        # Editar descuentos y días de licencia.
        # Las inserciones de detalle del maestro ya subieron revision_edicion:
        # el cliente debe releerla antes de editar.
        revision_actual = PLAN.get_planilla_version(
            self.admin_token, res['planilla_id'])['revision_edicion']
        PLAN.guardar_edicion_lote(self.admin_token, v_id, revision_esperada=revision_actual, cambios=[{
            'detalle_id': row_id,
            'importe': Decimal('1350.00'),
            'dias_licencia': 2,  # Licencia 2 días: 1350/30*2 = 90.00
            'PICHINCHA': Decimal('200.00'),
            'CAJA_SULLANA': Decimal('100.00')
        }])

        det_edit = PLAN.get_detalle_version(self.admin_token, v_id)
        # Descuentos: 90.00 (licencia) + 200.00 + 100.00 = 390.00; Neto = 960.00
        self.assertEqual(det_edit[0]['total_descuentos'], Decimal('390.00'))
        self.assertEqual(det_edit[0]['neto'], Decimal('960.00'))

        # CLR-01: Limpiar todos los descuentos
        v_info = PLAN.get_planilla_version(self.admin_token, res['planilla_id'])
        PLAN.limpiar_todos_descuentos(self.admin_token, v_id, revision_esperada=v_info['revision_edicion'])

        det_limpio = PLAN.get_detalle_version(self.admin_token, v_id)
        self.assertEqual(det_limpio[0]['total_descuentos'], Decimal('0.00'))
        self.assertEqual(det_limpio[0]['neto'], Decimal('1350.00'))
        self.assertEqual(det_limpio[0]['dias_licencia'], 0)

    # -------------------------------------------------------------------------
    # 4. Cierre y Reapertura Versionada (CIE-01, HIS-03, HIS-04)
    # -------------------------------------------------------------------------
    def test_cierre_y_reapertura(self):
        # 1. Crear planilla
        res = PLAN.crear_desde_maestro(self.admin_token, 2026, 11, 'IIEE')
        p_id = res['planilla_id']
        v_id = res['version_id']

        def revision_vigente():
            return PLAN.get_planilla_version(
                self.admin_token, p_id)['revision_edicion']

        # 2. Intentar cerrar con 3 firmas (IIEE requiere 4) -> debe fallar
        with self.assertRaises(UserError):
            PLAN.cerrar_version(self.admin_token, v_id, revision_esperada=revision_vigente(),
                                firmas_ids=self.firmas[:3])

        # 3. Operador NO puede cerrar planilla
        token_planillas = self.create_user('PLANILLAS')
        with self.assertRaises(AccessError):
            PLAN.cerrar_version(token_planillas, v_id, revision_esperada=revision_vigente(),
                                firmas_ids=self.firmas[:4])

        # 4. Administrador cierra con 4 firmas correctas
        res_cierre = PLAN.cerrar_version(self.admin_token, v_id, revision_esperada=revision_vigente(),
                                         firmas_ids=self.firmas[:4])
        # El maestro es global: el cierre consolida todos los activos de II.EE.
        det = PLAN.get_detalle_version(self.admin_token, v_id)
        self.assertEqual(res_cierre['total_trabajadores'], len(det))
        self.assertEqual(res_cierre['total_importe'],
                         sum((f['importe'] for f in det), Decimal('0.00')))

        # Versión cerrada es inmutable: no se puede editar
        with self.assertRaises(Exception):
            PLAN.guardar_edicion_lote(self.admin_token, v_id, revision_esperada=revision_vigente(),
                                      cambios=[])

        # 5. Reapertura: Operador NO puede reabrir
        with self.assertRaises(AccessError):
            PLAN.reabrir_version(token_planillas, v_id, motivo='Ajuste de montos')

        # 6. Administrador reabre con motivo obligatorio
        res_reap = PLAN.reabrir_version(self.admin_token, v_id, motivo='Inclusión de descuento judicial ordenado')
        self.assertEqual(res_reap['nuevo_numero'], 2)
        v2_id = res_reap['nueva_version_id']

        # La versión 2 está en BORRADOR y es editable
        v2 = PLAN.get_planilla_version(self.admin_token, p_id, version_numero=2)
        self.assertEqual(v2['estado'], 'BORRADOR')
        self.assertEqual(v2['origen'], 'REAPERTURA')

        # La versión 1 permanece CERRADA
        v1 = PLAN.get_planilla_version(self.admin_token, p_id, version_numero=1)
        self.assertEqual(v1['estado'], 'CERRADA')

    # -------------------------------------------------------------------------
    # 5. Copia desde Mes Anterior (PER-04, PER-05)
    # -------------------------------------------------------------------------
    def test_copia_mes_anterior(self):
        # PER-05: Si no existe mes anterior, debe informar error
        with self.assertRaises(UserError):
            PLAN.copiar_mes_anterior(self.admin_token, 2026, 1, 'IIEE')

        # Creamos y cerramos Diciembre 2025
        res_dic = PLAN.crear_desde_maestro(self.admin_token, 2025, 12, 'IIEE')
        p_dic_id = res_dic['planilla_id']
        v_dic_id = res_dic['version_id']
        revision_dic = PLAN.get_planilla_version(
            self.admin_token, p_dic_id)['revision_edicion']
        PLAN.cerrar_version(self.admin_token, v_dic_id, revision_esperada=revision_dic,
                            firmas_ids=self.firmas[:4])

        # PER-04 / Cruce de año: Copiar Dic 2025 a Ene 2026
        res_ene = PLAN.copiar_mes_anterior(self.admin_token, 2026, 1, 'IIEE')
        self.assertGreater(res_ene['version_id'], 0)
        det_dic = PLAN.get_detalle_version(self.admin_token, v_dic_id)
        det_ene = PLAN.get_detalle_version(self.admin_token, res_ene['version_id'])
        self.assertEqual(res_ene['trabajadores_copiados'], len(det_ene))
        self.assertEqual(len(det_ene), len(det_dic))


if __name__ == '__main__':
    unittest.main()
