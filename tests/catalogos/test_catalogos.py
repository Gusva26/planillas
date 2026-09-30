"""Pruebas unitarias y de integración para el servicio de Catálogos (Etapa 3).
Se ejecuta contra una base aislada cafae_test_*.
"""
import os
import secrets
import sys
import unittest
import uuid

sys.path.insert(0, '/app')

from cafae.auth import AuthService
from cafae.catalogos import CatalogoService
from cafae.security import AccessError, SessionError, UserError

if not os.environ.get('CAFAE_DB_NAME', '').startswith('cafae_test_'):
    raise SystemExit('Estas pruebas requieren una base cafae_test_* aislada.')

AUTH = AuthService()
CAT = CatalogoService(AUTH)
ADMIN_PWD = secrets.token_urlsafe(24)


class TestCatalogos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Crear usuario administrador inicial
        try:
            AUTH.bootstrap('admin_cat', 'Administrador Catálogos', ADMIN_PWD)
        except UserError:
            pass

    def setUp(self):
        self.origin = uuid.uuid4().hex
        self.admin_token = AUTH.login('admin_cat', ADMIN_PWD, self.origin)

    def create_user_with_role(self, role):
        username = 'u_' + uuid.uuid4().hex[:10]
        temp_pwd = secrets.token_urlsafe(24)
        AUTH.create_user(self.admin_token, username, f'Usuario {role}', role, temp_pwd)
        token = AUTH.login(username, temp_pwd, self.origin)
        new_pwd = secrets.token_urlsafe(24)
        AUTH.change_password(token, temp_pwd, new_pwd)
        return AUTH.login(username, new_pwd, self.origin)

    # -------------------------------------------------------------------------
    # 1. Permisos y control de roles
    # -------------------------------------------------------------------------
    def test_permisos_catalogos_por_rol(self):
        token_planillas = self.create_user_with_role('PLANILLAS')
        token_consulta = self.create_user_with_role('CONSULTA')

        # Consulta puede listar
        niveles = CAT.list_niveles(token_consulta)
        self.assertIsInstance(niveles, list)

        # Planillas puede listar
        areas = CAT.list_areas_sede(token_planillas)
        self.assertIsInstance(areas, list)

        # Planillas NO puede crear catálogos
        with self.assertRaises(AccessError):
            CAT.create_cargo(token_planillas, 'Cargo No Permitido')

        # Consulta NO puede crear catálogos
        with self.assertRaises(AccessError):
            CAT.create_nivel(token_consulta, 'Nivel No Permitido')

        # Consulta NO puede actualizar
        with self.assertRaises(AccessError):
            CAT.update_configuracion(token_consulta, 'UGEL', 'SISTEMA')

    # -------------------------------------------------------------------------
    # 2. Niveles
    # -------------------------------------------------------------------------
    def test_niveles_crud_y_unicidad(self):
        nombre = f'Nivel Primaria {uuid.uuid4().hex[:6]}'
        nid = CAT.create_nivel(self.admin_token, nombre)
        self.assertGreater(nid, 0)

        # Verificar obtención
        n = CAT.get_nivel(self.admin_token, nid)
        self.assertEqual(n['nombre'], nombre)
        self.assertTrue(n['activo'])

        # Duplicado debe lanzar UserError
        with self.assertRaises(UserError) as ctx:
            CAT.create_nivel(self.admin_token, nombre)
        self.assertIn('Ya existe', str(ctx.exception))

        # Modificación y desactivación
        nuevo_nombre = f'Nivel Primaria Mod {uuid.uuid4().hex[:6]}'
        CAT.update_nivel(self.admin_token, nid, nuevo_nombre, activo=False)
        n_mod = CAT.get_nivel(self.admin_token, nid)
        self.assertEqual(n_mod['nombre'], nuevo_nombre)
        self.assertFalse(n_mod['activo'])

        # Listado con filtro de activos
        activos = CAT.list_niveles(self.admin_token, solo_activos=True)
        self.assertFalse(any(item['id'] == nid for item in activos))
        todos = CAT.list_niveles(self.admin_token, solo_activos=False)
        self.assertTrue(any(item['id'] == nid for item in todos))

    # -------------------------------------------------------------------------
    # 3. Partidas Presupuestarias
    # -------------------------------------------------------------------------
    def test_partidas_crud_y_unicidad(self):
        cod = f'2.1.{uuid.uuid4().hex[:4]}'
        pid = CAT.create_partida(self.admin_token, cod, 'Partida de gasto CAFAE')
        self.assertGreater(pid, 0)

        # Unicidad
        with self.assertRaises(UserError):
            CAT.create_partida(self.admin_token, cod, 'Otra partida duplicada')

        # Actualización
        CAT.update_partida(self.admin_token, pid, cod, 'Descripción actualizada', activo=True)
        partida = CAT.get_partida(self.admin_token, pid)
        self.assertEqual(partida['descripcion'], 'Descripción actualizada')

    # -------------------------------------------------------------------------
    # 4. Programas Presupuestarios (Jerarquía y prevención de ciclos)
    # -------------------------------------------------------------------------
    def test_programas_jerarquia_y_ciclos(self):
        c_padre = f'PR_{uuid.uuid4().hex[:4]}'
        c_hijo = f'PR_{uuid.uuid4().hex[:4]}'
        c_nieto = f'PR_{uuid.uuid4().hex[:4]}'

        p_id = CAT.create_programa(self.admin_token, c_padre, 'Programa Raíz', orden=1)
        h_id = CAT.create_programa(self.admin_token, c_hijo, 'Subprograma Hijo', orden=2, padre_id=p_id)
        n_id = CAT.create_programa(self.admin_token, c_nieto, 'Actividad Nieta', orden=3, padre_id=h_id)

        # Árbol estructurado
        arbol = CAT.get_arbol_programas(self.admin_token)
        nodo_p = next(x for x in arbol if x['id'] == p_id)
        self.assertEqual(len(nodo_p['hijos']), 1)
        self.assertEqual(nodo_p['hijos'][0]['id'], h_id)
        self.assertEqual(nodo_p['hijos'][0]['hijos'][0]['id'], n_id)

        # Intento de auto-paternidad
        with self.assertRaises(UserError):
            CAT.update_programa(self.admin_token, p_id, c_padre, 'Raíz', 1, padre_id=p_id, activo=True)

        # Intento de ciclo (padre apunta a nieto)
        with self.assertRaises(UserError) as ctx:
            CAT.update_programa(self.admin_token, p_id, c_padre, 'Raíz', 1, padre_id=n_id, activo=True)
        self.assertTrue('ciclo' in str(ctx.exception).lower() or 'circular' in str(ctx.exception).lower())

    # -------------------------------------------------------------------------
    # 5. Metas y Relación Nivel - Meta
    # -------------------------------------------------------------------------
    def test_metas_y_resolucion_nivel_meta(self):
        c_prog = f'PG_{uuid.uuid4().hex[:4]}'
        prog_id = CAT.create_programa(self.admin_token, c_prog, 'Prog Meta', orden=1)
        c_part = f'PT_{uuid.uuid4().hex[:4]}'
        part_id = CAT.create_partida(self.admin_token, c_part, 'Part Meta')

        # Crear dos metas
        m_cod1 = f'M_{uuid.uuid4().hex[:4]}'
        m_cod2 = f'M_{uuid.uuid4().hex[:4]}'
        m_id1 = CAT.create_meta(self.admin_token, m_cod1, 'Meta Inicial General', prog_id, part_id)
        m_id2 = CAT.create_meta(self.admin_token, m_cod2, 'Meta Específica IE', prog_id, part_id)

        # Crear nivel y asociar nivel con m_id1
        n_nombre = f'Nivel Sec {uuid.uuid4().hex[:4]}'
        n_id = CAT.create_nivel(self.admin_token, n_nombre)
        CAT.set_nivel_meta(self.admin_token, n_id, m_id1)

        nm_list = CAT.list_nivel_metas(self.admin_token)
        assoc = next(x for x in nm_list if x['nivel_id'] == n_id)
        self.assertEqual(assoc['meta_id'], m_id1)

        # IE sin meta propia -> resuelve meta del nivel (m_id1)
        mod_1 = f'0{uuid.uuid4().int % 9000000 + 1000000}'
        ie1_id = CAT.create_institucion(
            self.admin_token, mod_1, 'Colegio Sin Meta Propia',
            nivel_id=n_id, distrito='Chepén', meta_id=None
        )
        res1 = CAT.resolver_meta_institucion(self.admin_token, ie1_id)
        self.assertEqual(res1['meta_resuelta_id'], m_id1)
        self.assertEqual(res1['origen_resolucion'], 'NIVEL')

        # IE con meta propia (m_id2) -> resuelve su propia meta
        mod_2 = f'0{uuid.uuid4().int % 9000000 + 1000000}'
        ie2_id = CAT.create_institucion(
            self.admin_token, mod_2, 'Colegio Con Meta Propia',
            nivel_id=n_id, distrito='Pacanga', meta_id=m_id2
        )
        res2 = CAT.resolver_meta_institucion(self.admin_token, ie2_id)
        self.assertEqual(res2['meta_resuelta_id'], m_id2)
        self.assertEqual(res2['origen_resolucion'], 'INSTITUCION')

    # -------------------------------------------------------------------------
    # 6. Instituciones Educativas (Búsqueda y código modular de texto)
    # -------------------------------------------------------------------------
    def test_instituciones_busqueda_y_unicidad(self):
        n_id = CAT.create_nivel(self.admin_token, f'Nivel IE {uuid.uuid4().hex[:6]}')
        cod_mod = '0012345'  # Código con ceros a la izquierda
        inst_id = CAT.create_institucion(
            self.admin_token, cod_mod, 'I.E. Santa Rosa de Lima',
            nivel_id=n_id, distrito='Chepén', observaciones='Local histórico'
        )

        # Obtener y verificar conservación de ceros a la izquierda
        ie = CAT.get_institucion(self.admin_token, inst_id)
        self.assertEqual(ie['codigo_modular'], '0012345')

        # Búsqueda por código modular
        res = CAT.list_instituciones(self.admin_token, query='0012345')
        self.assertTrue(any(x['id'] == inst_id for x in res))

        # Búsqueda por nombre
        res_nom = CAT.list_instituciones(self.admin_token, query='Santa Rosa')
        self.assertTrue(any(x['id'] == inst_id for x in res_nom))

        # Duplicado de código modular
        with self.assertRaises(UserError):
            CAT.create_institucion(
                self.admin_token, cod_mod, 'Otra IE Mismo Código',
                nivel_id=n_id, distrito='Pueblo Nuevo'
            )

    # -------------------------------------------------------------------------
    # 7. Áreas de Sede
    # -------------------------------------------------------------------------
    def test_areas_sede_y_resolucion(self):
        m_id = CAT.create_meta(self.admin_token, f'MS_{uuid.uuid4().hex[:4]}', 'Meta Sede')
        nombre = f'Área de Personal {uuid.uuid4().hex[:4]}'
        area_id = CAT.create_area_sede(self.admin_token, nombre, meta_id=m_id)

        res = CAT.resolver_meta_area(self.admin_token, area_id)
        self.assertEqual(res['meta_resuelta_id'], m_id)
        self.assertEqual(res['origen_resolucion'], 'AREA')

        # Unicidad
        with self.assertRaises(UserError):
            CAT.create_area_sede(self.admin_token, nombre)

    # -------------------------------------------------------------------------
    # 8. Cargos, Categorías, Situaciones y Subtipos
    # -------------------------------------------------------------------------
    def test_tablas_adicionales_personal(self):
        # Cargo
        cid = CAT.create_cargo(self.admin_token, f'Especialista {uuid.uuid4().hex[:4]}')
        self.assertGreater(cid, 0)
        cargos = CAT.list_cargos(self.admin_token)
        self.assertTrue(any(c['id'] == cid for c in cargos))

        # Categoría
        cat_cod = f'CAT_{uuid.uuid4().hex[:4]}'
        cat_id = CAT.create_categoria(self.admin_token, cat_cod, 'Categoría Especial')
        self.assertGreater(cat_id, 0)
        cats = CAT.list_categorias(self.admin_token)
        self.assertTrue(any(c['id'] == cat_id for c in cats))

        # Situación
        sit_id = CAT.create_situacion(self.admin_token, f'Nombrado {uuid.uuid4().hex[:4]}')
        self.assertGreater(sit_id, 0)

        # Subtipo
        sub_id = CAT.create_subtipo(self.admin_token, f'Administrativo {uuid.uuid4().hex[:4]}')
        self.assertGreater(sub_id, 0)

    # -------------------------------------------------------------------------
    # 9. Firmas Maestras
    # -------------------------------------------------------------------------
    def test_firmas_maestras(self):
        fid = CAT.create_firma(self.admin_token, 'Prof. Juan Pérez', 'Director de UGEL Chepén')
        self.assertGreater(fid, 0)

        firmas = CAT.list_firmas(self.admin_token)
        f_row = next(f for f in firmas if f['id'] == fid)
        self.assertEqual(f_row['nombre_completo'], 'Prof. Juan Pérez')
        self.assertEqual(f_row['cargo'], 'Director de UGEL Chepén')

        CAT.update_firma(self.admin_token, fid, 'Prof. Juan Pérez Valdivia', 'Director de UGEL Chepén', activo=True)
        firmas_mod = CAT.list_firmas(self.admin_token)
        f_mod = next(f for f in firmas_mod if f['id'] == fid)
        self.assertEqual(f_mod['nombre_completo'], 'Prof. Juan Pérez Valdivia')

    # -------------------------------------------------------------------------
    # 10. Configuración e Identidad Institucional
    # -------------------------------------------------------------------------
    def test_configuracion_institucional(self):
        # Por defecto
        cfg = CAT.get_configuracion(self.admin_token)
        self.assertIn('nombre_institucion', cfg)
        self.assertEqual(cfg['zona_horaria'], 'America/Lima')

        # Actualización válida
        CAT.update_configuracion(
            self.admin_token,
            nombre_institucion='UGEL CHEPÉN - SEDE CENTRAL',
            nombre_sistema='CAFAE UGEL CHEPÉN v2',
            zona_horaria='America/Lima'
        )
        cfg_actualizada = CAT.get_configuracion(self.admin_token)
        self.assertEqual(cfg_actualizada['nombre_institucion'], 'UGEL CHEPÉN - SEDE CENTRAL')
        self.assertEqual(cfg_actualizada['nombre_sistema'], 'CAFAE UGEL CHEPÉN v2')

        # Zona horaria inválida rechazada
        with self.assertRaises(UserError):
            CAT.update_configuracion(
                self.admin_token,
                'UGEL', 'SISTEMA',
                zona_horaria='Zona/Ficticia_Invalida'
            )


if __name__ == '__main__':
    unittest.main()
