"""Contrato de errores del API (RFC 9457, sucesor de RFC 7807).

Toda respuesta de error sale con el mismo sobre:

.. code-block:: json

    {
      "type": "urn:problem-type:cafae:conflicto-revision",
      "title": "Conflicto de revisión",
      "status": 409,
      "code": "CONFLICTO_REVISION",
      "detail": "La planilla cambió; actualice antes de guardar.",
      "instance": "/api/planillas/versiones/12/lineas"
    }

- ``type`` y ``code`` son identificadores estables: el código de cliente debe
  ramificar por ellos, nunca por el texto de ``detail``.
- ``detail`` se mantiene como texto plano en español porque la UI lo muestra
  tal cual (``frontend/src/api/client.ts``).
- ``instance`` es la ruta que originó el error.
- ``errors`` solo aparece en fallos de validación de campos.

El medio es ``application/problem+json``.
"""
from typing import Any, Literal

from pydantic import BaseModel, Field

MEDIA_TYPE = 'application/problem+json'
TYPE_PREFIX = 'urn:problem-type:cafae:'

CodigoError = Literal[
    'SOLICITUD_INVALIDA',
    'NO_AUTENTICADO',
    'SIN_PERMISO',
    'NO_ENCONTRADO',
    'CONFLICTO_REVISION',
    'CONFLICTO_ESTADO',
    'VALIDACION',
    'ERROR_INTERNO',
]

# code -> (status HTTP, título legible)
CATALOGO: dict[str, tuple[int, str]] = {
    'SOLICITUD_INVALIDA': (400, 'Solicitud inválida'),
    'NO_AUTENTICADO': (401, 'No autenticado'),
    'SIN_PERMISO': (403, 'Sin permiso'),
    'NO_ENCONTRADO': (404, 'Recurso no encontrado'),
    'CONFLICTO_REVISION': (409, 'Conflicto de revisión'),
    'CONFLICTO_ESTADO': (409, 'Conflicto de estado'),
    'VALIDACION': (422, 'Solicitud inválida'),
    'ERROR_INTERNO': (500, 'Error interno'),
}


class CampoInvalido(BaseModel):
    campo: str = Field(..., description='Ruta del campo, por ejemplo "body.mes".')
    mensaje: str = Field(..., description='Motivo legible del rechazo.')


class Problem(BaseModel):
    """Sobre único de error del API."""

    type: str = Field(..., description='URI estable del tipo de problema.')
    title: str = Field(..., description='Resumen corto y estable del tipo.')
    status: int = Field(..., ge=400, le=599)
    code: CodigoError = Field(..., description='Código estable para ramificar en el cliente.')
    detail: str = Field(..., description='Mensaje legible en español.')
    instance: str | None = Field(None, description='Ruta de la solicitud que falló.')
    errors: list[CampoInvalido] | None = Field(
        None, description='Detalle por campo; solo en errores de validación.'
    )


def codigo_a_tipo(code: str) -> str:
    return TYPE_PREFIX + code.lower().replace('_', '-')


def problema(
    code: str,
    detail: str,
    *,
    instance: str | None = None,
    errors: list[dict[str, Any]] | None = None,
    status_code: int | None = None,
) -> dict[str, Any]:
    """Construye el cuerpo del error sin las claves vacías."""
    status_default, title = CATALOGO.get(code, CATALOGO['ERROR_INTERNO'])
    body: dict[str, Any] = {
        'type': codigo_a_tipo(code),
        'title': title,
        'status': status_code or status_default,
        'code': code,
        'detail': detail,
    }
    if instance:
        body['instance'] = instance
    if errors:
        body['errors'] = errors
    return body


def problema_para_status(status_code: int, detail: str, *, instance: str | None = None) -> dict[str, Any]:
    """Traduce un status HTTP suelto (``HTTPException``) al catálogo estable."""
    code = {
        400: 'SOLICITUD_INVALIDA',
        401: 'NO_AUTENTICADO',
        403: 'SIN_PERMISO',
        404: 'NO_ENCONTRADO',
        409: 'CONFLICTO_ESTADO',
        422: 'VALIDACION',
    }.get(status_code, 'ERROR_INTERNO' if status_code >= 500 else 'SOLICITUD_INVALIDA')
    return problema(code, detail, instance=instance, status_code=status_code)
