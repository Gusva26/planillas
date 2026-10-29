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
| `NO_ENCONTRADO` | 404 | Recurso inexistente (`NoEncontrado` en el servicio) |
| `CONFLICTO_REVISION` | 409 | Otro usuario movió `revision_edicion` |
| `CONFLICTO_ESTADO` | 409 | Estado incompatible o recurso en uso (`Conflicto`): versión ya cerrada, catálogo con dependencias |
| `VALIDACION` | 422 | Campos inválidos o faltantes |
| `ERROR_INTERNO` | 500 | Fallo no clasificado; nunca expone `str(exc)` |

### Identificador de correlación

Toda respuesta lleva `X-Request-ID`. El servidor respeta el valor que envíe el
cliente y, si falta, genera uno. Ese mismo valor aparece como `request_id` en
la línea JSON que el servicio registra para la petición, de modo que un reporte
de error se puede rastrear hasta el log sin adivinar. En los `5xx` conviene
mostrar ese identificador al usuario: es lo único que permite encontrar la
causa.

## Listados paginados

Todo listado que crece sin techo (`auditoria`, y a medida que se migren los
demás) devuelve el sobre `Pagina[T]` de `cafae/api/schemas.py` en lugar de un
arreglo suelto:

```json
{
  "items": [ { "id": 812, "accion": "UPDATE", "...": "..." } ],
  "total": 1432,
  "limite": 100,
  "desplazamiento": 0
}
```

| Campo | Uso |
| --- | --- |
| `items` | Filas de la página pedida. |
| `total` | Total de filas que cumplen el filtro (para dibujar el paginador). |
| `limite` | Tamaño de página efectivo; `1..500`. |
| `desplazamiento` | Filas saltadas; `>= 0`. |

Parámetros de query: `limite` (default `100`, máximo `500`) y `desplazamiento`
(default `0`). El orden es estable y descendente por `fecha_hora DESC, id DESC`,
de modo que dos páginas consecutivas no repiten filas.

### `GET /api/auditoria`

`response_model=Pagina[EventoAuditoria]`. Filtros opcionales: `entidad`,
`usuario_id`, `accion` (ILIKE), `resultado`. Solo `ADMINISTRADOR`.
`correlacion` se publica como cadena, aunque en la base sea `UUID`.

El registro es append-only: `total` solo crece. El cliente no debe descargar la
tabla completa ni paginar en memoria; pide página por página.

### Listados que todavía no usan el sobre

Los catálogos y las planillas siguen devolviendo arreglos (su volumen está
acotado por el maestro) y el frontend los pagina en el cliente con
`frontend/src/hooks/usePaginacion.ts`. Cuando un listado deje de estar acotado,
migra al sobre `Pagina[T]` **sin** romper retrocompatibilidad: se agrega un
parámetro y se publica un endpoint nuevo, o se espera a `/api/v2`.

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

### Lecturas consistentes

`GET /api/planillas/versiones/{id}` devuelve `version`, `firmas` y `lineas`
leídos en **una sola transacción**, y los endpoints de documentos parten de esa
misma lectura. No es un detalle de implementación: si alguien edita o cierra la
planilla mientras se arma la respuesta, las tres partes siguen siendo de la
misma revisión. Si la versión no existe, la respuesta es `404 NO_ENCONTRADO`.

### Borrado de catálogos

`DELETE /api/catalogos/...` responde `200` con el mensaje de éxito, o bien:

- `404 NO_ENCONTRADO` si el registro ya no existe (`NoEncontrado`).
- `409 CONFLICTO_ESTADO` si sigue referenciado por otros datos (`Conflicto`).
  En ese caso la salida correcta es `PATCH /api/catalogos/.../estado` para
  desactivarlo, no reintentar el borrado.

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

## Consumo desde el cliente

`frontend/src/api/client.ts` y `frontend/src/api/errors.ts` implementan el
contrato y son la única puerta de entrada a la API:

- `apiRequest<T>(path, options)` exige el tipo en el punto de llamada y **no**
  devuelve `any`; el valor por defecto es `unknown` para que ningún resultado
  entre a la UI sin declaración explícita.
- Toda respuesta fallida se convierte en `ApiError`, con `status`, `code`,
  `title`, `instance` y `erroresDeCampo`. La UI ramifica por `code`
  (`err.esConflictoDeRevision`), nunca por el texto de `detail`.
- `mensajeDeError(err, fallback)` devuelve siempre un string listo para mostrar.
- Respuestas `401` cierran la sesión y redirigen a `#/login` en un solo lugar.
- El cliente tolera respuestas legacy `{ "detail": "..." }` y cuerpos de texto
  plano (documentos) construyendo un `ApiError` sintético con el catálogo por
  status; `application/problem+json` siempre tiene prioridad.

### Pendiente conocido

`frontend/src/views/ReportesView.tsx` conserva **un** `any` documentado en
`reportData`: los nueve reportes devuelven formas distintas y todavía no tienen
modelo en `cafae/api/schemas.py`. Se tipará por reporte cuando el backend
publique esos esquemas; mientras tanto es el único `any` del frontend y está
marcado con su motivo.

## Verificación

```powershell
python scripts/test_api.py      # contrato y OpenAPI, sin base de datos
python scripts/test_seguridad.py # permisos, Bearer y bloqueo D.5
```

El test de contrato falla si un endpoint deja de documentar el sobre de error,
si `POST /api/planillas` pierde `revision_edicion`, si `GET /api/auditoria`
deja de publicar `Pagina[T]`, o si cualquiera de los siete routers de dominio
vuelve a capturar `UserError` en lugar de dejarlo al handler global. La única
excepción deliberada es `routes_auth`: el login distingue credenciales
inválidas (`401`) de solicitudes mal formadas (`400`), semántica que el handler
global no puede deducir de la clase de excepción.

Como `AccessError` y `SessionError` heredan de `UserError`, las rutas de
dominio ya no las traducen a `400`: el handler global responde `403
SIN_PERMISO` y `401 NO_AUTENTICADO` respectivamente, que es lo que el cliente
ya sabe interpretar.
