"""Módulo de interfaz de usuario para Planillas CAFAE (Creación, Edición mensual, Cierre e Historial).
"""
from datetime import datetime
from decimal import Decimal
from zoneinfo import ZoneInfo
import streamlit as st

from cafae.calculos import CONCEPTOS_DESCUENTO, a_decimal, calcular_licencia
from cafae.catalogos import CatalogoService
from cafae.planillas import PlanillaService
from cafae.security import UserError


def render_planillas_view(token, user_role):
    pln_service = PlanillaService()
    cat_service = CatalogoService()
    es_admin = (user_role == 'ADMINISTRADOR')
    puede_editar = (user_role in ('ADMINISTRADOR', 'PLANILLAS'))

    st.title('Gestión de Planillas CAFAE')
    st.write('Administración del ciclo de vida mensual: creación, edición de personal y descuentos, revisión, cierre e historial.')

    # Menú de contexto de planillas
    sub_seccion = st.radio(
        'Sección',
        ['📋 Listado de Planillas', '➕ Crear / Copiar Planilla', '📝 Editor de Planilla', '🔒 Cierre y Reapertura'],
        horizontal=True
    )

    # =========================================================================
    # 1. LISTADO DE PLANILLAS
    # =========================================================================
    if sub_seccion == '📋 Listado de Planillas':
        st.subheader('Planillas Registradas')
        col_f1, col_f2 = st.columns(2)
        f_tipo = col_f1.selectbox('Filtrar por tipo', ['Todos', 'IIEE', 'SEDE'])
        f_anio = col_f2.number_input('Año', min_value=2020, max_value=2030, value=datetime.now(ZoneInfo('America/Lima')).year)

        planillas = pln_service.list_planillas(
            token, anio=f_anio, tipo=None if f_tipo == 'Todos' else f_tipo
        )

        if not planillas:
            st.info('No se encontraron planillas para los filtros seleccionados. Puede crear una nueva desde la pestaña "Crear / Copiar Planilla".')
        else:
            tabla_p = []
            for p in planillas:
                estado_badge = '🟢 CERRADA' if p['version_estado'] == 'CERRADA' else ('🟡 EN REVISIÓN' if p['version_estado'] == 'EN_REVISION' else '⚪ BORRADOR')
                imp_str = f"S/ {p['total_importe']:.2f}" if p['total_importe'] is not None else 'En edición'
                desc_str = f"S/ {p['total_descuentos']:.2f}" if p['total_descuentos'] is not None else 'En edición'
                neto_str = f"S/ {p['total_neto']:.2f}" if p['total_neto'] is not None else 'En edición'
                tabla_p.append({
                    'ID': p['id'],
                    'Periodo': f"{p['anio']}-{p['mes']:02d}",
                    'Tipo': p['tipo'],
                    'Versión Actual': f"v{p['version_numero']} ({estado_badge})",
                    'Trabajadores': p['total_trabajadores'] or 'En edición',
                    'Total Importe': imp_str,
                    'Total Descuentos': desc_str,
                    'Líquido Neto': neto_str,
                    'Última Modificación / Cierre': p['cerrada_en'].strftime('%d/%m/%Y %H:%M') if p['cerrada_en'] else '-'
                })
            st.dataframe(tabla_p, hide_index=True, use_container_width=True)

            st.write('**Acceso Rápido al Editor:**')
            p_map = {p['id']: f"{p['anio']}-{p['mes']:02d} · {p['tipo']} (v{p['version_numero']})" for p in planillas}
            sel_p_id = st.selectbox('Seleccione una planilla para abrir en el editor', list(p_map.keys()), format_func=lambda x: p_map[x])
            if st.button('Abrir en el Editor de Planilla', type='primary'):
                st.session_state['editor_planilla_id'] = sel_p_id
                st.session_state['aviso'] = f'Abierta planilla {p_map[sel_p_id]}.'
                st.rerun()

    # =========================================================================
    # 2. CREAR / COPIAR PLANILLA
    # =========================================================================
    elif sub_seccion == '➕ Crear / Copiar Planilla':
        if not puede_editar:
            st.warning('No tiene permisos para crear planillas.')
        else:
            st.subheader('Creación de Nueva Planilla Mensual')
            st.write('Seleccione el periodo, ámbito y la modalidad de generación.')

            with st.form('form_crear_planilla'):
                c1, c2, c3 = st.columns(3)
                p_anio = c1.number_input('Año', min_value=2020, max_value=2030, value=datetime.now(ZoneInfo('America/Lima')).year)
                p_mes = c2.selectbox('Mes', list(range(1, 13)), format_func=lambda m: f"{m:02d} - {['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Setiembre', 'Octubre', 'Noviembre', 'Diciembre'][m-1]}", index=datetime.now(ZoneInfo('America/Lima')).month - 1)
                p_tipo = c3.selectbox('Tipo de Planilla', ['IIEE', 'SEDE'])

                modalidad = st.radio(
                    'Modalidad de Carga Inicial',
                    [
                        'Cargar desde Maestro de Personal (Solo personal activo, descuentos en cero)',
                        'Copiar desde el Mes Anterior (Copia fiel de trabajadores y descuentos vigentes)'
                    ]
                )

                if 'Copiar' in modalidad:
                    st.info('Se copiará íntegramente la versión cerrada del mes inmediatamente anterior. Las licencias sin goce se iniciarán en cero.')

                btn_crear = st.form_submit_button('Crear Planilla', type='primary')

            if btn_crear:
                if 'Maestro' in modalidad:
                    res = pln_service.crear_desde_maestro(token, p_anio, p_mes, p_tipo)
                    st.success(f'Planilla de {p_tipo} creada exitosamente con {res["trabajadores_copiados"]} trabajadores activos.')
                    st.session_state['editor_planilla_id'] = res['planilla_id']
                    st.rerun()
                else:
                    res = pln_service.copiar_mes_anterior(token, p_anio, p_mes, p_tipo)
                    st.success(f'Planilla de {p_tipo} generada por copia con {res["trabajadores_copiados"]} trabajadores.')
                    st.session_state['editor_planilla_id'] = res['planilla_id']
                    st.rerun()

    # =========================================================================
    # 3. EDITOR DE PLANILLA
    # =========================================================================
    elif sub_seccion == '📝 Editor de Planilla':
        st.subheader('Editor de Planilla Mensual')
        planillas_disp = pln_service.list_planillas(token)
        if not planillas_disp:
            st.info('No hay planillas registradas. Cree una nueva para comenzar.')
            return

        p_opts = {p['id']: f"{p['anio']}-{p['mes']:02d} · {p['tipo']} (v{p['version_numero']})" for p in planillas_disp}
        cur_sel = st.session_state.get('editor_planilla_id', list(p_opts.keys())[0])
        if cur_sel not in p_opts:
            cur_sel = list(p_opts.keys())[0]

        sel_p_id = st.selectbox('Seleccionar Planilla en Edición', list(p_opts.keys()), index=list(p_opts.keys()).index(cur_sel), format_func=lambda x: p_opts[x])
        st.session_state['editor_planilla_id'] = sel_p_id

        # Obtener versión activa
        v_info = pln_service.get_planilla_version(token, sel_p_id)
        if not v_info:
            st.error('No se pudo cargar la versión de la planilla.')
            return

        v_id = v_info['id']
        estado = v_info['estado']
        es_cerrada = (estado == 'CERRADA')

        # Tarjetas de estado
        col_st1, col_st2, col_st3, col_st4 = st.columns(4)
        col_st1.metric('Periodo / Tipo', f"{v_info['anio']}-{v_info['mes']:02d} ({v_info['tipo']})")
        col_st2.metric('Versión', f"v{v_info['numero']} ({v_info['origen']})")
        col_st3.metric('Estado Actual', estado)
        col_st4.metric('Revisión Concurrente', v_info['revision_edicion'])

        if es_cerrada:
            st.info('Esta versión está CERRADA e inmutable. Los datos se muestran en modo solo lectura.')

        # Cargar detalle completo
        filas = pln_service.get_detalle_version(token, v_id)

        # Métricas consolidadas en tiempo real
        tot_imp = sum(f['importe'] for f in filas)
        tot_lic = sum(f['monto_licencia'] for f in filas)
        tot_desc = sum(f['total_descuentos'] for f in filas)
        tot_neto = sum(f['neto'] for f in filas)
        netos_negativos = [f for f in filas if f['neto'] < Decimal('0.00')]

        m1, m2, m3, m4, m5 = st.columns(5)
        m1.metric('Trabajadores', len(filas))
        m2.metric('Total Importe', f"S/ {tot_imp:.2f}")
        m3.metric('Total Licencias', f"S/ {tot_lic:.2f}")
        m4.metric('Total Descuentos', f"S/ {tot_desc:.2f}")
        m5.metric('Líquido Neto Total', f"S/ {tot_neto:.2f}")

        if netos_negativos:
            st.warning(f'⚠️ Atención: Hay {len(netos_negativos)} trabajador(es) con líquido neto NEGATIVO. Esto debe corregirse antes de proceder al cierre.')

        # Filtros de visualización
        col_bq1, col_bq2 = st.columns([2, 1])
        q_filtro = col_bq1.text_input('Buscar en la planilla (DNI, nombres, apellidos)', key='q_ed_plan')
        filas_visibles = [f for f in filas if not q_filtro or (q_filtro.lower() in f['dni'].lower() or q_filtro.lower() in f['apellidos'].lower() or q_filtro.lower() in f['nombres'].lower())]

        st.caption(f'Mostrando {len(filas_visibles)} de {len(filas)} trabajadores.')

        # Acciones de lote
        if puede_editar and not es_cerrada:
            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                if estado == 'BORRADOR':
                    if st.button('Enviar a Revisión'):
                        pln_service.cambiar_estado(token, v_id, 'EN_REVISION')
                        st.success('Planilla marcada EN REVISIÓN.')
                        st.rerun()
                else:
                    if st.button('Regresar a Borrador'):
                        pln_service.cambiar_estado(token, v_id, 'BORRADOR')
                        st.success('Planilla regresada a BORRADOR.')
                        st.rerun()

            with col_b2:
                if st.button('Limpiar Todos los Descuentos', type='secondary'):
                    st.session_state['confirmar_limpieza'] = True

            if st.session_state.get('confirmar_limpieza'):
                st.warning('¿Confirma poner a S/ 0.00 todos los descuentos y licencias de esta planilla? Los importes se mantendrán.')
                col_c1, col_c2 = st.columns(2)
                if col_c1.button('Sí, Limpiar Descuentos', type='primary'):
                    pln_service.limpiar_todos_descuentos(token, v_id, v_info['revision_edicion'])
                    st.session_state['confirmar_limpieza'] = False
                    st.success('Descuentos limpiados.')
                    st.rerun()
                if col_c2.button('Cancelar'):
                    st.session_state['confirmar_limpieza'] = False
                    st.rerun()

        # Tabla de edición o consulta
        st.write('**Detalle de Personal y Descuentos:**')
        tabla_vis = []
        for f in filas_visibles:
            tabla_vis.append({
                'ID': f['id'],
                'DNI': f['dni'],
                'Apellidos y Nombres': f"{f['apellidos']}, {f['nombres']}",
                'Adscripción': f['institucion_nombre'] or f['area_nombre'] or '-',
                'Importe Base': f"S/ {f['importe']:.2f}",
                'Días Lic.': f['dias_licencia'],
                'Monto Lic.': f"S/ {f['monto_licencia']:.2f}",
                'Pichincha': f"S/ {f['pichincha']:.2f}",
                'Caja Sullana': f"S/ {f['caja_sullana']:.2f}",
                'Sub-CAFAE': f"S/ {f['sub_cafae']:.2f}",
                'BRENTA': f"S/ {f['brenta']:.2f}",
                'SITRASE': f"S/ {f['sitrase']:.2f}",
                'SITASE/FENTASE': f"S/ {f['sitase_fentase']:.2f}",
                'Otros': f"S/ {f['otros']:.2f}",
                'Total Descuentos': f"S/ {f['total_descuentos']:.2f}",
                'Líquido Neto': f"S/ {f['neto']:.2f}"
            })
        st.dataframe(tabla_vis, hide_index=True, use_container_width=True)

        # Formulario de modificación individual rápida
        if puede_editar and not es_cerrada and filas_visibles:
            st.divider()
            st.write('**Edición de Fila Individual:**')
            f_map = {f['id']: f"{f['dni']} - {f['apellidos']}, {f['nombres']}" for f in filas_visibles}
            sel_row_id = st.selectbox('Seleccione trabajador para editar montos', list(f_map.keys()), format_func=lambda x: f_map[x], key='sel_fila_editar')
            row_cur = next(f for f in filas if f['id'] == sel_row_id)

            with st.form(f'form_ed_row_{sel_row_id}'):
                ce1, ce2, ce3 = st.columns(3)
                ed_imp = ce1.text_input('Importe Base (S/)', value=str(row_cur['importe']))
                ed_dias = ce2.number_input('Días de Licencia (0-30)', min_value=0, max_value=30, value=int(row_cur['dias_licencia']), step=1)
                ed_pich = ce3.text_input('Pichincha (S/)', value=str(row_cur['pichincha']))

                ce4, ce5, ce6 = st.columns(3)
                ed_sull = ce4.text_input('Caja Sullana (S/)', value=str(row_cur['caja_sullana']))
                ed_subc = ce5.text_input('Sub-CAFAE (S/)', value=str(row_cur['sub_cafae']))
                ed_bren = ce6.text_input('Convenio BRENTA (S/)', value=str(row_cur['brenta']))

                ce7, ce8, ce9 = st.columns(3)
                ed_sitr = ce7.text_input('SITRASE (S/)', value=str(row_cur['sitrase']))
                ed_fent = ce8.text_input('SITASE / FENTASE (S/)', value=str(row_cur['sitase_fentase']))
                ed_otro = ce9.text_input('Otros Descuentos (S/)', value=str(row_cur['otros']))

                if st.form_submit_button('Guardar Cambios de este Trabajador', type='primary'):
                    cambios = [{
                        'detalle_id': sel_row_id,
                        'importe': a_decimal(ed_imp),
                        'dias_licencia': int(ed_dias),
                        'PICHINCHA': a_decimal(ed_pich),
                        'CAJA_SULLANA': a_decimal(ed_sull),
                        'SUB_CAFAE': a_decimal(ed_subc),
                        'BRENTA': a_decimal(ed_bren),
                        'SITRASE': a_decimal(ed_sitr),
                        'SITASE_FENTASE': a_decimal(ed_fent),
                        'OTROS': a_decimal(ed_otro)
                    }]
                    pln_service.guardar_edicion_lote(token, v_id, v_info['revision_edicion'], cambios)
                    st.success('Cambios guardados exitosamente.')
                    st.rerun()

    # =========================================================================
    # 4. CIERRE Y REAPERTURA
    # =========================================================================
    elif sub_seccion == '🔒 Cierre y Reapertura':
        st.subheader('Cierre Formal y Reapertura de Planillas')
        planillas_disp = pln_service.list_planillas(token)
        if not planillas_disp:
            st.info('No hay planillas registradas.')
            return

        p_opts = {p['id']: f"{p['anio']}-{p['mes']:02d} · {p['tipo']} (v{p['version_numero']})" for p in planillas_disp}
        sel_p_id = st.selectbox('Seleccione Planilla', list(p_opts.keys()), format_func=lambda x: p_opts[x], key='sel_pln_cierre')

        v_info = pln_service.get_planilla_version(token, sel_p_id)
        v_id = v_info['id']
        estado = v_info['estado']
        tipo = v_info['tipo']
        cant_firmas_req = v_info['cantidad_firmas']

        st.write(f'**Estado Actual:** `{estado}` | **Tipo:** `{tipo}` | **Firmas Requeridas:** `{cant_firmas_req}`')

        if estado != 'CERRADA':
            st.write('### 🔒 Procedimiento de Cierre')
            if not es_admin:
                st.warning('Solo un usuario con rol ADMINISTRADOR puede realizar el cierre formal de planillas.')
            else:
                filas = pln_service.get_detalle_version(token, v_id)
                netos_negativos = [f for f in filas if f['neto'] < Decimal('0.00')]
                if netos_negativos:
                    st.error(f'Imposible cerrar: existen {len(netos_negativos)} trabajador(es) con líquido neto negativo.')
                else:
                    st.info(f'Para cerrar la planilla de {tipo}, seleccione exactamente las {cant_firmas_req} firmas institucionales correspondientes:')
                    firmas_disponibles = cat_service.list_firmas(token, solo_activas=True)
                    f_opts = {f['id']: f"{f['nombre_completo']} ({f['cargo']})" for f in firmas_disponibles}

                    firmas_seleccionadas = []
                    c_cols = st.columns(cant_firmas_req)
                    for idx in range(cant_firmas_req):
                        def_idx = idx if idx < len(firmas_disponibles) else 0
                        sel_f = c_cols[idx].selectbox(f'Firma Posición {idx+1}', list(f_opts.keys()), index=def_idx, format_func=lambda x: f_opts[x], key=f'firma_cierre_{idx}')
                        firmas_seleccionadas.append(sel_f)

                    if len(set(firmas_seleccionadas)) != cant_firmas_req:
                        st.warning('Atención: Hay firmas repetidas en la selección.')

                    with st.form('form_cierre_formal'):
                        st.write('Al confirmar el cierre, la versión pasará a estado CERRADA, sus montos serán inmutables y quedará habilitada para emisión de documentos oficiales.')
                        confirma = st.checkbox('Confirmo que he revisado la conciliación y los cálculos de esta planilla')
                        btn_cerrar = st.form_submit_button('Cerrar Planilla Definitivamente', type='primary')

                    if btn_cerrar:
                        if not confirma:
                            st.error('Debe confirmar la revisión antes de cerrar.')
                        else:
                            pln_service.cerrar_version(token, v_id, v_info['revision_edicion'], firmas_seleccionadas)
                            st.success('¡Planilla cerrada exitosamente! Totales inmutables registrados.')
                            st.rerun()
        else:
            st.write('### 🔓 Reapertura de Planilla')
            st.success(f'Esta planilla fue cerrada el {v_info["cerrada_en"].strftime("%d/%m/%Y a las %H:%M")}.')
            if not es_admin:
                st.info('Solo un ADMINISTRADOR puede solicitar la reapertura de una planilla cerrada.')
            else:
                st.write('La reapertura generará una **nueva versión (v' + str(v_info['numero'] + 1) + ')** en modo borrador con copia fiel, dejando la versión actual cerrada e intacta.')
                with st.form('form_reapertura'):
                    motivo = st.text_area('Motivo Justificado de Reapertura (Obligatorio)', max_chars=500)
                    btn_reabrir = st.form_submit_button('Confirmar y Crear Nueva Versión Editable', type='primary')

                if btn_reabrir:
                    res = pln_service.reabrir_version(token, v_id, motivo)
                    st.success(f'Reapertura completada: Creada versión {res["nuevo_numero"]} con {res["filas_copiadas"]} trabajadores.')
                    st.rerun()

        # Historial de versiones
        st.divider()
        st.write('**Historial de Versiones de esta Planilla:**')
        versiones = pln_service.list_versiones_planilla(token, sel_p_id)
        st.dataframe([{
            'Versión': f"v{v['numero']}",
            'Estado': v['estado'],
            'Origen': v['origen'],
            'Motivo Reapertura': v['motivo_reapertura'] or '-',
            'Trabajadores': v['total_trabajadores'] or 'En edición',
            'Total Neto': f"S/ {v['total_neto']:.2f}" if v['total_neto'] is not None else '-',
            'Creada Por': v['creada_por_nombre'],
            'Fecha Creación': v['creada_en'].strftime('%d/%m/%Y %H:%M'),
            'Cerrada Por': v['cerrada_por_nombre'] or '-'
        } for v in versiones], hide_index=True, use_container_width=True)
