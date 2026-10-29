# ADR-001 · Monolito modular con capas explícitas y SQL directo (sin ORM)

## Estado

Aceptado — implementado. Revisado el 28/10/2026.

## Contexto

El sistema gestiona planillas de una única institución (UGEL Chepén), con
volumen bajo (decenas de instituciones, miles de filas por mes) y requisitos
duros de exactitud monetaria, inmutabilidad de cierres y auditoría. La base ya
impone reglas críticas con constraints, triggers y privilegios por rol SQL.

El código se organiza en módulos de dominio (`cafae/planillas.py`,
`trabajadores.py`, `catalogos.py`, …) que exponen clases de servicio, y una capa
`cafae/api/` con routers FastAPI. El acceso a datos usa `psycopg` con
`dict_row` y SQL parametrizado dentro de `cafae.db.transaction`.

## Decisión

Mantener un **monolito modular** con una regla de dependencia explícita:

```
frontend (React)  →  cafae/api/routes_*  →  cafae/<dominio>  →  cafae/db.transaction  →  PostgreSQL
                          ↓
                     cafae/api/deps.py  →  AuthService / security.py
```

- La API no contiene reglas de negocio ni SQL propio.
- El dominio no importa FastAPI ni Streamlit.
- Los generadores de documentos reciben datos ya resueltos; no consultan la base.
- La autorización real ocurre en el servicio (`AuthService.authorized` /
  `data_transaction`), no en la UI.

## Alternativas consideradas

- **SQLAlchemy ORM + repositorios**: mejor ergonomía y mapeo automático, pero
  agrega una capa de traducción sobre un esquema que ya vive en SQL (triggers,
  privilegios, `Decimal`), y difumina qué consulta exacta se ejecuta.
- **Microservicios por dominio**: aísla fallos, pero multiplica despliegues,
  transacciones y operación para un sistema de una sola institución.
- **Query builder ligero**: punto medio, sin ganancia clara frente al SQL
  parametrizado actual.

## Consecuencias

- **Positivas**: control total del SQL y del plan de ejecución; una sola unidad
  de despliegue; reglas críticas en la base, no solo en el código; pruebas
  contra PostgreSQL real.
- **Negativas**: mapeo manual a diccionarios; SQL repetido entre servicios;
  riesgo de que el SQL se filtre a los routers (ver deuda D-03); migraciones y
  tipado se resuelven a mano.
- **Deuda asociada**: extraer el SQL que hoy vive en `routes_catalogos`,
  `routes_planillas` y `routes_documentos` hacia sus servicios.

## Trade-offs

Se prioriza **control y simplicidad operativa** sobre ergonomía del ORM. Si el
equipo crece o aparecen múltiples fuentes de datos, esta decisión debe
revisarse; no antes.
