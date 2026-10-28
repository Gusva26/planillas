"""Rutas del registro inmutable de auditoría forense."""
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, Query

from cafae.api.deps import require_role
from cafae.api.schemas import EventoAuditoria, Pagina
from cafae.auditoria import AuditoriaService

router = APIRouter(prefix='/auditoria', tags=['Auditoría'])
auditoria_service = AuditoriaService()


@router.get('', response_model=Pagina[EventoAuditoria])
def list_auditoria(
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))],
    entidad: Optional[str] = None,
    usuario_id: Optional[int] = None,
    accion: Optional[str] = None,
    resultado: Optional[str] = None,
    limite: int = Query(100, ge=1, le=500),
    desplazamiento: int = Query(0, ge=0),
):
    """Página de eventos, del más reciente al más antiguo.

    El registro es append-only: `total` solo crece, así que el cliente pagina
    con `limite`/`desplazamiento` en lugar de descargar la tabla completa.
    """
    return auditoria_service.list_eventos(
        user['token'],
        entidad=entidad,
        usuario_id=usuario_id,
        accion=accion,
        resultado=resultado,
        limite=limite,
        desplazamiento=desplazamiento,
    )


@router.get('/{auditoria_id}/cambios')
def get_auditoria_cambios(
    auditoria_id: int,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    return auditoria_service.get_cambios(user['token'], auditoria_id)
