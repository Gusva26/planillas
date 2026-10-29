# Matriz de Trazabilidad Integral — Sistema de Planillas CAFAE UGEL Chepén

Esta matriz certifica la cobertura de las 56 secciones de los requisitos originales y las 5 decisiones de negocio confirmadas frente al código ejecutable y las pruebas del sistema.

---

## 1. Cobertura de las 5 Decisiones de Negocio Confirmadas

| Decisión | Regla Confirmada | Implementación en Código | Evidencia / Pruebas | Estado |
|---|---|---|---|---|
| **D.1** | **Un único ingreso**: Retirar "Importe adicional", "Reintegro" y "Otros ingresos". `TOTAL DESCUENTOS = suma de los 8 conceptos`; `NETO = IMPORTE - TOTAL DESCUENTOS`. | `cafae/calculos.py`<br/>`cafae/documentos/excel_planillas.py`<br/>`cafae/documentos/boletas.py` | `CAL-01`, `CAL-05`<br/>`tests/planillas/test_planillas.py` | **Completado y Verificado** |
| **D.2** | **Importe de Sede**: Corresponde a "REMUN. TOTAL" (columna I de la referencia). No sumar RO ni Reintegro. | `cafae/documentos/excel_planillas.py`<br/>`cafae/documentos/remuneraciones.py` | `test_flujo_completo_sistema`<br/>`tests/integracion/test_flujo_integral.py` | **Completado y Verificado** |
| **D.3** | **Firmas institucionales**: Exactamente 4 firmas en II.EE. (Dirección, DGI, DGA, Finanzas) y 3 firmas en Sede (Dirección, DGI, Finanzas). Guardar nombre y cargo en el histórico. Firmas solo al final. | `database/migrations/001_base.sql`<br/>`cafae/planillas.py`<br/>`cafae/documentos/pdf_planillas.py` | `CIE-01`<br/>`tests/planillas/test_planillas.py`<br/>`tests/database/test_integrity.py` | **Completado y Verificado** |
| **D.4** | **Ocho descuentos completos**: Pichincha, Caja Sullana, Sub-CAFAE, Convenio BRENTA, SITRASE, SITASE/FENTASE, Licencia sin goce (calculado por días) y Otros descuentos. Ambos formatos muestran los 8 conceptos. | `cafae/calculos.py`<br/>`cafae/documentos/excel_planillas.py`<br/>`cafae/documentos/pdf_planillas.py` | `CAL-01`, `CAL-02`<br/>`tests/planillas/test_planillas.py` | **Completado y Verificado** |
| **D.5** | **TXT bancario**: Módulo bloqueado con explicación transparente hasta contar con la especificación técnica oficial o muestra real aceptada por el Banco de la Nación. No generar archivos no certificados. | `cafae/api/routes_documentos.py`<br/>`tests/database/test_integrity.py` | `test_documentos_no_generables_en_abierta_y_txt_pendiente` | **Completado y Bloqueado Documentado** |

---

## 2. Matriz de Requisitos Originales (Secciones 1 a 56)

