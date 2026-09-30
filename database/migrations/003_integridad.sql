SET LOCAL search_path TO cafae, public;

-- Funciones de trigger con search_path fijo; sin SQL dinámico procedente del usuario.
CREATE FUNCTION tocar_actualizado() RETURNS trigger LANGUAGE plpgsql
SET search_path = cafae, pg_temp AS $$
BEGIN NEW.actualizado_en := clock_timestamp(); RETURN NEW; END $$;

CREATE FUNCTION negar_mutacion() RETURNS trigger LANGUAGE plpgsql
SET search_path = cafae, pg_temp AS $$
BEGIN RAISE EXCEPTION 'Registro histórico: operación no permitida' USING ERRCODE='23514'; END $$;

CREATE FUNCTION proteger_periodo() RETURNS trigger LANGUAGE plpgsql
SET search_path = cafae, pg_temp AS $$
BEGIN
    IF EXISTS (SELECT 1 FROM planillas WHERE periodo_id=OLD.id) THEN
        RAISE EXCEPTION 'El periodo tiene planillas' USING ERRCODE='23514';
    END IF;
    IF TG_OP='DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER periodo_referenciado BEFORE UPDATE OR DELETE ON periodos
    FOR EACH ROW EXECUTE FUNCTION proteger_periodo();
CREATE TRIGGER planilla_identidad BEFORE UPDATE OR DELETE ON planillas
    FOR EACH ROW EXECUTE FUNCTION negar_mutacion();

CREATE FUNCTION validar_arbol_programas() RETURNS trigger LANGUAGE plpgsql
SET search_path = cafae, pg_temp AS $$
DECLARE ciclo boolean;
BEGIN
    -- Las ediciones de jerarquía se serializan para impedir ciclos cruzados.
    PERFORM pg_advisory_xact_lock(82609124);
    WITH RECURSIVE ascendientes(id,padre_id) AS (
        SELECT id,padre_id FROM programas WHERE id=NEW.padre_id
        UNION SELECT p.id,p.padre_id FROM programas p JOIN ascendientes a ON p.id=a.padre_id
    ) SELECT EXISTS(SELECT 1 FROM ascendientes WHERE id=NEW.id) INTO ciclo;
    IF ciclo THEN RAISE EXCEPTION 'Ciclo en programas' USING ERRCODE='23514'; END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER programas_arbol BEFORE INSERT OR UPDATE ON programas
    FOR EACH ROW EXECUTE FUNCTION validar_arbol_programas();

CREATE FUNCTION validar_version() RETURNS trigger LANGUAGE plpgsql
SET search_path = cafae, pg_temp AS $$
DECLARE p planillas%ROWTYPE; fuente planilla_versiones%ROWTYPE;
    fecha date; fecha_fuente date; cantidad integer; total_i numeric; total_d numeric; total_n numeric;
