"""Puebla planillas de prueba reales para II.EE. y SEDE (Feb 2026 cerrada, Mar 2026 borrador)."""
import os
import sys
import secrets

# Asegurar path de importación
sys.path.insert(0, '/app')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from cafae.auth import AuthService
from cafae.planillas import PlanillaService
from cafae.security import digest, UserError


def main():
    auth = AuthService()
    pln = PlanillaService(auth_service=auth)

    with auth._transaction() as conn:
        # 1. Obtener usuario administrador activo
        admin = conn.execute(
            '''SELECT u.id, u.usuario, u.nombre_completo 
               FROM usuarios u 
               JOIN roles r ON r.id = u.rol_id 
               WHERE r.codigo = 'ADMINISTRADOR' AND u.activo = true 
               ORDER BY u.id ASC LIMIT 1'''
        ).fetchone()

        if not admin:
            print("ERROR: No se encontró ningún usuario con rol ADMINISTRADOR activo.")
            return

        print(f"-> Usando usuario administrador: {admin['usuario']} ({admin['nombre_completo']})")

        # 2. Generar token de sesión seguro
        raw_token = secrets.token_urlsafe(32)
        t_hash = digest(raw_token)
        conn.execute(
            '''INSERT INTO sesiones (usuario_id, token_hash, expira_en)
               VALUES (%s, %s, now() + interval '8 hours')''',
            (admin['id'], t_hash)
        )

    token = raw_token

    # 3. Obtener firmas vigentes a través de la transacción de datos autorizada
    with auth.data_transaction(token, 'consultar') as (conn, _):
        firmas_rows = conn.execute(
            'SELECT id, nombre_completo, cargo FROM firmas WHERE activo = true ORDER BY id ASC'
        ).fetchall()
        print(f"-> Firmas vigentes encontradas: {len(firmas_rows)}")
        firmas_ids = [f['id'] for f in firmas_rows]

    def buscar_o_crear(anio, mes, tipo):
        try:
            res = pln.crear_desde_maestro(token, anio, mes, tipo)
            print(f"  [+] Planilla {tipo} {mes:02d}/{anio} creada desde maestro (v_id: {res['version_id']}, personal: {res['trabajadores_copiados']})")
            return res['version_id']
        except UserError:
            with auth.data_transaction(token, 'consultar') as (c, _):
                row = c.execute(
                    '''SELECT pv.id FROM planilla_versiones pv
                       JOIN planillas p ON p.id = pv.planilla_id
                       JOIN periodos per ON per.id = p.periodo_id
                       WHERE per.anio = %s AND per.mes = %s AND p.tipo = %s
                       ORDER BY pv.numero DESC LIMIT 1''',
                    (anio, mes, tipo)
                ).fetchone()
                print(f"  [i] Planilla {tipo} {mes:02d}/{anio} ya existía (v_id: {row['id']})")
                return row['id']

    # =========================================================================
    # PERIODO FEBRERO 2026 (PLANILLAS CERRADAS)
    # =========================================================================
    print("\n--- Procesando Febrero 2026 (Historial Cerrado) ---")
    
    # A. Planilla II.EE. Febrero 2026
    v_iiee_feb = buscar_o_crear(2026, 2, 'IIEE')
    with auth.data_transaction(token, 'consultar') as (c, _):
        info = c.execute('SELECT estado, revision_edicion FROM planilla_versiones WHERE id = %s', (v_iiee_feb,)).fetchone()
    
    if info['estado'] != 'CERRADA' and len(firmas_ids) >= 4:
        try:
            res_cierre = pln.cerrar_version(token, v_iiee_feb, revision_esperada=info['revision_edicion'], firmas_ids=firmas_ids[:4])
            print(f"  [✓] Planilla IIEE Feb 2026 CERRADA formalmente. Total Neto: S/ {res_cierre['total_neto']:,.2f}")
        except UserError as e:
            print(f"  [!] IIEE Feb 2026 cierre: {e}")
    else:
        print(f"  [i] IIEE Feb 2026 ya está en estado {info['estado']}.")

    # B. Planilla SEDE Febrero 2026
    v_sede_feb = buscar_o_crear(2026, 2, 'SEDE')
    with auth.data_transaction(token, 'consultar') as (c, _):
        info_sede = c.execute('SELECT estado, revision_edicion FROM planilla_versiones WHERE id = %s', (v_sede_feb,)).fetchone()
    
    if info_sede['estado'] != 'CERRADA' and len(firmas_ids) >= 3:
        try:
            res_cierre = pln.cerrar_version(token, v_sede_feb, revision_esperada=info_sede['revision_edicion'], firmas_ids=firmas_ids[:3])
            print(f"  [✓] Planilla SEDE Feb 2026 CERRADA formalmente. Total Neto: S/ {res_cierre['total_neto']:,.2f}")
        except UserError as e:
            print(f"  [!] SEDE Feb 2026 cierre: {e}")
    else:
        print(f"  [i] SEDE Feb 2026 ya está en estado {info_sede['estado']}.")

    # =========================================================================
    # PERIODO MARZO 2026 (PLANILLAS EN BORRADOR / EDICIÓN ACTIVA)
    # =========================================================================
    print("\n--- Procesando Marzo 2026 (Planillas Abiertas / Borrador) ---")
    
    # A. Planilla II.EE. Marzo 2026
    v_iiee_mar = buscar_o_crear(2026, 3, 'IIEE')
    with auth.data_transaction(token, 'consultar') as (c, _):
        info_mar = c.execute('SELECT estado, revision_edicion FROM planilla_versiones WHERE id = %s', (v_iiee_mar,)).fetchone()
    
    # Aplicar un descuento demostrativo si está en borrador
    if info_mar['estado'] == 'BORRADOR':
        lineas = pln.list_lineas_edicion(token, v_iiee_mar)
        if lineas:
            primer_trab = lineas[0]
            try:
                pln.guardar_edicion_lote(
                    token,
                    v_iiee_mar,
                    revision_esperada=info_mar['revision_edicion'],
                    cambios=[{
                        'detalle_id': primer_trab['id'],
                        'importe': primer_trab['importe'],
                        'dias_licencia': 0,
                        'SUB_CAFAE': 50.00
                    }]
                )
                print(f"  [+] Descuento demostrativo aplicado a {primer_trab['apellidos']} {primer_trab['nombres']} (SUB_CAFAE: S/ 50.00)")
            except UserError as e:
                print(f"  [!] Marzo IIEE descuento: {e}")

    # B. Planilla SEDE Marzo 2026
    v_sede_mar = buscar_o_crear(2026, 3, 'SEDE')
    print(f"  [+] Planilla SEDE Mar 2026 lista para edición.")

    print("\n=== ¡Poblado de planillas de prueba completado exitosamente! ===")


if __name__ == '__main__':
    main()
