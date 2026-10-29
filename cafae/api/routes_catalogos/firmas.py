"""Firmas autorizadas que se imprimen al pie de los documentos oficiales."""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from cafae.api.deps import get_current_user, require_role
from cafae.api.routes_catalogos._base import (
    FirmaRequest,
    ToggleEstadoRequest,
    catalogo_service,
)

router = APIRouter(tags=['Catálogos'])


# =============================================================================
# FIRMAS
# =============================================================================
@router.get('/firmas')
def list_firmas(user: Annotated[dict, Depends(get_current_user)], solo_activos: bool = False):
    return catalogo_service.list_firmas(user['token'], solo_activas=solo_activos)


@router.post('/firmas')
def create_firma(
    req: FirmaRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    nombre = req.nombre_completo or req.nombre_firmante
    cargo = req.cargo or req.cargo_firmante
    if not nombre or not cargo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Nombre y cargo de la firma son obligatorios.')
    new_id = catalogo_service.create_firma(
        user['token'], nombre, cargo
    )
    return {'ok': True, 'id': new_id, 'mensaje': 'Firma registrada con éxito.'}


@router.put('/firmas/{item_id}')
def update_firma(
    item_id: int,
    req: FirmaRequest,
    activo: bool = True,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))] = None
):
    nombre = req.nombre_completo or req.nombre_firmante
    cargo = req.cargo or req.cargo_firmante
    if not nombre or not cargo:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Nombre y cargo de la firma son obligatorios.')
    catalogo_service.update_firma(
        user['token'], item_id, nombre, cargo, activo
    )
    return {'ok': True, 'mensaje': 'Firma actualizada con éxito.'}


@router.patch('/firmas/{item_id}/estado')
def set_active_firma(
    item_id: int,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))],
    body: Optional[ToggleEstadoRequest] = None,
    activo: Optional[bool] = Query(None)
):
    val_activo = activo if activo is not None else (body.activo if body else None)
    if val_activo is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='El campo "activo" es obligatorio.')
    token = user['token']
    firmas = catalogo_service.list_firmas(token, solo_activas=False)
    target = next((f for f in firmas if f['id'] == item_id), None)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Firma no encontrada.')
    catalogo_service.update_firma(token, item_id, target['nombre_completo'], target['cargo'], val_activo)
    return {'ok': True, 'mensaje': f'Firma {"activada" if val_activo else "desactivada"} con éxito.'}


@router.delete('/firmas/{item_id}')
def delete_firma(
    item_id: int,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    catalogo_service.delete_firma(user['token'], item_id)
    return {'ok': True, 'mensaje': 'Firma autorizada eliminada con éxito.'}

