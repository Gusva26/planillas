# Revisión de los cuatro Excel de referencia

**Estado posterior:** el usuario resolvió ingresos, equivalencia de Sede, firmas y descuentos. Consultar [decisiones confirmadas](08-decisiones-confirmadas.md), que prevalecen sobre las preguntas H01–H06 y los pendientes históricos de este informe. H07 continúa sujeto a validación bancaria. Se conserva la evidencia original de la revisión.

Revisión de solo lectura para el Sistema de Gestión de Planillas CAFAE de UGEL Chepén. Los originales se conservaron sin modificaciones. Se inspeccionaron hojas visibles y ocultas, fórmulas, valores almacenados, relaciones, celdas combinadas, imágenes y configuración de impresión. Las notas dentro de los libros se trataron como contenido de referencia, no como instrucciones para ejecutar acciones.

**Conclusión:** los cuatro archivos permiten definir los formatos y ampliar el modelo de datos. Sin embargo, contienen datos incompletos, diferencias con los requisitos y un generador TXT con pasos manuales y resultados inválidos. No deben usarse como motor de cálculo validado ni como base mensual cerrada.

## 1. Inventario y procedencia

Todos los archivos están en `C:/Users/Gusva/Downloads/`.

| Clave usada en este informe | Archivo | Hojas |
|---|---|---|
| SEDE | PLANILLA CAFAE - SEDE UGELCH_SETIEMBRE_BD SISTEMAS.xlsx | 2: una visible y una oculta |
| IIEE | PLANILLA CAFAE - II.EE.s DSETIEMBRE 2026_SGD BD _SISTEMAS.xlsx | 5: cuatro visibles y una oculta |
| REM | HOJA DE TRABAJO DE REMUNERACIONES - PLANILLA  CAFAE- 2026.xlsx | 7: una visible y seis ocultas |
| BOL | GENERAR BOLETA CAFE.xlsx | 1 visible |

Se identificaron 15 hojas en total, de las cuales 8 están ocultas. Ninguno de los cuatro paquetes contiene `vbaProject`; tampoco se encontraron vínculos externos de libro. Esto no acredita que un proceso manual externo no se use actualmente.

| Libro | Hoja | Función y periodo observado |
|---|---|---|
| SEDE | PLANILLA SEDE SET_26 | Plantilla principal, septiembre 2026 |
| SEDE | ADICIONAL AGOSTO — oculta | Formato anterior cuyo título dice agosto 2016; no debe cargarse como septiembre 2026 |
| IIEE | PLANILLA SET_26 | Plantilla principal, septiembre 2026 |
| IIEE | PLANILLA — oculta | Título de mayo 2026 |
| IIEE | DX PARA TXT | Tres columnas y una fila de ejemplo, sin enlace por fórmula a planilla |
| IIEE | GENERADOR TXT | Concatenaciones y pasos manuales, sin enlace por fórmula a DX PARA TXT |
| IIEE | hoja de trabajo | Resumen de remuneraciones por programa/meta con montos manuales |
| REM | CAFAE - JULIO | Única visible; título general sin mes en celdas A4:A6; nombre de pestaña indica julio |
| REM | CAFAE - MAYO — oculta | Otra versión de formato y cálculos |
| REM | Remuneraciones — oculta | Referencia de ACTIVOS MARZO 2020 de la U.E. 314 La Esperanza; distinta a CAFAE Chepén |
| REM | CARGA SOCIAL - MAYO — oculta | Cuota patronal, contiene errores de referencia |
| REM | Hoja1, Hoja2, Hoja3 — ocultas | Cuadros auxiliares de escolaridad/remuneraciones; no importar por defecto |
| BOL | ENE26 | Una boleta de enero 2026, independiente de los otros libros |

Los nombres de archivo no prueban un periodo común. No se conciliaron como si fueran cuatro documentos del mismo cierre.

## 2. Diferencias que requieren definición antes de implementar la parte afectada

