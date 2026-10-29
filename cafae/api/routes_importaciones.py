"""Rutas del Asistente de Importación de Descuentos."""
from typing import Annotated, Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from pydantic import BaseModel, Field

from cafae.api.deps import get_current_user, require_role
from cafae.importaciones import ImportacionService

router = APIRouter(prefix='/importaciones', tags=['Importaciones'])
importacion_service = ImportacionService()


class ToggleFilaRequest(BaseModel):
    fila: int
    seleccionado: bool
    motivo: Optional[str] = None


class AplicarImportacionRequest(BaseModel):
    modalidad: str = Field(..., pattern='^(REEMPLAZAR|ACTUALIZAR)$')
    revision_esperada: int


@router.post('/procesar')
async def procesar_archivo(
    version_id: Annotated[int, Form()],
    tipo_descuento_id: Annotated[int, Form()],
    archivo: UploadFile = File(...),
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR', 'PLANILLAS'))] = None,
):
    content = await archivo.read()
    resumen = importacion_service.procesar_archivo_importacion(
        user['token'],
        version_id=version_id,
        tipo_descuento_id=tipo_descuento_id,
        nombre_archivo=archivo.filename,
        bytes_data=content,
    )
    return {'ok': True, 'resumen': resumen, 'mensaje': 'Archivo clasificado con éxito.'}


@router.get('/{importacion_id}')
def get_importacion(
    importacion_id: int,
    user: Annotated[dict, Depends(get_current_user)],
    estado_filtro: Optional[str] = None,
):
    resumen = importacion_service.get_resumen_importacion(user['token'], importacion_id)
    if not resumen:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail='Importación no encontrada.')
    filas = importacion_service.list_filas_importacion(user['token'], importacion_id, estado_filtro=estado_filtro)
    return {
        'resumen': resumen,
        'filas': filas,
    }


@router.patch('/{importacion_id}/filas')
def cambiar_seleccion_fila(
    importacion_id: int,
    req: ToggleFilaRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR', 'PLANILLAS'))]
):
    importacion_service.cambiar_seleccion_fila(
        user['token'], importacion_id, req.fila, req.seleccionado, req.motivo
    )
    return {'ok': True, 'mensaje': 'Fila actualizada.'}


@router.post('/{importacion_id}/aplicar')
def aplicar_importacion(
    importacion_id: int,
    req: AplicarImportacionRequest,
    user: Annotated[dict, Depends(require_role('ADMINISTRADOR', 'PLANILLAS'))]
):
    resultado = importacion_service.aplicar_importacion(
        user['token'], importacion_id, req.modalidad, req.revision_esperada
    )
    return {'ok': True, 'resultado': resultado, 'mensaje': 'Descuentos aplicados a la planilla exitosamente.'}
