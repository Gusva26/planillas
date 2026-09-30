"""Interfaz de la etapa 2. La autorización real se realiza en AuthService."""
import os
from datetime import datetime
import logging

import traceback
import uuid
from zoneinfo import ZoneInfo

import streamlit as st

from cafae.auth import AuthService
from cafae.security import ROLES, SessionError, UserError

st.set_page_config(page_title='CAFAE · UGEL Chepén', page_icon='🔐', layout='wide')
service = AuthService()


def notify(message):
    st.session_state['notice'] = message
    st.rerun()


def sign_out():
    service.logout(st.session_state.get('token'))
    st.session_state.clear()
    notify('Sesión cerrada.')


def login_page():
    _, middle, _ = st.columns([1, 1.2, 1])
    with middle:
        st.space('large')
        logo_path = 'assets/logo_ugel.png' if os.path.exists('assets/logo_ugel.png') else 'assets/identidad_ugel.jpeg'
        st.image(logo_path, width=120)
        st.caption('UGEL CHEPÉN')
        st.title('Planillas CAFAE')
        st.write('Ingresa con tu cuenta para acceder al sistema de gestión de planillas.')
        with st.form('login', clear_on_submit=True):
            username = st.text_input('Usuario', max_chars=80, autocomplete='username')
            password = st.text_input('Contraseña', type='password', max_chars=128, autocomplete='current-password')
            submitted = st.form_submit_button('Iniciar sesión', type='primary', width='stretch')
        if submitted:
            # Despliegue solo en loopback: límite global local además del límite por cuenta.
            # No confiar en IP/cabeceras de Streamlit para una frontera de seguridad.
            st.session_state['token'] = service.login(username, password, origin='local')
            st.rerun()
        st.caption('Si necesitas una cuenta o restablecer tu acceso, comunícate con el administrador.')


def password_form(token, required=False):
    st.subheader('Cambiar contraseña')
    if required:
        st.info('Tu cuenta usa una contraseña temporal. Cámbiala para continuar.')
    st.caption('Usa entre 12 y 128 caracteres. Una frase larga es fácil de recordar.')
    with st.form('change_password', clear_on_submit=True):
        current = st.text_input('Contraseña actual', type='password', max_chars=128, autocomplete='current-password')
        new = st.text_input('Nueva contraseña', type='password', max_chars=128, autocomplete='new-password')
        repeated = st.text_input('Repite la nueva contraseña', type='password', max_chars=128, autocomplete='new-password')
        submitted = st.form_submit_button('Guardar nueva contraseña', type='primary')
    if submitted:
        if new != repeated:
            raise UserError('Las contraseñas nuevas no coinciden.')
        service.change_password(token, current, new)
        st.session_state.clear()
        notify('Contraseña actualizada. Inicia sesión con tu nueva contraseña.')


