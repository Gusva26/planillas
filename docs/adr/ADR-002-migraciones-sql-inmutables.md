# ADR-002 · Migraciones SQL propias, inmutables y verificadas por hash

## Estado

Aceptado — implementado. Revisado el 28/10/2026.

## Contexto

El esquema se construyó por etapas y las migraciones incluyen privilegios,
triggers y funciones, no solo DDL de tablas. Los entornos son pocos (desarrollo
local y bases de prueba desechables), y el requisito es que una migración ya
aplicada **no pueda cambiar** sin que el sistema lo detecte.

## Decisión

- Un archivo por cambio: `database/migrations/NNN_nombre_en_snake_case.sql`.
- `scripts/migrate.py` aplica los archivos en orden dentro de **una sola
  transacción**, con `pg_advisory_xact_lock` para excluir ejecuciones
  concurrentes.
- Cada migración aplicada se registra en `public.cafae_migraciones` con su
  SHA-256. Si el hash cambia, el runner aborta.
- Los archivos no incluyen `BEGIN`/`COMMIT` propios.
- Solo se aceptan bases `cafae_dev` o `cafae_test_*`.

## Alternativas consideradas

- **Alembic**: autogeneración y downgrades, pero acopla las migraciones a los
  modelos Python y no cubre bien privilegios/triggers; el proyecto no usa ORM.
- **Flyway / Liquibase**: maduros, pero agregan una dependencia JVM y una
  convención más pesada para ocho migraciones.
- **`psql` manual**: sin registro ni detección de deriva.

## Consecuencias

- **Positivas**: historial auditable; imposible editar una migración aplicada
  en silencio; cero dependencias Python adicionales; funciona igual en local y
  en bases de prueba.
- **Negativas**: no hay `downgrade` automático — revertir exige escribir otra
  migración; no hay autogeneración; el estado real está en la base, no en un
  archivo de modelos.
- **Operativas**: recrear una base exige correr migraciones y luego
  `python -m cafae.bootstrap`.

## Trade-offs

Se prioriza **inmutabilidad y trazabilidad** sobre la comodidad de
autogeneración y rollback. Para un esquema con reglas de negocio en la base,
el intercambio es correcto.
