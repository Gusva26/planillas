# Navegación, permisos y experiencia de uso

Reglas confirmadas: un único ingreso; «REMUN. TOTAL» en Sede corresponde a importe. Los nuevos formatos retiran ingresos adicionales y muestran los ocho descuentos. Firmas configurables: cuatro para II.EE. y tres para Sede, según [decisiones vigentes](08-decisiones-confirmadas.md).

## Entrada y estructura de pantalla

La primera pantalla es Login: logo recibido, «Sistema de Gestión de Planillas CAFAE», «UGEL Chepén», usuario, contraseña y botón «Iniciar sesión». Campos con etiquetas visibles, navegación por teclado y mensaje genérico ante credenciales inválidas. No mostrar dashboard, métricas ni documentos antes de autenticar.

Al ingresar: encabezado con nombre completo, rol, fecha de Lima y «Cerrar sesión». Sidebar persistente, contenido con breadcrumb, título, breve descripción y acciones principales alineadas. Año/mes y ámbito siempre visibles en pantallas de planilla.

```text
Inicio
Personal
  Trabajadores II.EE.
  Trabajadores Sede
Planillas
  Instituciones Educativas
  Sede UGEL
  Importar descuentos
  Historial
Documentos
  PDF y Excel
  Boletas
  Hoja de remuneraciones
  TXT bancario
Reportes
Configuración                        [administrador]
  Instituciones
  Áreas de Sede
  Niveles y metas
  Cargos, categorías, situaciones y subtipos
  Firmas
  Identidad institucional
Usuarios                             [administrador]
Auditoría                            [administrador]
```

Los accesos «Documentos» e «Importar descuentos» llevan al mismo contexto de periodo/versionado usado en Planillas. No son sistemas separados ni solicitan volver a ingresar datos.

## Dashboard

Dos tarjetas principales grandes: **Planillas de Instituciones Educativas** y **Planillas de Sede UGEL**. Cada tarjeta muestra periodo, estado y acción «Ver planillas». Están disponibles para los tres roles, con acciones acordes al permiso.

Selector de periodo en el encabezado. Métricas: planilla actual, trabajadores activos, II.EE. registradas, importe mensual, descuentos y neto. Etiquetar si importes corresponden a borrador o último cierre; nunca mezclar cierres diferentes silenciosamente. Tabla de últimas planillas, importaciones recientes y alertas accionables. En ausencia de datos, indicar el siguiente paso sin cargar personas ficticias.

## Pantallas y contratos

| Pantalla | Contenido principal | Acciones |
|---|---|---|
| Trabajadores | Búsqueda DNI/nombre/apellido/código; filtros institución, nivel, cargo, categoría, situación, activo y tipo | Nuevo, editar, activar/desactivar con confirmación, historial y participaciones |
| Ficha de trabajador | Datos personales; adscripción; vínculo laboral; cuenta e importe; estado | Guardar, cancelar; advertencias claras de campos faltantes |
| Catálogos | Tabla buscable, estado, detalle y relaciones | Crear, editar, desactivar sin eliminar historia |
| Crear planilla | Año, mes, tipo, institución/todas según D01, origen maestro o mes previo | Previsualizar personal y confirmar creación; impedir duplicado |
| Editor de planilla | Datos fijos, importes y descuentos editables, días, resultados; scroll horizontal | Guardar lote, importar, limpiar descuentos, enviar a revisión |
| Importación | Tipo, archivo, extracción, mapeo, estadísticas, tabla y documento original | Corregir/revisar, seleccionar apariciones, elegir modalidad, previsualizar y aplicar |
| Revisión y cierre | Personal, sumas, alertas por fila, cuatro firmas II.EE. o tres Sede y estado del guardado | Ir a error, volver a editar, cerrar con confirmación |
| Historial | Filtros año/mes/tipo/institución/estado; cantidades, totales, fechas y autor | Ver, elegir versión, descargar documentos, reapertura por administrador |
| Documentos | Periodo y versión cerrada, prevalidaciones y archivos ya emitidos | PDF, Excel, remuneraciones, boleta individual/todas, TXT |
| Reportes | Filtros comunes y periodo comparado; tablas/gráficos con detalle | Consultar y descargar según rol |
| Usuarios | Usuario, nombre, rol, estado; sin mostrar hash ni contraseña | Crear, cambiar rol, desactivar, restablecer acceso |
| Auditoría | Fecha, actor, acción, entidad, resultado; filtros y diferencias | Consultar y exportar con permiso; ninguna edición |

La ficha incluye ID, DNI, apellidos, nombres, nivel, código modular/institución o área, subtipo, cargo, situación, nacimiento, ley/régimen, categoría, jornada, Multired, importe, estado y fechas. Código modular/nombre de institución se obtienen del catálogo, evitando escribirlos de nuevo. Para II.EE., un nivel distinto al institucional genera revisión.

## Editor de planilla

Breadcrumb de ejemplo: `Planillas > Instituciones Educativas > Octubre 2026 > Versión 1`.

Tabs: **Personal y descuentos · Importaciones · Revisión y firmas · Documentos**. Encima de la tabla: importe, descuentos y neto del conjunto; contador de personas y observaciones. Si una búsqueda filtra filas, distinguir «Totales del periodo» de «Subtotal visible». Guardar no debe borrar ni modificar las filas ocultas por el filtro.

