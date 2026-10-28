"""Catálogos del legajo: cargos, categorías, situaciones y subtipos."""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from cafae.api.deps import get_current_user, require_role
from cafae.api.routes_catalogos._base import (
    CargoRequest,
    CategoriaRequest,
    SituacionRequest,
    SubtipoRequest,
    ToggleEstadoRequest,
    catalogo_service,
)

router = APIRouter(tags=['Catálogos'])


# =============================================================================
# CARGOS
# =============================================================================
@router.get('/cargos')
def list_cargos(user: Annotated[dict, Depends(get_current_user)], solo_activos: bool = False):
    return catalogo_service.list_cargos(user['token'], solo_activos=solo_activos)


@router.post('/cargos')
def create_cargo(
    req: CargoRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    new_id = catalogo_service.create_cargo(user['token'], req.nombre)
    return {'ok': True, 'id': new_id, 'mensaje': 'Cargo registrado con éxito.'}


@router.put('/cargos/{item_id}')
def update_cargo(
    item_id: int,
    req: CargoRequest,
    activo: bool = True,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))] = None
):
    catalogo_service.update_cargo(user['token'], item_id, req.nombre, activo)
    return {'ok': True, 'mensaje': 'Cargo actualizado con éxito.'}


@router.patch('/cargos/{item_id}/estado')
def set_active_cargo(
    item_id: int,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))],
    body: Optional[ToggleEstadoRequest] = None,
    activo: Optional[bool] = Query(None)
):
    val_activo = activo if activo is not None else (body.activo if body else None)
    if val_activo is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='El campo "activo" es obligatorio.')
    token = user['token']
    cargos = catalogo_service.list_cargos(token, solo_activos=False)
    target = next((c for c in cargos if c['id'] == item_id), None)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Cargo no encontrado.')
    catalogo_service.update_cargo(token, item_id, target['nombre'], val_activo)
    return {'ok': True, 'mensaje': f'Cargo {"activado" if val_activo else "desactivado"} con éxito.'}


@router.delete('/cargos/{item_id}')
def delete_cargo(
    item_id: int,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    catalogo_service.delete_cargo(user['token'], item_id)
    return {'ok': True, 'mensaje': 'Cargo eliminado con éxito.'}


# =============================================================================
# CATEGORÍAS REMUNERATIVAS
# =============================================================================
@router.get('/categorias')
def list_categorias(user: Annotated[dict, Depends(get_current_user)], solo_activos: bool = False):
    return catalogo_service.list_categorias(user['token'], solo_activas=solo_activos)


@router.post('/categorias')
def create_categoria(
    req: CategoriaRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    new_id = catalogo_service.create_categoria(user['token'], req.codigo, req.descripcion)
    return {'ok': True, 'id': new_id, 'mensaje': 'Categoría registrada con éxito.'}


@router.put('/categorias/{item_id}')
def update_categoria(
    item_id: int,
    req: CategoriaRequest,
    activo: bool = True,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))] = None
):
    catalogo_service.update_categoria(user['token'], item_id, req.codigo, req.descripcion, activo)
    return {'ok': True, 'mensaje': 'Categoría actualizada con éxito.'}


@router.patch('/categorias/{item_id}/estado')
def set_active_categoria(
    item_id: int,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))],
    body: Optional[ToggleEstadoRequest] = None,
    activo: Optional[bool] = Query(None)
):
    val_activo = activo if activo is not None else (body.activo if body else None)
    if val_activo is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='El campo "activo" es obligatorio.')
    token = user['token']
    cats = catalogo_service.list_categorias(token, solo_activas=False)
    target = next((c for c in cats if c['id'] == item_id), None)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Categoría no encontrada.')
    catalogo_service.update_categoria(token, item_id, target['codigo'], target['descripcion'], val_activo)
    return {'ok': True, 'mensaje': f'Categoría {"activada" if val_activo else "desactivada"} con éxito.'}


