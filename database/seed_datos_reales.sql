-- =============================================================================
-- SEED DE DATOS REALES: CAFAE UGEL CHEPÉN
-- Catálogos institucionales, presupuestales y personal (II.EE. y SEDE)
-- =============================================================================
SET client_encoding = 'UTF8';
SET search_path TO cafae, public;

BEGIN;

SET LOCAL search_path TO cafae, public;

-- 1. NIVELES EDUCATIVOS (Fusión limpia de duplicados y actualización con tildes)
DO $$
DECLARE
    r RECORD;
    v_target_id BIGINT;
    v_dup_id BIGINT;
BEGIN
    FOR r IN SELECT * FROM (VALUES
        ('Inicial-Jardín', ARRAY['Inicial%', '%Jard%']),
        ('Primaria', ARRAY['Primaria%']),
        ('Secundaria', ARRAY['Secundaria%']),
        ('Básica Especial - Primaria', ARRAY['%Especial%']),
        ('Básica Alternativa - Avanzado', ARRAY['%Alternativa%']),
        ('Técnico Productiva', ARRAY['%Productiva%'])
    ) AS t(oficial, patrones)
    LOOP
        SELECT id INTO v_target_id FROM niveles WHERE nombre = r.oficial;
        IF v_target_id IS NULL THEN
            SELECT id INTO v_target_id FROM niveles 
            WHERE nombre LIKE ANY(r.patrones) ORDER BY id LIMIT 1;
            IF v_target_id IS NOT NULL THEN
                UPDATE niveles SET nombre = r.oficial WHERE id = v_target_id;
            ELSE
                INSERT INTO niveles (nombre, activo) VALUES (r.oficial, true) RETURNING id INTO v_target_id;
            END IF;
        END IF;

        FOR v_dup_id IN SELECT id FROM niveles WHERE id <> v_target_id AND nombre LIKE ANY(r.patrones)
        LOOP
            UPDATE instituciones SET nivel_id = v_target_id WHERE nivel_id = v_dup_id;
            UPDATE trabajadores SET nivel_id = v_target_id WHERE nivel_id = v_dup_id;
            DELETE FROM nivel_metas WHERE nivel_id = v_dup_id;
            DELETE FROM niveles WHERE id = v_dup_id;
        END LOOP;
    END LOOP;
END $$;

INSERT INTO niveles (nombre, activo) VALUES
    ('Inicial-Jardín', true),
    ('Primaria', true),
    ('Secundaria', true),
    ('Básica Especial - Primaria', true),
    ('Básica Alternativa - Avanzado', true),
    ('Técnico Productiva', true)
ON CONFLICT (nombre) DO UPDATE SET activo = true;

-- 2. PROGRAMAS PRESUPUESTARIOS
INSERT INTO programas (codigo, nombre, orden, activo) VALUES
    ('9001', 'Acciones Centrales', 1, true),
    ('9002', 'Asignaciones Presupuestarias que no Resultan en Productos', 2, true),
    ('0090', 'Logros de Aprendizaje de Estudiantes de la Educación Básica Regular', 3, true),
    ('0106', 'Inclusión de Niños, Niñas y Jóvenes con Discapacidad', 4, true)
ON CONFLICT (codigo) DO UPDATE SET nombre = EXCLUDED.nombre, activo = true;

-- 3. PARTIDAS PRESUPUESTARIAS
INSERT INTO partidas_presupuestarias (codigo, descripcion, activo) VALUES
    ('2.1.11.21', 'Asignación a Fondos de Asistencia y Estímulo (CAFAE)', true),
    ('2.1.11.12', 'Personal Administrativo Nombrado (Régimen 276)', true),
    ('2.1.11.13', 'Personal Administrativo Contratado', true)
ON CONFLICT (codigo) DO UPDATE SET descripcion = EXCLUDED.descripcion, activo = true;

-- 4. METAS PRESUPUESTALES
INSERT INTO metas (codigo, descripcion, activo) VALUES
    ('0001', 'Gestión Administrativa y Apoyo a la Sede Central', true),
    ('0011', 'Educación Inicial', true),
    ('0012', 'Educación Primaria', true),
    ('0014', 'Educación Secundaria', true),
    ('0030', 'Educación Básica Especial - Primaria', true),
    ('0042', 'Educación Técnico Productiva', true),
    ('0044', 'Educación Básica Alternativa - Avanzado', true)
