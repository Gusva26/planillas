# Acceso, usuarios y roles

Fecha de verificación: **24/09/2026**. Etapa 2 implementada y probada en desarrollo local.

## Entrar por primera vez

La aplicación está disponible en **http://localhost:8501** mientras Docker Desktop y los contenedores estén activos. El formulario usa la identidad institucional extraída de la boleta original, sin modificarla.

No hay usuario ni contraseña predeterminados. Para crear tu administrador, abre PowerShell y ejecuta:

```powershell
Set-Location 'C:\Users\Gusva\Desktop\proyecto_planillas'
docker compose run --build --rm app python -m cafae.bootstrap
```

El comando solicita usuario, nombre completo y contraseña dos veces. La contraseña se ingresa de forma oculta, debe tener entre 12 y 128 caracteres y puede ser una frase larga. No la escribas en comandos ni la envíes por el chat. El nombre de usuario admite de 3 a 80 letras sin tildes, números, punto, guion y guion bajo.

Este comando funciona únicamente mientras no existan usuarios. Dos ejecuciones simultáneas no pueden crear dos administradores iniciales. Si el ingreso se cancela o las contraseñas no coinciden, no se crea la cuenta. La base `cafae_dev` se dejó sin cuentas; las usadas durante las pruebas fueron sintéticas y se eliminaron con sus bases temporales.

Después de crear la cuenta, inicia sesión y entra en **Usuarios** para registrar las demás. Las cuentas nuevas usan una contraseña temporal y deben cambiarla antes de acceder a otras operaciones.

## Funciones disponibles

- Login con error genérico ante cuenta inexistente, inactiva o contraseña incorrecta; cierre de sesión.
- Inicio autenticado que identifica los módulos todavía pendientes, sin mostrar métricas ficticias.
- Mi cuenta: cambio de contraseña con verificación de la actual y cierre de todas las sesiones anteriores.
- Usuarios, solo para administrador: listado sin secretos, creación, edición de nombre/rol/estado, desactivación y restablecimiento de acceso con cambio obligatorio.
- Confirmación de cambios de cuenta y restablecimientos; control de revisión para rechazar guardados obsoletos.
- Protección contra desactivación o cambio de rol del último administrador activo, también bajo concurrencia.

El cambio de rol, contraseña o desactivación revoca las sesiones del usuario afectado. Reactivar una cuenta no revive sus sesiones anteriores. No se eliminan usuarios que forman parte del historial.

## Seguridad implementada

Los servicios están en [cafae/auth.py](../cafae/auth.py). Cada operación recibe un token y comprueba en PostgreSQL su vigencia, el estado del usuario y su rol actual. Ninguna operación administrativa acepta como autoridad un rol enviado por la interfaz. `data_transaction` ofrece a los futuros servicios de negocio una transacción con permiso comprobado y rol SQL restringido.