BEGIN
    IF TG_OP='DELETE' THEN
        RAISE EXCEPTION 'Las versiones no se eliminan' USING ERRCODE='23514';
    END IF;
    IF TG_OP='UPDATE' THEN
        IF OLD.estado='CERRADA' THEN
            RAISE EXCEPTION 'La versión cerrada es inmutable; cree una reapertura' USING ERRCODE='23514';
        END IF;
        IF (NEW.id,NEW.planilla_id,NEW.numero,NEW.origen,NEW.fuente_version_id,NEW.creada_por,NEW.creada_en)
            IS DISTINCT FROM (OLD.id,OLD.planilla_id,OLD.numero,OLD.origen,OLD.fuente_version_id,OLD.creada_por,OLD.creada_en) THEN
            RAISE EXCEPTION 'No se cambia la identidad u origen de la versión' USING ERRCODE='23514';
        END IF;
    END IF;
    SELECT * INTO STRICT p FROM planillas WHERE id=NEW.planilla_id;
    IF TG_OP='INSERT' THEN
        PERFORM 1 FROM planillas WHERE id=p.id FOR UPDATE;
        IF NEW.estado <> 'BORRADOR' OR NEW.numero <> COALESCE(
            (SELECT max(numero)+1 FROM planilla_versiones WHERE planilla_id=p.id),1) THEN
            RAISE EXCEPTION 'La versión debe comenzar en borrador y ser correlativa' USING ERRCODE='23514';
        END IF;
        IF NEW.numero > 1 AND NEW.origen <> 'REAPERTURA' THEN
            RAISE EXCEPTION 'Una versión posterior requiere reapertura' USING ERRCODE='23514';
        END IF;
        IF NEW.fuente_version_id IS NOT NULL THEN
            SELECT * INTO STRICT fuente FROM planilla_versiones WHERE id=NEW.fuente_version_id;
            IF NEW.origen='REAPERTURA' THEN
                IF fuente.planilla_id <> p.id OR fuente.estado <> 'CERRADA' OR fuente.numero <> NEW.numero-1 THEN
                    RAISE EXCEPTION 'Reabrir requiere el último cierre de la misma planilla' USING ERRCODE='23514';
                END IF;
                IF NOT pg_has_role(current_user,'cafae_admin','USAGE') THEN
                    RAISE EXCEPTION 'Reapertura reservada a administración' USING ERRCODE='42501';
                END IF;
            ELSIF NEW.origen='COPIA' THEN
                SELECT make_date(pe.anio,pe.mes,1) INTO fecha FROM periodos pe WHERE pe.id=p.periodo_id;
                SELECT make_date(pe.anio,pe.mes,1) INTO fecha_fuente
                    FROM planillas pf JOIN periodos pe ON pe.id=pf.periodo_id
                    WHERE pf.id=fuente.planilla_id AND pf.tipo=p.tipo;
                IF fecha_fuente IS NULL OR fecha_fuente <> (fecha - interval '1 month')::date THEN
                    RAISE EXCEPTION 'La copia requiere el mes inmediatamente anterior y mismo tipo' USING ERRCODE='23514';
                END IF;
            END IF;
        END IF;
    END IF;
    IF NEW.estado='CERRADA' THEN
        IF NOT pg_has_role(current_user,'cafae_admin','USAGE') THEN
            RAISE EXCEPTION 'Cierre reservado a administración' USING ERRCODE='42501';
        END IF;
        SELECT count(*) INTO cantidad FROM planilla_firmas WHERE version_id=NEW.id;
        IF cantidad <> p.cantidad_firmas OR EXISTS (
            SELECT 1 FROM planilla_firmas WHERE version_id=NEW.id AND posicion>p.cantidad_firmas) THEN
            RAISE EXCEPTION 'Faltan firmas o posiciones incorrectas para el tipo' USING ERRCODE='23514';
        END IF;
        IF EXISTS (SELECT 1 FROM planilla_detalle d WHERE d.version_id=NEW.id AND (
            d.importe=0 OR d.neto<0 OR NULLIF(btrim(d.meta_codigo),'') IS NULL
            OR NULLIF(btrim(d.categoria),'') IS NULL
            OR NULLIF(btrim(d.apellidos),'') IS NULL OR NULLIF(btrim(d.nombres),'') IS NULL
            OR (p.tipo='IIEE' AND (d.institucion_id IS NULL OR NULLIF(btrim(d.institucion_nombre),'') IS NULL))
            OR (p.tipo='SEDE' AND (d.area_id IS NULL OR NULLIF(btrim(d.area_nombre),'') IS NULL))
            OR (d.tipo_pago='CUENTA' AND (d.cuenta_multired IS NULL OR d.cuenta_multired !~ '^[0-9]+$'))
            OR (d.tipo_pago='CHEQUE' AND NULLIF(btrim(d.numero_cheque),'') IS NULL)
            OR d.monto_licencia <> round(d.importe/30*d.dias_licencia,2)
            OR d.total_descuentos <> d.monto_licencia + COALESCE(
                (SELECT sum(x.monto) FROM planilla_descuentos x WHERE x.detalle_id=d.id),0)
        )) THEN
            RAISE EXCEPTION 'La planilla tiene datos incompletos o cálculos inconsistentes' USING ERRCODE='23514';
        END IF;
        IF EXISTS (SELECT 1 FROM observaciones_planilla WHERE version_id=NEW.id
            AND revision_validada=NEW.revision_edicion AND severidad='ERROR') THEN
            RAISE EXCEPTION 'Existen observaciones bloqueantes' USING ERRCODE='23514';
        END IF;
        SELECT count(*),sum(importe),sum(total_descuentos),sum(neto)
            INTO cantidad,total_i,total_d,total_n FROM planilla_detalle WHERE version_id=NEW.id;
        IF cantidad=0 OR (NEW.total_trabajadores,NEW.total_importe,NEW.total_descuentos,NEW.total_neto)
            IS DISTINCT FROM (cantidad,total_i,total_d,total_n) THEN
            RAISE EXCEPTION 'Los totales de cierre no concilian con el detalle' USING ERRCODE='23514';
        END IF;
    END IF;
    RETURN NEW;
