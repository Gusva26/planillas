"""Módulo de interfaz de usuario para el Maestro de Personal (Trabajadores II.EE. y Sede).
"""
from decimal import Decimal
import streamlit as st

from cafae.catalogos import CatalogoService
from cafae.trabajadores import TrabajadorService, parse_monto
from cafae.security import UserError


def render_trabajadores_view(token, user_role):
    trab_service = TrabajadorService()
    cat_service = CatalogoService()
    puede_editar = (user_role in ('ADMINISTRADOR', 'PLANILLAS'))

    st.title('Maestro de Personal')
    st.write('Gestión integral de trabajadores adscritos a Instituciones Educativas y a la Sede UGEL Chepén.')

    if not puede_editar:
        st.info('Modo consulta: Visualización autorizada del personal. El registro y edición corresponden a Planillas y Administrador.')

    tab_iiee, tab_sede, tab_nuevo, tab_editar = st.tabs([
        '🏫 Personal II.EE.',
        '🏢 Personal Sede UGEL',
        '➕ Registrar Trabajador',
        '✏️ Editar Ficha / Historial'
    ])

    # Cargar catálogos para filtros
    instituciones = cat_service.list_instituciones(token, solo_activas=False)
    areas_sede = cat_service.list_areas_sede(token, solo_activas=False)
    niveles = cat_service.list_niveles(token, solo_activos=False)
    cargos = cat_service.list_cargos(token, solo_activos=False)
    categorias = cat_service.list_categorias(token, solo_activas=False)
    situaciones = cat_service.list_situaciones(token, solo_activas=False)
    subtipos = cat_service.list_subtipos(token, solo_activos=False)

    # =========================================================================
    # TAB 1: PERSONAL II.EE.
    # =========================================================================
    with tab_iiee:
        st.subheader('Personal de Instituciones Educativas')
        c_f1, c_f2, c_f3 = st.columns([2, 1, 1])
        q_iiee = c_f1.text_input('Buscar DNI, apellidos, nombres o I.E.', key='q_trab_iiee')
        inst_opts = {0: 'Todas las instituciones'} | {i['id']: f"{i['codigo_modular']} - {i['nombre'][:40]}" for i in instituciones}
        sel_inst = c_f2.selectbox('Institución Educativa', list(inst_opts.keys()), format_func=lambda x: inst_opts[x], key='f_inst_iiee')
        act_iiee = c_f3.checkbox('Solo activos', value=False, key='chk_act_iiee')

        c_f4, c_f5, c_f6 = st.columns(3)
        cargos_opts = {0: 'Todos los cargos'} | {c['id']: c['nombre'] for c in cargos}
        sel_cargo = c_f4.selectbox('Cargo', list(cargos_opts.keys()), format_func=lambda x: cargos_opts[x], key='f_cargo_iiee')
        cats_opts = {0: 'Todas las categorías'} | {c['id']: f"{c['codigo']} - {c['descripcion'][:30]}" for c in categorias}
        sel_cat = c_f5.selectbox('Categoría', list(cats_opts.keys()), format_func=lambda x: cats_opts[x], key='f_cat_iiee')
        sits_opts = {0: 'Todas las situaciones'} | {s['id']: s['nombre'] for s in situaciones}
        sel_sit = c_f6.selectbox('Situación', list(sits_opts.keys()), format_func=lambda x: sits_opts[x], key='f_sit_iiee')

        personal_iiee = trab_service.list_trabajadores(
            token, tipo='IIEE', solo_activos=act_iiee, query=q_iiee,
            institucion_id=sel_inst if sel_inst != 0 else None,
            cargo_id=sel_cargo if sel_cargo != 0 else None,
            categoria_id=sel_cat if sel_cat != 0 else None,
            situacion_id=sel_sit if sel_sit != 0 else None
        )

        st.caption(f'Total trabajadores encontrados: {len(personal_iiee)}')
        st.dataframe([{
            'ID': t['id'],
            'DNI': t['dni'],
            'Apellidos y Nombres': f"{t['apellidos']}, {t['nombres']}",
            'Institución Educativa': t['institucion_nombre'] or '-',
            'Nivel': t['nivel_nombre'] or '-',
            'Cargo': t['cargo_nombre'] or '-',
            'Categoría': t['categoria_codigo'] or '-',
            'Situación': t['situacion_nombre'] or '-',
            'Cuenta Multired': t['cuenta_multired'] or '-',
            'Importe Maestro': f"S/ {t['importe']:.2f}",
            'Estado': 'Activo' if t['activo'] else 'Inactivo'
        } for t in personal_iiee], hide_index=True, use_container_width=True)

    # =========================================================================
    # TAB 2: PERSONAL SEDE UGEL
    # =========================================================================
    with tab_sede:
        st.subheader('Personal de Sede UGEL Chepén')
        c_s1, c_s2, c_s3 = st.columns([2, 1, 1])
        q_sede = c_s1.text_input('Buscar DNI, apellidos, nombres o Área', key='q_trab_sede')
        areas_opts = {0: 'Todas las áreas'} | {a['id']: a['nombre'] for a in areas_sede}
        sel_area = c_s2.selectbox('Área de Sede', list(areas_opts.keys()), format_func=lambda x: areas_opts[x], key='f_area_sede')
        act_sede = c_s3.checkbox('Solo activos', value=False, key='chk_act_sede')

        personal_sede = trab_service.list_trabajadores(
            token, tipo='SEDE', solo_activos=act_sede, query=q_sede,
            area_id=sel_area if sel_area != 0 else None
        )

        st.caption(f'Total trabajadores encontrados: {len(personal_sede)}')
        st.dataframe([{
            'ID': t['id'],
            'DNI': t['dni'],
            'Apellidos y Nombres': f"{t['apellidos']}, {t['nombres']}",
            'Área de Sede': t['area_nombre'] or '-',
            'Cargo': t['cargo_nombre'] or '-',
            'Categoría': t['categoria_codigo'] or '-',
            'Situación': t['situacion_nombre'] or '-',
            'Cuenta Multired': t['cuenta_multired'] or '-',
            'Tipo Pago': t['tipo_pago'],
            'Importe Maestro': f"S/ {t['importe']:.2f}",
            'Estado': 'Activo' if t['activo'] else 'Inactivo'
        } for t in personal_sede], hide_index=True, use_container_width=True)

    # =========================================================================
    # TAB 3: REGISTRAR TRABAJADOR
    # =========================================================================
    with tab_nuevo:
        if not puede_editar:
            st.warning('No tienes permisos para registrar trabajadores.')
        else:
            st.subheader('Registrar Nuevo Trabajador')
            st.caption('Complete la ficha laboral del trabajador. Los datos se conservarán en el maestro.')

            with st.form('form_nuevo_trabajador', clear_on_submit=True):
                st.write('**1. Identificación Personal**')
                c1, c2, c3, c4 = st.columns(4)
                f_dni = c1.text_input('DNI (8 dígitos exactos)', max_chars=8)
                f_ape = c2.text_input('Apellidos Completos', max_chars=150)
                f_nom = c3.text_input('Nombres Completos', max_chars=150)
                f_nac = c4.date_input('Fecha de Nacimiento', value=None)

                st.write('**2. Adscripción y Dependencia**')
                ca1, ca2 = st.columns(2)
                f_tipo = ca1.radio('Ámbito Laboral', ['IIEE', 'SEDE'], horizontal=True)

                if f_tipo == 'IIEE':
                    inst_activas = [i for i in instituciones if i['activo']]
                    f_inst = ca2.selectbox('Institución Educativa', [i['id'] for i in inst_activas], format_func=lambda x: next(f"{i['codigo_modular']} - {i['nombre']}" for i in inst_activas if i['id'] == x) if inst_activas else 'No hay activas')
                    f_area = None
                else:
                    areas_activas = [a for a in areas_sede if a['activo']]
                    f_area = ca2.selectbox('Área de Sede', [a['id'] for a in areas_activas], format_func=lambda x: next(a['nombre'] for a in areas_activas if a['id'] == x) if areas_activas else 'No hay activas')
                    f_inst = None

                st.write('**3. Datos Laborales y Categorización**')
                cl1, cl2, cl3, cl4 = st.columns(4)
                niv_activas = [n for n in niveles if n['activo']]
                f_niv = cl1.selectbox('Nivel Educativo', [0] + [n['id'] for n in niv_activas], format_func=lambda x: 'Sin asignar' if x == 0 else next(n['nombre'] for n in niv_activas if n['id'] == x))
                cargos_activos = [c for c in cargos if c['activo']]
                f_car = cl2.selectbox('Cargo', [0] + [c['id'] for c in cargos_activos], format_func=lambda x: 'Sin asignar' if x == 0 else next(c['nombre'] for c in cargos_activos if c['id'] == x))
                cats_activas = [c for c in categorias if c['activo']]
                f_cat = cl3.selectbox('Categoría', [0] + [c['id'] for c in cats_activas], format_func=lambda x: 'Sin asignar' if x == 0 else next(f"{c['codigo']} - {c['descripcion']}" for c in cats_activas if c['id'] == x))
                sits_activas = [s for s in situaciones if s['activo']]
                f_sit = cl4.selectbox('Situación Laboral', [0] + [s['id'] for s in sits_activas], format_func=lambda x: 'Sin asignar' if x == 0 else next(s['nombre'] for s in sits_activas if s['id'] == x))

                cl5, cl6, cl7 = st.columns(3)
                subs_activos = [s for s in subtipos if s['activo']]
                f_sub = cl5.selectbox('Subtipo de Trabajador', [0] + [s['id'] for s in subs_activos], format_func=lambda x: 'Sin asignar' if x == 0 else next(s['nombre'] for s in subs_activos if s['id'] == x))
                f_reg_lab = cl6.text_input('Régimen Laboral / Ley (ej. D.L. 276, Ley 29944)', max_chars=120)
                f_jor = cl7.text_input('Jornada Laboral (ej. 40 Horas)', value='40 Horas', max_chars=60)

                st.write('**4. Remuneración y Pago**')
                cp1, cp2, cp3, cp4 = st.columns(4)
                f_imp_txt = cp1.text_input('Importe Remuneración Base (S/)', value='1350.00', max_chars=15)
                f_tipo_pago = cp2.selectbox('Forma de Pago', ['CUENTA', 'CHEQUE'])
                f_cta = cp3.text_input('N° Cuenta Multired (Banco de la Nación)', max_chars=60)
                f_cheq = cp4.text_input('N° Cheque (solo si aplica)', max_chars=60)

                st.write('**5. Datos Adicionales de Servicio y Boleta**')
                cd1, cd2, cd3 = st.columns(3)
                f_pen = cd1.text_input('Régimen Pensionario (ej. D.L. 19990, INTEGRA)', max_chars=120)
                f_fing = cd2.date_input('Fecha de Ingreso', value=None)
                f_fter = cd3.date_input('Fecha de Término', value=None)
                f_tserv = st.text_input('Tiempo de Servicio (ej. 15 años 03 meses)', max_chars=60)
                f_leyenda = st.text_area('Leyenda Permanente de Boleta', max_chars=500)

                btn_guardar_nuevo = st.form_submit_button('Registrar en el Maestro', type='primary')

            if btn_guardar_nuevo:
                datos = {
                    'dni': f_dni,
                    'apellidos': f_ape,
                    'nombres': f_nom,
                    'tipo': f_tipo,
                    'institucion_id': f_inst if f_tipo == 'IIEE' else None,
                    'area_id': f_area if f_tipo == 'SEDE' else None,
                    'nivel_id': f_niv if f_niv != 0 else None,
                    'cargo_id': f_car if f_car != 0 else None,
                    'categoria_id': f_cat if f_cat != 0 else None,
                    'situacion_id': f_sit if f_sit != 0 else None,
                    'subtipo_id': f_sub if f_sub != 0 else None,
                    'fecha_nacimiento': f_nac,
                    'regimen_laboral': f_reg_lab,
                    'jornada_laboral': f_jor,
                    'tipo_pago': f_tipo_pago,
                    'cuenta_multired': f_cta,
                    'numero_cheque': f_cheq,
                    'importe': parse_monto(f_imp_txt),
                    'regimen_pensionario': f_pen,
                    'fecha_ingreso': f_fing,
                    'fecha_termino': f_fter,
                    'tiempo_servicio_texto': f_tserv,
                    'leyenda_permanente': f_leyenda,
                    'activo': True
                }
                tid = trab_service.create_trabajador(token, datos)
                st.success(f'Trabajador {f_ape}, {f_nom} (DNI {f_dni}) registrado con ID #{tid}.')
                st.rerun()

    # =========================================================================
    # TAB 4: MODIFICAR FICHA / HISTORIAL
    # =========================================================================
    with tab_editar:
        st.subheader('Ficha Completa e Historial del Trabajador')
        todos_trab = trab_service.list_trabajadores(token, solo_activos=False)
        if not todos_trab:
            st.info('No hay trabajadores registrados en el sistema.')
        else:
            t_map = {t['id']: f"{t['dni']} - {t['apellidos']}, {t['nombres']} ({t['tipo']})" for t in todos_trab}
            sel_t_id = st.selectbox('Seleccione un trabajador para consultar o editar', list(t_map.keys()), format_func=lambda x: t_map[x], key='sel_trab_editar')
            cur_t = trab_service.get_trabajador(token, sel_t_id)

            sub_ficha, sub_hist = st.tabs(['Ficha Laboral', 'Historial en Planillas'])

            with sub_ficha:
                if not puede_editar:
                    st.write('**Detalles del Registro:**')
                    c_m1, c_m2, c_m3 = st.columns(3)
                    c_m1.metric('DNI', cur_t['dni'])
                    c_m1.metric('Estado', 'Activo' if cur_t['activo'] else 'Inactivo')
                    c_m2.metric('Importe Maestro', f"S/ {cur_t['importe']:.2f}")
                    c_m2.metric('Forma de Pago', cur_t['tipo_pago'])
                    c_m3.metric('Cuenta Multired', cur_t['cuenta_multired'] or 'Sin cuenta')
                    c_m3.metric('Ámbito', cur_t['tipo'])
                else:
                    with st.form(f'form_edit_trab_{sel_t_id}'):
                        e1, e2, e3 = st.columns(3)
                        ed_dni = e1.text_input('DNI', value=cur_t['dni'], max_chars=8)
                        ed_ape = e2.text_input('Apellidos', value=cur_t['apellidos'], max_chars=150)
                        ed_nom = e3.text_input('Nombres', value=cur_t['nombres'], max_chars=150)

                        ea1, ea2 = st.columns(2)
                        ed_tipo = ea1.radio('Ámbito', ['IIEE', 'SEDE'], index=0 if cur_t['tipo'] == 'IIEE' else 1, horizontal=True)

                        if ed_tipo == 'IIEE':
                            all_i_opts = [i for i in instituciones if i['activo'] or i['id'] == cur_t['institucion_id']]
                            cur_inst_idx = [i['id'] for i in all_i_opts].index(cur_t['institucion_id']) if cur_t['institucion_id'] in [i['id'] for i in all_i_opts] else 0
                            ed_inst = ea2.selectbox('Institución Educativa', [i['id'] for i in all_i_opts], index=cur_inst_idx, format_func=lambda x: next(f"{i['codigo_modular']} - {i['nombre']}" for i in all_i_opts if i['id'] == x))
                            ed_area = None
                        else:
                            all_a_opts = [a for a in areas_sede if a['activo'] or a['id'] == cur_t['area_id']]
                            cur_area_idx = [a['id'] for a in all_a_opts].index(cur_t['area_id']) if cur_t['area_id'] in [a['id'] for a in all_a_opts] else 0
                            ed_area = ea2.selectbox('Área de Sede', [a['id'] for a in all_a_opts], index=cur_area_idx, format_func=lambda x: next(a['nombre'] for a in all_a_opts if a['id'] == x))
                            ed_inst = None

                        ec1, ec2, ec3 = st.columns(3)
                        ed_imp = ec1.text_input('Importe Base (S/)', value=str(cur_t['importe']))
                        ed_cta = ec2.text_input('Cuenta Multired', value=cur_t['cuenta_multired'] or '')
                        ed_pago = ec3.selectbox('Tipo de Pago', ['CUENTA', 'CHEQUE'], index=0 if cur_t['tipo_pago'] == 'CUENTA' else 1)

                        ed_act = st.checkbox('Trabajador Activo en el Maestro', value=cur_t['activo'])
                        st.caption('Desactivar un trabajador impide que se incluya en nuevas planillas, conservando íntegro su historial previo.')

                        if st.form_submit_button('Actualizar Ficha de Personal', type='primary'):
                            datos_update = dict(cur_t)
                            datos_update.update({
                                'dni': ed_dni,
                                'apellidos': ed_ape,
                                'nombres': ed_nom,
                                'tipo': ed_tipo,
                                'institucion_id': ed_inst if ed_tipo == 'IIEE' else None,
                                'area_id': ed_area if ed_tipo == 'SEDE' else None,
                                'importe': parse_monto(ed_imp),
                                'cuenta_multired': ed_cta,
                                'tipo_pago': ed_pago,
                                'activo': ed_act
                            })
                            trab_service.update_trabajador(token, sel_t_id, datos_update)
                            st.success('Ficha del trabajador actualizada exitosamente.')
                            st.rerun()

            with sub_hist:
                historial = trab_service.historial_planillas(token, sel_t_id)
                if not historial:
                    st.info('Este trabajador aún no ha participado en ninguna planilla generada.')
                else:
                    st.write(f'**Participaciones Históricas ({len(historial)} registros):**')
                    st.dataframe([{
                        'Periodo': f"{h['anio']}-{h['mes']:02d}",
                        'Tipo Planilla': h['tipo'],
                        'Versión': f"v{h['version_numero']} ({h['version_estado']})",
                        'Adscripción': h['adscripcion_historica'],
                        'Categoría Histórica': h['categoria_historica'],
                        'Importe': f"S/ {h['importe']:.2f}",
                        'Total Descuentos': f"S/ {h['total_descuentos']:.2f}",
                        'Neto Pagado': f"S/ {h['neto']:.2f}",
                        'Licencia Días': h['dias_licencia'],
                        'Cerrado Por': h['cerrado_por_nombre'] or '-'
                    } for h in historial], hide_index=True, use_container_width=True)
