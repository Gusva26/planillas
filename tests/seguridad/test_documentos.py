"""Pruebas de borde de seguridad para documentos. No requieren base de datos.

Cubren las dos regresiones del hotfix:
- D-02: un solo esquema de credenciales (`Authorization: Bearer`).
- D-01: el TXT bancario exige permiso `txt_bancario`, está bloqueado por D.5
  y solo se emite desde una versión cerrada.
"""
import os
import sys
import unittest
from unittest import mock

from fastapi import HTTPException

sys.path.insert(0, '/app')

from cafae.api.deps import get_current_user, require_permission
from cafae.api.routes_documentos import (
    PERMISO_DOCUMENTOS,
    PERMISO_TXT,
    _exigir_txt_habilitado,
    _exigir_version_cerrada,
    router,
)


class EsquemaDeCredenciales(unittest.TestCase):
    def test_sin_encabezado_se_rechaza(self):
        with self.assertRaises(HTTPException) as ctx:
            get_current_user(None)
        self.assertEqual(ctx.exception.status_code, 401)

    def test_esquema_distinto_de_bearer_se_rechaza(self):
        with self.assertRaises(HTTPException) as ctx:
            get_current_user('Basic dXNlcjpwYXNz')
        self.assertEqual(ctx.exception.status_code, 401)

    def test_token_suelto_por_query_no_se_acepta(self):
        with self.assertRaises(HTTPException) as ctx:
            get_current_user('token-en-query')
        self.assertEqual(ctx.exception.status_code, 401)

    def test_bearer_vacio_se_rechaza(self):
        with self.assertRaises(HTTPException) as ctx:
            get_current_user('Bearer    ')
        self.assertEqual(ctx.exception.status_code, 401)


class MatrizDePermisos(unittest.TestCase):
    def test_consulta_no_puede_descargar_txt(self):
        guard = require_permission('txt_bancario')
        with self.assertRaises(HTTPException) as ctx:
            guard({'rol': 'CONSULTA'})
        self.assertEqual(ctx.exception.status_code, 403)

    def test_planillas_y_administrador_pueden(self):
        guard = require_permission('txt_bancario')
        for rol in ('PLANILLAS', 'ADMINISTRADOR'):
            self.assertEqual(guard({'rol': rol})['rol'], rol)

    def test_permiso_inexistente_deniega_a_todos(self):
        guard = require_permission('no_existe')
        for rol in ('CONSULTA', 'PLANILLAS', 'ADMINISTRADOR'):
            with self.assertRaises(HTTPException) as ctx:
                guard({'rol': rol})
            self.assertEqual(ctx.exception.status_code, 403)

    def test_consulta_no_puede_generar_documentos(self):
        # ADR-006: emitir PDF/Excel/boletas requiere generar_documentos.
        guard = require_permission(PERMISO_DOCUMENTOS)
        with self.assertRaises(HTTPException) as ctx:
            guard({'rol': 'CONSULTA'})
        self.assertEqual(ctx.exception.status_code, 403)

    def test_planillas_y_administrador_generan_documentos(self):
        guard = require_permission(PERMISO_DOCUMENTOS)
        for rol in ('PLANILLAS', 'ADMINISTRADOR'):
            self.assertEqual(guard({'rol': rol})['rol'], rol)


def _permisos_de_ruta(route) -> set:
    """Recolecta los permisos declarados por las dependencias de una ruta."""
    permisos, pila = set(), [route.dependant]
    while pila:
        dependant = pila.pop()
        pila.extend(dependant.dependencies)
        permiso = getattr(dependant.call, 'permiso_requerido', None)
        if permiso:
            permisos.add(permiso)
    return permisos


class PermisosDeclaradosEnRutas(unittest.TestCase):
    """Cada endpoint de documentos declara su permiso, no solo la sesión."""

    ESPERADOS = {
        '/documentos/planilla-pdf/{version_id}': PERMISO_DOCUMENTOS,
        '/documentos/planilla-excel/{version_id}': PERMISO_DOCUMENTOS,
        '/documentos/remuneraciones-excel/{version_id}': PERMISO_DOCUMENTOS,
        '/documentos/boleta-individual/{linea_id}': PERMISO_DOCUMENTOS,
        '/documentos/boleta-dni/{version_id}/{dni}': PERMISO_DOCUMENTOS,
        '/documentos/cuadernillo-boletas/{version_id}': PERMISO_DOCUMENTOS,
        '/documentos/banco-txt/{version_id}': PERMISO_TXT,
        '/documentos/banco-txt-resumen/{version_id}': PERMISO_TXT,
    }

    def test_cada_endpoint_exige_su_permiso(self):
        rutas = {ruta.path: ruta for ruta in router.routes}
        self.assertEqual(set(rutas), set(self.ESPERADOS))
        for path, permiso in self.ESPERADOS.items():
            with self.subTest(path=path):
                self.assertIn(permiso, _permisos_de_ruta(rutas[path]))


class BloqueoTxtBancario(unittest.TestCase):
    def test_bloqueado_por_defecto(self):
        entorno = {k: v for k, v in os.environ.items() if k != 'CAFAE_TXT_BANCARIO'}
        with mock.patch.dict(os.environ, entorno, clear=True):
            with self.assertRaises(HTTPException) as ctx:
                _exigir_txt_habilitado()
        self.assertEqual(ctx.exception.status_code, 403)
        self.assertIn('D.5', ctx.exception.detail)

    def test_habilitado_solo_con_bandera_explicita(self):
        with mock.patch.dict(os.environ, {'CAFAE_TXT_BANCARIO': '1'}):
            _exigir_txt_habilitado()

    def test_bandera_con_otro_valor_no_habilita(self):
        for valor in ('0', 'true', 'si', ''):
            with mock.patch.dict(os.environ, {'CAFAE_TXT_BANCARIO': valor}):
                with self.assertRaises(HTTPException) as ctx:
                    _exigir_txt_habilitado()
                self.assertEqual(ctx.exception.status_code, 403)

    def test_solo_versiones_cerradas(self):
        for estado in ('BORRADOR', 'EN_REVISION'):
            with self.assertRaises(HTTPException) as ctx:
                _exigir_version_cerrada({'estado': estado})
            self.assertEqual(ctx.exception.status_code, 409)
        _exigir_version_cerrada({'estado': 'CERRADA'})

    def test_version_sin_estado_se_rechaza(self):
        with self.assertRaises(HTTPException) as ctx:
            _exigir_version_cerrada({})
        self.assertEqual(ctx.exception.status_code, 409)


if __name__ == '__main__':
    unittest.main()
