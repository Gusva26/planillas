SET LOCAL search_path TO cafae, public;
REVOKE ALL ON SCHEMA cafae FROM PUBLIC;
REVOKE ALL ON ALL TABLES IN SCHEMA cafae FROM PUBLIC;
REVOKE ALL ON ALL SEQUENCES IN SCHEMA cafae FROM PUBLIC;
REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA cafae FROM PUBLIC;
GRANT USAGE ON SCHEMA cafae TO cafae_consulta,cafae_operador,cafae_admin;
GRANT cafae_consulta TO cafae_operador;
GRANT cafae_operador TO cafae_admin;

GRANT SELECT ON trabajadores,instituciones,areas_sede,niveles,metas,cargos,categorias,
    situaciones,subtipos_trabajador,firmas,programas,partidas_presupuestarias,nivel_metas,
    periodos,planillas,planilla_versiones,planilla_detalle,planilla_descuentos,tipos_descuento,
    planilla_firmas,planilla_programas,observaciones_planilla,ultimos_cierres,remuneraciones_por_meta
    TO cafae_consulta;
-- Las descargas pasarán por servicios autorizados; consulta no lee rutas ni TXT directamente.
GRANT SELECT ON archivos,plantillas_documento,documentos_generados,importaciones,importacion_detalle
    TO cafae_operador;
GRANT USAGE,SELECT ON ALL SEQUENCES IN SCHEMA cafae TO cafae_operador;
GRANT INSERT,UPDATE ON trabajadores,planillas,planilla_versiones,planilla_detalle,
    planilla_descuentos,planilla_firmas,planilla_programas,observaciones_planilla,
    importaciones,importacion_detalle TO cafae_operador;
GRANT DELETE ON planilla_descuentos,planilla_firmas,planilla_programas,observaciones_planilla,
    importacion_detalle TO cafae_operador;
GRANT INSERT,UPDATE ON periodos,archivos,documentos_generados TO cafae_operador;
GRANT EXECUTE ON FUNCTION bloquear_edicion(bigint,bigint) TO cafae_operador;

GRANT SELECT,INSERT,UPDATE,DELETE ON usuarios,instituciones,areas_sede,niveles,metas,cargos,categorias,
    situaciones,subtipos_trabajador,firmas,programas,partidas_presupuestarias,nivel_metas,
    configuracion_institucional,plantillas_documento TO cafae_admin;
GRANT SELECT ON roles,auditoria,auditoria_cambios TO cafae_admin;
-- Autenticación (etapa 2) tendrá una conexión/servicio separado y no expondrá hashes.
-- Ningún rol de aplicación es propietario, superusuario ni tiene TRUNCATE o DDL.
ALTER DEFAULT PRIVILEGES IN SCHEMA cafae REVOKE EXECUTE ON FUNCTIONS FROM PUBLIC;
