"""Registro estructurado en JSON con identificador de correlación por solicitud.

Cada línea es un objeto JSON con `ts`, `nivel`, `logger`, `mensaje` y
`request_id`, más los campos que se pasen por `extra` (`metodo`, `ruta`,
`estado`, `duracion_ms`, ...). Así un incidente se rastrea desde la cabecera
`X-Request-ID` de la respuesta hasta la línea exacta del log, sin parsear texto
libre ni correlacionar a ojo.

El identificador vive en un `ContextVar`: el middleware lo fija al entrar la
petición y todo lo que se registre mientras corre —servicios incluidos— lo
hereda sin pasarlo de mano en mano.
"""
import json
import logging
import os
import sys
from contextvars import ContextVar
from datetime import datetime, timezone

request_id: ContextVar[str] = ContextVar('request_id', default='-')

# Campos opcionales que se copian al JSON si el registro los trae.
CAMPOS = (
    'evento',
    'metodo',
    'ruta',
    'estado',
    'duracion_ms',
    'usuario',
    'detalle',
)


class FormateadorJSON(logging.Formatter):
    """Serializa cada registro como una línea JSON, sin perder el traceback."""

    def format(self, record: logging.LogRecord) -> str:
        salida = {
            'ts': datetime.fromtimestamp(
                record.created, timezone.utc
            ).isoformat(timespec='milliseconds'),
            'nivel': record.levelname,
            'logger': record.name,
            'mensaje': record.getMessage(),
            'request_id': request_id.get(),
        }
        for campo in CAMPOS:
            valor = getattr(record, campo, None)
            if valor is not None:
                salida[campo] = valor
        if record.exc_info:
            salida['excepcion'] = self.formatException(record.exc_info)
        return json.dumps(salida, ensure_ascii=False, default=str)


def configurar(nivel: str | None = None) -> None:
    """Instala el formateador JSON en la raíz; idempotente.

    Uvicorn y cualquier otro logger de librería escriben a través de la raíz:
    sus handlers propios duplicarían cada línea y romperían el formato.
    """
    manejador = logging.StreamHandler(sys.stdout)
    manejador.setFormatter(FormateadorJSON())

    raiz = logging.getLogger()
    raiz.handlers = [manejador]
    raiz.setLevel((nivel or os.environ.get('CAFAE_LOG_LEVEL', 'INFO')).upper())

    # `uvicorn.access` queda fuera a propósito: el log de acceso lo emite el
    # middleware (con id, estado y duración) y uvicorn arranca con
    # `--no-access-log`. Si se reengancha aquí, cada petición sale dos veces.
    for nombre in ('uvicorn', 'uvicorn.error'):
        logger = logging.getLogger(nombre)
        logger.handlers = []
        logger.propagate = True
