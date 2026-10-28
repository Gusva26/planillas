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
from unittest import mock

sys.path.insert(0, '/app')

from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from cafae.api.errors import CATALOGO, MEDIA_TYPE, Problem, problema, problema_para_status
from cafae.api.main import (
    access_error_handler,
    app,
    http_exception_handler,
    no_encontrado_handler,
    serialization_failure_handler,
    session_error_handler,
    user_error_handler,
    validation_error_handler,
)
from cafae.api.schemas import PlanillaCreada, RespuestaCreacionPlanilla
from cafae.security import NoEncontrado, UserError


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


# `AccessError` y `SessionError` heredan de `UserError`: capturarlas en un router
# esquiva los handlers globales de 403 y 401 igual que capturar la base.
FAMILIA_USER_ERROR = {'UserError', 'AccessError', 'SessionError'}


def _captura_user_error(tipo):
    """True si el `except` atrapa la familia `UserError`, en forma simple o tupla."""
    if isinstance(tipo, ast.Name):
        return tipo.id in FAMILIA_USER_ERROR
    if isinstance(tipo, ast.Tuple):
        return any(_captura_user_error(elemento) for elemento in tipo.elts)
    return False


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

    def test_error_de_permiso_es_403(self):
        from cafae.security import AccessError

        response = self._respuesta(access_error_handler, AccessError('No tiene el permiso.'))
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.media_type, MEDIA_TYPE)
        body = _json(response)
        self.assertEqual(body['code'], 'SIN_PERMISO')
        self.assertEqual(body['detail'], 'No tiene el permiso.')

    def test_sesion_vencida_es_401(self):
        from cafae.security import SessionError

        response = self._respuesta(session_error_handler, SessionError('Sesión vencida.'))
        self.assertEqual(response.status_code, 401)
        body = _json(response)
        self.assertEqual(body['code'], 'NO_AUTENTICADO')
        self.assertEqual(body['detail'], 'Sesión vencida.')

    def test_recurso_inexistente_es_404(self):
        """`NoEncontrado` permite que un servicio señale 404 sin HTTPException."""
        response = self._respuesta(
            no_encontrado_handler,
            NoEncontrado('Versión de planilla no encontrada.'),
            path='/api/planillas/versiones/999999',
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.media_type, MEDIA_TYPE)
        body = _json(response)
        self.assertEqual(body['code'], 'NO_ENCONTRADO')
        self.assertEqual(body['detail'], 'Versión de planilla no encontrada.')

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

    # `routes_auth` queda fuera a propósito: el login distingue credenciales
    # inválidas (401) de solicitudes mal formadas (400), y el handler global no
    # puede deducir esa intención de la clase de excepción.
    RUTAS = [
        'routes_planillas',
        'routes_importaciones',
        'routes_documentos',
        'routes_auditoria',
        'routes_catalogos',
        'routes_reportes',
        'routes_trabajadores',
    ]

    def test_los_routers_no_repiten_el_mapeo_de_user_error(self):
        for nombre in self.RUTAS:
            with self.subTest(router=nombre):
                modulo = importlib.import_module(f'cafae.api.{nombre}')
                arbol = ast.parse(Path(inspect.getfile(modulo)).read_text(encoding='utf-8'))
                capturas = [
                    nodo
                    for nodo in ast.walk(arbol)
                    if isinstance(nodo, ast.ExceptHandler) and _captura_user_error(nodo.type)
                ]
                self.assertEqual(
                    capturas, [],
                    f'{nombre} captura UserError: el handler global ya lo traduce.',
                )

    def test_la_guardia_detecta_tuplas_de_excepciones(self):
        """El chequeo cubre `except (UserError, Otra)`, no solo `except UserError`."""
        arbol = ast.parse(
            'try:\n'
            '    pass\n'
            'except (UserError, SessionError):\n'
            '    pass\n'
        )
        handler = arbol.body[0].handlers[0]
        self.assertTrue(_captura_user_error(handler.type))


class SinSqlEnRouters(unittest.TestCase):
    """D-03: el SQL vive en los servicios, no en los routers.

    Solo cubre los routers ya migrados; `routes_catalogos` se sumará cuando sus
    `DELETE ... RETURNING` se muevan a `CatalogoService`.
    """

    RUTAS = ['routes_planillas', 'routes_documentos']

    def test_los_routers_migrados_no_ejecutan_sql_ni_abren_transacciones(self):
        for nombre in self.RUTAS:
            with self.subTest(router=nombre):
                modulo = importlib.import_module(f'cafae.api.{nombre}')
                arbol = ast.parse(Path(inspect.getfile(modulo)).read_text(encoding='utf-8'))
                ejecuciones = [
                    nodo.func.attr
                    for nodo in ast.walk(arbol)
                    if isinstance(nodo, ast.Call)
                    and isinstance(nodo.func, ast.Attribute)
                    and nodo.func.attr in ('execute', 'data_transaction')
                ]
                self.assertEqual(
                    ejecuciones, [],
                    f'{nombre} todavía accede a la base: moverlo al servicio.',
                )


class RoutersDeleganEnElServicio(unittest.TestCase):
    """D-03/D-04: las rutas piden la lectura consolidada, no la arman."""

    def test_version_detalle_es_una_sola_llamada_al_servicio(self):
        from cafae.api import routes_planillas

        with mock.patch.object(
            routes_planillas.planilla_service, 'get_version_completa'
        ) as servicio:
            servicio.return_value = {'version': {'id': 5}, 'firmas': [], 'lineas': []}
            respuesta = routes_planillas.get_version_detalle(
                5, {'token': 'token'}, query='perez', institucion_id=2, area_id=3)

        self.assertEqual(respuesta['version']['id'], 5)
        servicio.assert_called_once_with(
            'token', 5, institucion_id=2, area_id=3, query='perez')

    def test_documentos_comparte_la_misma_lectura(self):
        from cafae.api import routes_documentos

        with mock.patch.object(
            routes_documentos.pln_service, 'get_version_completa'
        ) as servicio, mock.patch.object(
            routes_documentos.cat_service, 'list_firmas'
        ) as firmas:
            servicio.return_value = {
                'version': {'id': 5, 'cantidad_firmas': 2},
                'firmas': [],
                'lineas': [{'id': 1}],
            }
            firmas.return_value = [{'id': 10}, {'id': 11}, {'id': 12}]
            v_info, filas, firmas_doc = routes_documentos._get_contexto_version(
                'token', 5, permission='generar_documentos')

        servicio.assert_called_once_with('token', 5, permiso='generar_documentos')
        self.assertEqual(v_info['id'], 5)
        self.assertEqual(filas, [{'id': 1}])
        # El catálogo se recorta a las firmas que pide la planilla.
        self.assertEqual([f['id'] for f in firmas_doc], [10, 11])

    def test_boleta_individual_pide_linea_y_version_juntas(self):
        from cafae.api import routes_documentos

        with mock.patch.object(
            routes_documentos.pln_service, 'get_linea_con_version'
        ) as servicio, mock.patch.object(
            routes_documentos, 'generar_boleta_pdf'
        ) as boleta:
            servicio.return_value = ({'anio': 2026, 'mes': 3}, {'id': 11, 'dni': '12345678'})
            boleta.return_value = b'%PDF-1.4'
            respuesta = routes_documentos.descargar_boleta_individual(
                11, {'token': 'token'})

        servicio.assert_called_once_with('token', 11, permiso='generar_documentos')
        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.body, b'%PDF-1.4')


if __name__ == '__main__':
    unittest.main()
