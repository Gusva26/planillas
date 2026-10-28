# ADR-006 · Los documentos oficiales exigen permiso específico y versión cerrada

## Estado

**Aceptado** — 28/10/2026, por decisión del responsable del sistema.
**Implementado el 28/10/2026**: los ocho endpoints de `/api/documentos` declaran
su permiso, y `CONSULTA` ya no puede emitir documentos.

## Contexto

El diseño define los permisos `generar_documentos` y `txt_bancario`, y la
decisión D.5 establece que el archivo bancario TXT permanece **bloqueado** hasta
contar con especificación oficial.

Sin embargo, antes del hotfix:

- `cafae/api/routes_documentos.py` resolvía el contexto con
  `data_transaction(token, 'consultar')`.
- Todos los endpoints de descarga (PDF, Excel, boletas, remuneraciones y **TXT**)
  dependían solo de `get_current_user`.
- `txt_bancario` y `generar_documentos` no se usaban en ningún punto del backend.
- `cafae/documentos/banco_txt.py` ya generaba líneas de 28 caracteres y estaba
  expuesto en `GET /api/documentos/banco-txt/{version_id}`.

Resultado: un usuario `CONSULTA` podía descargar planillas, boletas y el TXT, y
el sistema entregaba un artefacto que la decisión D.5 declara no certificado.

## Decisión

1. **Todos los documentos oficiales exigen `generar_documentos`**
   (ADMINISTRADOR / PLANILLAS): planilla PDF, planilla Excel, remuneraciones
   Excel, boleta individual, boleta por DNI y cuadernillo de boletas.
2. **`CONSULTA` conserva la lectura** de planillas y detalle, pero **no emite
   documentos**. La UI de React muestra un aviso en lugar de las acciones.
3. `GET /api/documentos/banco-txt/{version_id}` y `banco-txt-resumen/{version_id}`
   exigen `txt_bancario` **y** que la versión esté `CERRADA`; mientras D.5 siga
   vigente responden `403` con motivo explícito aunque el permiso exista
   (`CAFAE_TXT_BANCARIO=1` es la única habilitación, para entornos de prueba).
4. La autorización se aplica en el endpoint **y** en la transacción del servicio
   (`data_transaction`); la UI no es frontera de seguridad.
5. La matriz de permisos se cubre con tests negativos por rol y con un test
   estructural que verifica el permiso declarado en cada ruta.

## Alternativas consideradas

- **Dejar `consultar` para todo**: simple, pero contradice la matriz de roles y
  permite descargar datos sensibles a un perfil de solo lectura. Descartada.
- **Bloquear solo en la UI**: insuficiente; una llamada directa a la API lo
  evade, y el propio diseño lo prohíbe. Descartada.
- **Eliminar el endpoint TXT hasta tener la especificación**: máxima seguridad,
  pero pierde el trabajo ya hecho; se prefiere mantenerlo tras permiso, estado y
  bandera explícita.

## Consecuencias

- **Positivas**: coherencia entre diseño y código; los permisos declarados pasan
  a tener efecto; se cierra la exposición de datos personales a `CONSULTA`.
- **Negativas**: `CONSULTA` pierde una capacidad que antes tenía; si el área
  usuaria necesita imprimir, hay que asignarle un rol con `generar_documentos`
  (no ampliar el permiso de lectura).
- **Operación**: el TXT sigue inutilizable en producción por D.5; habilitarlo
  exige revisar este ADR y el README, no solo la variable de entorno.
- **Verificación**: `python scripts/test_seguridad.py` cubre el esquema de
  credenciales, la matriz de roles, el bloqueo D.5, la exigencia de versión
  cerrada y la declaración de permisos en cada ruta.

## Trade-offs

Se prioriza **coherencia con las decisiones de negocio y mínimo privilegio**
sobre la comodidad de un único permiso de lectura. Si D.5 se revisa, este ADR
debe actualizarse junto con el README, no por separado.