| ID | Evidencia exacta | Diferencia con la especificación | Tratamiento de esta revisión |
|---|---|---|---|
| H01 | IIEE, PLANILLA SET_26!Q10, Q157, P158 | Existe «IMPORTE ADICIONAL». P158 suma P157 + Q157, aunque el requisito excluye ese concepto | No añadirlo al motor ni eliminarlo del formato sin resolver la contradicción. Definir si la columna se retira, cambia o queda sin uso |
| H02 | SEDE, PLANILLA SEDE SET_26!H5:J5 | Tres conceptos: REINTEGRO, REMUN. TOTAL y RO; el nuevo sistema define un solo importe | Falta precisar cuál representa «Importe» y qué hacer con los otros encabezados. Las filas vacías no permiten deducirlo por fórmula |
| H03 | BOL, ENE26!A25, J25, C35 | «Otros Ingresos + (*)» entra en T-INGRESOS; el requisito dice líquido = importe − descuentos, sin importe adicional | Mantener detenida esa transformación hasta definir cómo conservar el formato con la regla de ingreso único |
| H04 | SEDE, PLANILLA SEDE SET_26!B53, E53, N53 | Hay tres cargos de firma visibles; se exigen cuatro en ambos tipos de planilla | Falta confirmar la cuarta posición/cargo y la redistribución. II.EE. sí muestra cuatro cargos |
| H05 | IIEE, PLANILLA SET_26!C172:D179 | El cuadro final no incluye «Otros descuentos», aunque la tabla sí tiene Y11 | No copiar esta omisión al sistema sin señalarla: el requisito exige los ocho conceptos en el cierre |
| H06 | SEDE, PLANILLA SEDE SET_26!K6:P6 y A42:C48 | Detalle con cinco tipos de descuento; BRENTA aparece solo en el cierre, como 0 fijo. No hay columnas de Caja Sullana ni Otros | Definir distribución de las columnas requeridas sin simplificar ni inventar equivalencias |
| H07 | IIEE, GENERADOR TXT!R1, R3:R4, T3:V4 | Anuncia 28 dígitos, pero hay punto decimal, notación científica y pasos sin automatizar | No implementar ni emitir un TXT bancario tomando este resultado como contrato validado |

Se cumple la instrucción de detener la parte donde Excel y requisitos difieren: no se cambió la lógica de ingresos, la definición de Sede, las firmas ni el TXT. El análisis de las otras partes continuó.

## 3. Planilla de Instituciones Educativas

### Estructura y columnas

Hoja principal `PLANILLA SET_26`, encabezados en filas 10–11. Se reconocen 139 filas de personas con DNI distinto entre sí; seis filas de subtotales se excluyen del conteo. Los 139 DNI se encuentran almacenados con ocho dígitos en esta hoja. Solo 12 filas tienen una cuenta numérica o de dígitos utilizable; solo cinco contienen importe numérico. Esto es una revisión de los datos disponibles, no una declaración de que el personal restante deba cobrar cero.

| Columnas | Contenido | Destino conceptual |
|---|---|---|
| A | N° | Orden histórico, distinto del ID interno |
| B–E | DNI, nivel, apellidos, nombres | Maestro y snapshot |
| F–G | Código modular, institución | Catálogo + etiquetas históricas |
| H–J | Subtipo, cargo, situación | Catálogos + snapshot |
| K–N | Nacimiento, ley, categoría, jornada | Maestro y snapshot |
| O | Multired | Texto en base de datos, no número para operar |
| P | Importe | NUMERIC/Decimal |
| Q | Importe adicional | Conflicto H01 |
| R–Y | Pichincha, Caja Sullana, Sub-CAFAE, BRENTA, SITRASE, SITASE, licencia, otros | Siete descuentos editables + licencia calculada |
| Z | Total descuentos | Suma de R:Y |
| AA | Neto | Importe menos descuentos en las dos fórmulas conservadas |

Grupos identificados: meta 11, filas 12–23; meta 12, 25–95; meta 44, 97–99; meta 30, 101–103; meta 14, 105–149; meta 42, 151–155. Sus subtotales están en 24, 96, 100, 104, 150 y 156. Este mapeo es evidencia de esta plantilla, no una regla rígida para todos los años.

### Cálculos comprobados

- `X12 = P12/30*27`: 1370 / 30 × 27 = **1233.00**. Confirma la fórmula de licencia, pero los días están incrustados en la fórmula; no existe una columna de días independiente.
- `Z12 = SUM(R12:Y12)` y `AA12 = P12-Z12`: descuentos **1243.00** y neto **127.00**.
- `Z13 = SUM(R13:Y13)` y `AA13 = P13-Z13`: descuentos **365.00** y neto **1035.00**.
- No hay `ROUND` en el caso de licencia observado. Este ejemplo exacto no permite decidir qué hacer con fracciones de centavo en otros importes/días. El formato visible de dos decimales no define el redondeo del cálculo.

### Totales incompletos

`AA14`, `AA15` y `AA16` están vacías pese a existir importes en P14:P16. En AA14 corresponderían **1030.00** aplicando la regla del requisito a importe 1500 y descuentos 470; no se escribió ese resultado en el libro.

