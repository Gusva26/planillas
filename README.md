# Sistema de Gestión de Planillas CAFAE · UGEL Chepén

**Sistema web integral de planillas CAFAE implementado y probado.**
Desarrollado en Python (FastAPI) + React + PostgreSQL 17 en contenedores Docker, con arquitectura modular por capas, seguridad estricta, fidelidad a las plantillas institucionales y cobertura total de las etapas administrativas.

---

## 1. Acceso y Puesta en Marcha

La aplicación web está disponible localmente en:
👉 **[http://localhost:8501](http://localhost:8501)**

### Primer Administrador del Sistema
Antes de inicializar el usuario (o tras recrear la base de datos), asegúrese de tener configuradas las credenciales del servicio y migraciones ejecutando:

```powershell
python scripts/setup_app.py
```

Luego, inicialice el primer administrador institucional ejecutando en PowerShell:

```powershell
docker compose run --build --rm app python -m cafae.bootstrap
```
*El comando solicitará nombre de usuario, nombre completo y contraseña mediante ingreso oculto por consola.*

### Gestión de Contenedores
```powershell
# Iniciar servicios
docker compose up -d --wait

# Ver estado de salud de contenedores
docker compose ps

# Detener conservando datos
docker compose stop
```

---

## 2. Módulos y Funcionalidades del Sistema

1. **Dashboard Institucional**:
   - Tarjetas de resumen para Planillas de Instituciones Educativas (II.EE.) y Sede UGEL Chepén.
   - Indicadores rápidos de personal activo, masa salarial y alertas de netos negativos.
2. **Maestro de Personal (Trabajadores)**:
   - Separación estricta entre II.EE. (adscripción obligatoria a I.E.) y Sede UGEL (adscripción a Área).
   - DNI de 8 dígitos preservado como texto con ceros iniciales, cuentas Multired, importes en `Decimal(12,2)` y fechas laborales.
3. **Gestión Mensual de Planillas**:
   - Creación mensual desde maestro (solo activos, descuentos en cero) o por copia íntegra del mes anterior.
   - Editor masivo con recálculo automático de los 8 conceptos autorizados y licencias sin goce `(Importe/30) × Días`.
   - Limpieza de descuentos por lote y control de concurrencia optimista (`revision_edicion`).
   - Cierre formal definitivo con firmas institucionales (4 en II.EE. / 3 en Sede).
   - Reapertura versionada con motivo justificado obligatorio, manteniendo el cierre anterior inmutable.
4. **Importación Masiva de Descuentos**:
   - Extracción desde Excel con clasificación automática por DNI (`IDENTIFICADO`, `REVISAR`, `DNI_DUPLICADO`, `NO_ENCONTRADO`, `MONTO_INVALIDO`).
   - Modalidades `ACTUALIZAR` (solo seleccionados) y `REEMPLAZAR` (limpia el concepto y aplica seleccionados) con idempotencia.
5. **Emisión de Documentos Oficiales**:
   - **Planilla Oficial en PDF**: A4 horizontal, encabezados repetidos por página, cuadro consolidado de los 8 descuentos y firmas en la última página.
   - **Planilla Oficial en Excel (.xlsx)**: Con formato idéntico a las referencias originales y celdas numéricas formateadas (`#,##0.00`).
   - **Hoja de Trabajo de Remuneraciones**: Agrupada por metas presupuestarias sumando exclusivamente el importe bruto.
   - **Boletas de Pago CAFAE**: Descarga individual y Cuadernillo Mensual Completo en PDF con logo oficial y único concepto de ingreso.
   - **Archivo Bancario (TXT)**: Módulo bloqueado de forma transparente y justificada conforme a la Decisión Confirmada 4.5 hasta disponer de la especificación técnica oficial o muestra real aceptada por el Banco de la Nación.
6. **Catálogos y Parámetros**:
   - Instituciones, Áreas de Sede, Niveles y Metas, Jerarquía de Programas Presupuestarios, Partidas, Cargos, Categorías, Situaciones, Subtipos y Firmas.
7. **Reportes Administrativos**:
   - Los 9 reportes obligatorios sin mezclar periodos ni versiones históricas.
8. **Auditoría Forense Inmutable**:
   - Registro append-only con comparador de cambios antes/después por campo.

---

## 3. Decisiones de Negocio Confirmadas

- **D.1 Un único ingreso**: Total Descuentos = suma de los 8 conceptos; Neto = Importe - Total Descuentos. Retirados sumandos adicionales o reintegros como conceptos de pago.
- **D.2 Importe de Sede**: Corresponde a "REMUN. TOTAL" (columna I de la referencia).
- **D.3 Firmas**: Exactamente 4 firmas en II.EE. y 3 en Sede, con bloque de firmas indivisible al final.
- **D.4 Ocho descuentos completos**: Pichincha, Caja Sullana, Sub-CAFAE, Convenio BRENTA, SITRASE, SITASE/FENTASE, Licencia sin goce y Otros descuentos.
- **D.5 TXT bancario**: Bloqueo preventivo documentado sin generar salidas provisionales no certificadas. El endpoint exige permiso `txt_bancario`, responde `403` salvo `CAFAE_TXT_BANCARIO=1` y solo opera sobre versiones cerradas ([ADR-006](docs/adr/ADR-006-documentos-permiso-y-version-cerrada.md)).
- **Documentos oficiales**: PDF, Excel, remuneraciones, boletas y cuadernillo exigen permiso `generar_documentos` (ADMINISTRADOR / PLANILLAS). El rol `CONSULTA` puede leer planillas pero no emitir documentos.

---

## 4. Documentación del Proyecto

1. [Manual de Usuario y Operación Técnica](docs/11-manual-usuario-y-operacion.md)
2. [Matriz de Trazabilidad Integral (56 Secciones y 5 Decisiones)](docs/12-matriz-trazabilidad-56-secciones.md)
3. [Decisiones Confirmadas y Correspondencias](docs/08-decisiones-confirmadas.md)
4. [Revisión de los Cuatro Excel de Referencia](docs/07-analisis-plantillas.md)
5. [Arquitectura, Seguridad y Procesos](docs/02-arquitectura.md)
6. [Modelo Entidad-Relación y Diccionario de Datos](docs/03-modelo-datos.md)
7. [Navegación, Permisos y Experiencia de Uso](docs/04-navegacion.md)
8. [Plan de Pruebas y Criterios de Aceptación](docs/05-plan-y-pruebas.md)
9. [Base de Datos Implementada](docs/09-base-datos-implementada.md)
10. [Acceso, Usuarios y Roles](docs/10-acceso-y-usuarios.md)
11. [Decisiones de Arquitectura (ADR)](docs/adr/README.md)
