"""Modelos de respuesta que forman el contrato público del API.

Estos tipos son la fuente del esquema OpenAPI que consume el frontend; si un
campo no está acá, no es parte del contrato.
"""
from pydantic import BaseModel, Field


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
