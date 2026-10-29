"""Catálogos de estructura: niveles, instituciones, áreas de sede y metas.

Niveles e instituciones son la base del maestro de II.EE.; las áreas de sede
hacen lo propio para el personal administrativo. Las metas se resuelven por
nivel y por área (`resolver_meta_*`).
"""
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status

from cafae.api.deps import get_current_user, require_role
from cafae.api.routes_catalogos._base import (
    AreaRequest,
    InstitucionRequest,
    MetaRequest,
    NivelRequest,
    ToggleEstadoRequest,
    catalogo_service,
)
from cafae.security import UserError

router = APIRouter(tags=['Catálogos'])


# =============================================================================
# NIVELES EDUCATIVOS
# =============================================================================
@router.get('/niveles')
def list_niveles(user: Annotated[dict, Depends(get_current_user)], solo_activos: bool = False):
    return catalogo_service.list_niveles(user['token'], solo_activos=solo_activos)


@router.post('/niveles')
def create_nivel(
    req: NivelRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    new_id = catalogo_service.create_nivel(user['token'], req.nombre)
    return {'ok': True, 'id': new_id, 'mensaje': 'Nivel educativo registrado con éxito.'}


@router.put('/niveles/{item_id}')
def update_nivel(
    item_id: int,
    req: NivelRequest,
    activo: bool = True,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))] = None
):
    catalogo_service.update_nivel(user['token'], item_id, req.nombre, activo)
    return {'ok': True, 'mensaje': 'Nivel educativo actualizado con éxito.'}


@router.patch('/niveles/{item_id}/estado')
def set_active_nivel(
    item_id: int,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))],
    body: Optional[ToggleEstadoRequest] = None,
    activo: Optional[bool] = Query(None)
):
    val_activo = activo if activo is not None else (body.activo if body else None)
    if val_activo is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='El campo "activo" es obligatorio.')
    token = user['token']
    nivel = catalogo_service.get_nivel(token, item_id)
    if not nivel:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Nivel educativo no encontrado.')
    catalogo_service.update_nivel(token, item_id, nivel['nombre'], val_activo)
    return {'ok': True, 'mensaje': f'Nivel {"activado" if val_activo else "desactivado"} con éxito.'}


@router.delete('/niveles/{item_id}')
def delete_nivel(
    item_id: int,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    catalogo_service.delete_nivel(user['token'], item_id)
    return {'ok': True, 'mensaje': 'Nivel educativo eliminado con éxito.'}


# =============================================================================
# INSTITUCIONES EDUCATIVAS
# =============================================================================
@router.get('/instituciones')
def list_instituciones(
    user: Annotated[dict, Depends(get_current_user)],
    solo_activos: bool = False,
    query: Optional[str] = None,
    nivel_id: Optional[int] = None
):
    return catalogo_service.list_instituciones(
        user['token'], solo_activas=solo_activos, query=query, nivel_id=nivel_id
    )


@router.post('/instituciones')
def create_institucion(
    req: InstitucionRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    token = user['token']
    nivel_id = req.nivel_id
    if not nivel_id:
        niveles = catalogo_service.list_niveles(token, solo_activos=True)
        if niveles:
            nivel_id = niveles[0]['id']
        else:
            raise UserError('No hay niveles educativos disponibles para asignar a la institución.')

    codigo_modular = req.codigo_modular or f"IE-{req.nombre[:10].strip().upper()}"
    distrito = req.distrito or 'Chepén'

    new_id = catalogo_service.create_institucion(
        token, codigo_modular, req.nombre, nivel_id, distrito, req.meta_id, req.observaciones
    )
    return {'ok': True, 'id': new_id, 'mensaje': 'Institución registrada con éxito.'}


@router.put('/instituciones/{item_id}')
def update_institucion(
    item_id: int,
    req: InstitucionRequest,
    activo: bool = True,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))] = None
):
    token = user['token']
    inst = catalogo_service.get_institucion(token, item_id)
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Institución no encontrada.')

    codigo_modular = req.codigo_modular or inst['codigo_modular']
    nombre = req.nombre or inst['nombre']
    nivel_id = req.nivel_id or inst['nivel_id']
    distrito = req.distrito or inst['distrito'] or 'Chepén'
    meta_id = req.meta_id if req.meta_id is not None else inst.get('meta_id')
    observaciones = req.observaciones if req.observaciones is not None else inst.get('observaciones')

    catalogo_service.update_institucion(
        token, item_id, codigo_modular, nombre, nivel_id, distrito, meta_id, observaciones, activo
    )
    return {'ok': True, 'mensaje': 'Institución actualizada con éxito.'}


