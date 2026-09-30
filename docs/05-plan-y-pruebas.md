# Plan de desarrollo, trazabilidad y aceptación

## Regla de avance

Se conserva el orden de las 18 etapas solicitado. Cada etapa debe entregar funcionalidad, pruebas y evidencia antes de avanzar. **Las etapas 1 y 2 están implementadas y probadas en desarrollo local**, con evidencia en el [informe de base de datos](09-base-datos-implementada.md) y el [informe de acceso](10-acceso-y-usuarios.md); no equivale a aceptación administrativa ni a habilitación para producción. El usuario debe crear su administrador inicial mediante el comando local. Las etapas 3–18 siguen pendientes. Las plantillas ya se recibieron y se revisaron. El usuario resolvió ingresos, equivalencia de Sede, firmas y descuentos en las [decisiones confirmadas](08-decisiones-confirmadas.md). H07 mantiene pendiente el contrato bancario.

## Etapas y puertas de aceptación

| Etapa | Entrega | Evidencia necesaria antes de avanzar |
|---|---|---|
| 1. Arquitectura y base de datos | Inventario de originales, decisiones resueltas, ER, migraciones, restricciones, protección de cierres y auditoría base | Crear base vacía PostgreSQL, ejecutar migraciones, probar FKs/índices/constraints/inmutabilidad y rollback; revisar D01 |
| 2. Login, usuarios y roles | Login, bootstrap sin credenciales fijas, sesiones, tres roles | Hash y verificación; expiración/revocación; cuenta inactiva; todos los permisos probados también desde servicio |
| 3. Catálogos | Instituciones, áreas, niveles, metas, cargos, categorías, situaciones, subtipos y firmas | Edición/desactivación sin romper FKs; resolución de meta configurable |
| 4. Trabajadores | Maestro II.EE./Sede con búsquedas y ficha completa | DNI único con ceros, adscripción, desactivación, historial y campos completos |
| 5. Creación y edición | Crear desde maestro o copiar mes previo, edición por lote | Periodo único bajo concurrencia, descuentos cero desde maestro, copia fiel, conflictos de guardado |
| 6. Cálculos | Motor Decimal único, licencia y totales | Casos exactos, extremos y redondeos contrastados con Excel; no float |
| 7. Importaciones | PDF digital/escaneado, DOCX/tablas, Excel, revisión y modalidades | Casos ambiguos, duplicados, no encontrados, OCR por página, rollback e idempotencia |
| 8. Cierre e historial | Validaciones, firmas por tipo (4 II.EE. / 3 Sede), cierre, reapertura versionada | Snapshot estable, protección DB, carreras edición/cierre, historia reproducible |
| 9. PDF II.EE. | Réplica A4 horizontal del original | Comparación visual y numérica, encabezados repetidos, cierre solo última página |
| 10. PDF Sede | Réplica con áreas y distribución propia | Misma evidencia, grupos/subtotales y no reutilización simplificada de II.EE. |
| 11. Excel | Libro con impresión y formato oficial | Apertura y renderizado, campos, celdas, bordes, dimensiones, totales y cierre |
| 12. Remuneraciones | Agrupación por meta con importe bruto | Conciliación exacta con planilla y fidelidad de plantilla |
| 13. Boletas | Individual y un PDF mensual | Datos completos, orden, conteo, saltos y valores históricos |
| 14. TXT | Réplica del contrato extraído | Comparación byte por byte con archivo de referencia, longitudes, relleno, netos y rechazo de errores |
| 15. Auditoría | Visor, filtros y revisión de cobertura | Todos los eventos ya registrados desde sus etapas; cambios trazables e historial inalterable |
| 16. Dashboard y reportes | Métricas, alertas y nueve reportes | Conciliación y filtros, periodos comparables, sin doble conteo por versiones |
| 17. Pruebas integrales | Escenarios de punta a punta, carga y recuperación | Ejecución sobre PostgreSQL real, restore aislado, seguridad y aceptación administrativa |
| 18. UX/UI final | Ajustes visuales y accesibilidad | Validación en escritorio y ancho reducido, formularios, keyboard, estados y documentos finales |

La etapa 5 valida persistencia y edición; la certificación monetaria la completa la etapa 6 antes de usar importaciones o cerrar. La estructura visual se usa desde login; etapa 18 la perfecciona, no posterga la usabilidad hasta el final.

## Matriz de pruebas obligatorias