ON CONFLICT (codigo) DO UPDATE SET descripcion = EXCLUDED.descripcion, activo = true;

-- 5. RELACIÓN NIVEL - METAS (Heredabilidad de meta para II.EE.)
INSERT INTO nivel_metas (nivel_id, meta_id, actualizado_en)
SELECT n.id, m.id, now()
FROM niveles n, metas m
WHERE (n.nombre = 'Inicial-Jardín' AND m.codigo = '0011')
   OR (n.nombre = 'Primaria' AND m.codigo = '0012')
   OR (n.nombre = 'Secundaria' AND m.codigo = '0014')
   OR (n.nombre = 'Básica Especial - Primaria' AND m.codigo = '0030')
   OR (n.nombre = 'Técnico Productiva' AND m.codigo = '0042')
   OR (n.nombre = 'Básica Alternativa - Avanzado' AND m.codigo = '0044')
ON CONFLICT (nivel_id) DO UPDATE SET meta_id = EXCLUDED.meta_id, actualizado_en = now();

-- 6. CATEGORÍAS REMUNERATIVAS
-- Grupo Auxiliar (AA a AF: S/ 1,350.00)
-- Grupo Técnico (TA a TF: S/ 1,370.00)
-- Grupo Funcionarios y Profesionales Sede (F2, PA, PE)
INSERT INTO categorias (codigo, descripcion, activo) VALUES
    ('AA', 'Auxiliar A (S/ 1,350.00)', true),
    ('AB', 'Auxiliar B (S/ 1,350.00)', true),
    ('AC', 'Auxiliar C (S/ 1,350.00)', true),
    ('AD', 'Auxiliar D (S/ 1,350.00)', true),
    ('AE', 'Auxiliar E (S/ 1,350.00)', true),
    ('AF', 'Auxiliar F (S/ 1,350.00)', true),
    ('TA', 'Técnico A (S/ 1,370.00)', true),
    ('TB', 'Técnico B (S/ 1,370.00)', true),
    ('TC', 'Técnico C (S/ 1,370.00)', true),
    ('TD', 'Técnico D (S/ 1,370.00)', true),
    ('TE', 'Técnico E (S/ 1,370.00)', true),
    ('TF', 'Técnico F (S/ 1,370.00)', true),
    ('F2', 'Funcionario 2 (S/ 2,400.00)', true),
    ('PA', 'Profesional A (S/ 1,850.00)', true),
    ('PE', 'Profesional E (S/ 1,650.00)', true)
ON CONFLICT (codigo) DO UPDATE SET descripcion = EXCLUDED.descripcion, activo = true;

-- 7. SITUACIONES LABORALES
INSERT INTO situaciones (nombre, activo) VALUES
    ('NOMBRADO', true),
    ('CONTRATADO', true)
ON CONFLICT (nombre) DO UPDATE SET activo = true;

-- 8. SUBTIPOS DE TRABAJADOR
INSERT INTO subtipos_trabajador (nombre, activo) VALUES
    ('ADMINISTRATIVO', true),
    ('DOCENTE', true),
    ('AUXILIAR', true)
ON CONFLICT (nombre) DO UPDATE SET activo = true;

-- 9. ÁREAS DE SEDE CENTRAL (Fusión limpia de duplicados y asignación oficial con tildes)
DO $$
DECLARE
    r RECORD;
    v_target_id BIGINT;
    v_dup_id BIGINT;
