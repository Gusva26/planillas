# ADR-003 · Un único artefacto sirve la API y la SPA en el mismo origen

## Estado

Aceptado — implementado. Revisado el 28/10/2026.

## Contexto

El sistema se despliega en un servidor institucional y se consume desde la red
local. No hay CDN ni balanceador. Se busca minimizar piezas operativas y evitar
problemas de CORS, cookies y rutas relativas.

## Decisión

- El `Dockerfile` compila el frontend en una etapa Node y copia `dist/` a
  `static/` en la imagen final.
- FastAPI registra los routers bajo `/api` y, **al final**, monta `static/` o
  `frontend/dist/` en `/`.
- El frontend llama rutas relativas (`/api/...`), sin configuración de host.
- Un solo contenedor de aplicación detrás de `127.0.0.1:8501`.

## Alternativas consideradas

- **Nginx como sidecar**: mejor serving estático, compresión y caché, pero una
  pieza más que configurar y versionar.
- **Host estático separado** (S3/CDN): añade configuración de CORS, TLS y
  despliegues coordinados, sin beneficio en red local.
- **SSR (Next.js)**: no aporta para una aplicación interna autenticada.

## Consecuencias

- **Positivas**: despliegue de una imagen; mismo origen ⇒ sin preflight; rutas
  relativas; un solo healthcheck (`/api/health`).
- **Negativas**: el serving estático no compite con Nginx (caché, `gzip`,
  inmutabilidad de assets); el montaje en `/` debe quedar después de los
  routers para no capturar `/api`; el escalado horizontal exige sticky sessions
  o sesiones compartidas (ver ADR-004).
- **Seguridad**: al ser mismo origen, CORS abierto es innecesario; ver deuda
  D-09.

## Trade-offs

Se prioriza **simplicidad operativa** sobre rendimiento de serving estático.
Si el sistema se expone a Internet o crece el tráfico, mover el estático a un
proxy/CDN sin cambiar el contrato de la API.