END $$;

-- Los roles se crean sin LOGIN y sin privilegios administrativos.
DO $$ BEGIN
    IF NOT EXISTS(SELECT FROM pg_roles WHERE rolname='cafae_consulta') THEN CREATE ROLE cafae_consulta NOLOGIN; END IF;
    IF NOT EXISTS(SELECT FROM pg_roles WHERE rolname='cafae_operador') THEN CREATE ROLE cafae_operador NOLOGIN; END IF;
    IF NOT EXISTS(SELECT FROM pg_roles WHERE rolname='cafae_admin') THEN CREATE ROLE cafae_admin NOLOGIN; END IF;
END $$;
CREATE TRIGGER version_integridad BEFORE INSERT OR UPDATE OR DELETE ON planilla_versiones
    FOR EACH ROW EXECUTE FUNCTION validar_version();

CREATE FUNCTION bloquear_edicion(p_version bigint, p_revision bigint DEFAULT NULL)
RETURNS bigint LANGUAGE plpgsql SET search_path = cafae, pg_temp AS $$
DECLARE v planilla_versiones%ROWTYPE;
BEGIN
    SELECT * INTO STRICT v FROM planilla_versiones WHERE id=p_version FOR UPDATE;
    IF v.estado='CERRADA' THEN
        RAISE EXCEPTION 'La versión está cerrada' USING ERRCODE='23514';
    END IF;
    IF p_revision IS NOT NULL AND p_revision <> v.revision_edicion THEN
        RAISE EXCEPTION 'La planilla cambió; actualice antes de guardar' USING ERRCODE='40001';
    END IF;
    -- Escribir, además de bloquear, fuerza conflicto en snapshots repetibles antiguos.
    UPDATE planilla_versiones SET revision_edicion=revision_edicion+1 WHERE id=p_version;
    RETURN v.revision_edicion+1;
END $$;

CREATE FUNCTION proteger_hijo() RETURNS trigger LANGUAGE plpgsql
SET search_path = cafae, pg_temp AS $$
DECLARE fila jsonb; anterior jsonb; v_id bigint; max_firmas integer; importe_base numeric; suma numeric;
BEGIN
    IF TG_OP='DELETE' THEN fila:=to_jsonb(OLD); ELSE fila:=to_jsonb(NEW); END IF;
    IF TG_OP='UPDATE' THEN
        anterior:=to_jsonb(OLD);
        IF (fila->>'id',fila->>TG_ARGV[0]) IS DISTINCT FROM (anterior->>'id',anterior->>TG_ARGV[0]) THEN
            RAISE EXCEPTION 'No se permite mover un registro a otro padre' USING ERRCODE='23514';
        END IF;
    END IF;
    IF TG_ARGV[0]='detalle_id' THEN
        SELECT version_id INTO STRICT v_id FROM planilla_detalle WHERE id=(fila->>'detalle_id')::bigint;
    ELSE v_id:=(fila->>'version_id')::bigint; END IF;
    PERFORM bloquear_edicion(v_id);
    IF TG_TABLE_NAME='planilla_firmas' AND TG_OP<>'DELETE' THEN
        SELECT p.cantidad_firmas INTO max_firmas FROM planillas p
            JOIN planilla_versiones v ON v.planilla_id=p.id WHERE v.id=v_id;
        IF NEW.posicion>max_firmas THEN
            RAISE EXCEPTION 'Posición de firma no permitida para este tipo' USING ERRCODE='23514';
        END IF;
        IF btrim(NEW.nombre_completo)='' OR btrim(NEW.cargo)='' THEN
            RAISE EXCEPTION 'Firma sin nombre o cargo' USING ERRCODE='23514';
        END IF;
    END IF;
    IF TG_OP='DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END $$;

CREATE TRIGGER a_detalle_abierto BEFORE INSERT OR UPDATE OR DELETE ON planilla_detalle
    FOR EACH ROW EXECUTE FUNCTION proteger_hijo('version_id');
