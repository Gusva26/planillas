# ADR-005 · React como UI única y retiro planificado de Streamlit

## Estado

**Aceptado** — 28/10/2026, por decisión del responsable del sistema.

## Contexto

Hoy conviven dos interfaces:

- **React 19 + Vite** (`frontend/src/`) que consume `/api` y se sirve como
  estático desde FastAPI.
- **Streamlit** (`app.py` + `cafae/ui/`) que importa directamente los servicios
  de dominio, sin pasar por la API.

Ambas implementan pantallas equivalentes (planillas, trabajadores, catálogos,
importaciones, documentos, reportes, auditoría). Cada cambio funcional debe
hacerse dos veces o queda divergente. Además, Streamlit usa un esquema de
sesión distinto (`st.session_state`) y no comparte el contrato de la API; el
hotfix de seguridad del 28/10 (D-02) tuvo que corregirse en dos clientes porque
cada UI resolvía las credenciales a su manera.

## Decisión

1. **React es la única UI del sistema.** Toda funcionalidad nueva se implementa
   solo en React + `/api`.
2. **Streamlit se retira**, no se mantiene en modo legado indefinido. Desde hoy
   queda congelado: no recibe features, ni correcciones de diseño, ni cambios
   de permisos.
3. **Plan de retiro**:
   1. Completar la matriz de paridad de pantallas React ↔ Streamlit y firmarla.
   2. Correr el flujo integral completo contra `/api` sin Streamlit.
   3. Eliminar `app.py`, `cafae/ui/`, `.streamlit/`, la dependencia `streamlit`
      de `requirements*.txt` y el servicio de UI del despliegue.
   4. Ajustar `compose.yaml`/`Dockerfile` para exponer solo la API + SPA.
4. **Criterio de cierre**: la suite completa pasa en verde sin `streamlit`
   instalado, y ninguna pantalla de la matriz queda solo en Streamlit.
5. La lógica de negocio permanece exclusivamente en `cafae/*.py`; ninguna UI
   contiene reglas.
6. Mientras el retiro no se ejecute, **ninguna corrección de seguridad se
   replica en Streamlit**: se corrige en la API, que es la única superficie
   soportada.

## Alternativas consideradas

- **Mantener ambas**: duplica mantenimiento y pruebas; el riesgo de divergencia
  ya es visible (permisos y flujos distintos). Descartada.
- **Congelar Streamlit sin retirarlo**: deja código muerto con credenciales,
  sesiones y reglas duplicadas; sigue siendo superficie de ataque. Descartada.
- **Volver a Streamlit**: más rápido para formularios, pero pierde la SPA, el
  diseño institucional y el contrato tipado. Descartada.

## Consecuencias

- **Positivas**: un solo frontend que probar y desplegar; una sola ruta de
  autorización; se elimina `cafae/ui/` (≈1.300 líneas), `app.py` y la
  dependencia `streamlit`; el despliegue queda alineado con ADR-003 (un solo
  artefacto).
- **Negativas**: hasta completar el retiro hay dos árboles de dependencias en la
  imagen; si algún flujo solo existe en Streamlit, hay que portarlo antes de
  borrar. El retiro toca `compose.yaml`, `Dockerfile`, `requirements.txt` y la
  documentación de operación, así que se ejecuta como cambio propio, no
  mezclado con features.
- **Riesgo asumido**: durante la ventana de retiro, Streamlit puede quedar
  desactualizado respecto de la API. Es aceptable porque deja de ser una
  interfaz soportada.

## Trade-offs

Se prioriza **una sola superficie de producto** sobre la comodidad de mantener
una herramienta rápida para prototipos. Si se necesita prototipado interno,
debe hacerse fuera de este repositorio.