BEGIN
    FOR r IN SELECT * FROM (VALUES
        ('DIRECCIÓN', ARRAY['DIRECCION', 'DIRECCI%']),
        ('GESTIÓN PEDAGÓGICA', ARRAY['GESTION PEDAGOGICA', 'GESTI%PEDAG%']),
        ('GESTIÓN INSTITUCIONAL', ARRAY['GESTION INSTITUCIONAL', 'GESTI%INSTITUCIONAL%']),
        ('GESTIÓN ADMINISTRATIVA', ARRAY['GESTION ADMINISTRATIVA', 'GESTI%ADMINISTRATIVA%']),
        ('CONTROL INSTITUCIONAL', ARRAY['CONTROL INSTITUCIONAL', 'CONTROL%'])
    ) AS t(oficial, patrones)
    LOOP
        SELECT id INTO v_target_id FROM areas_sede WHERE nombre = r.oficial;
        IF v_target_id IS NULL THEN
            SELECT id INTO v_target_id FROM areas_sede 
            WHERE nombre LIKE ANY(r.patrones) ORDER BY id LIMIT 1;
            IF v_target_id IS NOT NULL THEN
                UPDATE areas_sede SET nombre = r.oficial WHERE id = v_target_id;
            ELSE
                INSERT INTO areas_sede (nombre, activo) VALUES (r.oficial, true) RETURNING id INTO v_target_id;
            END IF;
        END IF;

        FOR v_dup_id IN SELECT id FROM areas_sede WHERE id <> v_target_id AND nombre LIKE ANY(r.patrones)
        LOOP
            UPDATE trabajadores SET area_id = v_target_id WHERE area_id = v_dup_id;
            DELETE FROM areas_sede WHERE id = v_dup_id;
        END LOOP;
    END LOOP;
END $$;

INSERT INTO areas_sede (nombre, meta_id, activo)
SELECT a.nombre, m.id, true
FROM (VALUES
    ('DIRECCIÓN'),
    ('GESTIÓN PEDAGÓGICA'),
    ('GESTIÓN INSTITUCIONAL'),
    ('GESTIÓN ADMINISTRATIVA'),
    ('CONTROL INSTITUCIONAL')
) AS a(nombre)
LEFT JOIN metas m ON m.codigo = '0001'
ON CONFLICT (nombre) DO UPDATE SET meta_id = EXCLUDED.meta_id, activo = true;

-- 10. CARGOS
DO $$
DECLARE
    r RECORD;
    v_target_id BIGINT;
    v_dup_id BIGINT;
BEGIN
    FOR r IN SELECT * FROM (VALUES
        ('Técnico Administrativo', ARRAY['T%cnico Administrativo']),
        ('Técnico Administrativo I', ARRAY['T%cnico Administrativo I']),
        ('Técnico Administrativo II', ARRAY['T%cnico Administrativo II']),
        ('Técnico Administrativo - Escalafón', ARRAY['T%cnico Administrativo - Escalaf%'])
    ) AS t(oficial, patrones)
    LOOP
        SELECT id INTO v_target_id FROM cargos WHERE nombre = r.oficial;
        IF v_target_id IS NULL THEN
            SELECT id INTO v_target_id FROM cargos 
            WHERE nombre LIKE ANY(r.patrones) AND nombre NOT IN ('Técnico Administrativo I', 'Técnico Administrativo II', 'Técnico Administrativo - Escalafón')
            ORDER BY id LIMIT 1;
            IF v_target_id IS NOT NULL THEN
                UPDATE cargos SET nombre = r.oficial WHERE id = v_target_id;
            ELSE
                INSERT INTO cargos (nombre, activo) VALUES (r.oficial, true) RETURNING id INTO v_target_id;
            END IF;
        END IF;

        FOR v_dup_id IN SELECT id FROM cargos WHERE id <> v_target_id AND nombre LIKE ANY(r.patrones)
            AND (r.oficial <> 'Técnico Administrativo' OR nombre NOT IN ('Técnico Administrativo I', 'Técnico Administrativo II', 'Técnico Administrativo - Escalafón'))
        LOOP
            UPDATE trabajadores SET cargo_id = v_target_id WHERE cargo_id = v_dup_id;
            DELETE FROM cargos WHERE id = v_dup_id;
        END LOOP;
    END LOOP;
END $$;

INSERT INTO cargos (nombre, activo) VALUES
    -- Cargos de II.EE.
    ('Auxiliar de Biblioteca', true),
    ('Auxiliar de Laboratorio', true),
    ('Oficinista', true),
    ('Secretaria', true),
    ('Técnico Administrativo', true),
    ('Trabajador de Servicio', true),
    -- Cargos de Sede Central
    ('Técnico Administrativo I', true),
    ('Ingeniero I', true),
    ('ABOGADO I', true),
    ('Secretaria II', true),
    ('Secretaria I', true),
    ('Secretario I', true),
    ('Planificador I', true),
    ('Especialista en Racionalización', true),
    ('Director de Sistema Administrativo II Jefe de DGI', true),
    ('Especialista en Finanzas I', true),
    ('Director de Sistema Administrativo II Jefe de DGA', true),
    ('Tesorera I', true),
    ('Técnico Administrativo - Escalafón', true),
    ('Contador I', true),
    ('Trabajador de Servicio II', true),
    ('Operador PAD I', true),
    ('Especialista Administrativo - Abastecimiento', true),
    ('TRABAJADOR DE SERVICIO', true),
    ('Técnico Administrativo II', true),
    ('Especialista Administrativo - OPER', true),
    ('Director de Sistema Administrativo Jefe de OCI', true),
    ('Auditor I', true)
