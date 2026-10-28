"""Punto de entrada principal de la API REST FastAPI."""
from decimal import Decimal
from datetime import date, datetime
import json
from uuid import UUID
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from psycopg.errors import SerializationFailure
from starlette.exceptions import HTTPException as StarletteHTTPException

from cafae.api.errors import MEDIA_TYPE, Problem, problema, problema_para_status
from cafae.api.routes_auth import router as auth_router, users_router
from cafae.api.routes_catalogos import router as catalogos_router
from cafae.api.routes_trabajadores import router as trabajadores_router
from cafae.api.routes_planillas import router as planillas_router
from cafae.api.routes_importaciones import router as importaciones_router
from cafae.api.routes_documentos import router as documentos_router
from cafae.api.routes_reportes import router as reportes_router
from cafae.api.routes_auditoria import router as auditoria_router
from cafae.security import AccessError, Conflicto, NoEncontrado, SessionError, UserError


class CustomJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)  # Para transporte JSON a frontend
        if isinstance(obj, (datetime, date)):
            return obj.isoformat()
        if isinstance(obj, UUID):
            return str(obj)
        return super().default(obj)


class CustomJSONResponse(JSONResponse):
    def render(self, content) -> bytes:
        return json.dumps(
            content,
            ensure_ascii=False,
            allow_nan=False,
            indent=None,
            separators=(',', ':'),
            cls=CustomJSONEncoder,
        ).encode('utf-8')


app = FastAPI(
    title='Sistema de Planillas CAFAE · UGEL Chepén API',
    description=(
        'API REST oficial para la gestión institucional de planillas CAFAE.\n\n'
        '**Errores**: todas las respuestas de error usan el mismo sobre '
        '(`type`, `title`, `status`, `code`, `detail`, `instance`), servido como '
        '`application/problem+json`. El cliente debe ramificar por `code`.\n\n'
        '**Concurrencia**: las operaciones de edición y cierre exigen la '
        '`revision_esperada` vigente y responden `409` (`CONFLICTO_REVISION`) '
        'si otro usuario ya la movió.'
    ),
    version='2.1.0',
    default_response_class=CustomJSONResponse,
    responses={
        400: {'model': Problem, 'description': 'Solicitud inválida'},
        401: {'model': Problem, 'description': 'Sesión ausente o vencida'},
        403: {'model': Problem, 'description': 'El rol no permite la operación'},
        409: {'model': Problem, 'description': 'Conflicto de revisión o de estado'},
        422: {'model': Problem, 'description': 'Validación de campos'},
    },
)

# CORS permitido para desarrollo frontend moderno
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


def _respuesta_problema(body: dict, status_code: int) -> CustomJSONResponse:
    return CustomJSONResponse(
        status_code=status_code,
        content=body,
        media_type=MEDIA_TYPE,
    )


@app.exception_handler(UserError)
async def user_error_handler(request: Request, exc: UserError):
    """Error de dominio esperado: la regla de negocio rechazó la operación."""
    body = problema('SOLICITUD_INVALIDA', str(exc), instance=request.url.path)
    return _respuesta_problema(body, body['status'])


@app.exception_handler(SessionError)
async def session_error_handler(request: Request, exc: SessionError):
    body = problema('NO_AUTENTICADO', str(exc), instance=request.url.path)
    return _respuesta_problema(body, body['status'])


@app.exception_handler(NoEncontrado)
async def no_encontrado_handler(request: Request, exc: NoEncontrado):
    """El servicio no halló el recurso: `404` en vez de un `400` genérico."""
    body = problema('NO_ENCONTRADO', str(exc), instance=request.url.path)
    return _respuesta_problema(body, body['status'])


@app.exception_handler(Conflicto)
async def conflicto_handler(request: Request, exc: Conflicto):
    """El recurso existe pero está en uso: `409` en vez de un `400` genérico."""
    body = problema('CONFLICTO_ESTADO', str(exc), instance=request.url.path)
    return _respuesta_problema(body, body['status'])


@app.exception_handler(AccessError)
async def access_error_handler(request: Request, exc: AccessError):
    body = problema('SIN_PERMISO', str(exc), instance=request.url.path)
    return _respuesta_problema(body, body['status'])


@app.exception_handler(SerializationFailure)
async def serialization_failure_handler(request: Request, exc: SerializationFailure):
    """Conflicto de revisión detectado en la base (`bloquear_edicion`)."""
    body = problema(
        'CONFLICTO_REVISION',
        'La planilla cambió desde que la abrió. Vuelva a cargarla antes de guardar.',
        instance=request.url.path,
    )
    return _respuesta_problema(body, body['status'])


@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    """Uniforma los `HTTPException` de FastAPI al mismo sobre."""
    body = problema_para_status(exc.status_code, str(exc.detail), instance=request.url.path)
    response = _respuesta_problema(body, exc.status_code)
    if exc.headers:
        response.headers.update(exc.headers)
    return response


@app.exception_handler(RequestValidationError)
async def validation_error_handler(request: Request, exc: RequestValidationError):
    errores = [
        {
            'campo': '.'.join(str(parte) for parte in error.get('loc', ())),
            'mensaje': error.get('msg', 'Valor inválido.'),
        }
        for error in exc.errors()
    ]
    body = problema(
        'VALIDACION',
        'La solicitud tiene campos inválidos o faltantes.',
        instance=request.url.path,
        errors=errores,
    )
    return _respuesta_problema(body, body['status'])


# Registrar Routers bajo /api
api_prefix = '/api'
app.include_router(auth_router, prefix=api_prefix)
app.include_router(users_router, prefix=api_prefix)
app.include_router(catalogos_router, prefix=api_prefix)
app.include_router(trabajadores_router, prefix=api_prefix)
app.include_router(planillas_router, prefix=api_prefix)
app.include_router(importaciones_router, prefix=api_prefix)
app.include_router(documentos_router, prefix=api_prefix)
app.include_router(reportes_router, prefix=api_prefix)
app.include_router(auditoria_router, prefix=api_prefix)


import os
from fastapi.staticfiles import StaticFiles

@app.get('/api/health')
def health():
    return {'status': 'healthy', 'service': 'cafae-api', 'version': '2.1.0'}


# Servir Frontend Compilado (React + Vite)
for s_dir in [os.path.join(os.getcwd(), 'static'), os.path.join(os.getcwd(), 'frontend', 'dist')]:
    if os.path.exists(s_dir) and os.path.isdir(s_dir):
        app.mount('/', StaticFiles(directory=s_dir, html=True), name='static')
        break