Columnas fijas de identificación, campos históricos consultables y sección editable: importe, Pichincha, Caja Sullana, Sub-CAFAE, BRENTA, SITRASE, SITASE/FENTASE, días licencia y otros. Monto licencia, descuentos totales y neto son de solo lectura. Nombres de columnas completos mediante encabezados o ayuda accesible.

Recalcular al confirmar una celda y mostrar vista previa. «Guardar cambios» aplica el lote; indicador de cambios pendientes y hora del último guardado. Versión cerrada muestra modo lectura y fecha/autor. En revisión sigue editable con aviso; editar invalida la validación anterior hasta recalcularla.

## Previsualización de importaciones

Nombre del archivo, tipo de descuento, versión destino, uso de OCR y resumen: registros, identificados, no encontrados, duplicados y monto detectado. El monto detectado es informativo y puede incluir repetidos; mostrar por separado «Monto seleccionado para aplicar».

Tabla: estado, DNI, nombre original, trabajador encontrado, monto, página/fila y observación. Filtros Todos, Correctos, Revisar, No encontrados, Duplicados y Montos inválidos. Selecciones inicialmente desactivadas para casos dudosos. Corregir un DNI nunca se hace por similitud de nombre sin decisión humana trazable.

La confirmación muestra la modalidad escrita completa, cantidad de filas afectadas, montos antes/después y cantidad excluida. El botón «Aplicar descuentos» no se habilita por el mero hecho de subir un archivo.

## Estados y mensajes

| Etiqueta visible | Representación | Uso |
|---|---|---|
| Borrador | Gris azulado + texto | Versión editable |
| Abierta | Texto auxiliar | Agrupa borrador/en revisión según D02 |
| En revisión | Ámbar suave + icono | Editable con advertencia |
| Cerrada | Verde oscuro suave + candado | Solo lectura |
| Con observaciones | Badge ámbar/rojo según severidad | Validación de la revisión actual |

El color nunca es la única señal. Éxito: «Se guardaron los cambios». Error de conflicto: «Otra persona modificó esta planilla. Actualiza para revisar sus cambios». Error de importación: «No pudimos identificar una columna de importe. Selecciona la columna correcta». Fallo inesperado: mensaje comprensible y código de referencia; traceback solo en logs.

## Matriz inicial de permisos

| Operación | Administrador | Planillas | Consulta |
|---|---|---|---|
| Consultar personal, planillas e historial | Sí | Sí | Sí |
| Registrar/editar/activar/desactivar trabajadores | Sí | Sí | No |
| Crear/copiar planilla y editar versión abierta | Sí | Sí | No |
| Importar, resolver y aplicar descuentos | Sí | Sí | No |
| Limpiar descuentos con confirmación | Sí | Sí | No |
| Seleccionar firmas existentes | Sí | Sí | No |
| Enviar a revisión | Sí | Sí | No |
| Cerrar periodo | Sí | No, pendiente D03 | No |
| Reabrir con motivo y nueva versión | Sí | No | No |
| Generar PDF/Excel y documentos de cierre | Sí | Sí | No |
| Ver boletas y descargar reportes autorizados ya emitidos | Sí | Sí | Sí |
| Generar/descargar TXT | Sí | Sí | No |
| Editar instituciones, áreas, metas, firmas y catálogos críticos | Sí | No | No |
| Administrar usuarios, identidad y configuración | Sí | No | No |
| Consultar auditoría administrativa | Sí | No | No |

La propuesta de CONSULTA distingue generar de descargar: accede a artefactos autorizados ya emitidos. Cualquier autorización más específica por tipo de reporte se define antes de implementar ese módulo. Permisos también se verifican al descargar y no solo al entrar en la pantalla.

## Confirmaciones requeridas

- Limpiar descuentos: indicar periodo, personas afectadas y los ocho componentes; limpiar incluye días/licencia. No alterar importes.
- Desactivar: identificar trabajador; explicar que seguirá en historia y no entrará en cargas nuevas.
- Reemplazar importación: mostrar tipo exacto que se pondrá en cero y filas que mantendrán/cambiarán valores según modalidad.
- Cerrar: resumen, cuatro firmas para II.EE. o tres para Sede y advertencias; confirmar sobre revisión concreta.
- Reabrir: motivo obligatorio, aviso de nueva versión y conservación del cierre previo.

## Dirección visual

Paleta propuesta: azul institucional `#16324F`, fondo `#F4F6F9`, superficies blancas, texto `#172B3A`, acento verde petróleo `#176B69`. Comprobar contraste de cada combinación al implementar; no afirmar cumplimiento solo por escoger colores.

Tipografía de sistema con fallback legible, escala coherente, espaciado en múltiplos de 8 px, bordes sutiles, radio discreto y acciones primarias limitadas por pantalla. Importes alineados a la derecha, números tabulares, encabezados visibles y columnas de identidad fijas cuando el componente lo permita. Formularios en dos columnas en escritorio, una en pantallas estrechas.

Usar componentes públicos de Streamlit y tema como base. Encapsular CSS y selectores específicos que puedan cambiar con versiones. No construir lógica sensible dentro de HTML ni insertar nombres de archivos/personas como HTML sin escapar. El diseño final se verificará en navegador con captura de login, dashboard, tabla ancha, importación y cierre; no se entrega aún una maqueta como si fuera la aplicación.
