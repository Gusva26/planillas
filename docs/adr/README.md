# Registro de decisiones de arquitectura (ADR)

Cada ADR documenta una decisión estructural: contexto, alternativas,
consecuencias y el trade-off aceptado. Se escriben una vez y se **supersedan**,
nunca se reescriben.

| ADR | Decisión | Estado |
| --- | --- | --- |
| [ADR-001](ADR-001-monolito-modular-sin-orm.md) | Monolito modular con capas explícitas y SQL directo, sin ORM | Aceptado |
| [ADR-002](ADR-002-migraciones-sql-inmutables.md) | Migraciones SQL propias, inmutables y verificadas por hash | Aceptado |
| [ADR-003](ADR-003-despliegue-unico-spa-mas-api.md) | Un único artefacto sirve la API y la SPA en el mismo origen | Aceptado |
| [ADR-004](ADR-004-sesion-token-opaco.md) | Sesión por token opaco hasheado, con doble control de acceso | Aceptado |
| [ADR-005](ADR-005-react-ui-objetivo-streamlit-legado.md) | React como UI única; retiro planificado de Streamlit | Aceptado |
| [ADR-006](ADR-006-documentos-permiso-y-version-cerrada.md) | Documentos oficiales con permiso específico y versión cerrada | Aceptado |

## Convención

- Numeración correlativa de tres dígitos; el título no se cambia.
- Estados válidos: `Propuesto`, `Aceptado`, `Rechazado`, `Supersedido por NNN`.
- Un ADR aceptado no se edita para cambiar la decisión: se crea otro que lo
  supersede y se actualiza el estado del anterior.
- Las decisiones de negocio (D.1–D.5) viven en
  [`../08-decisiones-confirmadas.md`](../08-decisiones-confirmadas.md); los ADR
  no las reemplazan, las implementan.
