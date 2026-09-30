# Referencias y decisiones pendientes

**Reglas confirmadas después de la revisión:** [decisiones del usuario](08-decisiones-confirmadas.md). Ingreso único; REMUN. TOTAL como importe de Sede; cuatro firmas para II.EE. y tres para Sede; ocho descuentos en detalle y cierre. Solo la validación bancaria de H07 sigue pendiente entre los cinco puntos consultados.

**Actualización posterior a la propuesta inicial:** los cuatro Excel ya fueron recibidos y revisados. El [informe de análisis](07-analisis-plantillas.md) contiene hallazgos por celda y sustituye las suposiciones que dependían de archivos ausentes. Las decisiones D01–D11 siguientes siguen siendo propuestas salvo la evidencia expresamente recogida en ese informe.

## Inventario comprobado

| Referencia | Disponibilidad | Uso previsto |
|---|---|---|
| Texto pegado.txt | Recibido y leído | Requisitos funcionales 1–56 |
| PLANILLA CAFAE - II.EE.s SETIEMBRE 2026 | Recibido y revisado | Columnas, cálculos, agrupaciones, cierre y hojas DX PARA TXT / GENERADOR TXT |
| PLANILLA CAFAE - SEDE UGELCH SETIEMBRE | Recibido y revisado | Organización por áreas y formato particular |
| HOJA DE TRABAJO DE REMUNERACIONES - PLANILLA CAFAE 2026 | Recibido y revisado | Distribución oficial y consolidación por meta |
| GENERAR BOLETA CAFE | Recibido y revisado | Boleta individual, fórmulas y campos adicionales |
| Logo institucional | Imagen de encabezado en boleta | Referencia visual disponible; resolución final por validar |

Se analizaron los cuatro libros Excel y sus 15 hojas. No se recibieron PDF impresos de control ni un TXT aceptado por el banco; la revisión no acredita todavía equivalencia de impresión o aceptación bancaria.

## Protocolo de análisis y validación

1. Registrar nombre, tamaño, SHA-256 y versión del archivo; conservar original sin modificaciones.
2. Inventariar hojas visibles y ocultas, tablas, nombres definidos, fórmulas, valores almacenados, vínculos externos, macros y protecciones. No ejecutar macros desconocidas durante la inspección.
3. Extraer celdas combinadas, fuentes, bordes, anchos, alturas, imágenes, áreas de impresión, márgenes, escala, saltos y encabezados repetidos.
4. Comparar campos de II.EE. y Sede; registrar todos, incluso los no citados en los requisitos. Un campo descubierto se incorpora mediante una migración, sin ocultarlo en un JSON genérico.
5. Rastrear origen de cada subtotal, fórmula de licencia, regla de redondeo, orden de filas y sumatoria por meta.
6. En DX PARA TXT y GENERADOR TXT: localizar fórmulas, concatenaciones, rellenos, posiciones, cabeceras, pies, orden, codificación y fin de línea. Obtener un archivo aceptado de ejemplo para comparación byte por byte.
7. Renderizar las plantillas y producir muestras de 1, 2 y varias páginas; medir la sección final y las firmas correspondientes al tipo (cuatro II.EE., tres Sede).
8. Elaborar una tabla «campo original → columna de datos → regla → posición de salida → prueba».
9. Si una fórmula contradice los requisitos, detener ese cálculo o generador y documentar la diferencia concreta. El resto del trabajo independiente puede continuar.

OpenPyXL no se tratará como motor de recálculo de Excel: se contrastarán fórmulas y valores calculados con el original validado. No se deducirá una fórmula de un valor aislado.

## Propuestas explícitas, todavía sujetas a contraste

| ID | Ambigüedad o dato faltante | Propuesta de diseño | Consecuencia |
|---|---|---|---|
| D01 | §13 permite institución/todas; §42 exige periodo único por tipo | Una planilla lógica por mes/año y tipo. El selector institucional determina la carga inicial; las instituciones restantes se agregan a esa misma versión abierta | El SQL no permite múltiples planillas II.EE. independientes del mismo mes. Si se requieren, cambiar alcance y restricción antes de implementar |
| D02 | §6 enumera BORRADOR, ABIERTO, EN REVISIÓN, CERRADO, CON OBSERVACIONES; §26 define tres estados | Estados persistentes BORRADOR, EN_REVISION y CERRADA. «Abierta» agrupa las dos primeras; «Con observaciones» es un indicador de validación | Conserva los conceptos visuales sin duplicar estados contradictorios |
| D03 | El rol PLANILLAS no enumera permiso de cierre, el administrador sí | Solo ADMINISTRADOR cierra y reabre inicialmente | Ampliar permiso de cierre requiere definición explícita |
| D04 | No se establece método de redondeo | Proponer ROUND_HALF_UP a dos decimales, redondeando licencia tras multiplicar días | No consolidar esta regla como definitiva hasta revisar Excel; jamás redondear primero el valor diario |
| D05 | Neto negativo requiere advertencia; no se indica expresamente si impide cerrar | Permitir borrador con alerta y proponer bloquear cierre y TXT con neto negativo | Política de cierre pendiente de confirmar; no imponer un CHECK de neto no negativo a borradores |
| D06 | Se exige validar cuentas pero no se indica longitud ni algoritmo | Conservar cuenta como texto y mostrar faltantes; validación bancaria específica pendiente | TXT deshabilitado hasta conocer contrato real; no inferir longitudes |
| D07 | Reapertura de una planilla histórica | Abrir una nueva versión de la misma planilla; conservar la versión cerrada anterior y sus documentos | El historial puede descargar cada cierre. Los reportes habituales usan una única versión vigente, sin doble conteo |
| D08 | Meta asociada a nivel/institución; Sede también requiere meta | Institución puede tener meta explícita; nivel ofrece meta por defecto; área de Sede puede tener meta explícita | Prioridad institución/área → nivel. Conflictos o ausencia se revisan antes del cierre |
| D09 | No hay volumen de trabajadores, usuarios simultáneos, hosting ni objetivos de recuperación | Medir con un conjunto representativo; despliegue institucional privado con TLS, sin publicar todavía | Definir capacidad, RPO, RTO y retención antes de producción |
| D10 | No se define cuándo un descuento es «sospechoso» | Siempre alertar si supera importe; umbrales adicionales configurables y versionados | No introducir límites monetarios arbitrarios |
| D11 | «DNI único en activos cuando corresponda» y DNI único administrativo en §7 | Un DNI único para todo el maestro, con reactivación del registro existente | Evita duplicar identidades históricas; validar posibles excepciones administrativas |

## Alcance de esta entrega

Se definen arquitectura, tablas y contratos; no se certifica un sistema listo para uso real. Tras la revisión, el trabajo pendiente es resolver diferencias y actualizar el diseño. No se reemplazan documentos obligatorios por formatos simplificados.
