"""Servicio de Dashboard y los 9 Reportes Administrativos Obligatorios (Etapa 16).
Garantiza que cada cifra provenga de la versión exacta seleccionada sin mezclar históricos.
"""
from decimal import Decimal
from cafae.auth import AuthService
from cafae.security import UserError


class ReporteService:
    def __init__(self, auth_service=None):
        self.auth = auth_service or AuthService()

    # =========================================================================
    # DASHBOARD
    # =========================================================================
    def get_dashboard_summary(self, token):
        """Retorna las métricas institucionales de II.EE. y Sede para el Dashboard."""
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            # Última versión de IIEE
            pln_iiee = conn.execute(
                '''SELECT p.id, per.anio, per.mes, p.tipo, pv.id AS version_id,
                          pv.numero, pv.estado, pv.total_trabajadores, pv.total_importe,
                          pv.total_descuentos, pv.total_neto, pv.cerrada_en
                   FROM planillas p
                   JOIN periodos per ON per.id = p.periodo_id
                   JOIN planilla_versiones pv ON pv.id = (
                       SELECT id FROM planilla_versiones WHERE planilla_id = p.id ORDER BY numero DESC LIMIT 1
                   )
                   WHERE p.tipo = 'IIEE'
                   ORDER BY per.anio DESC, per.mes DESC LIMIT 1'''
            ).fetchone()

            # Última versión de SEDE
            pln_sede = conn.execute(
                '''SELECT p.id, per.anio, per.mes, p.tipo, pv.id AS version_id,
                          pv.numero, pv.estado, pv.total_trabajadores, pv.total_importe,
                          pv.total_descuentos, pv.total_neto, pv.cerrada_en
                   FROM planillas p
                   JOIN periodos per ON per.id = p.periodo_id
                   JOIN planilla_versiones pv ON pv.id = (
                       SELECT id FROM planilla_versiones WHERE planilla_id = p.id ORDER BY numero DESC LIMIT 1
                   )
                   WHERE p.tipo = 'SEDE'
                   ORDER BY per.anio DESC, per.mes DESC LIMIT 1'''
            ).fetchone()

            tot_trab_activos = conn.execute(
                'SELECT count(*) AS total FROM trabajadores WHERE activo = true'
            ).fetchone()['total']

            tot_iiee = conn.execute(
                'SELECT count(*) AS total FROM instituciones WHERE activo = true'
            ).fetchone()['total']

            # Alertas accionables (netos negativos en versiones abiertas)
            alertas = conn.execute(
                '''SELECT count(*) AS total FROM planilla_detalle pd
                   JOIN planilla_versiones pv ON pv.id = pd.version_id
                   WHERE pv.estado <> 'CERRADA' AND pd.neto < 0'''
            ).fetchone()['total']

            return {
                'iiee': pln_iiee,
                'sede': pln_sede,
                'trabajadores_activos': tot_trab_activos,
                'instituciones_activas': tot_iiee,
                'alertas_neto_negativo': alertas
            }

    # =========================================================================
    # LOS 9 REPORTES OBLIGATORIOS
    # =========================================================================
    # 1. Resumen mensual
    def reporte_resumen_mensual(self, token, version_id):
        sql = '''SELECT pv.numero, pv.estado, pv.origen, p.tipo, per.anio, per.mes,
                        count(pd.id) AS total_personas,
                        COALESCE(sum(pd.importe), 0.00) AS total_importe,
                        COALESCE(sum(pd.monto_licencia), 0.00) AS total_licencia,
                        COALESCE(sum(pd.total_descuentos), 0.00) AS total_descuentos,
                        COALESCE(sum(pd.neto), 0.00) AS total_neto
                 FROM planilla_versiones pv
                 JOIN planillas p ON p.id = pv.planilla_id
                 JOIN periodos per ON per.id = p.periodo_id
                 LEFT JOIN planilla_detalle pd ON pd.version_id = pv.id
                 WHERE pv.id = %s
                 GROUP BY pv.id, pv.numero, pv.estado, pv.origen, p.tipo, per.anio, per.mes'''
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, (version_id,)).fetchone()

    # 2. Importe por institución
    def reporte_importe_por_institucion(self, token, version_id):
        sql = '''SELECT pd.institucion_id,
                        COALESCE(pd.institucion_nombre, 'SIN INSTITUCIÓN') AS institucion_nombre,
                        pd.codigo_modular,
                        count(pd.id) AS cantidad_trabajadores,
                        sum(pd.importe) AS total_importe,
                        sum(pd.total_descuentos) AS total_descuentos,
                        sum(pd.neto) AS total_neto
                 FROM planilla_detalle pd
                 WHERE pd.version_id = %s
                 GROUP BY pd.institucion_id, pd.institucion_nombre, pd.codigo_modular
                 ORDER BY total_importe DESC'''
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, (version_id,)).fetchall()

    # 3. Importe por meta
    def reporte_importe_por_meta(self, token, version_id):
        sql = '''SELECT pd.meta_codigo,
                        COALESCE(pd.meta_descripcion, 'Sin meta asignada') AS meta_descripcion,
                        count(pd.id) AS cantidad_trabajadores,
                        sum(pd.importe) AS total_importe,
                        sum(pd.neto) AS total_neto
                 FROM planilla_detalle pd
                 WHERE pd.version_id = %s
                 GROUP BY pd.meta_codigo, pd.meta_descripcion
                 ORDER BY pd.meta_codigo ASC'''
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, (version_id,)).fetchall()

    # 4. Descuentos por entidad
    def reporte_descuentos_por_entidad(self, token, version_id):
        sql = '''SELECT td.codigo, td.nombre AS entidad_nombre,
                        count(pd.id) FILTER (WHERE pd.monto > 0) AS trabajadores_afectados,
                        COALESCE(sum(pd.monto), 0.00) AS total_descontado
                 FROM tipos_descuento td
                 LEFT JOIN planilla_descuentos pd ON pd.tipo_descuento_id = td.id
                      AND pd.detalle_id IN (SELECT id FROM planilla_detalle WHERE version_id = %s)
                 GROUP BY td.id, td.codigo, td.nombre, td.orden
                 ORDER BY td.orden ASC'''
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, (version_id,)).fetchall()

    # 5. Neto por institución
    def reporte_neto_por_institucion(self, token, version_id):
        sql = '''SELECT COALESCE(pd.institucion_nombre, pd.area_nombre, 'GENERAL') AS nombre_entidad,
                        count(pd.id) AS personas,
                        sum(pd.importe) AS importe,
                        sum(pd.total_descuentos) AS descuentos,
                        sum(pd.neto) AS liquido_neto
                 FROM planilla_detalle pd
                 WHERE pd.version_id = %s
                 GROUP BY pd.institucion_nombre, pd.area_nombre
                 ORDER BY liquido_neto DESC'''
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, (version_id,)).fetchall()

    # 6. Trabajadores por nivel
    def reporte_trabajadores_por_nivel(self, token, version_id):
        sql = '''SELECT COALESCE(pd.nivel_nombre, 'SIN NIVEL') AS nivel_nombre,
                        count(pd.id) AS total_trabajadores,
                        sum(pd.importe) AS total_importe
                 FROM planilla_detalle pd
                 WHERE pd.version_id = %s
                 GROUP BY pd.nivel_nombre
                 ORDER BY total_trabajadores DESC'''
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, (version_id,)).fetchall()

    # 7. Trabajadores por situación
    def reporte_trabajadores_por_situacion(self, token, version_id):
        sql = '''SELECT COALESCE(pd.situacion, 'NO ESPECIFICADA') AS situacion_laboral,
                        count(pd.id) AS total_trabajadores,
                        sum(pd.importe) AS total_importe
                 FROM planilla_detalle pd
                 WHERE pd.version_id = %s
                 GROUP BY pd.situacion
                 ORDER BY total_trabajadores DESC'''
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, (version_id,)).fetchall()

    # 8. Licencias sin goce
    def reporte_licencias_sin_goce(self, token, version_id):
        sql = '''SELECT pd.dni, pd.apellidos, pd.nombres,
                        COALESCE(pd.institucion_nombre, pd.area_nombre) AS adscripcion,
                        pd.importe, pd.dias_licencia, pd.monto_licencia, pd.neto
                 FROM planilla_detalle pd
                 WHERE pd.version_id = %s AND pd.dias_licencia > 0
                 ORDER BY pd.dias_licencia DESC, pd.apellidos ASC'''
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, (version_id,)).fetchall()

    # 9. Comparación mensual
    def reporte_comparacion_mensual(self, token, version_id_1, version_id_2):
        sql = '''SELECT pv.id AS version_id, p.tipo, per.anio, per.mes, pv.numero,
                        pv.total_trabajadores, pv.total_importe, pv.total_descuentos, pv.total_neto
                 FROM planilla_versiones pv
                 JOIN planillas p ON p.id = pv.planilla_id
                 JOIN periodos per ON per.id = p.periodo_id
                 WHERE pv.id IN (%s, %s)'''
        with self.auth.data_transaction(token, 'consultar') as (conn, _):
            return conn.execute(sql, (version_id_1, version_id_2)).fetchall()
