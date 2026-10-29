"""Modelos de respuesta que forman el contrato público del API.

Estos tipos son la fuente del esquema OpenAPI que consume el frontend; si un
campo no está acá, no es parte del contrato.
"""
from datetime import datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, Field

T = TypeVar('T')


class PlanillaCreada(BaseModel):
    planilla_id: int = Field(..., gt=0)
    version_id: int = Field(..., gt=0)
    trabajadores_copiados: int = Field(..., ge=0)
    revision_edicion: int = Field(
        ...,
        gt=0,
        description=(
            'Revisión vigente de la versión recién creada. Las inserciones de '
            'detalle la incrementan, así que nunca es 1: el cliente debe usar '
            'este valor como `revision_esperada` en la primera edición.'
        ),
    )

    model_config = {
        'json_schema_extra': {
            'example': {
                'planilla_id': 12,
                'version_id': 31,
                'trabajadores_copiados': 24,
                'revision_edicion': 49,
            }
        }
    }


class RespuestaCreacionPlanilla(BaseModel):
    ok: bool = True
    planilla: PlanillaCreada
    mensaje: str = Field(..., description='Mensaje listo para mostrar al usuario.')


class Pagina(BaseModel, Generic[T]):
    """Sobre estándar de los listados paginados.

    Todo listado que crezca sin techo debe devolver este sobre en lugar de un
    arreglo suelto, para que el cliente pagine sin descargar la tabla completa.
    """

    items: list[T] = Field(..., description='Filas de la página pedida.')
    total: int = Field(..., ge=0, description='Total de filas que cumplen el filtro.')
    limite: int = Field(..., ge=1, le=500, description='Tamaño de página aplicado.')
    desplazamiento: int = Field(..., ge=0, description='Filas saltadas antes de esta página.')


class EventoAuditoria(BaseModel):
    """Fila del registro append-only de auditoría."""

    id: int
    fecha_hora: datetime
    usuario_id: int | None = None
    usuario_nombre: str | None = None
    accion: str
    entidad: str
    entidad_id: int | None = None
    descripcion: str
    resultado: Literal['EXITO', 'RECHAZADO', 'ERROR']
    correlacion: str
    total_cambios: int = Field(..., ge=0, description='Campos modificados registrados en el evento.')
