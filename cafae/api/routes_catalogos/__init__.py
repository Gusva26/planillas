"""Rutas de catálogos institucionales y presupuestarios.

El paquete se divide por grupo para que ningún módulo repita el patrón CRUD de
los demás. El prefijo `/catalogos` se aplica aquí, una sola vez.
"""
from fastapi import APIRouter

from cafae.api.routes_catalogos import (
    bundle,
    configuracion,
    firmas,
    institucional,
    personal,
    presupuesto,
)
from cafae.api.routes_catalogos._base import catalogo_service

# Reexportados a propósito: las pruebas y cualquier import histórico siguen
# encontrando las rutas en `cafae.api.routes_catalogos`.
from cafae.api.routes_catalogos.firmas import delete_firma
from cafae.api.routes_catalogos.institucional import (
    delete_area,
    delete_institucion,
    delete_meta,
    delete_nivel,
    list_areas,
    list_instituciones,
    list_metas,
    list_niveles,
)
from cafae.api.routes_catalogos.personal import (
    delete_cargo,
    delete_categoria,
    delete_situacion,
    delete_subtipo,
)
from cafae.api.routes_catalogos.presupuesto import (
    delete_partida,
    delete_programa,
    list_partidas,
    list_programas,
)

router = APIRouter(prefix='/catalogos', tags=['Catálogos'])
router.include_router(bundle.router)
router.include_router(institucional.router)
router.include_router(presupuesto.router)
router.include_router(personal.router)
router.include_router(firmas.router)
router.include_router(configuracion.router)

__all__ = [
    'router',
    'catalogo_service',
    'delete_area',
    'delete_cargo',
    'delete_categoria',
    'delete_firma',
    'delete_institucion',
    'delete_meta',
    'delete_nivel',
    'delete_partida',
    'delete_programa',
    'delete_situacion',
    'delete_subtipo',
    'list_areas',
    'list_instituciones',
    'list_metas',
    'list_niveles',
    'list_partidas',
    'list_programas',
]