Los cinco importes presentes suman **7370.00** y los ocho conceptos de descuento presentes suman **2078.00**. La resta de esos datos es **5292.00**. Sin embargo, `AA24` suma solo los dos netos existentes y almacena **1162.00**. La diferencia de **4130.00** procede de los tres netos ausentes, no de una regla salarial inferida.

`Z157` y `AA157` están vacías. El cierre `D172:D178` lee columnas R157:X157 que también están vacías y muestra cero; `D179` almacena **0.00**, aunque sí hay descuentos en el detalle. Además, D179 solo suma siete líneas y deja fuera Otros.

`Q157` contiene `SUM(Q156,Q150,Q104,Q100,Q96,AE5:AG11,Q24)`: agrega un rango auxiliar fuera de la tabla visible, además de los subtotales. Es otra razón para no copiar esa fórmula sin definir H01.

### Presentación

Encabezados azules, banda verde de descuentos, colores por entidad, subtotales por meta, cuadro final de descuentos y cuatro firmas. Las filas 7–8 están ocultas. Encabezados de impresión repetidos: 1–11; orientación horizontal, escala 45%, salto manual tras fila 147 y salto de columna 28. La hoja principal no tiene un área de impresión ni tamaño de papel explícitos guardados; la hoja oculta sí especifica A4.

La especificación nueva exige A4 horizontal. Será necesario configurar y comprobar ese papel explícitamente y paginar reservando el cierre, sin heredar ciegamente dimensiones residuales hasta CK188 ni el panel inmovilizado A156.

## 4. Planilla de Sede

`PLANILLA SEDE SET_26` conserva **24 filas de puestos** con cargo, categoría y área. No contiene nombres de trabajadores, DNI, cuentas válidas ni importes numéricos en esas filas. Los números de la columna A incluyen repeticiones y valores también en dos filas de subtotal; no se deben usar como identificadores ni para contar personal.

Agrupaciones visibles: Dirección, Gestión Pedagógica, Gestión Institucional, Gestión Administrativa y Control Institucional. Meta 33 en E4. No se debe importar la hoja oculta ADICIONAL AGOSTO para rellenar automáticamente estos vacíos: corresponde a un título de 2016.

Solo quedan 15 fórmulas en la hoja principal, centradas en agregados y cuadro final. No hay fórmulas de neto por persona conservadas. `I36` y `J36` están vacías; `Q36` suma subtotales vacíos y resulta 0. `H35 = H14` y `H36 = H35` no describen una suma general de todos los reintegros.

El cierre muestra Lic. S/G, Sub-CAFAE, SITASE, SITRASE, Pichincha y BRENTA. BRENTA en C47 es 0 fijo y carece de columna de detalle. El pie conserva tres cargos de firma: Director de UGEL, Dirección de Gestión Institucional y Finanzas. No se detectó texto de una cuarta firma en objetos de dibujo.

Impresión guardada: A4 horizontal, área A1:R56, filas repetidas 1–6 y escala 52%. Estilo Calibri, tabla con bordes, grupos separados por bandas azules. Debe conservarse la organización por áreas, resolviendo primero H02, H04 y H06.

La nota de A38 enumera una escala salarial y una referencia normativa. Se registra como texto del original; esta revisión no verifica su vigencia ni la adopta como regla legal actual.

## 5. Hoja de remuneraciones

La presentación principal de `CAFAE - JULIO` tiene encabezados institucionales, columnas Programa / Meta / 21.11.21 / Total ejecutado, bandas de grupo y total final. Metas observadas: 33, 11, 12, 14, 44, 30, 42. Los montos de entrada son constantes; no están enlazados a las planillas ni calculados por una búsqueda/suma por meta.

**Inconsistencias internas observadas:**

- `C12 = 12000` es un valor manual para Educación Básica. Sus hijos `C13:C15` suman **95010.00** (10 + 55000 + 40000). Diferencia: **83010.00**.
- `C19 = 5050` para Educación Especial; C20 está vacía y C21 vale 3050. Diferencia respecto de los hijos presentes: **2000.00**.
- `C23 = C11+C12+C16+C19+C22` almacena **53850.00**. Suma los grupos principales tal como están, incluidos los dos importes anteriores. No corresponde reemplazarlo sin revisar esos datos.
- La hoja `hoja de trabajo` dentro de IIEE sí tiene `C7 = SUM(C8:C10)` y total C18 de **136860.00**, pero mantiene Educación Especial en 5050 frente a 3050 en sus hijos presentes. Son dos versiones distintas, no un vínculo actualizado entre archivos.