ON CONFLICT (nombre) DO UPDATE SET activo = true;

-- 11. INSTITUCIONES EDUCATIVAS DE CHEPÉN
INSERT INTO instituciones (codigo_modular, nombre, nivel_id, distrito, meta_id, activo)
SELECT ie.codigo_modular, ie.nombre, n.id, ie.distrito, m.id, true
FROM (VALUES
    ('0341257', 'I.E.I. N° 161 Rayitos de Sol', 'Inicial-Jardín', 'Chepén', '0011'),
    ('0341588', 'I.E. N° 81014 San Pedro', 'Primaria', 'Chepén', '0012'),
    ('0341620', 'I.E. Santa Inés', 'Secundaria', 'Chepén', '0014'),
    ('0341893', 'I.E. César Abraham Vallejo Mendoza', 'Secundaria', 'Chepén', '0014'),
    ('0342115', 'I.E. N° 80388 Alfredo Tello Salavarría', 'Primaria', 'Pacanga', '0012'),
    ('0524181', 'CEBE Chepén', 'Básica Especial - Primaria', 'Chepén', '0030'),
    ('0689452', 'CETPRO Chepén', 'Técnico Productiva', 'Chepén', '0042'),
    ('0741289', 'CEBA San Pedro', 'Básica Alternativa - Avanzado', 'Chepén', '0044')
) AS ie(codigo_modular, nombre, nivel_nombre, distrito, meta_codigo)
JOIN niveles n ON n.nombre = ie.nivel_nombre
LEFT JOIN metas m ON m.codigo = ie.meta_codigo
ON CONFLICT (codigo_modular) DO UPDATE SET 
    nombre = EXCLUDED.nombre, 
    nivel_id = EXCLUDED.nivel_id, 
    distrito = EXCLUDED.distrito, 
    meta_id = EXCLUDED.meta_id, 
    activo = true;

-- 12. FIRMAS AUTORIZADAS
UPDATE firmas SET nombre_completo = 'Mg. Ángel Rodolfo Mendoza Flores', cargo = 'Director del Programa Sectorial III - UGEL Chepén', activo = true WHERE cargo LIKE '%Director%';
UPDATE firmas SET nombre_completo = 'Lic. Carlos Alberto Díaz Paredes', cargo = 'Jefe del Área de Gestión Institucional', activo = true WHERE cargo LIKE '%Institucional%';
UPDATE firmas SET nombre_completo = 'CPC. Walter David Sánchez Vásquez', cargo = 'Jefe del Área de Gestión Administrativa', activo = true WHERE cargo LIKE '%Administrativa%';
UPDATE firmas SET nombre_completo = 'Econ. María Elena Torres Ruiz', cargo = 'Especialista en Finanzas y Tesorería', activo = true WHERE cargo LIKE '%Finanzas%';

INSERT INTO firmas (nombre_completo, cargo, activo)
SELECT f.nombre_completo, f.cargo, true
FROM (VALUES
    ('Mg. Ángel Rodolfo Mendoza Flores', 'Director del Programa Sectorial III - UGEL Chepén'),
    ('Lic. Carlos Alberto Díaz Paredes', 'Jefe del Área de Gestión Institucional'),
    ('CPC. Walter David Sánchez Vásquez', 'Jefe del Área de Gestión Administrativa'),
    ('Econ. María Elena Torres Ruiz', 'Especialista en Finanzas y Tesorería')
) AS f(nombre_completo, cargo)
WHERE NOT EXISTS (SELECT 1 FROM firmas WHERE cargo = f.cargo);