CREATE TRIGGER a_descuento_abierto BEFORE INSERT OR UPDATE OR DELETE ON planilla_descuentos
    FOR EACH ROW EXECUTE FUNCTION proteger_hijo('detalle_id');
CREATE TRIGGER a_firma_abierta BEFORE INSERT OR UPDATE OR DELETE ON planilla_firmas
    FOR EACH ROW EXECUTE FUNCTION proteger_hijo('version_id');
CREATE TRIGGER a_programa_abierto BEFORE INSERT OR UPDATE OR DELETE ON planilla_programas
    FOR EACH ROW EXECUTE FUNCTION proteger_hijo('version_id');
CREATE TRIGGER a_observacion_abierta BEFORE INSERT OR UPDATE OR DELETE ON observaciones_planilla
    FOR EACH ROW EXECUTE FUNCTION proteger_hijo('version_id');

CREATE FUNCTION calcular_detalle() RETURNS trigger LANGUAGE plpgsql
SET search_path = cafae, pg_temp AS $$
BEGIN
    NEW.monto_licencia:=round(NEW.importe/30*NEW.dias_licencia,2);
    SELECT NEW.monto_licencia+COALESCE(sum(monto),0) INTO NEW.total_descuentos
        FROM planilla_descuentos WHERE detalle_id=NEW.id;
    NEW.neto:=NEW.importe-NEW.total_descuentos;
    NEW.actualizado_en:=clock_timestamp();
    RETURN NEW;
END $$;
CREATE TRIGGER b_calcular_detalle BEFORE INSERT OR UPDATE ON planilla_detalle
    FOR EACH ROW EXECUTE FUNCTION calcular_detalle();

CREATE FUNCTION recalcular_descuento() RETURNS trigger LANGUAGE plpgsql
SET search_path = cafae, pg_temp AS $$
DECLARE d_id bigint;
BEGIN
    IF TG_OP='DELETE' THEN d_id:=OLD.detalle_id; ELSE d_id:=NEW.detalle_id; END IF;
    UPDATE planilla_detalle SET actualizado_en=clock_timestamp() WHERE id=d_id;
    RETURN NULL;
END $$;
CREATE TRIGGER descuento_recalculo AFTER INSERT OR UPDATE OR DELETE ON planilla_descuentos
    FOR EACH ROW EXECUTE FUNCTION recalcular_descuento();

CREATE FUNCTION proteger_importacion() RETURNS trigger LANGUAGE plpgsql
SET search_path = cafae, pg_temp AS $$
DECLARE imp importaciones%ROWTYPE; fila jsonb;
BEGIN
    IF TG_OP='DELETE' THEN fila:=to_jsonb(OLD); ELSE fila:=to_jsonb(NEW); END IF;
    IF TG_OP='UPDATE' AND (to_jsonb(OLD)->>'id',to_jsonb(OLD)->>'version_id',to_jsonb(OLD)->>'importacion_id')
        IS DISTINCT FROM (fila->>'id',fila->>'version_id',fila->>'importacion_id') THEN
        RAISE EXCEPTION 'No se permite mover una importación' USING ERRCODE='23514';
    END IF;
    PERFORM bloquear_edicion((fila->>'version_id')::bigint);
    IF TG_TABLE_NAME='importaciones' THEN
        IF TG_OP<>'INSERT' AND OLD.estado='APLICADA' THEN
            RAISE EXCEPTION 'La importación aplicada es inmutable' USING ERRCODE='23514';
        END IF;
    ELSE
        SELECT * INTO STRICT imp FROM importaciones WHERE id=(fila->>'importacion_id')::bigint FOR UPDATE;
        IF imp.estado='APLICADA' THEN
            RAISE EXCEPTION 'El detalle de una importación aplicada es inmutable' USING ERRCODE='23514';
        END IF;
        IF TG_OP<>'DELETE' AND NEW.seleccionado AND NOT EXISTS (
            SELECT 1 FROM planilla_detalle WHERE id=NEW.detalle_planilla_id
              AND version_id=NEW.version_id AND dni=NEW.dni_normalizado) THEN
            RAISE EXCEPTION 'El DNI no coincide con el detalle de la planilla' USING ERRCODE='23514';
        END IF;
    END IF;
    IF TG_OP='DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER importacion_protegida BEFORE INSERT OR UPDATE OR DELETE ON importaciones
    FOR EACH ROW EXECUTE FUNCTION proteger_importacion();