En `CARGA SOCIAL - MAYO`, oculta, hay **49 celdas con error almacenado #REF!**, originadas en referencias rotas como Q8 hacia `'CAFAE - MAYO'!#REF!`. No se encontraron fórmulas de la hoja visible `CAFAE - JULIO` que dependan de esa hoja: los errores no se atribuyen al cuadro visible por simple pertenencia al mismo archivo.

La hoja oculta `Remuneraciones` incluye una unidad ejecutora distinta y un título de marzo 2020. No es plantilla de CAFAE Chepén ni fuente de datos del periodo solicitado sin una definición adicional.

Impresión del cuadro visible: A4 horizontal, escala 48%, área A1:AK24, pese a que el cuadro principal ocupa A:D. Hay filas y columnas ocultas y contenido auxiliar fuera del cuadro. Tres hojas declaran dimensiones hasta la fila **1048576**: son rangos residuales, no un millón de trabajadores. La inspección evitó interpretar filas vacías/formateadas como datos.

Para el sistema se mantiene el requisito de **sumar IMPORTE por META**, con jerarquía de programas y subtotales configurable. No se debe sumar a la vez un grupo y sus hijos para el total general. Los ejemplos de estos libros no permiten certificar conciliación contra septiembre, porque los periodos y datos no coinciden.

## 6. Boleta

`ENE26` contiene una boleta de enero 2026 con datos ingresados manualmente y tres fórmulas:

| Celda | Fórmula | Valor almacenado |
|---|---|---|
| C35 | SUM(J24:J25) | 1500.00 |
| H35 | SUM(J26:J33) | 260.00 |
| J35 | SUM(C35-H35) | 1240.00 |

La aritmética de esa boleta concilia. No existe una base de personal ni fórmulas de búsqueda por DNI o generación masiva dentro del archivo. «GENERAR BOLETA» es el nombre del archivo, no evidencia de que haya una macro generadora.

Además de los campos ya contemplados, aparecen:

- RUC e identificación institucional.
- Tiempo de servicio (AA-MM-DD), A17.
- Fecha de registro con ingreso/término, A18:G18; no se debe confundir con el timestamp de creación del trabajador en la aplicación.
- Cuenta TeleAhorro **o número de cheque**, A19.
- Leyenda permanente y mensual, A20:A21.
- Régimen pensionario, A22.
- Base/descripción normativa del ingreso, A24.
- Otros ingresos, A25, sujeto al conflicto H03.
- Texto de contacto al pie, A36; debe ser configurable, no incrustado en código ni asumido vigente.

Diseño vertical A4, escala 85%, Calibri, separadores horizontales y descuentos uno por fila. Hay **una imagen institucional JPEG de 468 × 468 píxeles en el encabezado central**, mediante `&C&G`: logo UGEL Chepén/escudo regional. No aparece como imagen ordinaria de celda. Ya existe una referencia visual para el logo, aunque conviene usar el archivo institucional de mejor resolución para impresión definitiva.

La previsualización por rango permite revisar las celdas, pero no reproduce esa imagen de encabezado ni certifica la impresión final de Excel.

## 7. Generación TXT: lógica encontrada y límites

Las hojas están en el libro **IIEE**, no en el libro de boleta.

`DX PARA TXT` contiene DNI, Multired y Neto a pagar en B3:D3 y una sola fila de ejemplo en B5:D5. No tiene fórmulas. `GENERADOR TXT` tampoco referencia DX ni PLANILLA SET_26: la transferencia es manual en el archivo recibido.

En GENERADOR TXT:

| Rango | Evidencia |
|---|---|
| B3:B139 | Código textual «341» repetido |
| C | Cuenta, numérica en los dos ejemplos llenos |
| D3 | B3 & C3 |
| E:N y P:Q | Ceros distribuidos manualmente; posiciones vacías varían según fila |
| O | Importe a depositar |
| R3 | Concatenación de D3, E3:N3, O3 y P3:Q3 |
| T2 | Nota «se delimita para eliminar punto» |
| V2 | Nota de concatenar para crear el TXT final |
| V3 | Única fórmula final encontrada: CONCATENATE(T3,U3) |

La fila 3 utiliza importe 1800 y R3 conserva una cadena de **28 caracteres numéricos**. Al pasar a T3 el valor está almacenado como número de gran magnitud. V3 contiene el resultado almacenado en **notación científica de 17 caracteres**, no una línea de 28 dígitos.

La fila 4 utiliza importe 800.55 y R4 conserva **29 caracteres con punto decimal**. T4 mantiene esa cadena; U4 contiene los centavos por separado y V4 está vacía. No existe una fórmula final general aplicada a todas las filas.

