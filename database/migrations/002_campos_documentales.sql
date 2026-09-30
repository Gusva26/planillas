SET LOCAL search_path TO cafae, public;

CREATE TABLE programas (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    padre_id BIGINT REFERENCES programas(id),
    codigo VARCHAR(30) NOT NULL UNIQUE CHECK (btrim(codigo) <> ''),
    nombre VARCHAR(180) NOT NULL,
    orden INTEGER NOT NULL CHECK (orden >= 0),
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    CHECK (padre_id IS NULL OR padre_id <> id)
);
CREATE INDEX ix_programa_padre ON programas(padre_id);
CREATE TABLE partidas_presupuestarias (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    codigo VARCHAR(40) NOT NULL UNIQUE,
    descripcion TEXT NOT NULL,
    activo BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en TIMESTAMPTZ NOT NULL DEFAULT now(),
    actualizado_en TIMESTAMPTZ NOT NULL DEFAULT now()
);
ALTER TABLE metas ADD COLUMN programa_id BIGINT REFERENCES programas(id),
    ADD COLUMN partida_id BIGINT REFERENCES partidas_presupuestarias(id);
CREATE INDEX ix_meta_programa ON metas(programa_id);
CREATE INDEX ix_meta_partida ON metas(partida_id);

ALTER TABLE trabajadores
    ADD COLUMN regimen_pensionario VARCHAR(120),
    ADD COLUMN fecha_ingreso DATE,
    ADD COLUMN fecha_termino DATE,
    ADD COLUMN tiempo_servicio_texto VARCHAR(60),
    ADD COLUMN leyenda_permanente TEXT,
    ADD COLUMN tipo_pago VARCHAR(10) NOT NULL DEFAULT 'CUENTA'
        CHECK (tipo_pago IN ('CUENTA', 'CHEQUE')),
    ADD COLUMN numero_cheque VARCHAR(60),
    ADD CONSTRAINT ck_fechas_laborales CHECK
        (fecha_termino IS NULL OR fecha_ingreso IS NULL OR fecha_termino >= fecha_ingreso);

-- Árbol copiado por versión. La relación padre/hijo también queda histórica.
CREATE TABLE planilla_programas (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    version_id BIGINT NOT NULL REFERENCES planilla_versiones(id),
    programa_id BIGINT NOT NULL REFERENCES programas(id),
    padre_id BIGINT,
    codigo VARCHAR(30) NOT NULL,
    nombre VARCHAR(180) NOT NULL,
    orden INTEGER NOT NULL CHECK (orden >= 0),
    UNIQUE(id, version_id),
    UNIQUE(version_id, programa_id),
    UNIQUE(version_id, codigo),
    FOREIGN KEY (padre_id, version_id) REFERENCES planilla_programas(id, version_id),
    CHECK (padre_id IS NULL OR padre_id <> id)
);
CREATE INDEX ix_pp_padre ON planilla_programas(padre_id, version_id);
CREATE INDEX ix_pp_programa ON planilla_programas(programa_id);
ALTER TABLE planilla_detalle
    ADD COLUMN regimen_pensionario VARCHAR(120),
    ADD COLUMN fecha_ingreso DATE,
    ADD COLUMN fecha_termino DATE,
    ADD COLUMN tiempo_servicio_texto VARCHAR(60),
    ADD COLUMN leyenda_permanente TEXT,
    ADD COLUMN leyenda_mensual TEXT,
    ADD COLUMN descripcion_ingreso TEXT,
    ADD COLUMN tipo_pago VARCHAR(10) NOT NULL DEFAULT 'CUENTA'
        CHECK (tipo_pago IN ('CUENTA', 'CHEQUE')),
    ADD COLUMN numero_cheque VARCHAR(60),
    ADD COLUMN programa_snapshot_id BIGINT,
    ADD COLUMN partida_codigo VARCHAR(40),
    ADD COLUMN partida_descripcion TEXT,
    ADD CONSTRAINT fk_detalle_programa FOREIGN KEY (programa_snapshot_id, version_id)
        REFERENCES planilla_programas(id, version_id),
    ADD CONSTRAINT ck_snapshot_fechas CHECK
        (fecha_termino IS NULL OR fecha_ingreso IS NULL OR fecha_termino >= fecha_ingreso);
CREATE INDEX ix_detalle_programa ON planilla_detalle(programa_snapshot_id, version_id);

ALTER TABLE configuracion_institucional
    ADD COLUMN ruc VARCHAR(11) CHECK (ruc ~ '^[0-9]{11}$'),
    ADD COLUMN unidad_ejecutora VARCHAR(200),
    ADD COLUMN texto_contacto TEXT,
    ADD COLUMN descripcion_ingreso TEXT;
ALTER TABLE planilla_versiones
    ADD COLUMN institucion_emisora VARCHAR(200),
    ADD COLUMN ruc_emisor VARCHAR(11) CHECK (ruc_emisor ~ '^[0-9]{11}$'),
    ADD COLUMN unidad_ejecutora VARCHAR(200),
    ADD COLUMN texto_contacto TEXT;
-- El archivo de logo se referencia después de existir archivos en la base.
ALTER TABLE planilla_versiones ADD COLUMN logo_archivo_id BIGINT REFERENCES archivos(id);
CREATE INDEX ix_version_logo ON planilla_versiones(logo_archivo_id);

COMMENT ON COLUMN trabajadores.tiempo_servicio_texto IS
    'Dato documental de origen. No inferir antigüedad automáticamente sin regla administrativa.';
COMMENT ON COLUMN planilla_detalle.importe IS
    'Único ingreso. En Sede corresponde a REMUN. TOTAL, columna I del original.';
COMMENT ON COLUMN planilla_detalle.monto_licencia IS
    'Derivado de importe / 30 * días; no duplicar en planilla_descuentos.';