CREATE TRIGGER importacion_fila_protegida BEFORE INSERT OR UPDATE OR DELETE ON importacion_detalle
    FOR EACH ROW EXECUTE FUNCTION proteger_importacion();

CREATE FUNCTION validar_documento() RETURNS trigger LANGUAGE plpgsql
SET search_path = cafae, pg_temp AS $$
DECLARE estado_version text; tipo_plantilla text; validada timestamptz; tipo_planilla text;
BEGIN
    SELECT v.estado,p.tipo INTO STRICT estado_version,tipo_planilla
      FROM planilla_versiones v JOIN planillas p ON p.id=v.planilla_id WHERE v.id=NEW.version_id;
    IF estado_version<>'CERRADA' THEN
        RAISE EXCEPTION 'Solo se archivan documentos de versiones cerradas' USING ERRCODE='23514';
    END IF;
    SELECT tipo,validada_en INTO STRICT tipo_plantilla,validada FROM plantillas_documento WHERE id=NEW.plantilla_id;
    IF validada IS NULL THEN RAISE EXCEPTION 'Plantilla no validada' USING ERRCODE='23514'; END IF;
    IF tipo_plantilla <> (CASE NEW.tipo
       WHEN 'PLANILLA_PDF' THEN 'PLANILLA_'||tipo_planilla||'_PDF'
       WHEN 'PLANILLA_EXCEL' THEN 'PLANILLA_'||tipo_planilla||'_EXCEL'
       WHEN 'BOLETA_INDIVIDUAL' THEN 'BOLETA' WHEN 'BOLETAS_TODAS' THEN 'BOLETA'
       WHEN 'TXT' THEN 'TXT_BANCARIO' ELSE NEW.tipo END) THEN
        RAISE EXCEPTION 'Plantilla incompatible con el documento' USING ERRCODE='23514';
    END IF;
    IF NEW.tipo='TXT' THEN
        RAISE EXCEPTION 'TXT pendiente de contrato bancario validado' USING ERRCODE='23514';
    END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER documento_validado BEFORE INSERT ON documentos_generados
    FOR EACH ROW EXECUTE FUNCTION validar_documento();
CREATE TRIGGER documento_inmutable BEFORE UPDATE OR DELETE ON documentos_generados
    FOR EACH ROW EXECUTE FUNCTION negar_mutacion();
CREATE TRIGGER archivo_inmutable BEFORE UPDATE OR DELETE ON archivos
    FOR EACH ROW EXECUTE FUNCTION negar_mutacion();

-- Plantillas ya validadas se versionan mediante un nuevo registro.
CREATE FUNCTION proteger_plantilla() RETURNS trigger LANGUAGE plpgsql
SET search_path = cafae, pg_temp AS $$
BEGIN
    IF OLD.validada_en IS NOT NULL THEN
        RAISE EXCEPTION 'Crear otra versión de la plantilla validada' USING ERRCODE='23514';
    END IF;
    IF TG_OP='DELETE' THEN RETURN OLD; END IF;
    RETURN NEW;
END $$;
CREATE TRIGGER plantilla_inmutable BEFORE UPDATE OR DELETE ON plantillas_documento
    FOR EACH ROW EXECUTE FUNCTION proteger_plantilla();

-- JSON solo se usa transitoriamente para comparar columnas, no como almacén de planillas.
CREATE FUNCTION auditar_cambio() RETURNS trigger LANGUAGE plpgsql SECURITY DEFINER
SET search_path = cafae, pg_temp AS $$
DECLARE previo jsonb; actual jsonb; actor bigint; evento bigint; identificador bigint;
    campo text; valor jsonb; nombre_actor text; operacion text;
