SET LOCAL search_path TO cafae, public;

CREATE FUNCTION cerrar_planilla(p_version bigint,p_revision bigint,p_usuario bigint)
RETURNS bigint LANGUAGE plpgsql SET search_path = cafae, pg_temp AS $$
DECLARE v planilla_versiones%ROWTYPE; n integer; importe numeric; descuentos numeric; neto numeric;
BEGIN
    IF NOT pg_has_role(current_user,'cafae_admin','USAGE') THEN
        RAISE EXCEPTION 'Cierre reservado a administración' USING ERRCODE='42501';
    END IF;
    IF NOT EXISTS(SELECT 1 FROM usuarios u JOIN roles r ON r.id=u.rol_id
        WHERE u.id=p_usuario AND u.activo AND r.codigo='ADMINISTRADOR') THEN
        RAISE EXCEPTION 'El responsable debe ser administrador activo' USING ERRCODE='42501';
    END IF;
    SELECT * INTO STRICT v FROM planilla_versiones WHERE id=p_version FOR UPDATE;
    IF v.estado='CERRADA' THEN
        RAISE EXCEPTION 'La versión ya está cerrada' USING ERRCODE='23514';
    END IF;
    IF p_revision IS NULL OR v.revision_edicion <> p_revision THEN
        RAISE EXCEPTION 'La planilla cambió; vuelva a revisar antes de cerrar' USING ERRCODE='40001';
    END IF;
    -- En READ COMMITTED esta consulta obtiene una vista fresca después del bloqueo.
    -- Todo escritor de hijos bloquea/escribe la misma fila de versión.
    SELECT count(*),sum(d.importe),sum(d.total_descuentos),sum(d.neto)
        INTO n,importe,descuentos,neto FROM planilla_detalle d WHERE version_id=p_version;
    PERFORM set_config('cafae.usuario_id',p_usuario::text,true);
    UPDATE planilla_versiones SET estado='CERRADA',cerrada_por=p_usuario,cerrada_en=clock_timestamp(),
        total_trabajadores=n,total_importe=importe,total_descuentos=descuentos,total_neto=neto
        WHERE id=p_version;
    RETURN p_version;
END $$;
REVOKE EXECUTE ON FUNCTION cerrar_planilla(bigint,bigint,bigint) FROM PUBLIC;
GRANT EXECUTE ON FUNCTION cerrar_planilla(bigint,bigint,bigint) TO cafae_admin;
