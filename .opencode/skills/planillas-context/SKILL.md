---
name: Planillas CAFAE — Contexto del Proyecto
description: Arquitectura, comandos, migraciones, tests y reglas de negocio del sistema de planillas CAFAE (FastAPI + PostgreSQL 17 + React/Vite, con UI Streamlit legada). Úsala al empezar cualquier tarea de código en este repositorio para ubicar capas, ejecutar el proyecto o los tests y respetar las convenciones de migración y dominio.
---

# Planillas CAFAE · UGEL Chepén

Contexto operativo del repositorio. No repitas esta estructura en la respuesta:
usala para decidir dónde mirar y cómo ejecutar.

## Cuándo usar esta skill

- Al iniciar cualquier cambio de código, migración o test en este repo.
- Para saber qué capa toca un cambio (API, dominio, UI, documentos, DB).
- Para ejecutar migraciones o la suite de pruebas sin romper datos reales.

No la uses para preguntas conceptuales ni para explicar teoría.

## Stack

| Capa | Tecnología | Ubicación |
| --- | --- | --- |
| API REST | FastAPI + Uvicorn, montada en `/api`, puerto 8501 | `cafae/api/` |
| Dominio | Python 3.12, sin ORM (SQL con `psycopg` + `transaction()`) | `cafae/*.py` |
| DB | PostgreSQL 17 (contenedor `cafae-postgres-dev`, puerto host 55432) | `database/` |
| Frontend | React 19 + TypeScript + Vite | `frontend/src/` |
| UI legada | Streamlit (`app.py`, `cafae/ui/`) | raíz |
| Documentos | PDF (reportlab), Excel (openpyxl), TXT | `cafae/documentos/` |
| Empaquetado | Docker multi-stage; el `dist` de Vite se sirve como estático desde `/` | `Dockerfile` |

`cafae/api/main.py` registra los routers bajo `/api`, expone `/api/health` y
monta `static/` o `frontend/dist/` si existe. Las excepciones de dominio
(`UserError`, `SessionError`, `AccessError`) se traducen a 400/401/403.

## Mapa de módulos

- `cafae/auth.py` + `cafae/security.py` — login, sesiones, roles, permisos,
  hashing Argon2. Los roles/permisos viven en `security.py` (`ROLES`,
  `PERMISSIONS`); el enforcement real está en el servicio, no en la UI.
- `cafae/planillas.py` — ciclo mensual: crear desde maestro o copiar mes
  anterior, edición masiva, recálculo, cierre, reapertura versionada,
  concurrencia optimista (`revision_edicion`).
- `cafae/trabajadores.py`, `cafae/catalogos.py`, `cafae/importaciones.py`,
  `cafae/extractores.py`, `cafae/reportes.py`, `cafae/auditoria.py`.
- `cafae/calculos.py` — fórmulas de los 8 conceptos y licencias sin goce.
- `cafae/api/routes_*.py` — un router por dominio; `deps.py` resuelve sesión.
- `cafae/documentos/` — `pdf_planillas.py`, `excel_planillas.py`,
  `boletas.py`, `remuneraciones.py`, `banco_txt.py` (bloqueado a propósito).
- `frontend/src/api/client.ts` — cliente HTTP único; `AuthContext.tsx`
  guarda el token. Vistas en `views/`, sin router: el estado de navegación
  se maneja en `App.tsx`.

## Comandos

```powershell
# Servicios
docker compose up -d --wait
docker compose ps
docker compose stop

# Migraciones (idempotentes, dentro del contenedor)
python scripts/migrate.py                     # cafae_dev
python scripts/migrate.py --database cafae_test_x

# Primer admin (interactivo)
docker compose run --build --rm app python -m cafae.bootstrap

# Frontend
cd frontend; npm install; npm run dev         # Vite en su puerto propio
cd frontend; npm run build                    # tsc + vite build -> dist/
```

## Migraciones