| Rango de Secciones | Requisito / Alcance | Componente Implementado | Pruebas Asociadas | Estado |
|---|---|---|---|---|
| **§01 - §05** | Arquitectura general, entorno local, PostgreSQL 17, separación por capas, seguridad y sesiones. | `cafae/db.py`<br/>`cafae/security.py`<br/>`compose.yaml` | `tests/database/test_integrity.py`<br/>`scripts/test_auth.py` | **Completado** |
| **§06 - §10** | Autenticación, contraseñas seguras con Argon2id, roles (ADMINISTRADOR, PLANILLAS, CONSULTA), bloqueo de fuerza bruta y cambio obligatorio de contraseña temporal. | `cafae/auth.py`<br/>`cafae/bootstrap.py`<br/>`frontend/src/views/LoginView.tsx` | `test_auth.py` (27 pruebas)<br/>`test_limite_intentos_por_cuenta` | **Completado** |
| **§11 - §15** | Modelo de datos relacional, inmutabilidad de cierres, prevención de mutaciones en histórico, dominios NUMERIC(12,2) y Decimal sin float. | `database/migrations/001_base.sql`<br/>`database/migrations/003_integridad.sql`<br/>`cafae/calculos.py` | `test_dinero_invalido`<br/>`test_cierre_inmutable_incluso_sql_directo` | **Completado** |
| **§16 - §20** | Catálogos institucionales: Instituciones, áreas de Sede, niveles educativos, metas presupuestarias, relación nivel-meta, programas jerárquicos y partidas presupuestarias. | `cafae/catalogos.py`<br/>`frontend/src/views/CatalogosView.tsx` | `test_catalogos.py` (10 pruebas)<br/>`test_programas_jerarquia_y_ciclos` | **Completado** |
| **§21 - §25** | Parámetros de personal: Cargos, categorías, situaciones laborales, subtipos de trabajador y firmas maestras. | `cafae/catalogos.py`<br/>`frontend/src/views/CatalogosView.tsx` | `test_tablas_adicionales_personal`<br/>`test_firmas_maestras` | **Completado** |
| **§26 - §30** | Maestro de Personal: Separación II.EE. vs Sede, validación de DNI de 8 dígitos, adscripción obligatoria, cuentas Multired, importes y fechas laborales. | `cafae/trabajadores.py`<br/>`frontend/src/views/TrabajadoresView.tsx` | `test_trabajadores.py` (6 suites)<br/>`test_separacion_iiee_sede` | **Completado** |
| **§31 - §35** | Boletas de pago CAFAE: Datos del servidor, logo oficial, único concepto de ingreso, los 8 descuentos y líquido neto en números. | `cafae/documentos/boletas.py`<br/>`frontend/src/views/DocumentosView.tsx` | `test_flujo_completo_sistema`<br/>`tests/integracion/test_flujo_integral.py` | **Completado** |
| **§36 - §40** | Creación mensual de planillas (desde maestro con descuentos en cero o copia mes anterior), editor por lote, control de concurrencia y limpieza de descuentos. | `cafae/planillas.py`<br/>`frontend/src/views/PlanillasView.tsx` | `PER-01` a `PER-07`<br/>`CLR-01`, `test_edicion_lote_y_limpieza` | **Completado** |
| **§41 - §45** | Motor de cálculos monetarios Decimal ROUND_HALF_UP, cálculo de licencia sin goce `(importe/30)*días` y consistencia de totales. | `cafae/calculos.py` | `CAL-01` a `CAL-07`<br/>`tests/planillas/test_planillas.py` | **Completado** |
| **§46 - §50** | Importación masiva de descuentos desde Excel, matching por DNI, clasificación de estados, resolución de duplicados y modalidades REEMPLAZAR/ACTUALIZAR. | `cafae/extractores.py`<br/>`cafae/importaciones.py`<br/>`frontend/src/views/ImportacionesView.tsx` | `IMP-01` a `IMP-13`<br/>`tests/importaciones/test_importaciones.py` | **Completado** |
| **§51 - §53** | Cierre formal de planillas (exclusivo Administrador con firmas institucionales) y reapertura versionada con motivo justificado dejando el cierre anterior intacto. | `cafae/planillas.py`<br/>`database/migrations/005_cierre_transaccional.sql` | `CIE-01`, `HIS-01` a `HIS-05`<br/>`test_cierre_y_reapertura` | **Completado** |
| **§54 - §55** | Emisión de Planillas Oficiales en PDF (A4 horizontal con firmas al final) y Excel (.xlsx) fiel a los formatos administrativos. Hoja de Remuneraciones por metas presupuestarias. | `cafae/documentos/excel_planillas.py`<br/>`cafae/documentos/pdf_planillas.py`<br/>`cafae/documentos/remuneraciones.py` | `DOC-01`, `DOC-03`, `REM-01`<br/>`tests/integracion/test_flujo_integral.py` | **Completado** |
| **§56** | Auditoría administrativa append-only con comparativa antes/después, Dashboard institucional con dos tarjetas y 9 reportes obligatorios. | `cafae/auditoria.py`<br/>`cafae/reportes.py`<br/>`frontend/src/views/AuditoriaView.tsx`<br/>`frontend/src/views/ReportesView.tsx`<br/>`frontend/src/App.tsx` | `tests/integracion/test_flujo_integral.py`<br/>`tests/database/test_integrity.py` | **Completado** |
