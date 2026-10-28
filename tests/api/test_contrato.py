"""Contrato público del API: sobre de error y esquema OpenAPI.

No requiere base de datos: valida el contrato que consume el frontend.
"""
import ast
import asyncio
import importlib
import inspect
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, '/app')

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from cafae.api.errors import CATALOGO, MEDIA_TYPE, Problem, problema, problema_para_status
from cafae.api.main import (
    app,
    http_exception_handler,
    serialization_failure_handler,
    user_error_handler,
    validation_error_handler,
)
from cafae.api.schemas import PlanillaCreada, RespuestaCreacionPlanilla
from cafae.security import UserError


def _request(path='/api/planillas'):
    return Request({
        'type': 'http',
        'http_version': '1.1',
        'method': 'GET',
        'scheme': 'http',
        'path': path,
        'root_path': '',
        'query_string': b'',
        'headers': [],
        'server': ('testserver', 80),
        'client': ('testclient', 12345),
    })


def _json(response):
    return json.loads(response.body.decode('utf-8'))


class SobreDeError(unittest.TestCase):
    def test_catalogo_usa_status_http_correctos(self):
        self.assertEqual(CATALOGO['SOLICITUD_INVALIDA'][0], 400)
        self.assertEqual(CATALOGO['NO_AUTENTICADO'][0], 401)
        self.assertEqual(CATALOGO['SIN_PERMISO'][0], 403)
        self.assertEqual(CATALOGO['CONFLICTO_REVISION'][0], 409)
        self.assertEqual(CATALOGO['VALIDACION'][0], 422)

    def test_problema_arma_el_sobre_completo(self):
        body = problema('CONFLICTO_REVISION', 'La planilla cambió.', instance='/api/x')
        self.assertEqual(body['type'], 'urn:problem-type:cafae:conflicto-revision')
        self.assertEqual(body['title'], 'Conflicto de revisión')
        self.assertEqual(body['status'], 409)
        self.assertEqual(body['code'], 'CONFLICTO_REVISION')
        self.assertEqual(body['detail'], 'La planilla cambió.')
        self.assertEqual(body['instance'], '/api/x')

    def test_problema_no_incluye_claves_vacias(self):
        body = problema('SIN_PERMISO', 'No autorizado.')
        self.assertNotIn('instance', body)
        self.assertNotIn('errors', body)

    def test_codigo_desconocido_no_filtra_detalle_interno(self):
        body = problema('CODIGO_QUE_NO_EXISTE', 'algo')
        self.assertEqual(body['status'], 500)
        self.assertEqual(body['code'], 'CODIGO_QUE_NO_EXISTE')

    def test_status_suelto_se_traduce_al_catalogo(self):
        self.assertEqual(problema_para_status(404, 'x')['code'], 'NO_ENCONTRADO')
        self.assertEqual(problema_para_status(401, 'x')['code'], 'NO_AUTENTICADO')
        self.assertEqual(problema_para_status(409, 'x')['code'], 'CONFLICTO_ESTADO')
        self.assertEqual(problema_para_status(599, 'x')['code'], 'ERROR_INTERNO')

    def test_el_modelo_publicado_exige_las_claves_del_sobre(self):
        self.assertEqual(
            set(Problem.model_json_schema()['required']),
            {'type', 'title', 'status', 'code', 'detail'},
        )


class Handlers(unittest.TestCase):
    """Cada excepción sale como application/problem+json."""

    def _respuesta(self, handler, exc, path='/api/planillas'):
        return asyncio.run(handler(_request(path), exc))

    def test_error_de_dominio_es_400(self):
        response = self._respuesta(user_error_handler, UserError('Mes inválido.'))
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.media_type, MEDIA_TYPE)
        body = _json(response)
        self.assertEqual(body['code'], 'SOLICITUD_INVALIDA')
        self.assertEqual(body['detail'], 'Mes inválido.')
        self.assertEqual(body['instance'], '/api/planillas')

    def test_http_exception_conserva_status_y_headers(self):
        exc = StarletteHTTPException(
            status_code=404, detail='Versión no encontrada.',
            headers={'WWW-Authenticate': 'Bearer'},
        )
        response = self._respuesta(http_exception_handler, exc)
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.headers['www-authenticate'], 'Bearer')
        body = _json(response)
        self.assertEqual(body['code'], 'NO_ENCONTRADO')
        self.assertEqual(body['status'], 404)
        self.assertEqual(body['detail'], 'Versión no encontrada.')

    def test_conflicto_de_revision_es_409(self):
        from psycopg.errors import SerializationFailure

        response = self._respuesta(
            serialization_failure_handler,
            SerializationFailure('La planilla cambió'),
            path='/api/planillas/versiones/31/lineas',
        )
        self.assertEqual(response.status_code, 409)
        body = _json(response)
        self.assertEqual(body['code'], 'CONFLICTO_REVISION')
        # El mensaje crudo de psycopg no se reenvía: se usa el texto del catálogo.
        self.assertEqual(body['detail'], 'La planilla cambió desde que la abrió. '
                                          'Vuelva a cargarla antes de guardar.')

    def test_validacion_lista_los_campos(self):
        exc = RequestValidationError([{
            'type': 'greater_than_equal',
            'loc': ('body', 'mes'),
            'msg': 'Input should be greater than or equal to 1',
            'input': 0,
        }])
        response = self._respuesta(validation_error_handler, exc)
        self.assertEqual(response.status_code, 422)
        body = _json(response)
        self.assertEqual(body['code'], 'VALIDACION')
        self.assertEqual(body['errors'][0]['campo'], 'body.mes')


class EsquemaOpenAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec = app.openapi()

    def test_creacion_devuelve_revision_edicion(self):
        respuesta = self.spec['paths']['/api/planillas']['post']['responses']['200']
        ref = respuesta['content']['application/json']['schema']['$ref']
        self.assertTrue(ref.endswith('/RespuestaCreacionPlanilla'))

        planilla = self.spec['components']['schemas']['PlanillaCreada']
        self.assertIn('revision_edicion', planilla['required'])
        self.assertIn('revision_edicion', planilla['properties'])

    def test_problem_publicado_en_components(self):
        problem = self.spec['components']['schemas']['Problem']
        self.assertIn('code', problem['properties'])
        self.assertIn('instance', problem['properties'])

    def test_operaciones_declarar_error_uniforme(self):
        operaciones = [
            ('/api/planillas', 'post'),
            ('/api/planillas/versiones/{version_id}/lineas', 'put'),
            ('/api/planillas/versiones/{version_id}/cerrar', 'post'),
            ('/api/documentos/planilla-pdf/{version_id}', 'get'),
        ]
        for path, metodo in operaciones:
            with self.subTest(operacion=f'{metodo.upper()} {path}'):
                responses = self.spec['paths'][path][metodo]['responses']
                for codigo in ('400', '401', '403', '409'):
                    self.assertIn(codigo, responses)
                    self.assertEqual(
                        responses[codigo]['content']['application/json']['schema']['$ref'],
                        '#/components/schemas/Problem',
                    )

    def test_el_contrato_de_creacion_valida_revision_positiva(self):
        with self.assertRaises(Exception):
            PlanillaCreada(
                planilla_id=1, version_id=2, trabajadores_copiados=0,
                revision_edicion=0,
            )

    def test_respuesta_de_creacion_serializa_la_revision(self):
        respuesta = RespuestaCreacionPlanilla(
            planilla=PlanillaCreada(
                planilla_id=1, version_id=2, trabajadores_copiados=3,
                revision_edicion=4,
            ),
            mensaje='ok',
        )
        self.assertEqual(respuesta.model_dump()['planilla']['revision_edicion'], 4)


class PaginacionDeListados(unittest.TestCase):
    """Los listados que crecen sin techo usan el sobre `Pagina[T]`."""

    @classmethod
    def setUpClass(cls):
        cls.spec = app.openapi()

    def test_auditoria_declara_el_sobre_paginado(self):
        respuesta = self.spec['paths']['/api/auditoria']['get']['responses']['200']
        ref = respuesta['content']['application/json']['schema']['$ref']
        nombre = ref.rsplit('/', 1)[-1]
        esquema = self.spec['components']['schemas'][nombre]
        self.assertEqual(
            set(esquema['required']),
            {'items', 'total', 'limite', 'desplazamiento'},
        )

    def test_auditoria_acepta_limite_y_desplazamiento(self):
        parametros = {
            p['name']: p
            for p in self.spec['paths']['/api/auditoria']['get']['parameters']
        }
        self.assertEqual(parametros['limite']['schema']['maximum'], 500)
        self.assertEqual(parametros['limite']['schema']['default'], 100)
        self.assertEqual(parametros['desplazamiento']['schema']['minimum'], 0)


class ManejoDeErroresEnRutas(unittest.TestCase):
    """El mapeo `UserError` → 400 vive en el handler global, no en cada ruta."""

    RUTAS = [
        'routes_planillas',
        'routes_importaciones',
        'routes_documentos',
        'routes_auditoria',
    ]

    def test_los_routers_no_repiten_el_mapeo_de_user_error(self):
        for nombre in self.RUTAS:
            with self.subTest(router=nombre):
                modulo = importlib.import_module(f'cafae.api.{nombre}')
                arbol = ast.parse(Path(inspect.getfile(modulo)).read_text(encoding='utf-8'))
                capturas = [
                    nodo
                    for nodo in ast.walk(arbol)
                    if isinstance(nodo, ast.ExceptHandler)
                    and isinstance(nodo.type, ast.Name)
                    and nodo.type.id == 'UserError'
                ]
                self.assertEqual(
                    capturas, [],
                    f'{nombre} captura UserError: el handler global ya lo traduce.',
                )


if __name__ == '__main__':
    unittest.main()