-- 13. TRABAJADORES DE SEDE (24 Puestos basados en la imagen oficial)
INSERT INTO trabajadores (
    dni, apellidos, nombres, tipo, area_id, cargo_id, categoria_id, situacion_id, subtipo_id,
    ley, jornada_laboral, cuenta_multired, importe, activo, tipo_pago
)
SELECT
    t.dni, t.apellidos, t.nombres, 'SEDE', a.id, c.id, cat.id, s.id, sub.id,
    '276', '40', t.cuenta, t.importe, true, 'CUENTA'
FROM (VALUES
    -- DIRECCIÓN
    ('40123401', 'ALVITEZ QUIROZ', 'SEGUNDO RAMIRO', 'DIRECCIÓN', 'Técnico Administrativo I', 'TE', 'NOMBRADO', 1370.00, '04231100201'),
    ('41234502', 'BARRUETO CORREA', 'CARLOS ALBERTO', 'DIRECCIÓN', 'Ingeniero I', 'PE', 'NOMBRADO', 1650.00, '04231100202'),
    ('42345603', 'CASTILLO MONCADA', 'MARIA ISABEL', 'DIRECCIÓN', 'ABOGADO I', 'PE', 'NOMBRADO', 1650.00, '04231100203'),
    ('43456704', 'CHAVEZ SANCHEZ', 'ROSA ELVIRA', 'DIRECCIÓN', 'Secretaria II', 'TE', 'NOMBRADO', 1370.00, '04231100204'),
    -- GESTIÓN PEDAGÓGICA
    ('44567805', 'DÍAZ LINGÁN', 'CARMEN ROSA', 'GESTIÓN PEDAGÓGICA', 'Secretaria I', 'TA', 'NOMBRADO', 1370.00, '04231100205'),
    ('45678906', 'ESPINOZA PAREDES', 'MANUEL ENRIQUE', 'GESTIÓN PEDAGÓGICA', 'Planificador I', 'PE', 'NOMBRADO', 1650.00, '04231100206'),
    -- GESTIÓN INSTITUCIONAL
    ('46789007', 'FLORES QUISPE', 'CESAR AUGUSTO', 'GESTIÓN INSTITUCIONAL', 'Especialista en Racionalización', 'PA', 'NOMBRADO', 1850.00, '04231100207'),
    ('47890108', 'GARCÍA ZAVALETA', 'JORGE LUIS', 'GESTIÓN INSTITUCIONAL', 'Director de Sistema Administrativo II Jefe de DGI', 'F2', 'NOMBRADO', 2400.00, '04231100208'),
    ('48901209', 'HERRERA MENDOZA', 'ANA MARIA', 'GESTIÓN INSTITUCIONAL', 'Especialista en Finanzas I', 'PE', 'NOMBRADO', 1650.00, '04231100209'),
    ('49012310', 'IPANAQUE CUSTODIO', 'PEDRO PABLO', 'GESTIÓN INSTITUCIONAL', 'Secretario I', 'TA', 'NOMBRADO', 1370.00, '04231100210'),
    -- GESTIÓN ADMINISTRATIVA
    ('50123411', 'JAÚREGUI ROJAS', 'FERNANDO JAVIER', 'GESTIÓN ADMINISTRATIVA', 'Director de Sistema Administrativo II Jefe de DGA', 'F2', 'NOMBRADO', 2400.00, '04231100211'),
    ('51234512', 'LÓPEZ BUSTAMANTE', 'GLORIA TERESA', 'GESTIÓN ADMINISTRATIVA', 'Tesorera I', 'PA', 'NOMBRADO', 1850.00, '04231100212'),
    ('52345613', 'MALCA VIGO', 'VICTOR RAUL', 'GESTIÓN ADMINISTRATIVA', 'Técnico Administrativo - Escalafón', 'TA', 'NOMBRADO', 1370.00, '04231100213'),
    ('53456714', 'NUÑEZ ALVARADO', 'GUILLERMO ALFREDO', 'GESTIÓN ADMINISTRATIVA', 'Contador I', 'PE', 'NOMBRADO', 1650.00, '04231100214'),
    ('54567815', 'OLIVARES BAZAN', 'PATRICIA ELIZABETH', 'GESTIÓN ADMINISTRATIVA', 'Secretaria I', 'TE', 'NOMBRADO', 1370.00, '04231100215'),
    ('55678916', 'PÉREZ CABANILLAS', 'JUAN CARLOS', 'GESTIÓN ADMINISTRATIVA', 'Trabajador de Servicio II', 'AE', 'NOMBRADO', 1350.00, '04231100216'),
    ('56789017', 'QUISPE TANTALEAN', 'ROBERTO CARLOS', 'GESTIÓN ADMINISTRATIVA', 'Operador PAD I', 'TE', 'CONTRATADO', 1370.00, '04231100217'),
    ('57890118', 'RODRÍGUEZ MURIEL', 'LUIS ALBERTO', 'GESTIÓN ADMINISTRATIVA', 'Especialista Administrativo - Abastecimiento', 'PA', 'NOMBRADO', 1850.00, '04231100218'),
    ('58901219', 'SALAZAR GUEVARA', 'JOSE SANTOS', 'GESTIÓN ADMINISTRATIVA', 'TRABAJADOR DE SERVICIO', 'AE', 'NOMBRADO', 1350.00, '04231100219'),
    ('59012320', 'TORRES HUAMAN', 'DANIEL RICARDO', 'GESTIÓN ADMINISTRATIVA', 'Técnico Administrativo II', 'TE', 'NOMBRADO', 1370.00, '04231100220'),
    ('60123421', 'UBILLÚS VÁSQUEZ', 'HECTOR DAVID', 'GESTIÓN ADMINISTRATIVA', 'Especialista Administrativo - OPER', 'TE', 'NOMBRADO', 1370.00, '04231100221'),
    -- CONTROL INSTITUCIONAL
    ('61234522', 'VALDIVIA CHUNGA', 'OSCAR EDUARDO', 'CONTROL INSTITUCIONAL', 'Director de Sistema Administrativo Jefe de OCI', 'F2', 'NOMBRADO', 2400.00, '04231100222'),
    ('62345623', 'YPARRAGUIRRE SILVA', 'MONICA BEATRIZ', 'CONTROL INSTITUCIONAL', 'Secretaria I', 'TA', 'NOMBRADO', 1370.00, '04231100223'),
    ('63456724', 'ZAMORA CORONADO', 'FELIX ALONSO', 'CONTROL INSTITUCIONAL', 'Auditor I', 'PE', 'NOMBRADO', 1650.00, '04231100224')
) AS t(dni, apellidos, nombres, area_nombre, cargo_nombre, cat_codigo, situacion_nombre, importe, cuenta)
JOIN areas_sede a ON a.nombre = t.area_nombre
JOIN cargos c ON c.nombre = t.cargo_nombre
JOIN categorias cat ON cat.codigo = t.cat_codigo
JOIN situaciones s ON s.nombre = t.situacion_nombre
JOIN subtipos_trabajador sub ON sub.nombre = 'ADMINISTRATIVO'
ON CONFLICT (dni) DO UPDATE SET
    apellidos = EXCLUDED.apellidos,
    nombres = EXCLUDED.nombres,
    area_id = EXCLUDED.area_id,
    cargo_id = EXCLUDED.cargo_id,
    categoria_id = EXCLUDED.categoria_id,
    situacion_id = EXCLUDED.situacion_id,
    importe = EXCLUDED.importe,
    cuenta_multired = EXCLUDED.cuenta_multired,
    activo = true;

