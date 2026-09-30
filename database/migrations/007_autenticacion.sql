SET LOCAL search_path TO cafae, public;

DO $$ BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='cafae_auth') THEN
        CREATE ROLE cafae_auth NOLOGIN;
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname='cafae_service') THEN
        CREATE ROLE cafae_service LOGIN NOINHERIT NOSUPERUSER NOCREATEDB NOCREATEROLE;
    END IF;
END $$;
GRANT cafae_auth,cafae_consulta,cafae_operador,cafae_admin TO cafae_service;
GRANT USAGE ON SCHEMA cafae TO cafae_auth;
GRANT SELECT ON roles TO cafae_auth;
GRANT SELECT,INSERT,UPDATE ON usuarios,sesiones TO cafae_auth;
GRANT INSERT ON auditoria TO cafae_auth;
GRANT USAGE,SELECT ON SEQUENCE usuarios_id_seq,sesiones_id_seq,auditoria_id_seq TO cafae_auth;

CREATE TABLE acceso_intentos (
    clave CHAR(64) PRIMARY KEY CHECK (clave ~ '^[0-9a-f]{64}$'),
    inicio TIMESTAMPTZ NOT NULL DEFAULT now(),
    fallos INTEGER NOT NULL DEFAULT 0 CHECK (fallos>=0)
);
GRANT SELECT,INSERT,UPDATE,DELETE ON acceso_intentos TO cafae_auth;
CREATE INDEX ix_acceso_intentos_inicio ON acceso_intentos(inicio);
ALTER TABLE usuarios ADD COLUMN revision BIGINT NOT NULL DEFAULT 1 CHECK (revision>0);
INSERT INTO control_catalogos(codigo,revision) VALUES('usuarios',1);

CREATE FUNCTION proteger_usuarios() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
SET search_path = cafae, pg_temp AS $$
BEGIN
    -- Escritura de mutex: serializa incluso snapshots REPEATABLE READ antiguos.
    UPDATE control_catalogos SET revision=revision+1 WHERE codigo='usuarios';
    IF NOT EXISTS(SELECT 1 FROM usuarios u JOIN roles r ON r.id=u.rol_id
        WHERE u.activo AND r.codigo='ADMINISTRADOR') THEN
        RAISE EXCEPTION 'Debe conservarse al menos un administrador activo' USING ERRCODE='23514';
    END IF;
    IF TG_OP='UPDATE' THEN
        IF OLD.password_hash IS DISTINCT FROM NEW.password_hash OR OLD.rol_id<>NEW.rol_id
          OR OLD.activo IS DISTINCT FROM NEW.activo
          OR (NEW.debe_cambiar_password AND NOT OLD.debe_cambiar_password) THEN
            UPDATE sesiones SET revocada_en=now() WHERE usuario_id=NEW.id AND revocada_en IS NULL;
        END IF;
    END IF;
    RETURN NULL;
END $$;
CREATE FUNCTION revision_usuario() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    NEW.revision:=OLD.revision+1;
    IF NEW.password_hash IS DISTINCT FROM OLD.password_hash THEN
        NEW.password_actualizado_en:=now();
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER a_revision_usuario BEFORE UPDATE ON usuarios FOR EACH ROW EXECUTE FUNCTION revision_usuario();
CREATE TRIGGER y_proteger_usuarios AFTER INSERT OR UPDATE ON usuarios FOR EACH ROW EXECUTE FUNCTION proteger_usuarios();
CREATE TRIGGER usuario_no_borrar BEFORE DELETE ON usuarios FOR EACH ROW EXECUTE FUNCTION negar_mutacion();
CREATE TRIGGER usuario_no_truncar BEFORE TRUNCATE ON usuarios FOR EACH STATEMENT EXECUTE FUNCTION negar_mutacion();
REVOKE ALL ON acceso_intentos FROM PUBLIC;
REVOKE EXECUTE ON FUNCTION proteger_usuarios(),revision_usuario() FROM PUBLIC;
