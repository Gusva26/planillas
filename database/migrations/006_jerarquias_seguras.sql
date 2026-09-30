SET LOCAL search_path TO cafae, public;

-- Escribir esta fila serializa las modificaciones del árbol incluso con un
-- snapshot REPEATABLE READ anterior: el segundo escritor debe reintentar.
CREATE TABLE control_catalogos (
    codigo VARCHAR(40) PRIMARY KEY,
    revision BIGINT NOT NULL CHECK (revision > 0)
);
INSERT INTO control_catalogos(codigo,revision) VALUES ('programas',1);

CREATE OR REPLACE FUNCTION validar_arbol_programas() RETURNS trigger LANGUAGE plpgsql
SECURITY DEFINER SET search_path = cafae, pg_temp AS $$
DECLARE ciclo boolean;
BEGIN
    UPDATE control_catalogos SET revision=revision+1 WHERE codigo='programas';
    WITH RECURSIVE ascendientes(id,padre_id) AS (
        SELECT id,padre_id FROM programas WHERE id=NEW.padre_id
        UNION SELECT p.id,p.padre_id FROM programas p JOIN ascendientes a ON p.id=a.padre_id
    ) SELECT EXISTS(SELECT 1 FROM ascendientes WHERE id=NEW.id) INTO ciclo;
    IF ciclo THEN RAISE EXCEPTION 'Ciclo en programas' USING ERRCODE='23514'; END IF;
    RETURN NEW;
END $$;

CREATE FUNCTION validar_arbol_historico() RETURNS trigger LANGUAGE plpgsql
SET search_path = cafae, pg_temp AS $$
DECLARE ciclo boolean;
BEGIN
    -- a_programa_abierto ya adquirió/escribió el mutex de esta versión.
    WITH RECURSIVE ascendientes(id,padre_id) AS (
        SELECT id,padre_id FROM planilla_programas WHERE id=NEW.padre_id AND version_id=NEW.version_id
        UNION SELECT p.id,p.padre_id FROM planilla_programas p
          JOIN ascendientes a ON p.id=a.padre_id WHERE p.version_id=NEW.version_id
    ) SELECT EXISTS(SELECT 1 FROM ascendientes WHERE id=NEW.id) INTO ciclo;
    IF ciclo THEN RAISE EXCEPTION 'Ciclo en programas históricos' USING ERRCODE='23514'; END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER b_arbol_historico BEFORE INSERT OR UPDATE ON planilla_programas
    FOR EACH ROW EXECUTE FUNCTION validar_arbol_historico();
REVOKE EXECUTE ON FUNCTION validar_arbol_historico() FROM PUBLIC;
