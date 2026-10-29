"""Rutas de gestión y ciclo de vida de planillas."""
from typing import Annotated, Any, Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from cafae.api.deps import get_current_user, require_role
from cafae.api.schemas import RespuestaCreacionPlanilla
from cafae.planillas import PlanillaService

router = APIRouter(prefix='/planillas', tags=['Planillas'])
planilla_service = PlanillaService()


class PlanillaCreateRequest(BaseModel):
    anio: int = Field(..., ge=2000, le=2100)
    mes: int = Field(..., ge=1, le=12)
    tipo: str = Field(..., pattern='^(IIEE|SEDE)$')
    origen: str = Field('MAESTRO', pattern='^(MAESTRO|COPIA)$')
    version_fuente_id: Optional[int] = None


class BatchEditRequest(BaseModel):
    revision_esperada: int
    cambios: list[dict[str, Any]]


class LimpiarDescuentosRequest(BaseModel):
    revision_esperada: int
    concepto_codigo: Optional[str] = None


class CerrarPlanillaRequest(BaseModel):
    revision_esperada: int
    firmas_ids: list[int]


class ReabrirPlanillaRequest(BaseModel):
    motivo: str = Field(..., min_length=5, max_length=500)


@router.get('')
def list_planillas(
    user: Annotated[dict, Depends(get_current_user)],
    anio: Optional[int] = None,
    mes: Optional[int] = None,
    tipo: Optional[str] = None,
):
    return planilla_service.list_planillas(
        user['token'], anio=anio, mes=mes, tipo=tipo
    )


@router.post('', response_model=RespuestaCreacionPlanilla)
def create_planilla(
    req: PlanillaCreateRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR', 'PLANILLAS'))]
):
    """Crea la versión 1 desde el maestro o copiando el mes anterior.

    Devuelve la `revision_edicion` vigente: las inserciones de detalle la
    incrementan, así que el cliente no debe asumir 1 ni volver a leerla.
    """
    if req.origen == 'COPIA':
        res = planilla_service.copiar_mes_anterior(
            user['token'], req.anio, req.mes, req.tipo, req.version_fuente_id
        )
    else:
        res = planilla_service.crear_desde_maestro(
            user['token'], req.anio, req.mes, req.tipo
        )
    return {'ok': True, 'planilla': res, 'mensaje': 'Planilla creada exitosamente.'}


@router.get('/versiones/{version_id}')
def get_version_detalle(
    version_id: int,
    user: Annotated[dict, Depends(get_current_user)],
    query: Optional[str] = None,
    institucion_id: Optional[int] = None,
    area_id: Optional[int] = None,
):
    """Devuelve la información consolidada de la versión y todas sus líneas de detalle.

    Cabecera, firmas y líneas salen de la misma transacción (D-04): si alguien
    edita o cierra la planilla mientras se arma la respuesta, no se mezclan
    revisiones distintas.
    """
    return planilla_service.get_version_completa(
        user['token'],
        version_id,
        institucion_id=institucion_id,
        area_id=area_id,
        query=query,
    )


@router.put('/versiones/{version_id}/lineas')
def update_lineas(
    version_id: int,
    req: BatchEditRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR', 'PLANILLAS'))]
):
    planilla_service.guardar_edicion_lote(
        user['token'], version_id, req.revision_esperada, req.cambios
    )
    return {'ok': True, 'mensaje': 'Cambios guardados exitosamente.'}


@router.post('/versiones/{version_id}/limpiar')
def limpiar_descuentos(
    version_id: int,
    req: LimpiarDescuentosRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR', 'PLANILLAS'))]
):
    planilla_service.limpiar_descuentos(
        user['token'], version_id, req.revision_esperada, concepto_codigo=req.concepto_codigo
    )
    return {'ok': True, 'mensaje': 'Descuentos limpiados exitosamente.'}


@router.post('/versiones/{version_id}/cerrar')
def cerrar_version(
    version_id: int,
    req: CerrarPlanillaRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    res = planilla_service.cerrar_version(
        user['token'], version_id, req.revision_esperada, req.firmas_ids
    )
    return {'ok': True, 'resultado': res, 'mensaje': 'Planilla cerrada formalmente con éxito.'}


@router.post('/versiones/{version_id}/reabrir')
def reabrir_version(
    version_id: int,
    req: ReabrirPlanillaRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    nueva = planilla_service.reabrir_version(
        user['token'], version_id, req.motivo
    )
    return {'ok': True, 'nueva_version': nueva, 'mensaje': 'Planilla reabierta con nueva versión editable.'}
