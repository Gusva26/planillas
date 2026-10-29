"""Catálogos presupuestarios: programas y partidas."""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from cafae.api.deps import get_current_user, require_role
from cafae.api.routes_catalogos._base import (
    PartidaRequest,
    ProgramaRequest,
    ToggleEstadoRequest,
    catalogo_service,
)

router = APIRouter(tags=['Catálogos'])


# =============================================================================
# PROGRAMAS PRESUPUESTARIOS
# =============================================================================
@router.get('/programas')
def list_programas(user: Annotated[dict, Depends(get_current_user)], solo_activos: bool = False):
    return catalogo_service.list_programas(user['token'], solo_activos=solo_activos)


@router.post('/programas')
def create_programa(
    req: ProgramaRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    new_id = catalogo_service.create_programa(
        user['token'], req.codigo, req.nombre, orden=req.orden or 0, padre_id=req.padre_id
    )
    return {'ok': True, 'id': new_id, 'mensaje': 'Programa registrado con éxito.'}


@router.put('/programas/{item_id}')
def update_programa(
    item_id: int,
    req: ProgramaRequest,
    activo: bool = True,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))] = None
):
    catalogo_service.update_programa(
        user['token'], item_id, req.codigo, req.nombre, req.orden or 0, req.padre_id, activo
    )
    return {'ok': True, 'mensaje': 'Programa actualizado con éxito.'}


@router.patch('/programas/{item_id}/estado')
def set_active_programa(
    item_id: int,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))],
    body: Optional[ToggleEstadoRequest] = None,
    activo: Optional[bool] = Query(None)
):
    val_activo = activo if activo is not None else (body.activo if body else None)
    if val_activo is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='El campo "activo" es obligatorio.')
    token = user['token']
    progs = catalogo_service.list_programas(token, solo_activos=False)
    target = next((p for p in progs if p['id'] == item_id), None)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Programa no encontrado.')
    catalogo_service.update_programa(
        token, item_id, target['codigo'], target['nombre'], target['orden'], target['padre_id'], val_activo
    )
    return {'ok': True, 'mensaje': f'Programa {"activado" if val_activo else "desactivado"} con éxito.'}


@router.delete('/programas/{item_id}')
def delete_programa(
    item_id: int,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    catalogo_service.delete_programa(user['token'], item_id)
    return {'ok': True, 'mensaje': 'Programa eliminado con éxito.'}


# =============================================================================
# PARTIDAS PRESUPUESTARIAS
# =============================================================================
@router.get('/partidas')
def list_partidas(user: Annotated[dict, Depends(get_current_user)], solo_activos: bool = False):
    return catalogo_service.list_partidas(user['token'], solo_activos=solo_activos)


@router.post('/partidas')
def create_partida(
    req: PartidaRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    new_id = catalogo_service.create_partida(user['token'], req.codigo, req.descripcion)
    return {'ok': True, 'id': new_id, 'mensaje': 'Partida registrada con éxito.'}


@router.put('/partidas/{item_id}')
def update_partida(
    item_id: int,
    req: PartidaRequest,
    activo: bool = True,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))] = None
):
    catalogo_service.update_partida(user['token'], item_id, req.codigo, req.descripcion, activo)
    return {'ok': True, 'mensaje': 'Partida actualizada con éxito.'}


@router.patch('/partidas/{item_id}/estado')
def set_active_partida(
    item_id: int,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))],
    body: Optional[ToggleEstadoRequest] = None,
    activo: Optional[bool] = Query(None)
):
    val_activo = activo if activo is not None else (body.activo if body else None)
    if val_activo is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='El campo "activo" es obligatorio.')
    token = user['token']
    target = catalogo_service.get_partida(token, item_id)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Partida no encontrada.')
    catalogo_service.update_partida(token, item_id, target['codigo'], target['descripcion'], val_activo)
    return {'ok': True, 'mensaje': f'Partida {"activada" if val_activo else "desactivada"} con éxito.'}


@router.delete('/partidas/{item_id}')
def delete_partida(
    item_id: int,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    catalogo_service.delete_partida(user['token'], item_id)
    return {'ok': True, 'mensaje': 'Partida eliminada con éxito.'}