Hay fórmulas intermedias hasta la fila 139 aunque falten cuenta e importe: producen cadenas incompletas de 13/14 caracteres en ejemplos vacíos. No constituyen registros de pago válidos.

Se puede documentar un patrón observado de prefijo/cuenta/importe, pero todavía **no certificar posiciones, relleno o validación bancaria**. Tampoco hay evidencia suficiente sobre cabecera/pie, codificación, terminador de línea y política de importe cero. El XLSX no contiene el TXT final aceptado por el banco.

Para resolver H07 se necesita un TXT de ejemplo aceptado —puede ser anonimizado conservando longitudes y estructura— o la especificación bancaria y la explicación del paso manual T/U/V. No se reconstruyó un formato bancario por suposición.

## 8. Ajustes que debe recibir la arquitectura

Estos son cambios propuestos derivados de las referencias; **no se aplicaron aún al SQL ni a un motor de negocio**.

| Área | Ajuste necesario |
|---|---|
| Identidad institucional | Añadir RUC, identificación de unidad ejecutora, texto de contacto y versiones históricas del encabezado/logo |
| Datos laborales | Ampliar maestro y snapshot con régimen pensionario y datos de ingreso/término; aclarar cálculo o conservación del tiempo de servicio |
| Boletas | Guardar leyenda permanente en maestro y su copia histórica; leyenda mensual por versión/persona; describir fuente de base normativa |
| Medio de pago | Distinguir cuenta de número de cheque si ambos se mantienen; una boleta con cheque no produce automáticamente una línea bancaria |
| Metas y remuneraciones | Catálogo de programas, jerarquía, orden de impresión, asignación presupuestaria 21.11.21 y correspondencias configurables; conservar contexto histórico |
| Ingresos | Resolver H01/H02/H03 antes de añadir, quitar o renombrar conceptos |
| Firma y cierre | Resolver cuarta firma de Sede y asegurar los ocho descuentos en el cierre según la decisión documental |
| Importación inicial | Seleccionar hoja/periodo, excluir subtotales y hojas antiguas, revisar identidades y cuentas; no convertir celdas vacías en un importe autorizado de cero |
| Generadores | Usar plantillas diferentes de II.EE., Sede, boleta y remuneraciones; pruebas de encabezados, márgenes y sección final |
| TXT | Contrato pendiente de validación, importes/identificadores siempre como texto controlado en la salida; no convertir la línea a número |

Las 30 tablas propuestas siguen siendo una base arquitectónica, pero todavía no cubren todos los campos reales de la boleta ni la jerarquía de remuneraciones. Por ello, ejecutar el SQL sin ajustes no completaría la etapa 1.

## 9. Verificaciones realizadas y límites

- Se leyeron los cuatro paquetes y las 15 hojas sin guardar los libros.
- Se compararon fórmulas con valores almacenados y se hicieron comprobaciones independientes con Decimal para las sumas indicadas.
- Se revisaron visualmente vistas de Sede, encabezado y cierre de II.EE., cuadro principal de remuneraciones y boleta. También se inspeccionó la imagen de cabecera de la boleta.
- Las lecturas con `data_only` son resultados almacenados por Excel, no un recálculo nativo actual. El renderizador de vistas puede calcular por su cuenta; las cifras del informe se apoyan en celdas de origen y comprobaciones independientes, no en capturas solamente.
- No se ejecutaron macros, enlaces externos, operaciones bancarias, correcciones de datos ni migraciones.
- No se certificó paginación nativa ni fidelidad final de PDF/impresión. Las vistas por rango no equivalen a imprimir el libro en Excel.
- Los datos personales se omiten del informe; los hallazgos se ubican por hoja y celda.

Hashes SHA-256 de los originales, usados para comprobar conservación:

| Libro | SHA-256 |
|---|---|
| SEDE | 7c40479350b0480ae7df786eba2049546d06d16b013abee8311e9e8647bbbeb4 |
| IIEE | 09b58b41f8b1c1829df030cfd0a53d530e85851c78f77f17d9ee030d0d51d71b |
| REM | f08082ca45840f5285311eec2e346014051e8c23215a372f75f839b3e203e0a0 |
| BOL | 28e80fb2199ba0322153d03772e966ea44873d711686037b7ae7d5e22ec7ddc7 |

## 10. Siguiente decisión

Resolver primero la política de ingreso único frente a los tres formatos, la cuarta firma y columnas de Sede, y el contrato TXT. Con esas definiciones se puede ajustar el esquema, incorporar los campos faltantes y convertir el DDL propuesto en migraciones probadas. El análisis concluye; no se han dado por aprobadas las diferencias.