Las contraseñas usan Argon2id, con sal distinta y parámetros explícitos: memoria 65536 KiB, tres iteraciones y paralelismo cuatro. La biblioteca permite verificar y detectar hashes que requieren actualización; se usa su [API oficial de PasswordHasher](https://argon2-cffi.readthedocs.io/en/stable/api.html). Se rechazan contraseñas demasiado largas antes del cálculo.

Los tokens se generan con aleatoriedad criptográfica y solo su SHA-256 se guarda en `sesiones`. El token real permanece en el estado de sesión del servidor; no se agrega a URLs ni se persiste como contraseña en el navegador.

Las sesiones tienen un máximo de **8 horas** y **30 minutos de inactividad**. Se valida cada operación; una pantalla inactiva puede seguir visible, pero no permite una nueva operación con una sesión vencida. Son valores técnicos iniciales, ajustables en desarrollo según la política institucional.

Se limita a cinco fallos por cuenta y treinta por origen en una ventana de quince minutos. En este despliegue, accesible solo por loopback, todas las conexiones usan el origen fijo `local`: es un límite compartido adicional. No se confía en cabeceras ni en la IP no validada para aplicar controles de seguridad. Los intentos y rechazos relevantes quedan auditados sin contraseñas, tokens ni sus hashes.

La migración [007_autenticacion.sql](../database/migrations/007_autenticacion.sql) añade la tabla de intentos, revisión de cuentas, protección del último administrador y revocación automática de sesiones por cambios de credenciales/rol/estado. La base contiene **35 tablas en `cafae` y siete migraciones aplicadas**.

La aplicación usa `cafae_service`, un usuario técnico distinto del migrador, sin superusuario, creación de bases/roles ni herencia automática de privilegios. El servicio cambia a roles permitidos dentro de transacciones. Sus credenciales están únicamente en `.env`, excluido del contexto de construcción y de Git; no se incluyen en la imagen. La conexión de servicio es un componente de confianza del servidor y nunca se entrega al navegador.

Las consultas usan parámetros y transacciones de Psycopg; su [documentación oficial](https://www.psycopg.org/psycopg3/docs/basic/transactions.html) describe el commit/rollback por contexto. La API FastAPI mantiene activadas las protecciones de cabeceras y control de orígenes. El contenedor de la aplicación se ejecuta con usuario Linux sin privilegios de root.

## Volver a iniciar el sistema

Desde la carpeta del proyecto, con Docker Desktop abierto:

```powershell
docker compose up -d --wait
docker compose ps
```

Para detener ambos contenedores conservando los datos:

```powershell
docker compose stop
```

Para reconstruir después de editar código:

```powershell
docker compose build app
docker compose up -d --wait app
```

En una instalación nueva, primero genera la configuración e inicia PostgreSQL con `scripts/db.ps1 init` y `scripts/db.ps1 up`. Después ejecuta:

```powershell
$taskPython = 'C:\Users\Gusva\.cache\codex-runtimes\codex-primary-runtime\dependencies\python\python.exe'
$env:PYTHONIOENCODING = 'utf-8'
& $taskPython scripts/setup_app.py
docker compose build app
docker compose up -d --wait app
```

`setup_app.py` aplica las migraciones y configura una contraseña técnica aleatoria distinta a la de migración, sin mostrarla. Se puede reejecutar sin crear cuentas de negocio. En otro equipo debe ajustarse la ruta de Python. `requirements.txt` identifica dependencias directas y `requirements.lock` fija las versiones directas y transitivas probadas de la imagen.

## Evidencia

| Comprobación | Resultado |
|---|---|
| Pruebas de autenticación, autorización y cuentas | **23 satisfactorias** |
| Bootstrap concurrente en una base vacía | Un administrador creado; segundo intento rechazado |
| Dos cambios de usuario con igual revisión | Uno guardado; otro rechazado |
| Dos administradores intentan desactivarse simultáneamente | Se conserva al menos uno activo |
| Regresión de base de datos tras migración 007 | 23 pruebas, cuatro escenarios concurrentes y restauración satisfactoria |
| Login en navegador real | Revisado visualmente con logo, etiquetas, contraseña oculta y botón de acceso |
| Salud de PostgreSQL y aplicación; endpoint `/api/health` | `healthy` y respuesta `ok` |

Los dos escenarios concurrentes de cuentas están incluidos en las pruebas de acceso. El bootstrap concurrente se ejecuta antes de la suite.

Para repetir:

```powershell
& $taskPython scripts/test_auth.py
& $taskPython tests/database/test_integrity.py
```

Ambos ejecutores crean bases `cafae_test_*` y las eliminan al terminar. Los resultados locales están en `test-results/auth.json` y `test-results/database.json`. Desde el retiro de Streamlit (ADR-005), las pruebas de acceso cubren solo servicio y base; la interfaz React se valida con el build de TypeScript y el flujo integral contra `/api`.

## Alcance pendiente

La siguiente etapa es **catálogos**. Los permisos centrales ya están definidos para los módulos futuros; esto no implica que estén implementados personal, planillas, importaciones, cierres desde UI, documentos, reportes ni visor de auditoría.

El acceso actual está limitado a `127.0.0.1`; no se publicó el sistema en Internet ni en la red institucional. Antes de un despliegue compartido deberán definirse TLS/proxy, origen confiable para límites, respaldos operativos, gestión de secretos, retención/limpieza de intentos y sesiones, recuperación administrativa y aceptación institucional. El TXT continúa pendiente de referencia bancaria validada.
