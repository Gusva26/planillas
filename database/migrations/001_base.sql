-- Base relacional. Se ejecuta transaccionalmente mediante scripts/migrate.py.
CREATE SCHEMA cafae;
SET LOCAL search_path TO cafae, public;

-- Los dominios conservan NUMERIC(12,2). El límite superior rechaza también NaN.
CREATE DOMAIN monto AS NUMERIC(12,2)
    CHECK (VALUE BETWEEN 0 AND 9999999999.99);
CREATE DOMAIN saldo AS NUMERIC(12,2)
    CHECK (VALUE BETWEEN -9999999999.99 AND 9999999999.99);

CREATE TABLE roles (
    id SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo VARCHAR(20) NOT NULL UNIQUE
        CHECK (codigo IN ('ADMINISTRADOR', 'PLANILLAS', 'CONSULTA')),
    descripcion TEXT NOT NULL
);

CREATE TABLE usuarios (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    usuario VARCHAR(80) NOT NULL CHECK (btrim(usuario) <> ''),
    nombre_completo VARCHAR(200) NOT NULL,
    password_hash TEXT NOT NULL,
    rol_id SMALLINT NOT NULL REFERENCES roles(id),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    debe_cambiar_password BOOLEAN NOT NULL DEFAULT TRUE,
    password_actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE UNIQUE INDEX ux_usuario_normalizado ON usuarios (lower(btrim(usuario)));

CREATE TABLE sesiones (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    usuario_id BIGINT NOT NULL REFERENCES usuarios(id),
    token_hash VARCHAR(64) NOT NULL UNIQUE CHECK (token_hash ~ '^[0-9a-f]{64}$'),
    creada_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    ultimo_acceso_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    expira_en TIMESTAMPTZ NOT NULL,
    revocada_en TIMESTAMPTZ,
    CHECK (expira_en > creada_en)
);
CREATE INDEX ix_sesion_usuario ON sesiones(usuario_id);

CREATE TABLE metas (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo VARCHAR(30) NOT NULL UNIQUE CHECK (btrim(codigo) <> ''),
    descripcion TEXT NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE niveles (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(100) NOT NULL UNIQUE,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

-- Relación configurable; no se precargan códigos de meta ni equivalencias.
CREATE TABLE nivel_metas (
    nivel_id BIGINT PRIMARY KEY REFERENCES niveles(id),
    meta_id BIGINT NOT NULL REFERENCES metas(id),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_nivel_meta ON nivel_metas(meta_id);

CREATE TABLE instituciones (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo_modular VARCHAR(30) NOT NULL UNIQUE CHECK (btrim(codigo_modular) <> ''),
    nombre VARCHAR(240) NOT NULL,
    nivel_id BIGINT NOT NULL REFERENCES niveles(id),
    distrito VARCHAR(120) NOT NULL,
    meta_id BIGINT REFERENCES metas(id),
    observaciones TEXT,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_institucion_nivel ON instituciones(nivel_id);
CREATE INDEX ix_institucion_meta ON instituciones(meta_id);

CREATE TABLE areas_sede (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL UNIQUE,
    meta_id BIGINT REFERENCES metas(id),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_area_meta ON areas_sede(meta_id);

CREATE TABLE cargos (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(150) NOT NULL UNIQUE,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE categorias (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo VARCHAR(50) NOT NULL UNIQUE,
    descripcion VARCHAR(150) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE situaciones (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL UNIQUE,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE TABLE subtipos_trabajador (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre VARCHAR(120) NOT NULL UNIQUE,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE firmas (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre_completo VARCHAR(200) NOT NULL,
    cargo VARCHAR(200) NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE trabajadores (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    dni VARCHAR(8) NOT NULL UNIQUE CHECK (dni ~ '^[0-9]{8}$'),
    apellidos VARCHAR(150) NOT NULL CHECK (btrim(apellidos) <> ''),
    nombres VARCHAR(150) NOT NULL CHECK (btrim(nombres) <> ''),
    tipo VARCHAR(4) NOT NULL CHECK (tipo IN ('IIEE', 'SEDE')),
    institucion_id BIGINT REFERENCES instituciones(id),
    area_id BIGINT REFERENCES areas_sede(id),
    nivel_id BIGINT REFERENCES niveles(id),
    subtipo_id BIGINT REFERENCES subtipos_trabajador(id),
    cargo_id BIGINT REFERENCES cargos(id),
    situacion_id BIGINT REFERENCES situaciones(id),
    categoria_id BIGINT REFERENCES categorias(id),
    fecha_nacimiento DATE,
    ley VARCHAR(120),
    regimen_laboral VARCHAR(120),
    jornada_laboral VARCHAR(60),
    cuenta_multired VARCHAR(60),
    importe monto NOT NULL DEFAULT 0,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- Permite una ficha incompleta para revisión; exige adscripción al cerrar.
    CHECK ((tipo = 'IIEE' AND area_id IS NULL)
        OR (tipo = 'SEDE' AND institucion_id IS NULL))
);
CREATE INDEX ix_trabajador_tipo_activo ON trabajadores(tipo, activo);
CREATE INDEX ix_trabajador_nombre ON trabajadores(lower(apellidos), lower(nombres));
CREATE INDEX ix_trabajador_institucion ON trabajadores(institucion_id);
CREATE INDEX ix_trabajador_area ON trabajadores(area_id);
CREATE INDEX ix_trabajador_nivel ON trabajadores(nivel_id);
CREATE INDEX ix_trabajador_cargo ON trabajadores(cargo_id);
CREATE INDEX ix_trabajador_categoria ON trabajadores(categoria_id);
CREATE INDEX ix_trabajador_situacion ON trabajadores(situacion_id);
CREATE INDEX ix_trabajador_subtipo ON trabajadores(subtipo_id);

CREATE TABLE periodos (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    anio SMALLINT NOT NULL CHECK (anio BETWEEN 1900 AND 9999),
    mes SMALLINT NOT NULL CHECK (mes BETWEEN 1 AND 12),
    UNIQUE (anio, mes)
);

CREATE TABLE planillas (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    periodo_id BIGINT NOT NULL REFERENCES periodos(id),
    tipo VARCHAR(4) NOT NULL CHECK (tipo IN ('IIEE', 'SEDE')),
    cantidad_firmas SMALLINT GENERATED ALWAYS AS
        (CASE tipo WHEN 'IIEE' THEN 4 ELSE 3 END) STORED,
    creada_por BIGINT NOT NULL REFERENCES usuarios(id),
    creada_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    -- D01: una única planilla lógica para el tipo en ese periodo.
    UNIQUE (periodo_id, tipo)
);

CREATE TABLE planilla_versiones (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    planilla_id BIGINT NOT NULL REFERENCES planillas(id),
    numero INTEGER NOT NULL CHECK (numero > 0),
    estado VARCHAR(15) NOT NULL DEFAULT 'BORRADOR'
        CHECK (estado IN ('BORRADOR', 'EN_REVISION', 'CERRADA')),
    origen VARCHAR(15) NOT NULL CHECK (origen IN ('MAESTRO', 'COPIA', 'REAPERTURA')),
    fuente_version_id BIGINT REFERENCES planilla_versiones(id),
    motivo_reapertura TEXT,
    revision_edicion BIGINT NOT NULL DEFAULT 1 CHECK (revision_edicion > 0),
    version_calculo VARCHAR(80) NOT NULL,
    creada_por BIGINT NOT NULL REFERENCES usuarios(id),
    creada_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    cerrada_por BIGINT REFERENCES usuarios(id),
    cerrada_en TIMESTAMPTZ,
    total_trabajadores INTEGER CHECK (total_trabajadores >= 0),
    total_importe monto,
    total_descuentos monto,
    total_neto saldo,
    UNIQUE (planilla_id, numero),
    CHECK (fuente_version_id IS NULL OR fuente_version_id <> id),
    CHECK ((origen = 'MAESTRO' AND fuente_version_id IS NULL)
        OR (origen IN ('COPIA', 'REAPERTURA') AND fuente_version_id IS NOT NULL)),
    CHECK (origen <> 'REAPERTURA' OR
        (motivo_reapertura IS NOT NULL AND btrim(motivo_reapertura) <> '')),
    CHECK ((estado = 'CERRADA' AND cerrada_por IS NOT NULL AND cerrada_en IS NOT NULL
        AND total_trabajadores IS NOT NULL AND total_importe IS NOT NULL
        AND total_descuentos IS NOT NULL AND total_neto IS NOT NULL
        AND total_neto = total_importe - total_descuentos)
        OR (estado <> 'CERRADA' AND cerrada_por IS NULL AND cerrada_en IS NULL
        AND total_trabajadores IS NULL AND total_importe IS NULL
        AND total_descuentos IS NULL AND total_neto IS NULL))
);
CREATE UNIQUE INDEX ux_version_abierta ON planilla_versiones(planilla_id)
    WHERE estado <> 'CERRADA';
CREATE INDEX ix_version_fuente ON planilla_versiones(fuente_version_id);
CREATE INDEX ix_version_estado ON planilla_versiones(estado, creada_en);

-- Copia histórica explícita, no una consulta a los datos maestros actuales.
CREATE TABLE planilla_detalle (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    version_id BIGINT NOT NULL REFERENCES planilla_versiones(id),
    trabajador_id BIGINT NOT NULL REFERENCES trabajadores(id),
    orden INTEGER NOT NULL CHECK (orden > 0),
    dni VARCHAR(8) NOT NULL CHECK (dni ~ '^[0-9]{8}$'),
    apellidos VARCHAR(150) NOT NULL,
    nombres VARCHAR(150) NOT NULL,
    institucion_id BIGINT REFERENCES instituciones(id),
    institucion_nombre VARCHAR(240),
    codigo_modular VARCHAR(30),
    distrito VARCHAR(120),
    area_id BIGINT REFERENCES areas_sede(id),
    area_nombre VARCHAR(150),
    nivel_id BIGINT REFERENCES niveles(id),
    nivel_nombre VARCHAR(100),
    meta_id BIGINT REFERENCES metas(id),
    meta_codigo VARCHAR(30),
    meta_descripcion TEXT,
    subtipo VARCHAR(120),
    cargo VARCHAR(150),
    situacion VARCHAR(120),
    categoria VARCHAR(50),
    categoria_descripcion VARCHAR(150),
    fecha_nacimiento DATE,
    ley VARCHAR(120),
    regimen_laboral VARCHAR(120),
    jornada_laboral VARCHAR(60),
    cuenta_multired VARCHAR(60),
    importe monto NOT NULL,
    dias_licencia SMALLINT NOT NULL DEFAULT 0 CHECK (dias_licencia BETWEEN 0 AND 30),
    monto_licencia monto NOT NULL DEFAULT 0,
    total_descuentos monto NOT NULL DEFAULT 0,
    neto saldo NOT NULL,
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (version_id, trabajador_id),
    UNIQUE (version_id, dni),
    UNIQUE (version_id, orden),
    UNIQUE (id, version_id),
    CHECK (neto = importe - total_descuentos),
    CHECK (total_descuentos >= monto_licencia)
);
CREATE INDEX ix_detalle_trabajador ON planilla_detalle(trabajador_id);
CREATE INDEX ix_detalle_institucion ON planilla_detalle(institucion_id);
CREATE INDEX ix_detalle_area ON planilla_detalle(area_id);
CREATE INDEX ix_detalle_nivel ON planilla_detalle(nivel_id);
CREATE INDEX ix_detalle_meta ON planilla_detalle(version_id, meta_codigo);
CREATE INDEX ix_detalle_meta_fk ON planilla_detalle(meta_id);

CREATE TABLE tipos_descuento (
    id SMALLINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo VARCHAR(24) NOT NULL UNIQUE CHECK (codigo IN
        ('PICHINCHA', 'CAJA_SULLANA', 'SUB_CAFAE', 'BRENTA', 'SITRASE', 'SITASE_FENTASE', 'OTROS')),
    nombre VARCHAR(100) NOT NULL,
    orden SMALLINT NOT NULL UNIQUE CHECK (orden BETWEEN 1 AND 7)
);

CREATE TABLE planilla_descuentos (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    detalle_id BIGINT NOT NULL REFERENCES planilla_detalle(id),
    tipo_descuento_id SMALLINT NOT NULL REFERENCES tipos_descuento(id),
    monto monto NOT NULL DEFAULT 0,
    actualizado_por BIGINT NOT NULL REFERENCES usuarios(id),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    UNIQUE (detalle_id, tipo_descuento_id)
);
CREATE INDEX ix_descuento_tipo ON planilla_descuentos(tipo_descuento_id);

CREATE TABLE planilla_firmas (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    version_id BIGINT NOT NULL REFERENCES planilla_versiones(id),
    posicion SMALLINT NOT NULL CHECK (posicion BETWEEN 1 AND 4),
    -- Máximo global 4. El trigger de cierre/escritura pendiente debe exigir
    -- posiciones 1..planillas.cantidad_firmas y rechazar la cuarta en Sede.
    firma_id BIGINT NOT NULL REFERENCES firmas(id),
    nombre_completo VARCHAR(200) NOT NULL,
    cargo VARCHAR(200) NOT NULL,
    UNIQUE (version_id, posicion)
);
CREATE INDEX ix_planilla_firma ON planilla_firmas(firma_id);

CREATE TABLE archivos (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    nombre_original VARCHAR(255) NOT NULL,
    clave_almacenamiento TEXT NOT NULL UNIQUE,
    mime_type VARCHAR(150) NOT NULL,
    bytes BIGINT NOT NULL CHECK (bytes >= 0),
    sha256 VARCHAR(64) NOT NULL CHECK (sha256 ~ '^[0-9a-f]{64}$'),
    creado_por BIGINT NOT NULL REFERENCES usuarios(id),
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ix_archivo_hash ON archivos(sha256);

CREATE TABLE importaciones (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    version_id BIGINT NOT NULL REFERENCES planilla_versiones(id),
    tipo_descuento_id SMALLINT NOT NULL REFERENCES tipos_descuento(id),
    archivo_id BIGINT NOT NULL REFERENCES archivos(id),
    estado VARCHAR(16) NOT NULL DEFAULT 'PROCESANDO'
        CHECK (estado IN ('PROCESANDO', 'REVISION', 'APLICADA', 'CANCELADA', 'ERROR')),
    modo VARCHAR(12) CHECK (modo IN ('REEMPLAZAR', 'ACTUALIZAR')),
    revision_previsualizada BIGINT NOT NULL CHECK (revision_previsualizada > 0),
    idempotencia UUID NOT NULL UNIQUE,
    version_extractor VARCHAR(80) NOT NULL,
    uso_ocr BOOLEAN NOT NULL DEFAULT FALSE,
    registros_detectados INTEGER CHECK (registros_detectados >= 0),
    registros_aplicados INTEGER CHECK (registros_aplicados >= 0),
    registros_rechazados INTEGER CHECK (registros_rechazados >= 0),
    filas_duplicadas INTEGER CHECK (filas_duplicadas >= 0),
    total_detectado monto,
    total_aplicado monto,
    creada_por BIGINT NOT NULL REFERENCES usuarios(id),
    creada_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    aplicada_por BIGINT REFERENCES usuarios(id),
    aplicada_en TIMESTAMPTZ,
    UNIQUE (id, version_id),
    CHECK ((estado = 'APLICADA' AND aplicada_por IS NOT NULL
        AND aplicada_en IS NOT NULL AND modo IS NOT NULL
        AND registros_aplicados IS NOT NULL AND registros_aplicados > 0
        AND total_aplicado IS NOT NULL)
        OR (estado <> 'APLICADA' AND aplicada_por IS NULL AND aplicada_en IS NULL))
);
CREATE INDEX ix_importacion_version ON importaciones(version_id, creada_en);
CREATE INDEX ix_importacion_archivo ON importaciones(archivo_id);
CREATE INDEX ix_importacion_tipo ON importaciones(tipo_descuento_id);

CREATE TABLE importacion_detalle (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    importacion_id BIGINT NOT NULL,
    version_id BIGINT NOT NULL,
    fila INTEGER NOT NULL CHECK (fila > 0),
    pagina INTEGER CHECK (pagina > 0),
    hoja VARCHAR(150),
    dni_original TEXT,
    nombre_original TEXT,
    monto_original TEXT,
    texto_original TEXT,
    dni_normalizado VARCHAR(8),
    monto_validado monto,
    detalle_planilla_id BIGINT,
    estado VARCHAR(20) NOT NULL CHECK (estado IN
        ('IDENTIFICADO', 'REVISAR', 'NO_ENCONTRADO', 'DNI_DUPLICADO', 'MONTO_INVALIDO')),
    observacion TEXT,
    seleccionado BOOLEAN NOT NULL DEFAULT FALSE,
    resuelto_por BIGINT REFERENCES usuarios(id),
    resuelto_en TIMESTAMPTZ,
    motivo_resolucion TEXT,
    FOREIGN KEY (importacion_id, version_id) REFERENCES importaciones(id, version_id),
    FOREIGN KEY (detalle_planilla_id, version_id) REFERENCES planilla_detalle(id, version_id),
    UNIQUE (importacion_id, fila),
    CHECK (dni_normalizado IS NULL OR dni_normalizado ~ '^[0-9]{8}$'),
    CHECK (NOT seleccionado OR (dni_normalizado IS NOT NULL
        AND detalle_planilla_id IS NOT NULL AND monto_validado IS NOT NULL
        AND (estado = 'IDENTIFICADO' OR
            (resuelto_por IS NOT NULL AND resuelto_en IS NOT NULL
             AND motivo_resolucion IS NOT NULL AND btrim(motivo_resolucion) <> ''))))
);
CREATE UNIQUE INDEX ux_importacion_dni_seleccionado
    ON importacion_detalle(importacion_id, dni_normalizado) WHERE seleccionado;
CREATE INDEX ix_importacion_match ON importacion_detalle(detalle_planilla_id, version_id);

CREATE TABLE observaciones_planilla (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    version_id BIGINT NOT NULL REFERENCES planilla_versiones(id),
    detalle_id BIGINT,
    revision_validada BIGINT NOT NULL CHECK (revision_validada > 0),
    codigo VARCHAR(80) NOT NULL,
    severidad VARCHAR(12) NOT NULL CHECK (severidad IN ('ERROR', 'ADVERTENCIA', 'INFORMACION')),
    descripcion TEXT NOT NULL,
    creada_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    aceptada_por BIGINT REFERENCES usuarios(id),
    aceptada_en TIMESTAMPTZ,
    motivo_aceptacion TEXT,
    FOREIGN KEY (detalle_id, version_id) REFERENCES planilla_detalle(id, version_id),
    CHECK (aceptada_por IS NULL OR (severidad = 'ADVERTENCIA'
        AND aceptada_en IS NOT NULL AND motivo_aceptacion IS NOT NULL))
);
CREATE INDEX ix_observacion_version ON observaciones_planilla(version_id, revision_validada);
CREATE INDEX ix_observacion_detalle ON observaciones_planilla(detalle_id, version_id);

CREATE TABLE plantillas_documento (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tipo VARCHAR(30) NOT NULL CHECK (tipo IN
        ('PLANILLA_IIEE_PDF', 'PLANILLA_SEDE_PDF', 'PLANILLA_IIEE_EXCEL',
         'PLANILLA_SEDE_EXCEL', 'REMUNERACIONES', 'BOLETA', 'TXT_BANCARIO')),
    version VARCHAR(80) NOT NULL,
    archivo_referencia_id BIGINT NOT NULL REFERENCES archivos(id),
    validada_por BIGINT REFERENCES usuarios(id),
    validada_en TIMESTAMPTZ,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (tipo, version),
    CHECK ((validada_por IS NULL AND validada_en IS NULL)
        OR (validada_por IS NOT NULL AND validada_en IS NOT NULL))
);
CREATE INDEX ix_plantilla_archivo ON plantillas_documento(archivo_referencia_id);

CREATE TABLE documentos_generados (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    version_id BIGINT NOT NULL REFERENCES planilla_versiones(id),
    detalle_id BIGINT,
    plantilla_id BIGINT NOT NULL REFERENCES plantillas_documento(id),
    archivo_id BIGINT NOT NULL UNIQUE REFERENCES archivos(id),
    tipo VARCHAR(25) NOT NULL CHECK (tipo IN
        ('PLANILLA_PDF', 'PLANILLA_EXCEL', 'REMUNERACIONES', 'BOLETA_INDIVIDUAL', 'BOLETAS_TODAS', 'TXT')),
    version_generador VARCHAR(80) NOT NULL,
    registros INTEGER NOT NULL CHECK (registros >= 0),
    total_referencia saldo NOT NULL,
    generado_por BIGINT NOT NULL REFERENCES usuarios(id),
    generado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    FOREIGN KEY (detalle_id, version_id) REFERENCES planilla_detalle(id, version_id),
    CHECK ((tipo = 'BOLETA_INDIVIDUAL' AND detalle_id IS NOT NULL)
        OR (tipo <> 'BOLETA_INDIVIDUAL' AND detalle_id IS NULL))
);
CREATE INDEX ix_documento_version ON documentos_generados(version_id, tipo);
CREATE INDEX ix_documento_plantilla ON documentos_generados(plantilla_id);
CREATE INDEX ix_documento_detalle ON documentos_generados(detalle_id, version_id);

CREATE TABLE configuracion_institucional (
    id SMALLINT PRIMARY KEY CHECK (id = 1),
    nombre_institucion VARCHAR(200) NOT NULL,
    nombre_sistema VARCHAR(200) NOT NULL,
    zona_horaria VARCHAR(80) NOT NULL DEFAULT 'America/Lima',
    logo_archivo_id BIGINT REFERENCES archivos(id),
    actualizado_por BIGINT NOT NULL REFERENCES usuarios(id),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE auditoria (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    usuario_id BIGINT REFERENCES usuarios(id),
    usuario_nombre VARCHAR(200),
    fecha_hora TIMESTAMPTZ NOT NULL DEFAULT now(),
    accion VARCHAR(80) NOT NULL,
    entidad VARCHAR(80) NOT NULL,
    entidad_id BIGINT,
    descripcion TEXT NOT NULL,
    resultado VARCHAR(12) NOT NULL CHECK (resultado IN ('EXITO', 'RECHAZADO', 'ERROR')),
    correlacion UUID NOT NULL
);
CREATE INDEX ix_auditoria_fecha ON auditoria(fecha_hora);
CREATE INDEX ix_auditoria_usuario ON auditoria(usuario_id, fecha_hora);
CREATE INDEX ix_auditoria_entidad ON auditoria(entidad, entidad_id);

CREATE TABLE auditoria_cambios (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    auditoria_id BIGINT NOT NULL REFERENCES auditoria(id),
    entidad VARCHAR(80) NOT NULL,
    entidad_id BIGINT NOT NULL,
    campo VARCHAR(100) NOT NULL,
    valor_anterior TEXT,
    valor_nuevo TEXT
);
CREATE INDEX ix_auditoria_cambio ON auditoria_cambios(auditoria_id);

INSERT INTO roles(codigo, descripcion) VALUES
    ('ADMINISTRADOR', 'Administración integral, cierre y reapertura'),
    ('PLANILLAS', 'Operación de personal y planillas abiertas'),
    ('CONSULTA', 'Lectura y reportes autorizados');

INSERT INTO tipos_descuento(codigo, nombre, orden) VALUES
    ('PICHINCHA', 'Pichincha', 1), ('CAJA_SULLANA', 'Caja Sullana', 2),
    ('SUB_CAFAE', 'Sub-CAFAE', 3), ('BRENTA', 'Conv. BRENTA', 4),
    ('SITRASE', 'SITRASE', 5), ('SITASE_FENTASE', 'SITASE / FENTASE', 6),
    ('OTROS', 'Otros descuentos', 7);

-- No se crean usuarios, contraseñas, trabajadores, cuentas, metas o firmas ficticias.
