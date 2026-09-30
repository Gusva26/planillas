"""Módulo de interfaz de usuario para Importación de Descuentos en Streamlit (Etapa 7).
"""
from decimal import Decimal
import streamlit as st

from cafae.importaciones import ImportacionService
from cafae.planillas import PlanillaService
from cafae.security import UserError

TIPOS_DESCUENTO_OPTS = {
    1: '1. Pichincha',
    2: '2. Caja Sullana',
    3: '3. Sub-CAFAE',
    4: '4. Convenio BRENTA',
    5: '5. SITRASE',
    6: '6. SITASE / FENTASE',
    7: '7. Otros Descuentos'
}


def render_importaciones_view(token, user_role):
    imp_service = ImportacionService()
    pln_service = PlanillaService()
    puede_editar = (user_role in ('ADMINISTRADOR', 'PLANILLAS'))

    st.title('Importación de Descuentos')
    st.write('Extracción y aplicación masiva de descuentos por planilla mediante archivos Excel.')

    if not puede_editar:
        st.warning('No tiene permisos para importar o aplicar descuentos.')
        return

    # 1. Seleccionar Planilla Abierta
    planillas = pln_service.list_planillas(token)
    planillas_abiertas = [p for p in planillas if p['version_estado'] != 'CERRADA']

    if not planillas_abiertas:
        st.info('No hay planillas en estado BORRADOR o EN REVISIÓN. Cree o reabra una planilla para importar descuentos.')
        return

    p_map = {p['id']: f"{p['anio']}-{p['mes']:02d} · {p['tipo']} (v{p['version_numero']})" for p in planillas_abiertas}
    sel_p_id = st.selectbox('Seleccione Planilla Destino', list(p_map.keys()), format_func=lambda x: p_map[x], key='sel_pln_imp')

    v_info = pln_service.get_planilla_version(token, sel_p_id)
    v_id = v_info['id']

    st.divider()

    # Formulario de carga
    st.subheader('1. Subir Archivo de Descuentos')
    c1, c2 = st.columns([1, 2])
    sel_tipo_desc = c1.selectbox('Concepto de Descuento', list(TIPOS_DESCUENTO_OPTS.keys()), format_func=lambda x: TIPOS_DESCUENTO_OPTS[x])
    archivo_subido = c2.file_uploader('Seleccione archivo Excel (.xlsx, .xls)', type=['xlsx', 'xls'])

    if archivo_subido is not None:
        if st.button('Procesar y Extraer Archivo', type='primary'):
            bytes_data = archivo_subido.getvalue()
            res = imp_service.procesar_archivo_importacion(
                token, v_id, sel_tipo_desc, archivo_subido.name, bytes_data
            )
            st.session_state['current_importacion_id'] = res['importacion_id']
            st.success(f'Archivo procesado exitosamente. Se detectaron {res["registros_detectados"]} registros.')
            st.rerun()

    # Si hay una importación procesada en sesión
    imp_id = st.session_state.get('current_importacion_id')
    if imp_id:
        resumen = imp_service.get_resumen_importacion(token, imp_id)
        if not resumen:
            return

        st.divider()
        st.subheader(f'2. Previsualización y Clasificación ({resumen["tipo_descuento_nombre"]})')
        st.caption(f'Archivo: `{resumen["archivo_nombre"]}` · Estado: `{resumen["estado"]}`')

        # Tarjetas de resumen
        filas = imp_service.list_filas_importacion(token, imp_id)
        total_det = len(filas)
        identificados = len([f for f in filas if f['estado'] == 'IDENTIFICADO'])
        revisar = len([f for f in filas if f['estado'] == 'REVISAR'])
        no_encontrados = len([f for f in filas if f['estado'] == 'NO_ENCONTRADO'])
        duplicados = len([f for f in filas if f['estado'] == 'DNI_DUPLICADO'])
        invalidos = len([f for f in filas if f['estado'] == 'MONTO_INVALIDO'])

        seleccionadas = [f for f in filas if f['seleccionado']]
        total_monto_sel = sum(f['monto_validado'] for f in seleccionadas if f['monto_validado'])

        m1, m2, m3, m4, m5, m6 = st.columns(6)
        m1.metric('Total Detectados', total_det)
        m2.metric('Identificados', identificados)
        m3.metric('Por Revisar', revisar)
        m4.metric('No Encontrados', no_encontrados)
        m5.metric('DNI Duplicados', duplicados)
        m6.metric('Monto Seleccionado', f"S/ {total_monto_sel:.2f}")

        # Filtro por estado para la tabla
        filtro_est = st.selectbox(
            'Filtrar tabla por estado',
            ['TODOS', 'IDENTIFICADO', 'REVISAR', 'DNI_DUPLICADO', 'NO_ENCONTRADO', 'MONTO_INVALIDO']
        )
        filas_mostrar = imp_service.list_filas_importacion(token, imp_id, estado_filtro=filtro_est)

        st.dataframe([{
            'Fila': f['fila'],
            'DNI Original': f['dni_original'],
            'DNI Normalizado': f['dni_normalizado'] or '-',
            'Nombre en Archivo': f['nombre_original'] or '-',
            'Trabajador en Planilla': f"{f['trabajador_apellidos']}, {f['trabajador_nombres']}" if f['trabajador_apellidos'] else '-',
            'Monto': f"S/ {f['monto_validado']:.2f}" if f['monto_validado'] else f['monto_original'],
            'Estado': f['estado'],
            'Seleccionado': '✅ SÍ' if f['seleccionado'] else '❌ NO',
            'Observación': f['observacion'] or '-'
        } for f in filas_mostrar], hide_index=True, use_container_width=True)

        if resumen['estado'] != 'APLICADA':
            st.divider()
            st.subheader('3. Aplicación a la Planilla')

            c_mod1, c_mod2 = st.columns(2)
            modo_aplicacion = c_mod1.radio(
                'Modalidad de Aplicación',
                [
                    'ACTUALIZAR: Aplicar solo a los seleccionados y conservar los montos de otros trabajadores',
                    'REEMPLAZAR: Poner este concepto a cero para todos y aplicar únicamente los seleccionados'
                ]
            )
            modo_codigo = 'REEMPLAZAR' if 'REEMPLAZAR' in modo_aplicacion else 'ACTUALIZAR'

            c_mod2.info(f'Se aplicarán {len(seleccionadas)} registros seleccionados por un monto total de S/ {total_monto_sel:.2f}.')

            with st.form('form_aplicar_descuentos'):
                confirma_ap = st.checkbox(f'Confirmo la aplicación de descuentos en modalidad {modo_codigo}')
                btn_aplicar = st.form_submit_button('Aplicar Descuentos a la Planilla', type='primary')

            if btn_aplicar:
                if not confirma_ap:
                    st.error('Debe confirmar antes de aplicar.')
                else:
                    res_ap = imp_service.aplicar_importacion(
                        token, imp_id, modo=modo_codigo, revision_esperada=v_info['revision_edicion']
                    )
                    st.success(
                        f'¡Descuentos aplicados con éxito! ({res_ap["registros_aplicados"]} trabajadores actualizados por S/ {res_ap["total_aplicado"]:.2f}).'
                    )
                    st.session_state.pop('current_importacion_id', None)
                    st.rerun()
        else:
            st.success('Esta importación ya fue APLICADA a la versión correspondiente.')