def users_page(token):
    st.title('Usuarios')
    st.write('Administra las cuentas y los permisos de acceso.')
    users = service.list_users(token)
    st.dataframe([{'Usuario': u['usuario'], 'Nombre completo': u['nombre_completo'], 'Rol': u['rol'],
                   'Estado': 'Activo' if u['activo'] else 'Inactivo',
                   'Cambio de contraseña': 'Pendiente' if u['debe_cambiar_password'] else 'Completado'} for u in users],
                 hide_index=True, width='stretch')
    create, edit, reset = st.tabs(['Crear usuario', 'Editar cuenta', 'Restablecer acceso'])
    with create:
        with st.form('create_user', clear_on_submit=True):
            a, b = st.columns(2)
            username = a.text_input('Nuevo usuario', max_chars=80)
            name = b.text_input('Nombre completo', max_chars=200)
            role = st.selectbox('Rol de la nueva cuenta', ROLES, index=2)
            password = st.text_input('Contraseña temporal', type='password', max_chars=128, autocomplete='new-password')
            repeat = st.text_input('Repite la contraseña temporal', type='password', max_chars=128, autocomplete='new-password')
            st.caption('La persona deberá cambiar esta contraseña al ingresar por primera vez.')
            submitted = st.form_submit_button('Crear usuario', type='primary')
        if submitted:
            if password != repeat:
                raise UserError('Las contraseñas temporales no coinciden.')
            service.create_user(token, username, name, role, password)
            notify('Usuario creado. El cambio de contraseña será obligatorio al ingresar.')
    labels = {u['id']: f"{u['usuario']} · {u['nombre_completo']}" for u in users}
    by_id = {u['id']: u for u in users}
    with edit:
        selected = st.selectbox('Cuenta para editar', labels, format_func=labels.get, key='edit_user_id')
        target = by_id[selected]
        # La revisión forma parte del formulario: un envío viejo no sobrescribe cambios ajenos.
        with st.form(f"edit_user_{selected}_{target['revision']}"):
            name = st.text_input('Nombre completo de la cuenta', value=target['nombre_completo'], max_chars=200)
            role = st.selectbox('Rol de la cuenta', ROLES, index=ROLES.index(target['rol']))
            active = st.checkbox('Cuenta activa', value=target['activo'])
            confirmed = st.checkbox('Confirmo los cambios de esta cuenta')
            st.caption('Cambiar el rol o desactivar la cuenta cierra sus sesiones. El historial se conserva.')
            submitted = st.form_submit_button('Guardar cambios', type='primary')
        if submitted:
            if not confirmed:
                raise UserError('Confirma los cambios antes de guardar.')
            service.update_user(token, selected, target['revision'], name, role, active)
            notify('Cuenta actualizada.')
    with reset:
        selected = st.selectbox('Cuenta para restablecer', labels, format_func=labels.get, key='reset_user_id')
        target = by_id[selected]
        with st.form(f"reset_{selected}_{target['revision']}", clear_on_submit=True):
            password = st.text_input('Nueva contraseña temporal', type='password', max_chars=128, autocomplete='new-password')
            repeat = st.text_input('Repite la nueva contraseña temporal', type='password', max_chars=128, autocomplete='new-password')
            confirmed = st.checkbox('Confirmo el restablecimiento y cierre de sus sesiones')
            submitted = st.form_submit_button('Restablecer acceso')
        if submitted:
            if not confirmed:
                raise UserError('Confirma el restablecimiento antes de continuar.')
            if password != repeat:
                raise UserError('Las contraseñas temporales no coinciden.')
            service.reset_password(token, selected, target['revision'], password)
            notify('Acceso restablecido. La persona deberá cambiar su contraseña al ingresar.')


