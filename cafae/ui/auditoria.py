"""Módulo de interfaz de usuario para Auditoría Administrativa (Etapa 15).
"""
import streamlit as st

from cafae.auditoria import AuditoriaService


def render_auditoria_view(token, user_role):
    aud_service = AuditoriaService()
    if user_role != 'ADMINISTRADOR':
        st.warning('El visor de auditoría administrativa está reservado exclusivamente para el Administrador.')
        return

    st.title('Auditoría del Sistema')
    st.write('Registro inmutable de trazabilidad de operaciones, accesos, cambios de datos y eventos de seguridad.')

    col_f1, col_f2, col_f3 = st.columns(3)
    entidades = [
        'TODAS', 'acceso', 'usuarios', 'trabajadores', 'instituciones', 'areas_sede',
        'metas', 'niveles', 'cargos', 'categorias', 'situaciones', 'firmas',
        'planillas', 'planilla_versiones', 'planilla_detalle', 'planilla_descuentos',
        'importaciones', 'configuracion_institucional'
    ]
    f_ent = col_f1.selectbox('Filtrar por Entidad', entidades)
    f_acc = col_f2.text_input('Buscar Acción (ej. INSERT, UPDATE, LOGIN)')
    f_res = col_f3.selectbox('Resultado', ['TODOS', 'EXITO', 'RECHAZADO', 'ERROR'])

    eventos = aud_service.list_eventos(
        token,
        entidad=None if f_ent == 'TODAS' else f_ent,
        accion=f_acc if f_acc else None,
        resultado=None if f_res == 'TODOS' else f_res,
        limite=150
    )['items']

    st.caption(f'Mostrando los últimos {len(eventos)} eventos registrados en la base de datos.')

    st.dataframe([{
        'ID': e['id'],
        'Fecha y Hora': e['fecha_hora'].strftime('%d/%m/%Y %H:%M:%S'),
        'Usuario': e['usuario_nombre'] or f"ID {e['usuario_id']}" if e['usuario_id'] else 'Sistema',
        'Acción': e['accion'],
        'Entidad': f"{e['entidad']} #{e['entidad_id']}" if e['entidad_id'] else e['entidad'],
        'Resultado': '✅ ÉXITO' if e['resultado'] == 'EXITO' else ('⚠️ RECHAZADO' if e['resultado'] == 'RECHAZADO' else '❌ ERROR'),
        'Descripción': e['descripcion'],
        'Cambios': f"{e['total_cambios']} campos" if e['total_cambios'] else '-'
    } for e in eventos], hide_index=True, use_container_width=True)

    # Detalle de cambios por evento
    eventos_con_cambios = [e for e in eventos if e['total_cambios'] > 0]
    if eventos_con_cambios:
        st.divider()
        st.subheader('Detalle de Modificaciones (Antes / Después)')
        ev_map = {e['id']: f"#{e['id']} · {e['fecha_hora'].strftime('%H:%M:%S')} - {e['accion']} en {e['entidad']} ({e['usuario_nombre']})" for e in eventos_con_cambios}
        sel_ev = st.selectbox('Seleccione un evento para ver los campos modificados', list(ev_map.keys()), format_func=lambda x: ev_map[x])

        cambios = aud_service.get_cambios(token, sel_ev)
        st.dataframe([{
            'Campo Modificado': c['campo'],
            'Valor Anterior': c['valor_anterior'] if c['valor_anterior'] is not None else '<VACÍO>',
            'Valor Nuevo': c['valor_nuevo'] if c['valor_nuevo'] is not None else '<VACÍO>'
        } for c in cambios], hide_index=True, use_container_width=True)