| ID | Caso | Resultado verificable |
|---|---|---|
| CAL-01 | Importe 1350.00; Pichincha 735.45; SITASE/FENTASE 10.00; resto 0 | Descuentos **745.45**, neto **604.55**, igualdad Decimal exacta |
| CAL-02 | Importe 1350.00; licencia 3 días | Licencia **135.00**, neto **1215.00** sin otros descuentos |
| CAL-03 | Licencia 0 y 30 días | Cero y el importe completo; no se edita monto de licencia |
| CAL-04 | Días −1, 31, fracción; importe/desc. negativo, NaN, infinito | Rechazo amigable sin persistencia parcial |
| CAL-05 | Descuentos mayores al importe | Neto negativo visible con alerta; TXT bloqueado y cierre según D05 |
| CAL-06 | Fracciones periódicas de importe/30 y casos de medio centavo | Igualdad con Excel validado; redondear en el punto establecido D04 |
| CAL-07 | Neto 0 | Planilla lo distingue; validación TXT lo marca como error |
| PER-01 | Crear dos veces mismo año/mes/tipo, incluso concurrentemente | Una planilla lógica; segunda operación informa existencia |
| PER-02 | Crear II.EE. y Sede en el mismo periodo | Permitido y aislado |
| PER-03 | Crear desde maestro con personal activo/inactivo | Solo activos, snapshot completo y todos los descuentos/días en cero |
| PER-04 | Copiar septiembre a octubre con cambios posteriores en maestro | Copia versión elegida de septiembre, incluyendo descuentos y datos originales |
| PER-05 | Copiar diciembre a enero; falta mes anterior | Cruce de año correcto; faltante comunicado sin elegir otro mes |
| PER-06 | Edición masiva con una fila inválida | Rollback completo, filas erróneas identificadas |
| PER-07 | Dos editores guardan desde igual revisión | Primer lote se guarda; segundo recibe conflicto sin sobrescritura |
| IMP-01 | PDF digital con múltiples columnas de montos | No asignar columna ambigua; previsualización antes de aplicar |
| IMP-02 | DOCX con tablas y filas repetidas | Extraer todas las apariciones con origen; no sumar automáticamente |
| IMP-03 | PDF escaneado y PDF mixto | OCR solo donde falte texto; DNI incierto queda para revisar |
| IMP-04 | Mismo DNI dos o más veces | Todas las filas marcadas; cero seleccionadas por defecto; usuario elige una |
| IMP-05 | DNI no incluido en planilla, nombre muy parecido | NO_ENCONTRADO; jamás match automático por nombre |
| IMP-06 | Nombre diferente con DNI existente | REVISAR con nombre original y snapshot visibles |
| IMP-07 | Reemplazar un tipo | Cero para ese tipo en todas las filas y luego aplicar seleccionados; otros tipos intactos |
| IMP-08 | Actualizar solo encontrados | No incluidos conservan monto; una sola transacción |
| IMP-09 | Doble clic/reintento en aplicar | Una aplicación por idempotencia, un registro de efecto |
| IMP-10 | Monto inválido, formato ambiguo, DNI con cero inicial | Revisión sin interpretar arbitrariamente; DNI conserva cero |
| IMP-11 | Error durante aplicación o planilla modificada desde preview | Sin cambios parciales; exigir previsualización vigente |
| IMP-12 | Cero seleccionados o reemplazo con rechazados | No limpiar por accidente; confirmar exclusiones antes de aplicar |
| IMP-13 | Importación intenta apuntar a detalle de otro periodo | Rechazo por FK compuesta y servicio |
| CLR-01 | Limpiar todos los descuentos | Confirmación, siete tipos a cero, días y licencia cero, importes intactos y auditoría |
| CIE-01 | Cierre II.EE. con tres firmas, Sede con dos o posición repetida | No cierra; II.EE. requiere 1–4 y Sede 1–3. La cuarta firma de Sede se rechaza. Copiar nombre/cargo histórico |
| CIE-02 | DNI/cuenta/meta/categoría/institución faltantes y monto sospechoso | Validación explícita por persona; política de errores/advertencias trazable |
| CIE-03 | Edición/importación simultánea con cierre | Un orden serial válido; nunca cierre con totales de una revisión distinta |
| HIS-01 | Cambiar trabajador, institución, meta y firma tras cierre | Cierre y documentos emitidos conservan todos los valores anteriores |
| HIS-02 | SQL directo intenta modificar/eliminar/agregar hijos de cierre | Usuario técnico/disparador rechaza, incluidos cambios de version_id |
| HIS-03 | Reapertura por operador o consulta | Rechazo aunque intente invocar servicio directamente |
| HIS-04 | Reapertura administrativa confirmada con motivo | Nueva versión abierta, anterior intacta, auditoría y numeración correcta |
| HIS-05 | Dos versiones cerradas y una corrección abierta | Reporte corriente no duplica personas/importes; historial muestra versiones |
| DOC-01 | PDF con 1 fila, página exacta, una fila adicional y varias páginas | Encabezados, ocho descuentos en detalle/cierre y firmas solo al final: cuatro II.EE., tres Sede |
| DOC-02 | Nombres largos y muchos grupos de Sede | Sin recortes, superposición ni subtotales separados incorrectamente |
| DOC-03 | Exportar Excel | Formatos, impresión, sumas y cuentas como texto; no inyección de fórmulas |
| DOC-04 | Formatos II.EE., Sede y boleta después de retirar conceptos adicionales | Un único ingreso; sin Importe adicional, Reintegro u Otros ingresos como campos de pago |
| DAT-01 | Muestra sintética de Sede con importes diferentes en H, I y J | Importe proviene exclusivamente de I (REMUN. TOTAL); no sumar RO ni Reintegro |
| DAT-02 | Original con ingreso adicional distinto de cero | Detener esa fila y avisar; no descartar ni incorporar silenciosamente el concepto |
| REM-01 | Dos personas meta 11: importes 1350 y 1500, netos distintos | Meta 11 = **2850.00**; no suma netos; total metas = total importe |
| BOL-01 | Boleta individual y lote desde cierre | Todos los campos de §35; líquido coincide con neto; orden y cantidad exactos |
| BOL-02 | Maestro cambia después del cierre | Boleta nueva del mismo cierre usa snapshot, no maestro actualizado |
| TXT-01 | Comparación con salida original validada | Bytes, ancho, orden, relleno, decimales, codificación y fin de línea iguales |
| TXT-02 | Multired vacío/inválido, neto cero/negativo | Contadores y detalle visibles; archivo definitivo no emitido |
| TXT-03 | Plantilla o regla bancaria ausente/no validada | Generación bloqueada con explicación, sin formato alternativo inventado |
| SEG-01 | Roles, usuario inactivo, sesión expirada/revocada | Operación y descarga rechazadas desde UI y servicios |
| SEG-02 | Cambio de rol/contraseña y cierre de sesión | Sesiones revocadas; no seguir operando con permiso anterior |
| SEG-03 | Entradas SQL, HTML y nombres de archivo hostiles | Consultas parametrizadas, HTML escapado y almacenamiento con clave segura |
| AUD-01 | Eventos de §40 y rechazo de transacción | Usuario/fecha/entidad/cambios/motivo disponibles; falla no borra registro de intento |
| OPS-01 | Backup + restauración en base y directorio aislados | Personas, versiones, cierres, importaciones y hashes de documentos concilian |

