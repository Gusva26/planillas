"""Contrato público del API: sobre de error y esquema OpenAPI.

No requiere base de datos: valida el contrato que consume el frontend.
"""
import ast
import asyncio
import importlib
import inspect
import json
import logging
import sys
import unittest
from pathlib import Path
from unittest import mock

sys.path.insert(0, '/app')

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request

from cafae.api.errors import CATALOGO, MEDIA_TYPE, Problem, problema, problema_para_status
from cafae.api.main import (
    access_error_handler,
    app,
    conflicto_handler,
    error_interno_handler,
    http_exception_handler,
    no_encontrado_handler,
    serialization_failure_handler,
    session_error_handler,
    user_error_handler,
    validation_error_handler,
)
from cafae.api.schemas import PlanillaCreada, RespuestaCreacionPlanilla
from cafae.security import Conflicto, NoEncontrado, UserError


def _request(path='/api/planillas', headers=None):
    return Request({
        'type': 'http',
        'http_version': '1.1',
        'method': 'GET',
        'scheme': 'http',
        'path': path,
        'root_path': '',
        'query_string': b'',
        'headers': [(k.lower().encode(), v.encode()) for k, v in (headers or {}).items()],
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

    def test_recurso_en_uso_es_409(self):
        """`Conflicto` evita que un catálogo en uso caiga como 400 genérico."""
        response = self._respuesta(
            conflicto_handler,
            Conflicto('No se puede eliminar el cargo porque está asignado a trabajadores.'),
            path='/api/catalogos/cargos/7',
        )
        self.assertEqual(response.status_code, 409)
        self.assertEqual(response.media_type, MEDIA_TYPE)
        body = _json(response)
        self.assertEqual(body['code'], 'CONFLICTO_ESTADO')

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

    def test_fallo_no_clasificado_usa_el_sobre(self):
        """Sin handler, Starlette responde `text/plain` y el cliente no lee `code`."""
        response = self._respuesta(
            error_interno_handler, RuntimeError('password=secreto'))
        self.assertEqual(response.status_code, 500)
        self.assertEqual(response.media_type, MEDIA_TYPE)
        body = _json(response)
        self.assertEqual(body['code'], 'ERROR_INTERNO')
        # El detalle de la excepción no se filtra al cliente.
        self.assertNotIn('secreto', body['detail'])
        self.assertEqual(body['instance'], '/api/planillas')

    def test_el_500_conserva_el_id_de_correlacion(self):
        """El handler corre fuera del middleware, así que lee el id del estado."""
        peticion = _request()
        peticion.state.request_id = 'abc123'
        response = asyncio.run(error_interno_handler(peticion, RuntimeError('x')))
        self.assertEqual(response.headers['X-Request-ID'], 'abc123')

    def test_el_500_esta_registrado_como_handler_global(self):
        self.assertIn(Exception, app.exception_handlers)


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

    def test_los_62_endpoints_de_catalogos_siguen_registrados(self):
        """D-07: partir el archivo en un paquete no pierde ni duplica rutas."""
        operaciones = [
            (metodo.upper(), ruta)
            for ruta, metodos in self.spec['paths'].items()
            if ruta.startswith('/api/catalogos')
            for metodo in metodos
        ]

        self.assertEqual(len(operaciones), 62)
        self.assertEqual(
            {metodo: sum(1 for m, _ in operaciones if m == metodo)
             for metodo, _ in operaciones},
            {'GET': 14, 'POST': 12, 'PUT': 13, 'PATCH': 12, 'DELETE': 11},
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


class CorrelacionYRegistro(unittest.TestCase):
    """D-08: cada solicitud deja una línea JSON con su identificador."""

    def test_el_formateador_emite_json_con_el_id_vigente(self):
        from cafae.logging_conf import FormateadorJSON, request_id

        marca = request_id.set('prueba-123')
        try:
            registro = logging.LogRecord(
                'cafae.api', logging.INFO, __file__, 1, 'solicitud', None, None)
            registro.metodo = 'GET'
            registro.ruta = '/api/health'
            linea = json.loads(FormateadorJSON().format(registro))
        finally:
            request_id.reset(marca)

        self.assertEqual(linea['request_id'], 'prueba-123')
        self.assertEqual(linea['metodo'], 'GET')
        self.assertEqual(linea['ruta'], '/api/health')
        self.assertEqual(linea['nivel'], 'INFO')

    def test_la_respuesta_devuelve_el_id_recibido(self):
        from cafae.api.main import correlacion
        from cafae.logging_conf import request_id

        visto = {}

        async def siguiente(peticion):
            visto['id'] = request_id.get()
            return JSONResponse({'ok': True})

        respuesta = asyncio.run(
            correlacion(_request('/api/health', {'X-Request-ID': 'abc123'}), siguiente))

        self.assertEqual(visto['id'], 'abc123')
        self.assertEqual(respuesta.headers['x-request-id'], 'abc123')
        # El contexto no queda contaminado para la siguiente solicitud.
        self.assertEqual(request_id.get(), '-')

    def test_sin_cabecera_se_genera_un_id(self):
        from cafae.api.main import correlacion

        async def siguiente(peticion):
            return JSONResponse({'ok': True})

        respuesta = asyncio.run(correlacion(_request('/api/health'), siguiente))

        self.assertEqual(len(respuesta.headers['x-request-id']), 32)


class ConfiguracionDeCors(unittest.TestCase):
    """D-09: sin comodín ni credenciales en CORS."""

    def setUp(self):
        from cafae.api.main import app

        self.opciones = next(
            middleware.kwargs
            for middleware in app.user_middleware
            if middleware.cls.__name__ == 'CORSMiddleware'
        )

    def test_no_abre_cualquier_origen(self):
        self.assertNotIn('*', self.opciones['allow_origins'])
        self.assertTrue(self.opciones['allow_origins'])

    def test_no_admite_credenciales_de_navegador(self):
        # La sesión viaja en `Authorization`, no en cookies.
        self.assertFalse(self.opciones['allow_credentials'])

    def test_expone_el_id_de_correlacion(self):
        self.assertIn('X-Request-ID', self.opciones['expose_headers'])
        self.assertIn('X-Request-ID', self.opciones['allow_headers'])


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

    Cubre los tres routers que llegaron a tener SQL inline, incluidos los
    módulos del paquete `routes_catalogos`. Si aparece un `conn.execute` o un
    `data_transaction` en la capa HTTP, la prueba falla.
    """

    RUTAS = ['routes_catalogos', 'routes_planillas', 'routes_documentos']

    @staticmethod
    def _archivos(nombre):
        """Un módulo suelto o todos los archivos de un paquete de rutas."""
        ruta = Path(inspect.getfile(importlib.import_module(f'cafae.api.{nombre}')))
        if ruta.name == '__init__.py':
            return sorted(ruta.parent.glob('*.py'))
        return [ruta]

    def test_los_routers_migrados_no_ejecutan_sql_ni_abren_transacciones(self):
        for nombre in self.RUTAS:
            for ruta in self._archivos(nombre):
                with self.subTest(router=nombre, archivo=ruta.name):
                    arbol = ast.parse(ruta.read_text(encoding='utf-8'))
                    ejecuciones = [
                        nodo.func.attr
                        for nodo in ast.walk(arbol)
                        if isinstance(nodo, ast.Call)
                        and isinstance(nodo.func, ast.Attribute)
                        and nodo.func.attr in ('execute', 'data_transaction')
                    ]
                    self.assertEqual(
                        ejecuciones, [],
                        f'{ruta.name} todavía accede a la base: moverlo al servicio.',
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

    def test_documentos_usan_las_firmas_de_la_version(self):
        """D-04: el documento se firma con la copia de la versión, no con el catálogo.

        `planilla_firmas` guarda nombre y cargo al crear y al cerrar. Leer el
        catálogo vivo haría que una planilla ya cerrada cambiara de firmantes si
        alguien edita el catálogo después.
        """
        from cafae.api import routes_documentos

        with mock.patch.object(
            routes_documentos.pln_service, 'get_version_completa'
        ) as servicio, mock.patch(
            'cafae.catalogos.CatalogoService.list_firmas'
        ) as catalogo:
            servicio.return_value = {
                'version': {'id': 5, 'cantidad_firmas': 4, 'estado': 'CERRADA'},
                'firmas': [{'id': 10}, {'id': 11}, {'id': 12}, {'id': 13}],
                'lineas': [{'id': 1}],
            }
            v_info, filas, firmas_doc = routes_documentos._get_contexto_version(
                'token', 5, permission='generar_documentos')

        servicio.assert_called_once_with('token', 5, permiso='generar_documentos')
        catalogo.assert_not_called()
        self.assertEqual(v_info['id'], 5)
        self.assertEqual(filas, [{'id': 1}])
        self.assertEqual([f['id'] for f in firmas_doc], [10, 11, 12, 13])

    def test_documentos_no_rellenan_firmas_que_la_version_no_tiene(self):
        """Un recorte o relleno silencioso escondería un bloque de firmas incompleto."""
        from cafae.api import routes_documentos

        with mock.patch.object(
            routes_documentos.pln_service, 'get_version_completa'
        ) as servicio:
            servicio.return_value = {
                'version': {'id': 5, 'cantidad_firmas': 4, 'estado': 'ABIERTA'},
                'firmas': [{'id': 10}, {'id': 11}, {'id': 12}],
                'lineas': [],
            }
            _, _, firmas_doc = routes_documentos._get_contexto_version('token', 5)

        self.assertEqual([f['id'] for f in firmas_doc], [10, 11, 12])

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

    def test_los_borrados_de_catalogos_delegan_en_el_servicio(self):
        """Cada `DELETE` del router es una llamada al servicio, sin SQL."""
        from cafae.api import routes_catalogos

        casos = [
            (routes_catalogos.delete_nivel, 'delete_nivel'),
            (routes_catalogos.delete_institucion, 'delete_institucion'),
            (routes_catalogos.delete_area, 'delete_area_sede'),
            (routes_catalogos.delete_meta, 'delete_meta'),
            (routes_catalogos.delete_firma, 'delete_firma'),
            (routes_catalogos.delete_programa, 'delete_programa'),
            (routes_catalogos.delete_partida, 'delete_partida'),
            (routes_catalogos.delete_cargo, 'delete_cargo'),
            (routes_catalogos.delete_categoria, 'delete_categoria'),
            (routes_catalogos.delete_situacion, 'delete_situacion'),
            (routes_catalogos.delete_subtipo, 'delete_subtipo'),
        ]

        for ruta, metodo in casos:
            with self.subTest(ruta=ruta.__name__, servicio=metodo):
                with mock.patch.object(
                    routes_catalogos.catalogo_service, metodo
                ) as servicio:
                    respuesta = ruta(7, {'token': 'token'})

                servicio.assert_called_once_with('token', 7)
                self.assertTrue(respuesta['ok'])

    def test_el_bundle_no_convierte_un_fallo_del_servidor_en_400(self):
        """Un `except Exception` en la ruta enmascaraba los 500 como 400."""
        from cafae.api.routes_catalogos import bundle

        with mock.patch.object(
            bundle.catalogo_service, 'list_niveles', side_effect=RuntimeError('sin conexión')
        ):
            with self.assertRaises(RuntimeError):
                bundle.get_catalogo_bundle({'token': 'token'})


if __name__ == '__main__':
    unittest.main()