BEGIN
    IF TG_OP<>'INSERT' THEN previo:=to_jsonb(OLD); END IF;
    IF TG_OP<>'DELETE' THEN actual:=to_jsonb(NEW); END IF;
    IF previo IS NOT DISTINCT FROM actual THEN RETURN NULL; END IF;
    actor:=NULLIF(current_setting('cafae.usuario_id',true),'')::bigint;
    IF actor IS NOT NULL THEN SELECT nombre_completo INTO STRICT nombre_actor FROM usuarios WHERE id=actor; END IF;
    identificador:=COALESCE((actual->>'id')::bigint,(previo->>'id')::bigint,
        (actual->>'nivel_id')::bigint,(previo->>'nivel_id')::bigint);
    operacion:=TG_OP;
    IF TG_TABLE_NAME='planilla_versiones' AND actual->>'estado'='CERRADA' THEN operacion:='CERRAR_PLANILLA';
    ELSIF TG_TABLE_NAME='planilla_versiones' AND TG_OP='INSERT' AND actual->>'origen'='REAPERTURA' THEN operacion:='REABRIR_PLANILLA'; END IF;
    INSERT INTO auditoria(usuario_id,usuario_nombre,accion,entidad,entidad_id,descripcion,resultado,correlacion)
        VALUES(actor,nombre_actor,operacion,TG_TABLE_NAME,identificador,
          'Operación de base de datos; rol técnico: '||COALESCE(NULLIF(current_setting('role',true),'none'),session_user),
          'EXITO',COALESCE(NULLIF(current_setting('cafae.correlacion',true),'')::uuid,gen_random_uuid())) RETURNING id INTO evento;
    FOR campo,valor IN SELECT * FROM jsonb_each(COALESCE(actual,previo)) LOOP
        IF campo NOT IN ('password_hash','token_hash','actualizado_en','revision_edicion','ultimo_acceso_en')
           AND previo->campo IS DISTINCT FROM actual->campo THEN
            INSERT INTO auditoria_cambios(auditoria_id,entidad,entidad_id,campo,valor_anterior,valor_nuevo)
                VALUES(evento,TG_TABLE_NAME,identificador,campo,previo->>campo,actual->>campo);
        END IF;
    END LOOP;
    RETURN NULL;
END $$;
CREATE TRIGGER auditoria_inmutable BEFORE UPDATE OR DELETE ON auditoria
    FOR EACH ROW EXECUTE FUNCTION negar_mutacion();
CREATE TRIGGER auditoria_cambios_inmutables BEFORE UPDATE OR DELETE ON auditoria_cambios
    FOR EACH ROW EXECUTE FUNCTION negar_mutacion();

DO $$ DECLARE t text; BEGIN
    FOREACH t IN ARRAY ARRAY['usuarios','trabajadores','instituciones','areas_sede','niveles','metas','cargos',
        'categorias','situaciones','subtipos_trabajador','firmas','programas','partidas_presupuestarias',
        'configuracion_institucional','planilla_descuentos','nivel_metas'] LOOP
        EXECUTE format('CREATE TRIGGER z_actualizado BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION tocar_actualizado()',t);
    END LOOP;
    FOREACH t IN ARRAY ARRAY['usuarios','trabajadores','instituciones','areas_sede','niveles','metas','cargos',
        'categorias','situaciones','subtipos_trabajador','firmas','programas','partidas_presupuestarias',
        'configuracion_institucional','planillas','planilla_versiones','planilla_detalle','planilla_descuentos',
        'planilla_firmas','planilla_programas','importaciones','importacion_detalle','documentos_generados','nivel_metas'] LOOP
        EXECUTE format('CREATE TRIGGER z_auditar AFTER INSERT OR UPDATE OR DELETE ON %I FOR EACH ROW EXECUTE FUNCTION auditar_cambio()',t);
    END LOOP;
    FOREACH t IN ARRAY ARRAY['planillas','planilla_versiones','planilla_detalle','planilla_descuentos',
        'planilla_firmas','planilla_programas','observaciones_planilla','importaciones','importacion_detalle',
        'documentos_generados','archivos','auditoria','auditoria_cambios','periodos','plantillas_documento'] LOOP
        EXECUTE format('CREATE TRIGGER no_truncar BEFORE TRUNCATE ON %I EXECUTE FUNCTION negar_mutacion()',t);
    END LOOP;
END $$;

CREATE VIEW ultimos_cierres AS
    SELECT DISTINCT ON (planilla_id) * FROM planilla_versiones WHERE estado='CERRADA'
    ORDER BY planilla_id,numero DESC;
CREATE VIEW remuneraciones_por_meta AS
    SELECT d.version_id,d.meta_codigo,d.meta_descripcion,d.partida_codigo,
           count(*) AS trabajadores,sum(d.importe) AS importe
    FROM planilla_detalle d JOIN ultimos_cierres v ON v.id=d.version_id
    GROUP BY d.version_id,d.meta_codigo,d.meta_descripcion,d.partida_codigo;
