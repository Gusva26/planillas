# Contrato del API

Documento normativo de la superficie HTTP. Si el código y este documento
difieren, es un defecto de cualquiera de los dos.

- **Fuente de verdad**: el esquema OpenAPI que genera FastAPI (`/openapi.json`,
  `/docs`). Los modelos viven en `cafae/api/schemas.py` y `cafae/api/errors.py`.
- **Raíz**: todos los recursos cuelgan de `/api`.
- **Formato**: JSON en `snake_case`; fechas ISO 8601; montos como número decimal
  (`Decimal` se serializa a número para transporte, nunca a cadena).
- **Autenticación**: `Authorization: Bearer <token>`. Es el único esquema
  aceptado; no hay token por query string ni cabeceras alternativas.

## Sobre único de error

Toda respuesta `4xx`/`5xx` usa `application/problem+json` (RFC 9457):

```json
{
  "type": "urn:problem-type:cafae:conflicto-revision",
  "title": "Conflicto de revisión",
  "status": 409,
  "code": "CONFLICTO_REVISION",
  "detail": "La planilla cambió desde que la abrió. Vuelva a cargarla antes de guardar.",
  "instance": "/api/planillas/versiones/31/lineas",
  "errors": [
    { "campo": "body.mes", "mensaje": "Input should be greater than or equal to 1" }
  ]
}
```

| Campo | Uso |
| --- | --- |
| `code` | **Rama estable para el cliente.** No compares contra `detail`. |
| `detail` | Texto en español listo para mostrar. Puede cambiar redacción. |
| `type` | URI estable del tipo; deriva de `code`. |
| `status` | Igual al status HTTP. |
| `instance` | Ruta que originó el error. |
| `errors` | Solo en validación de campos (`VALIDACION`). |

### Catálogo de códigos

| `code` | HTTP | Cuándo |
| --- | --- | --- |
| `SOLICITUD_INVALIDA` | 400 | Regla de negocio rechazó la operación (`UserError`) |
| `NO_AUTENTICADO` | 401 | Token ausente, vencido o revocado |
| `SIN_PERMISO` | 403 | El rol no tiene el permiso requerido |
| `NO_ENCONTRADO` | 404 | Recurso inexistente |
| `CONFLICTO_REVISION` | 409 | Otro usuario movió `revision_edicion` |
| `CONFLICTO_ESTADO` | 409 | Estado incompatible (por ejemplo, versión ya cerrada) |
| `VALIDACION` | 422 | Campos inválidos o faltantes |
| `ERROR_INTERNO` | 500 | Fallo no clasificado; nunca expone `str(exc)` |

## Concurrencia y `revision_edicion`

`planilla_versiones.revision_edicion` es un contador monótono. **Se incrementa
en cada inserción, actualización o borrado de hijos** (detalle, descuentos,
firmas, programas) por el trigger `proteger_hijo` → `bloquear_edicion()`.

Consecuencias contractuales:

1. `POST /api/planillas` devuelve `planilla.revision_edicion` ya vigente; nunca
   asumas que una versión nueva está en `1`.
2. Toda edición (`PUT /api/planillas/versiones/{id}/lineas`), limpieza o cierre
   exige `revision_esperada` con el valor vigente.
3. Si el valor no coincide, la operación no se aplica y responde
   `409 CONFLICTO_REVISION`. El cliente debe recargar la versión y reintentar.
4. Tras un guardado exitoso, la respuesta trae la nueva revisión o el cliente
   debe recargar; no reutilices la anterior.

## Creación de planilla

`POST /api/planillas`

```json
{ "anio": 2026, "mes": 9, "tipo": "IIEE", "origen": "MAESTRO" }
```

Respuesta `200` (`RespuestaCreacionPlanilla`):

```json
{
  "ok": true,
  "planilla": {
    "planilla_id": 12,
    "version_id": 31,
    "trabajadores_copiados": 24,
    "revision_edicion": 49
  },
  "mensaje": "Planilla creada exitosamente."
}
```

`origen: "COPIA"` copia el mes inmediatamente anterior del mismo tipo y exige
que la fuente esté cerrada.

## Versionado

La API se publica en `2.1.0` (`info.version` del OpenAPI). Mientras no exista
un prefijo `/api/v2`, los cambios se mantienen **retrocompatibles**:

- agregar campos opcionales: permitido;
- agregar valores a un enum: requiere aviso;
- renombrar o quitar campos, cambiar status o códigos: requiere nueva versión
  de prefijo y ventana de convivencia.

## Verificación

```powershell
python scripts/test_api.py      # contrato y OpenAPI, sin base de datos
python scripts/test_seguridad.py # permisos, Bearer y bloqueo D.5
```

El test de contrato falla si un endpoint deja de documentar el sobre de error,
si `POST /api/planillas` pierde `revision_edicion` o si el modelo `Problem`
cambia sus claves obligatorias.
