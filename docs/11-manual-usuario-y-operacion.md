# Manual de Usuario y Operación Técnica — Sistema de Planillas CAFAE UGEL Chepén

Este manual documenta el uso operativo del sistema web para la gestión integral de planillas de incentivo único CAFAE para las Instituciones Educativas y la Sede de la UGEL Chepén.

---

## 1. Acceso y Roles de Seguridad

El sistema cuenta con tres perfiles de usuario basados en el principio de mínimo privilegio:

1. **ADMINISTRADOR**:
   - Acceso total al sistema.
   - Creación y administración de cuentas de usuario.
   - Modificación de catálogos institucionales e identidad.
   - Cierre formal definitivo de planillas mensuales.
   - Reapertura justificada de planillas cerradas.
   - Consulta y exportación de auditoría forense inmutable.

2. **PLANILLAS (Operador)**:
   - Registro y modificación de la ficha de personal en el maestro.
   - Creación de planillas mensuales (desde maestro o copia del mes anterior).
   - Edición mensual de importes, descuentos y días de licencia sin goce.
   - Importación masiva de descuentos por Excel.
   - Emisión y descarga de documentos de trabajo (PDF, Excel, boletas y remuneraciones).

3. **CONSULTA (Auditor / Lector)**:
   - Visualización y consulta de planillas, personal, catálogos y reportes.
   - Descarga de documentos oficiales ya emitidos.
   - Sin permisos de escritura, importación ni mutación de datos.

### Políticas de Sesión y Contraseñas
- **Duración de sesión**: Máximo 8 horas de sesión continua o 30 minutos de inactividad.
- **Contraseñas temporales**: Al crear o restablecer una cuenta, el usuario debe cambiar obligatoriamente su contraseña temporal en su primer inicio de sesión.
- **Protección de fuerza bruta**: Bloqueo progresivo tras intentos fallidos consecutivos por cuenta y por origen.

---

## 2. Panel Principal (Dashboard)

Al iniciar sesión, la pantalla de inicio presenta dos tarjetas centrales:
- **Planillas de Instituciones Educativas (II.EE.)**: Muestra el último periodo registrado, versión activa, cantidad de trabajadores y masa salarial neta.
- **Planillas de Sede UGEL**: Muestra el último periodo registrado de la sede central y su estado actual.
- **Indicadores rápidos**: Total de trabajadores activos en el maestro, instituciones educativas registradas y alertas de líquido neto negativo que requieren corrección antes del cierre.

---

## 3. Maestro de Personal (Trabajadores)

Ubicado en el menú **Personal**:
- **Separación de Ámbitos**:
  - Personal adscrito a **Instituciones Educativas (II.EE.)**: Requiere selección obligatoria de la I.E. de adscripción y nivel educativo.
  - Personal adscrito a **Sede UGEL Chepén**: Requiere asignación del Área de Sede correspondiente.
- **Campos Laborales Fieles**:
  - DNI (8 dígitos exactos, preservando ceros a la izquierda como texto).
  - Apellidos y Nombres completos.
  - Cargo, Categoría remunerativa, Situación laboral y Subtipo.
  - Régimen laboral / Ley (ej. D.L. 276, Ley 29944) y Régimen pensionario.
  - Jornada laboral (ej. 40 Horas) y Fecha de nacimiento.
  - Modalidad de Pago: Cuenta Multired (Banco de la Nación) o Cheque con numeración.
  - Remuneración Base / Importe: Administrado estrictamente con precisión `Decimal(12,2)`.
  - Leyenda permanente para boletas de pago.
- **Activación / Desactivación**:
  - Desactivar a un trabajador impide que sea cargado en nuevas planillas mensuales, conservando íntegro su historial en periodos cerrados anteriores.

---

## 4. Gestión Mensual de Planillas

Ubicado en el menú **Planillas**:

### A. Creación de la Planilla Mensual
1. Seleccionar el Año, Mes (1 al 12) y Tipo (`IIEE` o `SEDE`).
2. Elegir la modalidad de generación:
   - **Desde Maestro de Personal**: Carga a todos los trabajadores activos en el maestro con sus importes vigentes y los 8 conceptos de descuento inicializados en S/ 0.00.
   - **Copia del Mes Anterior**: Copia íntegramente la versión del mes inmediatamente anterior (conservando importes, cuentas y descuentos recurrentes). Los días de licencia se reinician en cero.

### B. Edición de Descuentos y Licencias
1. En el **Editor de Planilla**, visualizar la nómina completa.
2. Cada fila contiene los 8 conceptos de negocio aprobados:
   - `Pichincha`
   - `Caja Sullana`
   - `Sub-CAFAE`
   - `Convenio BRENTA`
   - `SITRASE`
   - `SITASE / FENTASE`
   - `Licencia sin goce de haber` (se calcula automáticamente ingresando los días de 0 a 30).
   - `Otros descuentos`
