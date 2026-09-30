"""Generador de datos masivos para CAFAE UGEL Chepén:
- 140 trabajadores de IIEE con distribución completa por instituciones y metas
- 25 trabajadores de SEDE
- 4 nuevas instituciones en Inicial, Primaria y Secundaria
- Planillas de Enero, Febrero, Marzo, Abril y Mayo 2026 (IIEE y SEDE)
- Descuentos realistas (0 o 10 soles) y casos de licencias (1 a 5 días)
"""
import random

APELLIDOS = [
    "QUISPE", "FLORES", "RODRIGUEZ", "SANCHEZ", "GARCIA", "ROJAS", "DIAZ", "TORRES",
    "LOPEZ", "GONZALES", "PEREZ", "CHAVEZ", "VASQUEZ", "RAMOS", "CASTILLO", "ALVAREZ",
    "ESPINOZA", "MENDOZA", "GUTIERREZ", "HERRERA", "HUAMAN", "VARGAS", "FERNANDEZ", "ALVA",
    "CUEVA", "BAZAN", "PAREDES", "CABRERA", "JIMENEZ", "SALDAÑA", "VALENCIA", "MONTALVO",
    "ZAPATA", "HERNANDEZ", "INFANTE", "CORREA", "BECERRA", "MORI", "ORTEGA", "ARAUJO",
    "CHAVESTA", "DAVILA", "ESTRADA", "FIGUEROA", "MALCA", "JAUREGUI", "VIGO", "BUSTAMANTE",
    "SALAZAR", "TANTALEAN", "MURIEL", "GUEVARA", "UBILLUS", "YPARRAGUIRRE", "ZAMORA", "CORONADO",
    "VALDIVIA", "CHUNGA", "ALVITEZ", "BARRUETO", "MONCADA", "LINGAN", "CUSTODIO", "IPANAQUE"
]

NOMBRES_M = [
    "JUAN CARLOS", "JOSE LUIS", "SEGUNDO TEOFILO", "CARLOS ENRIQUE", "VICTOR MANUEL",
    "PEDRO WILFREDO", "RAUL EDGARDO", "JORGE LUIS", "CESAR AUGUSTO", "MANUEL ENRIQUE",
    "FERNANDO JAVIER", "LUIS ALBERTO", "ROBERTO CARLOS", "DANIEL RICARDO", "HECTOR DAVID",
    "OSCAR EDUARDO", "FELIX ALONSO", "SEGUNDO RAMIRO", "CARLOS ALBERTO", "PEDRO PABLO",
    "VICTOR RAUL", "GUILLERMO ALFREDO", "JOSE SANTOS", "MIGUEL ANGEL", "WALTER DAVID"
]

NOMBRES_F = [
    "MIRTHA MARLENE", "ELIZABETH LUZ", "MARIA ROSARIO", "OLGA LIDIA", "MARTHA ELENA",
    "DORA ALICIA", "SONIA MARIBEL", "CARMEN BEATRIZ", "MARIA ISABEL", "ROSA ELVIRA",
    "CARMEN ROSA", "ANA MARIA", "GLORIA TERESA", "PATRICIA ELIZABETH", "MONICA BEATRIZ",
    "YOLANDA BEATRIZ", "TERESA DE JESUS", "SILVIA MERCEDES", "LIDIA MARLENE", "SUSANA BEATRIZ",
    "LUCIA DEL PILAR", "ROCIO DEL CARMEN", "ELENA MERCEDES", "BLANCA NIEVES", "IRMA YOLANDA"
]

CARGOS_IIEE = [
    ("Auxiliar de Biblioteca", "AA", "NOMBRADO", 1350.00),
    ("Trabajador de Servicio", "AE", "NOMBRADO", 1350.00),
    ("Trabajador de Servicio", "AF", "CONTRATADO", 1350.00),
    ("Técnico Administrativo", "TA", "NOMBRADO", 1370.00),
    ("Oficinista", "AB", "NOMBRADO", 1350.00),
    ("Secretaria", "TC", "NOMBRADO", 1370.00),
    ("Auxiliar de Laboratorio", "TB", "NOMBRADO", 1370.00),
    ("Secretaria", "TE", "NOMBRADO", 1370.00),
    ("Oficinista", "AC", "NOMBRADO", 1350.00),
    ("Auxiliar de Laboratorio", "TF", "NOMBRADO", 1370.00),
    ("Técnico Administrativo", "TD", "NOMBRADO", 1370.00),
    ("Trabajador de Servicio", "AA", "NOMBRADO", 1350.00)
]