## Reportes exigidos

Resumen mensual; importe por institución; importe por meta; descuentos por entidad; neto por institución; trabajadores por nivel; trabajadores por situación; licencias sin goce; comparación mensual. Todos respetan año/mes, institución, nivel y tipo cuando aplican. Los reportes de descuentos incluyen licencia como octavo componente. Cada total debe conciliar contra la misma versión elegida.

## Trazabilidad de las 56 secciones

| Requisitos | Diseño / módulo | Etapas |
|---|---|---|
| 1–2 Tecnología y proceso | Arquitectura y contratos | 1, 17 |
| 3–4 Login y roles | Seguridad, usuarios, matriz | 2 |
| 5–6 Principal y UX | Navegación y diseño visual | 16, 18 |
| 7–8 Maestro y gestión | Trabajadores y snapshots | 4 |
| 9–11 Instituciones, áreas, metas | Catálogos y relaciones | 3 |
| 12 Importe | Maestro y detalle histórico | 4–6 |
| 13–14 Creación y columnas | Planillas/versiones/detalle | 5 |
| 15–16 Cálculos y licencia | Dinero Decimal, licencia derivada | 6 |
| 17 Edición | Guardado masivo y concurrencia | 5–6 |
| 18–24 Importación, match, duplicados, preview, modos, auditoría | Adaptadores y lotes normalizados | 7 |
| 25–28 Validación, estados, historial, snapshot | Cierre, observaciones, versiones | 8 |
| 29–31 PDF II.EE./Sede y sección final | Generadores específicos y paginación | 9–10 |
| 32 Firmas y precisión posterior del usuario | Catálogo y copia por tipo: cuatro II.EE. / tres Sede | 3, 8 |
| 33 Excel | Generador con plantilla | 11 |
| 34 Remuneraciones | Agregación de importe por meta | 12 |
| 35–36 Boletas individual y mensual | Datos históricos y PDF conjunto | 13 |
| 37–38 TXT y validación | Contrato bancario extraído del original | 14 |
| 39 Reportes | Agregados de versiones correctas | 16 |
| 40 Auditoría | Eventos desde cada servicio y visor | 1–15 |
| 41–43 Base, integridad y dinero | SQL, restricciones y transacciones | 1, 6, 17 |
| 44–45 Seguridad y backup | Sesiones, permisos, operación y restore | 2, 17 |
| 46 Experiencia | Flujo administrativo y contexto | 5–8, 18 |
| 47 Dashboard | Indicadores y alertas | 16 |
| 48 Búsquedas | Filtros de módulos e índices | 3–5, 8, 16 |
| 49 Confirmaciones | UI y guardas de servicio | 4–8 |
| 50 Errores | Mensajes, logs y correlación | Transversal |
| 51–52 Diseño y documentos | QA visual y comparación de originales | 9–13, 18 |
| 53 Ejemplo completo | Escenario de aceptación extremo a extremo | 17 |
| 54 Orden de desarrollo | Puertas de aceptación de este plan | 1–18 |
| 55 Pruebas | Matriz anterior | Todas |
| 56 Resultado y prioridades | Condiciones de salida | 17–18 |

## Condiciones para uso real

No declarar «listo para producción» hasta recibir y contrastar originales, resolver decisiones que alteran comportamiento, pasar pruebas sobre PostgreSQL real, comparar documentos impresos, validar TXT contra referencia aceptada, probar restauración y completar revisión administrativa con datos controlados. La revisión estática de documentos o SQL no sustituye ninguna de esas verificaciones.