3. Los totales de descuentos y líquido neto se recalculan automáticamente sin redondeos intermedios del jornal: `Monto Licencia = (Importe / 30) × Días`.
4. Botón **Limpiar Todos los Descuentos**: Permite reiniciar en cero los descuentos y licencias de toda la nómina manteniendo intactos los importes base (con confirmación obligatoria).

### C. Cierre Definitivo (Solo Administrador)
1. Verificar que no existan alertas de líquido neto negativo.
2. Seleccionar las firmas de conformidad requeridas:
   - **II.EE.**: Requiere exactamente 4 firmas (Dirección UGEL, Gestión Institucional, Gestión Administrativa, Finanzas).
   - **Sede UGEL**: Requiere exactamente 3 firmas (Dirección UGEL, Gestión Institucional, Finanzas).
3. Presionar **Cerrar Planilla Definitivamente**. La versión pasa a estado `CERRADA`, inmutable contra cualquier edición posterior.

### D. Reapertura Justificada (Solo Administrador)
Si se requiere una corrección posterior sobre una planilla cerrada:
1. Ingresar el **Motivo Justificado de Reapertura** (obligatorio y auditado).
2. El sistema crea una nueva versión (`v2`, `v3`...) en estado `BORRADOR` con copia íntegra, manteniendo la versión anterior cerrada e intacta en el historial.

---

## 5. Importación Masiva de Descuentos por Excel

Ubicado en el menú **Importar Descuentos**:
1. Seleccionar la planilla abierta de destino y el concepto de descuento (ej. Pichincha, Sub-CAFAE, etc.).
2. Subir el archivo Excel (.xlsx o .xls).
3. El sistema extrae y clasifica cada fila por **DNI exacto**:
   - `IDENTIFICADO`: DNI coincide y trabajador encontrado en la planilla.
   - `REVISAR`: DNI coincide pero el nombre del documento difiere del registrado.
   - `DNI_DUPLICADO`: El mismo DNI figura más de una vez en el archivo (requiere resolución explícita; inicialmente no se selecciona).
   - `NO_ENCONTRADO`: El DNI no pertenece a la planilla actual.
   - `MONTO_INVALIDO`: Monto no numérico o negativo.
4. Seleccionar la modalidad de aplicación:
   - **ACTUALIZAR**: Aplica los montos solo a los DNI seleccionados y conserva los montos preexistentes de los demás.
   - **REEMPLAZAR**: Pone en cero ese concepto específico en toda la planilla y aplica los seleccionados.
5. Confirmar y aplicar en una sola transacción segura con verificación de concurrencia.

---

## 6. Documentos Oficiales Emitidos

Ubicado en el menú **Documentos**:

1. **Planilla Oficial en PDF**:
   - Formato institucional A4 horizontal (Landscape).
   - Encabezados repetidos en cada página.
   - Cuadro consolidado con los 8 conceptos de descuento y bloque final de firmas indivisible en la última página.
2. **Planilla Oficial en Excel (.xlsx)**:
   - Réplica fiel de la plantilla institucional aprobada, con celdas numéricas formateadas (`#,##0.00`) y cuentas/DNI como texto.
3. **Hoja de Trabajo de Remuneraciones**:
   - Agrupada por Metas Presupuestarias, Programas y Partidas, sumando exclusivamente el **importe bruto** (regla confirmada 4.1 y 4.2).
4. **Boletas de Pago CAFAE**:
   - Descarga individual por trabajador.
   - Descarga del **Cuadernillo Mensual Completo en PDF** con todas las boletas del periodo, con logo oficial, único concepto de ingreso y los 8 descuentos.
5. **Archivo Bancario (TXT)**:
   - Módulo bloqueado con explicación transparente conforme a la decisión 4.5 hasta contar con la especificación oficial validada del Banco de la Nación.

---

## 7. Catálogos y Configuración

Ubicado en el menú **Catálogos** (Modificación reservada al Administrador):
- **Instituciones Educativas**: Código modular, nombre, nivel educativo, distrito y meta opcional.
- **Áreas de Sede**: Nombre de dependencias internas y meta presupuestaria.
- **Niveles y Metas**: Gestión de clasificadores presupuestarios y regla de resolución Nivel ↔ Meta.
- **Estructura Presupuestaria**: Programas en jerarquía multinivel con prevención de ciclos y partidas presupuestarias.
- **Parámetros de Personal**: Cargos, categorías remunerativas, situaciones y subtipos de trabajador.
- **Firmas Institucionales**: Catálogo de autoridades y cargos para documentos oficiales.
- **Identidad Institucional**: Nombre institucional, nombre del sistema y zona horaria (`America/Lima`).

---

## 8. Auditoría Administrativa

Ubicado en el menú **Auditoría**:
- Registro cronológico inmutable de todas las operaciones de acceso, creación, edición, importación, cierre y reapertura.
- Detalle comparativo de campos modificados (`valor_anterior` frente a `valor_nuevo`), sin exponer contraseñas ni secretos.
