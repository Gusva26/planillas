"""Módulo de interfaz de usuario para Emisión y Descarga de Documentos Oficiales (Etapas 9 a 14).
"""
import streamlit as st

from cafae.catalogos import CatalogoService
from cafae.documentos.boletas import generar_boleta_pdf, generar_cuadernillo_boletas_pdf
from cafae.documentos.excel_planillas import generar_excel_planilla
from cafae.documentos.pdf_planillas import generar_pdf_planilla
from cafae.documentos.remuneraciones import generar_excel_remuneraciones
from cafae.planillas import PlanillaService


def render_documentos_view(token, user_role):
    pln_service = PlanillaService()
    cat_service = CatalogoService()

    st.title('Emisión de Documentos Oficiales')
    st.write('Generación y descarga de Planillas (PDF/Excel), Boletas de Pago, Hojas de Remuneraciones y Archivos Bancarios.')

    planillas = pln_service.list_planillas(token)
    if not planillas:
        st.info('No hay planillas registradas en el sistema.')
        return

    # Selector de planilla
    p_map = {p['id']: f"{p['anio']}-{p['mes']:02d} · {p['tipo']} (v{p['version_numero']} - {p['version_estado']})" for p in planillas}
    sel_p_id = st.selectbox('Seleccione Planilla', list(p_map.keys()), format_func=lambda x: p_map[x], key='sel_doc_pln')

    v_info = pln_service.get_planilla_version(token, sel_p_id)
    v_id = v_info['id']
    es_cerrada = (v_info['estado'] == 'CERRADA')

    if not es_cerrada:
        st.warning('⚠️ Esta planilla se encuentra en estado ABIERTO (Borrador / Revisión). Los documentos generados tendrán carácter preliminar de trabajo.')
    else:
        st.success(f'🔒 Versión CERRADA el {v_info["cerrada_en"].strftime("%d/%m/%Y a las %H:%M")}. Los documentos emitidos son oficiales e inmutables.')

    filas = pln_service.get_detalle_version(token, v_id)
    firmas = cat_service.list_firmas(token, solo_activas=True)
    cant_req = v_info['cantidad_firmas']
    firmas_doc = firmas[:cant_req]

    tab_pln, tab_bol, tab_rem, tab_txt = st.tabs([
        '📄 Planilla Oficial (PDF / Excel)',
        '📑 Boletas de Pago',
        '📊 Hoja de Remuneraciones',
        '🏦 Archivo Bancario (TXT)'
    ])

    # =========================================================================
    # TAB 1: PLANILLA OFICIAL (PDF / EXCEL)
    # =========================================================================
    with tab_pln:
        st.subheader('Planilla Oficial de Pagos')
        st.caption(f'Formato horizontal A4 con 8 conceptos de descuento, ordenanzas institucionales y bloque final de firmas ({cant_req} firmas para {v_info["tipo"]}).')

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            st.write('**Formato PDF Institucional:**')
            pdf_bytes = generar_pdf_planilla(v_info, filas, firmas_doc)
            nombre_pdf = f"Planilla_CAFAE_{v_info['tipo']}_{v_info['anio']}_{v_info['mes']:02d}_v{v_info['numero']}.pdf"
            st.download_button(
                label='📥 Descargar Planilla en PDF (A4)',
                data=pdf_bytes,
                file_name=nombre_pdf,
                mime='application/pdf',
                type='primary',
                use_container_width=True
            )

        with col_d2:
            st.write('**Formato Excel Oficial (.xlsx):**')
            xlsx_bytes = generar_excel_planilla(v_info, filas, firmas_doc)
            nombre_xlsx = f"Planilla_CAFAE_{v_info['tipo']}_{v_info['anio']}_{v_info['mes']:02d}_v{v_info['numero']}.xlsx"
            st.download_button(
                label='📥 Descargar Planilla en Excel (.xlsx)',
                data=xlsx_bytes,
                file_name=nombre_xlsx,
                mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                use_container_width=True
            )

    # =========================================================================
    # TAB 2: BOLETAS DE PAGO
    # =========================================================================
    with tab_bol:
        st.subheader('Boletas de Pago CAFAE')
        st.caption('Emisión con logo oficial, datos laborales consolidados, único ingreso y los 8 conceptos de descuento.')

        st.write('**1. Cuadernillo Mensual Completo (Todas las Boletas en un solo PDF):**')
        cuadernillo_bytes = generar_cuadernillo_boletas_pdf(filas, v_info)
        nom_cuad = f"Boletas_CAFAE_{v_info['tipo']}_{v_info['anio']}_{v_info['mes']:02d}.pdf"
        st.download_button(
            label=f'📥 Descargar Cuadernillo Completo ({len(filas)} Boletas en PDF)',
            data=cuadernillo_bytes,
            file_name=nom_cuad,
            mime='application/pdf',
            type='primary'
        )

        st.divider()
        st.write('**2. Boleta Individual por Trabajador:**')
        f_map = {f['id']: f"{f['dni']} - {f['apellidos']}, {f['nombres']}" for f in filas}
        sel_t_id = st.selectbox('Seleccione Trabajador para emitir boleta individual', list(f_map.keys()), format_func=lambda x: f_map[x])
        trab_row = next(f for f in filas if f['id'] == sel_t_id)

        boleta_ind_bytes = generar_boleta_pdf(trab_row, v_info)
        nom_ind = f"Boleta_CAFAE_{trab_row['dni']}_{v_info['anio']}_{v_info['mes']:02d}.pdf"
        st.download_button(
            label=f'📥 Descargar Boleta Individual de {trab_row["apellidos"]}',
            data=boleta_ind_bytes,
            file_name=nom_ind,
            mime='application/pdf'
        )

    # =========================================================================
    # TAB 3: HOJA DE REMUNERACIONES
    # =========================================================================
    with tab_rem:
        st.subheader('Hoja de Trabajo de Remuneraciones')
        st.caption('Agrupación presupuestaria por metas, programas y partidas, consolidando exclusivamente el importe bruto.')

        rem_bytes = generar_excel_remuneraciones(v_info, filas)
        nom_rem = f"Hoja_Remuneraciones_CAFAE_{v_info['tipo']}_{v_info['anio']}_{v_info['mes']:02d}.xlsx"
        st.download_button(
            label='📥 Descargar Hoja de Remuneraciones en Excel (.xlsx)',
            data=rem_bytes,
            file_name=nom_rem,
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            type='primary'
        )

    # =========================================================================
    # TAB 4: ARCHIVO BANCARIO (TXT)
    # =========================================================================
    with tab_txt:
        st.subheader('Generador de Archivo Bancario (TXT - Banco de la Nación)')
        st.info("""
        **ESTADO DE LA INTEGRACIÓN BANCARIA (DECISIÓN CONFIRMADA 4.5):**

        La generación del archivo de abono bancario está **bloqueada de forma transparente y preventiva** conforme a las directrices del proyecto:
        - Las muestras de las hojas «DX PARA TXT» y «GENERADOR TXT» contenían fórmulas inconsistentes, notación científica y pasos manuales no estandarizados.
        - Para certificar un archivo bancario oficial sin riesgo de dispersión errónea o rechazo bancario de pagos, se requiere la especificación técnica oficial o un archivo TXT real aceptado por el Banco de la Nación (estructura de cabecera, longitudes, rellenos de ceros, separadores y checksum).
        - La aplicación no genera archivos bancarios provisionales no certificados.
        """)
        st.caption('Tan pronto como la entidad bancaria o la administración proporcione la estructura certificada, el servicio bancario validará y emitirá el archivo byte a byte.')