@router.delete('/categorias/{item_id}')
def delete_categoria(
    item_id: int,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    catalogo_service.delete_categoria(user['token'], item_id)
    return {'ok': True, 'mensaje': 'Categoría eliminada con éxito.'}


# =============================================================================
# SITUACIONES LABORALES
# =============================================================================
@router.get('/situaciones')
def list_situaciones(user: Annotated[dict, Depends(get_current_user)], solo_activos: bool = False):
    return catalogo_service.list_situaciones(user['token'], solo_activas=solo_activos)


@router.post('/situaciones')
def create_situacion(
    req: SituacionRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    new_id = catalogo_service.create_situacion(user['token'], req.nombre)
    return {'ok': True, 'id': new_id, 'mensaje': 'Situación laboral registrada con éxito.'}


@router.put('/situaciones/{item_id}')
def update_situacion(
    item_id: int,
    req: SituacionRequest,
    activo: bool = True,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))] = None
):
    catalogo_service.update_situacion(user['token'], item_id, req.nombre, activo)
    return {'ok': True, 'mensaje': 'Situación laboral actualizada con éxito.'}


@router.patch('/situaciones/{item_id}/estado')
def set_active_situacion(
    item_id: int,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))],
    body: Optional[ToggleEstadoRequest] = None,
    activo: Optional[bool] = Query(None)
):
    val_activo = activo if activo is not None else (body.activo if body else None)
    if val_activo is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='El campo "activo" es obligatorio.')
    token = user['token']
    sits = catalogo_service.list_situaciones(token, solo_activas=False)
    target = next((s for s in sits if s['id'] == item_id), None)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Situación no encontrada.')
    catalogo_service.update_situacion(token, item_id, target['nombre'], val_activo)
    return {'ok': True, 'mensaje': f'Situación {"activada" if val_activo else "desactivada"} con éxito.'}


@router.delete('/situaciones/{item_id}')
def delete_situacion(
    item_id: int,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    catalogo_service.delete_situacion(user['token'], item_id)
    return {'ok': True, 'mensaje': 'Situación laboral eliminada con éxito.'}


# =============================================================================
# SUBTIPOS DE TRABAJADOR
# =============================================================================
@router.get('/subtipos')
def list_subtipos(user: Annotated[dict, Depends(get_current_user)], solo_activos: bool = False):
    return catalogo_service.list_subtipos(user['token'], solo_activos=solo_activos)


@router.post('/subtipos')
def create_subtipo(
    req: SubtipoRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    new_id = catalogo_service.create_subtipo(user['token'], req.nombre)
    return {'ok': True, 'id': new_id, 'mensaje': 'Subtipo de trabajador registrado con éxito.'}


@router.put('/subtipos/{item_id}')
def update_subtipo(
    item_id: int,
    req: SubtipoRequest,
    activo: bool = True,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))] = None
):
    catalogo_service.update_subtipo(user['token'], item_id, req.nombre, activo)
    return {'ok': True, 'mensaje': 'Subtipo actualizado con éxito.'}


@router.patch('/subtipos/{item_id}/estado')
def set_active_subtipo(
    item_id: int,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))],
    body: Optional[ToggleEstadoRequest] = None,
    activo: Optional[bool] = Query(None)
):
    val_activo = activo if activo is not None else (body.activo if body else None)
    if val_activo is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='El campo "activo" es obligatorio.')
    token = user['token']
    subs = catalogo_service.list_subtipos(token, solo_activos=False)
    target = next((s for s in subs if s['id'] == item_id), None)
    if not target:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Subtipo no encontrado.')
    catalogo_service.update_subtipo(token, item_id, target['nombre'], val_activo)
    return {'ok': True, 'mensaje': f'Subtipo {"activado" if val_activo else "desactivado"} con éxito.'}


@router.delete('/subtipos/{item_id}')
def delete_subtipo(
    item_id: int,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    catalogo_service.delete_subtipo(user['token'], item_id)
    return {'ok': True, 'mensaje': 'Subtipo eliminado con éxito.'}