- Viven en `database/migrations/NNN_nombre.sql` (`NNN` de 3 dígitos,
  `nombre` en snake_case). El siguiente número es `max + 1`.
- `scripts/migrate.py` aplica cada archivo una vez y **guarda su SHA-256** en
  `public.cafae_migraciones`. Si editás una migración ya aplicada, el runner
  aborta con "La migración aplicada cambió". Nunca la edites: agregá una nueva.
- Todo corre en una transacción con `pg_advisory_xact_lock`. No metas
  `BEGIN`/`COMMIT` dentro del archivo `.sql`.
- `database/schema_propuesto.sql` es referencia/diseño, no el estado real.
- Borrar y recrear la DB exige re-ejecutar migraciones y `cafae.bootstrap`.

## Tests

- Son `unittest`, no pytest, y **no** se ejecutan con `python -m pytest`.
- Cada dominio tiene su runner: `scripts/test_auth.py`,
  `scripts/test_planillas.py`, `scripts/test_trabajadores.py`,
  `scripts/test_importaciones.py`, `scripts/test_catalogos.py`,
  `scripts/test_integral.py`, `scripts/test_seguridad.py` (este último no
  necesita base de datos).
- El runner crea una base desechable `cafae_test_<random>` en el contenedor,
  migra, corre el test con el código montado y **borra la base** al final.
  Requiere el contenedor `db` arriba (`docker compose up -d --wait`).
- Los tests validan esa condición al importar: sin `CAFAE_DB_NAME` que empiece
  con `cafae_test_` hacen `SystemExit`. No los corras contra `cafae_dev`.
- Cada runner escribe un resumen en `test-results/<dominio>.json`.
- Si agregás tests, seguí el patrón `tests/<dominio>/test_*.py` + runner en
  `scripts/` que monte esa carpeta en `/tests`.

## Reglas de dominio que no se cambian

- Un único ingreso. `Total Descuentos` = suma de los 8 conceptos.
  `Neto = Importe − Total Descuentos`. No agregar reintegros ni sumandos extra.
- 8 descuentos: Pichincha, Caja Sullana, Sub-CAFAE, Convenio BRENTA, SITRASE,
  SITASE/FENTASE, Licencia sin goce, Otros.
- Licencia sin goce = `(Importe / 30) × Días`.
- Exactamente 4 firmas en II.EE. y 3 en Sede, en bloque indivisible al final.
- Montos en `Decimal(12,2)`; en JSON se serializan como `float` solo para
  transporte (ver `CustomJSONEncoder`). No uses `float` en el dominio.
- DNI es texto de 8 dígitos (preserva ceros). No lo conviertas a entero.
- La auditoría es append-only; nunca `UPDATE`/`DELETE` sobre ella.
- El TXT bancario permanece bloqueado (D.5): el endpoint exige `txt_bancario`,
  solo opera sobre versiones `CERRADA` y responde `403` salvo
  `CAFAE_TXT_BANCARIO=1`.
- Todos los documentos oficiales (PDF, Excel, remuneraciones, boletas,
  cuadernillo) exigen `generar_documentos`; `CONSULTA` solo lee (ADR-006).

## Trampas conocidas

- El frontend habla con `/api` en el mismo origen; en dev con Vite hace falta
  proxy o `VITE_API_URL`. Revisá `frontend/vite.config.ts` antes de tocar URLs.
- CORS está en `allow_origins=['*']` con credenciales: es intencional para
  desarrollo, no lo copies a producción sin revisar.
- Los tests usan `sys.path.insert(0, '/app')`: el código se ejecuta dentro del
  contenedor, no en Windows directamente.
- Hay dos UIs: React es la vigente; `app.py`/`cafae/ui/` (Streamlit) es legado.
  Antes de duplicar un cambio, confirmá cuál se mantiene.
- `scripts/` contiene pobladores de datos de prueba (`poblar_*.sql`,
  `poblar_planillas_prueba.py`): nunca apuntarlos a datos reales.
