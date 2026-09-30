# Decisiones confirmadas después de revisar las plantillas

Este documento registra la respuesta del usuario a los cinco puntos de revisión y prevalece sobre las propuestas anteriores. Las diferencias H01–H06 dejan de bloquear el diseño conforme a las reglas siguientes. H07 conserva pendiente la validación bancaria.

## 1. Un único ingreso

Retirar de los nuevos formatos y del modelo operativo los conceptos «Importe adicional», «Reintegro» y «Otros ingresos». No conservarlos como entradas editables ni como sumandos ocultos.

```text
TOTAL DESCUENTOS = suma de los ocho conceptos
NETO = IMPORTE - TOTAL DESCUENTOS
```

La autorización permite adaptar la distribución de los documentos para retirar esos conceptos. Los Excel originales siguen siendo referencias intactas; no se sobrescriben ni se corrigen sus celdas.

En II.EE., el importe proviene de P («IMPORTE»), no de P158 si ese total incluye Q. En la boleta, el único ingreso corresponde a J24; se retira la línea de J25 («Otros ingresos»). La futura importación debe avisar y detener esa fila si un original contiene un ingreso adicional distinto de cero: nunca descartarlo silenciosamente ni sumarlo al importe autorizado.

## 2. Importe de Sede

El usuario identifica **REMUN. TOTAL** como el importe CAFAE mensual antes de descuentos. En la plantilla recibida corresponde a la **columna I**, encabezado I5.

La correspondencia será `REMUN. TOTAL → trabajadores.importe → planilla_detalle.importe` para la carga inicial y la copia mensual respectivamente. El histórico conserva su propio importe. «RO» no origina un segundo ingreso ni se suma al importe. No inferir montos desde la columna H de reintegro ni rellenar I vacía con cero como si fuera un pago validado.

## 3. Firmas por tipo de planilla

La precisión del usuario es que **Dirección de Gestión Administrativa pertenece solo a II.EE.** Se conserva la distribución de firmas de las referencias: cuatro posiciones para II.EE. y tres para Sede. Esto corrige la propuesta anterior de agregar esa cuarta firma a Sede.

| Posición | II.EE. | Sede |
|---|---|---|
| 1 | Dirección de UGEL | Dirección de UGEL |
| 2 | Dirección de Gestión Institucional | Dirección de Gestión Institucional |
| 3 | Dirección de Gestión Administrativa | Especialista en Finanzas |
| 4 | Especialista en Finanzas | No aplica |

Los cargos de la tabla describen la distribución inicial, no nombres de personas ni textos rígidos en código. Las personas y cargos son configurables. No asignar automáticamente a Sede el firmante de Gestión Administrativa por compartir una posición numérica con II.EE.

Al cerrar, validar las posiciones 1–4 de II.EE. o 1–3 de Sede. Guardar nombre y cargo seleccionados en la versión histórica. La sección final y paginación deben reservar espacio para la cantidad correspondiente; las firmas aparecen solo en la última página.

## 4. Ocho descuentos completos

Incluir en el detalle y cuadro final de ambos formatos:

1. Pichincha.
2. Caja Sullana.
3. Sub-CAFAE.
4. Conv. BRENTA.
5. SITRASE.
6. SITASE / FENTASE.
7. Licencia S/G.
8. Otros descuentos.

Se autoriza ajustar la distribución para incorporar las columnas y renglones que faltaban. Los siete descuentos editables se guardan en `planilla_descuentos`; licencia permanece derivada de los días 0–30 en `planilla_detalle`. No duplicar licencia en ambas estructuras.

El cierre de II.EE. debe sumar también Otros. En Sede, BRENTA debe derivarse de su detalle, no de un cero fijo. Los ocho subtotales deben conciliar con el total de descuentos y con la suma de personas de la misma versión.

## 5. TXT sujeto a validación bancaria

Validar contra un TXT aceptado por el banco o contra su especificación oficial. Hasta disponer de esa evidencia, no aprobar como contrato los 28 dígitos anotados en Excel ni deducir codificación, rellenos, cabecera/pie, fin de línea o reglas de cuentas.

La generación bancaria permanece pendiente y no bloquea el diseño de personal, catálogos, cálculos, cierre, historia o documentos no bancarios. No implementar una salida provisional que parezca apta para pagar.

## Impacto en las pruebas

- Verificar que los nuevos formatos no muestran entradas de ingresos adicionales y que el neto usa un solo importe.
- Usar valores distintos en H, I y J de una muestra sintética de Sede: la entrada debe tomar exclusivamente I (REMUN. TOTAL), sin cambiar el original.
- II.EE. no cierra con tres firmas; Sede cierra con tres posiciones válidas y rechaza una cuarta posición.
- Cambiar posteriormente nombre/cargo de una firma no altera cierres anteriores.
- Poner un valor diferente en cada uno de los ocho descuentos y comprobar su presencia en detalle, cierre y total, sin contar licencia dos veces.
- TXT sigue deshabilitado hasta validar el contrato y pasar las pruebas contra la referencia bancaria.

## Estado de implementación

Al 24/09/2026, Docker y PostgreSQL están operativos. Se aplicaron seis migraciones a `cafae_dev`, con cálculo de descuentos, protección de cierres, firmas por tipo, auditoría y permisos técnicos. Pasaron 27 pruebas de integridad, cuatro escenarios concurrentes y una restauración aislada. Véase el [informe de implementación](09-base-datos-implementada.md).

La etapa 2 ya implementó la interfaz de acceso y la autenticación; véase [acceso y usuarios](10-acceso-y-usuarios.md). La importación desde Excel y los formatos impresos aún requieren sus etapas de desarrollo. La validación bancaria sigue pendiente y la base bloquea el registro de documentos TXT. No se cargaron personas ni usuarios reales.