PENSIONES = ["ONP 19990", "AFP INTEGRA", "AFP PRIMA", "AFP PROFUTURO", "AFP HABITAT"]


def main():
    sql = []
    sql.append("-- =============================================================================")
    sql.append("-- POBLAMIENTO MASIVO OFICIAL: 140 IIEE, 25 SEDE, NUEVAS INSTITUCIONES Y PLANILLAS")
    sql.append("-- =============================================================================")
    sql.append("SET client_encoding = 'UTF8';")
    sql.append("SET search_path TO cafae, public;")
    sql.append("")
    sql.append("BEGIN;")
    sql.append("")

    # 1. Nuevas Instituciones
    sql.append("-- 1. NUEVAS INSTITUCIONES EDUCATIVAS")
    sql.append("""INSERT INTO instituciones (codigo_modular, nombre, nivel_id, distrito, meta_id, activo)
SELECT ie.codigo_modular, ie.nombre, n.id, ie.distrito, m.id, true
FROM (VALUES
    -- I.E. N° 80382 'Carlos A. Olivares' (Primaria y Secundaria)
    ('0341701', 'I.E. N° 80382 Carlos A. Olivares', 'Primaria', 'Chepén', '0012'),
    ('0341702', 'I.E. N° 80382 Carlos A. Olivares', 'Secundaria', 'Chepén', '0014'),
    -- I.E. N° 80386 'Santa Rosa' (Inicial y Primaria)
    ('0341711', 'I.E. N° 80386 Santa Rosa', 'Inicial-Jardín', 'Chepén', '0011'),
    ('0341712', 'I.E. N° 80386 Santa Rosa', 'Primaria', 'Chepén', '0012'),
    -- I.E. N° 80830 'Zoila Hora de Robles' (Primaria y Secundaria)
    ('0341721', 'I.E. N° 80830 Zoila Hora de Robles', 'Primaria', 'Chepén', '0012'),
    ('0341722', 'I.E. N° 80830 Zoila Hora de Robles', 'Secundaria', 'Chepén', '0014'),
    -- I.E. N° 81031 (Primaria)
    ('0341731', 'I.E. N° 81031', 'Primaria', 'Chepén', '0012')
) AS ie(codigo_modular, nombre, nivel_nombre, distrito, meta_codigo)
JOIN niveles n ON n.nombre = ie.nivel_nombre
LEFT JOIN metas m ON m.codigo = ie.meta_codigo
ON CONFLICT (codigo_modular) DO UPDATE SET 
    nombre = EXCLUDED.nombre, 
    nivel_id = EXCLUDED.nivel_id, 
    distrito = EXCLUDED.distrito, 
    meta_id = EXCLUDED.meta_id, 
    activo = true;
""")

    # 2. SEDE: Asegurar 25 personas
    sql.append("-- 2. SEDE: 25 TRABAJADORES EXACTOS")
    sql.append("""INSERT INTO trabajadores (
    dni, apellidos, nombres, tipo, area_id, cargo_id, categoria_id, situacion_id, subtipo_id,
    ley, jornada_laboral, cuenta_multired, importe, activo, tipo_pago,
    fecha_nacimiento, regimen_laboral, regimen_pensionario, tiempo_servicio_texto, fecha_ingreso
)
SELECT
    '64567825', 'CABRERA BAZAN', 'ELENA MERCEDES', 'SEDE', a.id, c.id, cat.id, s.id, sub.id,
    '276', '40', '04231100225', 1650.00, true, 'CUENTA',
    '1978-08-15'::date, '276', 'AFP INTEGRA', '14-06-12', '2012-03-01'::date
FROM areas_sede a
JOIN cargos c ON c.nombre = 'Secretaria I'
JOIN categorias cat ON cat.codigo = 'TA'
JOIN situaciones s ON s.nombre = 'NOMBRADO'
JOIN subtipos_trabajador sub ON sub.nombre = 'ADMINISTRATIVO'
WHERE a.nombre = 'GESTIÓN ADMINISTRATIVA'
ON CONFLICT (dni) DO UPDATE SET activo = true;
""")

    # 3. IIEE: Generar los trabajadores hasta completar 140
    # Obtenemos las IIEE con sus metas
    # Distribución meta objetivo:
    # 0011 (Inicial): 20
    # 0012 (Primaria): 50
    # 0014 (Secundaria): 50
    # 0030 (Especial): 8
    # 0042 (Técnico): 6
    # 0044 (Alternativa): 6
    # Total: 140
    sql.append("-- 3. TRABAJADORES DE II.EE. (140 EN TOTAL)")

    # Códigos modulares por nivel
    mods_por_meta = {
        '0011': ['0341257', '0341711'],
        '0012': ['0341588', '0342115', '0341701', '0341712', '0341721', '0341731'],
        '0014': ['0341620', '0341893', '0341702', '0341722'],
        '0030': ['0524181'],
        '0042': ['0689452'],
        '0044': ['0741289']
    }

    # Ya tenemos 16 trabajadores existentes: 70112201 a 70112216
    # Generamos desde 70112217 hasta 70112340 (124 adicionales)
    trab_iiee = []
    # Definir cuántos adicionales por meta:
    # 0011: 2 actuales -> 18 adicionales (total 20)
    # 0012: 3 actuales -> 47 adicionales (total 50)
    # 0014: 7 actuales -> 43 adicionales (total 50)
    # 0030: 2 actuales -> 6 adicionales (total 8)
    # 0042: 1 actual   -> 5 adicionales (total 6)
    # 0044: 1 actual   -> 5 adicionales (total 6)
    metas_adicionales = (
        ['0011'] * 18 +
        ['0012'] * 47 +
        ['0014'] * 43 +
        ['0030'] * 6 +
        ['0042'] * 5 +
        ['0044'] * 5
    )

    dni_num = 70112217
    random.seed(42)

    for idx, meta in enumerate(metas_adicionales):
        dni = str(dni_num)
        ap1 = APELLIDOS[idx % len(APELLIDOS)]
        ap2 = APELLIDOS[(idx + 13) % len(APELLIDOS)]
        apellidos = f"{ap1} {ap2}"
        if idx % 2 == 0:
            nombres = NOMBRES_M[idx % len(NOMBRES_M)]
        else:
            nombres = NOMBRES_F[idx % len(NOMBRES_F)]

        mods_disp = mods_por_meta[meta]
        cod_mod = mods_disp[idx % len(mods_disp)]

        cargo, cat, sit, imp = CARGOS_IIEE[idx % len(CARGOS_IIEE)]
        cuenta = f"042312{dni_num:05d}"
        f_nac = f"{1965 + (idx % 30):04d}-{(1 + idx % 12):02d}-{(1 + idx % 28):02d}"
        pension = PENSIONES[idx % len(PENSIONES)]
        ts_anios = 5 + (idx % 20)
        ts_meses = (idx * 2) % 12
        ts_dias = (idx * 3) % 28 + 1
        ts_str = f"{ts_anios:02d}-{ts_meses:02d}-{ts_dias:02d}"
        f_ingreso = f"{2005 + (idx % 15):04d}-03-01"

        trab_iiee.append((
            dni, apellidos, nombres, cod_mod, cargo, cat, sit, imp, cuenta,
            f_nac, pension, ts_str, f_ingreso
        ))
        dni_num += 1

    # Insertar en trabajadores
    sql.append("INSERT INTO trabajadores (")
    sql.append("    dni, apellidos, nombres, tipo, institucion_id, nivel_id, cargo_id, categoria_id, situacion_id, subtipo_id,")
    sql.append("    ley, jornada_laboral, cuenta_multired, importe, activo, tipo_pago,")
    sql.append("    fecha_nacimiento, regimen_laboral, regimen_pensionario, tiempo_servicio_texto, fecha_ingreso")
    sql.append(")")
    sql.append("SELECT")
    sql.append("    t.dni, t.apellidos, t.nombres, 'IIEE', i.id, i.nivel_id, c.id, cat.id, s.id, sub.id,")
    sql.append("    '276', '40', t.cuenta, t.importe, true, 'CUENTA',")
    sql.append("    t.f_nac::date, '276', t.pension, t.ts_str, t.f_ingreso::date")
    sql.append("FROM (VALUES")
    
    lineas_vals = []
    for t in trab_iiee:
        lineas_vals.append(
            f"    ('{t[0]}', '{t[1]}', '{t[2]}', '{t[3]}', '{t[4]}', '{t[5]}', '{t[6]}', {t[7]:.2f}, '{t[8]}', '{t[9]}', '{t[10]}', '{t[11]}', '{t[12]}')"
        )
    sql.append(",\n".join(lineas_vals))
    sql.append(") AS t(dni, apellidos, nombres, cod_mod, cargo_nombre, cat_codigo, situacion_nombre, importe, cuenta, f_nac, pension, ts_str, f_ingreso)")
    sql.append("JOIN instituciones i ON i.codigo_modular = t.cod_mod")
    sql.append("JOIN cargos c ON c.nombre = t.cargo_nombre")
    sql.append("JOIN categorias cat ON cat.codigo = t.cat_codigo")
    sql.append("JOIN situaciones s ON s.nombre = t.situacion_nombre")
    sql.append("JOIN subtipos_trabajador sub ON sub.nombre = 'ADMINISTRATIVO'")
    sql.append("ON CONFLICT (dni) DO UPDATE SET")
    sql.append("    apellidos = EXCLUDED.apellidos, nombres = EXCLUDED.nombres, institucion_id = EXCLUDED.institucion_id,")
    sql.append("    nivel_id = EXCLUDED.nivel_id, cargo_id = EXCLUDED.cargo_id, categoria_id = EXCLUDED.categoria_id,")
    sql.append("    situacion_id = EXCLUDED.situacion_id, importe = EXCLUDED.importe, cuenta_multired = EXCLUDED.cuenta_multired,")
    sql.append("    fecha_nacimiento = EXCLUDED.fecha_nacimiento, regimen_pensionario = EXCLUDED.regimen_pensionario,")
    sql.append("    tiempo_servicio_texto = EXCLUDED.tiempo_servicio_texto, fecha_ingreso = EXCLUDED.fecha_ingreso, activo = true;")
    sql.append("")

    # 4. Generación de periodos y planillas múltiples
    # Meses 1 a 5 de 2026
    sql.append("-- 4. PERIODOS Y PLANILLAS MÚLTIPLES (ENERO A MAYO 2026)")
    sql.append("""
-- Desactivar triggers de integridad para inicialización masiva
ALTER TABLE planilla_versiones DISABLE TRIGGER version_integridad;
ALTER TABLE planilla_detalle DISABLE TRIGGER a_detalle_abierto;
ALTER TABLE planilla_descuentos DISABLE TRIGGER a_descuento_abierto;
ALTER TABLE planilla_firmas DISABLE TRIGGER a_firma_abierta;
ALTER TABLE planilla_programas DISABLE TRIGGER a_programa_abierto;

DO $$
DECLARE
    m_mes INT;
    v_per_id BIGINT;
    v_plan_iiee_id BIGINT;
    v_plan_sede_id BIGINT;
    v_ver_iiee_id BIGINT;
    v_ver_sede_id BIGINT;
    v_estado VARCHAR(15);
    v_orden INT;
    r RECORD;
    v_dias_lic INT;
    v_monto_lic NUMERIC(12,2);
    v_tot_desc NUMERIC(12,2);
    v_neto NUMERIC(12,2);
BEGIN
    FOR m_mes IN 1..5 LOOP
        -- Estado: Meses 1 y 2 CERRADAS, Mes 3 CERRADA (o EN_REVISION), Mes 4 EN_REVISION, Mes 5 BORRADOR
        IF m_mes IN (1, 2, 3) THEN
            v_estado := 'CERRADA';
        ELSIF m_mes = 4 THEN
            v_estado := 'EN_REVISION';
        ELSE
            v_estado := 'BORRADOR';
        END IF;

        -- 1. Periodo
        INSERT INTO periodos (anio, mes) VALUES (2026, m_mes)
        ON CONFLICT (anio, mes) DO NOTHING;
        SELECT id INTO v_per_id FROM periodos WHERE anio = 2026 AND mes = m_mes;

        -- 2. Planilla IIEE
        SELECT id INTO v_plan_iiee_id FROM planillas WHERE periodo_id = v_per_id AND tipo = 'IIEE';
        IF v_plan_iiee_id IS NULL THEN
            INSERT INTO planillas (periodo_id, tipo, creada_por)
            VALUES (v_per_id, 'IIEE', 1) RETURNING id INTO v_plan_iiee_id;
        END IF;

        -- Versión 1 de IIEE (se crea en BORRADOR y se cerrará al final con totales)
        SELECT id INTO v_ver_iiee_id FROM planilla_versiones WHERE planilla_id = v_plan_iiee_id AND numero = 1;
        IF v_ver_iiee_id IS NULL THEN
            INSERT INTO planilla_versiones (planilla_id, numero, estado, origen, version_calculo, creada_por)
            VALUES (v_plan_iiee_id, 1, 'BORRADOR', 'MAESTRO', 'OFICIAL_V1', 1)
            RETURNING id INTO v_ver_iiee_id;
        ELSE
            UPDATE planilla_versiones SET estado = 'BORRADOR',
                cerrada_por = NULL,
                cerrada_en = NULL,
                total_trabajadores = NULL,
                total_importe = NULL,
                total_descuentos = NULL,
                total_neto = NULL
            WHERE id = v_ver_iiee_id;
        END IF;

        -- Programas y Firmas para IIEE
        DELETE FROM planilla_programas WHERE version_id = v_ver_iiee_id;
        INSERT INTO planilla_programas(version_id, programa_id, padre_id, codigo, nombre, orden)
        SELECT v_ver_iiee_id, id, padre_id, codigo, nombre, orden FROM programas WHERE activo = true;

        DELETE FROM planilla_firmas WHERE version_id = v_ver_iiee_id;
        INSERT INTO planilla_firmas(version_id, posicion, firma_id, nombre_completo, cargo)
        SELECT v_ver_iiee_id, row_number() OVER (ORDER BY id ASC), id, nombre_completo, cargo
        FROM firmas WHERE activo = true ORDER BY id ASC LIMIT 4;

        -- Detalle IIEE (Limpiar y volver a poblar con los 140 trabajadores ordenados por meta y apellidos)
        DELETE FROM planilla_descuentos WHERE detalle_id IN (SELECT id FROM planilla_detalle WHERE version_id = v_ver_iiee_id);
        DELETE FROM planilla_detalle WHERE version_id = v_ver_iiee_id;

        v_orden := 1;
        FOR r IN (
            SELECT t.*, i.nombre AS inst_nom, i.codigo_modular AS inst_mod, i.distrito AS inst_dist,
                   n.nombre AS niv_nom, m.id AS met_id, m.codigo AS m_cod, m.descripcion AS m_desc,
                   c.nombre AS car_nom, cat.codigo AS cat_cod, cat.descripcion AS cat_desc,
                   s.nombre AS sit_nom
            FROM trabajadores t
            JOIN instituciones i ON i.id = t.institucion_id
            JOIN niveles n ON n.id = t.nivel_id
            JOIN metas m ON m.id = i.meta_id
            JOIN cargos c ON c.id = t.cargo_id
            JOIN categorias cat ON cat.id = t.categoria_id
            JOIN situaciones s ON s.id = t.situacion_id
            WHERE t.tipo = 'IIEE' AND t.activo = true
            ORDER BY m.codigo ASC, t.apellidos ASC, t.nombres ASC
        ) LOOP
            -- Casos de licencia: 1 a 3 días cada ciertos trabajadores
            IF v_orden IN (7, 23, 45, 82, 115) THEN
                v_dias_lic := 1;
            ELSIF v_orden IN (14, 56, 98) THEN
                v_dias_lic := 2;
            ELSIF v_orden IN (33, 71, 126) THEN
                v_dias_lic := 3;
            ELSE
                v_dias_lic := 0;
            END IF;

            v_monto_lic := round((r.importe / 30.0) * v_dias_lic, 2);

            INSERT INTO planilla_detalle (
                version_id, trabajador_id, orden, dni, apellidos, nombres,
                institucion_id, institucion_nombre, codigo_modular, distrito,
                nivel_id, nivel_nombre, meta_id, meta_codigo, meta_descripcion,
                subtipo, cargo, situacion, categoria, categoria_descripcion,
                fecha_nacimiento, ley, regimen_laboral, jornada_laboral, cuenta_multired,
                importe, dias_licencia, monto_licencia, total_descuentos, neto,
                regimen_pensionario, fecha_ingreso, tiempo_servicio_texto, tipo_pago
            ) VALUES (
                v_ver_iiee_id, r.id, v_orden, r.dni, r.apellidos, r.nombres,
                r.institucion_id, r.inst_nom, r.inst_mod, r.inst_dist,
                r.nivel_id, r.niv_nom, r.met_id, r.m_cod, r.m_desc,
                'ADMINISTRATIVO', r.car_nom, r.sit_nom, r.cat_cod, r.cat_desc,
                r.fecha_nacimiento, '276', '276', '40', r.cuenta_multired,
                r.importe, v_dias_lic, v_monto_lic, 0.00, r.importe - v_monto_lic,
                r.regimen_pensionario, r.fecha_ingreso, r.tiempo_servicio_texto, 'CUENTA'
            );

            v_orden := v_orden + 1;
        END LOOP;

        -- 3. Planilla SEDE (25 trabajadores)
        SELECT id INTO v_plan_sede_id FROM planillas WHERE periodo_id = v_per_id AND tipo = 'SEDE';
        IF v_plan_sede_id IS NULL THEN
            INSERT INTO planillas (periodo_id, tipo, creada_por)
            VALUES (v_per_id, 'SEDE', 1) RETURNING id INTO v_plan_sede_id;
        END IF;

        SELECT id INTO v_ver_sede_id FROM planilla_versiones WHERE planilla_id = v_plan_sede_id AND numero = 1;
        IF v_ver_sede_id IS NULL THEN
            INSERT INTO planilla_versiones (planilla_id, numero, estado, origen, version_calculo, creada_por)
            VALUES (v_plan_sede_id, 1, 'BORRADOR', 'MAESTRO', 'OFICIAL_V1', 1)
            RETURNING id INTO v_ver_sede_id;
        ELSE
            UPDATE planilla_versiones SET estado = 'BORRADOR',
                cerrada_por = NULL,
                cerrada_en = NULL,
                total_trabajadores = NULL,
                total_importe = NULL,
                total_descuentos = NULL,
                total_neto = NULL
            WHERE id = v_ver_sede_id;
        END IF;

        DELETE FROM planilla_programas WHERE version_id = v_ver_sede_id;
        INSERT INTO planilla_programas(version_id, programa_id, padre_id, codigo, nombre, orden)
        SELECT v_ver_sede_id, id, padre_id, codigo, nombre, orden FROM programas WHERE activo = true;

        DELETE FROM planilla_firmas WHERE version_id = v_ver_sede_id;
        INSERT INTO planilla_firmas(version_id, posicion, firma_id, nombre_completo, cargo)
        SELECT v_ver_sede_id, row_number() OVER (ORDER BY id ASC), id, nombre_completo, cargo
        FROM firmas WHERE activo = true ORDER BY id ASC LIMIT 3;

        DELETE FROM planilla_descuentos WHERE detalle_id IN (SELECT id FROM planilla_detalle WHERE version_id = v_ver_sede_id);
        DELETE FROM planilla_detalle WHERE version_id = v_ver_sede_id;

        v_orden := 1;
        FOR r IN (
            SELECT t.*, a.nombre AS ar_nom, m.id AS met_id, m.codigo AS m_cod, m.descripcion AS m_desc,
                   c.nombre AS car_nom, cat.codigo AS cat_cod, cat.descripcion AS cat_desc,
                   s.nombre AS sit_nom
            FROM trabajadores t
            JOIN areas_sede a ON a.id = t.area_id
            JOIN metas m ON m.id = a.meta_id
            JOIN cargos c ON c.id = t.cargo_id
            JOIN categorias cat ON cat.id = t.categoria_id
            JOIN situaciones s ON s.id = t.situacion_id
            WHERE t.tipo = 'SEDE' AND t.activo = true
            ORDER BY a.nombre ASC, t.apellidos ASC, t.nombres ASC
        ) LOOP
            IF v_orden IN (5, 18) THEN
                v_dias_lic := 1;
            ELSIF v_orden = 12 THEN
                v_dias_lic := 2;
            ELSE
                v_dias_lic := 0;
            END IF;

            v_monto_lic := round((r.importe / 30.0) * v_dias_lic, 2);

            INSERT INTO planilla_detalle (
                version_id, trabajador_id, orden, dni, apellidos, nombres,
                area_id, area_nombre, meta_id, meta_codigo, meta_descripcion,
                subtipo, cargo, situacion, categoria, categoria_descripcion,
                fecha_nacimiento, ley, regimen_laboral, jornada_laboral, cuenta_multired,
                importe, dias_licencia, monto_licencia, total_descuentos, neto,
                regimen_pensionario, fecha_ingreso, tiempo_servicio_texto, tipo_pago
            ) VALUES (
                v_ver_sede_id, r.id, v_orden, r.dni, r.apellidos, r.nombres,
                r.area_id, r.ar_nom, r.met_id, r.m_cod, r.m_desc,
                'ADMINISTRATIVO', r.car_nom, r.sit_nom, r.cat_cod, r.cat_desc,
                r.fecha_nacimiento, '276', '276', '40', r.cuenta_multired,
                r.importe, v_dias_lic, v_monto_lic, 0.00, r.importe - v_monto_lic,
                r.regimen_pensionario, r.fecha_ingreso, r.tiempo_servicio_texto, 'CUENTA'
            );

            v_orden := v_orden + 1;
        END LOOP;

    END LOOP;
END $$;

-- 5. POBLAR LOS 7 DESCUENTOS PARA TODAS LAS PLANILLAS (0 o 10 soles habituales)
-- Tipo 1: PICHINCHA
INSERT INTO planilla_descuentos (detalle_id, tipo_descuento_id, monto, actualizado_por)
SELECT pd.id, 1, CASE WHEN (pd.orden % 5 = 0 OR pd.orden = 3) THEN 10.00 ELSE 0.00 END, 1
FROM planilla_detalle pd
ON CONFLICT (detalle_id, tipo_descuento_id) DO UPDATE SET monto = EXCLUDED.monto;

-- Tipo 2: CAJA SULLANA
INSERT INTO planilla_descuentos (detalle_id, tipo_descuento_id, monto, actualizado_por)
SELECT pd.id, 2, CASE WHEN (pd.orden % 4 = 1 OR pd.orden = 6) THEN 10.00 ELSE 0.00 END, 1
FROM planilla_detalle pd
ON CONFLICT (detalle_id, tipo_descuento_id) DO UPDATE SET monto = EXCLUDED.monto;

-- Tipo 3: SUB-CAFAE (10.00 en la mayoría)
INSERT INTO planilla_descuentos (detalle_id, tipo_descuento_id, monto, actualizado_por)
SELECT pd.id, 3, CASE WHEN (pd.orden % 3 <> 0) THEN 10.00 ELSE 0.00 END, 1
FROM planilla_detalle pd
ON CONFLICT (detalle_id, tipo_descuento_id) DO UPDATE SET monto = EXCLUDED.monto;

-- Tipo 4: BRENTA
INSERT INTO planilla_descuentos (detalle_id, tipo_descuento_id, monto, actualizado_por)
SELECT pd.id, 4, CASE WHEN (pd.orden % 6 = 2) THEN 10.00 ELSE 0.00 END, 1
FROM planilla_detalle pd
ON CONFLICT (detalle_id, tipo_descuento_id) DO UPDATE SET monto = EXCLUDED.monto;

-- Tipo 5: SITRASE
INSERT INTO planilla_descuentos (detalle_id, tipo_descuento_id, monto, actualizado_por)
SELECT pd.id, 5, CASE WHEN (pd.orden % 5 = 2) THEN 10.00 ELSE 0.00 END, 1
FROM planilla_detalle pd
ON CONFLICT (detalle_id, tipo_descuento_id) DO UPDATE SET monto = EXCLUDED.monto;

-- Tipo 6: SITASE
INSERT INTO planilla_descuentos (detalle_id, tipo_descuento_id, monto, actualizado_por)
SELECT pd.id, 6, CASE WHEN (pd.orden % 5 = 3) THEN 10.00 ELSE 0.00 END, 1
FROM planilla_detalle pd
ON CONFLICT (detalle_id, tipo_descuento_id) DO UPDATE SET monto = EXCLUDED.monto;

-- Tipo 7: OTROS
INSERT INTO planilla_descuentos (detalle_id, tipo_descuento_id, monto, actualizado_por)
SELECT pd.id, 7, CASE WHEN (pd.orden % 7 = 4) THEN 10.00 ELSE 0.00 END, 1
FROM planilla_detalle pd
ON CONFLICT (detalle_id, tipo_descuento_id) DO UPDATE SET monto = EXCLUDED.monto;

-- 6. Recalcular total_descuentos y neto en planilla_detalle
UPDATE planilla_detalle pd
SET 
    total_descuentos = pd.monto_licencia + COALESCE((
        SELECT sum(d.monto) FROM planilla_descuentos d WHERE d.detalle_id = pd.id
    ), 0.00),
    neto = pd.importe - (
        pd.monto_licencia + COALESCE((
            SELECT sum(d.monto) FROM planilla_descuentos d WHERE d.detalle_id = pd.id
        ), 0.00)
    ),
    actualizado_en = clock_timestamp();

-- 7. Consolidar totales y actualizar estados en planilla_versiones
-- Meses 1, 2 y 3 (Enero, Febrero, Marzo) a CERRADA:
UPDATE planilla_versiones pv
SET 
    estado = 'CERRADA',
    cerrada_por = 1,
    cerrada_en = now(),
    total_trabajadores = (SELECT count(*) FROM planilla_detalle WHERE version_id = pv.id),
    total_importe = (SELECT sum(importe) FROM planilla_detalle WHERE version_id = pv.id),
    total_descuentos = (SELECT sum(total_descuentos) FROM planilla_detalle WHERE version_id = pv.id),
    total_neto = (SELECT sum(neto) FROM planilla_detalle WHERE version_id = pv.id)
FROM planillas p
JOIN periodos per ON per.id = p.periodo_id
WHERE pv.planilla_id = p.id AND per.anio = 2026 AND per.mes IN (1, 2, 3);

-- Mes 4 (Abril) a EN_REVISION:
UPDATE planilla_versiones pv
SET 
    estado = 'EN_REVISION',
    cerrada_por = NULL,
    cerrada_en = NULL,
    total_trabajadores = NULL,
    total_importe = NULL,
    total_descuentos = NULL,
    total_neto = NULL
FROM planillas p
JOIN periodos per ON per.id = p.periodo_id
WHERE pv.planilla_id = p.id AND per.anio = 2026 AND per.mes = 4;

-- Mes 5 (Mayo) a BORRADOR:
UPDATE planilla_versiones pv
SET 
    estado = 'BORRADOR',
    cerrada_por = NULL,
    cerrada_en = NULL,
    total_trabajadores = NULL,
    total_importe = NULL,
    total_descuentos = NULL,
    total_neto = NULL
FROM planillas p
JOIN periodos per ON per.id = p.periodo_id
WHERE pv.planilla_id = p.id AND per.anio = 2026 AND per.mes = 5;

-- 8. Reactivar triggers de protección
ALTER TABLE planilla_versiones ENABLE TRIGGER version_integridad;
ALTER TABLE planilla_detalle ENABLE TRIGGER a_detalle_abierto;
ALTER TABLE planilla_descuentos ENABLE TRIGGER a_descuento_abierto;
ALTER TABLE planilla_firmas ENABLE TRIGGER a_firma_abierta;
ALTER TABLE planilla_programas ENABLE TRIGGER a_programa_abierto;

COMMIT;
""")

    with open("scripts/poblar_140_iiee_25_sede_y_mas_planillas.sql", "w", encoding="utf-8") as f:
        f.write("\n".join(sql))

    print("Archivo scripts/poblar_140_iiee_25_sede_y_mas_planillas.sql generado con éxito.")


if __name__ == "__main__":
    main()
