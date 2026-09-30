"""Módulo de interfaz de usuario para la gestión de catálogos institucionales.
Permite a los usuarios consultar y al Administrador crear y editar catálogos.
"""
import streamlit as st
from cafae.catalogos import CatalogoService
from cafae.security import UserError


def render_catalogos_view(token, user_role):
    catalogo_service = CatalogoService()
    es_admin = (user_role == 'ADMINISTRADOR')

    st.title('Configuración y Catálogos')
    st.write('Gestión centralizada de instituciones, áreas, metas, jerarquías presupuestarias y parámetros.')

    if not es_admin:
        st.info('Modo consulta: Visualización de catálogos autorizados. La edición está reservada al Administrador.')

    tab_inst, tab_areas, tab_niveles_metas, tab_presupuesto, tab_personal, tab_firmas, tab_identidad = st.tabs([
        '🏫 Instituciones',
        '🏢 Áreas de Sede',
        '🎯 Niveles y Metas',
        '📊 Programas y Partidas',
        '👥 Personal (Cargos/Cat.)',
        '✍️ Firmas',
        '⚙️ Identidad'
    ])

    # =========================================================================
    # TAB 1: INSTITUCIONES
    # =========================================================================
    with tab_inst:
        st.subheader('Instituciones Educativas')
        col_f1, col_f2, col_f3 = st.columns([2, 1, 1])
        q_inst = col_f1.text_input('Buscar por nombre, código modular o distrito', key='q_inst')
        niveles = catalogo_service.list_niveles(token, solo_activos=False)
        niv_options = {0: 'Todos los niveles'} | {n['id']: n['nombre'] for n in niveles}
        sel_nivel = col_f2.selectbox('Filtrar por nivel', list(niv_options.keys()), format_func=lambda x: niv_options[x], key='filtro_nivel_inst')
        solo_act = col_f3.checkbox('Solo activas', value=False, key='chk_inst_activas')

        instituciones = catalogo_service.list_instituciones(
            token, solo_activas=solo_act, query=q_inst, nivel_id=sel_nivel if sel_nivel != 0 else None
        )

        st.caption(f'Total encontradas: {len(instituciones)}')
        tabla_inst = []
        for i in instituciones:
            meta_desc = f"{i['meta_codigo']} (Propia)" if i['meta_codigo'] else (f"{i['nivel_meta_codigo']} (Del Nivel)" if i['nivel_meta_codigo'] else 'Sin asignar')
            tabla_inst.append({
                'ID': i['id'],
                'Cód. Modular': i['codigo_modular'],
                'Nombre Institución': i['nombre'],
                'Nivel': i['nivel_nombre'],
                'Distrito': i['distrito'],
                'Meta Resuelta': meta_desc,
                'Estado': 'Activa' if i['activo'] else 'Inactiva'
            })
        st.dataframe(tabla_inst, hide_index=True, use_container_width=True)

        if es_admin:
            st.divider()
            t_crear_i, t_editar_i = st.tabs(['Nueva Institución', 'Modificar Institución'])
            with t_crear_i:
                with st.form('form_crear_inst', clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    c_mod = c1.text_input('Código Modular (ej. 0012345)', max_chars=30)
                    c_nom = c2.text_input('Nombre de la Institución', max_chars=240)
                    c3, c4 = st.columns(2)
                    niv_activos = [n for n in niveles if n['activo']]
                    if not niv_activos:
                        st.warning('Debe registrar al menos un nivel educativo activo antes de crear instituciones.')
                    sel_n = c3.selectbox('Nivel Educativo', [n['id'] for n in niv_activos], format_func=lambda x: next(n['nombre'] for n in niv_activos if n['id'] == x) if niv_activos else '')
                    c_dist = c4.text_input('Distrito', value='Chepén', max_chars=120)

                    metas = catalogo_service.list_metas(token, solo_activos=True)
                    meta_opts = {0: 'Heredar del Nivel Educativo'} | {m['id']: f"{m['codigo']} - {m['descripcion'][:60]}" for m in metas}
                    sel_m = st.selectbox('Meta Presupuestaria Específica (Opcional)', list(meta_opts.keys()), format_func=lambda x: meta_opts[x])
                    c_obs = st.text_area('Observaciones', max_chars=500)
                    btn_crear = st.form_submit_button('Registrar Institución', type='primary')

                if btn_crear:
                    if not niv_activos:
                        st.error('No hay niveles educativos activos disponibles.')
                    else:
                        m_id = sel_m if sel_m != 0 else None
                        catalogo_service.create_institucion(token, c_mod, c_nom, sel_n, c_dist, m_id, c_obs)
                        st.success(f'Institución "{c_nom}" registrada exitosamente.')
                        st.rerun()

            with t_editar_i:
                if instituciones:
                    inst_map = {i['id']: f"{i['codigo_modular']} - {i['nombre']}" for i in instituciones}
                    sel_edit_id = st.selectbox('Seleccione Institución para editar', list(inst_map.keys()), format_func=lambda x: inst_map[x], key='sel_inst_edit')
                    target_i = next(i for i in instituciones if i['id'] == sel_edit_id)

                    with st.form(f'form_edit_inst_{sel_edit_id}'):
                        e1, e2 = st.columns(2)
                        e_mod = e1.text_input('Código Modular', value=target_i['codigo_modular'], max_chars=30)
                        e_nom = e2.text_input('Nombre', value=target_i['nombre'], max_chars=240)
                        e3, e4 = st.columns(2)
                        all_niv = catalogo_service.list_niveles(token, solo_activos=False)
                        e_niv = e3.selectbox('Nivel', [n['id'] for n in all_niv], index=[n['id'] for n in all_niv].index(target_i['nivel_id']), format_func=lambda x: next(n['nombre'] for n in all_niv if n['id'] == x))
                        e_dist = e4.text_input('Distrito', value=target_i['distrito'], max_chars=120)

                        all_metas = catalogo_service.list_metas(token, solo_activos=False)
                        meta_edit_opts = {0: 'Heredar del Nivel Educativo'} | {m['id']: f"{m['codigo']} - {m['descripcion'][:60]}" for m in all_metas}
                        cur_meta = target_i['meta_id'] if target_i['meta_id'] in meta_edit_opts else 0
                        e_meta = st.selectbox('Meta Presupuestaria Específica', list(meta_edit_opts.keys()), index=list(meta_edit_opts.keys()).index(cur_meta), format_func=lambda x: meta_edit_opts[x])
                        e_obs = st.text_area('Observaciones', value=target_i['observaciones'] or '', max_chars=500)
                        e_act = st.checkbox('Institución Activa', value=target_i['activo'])
                        st.caption('Desactivar una institución impide seleccionarla en futuras planillas sin afectar históricos.')
                        btn_guardar_i = st.form_submit_button('Guardar Cambios', type='primary')

                    if btn_guardar_i:
                        m_id = e_meta if e_meta != 0 else None
                        catalogo_service.update_institucion(token, sel_edit_id, e_mod, e_nom, e_niv, e_dist, m_id, e_obs, e_act)
                        st.success('Institución actualizada exitosamente.')
                        st.rerun()

    # =========================================================================
    # TAB 2: ÁREAS DE SEDE
    # =========================================================================
    with tab_areas:
        st.subheader('Áreas de Sede UGEL')
        areas = catalogo_service.list_areas_sede(token, solo_activas=False)
        st.dataframe([{
            'ID': a['id'],
            'Nombre del Área': a['nombre'],
            'Meta Presupuestaria': f"{a['meta_codigo']} - {a['meta_descripcion'][:60]}" if a['meta_codigo'] else 'Sin asignar',
            'Estado': 'Activa' if a['activo'] else 'Inactiva'
        } for a in areas], hide_index=True, use_container_width=True)

        if es_admin:
            st.divider()
            c_ar, e_ar = st.columns(2)
            with c_ar:
                st.write('**Registrar Nueva Área**')
                with st.form('form_crear_area', clear_on_submit=True):
                    a_nom = st.text_input('Nombre del Área (ej. Dirección de Gestión Pedagógica)', max_chars=150)
                    metas_activas = catalogo_service.list_metas(token, solo_activos=True)
                    m_opts_ar = {0: 'Sin meta asignada'} | {m['id']: f"{m['codigo']} - {m['descripcion'][:50]}" for m in metas_activas}
                    a_meta = st.selectbox('Meta Presupuestaria', list(m_opts_ar.keys()), format_func=lambda x: m_opts_ar[x])
                    if st.form_submit_button('Guardar Área', type='primary'):
                        m_id = a_meta if a_meta != 0 else None
                        catalogo_service.create_area_sede(token, a_nom, m_id)
                        st.success(f'Área "{a_nom}" registrada.')
                        st.rerun()

            with e_ar:
                if areas:
                    st.write('**Modificar Área Existente**')
                    ar_map = {a['id']: a['nombre'] for a in areas}
                    sel_ar = st.selectbox('Seleccionar Área', list(ar_map.keys()), format_func=lambda x: ar_map[x])
                    cur_ar = next(a for a in areas if a['id'] == sel_ar)
                    with st.form(f'form_edit_area_{sel_ar}'):
                        ea_nom = st.text_input('Nombre del Área', value=cur_ar['nombre'], max_chars=150)
                        all_m = catalogo_service.list_metas(token, solo_activos=False)
                        all_m_opts = {0: 'Sin meta asignada'} | {m['id']: f"{m['codigo']} - {m['descripcion'][:50]}" for m in all_m}
                        cur_m_id = cur_ar['meta_id'] if cur_ar['meta_id'] in all_m_opts else 0
                        ea_meta = st.selectbox('Meta Presupuestaria', list(all_m_opts.keys()), index=list(all_m_opts.keys()).index(cur_m_id), format_func=lambda x: all_m_opts[x])
                        ea_act = st.checkbox('Área Activa', value=cur_ar['activo'])
                        if st.form_submit_button('Actualizar Área', type='primary'):
                            m_id = ea_meta if ea_meta != 0 else None
                            catalogo_service.update_area_sede(token, sel_ar, ea_nom, m_id, ea_act)
                            st.success('Área actualizada.')
                            st.rerun()

    # =========================================================================
    # TAB 3: NIVELES Y METAS
    # =========================================================================
    with tab_niveles_metas:
        st.subheader('Niveles Educativos y Metas Presupuestarias')
        sub_niv, sub_meta, sub_rel = st.tabs(['Niveles Educativos', 'Metas Presupuestarias', 'Relación Nivel ↔ Meta'])

        with sub_niv:
            st.write('**Niveles Educativos**')
            niveles_all = catalogo_service.list_niveles(token, solo_activos=False)
            st.dataframe([{
                'ID': n['id'],
                'Nombre del Nivel': n['nombre'],
                'Estado': 'Activo' if n['activo'] else 'Inactivo'
            } for n in niveles_all], hide_index=True, use_container_width=True)

            if es_admin:
                col_cn1, col_cn2 = st.columns(2)
                with col_cn1:
                    with st.form('form_crear_nivel', clear_on_submit=True):
                        n_nuevo = st.text_input('Nuevo Nivel (ej. Secundaria, Primaria, Inicial)', max_chars=100)
                        if st.form_submit_button('Registrar Nivel', type='primary'):
                            catalogo_service.create_nivel(token, n_nuevo)
                            st.success(f'Nivel "{n_nuevo}" registrado.')
                            st.rerun()
                with col_cn2:
                    if niveles_all:
                        sel_n_id = st.selectbox('Editar Nivel', [n['id'] for n in niveles_all], format_func=lambda x: next(n['nombre'] for n in niveles_all if n['id'] == x))
                        n_obj = next(n for n in niveles_all if n['id'] == sel_n_id)
                        with st.form(f'form_edit_nivel_{sel_n_id}'):
                            en_nom = st.text_input('Nombre', value=n_obj['nombre'], max_chars=100)
                            en_act = st.checkbox('Activo', value=n_obj['activo'])
                            if st.form_submit_button('Actualizar Nivel'):
                                catalogo_service.update_nivel(token, sel_n_id, en_nom, en_act)
                                st.success('Nivel actualizado.')
                                st.rerun()

        with sub_meta:
            st.write('**Metas Presupuestarias**')
            metas_all = catalogo_service.list_metas(token, solo_activos=False)
            st.dataframe([{
                'ID': m['id'],
                'Código Meta': m['codigo'],
                'Descripción': m['descripcion'],
                'Programa': f"{m['programa_codigo']} - {m['programa_nombre']}" if m['programa_codigo'] else 'Sin asignar',
                'Partida': m['partida_codigo'] or 'Sin asignar',
                'Estado': 'Activa' if m['activo'] else 'Inactiva'
            } for m in metas_all], hide_index=True, use_container_width=True)

            if es_admin:
                st.write('**Gestión de Metas**')
                tm1, tm2 = st.tabs(['Nueva Meta', 'Editar Meta'])
                with tm1:
                    with st.form('form_crear_meta', clear_on_submit=True):
                        m1, m2 = st.columns(2)
                        c_m_cod = m1.text_input('Código de Meta (ej. 0011, 0022)', max_chars=30)
                        c_m_desc = m2.text_input('Descripción de la Meta', max_chars=500)
                        progs = catalogo_service.list_programas(token, solo_activos=True)
                        parts = catalogo_service.list_partidas(token, solo_activos=True)
                        m3, m4 = st.columns(2)
                        p_opts = {0: 'Ninguno'} | {p['id']: f"{p['codigo']} - {p['nombre']}" for p in progs}
                        pt_opts = {0: 'Ninguna'} | {pt['id']: f"{pt['codigo']} - {pt['descripcion'][:40]}" for pt in parts}
                        sel_p = m3.selectbox('Programa Asociado', list(p_opts.keys()), format_func=lambda x: p_opts[x])
                        sel_pt = m4.selectbox('Partida Asociada', list(pt_opts.keys()), format_func=lambda x: pt_opts[x])
                        if st.form_submit_button('Registrar Meta', type='primary'):
                            catalogo_service.create_meta(
                                token, c_m_cod, c_m_desc,
                                programa_id=sel_p if sel_p != 0 else None,
                                partida_id=sel_pt if sel_pt != 0 else None
                            )
                            st.success(f'Meta "{c_m_cod}" registrada.')
                            st.rerun()

                with tm2:
                    if metas_all:
                        m_map = {m['id']: f"{m['codigo']} - {m['descripcion'][:50]}" for m in metas_all}
                        sel_m_id = st.selectbox('Seleccionar Meta', list(m_map.keys()), format_func=lambda x: m_map[x])
                        m_cur = next(m for m in metas_all if m['id'] == sel_m_id)
                        with st.form(f'form_edit_meta_{sel_m_id}'):
                            em1, em2 = st.columns(2)
                            em_cod = em1.text_input('Código', value=m_cur['codigo'], max_chars=30)
                            em_desc = em2.text_input('Descripción', value=m_cur['descripcion'], max_chars=500)
                            all_progs = catalogo_service.list_programas(token, solo_activos=False)
                            all_parts = catalogo_service.list_partidas(token, solo_activos=False)
                            em3, em4 = st.columns(2)
                            p_all_opts = {0: 'Ninguno'} | {p['id']: f"{p['codigo']} - {p['nombre']}" for p in all_progs}
                            pt_all_opts = {0: 'Ninguna'} | {pt['id']: f"{pt['codigo']} - {pt['descripcion'][:40]}" for pt in all_parts}
                            cur_p = m_cur['programa_id'] if m_cur['programa_id'] in p_all_opts else 0
                            cur_pt = m_cur['partida_id'] if m_cur['partida_id'] in pt_all_opts else 0
                            em_p = em3.selectbox('Programa', list(p_all_opts.keys()), index=list(p_all_opts.keys()).index(cur_p), format_func=lambda x: p_all_opts[x])
                            em_pt = em4.selectbox('Partida', list(pt_all_opts.keys()), index=list(pt_all_opts.keys()).index(cur_pt), format_func=lambda x: pt_all_opts[x])
                            em_act = st.checkbox('Activa', value=m_cur['activo'])
                            if st.form_submit_button('Actualizar Meta', type='primary'):
                                catalogo_service.update_meta(
                                    token, sel_m_id, em_cod, em_desc,
                                    programa_id=em_p if em_p != 0 else None,
                                    partida_id=em_pt if em_pt != 0 else None,
                                    activo=em_act
                                )
                                st.success('Meta actualizada.')
                                st.rerun()

        with sub_rel:
            st.write('**Asignación de Meta por Defecto a Niveles Educativos**')
            st.caption('Cuando una institución no tiene meta específica, el sistema resuelve automáticamente la meta asignada a su nivel.')
            relaciones = catalogo_service.list_nivel_metas(token)
            st.dataframe([{
                'Nivel Educativo': r['nivel_nombre'],
                'Meta Asociada': f"{r['meta_codigo']} - {r['meta_descripcion']}",
                'Última Modificación': r['actualizado_en'].strftime('%d/%m/%Y %H:%M') if r['actualizado_en'] else '-'
            } for r in relaciones], hide_index=True, use_container_width=True)

            if es_admin:
                st.write('**Configurar Asignación Nivel ↔ Meta**')
                niveles_activos = catalogo_service.list_niveles(token, solo_activos=True)
                metas_activas = catalogo_service.list_metas(token, solo_activos=True)
                if niveles_activos and metas_activas:
                    with st.form('form_set_nivel_meta'):
                        col_rn1, col_rn2 = st.columns(2)
                        rn_id = col_rn1.selectbox('Nivel', [n['id'] for n in niveles_activos], format_func=lambda x: next(n['nombre'] for n in niveles_activos if n['id'] == x))
                        rm_id = col_rn2.selectbox('Meta Presupuestaria', [m['id'] for m in metas_activas], format_func=lambda x: f"{m['codigo']} - {m['descripcion'][:50]}")
                        if st.form_submit_button('Guardar Asignación', type='primary'):
                            catalogo_service.set_nivel_meta(token, rn_id, rm_id)
                            st.success('Asignación Nivel-Meta guardada.')
                            st.rerun()
                else:
                    st.warning('Debe tener niveles y metas activas para configurar la asignación.')

    # =========================================================================
    # TAB 4: PROGRAMAS Y PARTIDAS
    # =========================================================================
    with tab_presupuesto:
        st.subheader('Estructura Presupuestaria')
        sub_prog, sub_part = st.tabs(['Programas (Jerarquía)', 'Partidas Presupuestarias'])

        with sub_prog:
            st.write('**Programas Presupuestarios**')
            progs_all = catalogo_service.list_programas(token, solo_activos=False)
            st.dataframe([{
                'ID': p['id'],
                'Código': p['codigo'],
                'Nombre del Programa': p['nombre'],
                'Programa Padre': f"{p['padre_codigo']} - {p['padre_nombre']}" if p['padre_codigo'] else 'Principal (Raíz)',
                'Orden': p['orden'],
                'Estado': 'Activo' if p['activo'] else 'Inactivo'
            } for p in progs_all], hide_index=True, use_container_width=True)

            if es_admin:
                cp1, cp2 = st.columns(2)
                with cp1:
                    st.write('**Registrar Programa**')
                    with st.form('form_crear_prog', clear_on_submit=True):
                        pr_cod = st.text_input('Código (ej. 9001, 0090)', max_chars=30)
                        pr_nom = st.text_input('Nombre del Programa', max_chars=180)
                        pr_ord = st.number_input('Orden', min_value=0, value=1, step=1)
                        padres_opts = {0: 'Ninguno (Programa Raíz)'} | {p['id']: f"{p['codigo']} - {p['nombre']}" for p in progs_all if p['activo']}
                        pr_padre = st.selectbox('Programa Padre', list(padres_opts.keys()), format_func=lambda x: padres_opts[x])
                        if st.form_submit_button('Crear Programa', type='primary'):
                            pid = pr_padre if pr_padre != 0 else None
                            catalogo_service.create_programa(token, pr_cod, pr_nom, orden=pr_ord, padre_id=pid)
                            st.success('Programa registrado.')
                            st.rerun()

                with cp2:
                    if progs_all:
                        st.write('**Modificar Programa**')
                        pr_map = {p['id']: f"{p['codigo']} - {p['nombre']}" for p in progs_all}
                        sel_pr = st.selectbox('Seleccionar Programa', list(pr_map.keys()), format_func=lambda x: pr_map[x])
                        cur_pr = next(p for p in progs_all if p['id'] == sel_pr)
                        with st.form(f'form_edit_prog_{sel_pr}'):
                            epr_cod = st.text_input('Código', value=cur_pr['codigo'], max_chars=30)
                            epr_nom = st.text_input('Nombre', value=cur_pr['nombre'], max_chars=180)
                            epr_ord = st.number_input('Orden', min_value=0, value=cur_pr['orden'], step=1)
                            padre_edit_opts = {0: 'Ninguno (Programa Raíz)'} | {p['id']: f"{p['codigo']} - {p['nombre']}" for p in progs_all if p['id'] != sel_pr}
                            cur_padre_id = cur_pr['padre_id'] if cur_pr['padre_id'] in padre_edit_opts else 0
                            epr_padre = st.selectbox('Programa Padre', list(padre_edit_opts.keys()), index=list(padre_edit_opts.keys()).index(cur_padre_id), format_func=lambda x: padre_edit_opts[x])
                            epr_act = st.checkbox('Activo', value=cur_pr['activo'])
                            if st.form_submit_button('Actualizar Programa', type='primary'):
                                pid = epr_padre if epr_padre != 0 else None
                                catalogo_service.update_programa(token, sel_pr, epr_cod, epr_nom, epr_ord, pid, epr_act)
                                st.success('Programa actualizado.')
                                st.rerun()

        with sub_part:
            st.write('**Partidas Presupuestarias**')
            partidas = catalogo_service.list_partidas(token, solo_activos=False)
            st.dataframe([{
                'ID': pt['id'],
                'Código Clasificador': pt['codigo'],
                'Descripción': pt['descripcion'],
                'Estado': 'Activa' if pt['activo'] else 'Inactiva'
            } for pt in partidas], hide_index=True, use_container_width=True)

            if es_admin:
                col_pt1, col_pt2 = st.columns(2)
                with col_pt1:
                    st.write('**Registrar Partida**')
                    with st.form('form_crear_partida', clear_on_submit=True):
                        c_pt_cod = st.text_input('Código de Partida (ej. 2.1.11.21)', max_chars=40)
                        c_pt_desc = st.text_input('Descripción de la Partida', max_chars=500)
                        if st.form_submit_button('Guardar Partida', type='primary'):
                            catalogo_service.create_partida(token, c_pt_cod, c_pt_desc)
                            st.success('Partida registrada.')
                            st.rerun()

                with col_pt2:
                    if partidas:
                        st.write('**Editar Partida**')
                        pt_map = {pt['id']: f"{pt['codigo']} - {pt['descripcion'][:40]}" for pt in partidas}
                        sel_pt = st.selectbox('Seleccionar Partida', list(pt_map.keys()), format_func=lambda x: pt_map[x])
                        cur_pt = next(pt for pt in partidas if pt['id'] == sel_pt)
                        with st.form(f'form_edit_partida_{sel_pt}'):
                            ept_cod = st.text_input('Código', value=cur_pt['codigo'], max_chars=40)
                            ept_desc = st.text_input('Descripción', value=cur_pt['descripcion'], max_chars=500)
                            ept_act = st.checkbox('Activa', value=cur_pt['activo'])
                            if st.form_submit_button('Actualizar Partida', type='primary'):
                                catalogo_service.update_partida(token, sel_pt, ept_cod, ept_desc, ept_act)
                                st.success('Partida actualizada.')
                                st.rerun()

    # =========================================================================
    # TAB 5: PARÁMETROS DE PERSONAL
    # =========================================================================
    with tab_personal:
        st.subheader('Parámetros de Personal')
        p_cargos, p_cat, p_sit, p_sub = st.tabs(['Cargos', 'Categorías', 'Situaciones', 'Subtipos'])

        with p_cargos:
            st.write('**Cargos**')
            cargos = catalogo_service.list_cargos(token)
            st.dataframe([{'ID': c['id'], 'Nombre del Cargo': c['nombre'], 'Estado': 'Activo' if c['activo'] else 'Inactivo'} for c in cargos], hide_index=True, use_container_width=True)
            if es_admin:
                with st.form('form_crear_cargo', clear_on_submit=True):
                    c_cargo = st.text_input('Nuevo Cargo (ej. Especialista Administrativo, Oficinista)', max_chars=150)
                    if st.form_submit_button('Registrar Cargo', type='primary'):
                        catalogo_service.create_cargo(token, c_cargo)
                        st.success(f'Cargo "{c_cargo}" registrado.')
                        st.rerun()

        with p_cat:
            st.write('**Categorías Remunerativas**')
            cats = catalogo_service.list_categorias(token)
            st.dataframe([{'ID': c['id'], 'Código': c['codigo'], 'Descripción': c['descripcion'], 'Estado': 'Activa' if c['activo'] else 'Inactiva'} for c in cats], hide_index=True, use_container_width=True)
            if es_admin:
                with st.form('form_crear_categoria', clear_on_submit=True):
                    c1, c2 = st.columns(2)
                    c_cat_cod = c1.text_input('Código (ej. AE, F1, STA)', max_chars=50)
                    c_cat_desc = c2.text_input('Descripción (ej. Asistente Ejecutivo)', max_chars=150)
                    if st.form_submit_button('Registrar Categoría', type='primary'):
                        catalogo_service.create_categoria(token, c_cat_cod, c_cat_desc)
                        st.success('Categoría registrada.')
                        st.rerun()

        with p_sit:
            st.write('**Situaciones Laborales**')
            sits = catalogo_service.list_situaciones(token)
            st.dataframe([{'ID': s['id'], 'Situación Laboral': s['nombre'], 'Estado': 'Activa' if s['activo'] else 'Inactiva'} for s in sits], hide_index=True, use_container_width=True)
            if es_admin:
                with st.form('form_crear_situacion', clear_on_submit=True):
                    c_sit = st.text_input('Nueva Situación (ej. NOMBRADO, CONTRATADO)', max_chars=120)
                    if st.form_submit_button('Registrar Situación', type='primary'):
                        catalogo_service.create_situacion(token, c_sit)
                        st.success('Situación registrada.')
                        st.rerun()

        with p_sub:
            st.write('**Subtipos de Trabajador**')
            subs = catalogo_service.list_subtipos(token)
            st.dataframe([{'ID': s['id'], 'Subtipo': s['nombre'], 'Estado': 'Activo' if s['activo'] else 'Inactivo'} for s in subs], hide_index=True, use_container_width=True)
            if es_admin:
                with st.form('form_crear_subtipo', clear_on_submit=True):
                    c_sub = st.text_input('Nuevo Subtipo (ej. DOCENTE, ADMINISTRATIVO)', max_chars=120)
                    if st.form_submit_button('Registrar Subtipo', type='primary'):
                        catalogo_service.create_subtipo(token, c_sub)
                        st.success('Subtipo registrado.')
                        st.rerun()

    # =========================================================================
    # TAB 6: FIRMAS
    # =========================================================================
    with tab_firmas:
        st.subheader('Firmas Institucionales')
        st.info('Regla confirmada: II.EE. utiliza 4 firmas (UGEL, Gestión Institucional, Gestión Administrativa, Finanzas). Sede utiliza 3 firmas (UGEL, Gestión Institucional, Finanzas).')
        firmas = catalogo_service.list_firmas(token, solo_activas=False)
        st.dataframe([{'ID': f['id'], 'Persona': f['nombre_completo'], 'Cargo': f['cargo'], 'Estado': 'Activa' if f['activo'] else 'Inactiva'} for f in firmas], hide_index=True, use_container_width=True)

        if es_admin:
            cf1, cf2 = st.columns(2)
            with cf1:
                st.write('**Registrar Firma**')
                with st.form('form_crear_firma', clear_on_submit=True):
                    f_nom = st.text_input('Nombre Completo de la Autoridad', max_chars=200)
                    f_car = st.text_input('Cargo Institucional', max_chars=200)
                    if st.form_submit_button('Guardar Firma', type='primary'):
                        catalogo_service.create_firma(token, f_nom, f_car)
                        st.success('Firma registrada.')
                        st.rerun()

            with cf2:
                if firmas:
                    st.write('**Editar Firma**')
                    f_map = {f['id']: f"{f['nombre_completo']} ({f['cargo']})" for f in firmas}
                    sel_f = st.selectbox('Seleccionar Firma', list(f_map.keys()), format_func=lambda x: f_map[x])
                    cur_f = next(f for f in firmas if f['id'] == sel_f)
                    with st.form(f'form_edit_firma_{sel_f}'):
                        ef_nom = st.text_input('Nombre Completo', value=cur_f['nombre_completo'], max_chars=200)
                        ef_car = st.text_input('Cargo', value=cur_f['cargo'], max_chars=200)
                        ef_act = st.checkbox('Activa', value=cur_f['activo'])
                        if st.form_submit_button('Actualizar Firma', type='primary'):
                            catalogo_service.update_firma(token, sel_f, ef_nom, ef_car, ef_act)
                            st.success('Firma actualizada.')
                            st.rerun()

    # =========================================================================
    # TAB 7: IDENTIDAD INSTITUCIONAL
    # =========================================================================
    with tab_identidad:
        st.subheader('Identidad Institucional y Configuración del Sistema')
        cfg = catalogo_service.get_configuracion(token)

        st.write('**Parámetros Actuales:**')
        c_i1, c_i2, c_i3 = st.columns(3)
        c_i1.metric('Institución', cfg['nombre_institucion'])
        c_i2.metric('Sistema', cfg['nombre_sistema'])
        c_i3.metric('Zona Horaria', cfg['zona_horaria'])

        if es_admin:
            st.divider()
            st.write('**Actualizar Identidad Institucional**')
            with st.form('form_identidad'):
                ci_nom = st.text_input('Nombre de la Institución', value=cfg['nombre_institucion'], max_chars=200)
                ci_sis = st.text_input('Nombre del Sistema', value=cfg['nombre_sistema'], max_chars=200)
                ci_tz = st.text_input('Zona Horaria IANA', value=cfg['zona_horaria'], max_chars=80)
                st.caption('La zona horaria estándar administrativa es America/Lima.')
                if st.form_submit_button('Guardar Configuración', type='primary'):
                    catalogo_service.update_configuracion(token, ci_nom, ci_sis, zona_horaria=ci_tz)
                    st.success('Configuración institucional actualizada.')
                    st.rerun()
