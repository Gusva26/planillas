"""Rutas del Maestro de Personal (Trabajadores II.EE. y Sede)."""
from datetime import date
from decimal import Decimal
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from cafae.api.deps import get_current_user, require_role
from cafae.trabajadores import TrabajadorService
from cafae.security import UserError, AccessError

router = APIRouter(prefix='/trabajadores', tags=['Personal'])
trabajador_service = TrabajadorService()


class TrabajadorCreateRequest(BaseModel):
    dni: str = Field(..., min_length=8, max_length=8)
    apellidos: str = Field(..., max_length=120)
    nombres: str = Field(..., max_length=120)
    tipo: str = Field(..., pattern='^(IIEE|SEDE)$')
    institucion_id: Optional[int] = None
    area_id: Optional[int] = None
    nivel_id: Optional[int] = None
    cargo_id: Optional[int] = None
    situacion_id: Optional[int] = None
    categoria_id: Optional[int] = None
    subtipo_id: Optional[int] = None
    fecha_nacimiento: Optional[date] = None
    ley: Optional[str] = None
    regimen_laboral: Optional[str] = None
    jornada_laboral: Optional[str] = None
    cuenta_multired: Optional[str] = None
    importe: Decimal = Field(default=Decimal('0.00'), ge=0)
    tipo_pago: Optional[str] = 'CUENTA'
    numero_cheque: Optional[str] = None
    tiempo_servicio_texto: Optional[str] = None
    leyenda_permanente: Optional[str] = None


class TrabajadorUpdateRequest(TrabajadorCreateRequest):
    revision: int


class EstadoRequest(BaseModel):
    activo: bool
    revision: int


@router.get('')
def list_trabajadores(
    user: Annotated[dict, Depends(get_current_user)],
    tipo: Optional[str] = None,
    solo_activos: bool = False,
    q: Optional[str] = None,
    institucion_id: Optional[int] = None,
    area_id: Optional[int] = None,
    cargo_id: Optional[int] = None,
):
    try:
        return trabajador_service.list_trabajadores(
            user['token'],
            tipo=tipo,
            solo_activos=solo_activos,
            query=q,
            institucion_id=institucion_id,
            area_id=area_id,
            cargo_id=cargo_id,
        )
    except UserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get('/{item_id}')
def get_trabajador(item_id: int, user: Annotated[dict, Depends(get_current_user)]):
    try:
        t = trabajador_service.get_trabajador(user['token'], item_id)
        if not t:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Trabajador no encontrado.')
        return t
    except UserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post('')
def create_trabajador(
    req: TrabajadorCreateRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR', 'PLANILLAS'))]
):
    try:
        new_id = trabajador_service.create_trabajador(user['token'], req.model_dump())
        return {'ok': True, 'id': new_id, 'mensaje': 'Trabajador registrado con éxito.'}
    except UserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.put('/{item_id}')
def update_trabajador(
    item_id: int,
    req: TrabajadorUpdateRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR', 'PLANILLAS'))]
):
    try:
        datos = req.model_dump(exclude={'revision'})
        trabajador_service.update_trabajador(user['token'], item_id, datos, req.revision)
        return {'ok': True, 'mensaje': 'Ficha de trabajador actualizada con éxito.'}
    except UserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.patch('/{item_id}/estado')
def set_active_trabajador(
    item_id: int,
    req: EstadoRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR', 'PLANILLAS'))]
):
    try:
        trabajador_service.set_active_trabajador(user['token'], item_id, req.activo, req.revision)
        return {'ok': True, 'mensaje': f'Trabajador {"activado" if req.activo else "desactivado"} con éxito.'}
    except UserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
