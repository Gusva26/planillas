# ADR-004 · Sesión por token opaco, hasheado en base, con doble control de acceso

## Estado

Aceptado — implementado. Revisado el 28/10/2026.

## Contexto

Se requiere autenticación local (sin OIDC), revocación inmediata, bloqueo por
intentos, roles institucionales y auditoría de accesos denegados. La base ya
tiene privilegios separados (`cafae_consulta`, `cafae_operador`,
`cafae_admin`).

## Decisión

- Token aleatorio opaco (32–128 caracteres). En base se guarda **solo su
  SHA-256** (`sesiones.token_hash`).
- Vencimiento absoluto de 8 horas e inactividad de 30 minutos, verificados en
  cada operación.
- Contraseñas con Argon2id (`time_cost=3`, `memory_cost=65536`, `parallelism=4`)
  y hash ficticio para igualar tiempos cuando el usuario no existe.
- Autorización en dos capas dentro de la misma transacción:
  1. `PERMISSIONS` en `cafae/security.py` valida el permiso lógico.
  2. `SET LOCAL ROLE` cambia al rol SQL correspondiente
     (`ADMINISTRADOR → cafae_admin`, `PLANILLAS → cafae_operador`,
     `CONSULTA → cafae_consulta`).
- Cambio de contraseña, cambio de rol o desactivación revocan sesiones.
- Todo rechazo se audita fuera de la transacción abortada.

## Alternativas consideradas

- **JWT stateless**: no requiere consultar la base, pero no permite revocación
  inmediata ni control de inactividad sin una lista negra (que reintroduce la
  consulta).
- **Cookie de sesión `HttpOnly`**: mejor frente a XSS, pero exige CSRF token y
  ajustes de dominio; evaluable como evolución (ver deuda D-10).
- **OIDC institucional**: deseable a futuro, pero no disponible hoy y no elimina
  la necesidad de autorización propia.

## Consecuencias

- **Positivas**: revocación inmediata; la base aplica el mismo modelo de
  permisos que el código; intentos y denegaciones quedan auditados; no hay
  secretos de firma que rotar.
- **Negativas**: una consulta a `sesiones` por request; el frontend guarda el
  token en `localStorage`, expuesto a XSS; el escalado horizontal es viable
  porque el estado está en la base, pero cada request paga el acceso.
- **Resuelto el 28/10/2026**: `cafae/api/deps.py` acepta únicamente
  `Authorization: Bearer`; se eliminaron query string y cabeceras alternativas.

## Trade-offs

Se prioriza **revocación y auditoría** sobre statelessness. Es la decisión
correcta para un sistema administrativo con datos personales.
