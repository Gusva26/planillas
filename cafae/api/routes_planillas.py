"""Rutas de gestión y ciclo de vida de planillas."""
from typing import Annotated, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field

from cafae.api.deps import get_current_user, require_role
from cafae.planillas import PlanillaService
from cafae.security import UserError, AccessError

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
    try:
        return planilla_service.list_planillas(
            user['token'], anio=anio, mes=mes, tipo=tipo
        )
    except UserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post('')
def create_planilla(
    req: PlanillaCreateRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR', 'PLANILLAS'))]
):
    try:
        if req.origen == 'COPIA':
            res = planilla_service.copiar_mes_anterior(
                user['token'], req.anio, req.mes, req.tipo, req.version_fuente_id
            )
        else:
            res = planilla_service.crear_desde_maestro(
                user['token'], req.anio, req.mes, req.tipo
            )
        return {'ok': True, 'planilla': res, 'mensaje': 'Planilla creada exitosamente.'}
    except UserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get('/versiones/{version_id}')
def get_version_detalle(
    version_id: int,
    user: Annotated[dict, Depends(get_current_user)],
    query: Optional[str] = None,
    institucion_id: Optional[int] = None,
    area_id: Optional[int] = None,
):
    """Devuelve la información consolidada de la versión y todas sus líneas de detalle."""
    token = user['token']
    try:
        # 1. Obtener datos de la versión
        with planilla_service.auth.data_transaction(token, 'consultar') as (conn, _):
            version_info = conn.execute(
                '''SELECT pv.*, p.tipo, p.cantidad_firmas, per.anio, per.mes,
                          u_crea.nombre_completo AS creada_por_nombre,
                          u_cerr.nombre_completo AS cerrada_por_nombre
                   FROM planilla_versiones pv
                   JOIN planillas p ON p.id = pv.planilla_id
                   JOIN periodos per ON per.id = p.periodo_id
                   JOIN usuarios u_crea ON u_crea.id = pv.creada_por
                   LEFT JOIN usuarios u_cerr ON u_cerr.id = pv.cerrada_por
                   WHERE pv.id = %s''',
                (version_id,)
            ).fetchone()
            if not version_info:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Versión no encontrada.')

            # Firmas asignadas si está cerrada
            firmas = conn.execute(
                'SELECT * FROM planilla_firmas WHERE version_id = %s ORDER BY posicion ASC',
                (version_id,)
            ).fetchall()

        # 2. Obtener líneas de detalle
        lineas = planilla_service.get_detalle_version(
            token,
            version_id,
            query=query,
            institucion_id=institucion_id,
            area_id=area_id,
        )

        return {
            'version': version_info,
            'firmas': firmas,
            'lineas': lineas,
        }
    except UserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.put('/versiones/{version_id}/lineas')
def update_lineas(
    version_id: int,
    req: BatchEditRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR', 'PLANILLAS'))]
):
    try:
        planilla_service.guardar_edicion_lote(
            user['token'], version_id, req.revision_esperada, req.cambios
        )
        return {'ok': True, 'mensaje': 'Cambios guardados exitosamente.'}
    except UserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post('/versiones/{version_id}/limpiar')
def limpiar_descuentos(
    version_id: int,
    req: LimpiarDescuentosRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR', 'PLANILLAS'))]
):
    try:
        planilla_service.limpiar_descuentos(
            user['token'], version_id, req.revision_esperada, concepto_codigo=req.concepto_codigo
        )
        return {'ok': True, 'mensaje': 'Descuentos limpiados exitosamente.'}
    except UserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post('/versiones/{version_id}/cerrar')
def cerrar_version(
    version_id: int,
    req: CerrarPlanillaRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    try:
        res = planilla_service.cerrar_version(
            user['token'], version_id, req.revision_esperada, req.firmas_ids
        )
        return {'ok': True, 'resultado': res, 'mensaje': 'Planilla cerrada formalmente con éxito.'}
    except UserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post('/versiones/{version_id}/reabrir')
def reabrir_version(
    version_id: int,
    req: ReabrirPlanillaRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR'))]
):
    try:
        nueva = planilla_service.reabrir_version(
            user['token'], version_id, req.motivo
        )
        return {'ok': True, 'nueva_version': nueva, 'mensaje': 'Planilla reabierta con nueva versión editable.'}
    except UserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
