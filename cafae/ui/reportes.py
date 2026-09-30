"""Módulo de interfaz de usuario para los 9 Reportes Administrativos (Etapa 16).
"""
import streamlit as st

from cafae.planillas import PlanillaService
from cafae.reportes import ReporteService


def render_reportes_view(token, user_role):
    rep_service = ReporteService()
    pln_service = PlanillaService()

    st.title('Reportes Administrativos de Planillas')
    st.write('Consultas y consolidaciones estadísticas por versión exacta de planilla sin mezclar históricos.')

    planillas = pln_service.list_planillas(token)
    if not planillas:
        st.info('No hay planillas registradas para generar reportes.')
        return

    p_map = {p['id']: f"{p['anio']}-{p['mes']:02d} · {p['tipo']} (v{p['version_numero']} - {p['version_estado']})" for p in planillas}
    sel_p_id = st.selectbox('Seleccione Planilla y Periodo de Análisis', list(p_map.keys()), format_func=lambda x: p_map[x], key='sel_rep_pln')

    v_info = pln_service.get_planilla_version(token, sel_p_id)
    v_id = v_info['id']

    tipo_reporte = st.selectbox(
        'Seleccione el Reporte a Consultar',
        [
            '1. Resumen Mensual Consolidado',
            '2. Importe por Institución Educativa',
            '3. Importe por Meta Presupuestaria',
            '4. Descuentos por Entidad Convenio',
            '5. Líquido Neto por Institución / Área',
            '6. Trabajadores por Nivel Educativo',
            '7. Trabajadores por Situación Laboral',
            '8. Detalle de Licencias sin Goce de Haber',
            '9. Comparación Intermensual'
        ]
    )

    st.divider()

    # 1. Resumen Mensual
    if '1. Resumen' in tipo_reporte:
        st.subheader('1. Resumen Mensual Consolidado')
        res = rep_service.reporte_resumen_mensual(token, v_id)
        if res:
            c1, c2, c3, c4 = st.columns(4)
            c1.metric('Total Personal', res['total_personas'])
            c2.metric('Importe Bruto', f"S/ {res['total_importe']:.2f}")
            c3.metric('Total Descuentos', f"S/ {res['total_descuentos']:.2f}")
            c4.metric('Líquido Neto', f"S/ {res['total_neto']:.2f}")

    # 2. Importe por Institución
    elif '2. Importe por Institución' in tipo_reporte:
        st.subheader('2. Importe por Institución Educativa')
        filas = rep_service.reporte_importe_por_institucion(token, v_id)
        st.dataframe([{
            'Cód. Modular': f['codigo_modular'] or '-',
            'Institución Educativa': f['institucion_nombre'],
            'Trabajadores': f['cantidad_trabajadores'],
            'Total Importe': f"S/ {f['total_importe']:.2f}",
            'Total Descuentos': f"S/ {f['total_descuentos']:.2f}",
            'Neto a Pagar': f"S/ {f['total_neto']:.2f}"
        } for f in filas], hide_index=True, use_container_width=True)

    # 3. Importe por Meta
    elif '3. Importe por Meta' in tipo_reporte:
        st.subheader('3. Importe por Meta Presupuestaria')
        filas = rep_service.reporte_importe_por_meta(token, v_id)
        st.dataframe([{
            'Meta': f['meta_codigo'] or 'Sin código',
            'Descripción': f['meta_descripcion'],
            'Trabajadores': f['cantidad_trabajadores'],
            'Total Importe': f"S/ {f['total_importe']:.2f}",
            'Neto': f"S/ {f['total_neto']:.2f}"
        } for f in filas], hide_index=True, use_container_width=True)

    # 4. Descuentos por Entidad
    elif '4. Descuentos por Entidad' in tipo_reporte:
        st.subheader('4. Descuentos por Entidad Convenio (8 Conceptos)')
        filas = rep_service.reporte_descuentos_por_entidad(token, v_id)
        st.dataframe([{
            'Código': f['codigo'],
            'Entidad / Concepto': f['entidad_nombre'],
            'Trabajadores Afectados': f['trabajadores_afectados'],
            'Monto Descontado': f"S/ {f['total_descontado']:.2f}"
        } for f in filas], hide_index=True, use_container_width=True)

    # 5. Neto por Institución
    elif '5. Líquido Neto' in tipo_reporte:
        st.subheader('5. Líquido Neto por Institución / Área')
        filas = rep_service.reporte_neto_por_institucion(token, v_id)
        st.dataframe([{
            'Entidad': f['nombre_entidad'],
            'Personal': f['personas'],
            'Importe': f"S/ {f['importe']:.2f}",
            'Descuentos': f"S/ {f['descuentos']:.2f}",
            'Líquido Neto': f"S/ {f['liquido_neto']:.2f}"
        } for f in filas], hide_index=True, use_container_width=True)

    # 6. Trabajadores por Nivel
    elif '6. Trabajadores por Nivel' in tipo_reporte:
        st.subheader('6. Trabajadores por Nivel Educativo')
        filas = rep_service.reporte_trabajadores_por_nivel(token, v_id)
        st.dataframe([{
            'Nivel Educativo': f['nivel_nombre'],
            'Cantidad Personal': f['total_trabajadores'],
            'Masa Salarial': f"S/ {f['total_importe']:.2f}"
        } for f in filas], hide_index=True, use_container_width=True)

    # 7. Trabajadores por Situación
    elif '7. Trabajadores por Situación' in tipo_reporte:
        st.subheader('7. Trabajadores por Situación Laboral')
        filas = rep_service.reporte_trabajadores_por_situacion(token, v_id)
        st.dataframe([{
            'Situación Laboral': f['situacion_laboral'],
            'Cantidad Personal': f['total_trabajadores'],
            'Masa Salarial': f"S/ {f['total_importe']:.2f}"
        } for f in filas], hide_index=True, use_container_width=True)

    # 8. Licencias sin Goce
    elif '8. Detalle de Licencias' in tipo_reporte:
        st.subheader('8. Detalle de Licencias sin Goce de Haber')
        filas = rep_service.reporte_licencias_sin_goce(token, v_id)
        if not filas:
            st.info('No se registraron licencias sin goce de haber en esta planilla.')
        else:
            st.dataframe([{
                'DNI': f['dni'],
                'Apellidos y Nombres': f"{f['apellidos']}, {f['nombres']}",
                'Adscripción': f['adscripcion'],
                'Importe Base': f"S/ {f['importe']:.2f}",
                'Días Licencia': f['dias_licencia'],
                'Descuento Licencia': f"S/ {f['monto_licencia']:.2f}",
                'Neto Resultante': f"S/ {f['neto']:.2f}"
            } for f in filas], hide_index=True, use_container_width=True)

    # 9. Comparación Intermensual
    elif '9. Comparación' in tipo_reporte:
        st.subheader('9. Comparación Intermensual de Planillas')
        if len(planillas) < 2:
            st.info('Se requieren al menos dos planillas para efectuar la comparación.')
        else:
            c_comp1, c_comp2 = st.columns(2)
            p1_id = c_comp1.selectbox('Planilla Base (Periodo 1)', list(p_map.keys()), index=0)
            p2_id = c_comp2.selectbox('Planilla de Comparación (Periodo 2)', list(p_map.keys()), index=1)

            v1 = pln_service.get_planilla_version(token, p1_id)
            v2 = pln_service.get_planilla_version(token, p2_id)

            filas_comp = rep_service.reporte_comparacion_mensual(token, v1['id'], v2['id'])
            st.dataframe([{
                'Periodo': f"{c['anio']}-{c['mes']:02d}",
                'Tipo': c['tipo'],
                'Versión': f"v{c['numero']}",
                'Personal': c['total_trabajadores'] or 'En edición',
                'Importe Bruto': f"S/ {c['total_importe']:.2f}" if c['total_importe'] else '-',
                'Total Descuentos': f"S/ {c['total_descuentos']:.2f}" if c['total_descuentos'] else '-',
                'Neto Pagado': f"S/ {c['total_neto']:.2f}" if c['total_neto'] else '-'
            } for c in filas_comp], hide_index=True, use_container_width=True)
