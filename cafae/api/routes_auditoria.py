"""Rutas del registro inmutable de auditoría forense."""
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from cafae.api.deps import require_role
from cafae.auditoria import AuditoriaService
from cafae.security import UserError

router = APIRouter(prefix='/auditoria', tags=['Auditoría'])
auditoria_service = AuditoriaService()


@router.get('')
def list_auditoria(
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))],
    entidad: Optional[str] = None,
    usuario_id: Optional[int] = None,
    accion: Optional[str] = None,
    resultado: Optional[str] = None,
    limite: int = Query(100, ge=1, le=500),
):
    try:
        return auditoria_service.list_eventos(
            user['token'],
            entidad=entidad,
            usuario_id=usuario_id,
            accion=accion,
            resultado=resultado,
            limite=limite,
        )
    except UserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get('/{auditoria_id}/cambios')
def get_auditoria_cambios(
    auditoria_id: int,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    try:
        return auditoria_service.get_cambios(user['token'], auditoria_id)
    except UserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
