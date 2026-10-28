"""Entrega conjunta de todos los catálogos para la pantalla de configuración."""
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from cafae.api.deps import get_current_user
from cafae.api.routes_catalogos._base import catalogo_service

router = APIRouter(tags=['Catálogos'])


@router.get('/bundle')
def get_catalogo_bundle(user: Annotated[dict, Depends(get_current_user)]):
    """Devuelve todos los catálogos en un único payload optimizado para la UI."""
    token = user['token']
    try:
        return {
            'niveles': catalogo_service.list_niveles(token, solo_activos=False),
            'instituciones': catalogo_service.list_instituciones(token, solo_activas=False),
            'areas': catalogo_service.list_areas_sede(token, solo_activas=False),
            'metas': catalogo_service.list_metas(token, solo_activos=False),
            'programas': catalogo_service.list_programas(token, solo_activos=False),
            'partidas': catalogo_service.list_partidas(token, solo_activos=False),
            'cargos': catalogo_service.list_cargos(token, solo_activos=False),
            'categorias': catalogo_service.list_categorias(token, solo_activas=False),
            'situaciones': catalogo_service.list_situaciones(token, solo_activas=False),
            'subtipos': catalogo_service.list_subtipos(token, solo_activos=False),
            'firmas': catalogo_service.list_firmas(token, solo_activas=False),
            'tipos_descuento': catalogo_service.list_tipos_descuento(token, solo_activos=False),
            'configuracion': catalogo_service.get_configuracion(token),
        }
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))

