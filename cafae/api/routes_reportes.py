"""Rutas para el Dashboard y los 9 Reportes Administrativos."""
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status

from cafae.api.deps import get_current_user
from cafae.reportes import ReporteService
from cafae.security import UserError

router = APIRouter(prefix='/reportes', tags=['Reportes'])
reporte_service = ReporteService()


@router.get('/dashboard')
def get_dashboard(user: Annotated[dict, Depends(get_current_user)]):
    try:
        return reporte_service.get_dashboard_summary(user['token'])
    except UserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get('/{tipo_reporte}/{version_id}')
def get_reporte(
    tipo_reporte: str,
    version_id: int,
    user: Annotated[dict, Depends(get_current_user)]
):
    token = user['token']
    try:
        if tipo_reporte == 'resumen-mensual':
            return reporte_service.reporte_resumen_mensual(token, version_id)
        elif tipo_reporte == 'por-institucion':
            return reporte_service.reporte_importe_por_institucion(token, version_id)
        elif tipo_reporte == 'por-meta':
            return reporte_service.reporte_importe_por_meta(token, version_id)
        elif tipo_reporte == 'descuentos-por-entidad':
            return reporte_service.reporte_descuentos_por_entidad(token, version_id)
        elif tipo_reporte == 'neto-por-institucion':
            return reporte_service.reporte_neto_por_institucion(token, version_id)
        elif tipo_reporte == 'trabajadores-por-nivel':
            return reporte_service.reporte_trabajadores_por_nivel(token, version_id)
        elif tipo_reporte == 'trabajadores-por-situacion':
            return reporte_service.reporte_trabajadores_por_situacion(token, version_id)
        elif tipo_reporte == 'general-descuentos':
            return reporte_service.reporte_general_descuentos(token, version_id)
        elif tipo_reporte == 'licencias-sin-goce':
            return reporte_service.reporte_licencias_sin_goce(token, version_id)
        elif tipo_reporte == 'modalidad-pago':
            return reporte_service.reporte_modalidad_pago(token, version_id)
        elif tipo_reporte == 'comparativo-anterior':
            return reporte_service.reporte_comparativo_mes_anterior(token, version_id)
        elif tipo_reporte == 'padron-alfabetico':
            return reporte_service.reporte_padron_alfabetico(token, version_id)
        else:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f'Reporte "{tipo_reporte}" no encontrado.')
    except UserError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
