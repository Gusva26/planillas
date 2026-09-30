"""Punto de entrada principal de la API REST FastAPI."""
from decimal import Decimal
from datetime import date, datetime
import json
from uuid import UUID
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from cafae.api.routes_auth import router as auth_router, users_router
from cafae.api.routes_catalogos import router as catalogos_router
from cafae.api.routes_trabajadores import router as trabajadores_router
from cafae.api.routes_planillas import router as planillas_router
from cafae.api.routes_importaciones import router as importaciones_router
from cafae.api.routes_documentos import router as documentos_router
from cafae.api.routes_reportes import router as reportes_router
from cafae.api.routes_auditoria import router as auditoria_router
from cafae.security import AccessError, SessionError, UserError


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
    description='API REST oficial para la gestión institucional de planillas CAFAE.',
    version='2.0.0',
    default_response_class=CustomJSONResponse,
)

# CORS permitido para desarrollo frontend moderno
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


@app.exception_handler(UserError)
async def user_error_handler(request: Request, exc: UserError):
    return CustomJSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content={'detail': str(exc), 'tipo': 'UserError'},
    )


@app.exception_handler(SessionError)
async def session_error_handler(request: Request, exc: SessionError):
    return CustomJSONResponse(
        status_code=status.HTTP_401_UNAUTHORIZED,
        content={'detail': str(exc), 'tipo': 'SessionError'},
    )


@app.exception_handler(AccessError)
async def access_error_handler(request: Request, exc: AccessError):
    return CustomJSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={'detail': str(exc), 'tipo': 'AccessError'},
    )


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
@app.get('/_stcore/health')
def health():
    return {'status': 'healthy', 'service': 'cafae-api', 'version': '2.0.0'}


# Servir Frontend Compilado (React + Vite)
for s_dir in [os.path.join(os.getcwd(), 'static'), os.path.join(os.getcwd(), 'frontend', 'dist')]:
    if os.path.exists(s_dir) and os.path.isdir(s_dir):
        app.mount('/', StaticFiles(directory=s_dir, html=True), name='static')
        break

