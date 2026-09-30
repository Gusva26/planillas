# Base de datos implementada y verificada

Fecha: **24/09/2026**. Etapa 1 completada técnicamente en desarrollo local; la aplicación de usuario comienza en la etapa 2. No es una habilitación para procesar pagos reales.

**Registro de la etapa 1:** las cantidades y pendientes de este informe corresponden a ese corte. La etapa 2 ya añadió la séptima migración, la tabla de intentos de acceso y la aplicación Streamlit. Consulte el [estado de acceso y usuarios](10-acceso-y-usuarios.md) para la operación vigente.

## Entorno comprobado

- PostgreSQL **17.11**, contenedor `cafae-postgres-dev`, estado `healthy`.
- Base `cafae_dev`, esquema `cafae` con **34 tablas**, más el registro de migraciones en `public`.
- Puerto publicado solamente en `127.0.0.1:55432`; volumen persistente administrado por Compose.
- Seis migraciones aplicadas y reejecutadas sin duplicar estructuras ni datos; sus SHA-256 se comprueban en cada ejecución.
- Tres roles de negocio y siete tipos de descuento editables precargados. Licencia es el octavo descuento y se calcula desde los días.
- **Cero usuarios y cero trabajadores** en la base de desarrollo. Los datos sintéticos usados por las pruebas se crearon en bases separadas y se eliminaron al terminar.

## Implementación

| Migración | Alcance |
|---|---|
| `001_base.sql` | Tablas relacionales, dominios monetarios, restricciones, índices y catálogos mínimos |
| `002_campos_documentales.sql` | Campos laborales, pensión, pago por cuenta/cheque, leyendas, encabezados históricos, programas y partidas |
| `003_integridad.sql` | Cálculo de descuentos y neto, firmas, inmutabilidad de cierres, auditoría, importaciones, documentos y vistas de últimos cierres |
| `004_privilegios.sql` | Roles técnicos consulta/operador/administrador, acceso mínimo y protección de secretos y auditoría |
| `005_cierre_transaccional.sql` | Cierre que bloquea la versión, comprueba revisión y administrador activo, y toma los totales después del bloqueo |
| `006_jerarquias_seguras.sql` | Prevención de ciclos en programas maestros e históricos, incluso ante una transacción con una instantánea antigua |

Los importes son `NUMERIC`, con licencia redondeada a dos decimales y neto igual a importe menos descuentos. Los cambios de descuentos recalculan el detalle. Se rechazan totales de cierre que no concilian. Un borrador puede mostrar neto negativo; el cierre lo rechaza.

Las firmas conservan nombre y cargo en el histórico: cuatro posiciones en II.EE. y tres en Sede. Los cierres y sus hijos rechazan modificaciones, movimientos a otra versión y eliminaciones. Una reapertura conserva el cierre anterior y exige una nueva versión. Las vistas de remuneraciones suman el importe bruto del último cierre por planilla lógica, evitando duplicaciones por versiones.

La auditoría conserva cambios de campos sin almacenar contraseñas ni tokens. Los roles de consulta y operación no pueden alterar auditoría, administrar el esquema ni desactivar disparadores. Los roles técnicos son `NOLOGIN`: **aún no representan una sesión autenticada de la aplicación**. La separación del usuario de migración y la conexión de los servicios se completarán con el login.

Los snapshots y las restricciones de copias/importaciones ya existen; los servicios que crean planillas desde el maestro, copian todas sus filas, extraen archivos y resuelven duplicados se implementarán en las etapas correspondientes. La base bloquea el registro de TXT hasta validar el contrato bancario.

## Evidencia de pruebas

Ejecutor: [test_integrity.py](../tests/database/test_integrity.py). Datos: [fixture.sql](../tests/database/fixture.sql), exclusivamente sintéticos.

| Comprobación | Resultado |
|---|---|
| Integridad, cálculos, firmas, cierres, historia, roles, auditoría, importaciones y documentos | **27 pruebas satisfactorias** |
| Edición anterior al cierre: revisión obsoleta rechazada y cierre posterior conciliado | Satisfactorio |
| Cierre anterior a la edición: escritura tardía rechazada | Satisfactorio |
| Dos guardados con la misma revisión: segundo guardado rechazado | Satisfactorio |
| Jerarquía modificada desde una instantánea antigua: conflicto de serialización | Satisfactorio |
| Migraciones ejecutadas dos veces en base vacía de prueba | Satisfactorio |
| `pg_dump` y `pg_restore` en otra base temporal | Satisfactorio |
| Aplicación y reejecución en `cafae_dev` | Satisfactorio |

La restauración compara el contenido de trabajadores, versiones, detalle, firmas y auditoría. Acredita recuperación de esta base sintética; el respaldo institucional de archivos privados, su retención y recuperación completa siguen pendientes. El resultado automatizado local se guarda en `test-results/database.json` y se reemplaza tras una ejecución satisfactoria.

## Operación local

Desde la raíz del proyecto, con Docker Desktop iniciado y PowerShell 7:

```powershell
.\scripts\db.ps1 init
.\scripts\db.ps1 up
.\scripts\db.ps1 status
```

`init` conserva un `.env` existente y crea una contraseña aleatoria si falta. No muestra la contraseña. `.env` está excluido de Git y no se debe compartir. `up` reutiliza el volumen existente.

En este equipo se comprobó el Python integrado de Codex:

```powershell
$taskPython = 'C:\Users\Gusva\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$env:PYTHONIOENCODING = 'utf-8'
& $taskPython scripts/migrate.py
& $taskPython tests/database/test_integrity.py
```

Estos dos ejecutores solo requieren la biblioteca estándar de Python y Docker. En otro equipo puede usarse un Python 3 compatible instalado, ajustando la ruta. Las pruebas crean y eliminan únicamente sus bases temporales `cafae_test_*`; no cargan el fixture en `cafae_dev`.

Para detener PostgreSQL conservando los datos:

```powershell
.\scripts\db.ps1 stop
```

No modificar migraciones ya aplicadas: cualquier cambio posterior debe incorporarse como una nueva migración. El archivo `schema_propuesto.sql` conserva el diseño inicial y no debe ejecutarse además de las migraciones.

## Siguiente etapa y límites

Continuar con **login, usuarios y roles**: bootstrap seguro del primer administrador, hash de contraseñas, sesiones con vencimiento y revocación, y autorización en servicios además de la interfaz.

Antes de uso real deben completarse los módulos, la comparación de cálculos y redondeos con muestras validadas, la revisión visual de PDF/Excel/boletas, los respaldos operativos y la aceptación administrativa. Las políticas técnicas propuestas sobre cierre de datos incompletos, redondeo y alcance de planilla se conservan documentadas como tales; las cinco decisiones expresas del usuario están en [decisiones confirmadas](08-decisiones-confirmadas.md).

El único insumo externo pendiente identificado para el TXT es un archivo aceptado por el banco o su especificación oficial. Esto no impide continuar con el login y los demás módulos.
