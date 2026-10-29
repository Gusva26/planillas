"""Identidad institucional y tipos de descuento aplicables a la planilla."""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query

from cafae.api.deps import get_current_user, require_role
from cafae.api.routes_catalogos._base import (
    ConfiguracionRequest,
    TipoDescuentoRequest,
    ToggleEstadoRequest,
    catalogo_service,
)

router = APIRouter(tags=['Catálogos'])


# =============================================================================
# CONFIGURACIÓN E IDENTIDAD INSTITUCIONAL
# =============================================================================
@router.get('/configuracion')
def get_configuracion(user: Annotated[dict, Depends(get_current_user)]):
    return catalogo_service.get_configuracion(user['token'])


@router.put('/configuracion')
def update_configuracion(
    req: ConfiguracionRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    catalogo_service.update_configuracion(
        user['token'], req.nombre_institucion, req.nombre_sistema, req.zona_horaria
    )
    return {'ok': True, 'mensaje': 'Configuración institucional actualizada con éxito.'}


# =============================================================================
# TIPOS DE DESCUENTO
# =============================================================================
@router.get('/tipos-descuento')
def list_tipos_descuento(
    user: Annotated[dict, Depends(get_current_user)],
    solo_activos: bool = False,
    ambito: Optional[str] = None
):
    return catalogo_service.list_tipos_descuento(user['token'], solo_activos=solo_activos, ambito=ambito)


@router.post('/tipos-descuento')
def create_tipo_descuento(
    req: TipoDescuentoRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    new_id = catalogo_service.create_tipo_descuento(
        user['token'],
        codigo=req.codigo or req.nombre,
        nombre=req.nombre,
        orden=req.orden,
        aplica_iiee=req.aplica_iiee if req.aplica_iiee is not None else True,
        aplica_sede=req.aplica_sede if req.aplica_sede is not None else True,
    )
    return {'ok': True, 'id': new_id, 'mensaje': 'Tipo de descuento registrado con éxito.'}


@router.put('/tipos-descuento/{item_id}')
def update_tipo_descuento(
    item_id: int,
    req: TipoDescuentoRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    catalogo_service.update_tipo_descuento(
        user['token'],
        tipo_id=item_id,
        nombre=req.nombre,
        orden=req.orden or 1,
        aplica_iiee=req.aplica_iiee if req.aplica_iiee is not None else True,
        aplica_sede=req.aplica_sede if req.aplica_sede is not None else True,
        activo=req.activo if req.activo is not None else True,
    )
    return {'ok': True, 'mensaje': 'Tipo de descuento actualizado con éxito.'}


@router.patch('/tipos-descuento/{item_id}/estado')
def set_active_tipo_descuento(
    item_id: int,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))],
    body: Optional[ToggleEstadoRequest] = None,
    activo: Optional[bool] = Query(None)
):
    val_activo = activo if activo is not None else (body.activo if body else None)
    token = user['token']
    nuevo = catalogo_service.toggle_tipo_descuento(token, item_id, val_activo)
    return {'ok': True, 'activo': nuevo, 'mensaje': f'Tipo de descuento {"activado" if nuevo else "desactivado"} con éxito.'}

