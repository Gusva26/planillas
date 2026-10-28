# AGENTS.md — Sistema de Planillas CAFAE · UGEL Chepén

Instrucciones para agentes de OpenCode en este repositorio.

## Protocolo de selección de skills

0. Si la tarea toca código de este repo, cargá siempre `planillas-context`
   (arquitectura, comandos, migraciones, tests y trampas del proyecto).
1. **Antes de tocar código**, elegí el resto de las skills con la tabla de ruteo de abajo.
2. **Anuncialo en una línea**, antes de cargarlas:
   `Skills: planillas-context, fastapi-expert — endpoint nuevo sobre tabla existente.`
3. Cargalas con la herramienta `skill` usando el ID exacto.
4. **Máximo 2–3 skills por tarea.** Si la tarea cruza dos dominios, usá una
   "guardian" (`fullstack-guardian`) + un especialista, no cinco.
5. Si el usuario escribe `@skill-id` en el prompt, cargala sin discutir.
6. Si ninguna descripción encaja, **no cargues ninguna** y resolvé con las
   herramientas normales. Ante duda razonable, preguntá.

**No cargar skills** para: preguntas conceptuales, explicar código existente,
listar archivos, responder dudas generales o conversación.

## Tabla de ruteo

| Situación | Skills |
| --- | --- |
| Endpoint, router, DTO, validación, auth JWT | `fastapi-expert` |
| Componente/vista React, estado, hooks, tipos | `react-expert` (+ `typescript-pro` si hay tipos complejos) |
| Feature end-to-end (API + UI + permisos) | `fullstack-guardian` (+ `secure-code-guardian` si toca login/inputs) |
| Query lenta, índices, EXPLAIN, JSONB | `postgres-pro` + `sql-pro` |
| Migración o cambio de schema | `sql-pro` + `postgres-pro` |
| Bug, stack trace, "no funciona" | `debugging-wizard` |
| Tests unitarios o de integración | `test-master` |
| Tests E2E de la UI | `playwright-expert` |
| Revisión de cambios antes de commit | `code-reviewer` (+ `security-reviewer` si toca auth/datos personales) |
| Excel (`openpyxl`), PDF (`reportlab`), cálculos de planilla | `python-pro` (+ `pandas-pro` si es análisis tabular) |
| Docker, compose, deploy, CI | `devops-engineer` |
| Rendimiento, métricas, logging | `monitoring-expert` (+ `database-optimizer`) |
| Documentación o docstrings | `code-documenter` |
| Diseño de API desde cero | `api-designer` |

## Mapa del proyecto

- **Backend**: Python 3 · FastAPI (`cafae/api/`) · PostgreSQL 17 vía `psycopg`.
  Lógica de dominio en `cafae/*.py` (`planillas.py`, `trabajadores.py`,
  `importaciones.py`, `calculos.py`, `auth.py`, `auditoria.py`).
- **Frontend**: React + TypeScript + Vite en `frontend/src/`
  (`views/`, `components/`, `api/client.ts`, `context/AuthContext.tsx`).
- **UI legada**: Streamlit en `app.py` y `cafae/ui/`.
- **Documentos**: generación de PDF/Excel/TXT en `cafae/documentos/`.
- **Base de datos**: `database/migrations/00N_*.sql` (numeración correlativa,
  nunca editar una migración ya aplicada) y `database/schema_propuesto.sql`.
- **Tests**: `tests/<dominio>/test_*.py` (auth, planillas, trabajadores,
  importaciones, catálogos, database, integracion).
- **Infra**: `compose.yaml` (db + app en 127.0.0.1:8501), `Dockerfile`,
  `scripts/db.ps1`, `scripts/setup_app.py`.

## Reglas de negocio que no se negocian

Ver `README.md` §3 (Decisiones D.1–D.5). En particular:

- Un único ingreso; `Total Descuentos` = suma de los 8 conceptos;
  `Neto = Importe − Total Descuentos`.
- Exactamente 4 firmas en II.EE. y 3 en Sede.
- Montos con `Decimal(12,2)`; DNI como texto de 8 dígitos.
- El TXT bancario permanece bloqueado hasta tener especificación oficial.

## Convenciones de trabajo

- Español para mensajes al usuario, nombres de dominio y comentarios.
- No romper migraciones aplicadas ni el historial de auditoría append-only.
- Todo cambio de comportamiento debe venir con su test en `tests/`.
- Antes de commitear: `Skills: code-reviewer` y revisar el diff completo.