@router.patch('/instituciones/{item_id}/estado')
def set_active_institucion(
    item_id: int,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))],
    body: Optional[ToggleEstadoRequest] = None,
    activo: Optional[bool] = Query(None)
):
    val_activo = activo if activo is not None else (body.activo if body else None)
    if val_activo is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='El campo "activo" es obligatorio.')
    token = user['token']
    inst = catalogo_service.get_institucion(token, item_id)
    if not inst:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Institución no encontrada.')
    catalogo_service.update_institucion(
        token, item_id, inst['codigo_modular'], inst['nombre'], inst['nivel_id'],
        inst['distrito'], inst.get('meta_id'), inst.get('observaciones'), val_activo
    )
    return {'ok': True, 'mensaje': f'Institución {"activada" if val_activo else "desactivada"} con éxito.'}


@router.delete('/instituciones/{item_id}')
def delete_institucion(
    item_id: int,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    catalogo_service.delete_institucion(user['token'], item_id)
    return {'ok': True, 'mensaje': 'Institución eliminada definitivamente con éxito.'}


# =============================================================================
# ÁREAS DE SEDE
# =============================================================================
@router.get('/areas')
def list_areas(user: Annotated[dict, Depends(get_current_user)], solo_activos: bool = False):
    return catalogo_service.list_areas_sede(user['token'], solo_activas=solo_activos)


@router.post('/areas')
def create_area(
    req: AreaRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    new_id = catalogo_service.create_area_sede(user['token'], req.nombre, req.meta_id)
    return {'ok': True, 'id': new_id, 'mensaje': 'Área creada exitosamente.'}


@router.put('/areas/{item_id}')
def update_area(
    item_id: int,
    req: AreaRequest,
    activo: bool = True,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))] = None
):
    catalogo_service.update_area_sede(user['token'], item_id, req.nombre, req.meta_id, activo)
    return {'ok': True, 'mensaje': 'Área actualizada exitosamente.'}


@router.patch('/areas/{item_id}/estado')
def set_active_area(
    item_id: int,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))],
    body: Optional[ToggleEstadoRequest] = None,
    activo: Optional[bool] = Query(None)
):
    val_activo = activo if activo is not None else (body.activo if body else None)
    if val_activo is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='El campo "activo" es obligatorio.')
    token = user['token']
    area = catalogo_service.get_area_sede(token, item_id)
    if not area:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Área no encontrada.')
    catalogo_service.update_area_sede(token, item_id, area['nombre'], area.get('meta_id'), val_activo)
    return {'ok': True, 'mensaje': f'Área {"activada" if val_activo else "desactivada"} con éxito.'}


@router.delete('/areas/{item_id}')
def delete_area(
    item_id: int,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    catalogo_service.delete_area_sede(user['token'], item_id)
    return {'ok': True, 'mensaje': 'Área de sede eliminada definitivamente con éxito.'}


# =============================================================================
# METAS PRESUPUESTARIAS
# =============================================================================
@router.get('/metas')
def list_metas(user: Annotated[dict, Depends(get_current_user)], solo_activos: bool = False):
    return catalogo_service.list_metas(user['token'], solo_activos=solo_activos)


@router.post('/metas')
def create_meta(
    req: MetaRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    new_id = catalogo_service.create_meta(
        user['token'], req.codigo, req.descripcion or req.codigo, req.programa_id, req.partida_id
    )
    return {'ok': True, 'id': new_id, 'mensaje': 'Meta registrada con éxito.'}


@router.put('/metas/{item_id}')
def update_meta(
    item_id: int,
    req: MetaRequest,
    activo: bool = True,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))] = None,
):
    token = user['token']
    meta = catalogo_service.get_meta(token, item_id)
    if not meta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Meta no encontrada.')

    programa_id = req.programa_id if req.programa_id is not None else meta.get('programa_id')
    partida_id = req.partida_id if req.partida_id is not None else meta.get('partida_id')

    catalogo_service.update_meta(
        token, item_id, req.codigo, req.descripcion or req.codigo, programa_id, partida_id, activo
    )
    return {'ok': True, 'mensaje': 'Meta actualizada con éxito.'}


@router.patch('/metas/{item_id}/estado')
def set_active_meta(
    item_id: int,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))],
    body: Optional[ToggleEstadoRequest] = None,
    activo: Optional[bool] = Query(None)
):
    val_activo = activo if activo is not None else (body.activo if body else None)
    if val_activo is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='El campo "activo" es obligatorio.')
    token = user['token']
    meta = catalogo_service.get_meta(token, item_id)
    if not meta:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Meta no encontrada.')
    catalogo_service.update_meta(
        token, item_id, meta['codigo'], meta['descripcion'], meta.get('programa_id'), meta.get('partida_id'), val_activo
    )
    return {'ok': True, 'mensaje': f'Meta {"activada" if val_activo else "desactivada"} con éxito.'}


@router.delete('/metas/{item_id}')
def delete_meta(
    item_id: int,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    catalogo_service.delete_meta(user['token'], item_id)
    return {'ok': True, 'mensaje': 'Meta presupuestaria eliminada con éxito.'}