-- 14. TRABAJADORES DE II.EE. (Personal administrativo de II.EE.)
INSERT INTO trabajadores (
    dni, apellidos, nombres, tipo, institucion_id, nivel_id, cargo_id, categoria_id, situacion_id, subtipo_id,
    ley, jornada_laboral, cuenta_multired, importe, activo, tipo_pago
)
SELECT
    t.dni, t.apellidos, t.nombres, 'IIEE', i.id, i.nivel_id, c.id, cat.id, s.id, sub.id,
    '276', '40', t.cuenta, t.importe, true, 'CUENTA'
FROM (VALUES
    -- I.E.I. 161 (Inicial)
    ('70112201', 'ARAUJO RIOS', 'MIRTHA MARLENE', '0341257', 'Auxiliar de Biblioteca', 'AA', 'NOMBRADO', 1350.00, '04231200101'),
    ('70112202', 'BAZÁN CHAVESTA', 'ELIZABETH LUZ', '0341257', 'Trabajador de Servicio', 'AE', 'NOMBRADO', 1350.00, '04231200102'),
    -- I.E. 81014 San Pedro (Primaria)
    ('70112203', 'CABRERA VALENCIA', 'SEGUNDO TEOFILO', '0341588', 'Técnico Administrativo', 'TA', 'NOMBRADO', 1370.00, '04231200103'),
    ('70112204', 'DÁVILA QUIROZ', 'MARIA ROSARIO', '0341588', 'Oficinista', 'AB', 'NOMBRADO', 1350.00, '04231200104'),
    ('70112205', 'ESTRADA MENDOZA', 'JUAN BAUTISTA', '0341588', 'Trabajador de Servicio', 'AF', 'CONTRATADO', 1350.00, '04231200105'),
    -- I.E. Santa Inés (Secundaria)
    ('70112206', 'FIGUEROA SANCHEZ', 'OLGA LIDIA', '0341620', 'Secretaria', 'TC', 'NOMBRADO', 1370.00, '04231200106'),
    ('70112207', 'GUTIERREZ ZAPATA', 'CARLOS ENRIQUE', '0341620', 'Auxiliar de Laboratorio', 'TB', 'NOMBRADO', 1370.00, '04231200107'),
    ('70112208', 'HERNÁNDEZ CORREA', 'MARTHA ELENA', '0341620', 'Auxiliar de Biblioteca', 'AD', 'NOMBRADO', 1350.00, '04231200108'),
    ('70112209', 'INFANTE ALVA', 'LUCAS GONZALO', '0341620', 'Trabajador de Servicio', 'AE', 'CONTRATADO', 1350.00, '04231200109'),
    -- I.E. César Vallejo (Secundaria)
    ('70112210', 'JIMENEZ PASTOR', 'VICTOR MANUEL', '0341893', 'Técnico Administrativo', 'TD', 'NOMBRADO', 1370.00, '04231200110'),
    ('70112211', 'LOZANO BECERRA', 'DORA ALICIA', '0341893', 'Secretaria', 'TE', 'NOMBRADO', 1370.00, '04231200111'),
    ('70112212', 'MONTALVO CUEVA', 'PEDRO WILFREDO', '0341893', 'Trabajador de Servicio', 'AA', 'NOMBRADO', 1350.00, '04231200112'),
    -- CEBE Chepén (Especial)
    ('70112213', 'NUÑEZ PALACIOS', 'SONIA MARIBEL', '0524181', 'Oficinista', 'AC', 'NOMBRADO', 1350.00, '04231200113'),
    ('70112214', 'ORTEGA MORI', 'RAUL EDGARDO', '0524181', 'Trabajador de Servicio', 'AE', 'CONTRATADO', 1350.00, '04231200114'),
    -- CETPRO Chepén (Técnico)
    ('70112215', 'PAREDES SALDAÑA', 'JOSE LUIS', '0689452', 'Auxiliar de Laboratorio', 'TF', 'NOMBRADO', 1370.00, '04231200115'),
    -- CEBA San Pedro (Alternativa)
    ('70112216', 'QUISPE VILCA', 'CARMEN BEATRIZ', '0741289', 'Secretaria', 'TA', 'NOMBRADO', 1370.00, '04231200116')
) AS t(dni, apellidos, nombres, cod_mod, cargo_nombre, cat_codigo, situacion_nombre, importe, cuenta)
JOIN instituciones i ON i.codigo_modular = t.cod_mod
JOIN cargos c ON c.nombre = t.cargo_nombre
JOIN categorias cat ON cat.codigo = t.cat_codigo
JOIN situaciones s ON s.nombre = t.situacion_nombre
JOIN subtipos_trabajador sub ON sub.nombre = 'ADMINISTRATIVO'
ON CONFLICT (dni) DO UPDATE SET
    apellidos = EXCLUDED.apellidos,
    nombres = EXCLUDED.nombres,
    institucion_id = EXCLUDED.institucion_id,
    nivel_id = EXCLUDED.nivel_id,
    cargo_id = EXCLUDED.cargo_id,
    categoria_id = EXCLUDED.categoria_id,
    situacion_id = EXCLUDED.situacion_id,
    importe = EXCLUDED.importe,
    cuenta_multired = EXCLUDED.cuenta_multired,
    activo = true;

COMMIT;
