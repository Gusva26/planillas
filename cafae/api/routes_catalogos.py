"""Rutas de catálogos institucionales y presupuestarios."""
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from cafae.api.deps import get_current_user, require_role
from cafae.catalogos import CatalogoService
from cafae.security import UserError

router = APIRouter(prefix='/catalogos', tags=['Catálogos'])
catalogo_service = CatalogoService()


class InstitucionRequest(BaseModel):
    nombre: str = Field(..., max_length=240)
    codigo_modular: Optional[str] = Field(None, max_length=30)
    nivel_id: Optional[int] = None
    distrito: Optional[str] = Field(None, max_length=120)
    meta_id: Optional[int] = None
    observaciones: Optional[str] = None


class AreaRequest(BaseModel):
    nombre: str = Field(..., max_length=150)
    meta_id: Optional[int] = None


class MetaRequest(BaseModel):
    codigo: str = Field(..., max_length=30)
    descripcion: Optional[str] = Field(None, max_length=500)
    programa_id: Optional[int] = None
    partida_id: Optional[int] = None


class NivelRequest(BaseModel):
    nombre: str = Field(..., max_length=100)


class ProgramaRequest(BaseModel):
    codigo: str = Field(..., max_length=30)
    nombre: str = Field(..., max_length=180)
    orden: Optional[int] = 0
    padre_id: Optional[int] = None


class PartidaRequest(BaseModel):
    codigo: str = Field(..., max_length=40)
    descripcion: str = Field(..., max_length=500)


class CargoRequest(BaseModel):
    nombre: str = Field(..., max_length=150)


class CategoriaRequest(BaseModel):
    codigo: str = Field(..., max_length=50)
    descripcion: str = Field(..., max_length=150)


class SituacionRequest(BaseModel):
    nombre: str = Field(..., max_length=120)


class SubtipoRequest(BaseModel):
    nombre: str = Field(..., max_length=120)


class ConfiguracionRequest(BaseModel):
    nombre_institucion: str = Field(..., max_length=200)
    nombre_sistema: str = Field(..., max_length=200)
    zona_horaria: Optional[str] = 'America/Lima'


class FirmaRequest(BaseModel):
    nombre_completo: Optional[str] = Field(None, max_length=200)
    cargo: Optional[str] = Field(None, max_length=200)
    nombre_firmante: Optional[str] = Field(None, max_length=200)
    cargo_firmante: Optional[str] = Field(None, max_length=200)
    orden: Optional[int] = None
    ambito: Optional[str] = None


class TipoDescuentoRequest(BaseModel):
    codigo: Optional[str] = Field(None, max_length=30)
    nombre: str = Field(..., max_length=100)
    orden: Optional[int] = 1
    aplica_iiee: Optional[bool] = True
    aplica_sede: Optional[bool] = True
    activo: Optional[bool] = True


class ToggleEstadoRequest(BaseModel):
    activo: Optional[bool] = None


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