def main():
    notice = st.session_state.pop('notice', None)
    if notice:
        st.success(notice)
    token = st.session_state.get('token')
    if not token:
        login_page()
        return
    user = service.current_user(token)
    with st.sidebar:
        logo_path = 'assets/logo_ugel.png' if os.path.exists('assets/logo_ugel.png') else 'assets/identidad_ugel.jpeg'
        st.image(logo_path, width=105)
        st.caption('UGEL CHEPÉN')
        st.header('CAFAE')
        st.write(user['nombre_completo'])
        st.caption(user['rol'].capitalize())
        st.caption(datetime.now(ZoneInfo('America/Lima')).strftime('%d/%m/%Y'))
        if st.button('Cerrar sesión', width='stretch'):
            sign_out()
        options = ['Inicio', 'Planillas', 'Importar Descuentos', 'Documentos', 'Personal', 'Reportes', 'Catálogos', 'Mi cuenta']
        if user['rol'] == 'ADMINISTRADOR':
            options.insert(7, 'Usuarios')
            options.insert(8, 'Auditoría')
        page = st.radio('Navegación', options)
    if user['debe_cambiar_password']:
        password_form(token, required=True)
    elif page == 'Planillas':
        from cafae.ui.planillas import render_planillas_view
        render_planillas_view(token, user['rol'])
    elif page == 'Importar Descuentos':
        from cafae.ui.importaciones import render_importaciones_view
        render_importaciones_view(token, user['rol'])
    elif page == 'Documentos':
        from cafae.ui.documentos import render_documentos_view
        render_documentos_view(token, user['rol'])
    elif page == 'Personal':
        from cafae.ui.trabajadores import render_trabajadores_view
        render_trabajadores_view(token, user['rol'])
    elif page == 'Reportes':
        from cafae.ui.reportes import render_reportes_view
        render_reportes_view(token, user['rol'])
    elif page == 'Catálogos':
        from cafae.ui.catalogos import render_catalogos_view
        render_catalogos_view(token, user['rol'])
    elif page == 'Usuarios':
        users_page(token)
    elif page == 'Auditoría':
        from cafae.ui.auditoria import render_auditoria_view
        render_auditoria_view(token, user['rol'])
    elif page == 'Mi cuenta':
        st.title('Mi cuenta')
        st.write(f"Usuario: {user['usuario']}")
        password_form(token)
    else:
        service.require_permission(token, 'consultar')
        from cafae.reportes import ReporteService
        rep_service = ReporteService()
        dash = rep_service.get_dashboard_summary(token)

        st.caption('PANEL DE CONTROL PRINCIPAL')
        st.title('Sistema de Gestión de Planillas CAFAE')
        st.write(f"Bienvenido/a, **{user['nombre_completo']}** ({user['rol'].capitalize()}).")

        # Dos tarjetas principales grandes (II.EE. y Sede)
        st.write('### 📌 Estado de Planillas')
        col_t1, col_t2 = st.columns(2)

        with col_t1:
            st.subheader('🏫 Instituciones Educativas (II.EE.)')
            if dash['iiee']:
                i = dash['iiee']
                est = i['estado']
                badge = '🟢 Cerrada' if est == 'CERRADA' else ('🟡 En Revisión' if est == 'EN_REVISION' else '⚪ Borrador')
                st.write(f"**Último Periodo:** `{i['anio']}-{i['mes']:02d}` · Versión `v{i['numero']}` ({badge})")
                c1, c2 = st.columns(2)
                c1.metric('Personal en Planilla', i['total_trabajadores'] or 'En edición')
                neto_str = f"S/ {i['total_neto']:.2f}" if i['total_neto'] is not None else 'En edición'
                c2.metric('Líquido Neto', neto_str)
            else:
                st.info('Aún no se ha generado una planilla para II.EE.')

        with col_t2:
            st.subheader('🏢 Sede UGEL Chepén')
            if dash['sede']:
                s = dash['sede']
                est = s['estado']
                badge = '🟢 Cerrada' if est == 'CERRADA' else ('🟡 En Revisión' if est == 'EN_REVISION' else '⚪ Borrador')
                st.write(f"**Último Periodo:** `{s['anio']}-{s['mes']:02d}` · Versión `v{s['numero']}` ({badge})")
                c1, c2 = st.columns(2)
                c1.metric('Personal en Planilla', s['total_trabajadores'] or 'En edición')
                neto_str = f"S/ {s['total_neto']:.2f}" if s['total_neto'] is not None else 'En edición'
                c2.metric('Líquido Neto', neto_str)
            else:
                st.info('Aún no se ha generado una planilla para Sede UGEL.')

        st.divider()

        # Métricas generales y alertas accionables
        st.write('### 📊 Indicadores Institucionales')
        m1, m2, m3 = st.columns(3)
        m1.metric('Trabajadores Activos en el Maestro', dash['trabajadores_activos'])
        m2.metric('Instituciones Educativas Activas', dash['instituciones_activas'])
        m3.metric('Alertas de Neto Negativo en Borrador', dash['alertas_neto_negativo'])

        if dash['alertas_neto_negativo'] > 0:
            st.warning(f"⚠️ Existen {dash['alertas_neto_negativo']} registros con líquido neto negativo en versiones abiertas. Revíselos desde el Editor de Planilla.")


try:
    main()
except SessionError as exc:
    st.session_state.clear()
    st.session_state['notice'] = str(exc)
    st.rerun()
except UserError as exc:
    st.error(str(exc))
except Exception as exc:
    reference = uuid.uuid4().hex[:12]
    # No registrar mensajes de excepción SQL: podrían incluir datos o parámetros sensibles.
    frames = [(frame.filename, frame.lineno, frame.name) for frame in traceback.extract_tb(exc.__traceback__)]
    logging.error('Error %s (%s): %s', reference, type(exc).__name__, frames)
    st.error(f'No pudimos completar la operación. Inténtalo nuevamente. Referencia: {reference}')
