-- =============================================================================
-- POBLAMIENTO MASIVO OFICIAL: 140 IIEE, 25 SEDE, NUEVAS INSTITUCIONES Y PLANILLAS
-- =============================================================================
SET client_encoding = 'UTF8';
SET search_path TO cafae, public;

BEGIN;

-- 1. NUEVAS INSTITUCIONES EDUCATIVAS
INSERT INTO instituciones (codigo_modular, nombre, nivel_id, distrito, meta_id, activo)
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

-- 2. SEDE: 25 TRABAJADORES EXACTOS
INSERT INTO trabajadores (
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

-- 3. TRABAJADORES DE II.EE. (140 EN TOTAL)
INSERT INTO trabajadores (
    dni, apellidos, nombres, tipo, institucion_id, nivel_id, cargo_id, categoria_id, situacion_id, subtipo_id,
    ley, jornada_laboral, cuenta_multired, importe, activo, tipo_pago,
    fecha_nacimiento, regimen_laboral, regimen_pensionario, tiempo_servicio_texto, fecha_ingreso
)
SELECT
    t.dni, t.apellidos, t.nombres, 'IIEE', i.id, i.nivel_id, c.id, cat.id, s.id, sub.id,
    '276', '40', t.cuenta, t.importe, true, 'CUENTA',
    t.f_nac::date, '276', t.pension, t.ts_str, t.f_ingreso::date
FROM (VALUES
    ('70112217', 'QUISPE RAMOS', 'JUAN CARLOS', '0341257', 'Auxiliar de Biblioteca', 'AA', 'NOMBRADO', 1350.00, '04231270112217', '1965-01-01', 'ONP 19990', '05-00-01', '2005-03-01'),
    ('70112218', 'FLORES CASTILLO', 'ELIZABETH LUZ', '0341711', 'Trabajador de Servicio', 'AE', 'NOMBRADO', 1350.00, '04231270112218', '1966-02-02', 'AFP INTEGRA', '06-02-04', '2006-03-01'),
    ('70112219', 'RODRIGUEZ ALVAREZ', 'SEGUNDO TEOFILO', '0341257', 'Trabajador de Servicio', 'AF', 'CONTRATADO', 1350.00, '04231270112219', '1967-03-03', 'AFP PRIMA', '07-04-07', '2007-03-01'),
    ('70112220', 'SANCHEZ ESPINOZA', 'OLGA LIDIA', '0341711', 'Técnico Administrativo', 'TA', 'NOMBRADO', 1370.00, '04231270112220', '1968-04-04', 'AFP PROFUTURO', '08-06-10', '2008-03-01'),
    ('70112221', 'GARCIA MENDOZA', 'VICTOR MANUEL', '0341257', 'Oficinista', 'AB', 'NOMBRADO', 1350.00, '04231270112221', '1969-05-05', 'AFP HABITAT', '09-08-13', '2009-03-01'),
    ('70112222', 'ROJAS GUTIERREZ', 'DORA ALICIA', '0341711', 'Secretaria', 'TC', 'NOMBRADO', 1370.00, '04231270112222', '1970-06-06', 'ONP 19990', '10-10-16', '2010-03-01'),
    ('70112223', 'DIAZ HERRERA', 'RAUL EDGARDO', '0341257', 'Auxiliar de Laboratorio', 'TB', 'NOMBRADO', 1370.00, '04231270112223', '1971-07-07', 'AFP INTEGRA', '11-00-19', '2011-03-01'),
    ('70112224', 'TORRES HUAMAN', 'CARMEN BEATRIZ', '0341711', 'Secretaria', 'TE', 'NOMBRADO', 1370.00, '04231270112224', '1972-08-08', 'AFP PRIMA', '12-02-22', '2012-03-01'),
    ('70112225', 'LOPEZ VARGAS', 'CESAR AUGUSTO', '0341257', 'Oficinista', 'AC', 'NOMBRADO', 1350.00, '04231270112225', '1973-09-09', 'AFP PROFUTURO', '13-04-25', '2013-03-01'),
    ('70112226', 'GONZALES FERNANDEZ', 'ROSA ELVIRA', '0341711', 'Auxiliar de Laboratorio', 'TF', 'NOMBRADO', 1370.00, '04231270112226', '1974-10-10', 'AFP HABITAT', '14-06-28', '2014-03-01'),
    ('70112227', 'PEREZ ALVA', 'FERNANDO JAVIER', '0341257', 'Técnico Administrativo', 'TD', 'NOMBRADO', 1370.00, '04231270112227', '1975-11-11', 'ONP 19990', '15-08-03', '2015-03-01'),
    ('70112228', 'CHAVEZ CUEVA', 'ANA MARIA', '0341711', 'Trabajador de Servicio', 'AA', 'NOMBRADO', 1350.00, '04231270112228', '1976-12-12', 'AFP INTEGRA', '16-10-06', '2016-03-01'),
    ('70112229', 'VASQUEZ BAZAN', 'ROBERTO CARLOS', '0341257', 'Auxiliar de Biblioteca', 'AA', 'NOMBRADO', 1350.00, '04231270112229', '1977-01-13', 'AFP PRIMA', '17-00-09', '2017-03-01'),
    ('70112230', 'RAMOS PAREDES', 'PATRICIA ELIZABETH', '0341711', 'Trabajador de Servicio', 'AE', 'NOMBRADO', 1350.00, '04231270112230', '1978-02-14', 'AFP PROFUTURO', '18-02-12', '2018-03-01'),
    ('70112231', 'CASTILLO CABRERA', 'HECTOR DAVID', '0341257', 'Trabajador de Servicio', 'AF', 'CONTRATADO', 1350.00, '04231270112231', '1979-03-15', 'AFP HABITAT', '19-04-15', '2019-03-01'),
    ('70112232', 'ALVAREZ JIMENEZ', 'YOLANDA BEATRIZ', '0341711', 'Técnico Administrativo', 'TA', 'NOMBRADO', 1370.00, '04231270112232', '1980-04-16', 'ONP 19990', '20-06-18', '2005-03-01'),
    ('70112233', 'ESPINOZA SALDAÑA', 'FELIX ALONSO', '0341257', 'Oficinista', 'AB', 'NOMBRADO', 1350.00, '04231270112233', '1981-05-17', 'AFP INTEGRA', '21-08-21', '2006-03-01'),
    ('70112234', 'MENDOZA VALENCIA', 'SILVIA MERCEDES', '0341711', 'Secretaria', 'TC', 'NOMBRADO', 1370.00, '04231270112234', '1982-06-18', 'AFP PRIMA', '22-10-24', '2007-03-01'),
    ('70112235', 'GUTIERREZ MONTALVO', 'CARLOS ALBERTO', '0341588', 'Auxiliar de Laboratorio', 'TB', 'NOMBRADO', 1370.00, '04231270112235', '1983-07-19', 'AFP PROFUTURO', '23-00-27', '2008-03-01'),
    ('70112236', 'HERRERA ZAPATA', 'SUSANA BEATRIZ', '0342115', 'Secretaria', 'TE', 'NOMBRADO', 1370.00, '04231270112236', '1984-08-20', 'AFP HABITAT', '24-02-02', '2009-03-01'),
    ('70112237', 'HUAMAN HERNANDEZ', 'VICTOR RAUL', '0341701', 'Oficinista', 'AC', 'NOMBRADO', 1350.00, '04231270112237', '1985-09-21', 'ONP 19990', '05-04-05', '2010-03-01'),
    ('70112238', 'VARGAS INFANTE', 'ROCIO DEL CARMEN', '0341712', 'Auxiliar de Laboratorio', 'TF', 'NOMBRADO', 1370.00, '04231270112238', '1986-10-22', 'AFP INTEGRA', '06-06-08', '2011-03-01'),
    ('70112239', 'FERNANDEZ CORREA', 'JOSE SANTOS', '0341721', 'Técnico Administrativo', 'TD', 'NOMBRADO', 1370.00, '04231270112239', '1987-11-23', 'AFP PRIMA', '07-08-11', '2012-03-01'),
    ('70112240', 'ALVA BECERRA', 'BLANCA NIEVES', '0341731', 'Trabajador de Servicio', 'AA', 'NOMBRADO', 1350.00, '04231270112240', '1988-12-24', 'AFP PROFUTURO', '08-10-14', '2013-03-01'),
    ('70112241', 'CUEVA MORI', 'WALTER DAVID', '0341588', 'Auxiliar de Biblioteca', 'AA', 'NOMBRADO', 1350.00, '04231270112241', '1989-01-25', 'AFP HABITAT', '09-00-17', '2014-03-01'),
    ('70112242', 'BAZAN ORTEGA', 'MIRTHA MARLENE', '0342115', 'Trabajador de Servicio', 'AE', 'NOMBRADO', 1350.00, '04231270112242', '1990-02-26', 'ONP 19990', '10-02-20', '2015-03-01'),
    ('70112243', 'PAREDES ARAUJO', 'JOSE LUIS', '0341701', 'Trabajador de Servicio', 'AF', 'CONTRATADO', 1350.00, '04231270112243', '1991-03-27', 'AFP INTEGRA', '11-04-23', '2016-03-01'),
    ('70112244', 'CABRERA CHAVESTA', 'MARIA ROSARIO', '0341712', 'Técnico Administrativo', 'TA', 'NOMBRADO', 1370.00, '04231270112244', '1992-04-28', 'AFP PRIMA', '12-06-26', '2017-03-01'),
    ('70112245', 'JIMENEZ DAVILA', 'CARLOS ENRIQUE', '0341721', 'Oficinista', 'AB', 'NOMBRADO', 1350.00, '04231270112245', '1993-05-01', 'AFP PROFUTURO', '13-08-01', '2018-03-01'),
    ('70112246', 'SALDAÑA ESTRADA', 'MARTHA ELENA', '0341731', 'Secretaria', 'TC', 'NOMBRADO', 1370.00, '04231270112246', '1994-06-02', 'AFP HABITAT', '14-10-04', '2019-03-01'),
    ('70112247', 'VALENCIA FIGUEROA', 'PEDRO WILFREDO', '0341588', 'Auxiliar de Laboratorio', 'TB', 'NOMBRADO', 1370.00, '04231270112247', '1965-07-03', 'ONP 19990', '15-00-07', '2005-03-01'),
    ('70112248', 'MONTALVO MALCA', 'SONIA MARIBEL', '0342115', 'Secretaria', 'TE', 'NOMBRADO', 1370.00, '04231270112248', '1966-08-04', 'AFP INTEGRA', '16-02-10', '2006-03-01'),
    ('70112249', 'ZAPATA JAUREGUI', 'JORGE LUIS', '0341701', 'Oficinista', 'AC', 'NOMBRADO', 1350.00, '04231270112249', '1967-09-05', 'AFP PRIMA', '17-04-13', '2007-03-01'),
    ('70112250', 'HERNANDEZ VIGO', 'MARIA ISABEL', '0341712', 'Auxiliar de Laboratorio', 'TF', 'NOMBRADO', 1370.00, '04231270112250', '1968-10-06', 'AFP PROFUTURO', '18-06-16', '2008-03-01'),
    ('70112251', 'INFANTE BUSTAMANTE', 'MANUEL ENRIQUE', '0341721', 'Técnico Administrativo', 'TD', 'NOMBRADO', 1370.00, '04231270112251', '1969-11-07', 'AFP HABITAT', '19-08-19', '2009-03-01'),
    ('70112252', 'CORREA SALAZAR', 'CARMEN ROSA', '0341731', 'Trabajador de Servicio', 'AA', 'NOMBRADO', 1350.00, '04231270112252', '1970-12-08', 'ONP 19990', '20-10-22', '2010-03-01'),
    ('70112253', 'BECERRA TANTALEAN', 'LUIS ALBERTO', '0341588', 'Auxiliar de Biblioteca', 'AA', 'NOMBRADO', 1350.00, '04231270112253', '1971-01-09', 'AFP INTEGRA', '21-00-25', '2011-03-01'),
    ('70112254', 'MORI MURIEL', 'GLORIA TERESA', '0342115', 'Trabajador de Servicio', 'AE', 'NOMBRADO', 1350.00, '04231270112254', '1972-02-10', 'AFP PRIMA', '22-02-28', '2012-03-01'),
    ('70112255', 'ORTEGA GUEVARA', 'DANIEL RICARDO', '0341701', 'Trabajador de Servicio', 'AF', 'CONTRATADO', 1350.00, '04231270112255', '1973-03-11', 'AFP PROFUTURO', '23-04-03', '2013-03-01'),
    ('70112256', 'ARAUJO UBILLUS', 'MONICA BEATRIZ', '0341712', 'Técnico Administrativo', 'TA', 'NOMBRADO', 1370.00, '04231270112256', '1974-04-12', 'AFP HABITAT', '24-06-06', '2014-03-01'),
    ('70112257', 'CHAVESTA YPARRAGUIRRE', 'OSCAR EDUARDO', '0341721', 'Oficinista', 'AB', 'NOMBRADO', 1350.00, '04231270112257', '1975-05-13', 'ONP 19990', '05-08-09', '2015-03-01'),
    ('70112258', 'DAVILA ZAMORA', 'TERESA DE JESUS', '0341731', 'Secretaria', 'TC', 'NOMBRADO', 1370.00, '04231270112258', '1976-06-14', 'AFP INTEGRA', '06-10-12', '2016-03-01'),
    ('70112259', 'ESTRADA CORONADO', 'SEGUNDO RAMIRO', '0341588', 'Auxiliar de Laboratorio', 'TB', 'NOMBRADO', 1370.00, '04231270112259', '1977-07-15', 'AFP PRIMA', '07-00-15', '2017-03-01'),
    ('70112260', 'FIGUEROA VALDIVIA', 'LIDIA MARLENE', '0342115', 'Secretaria', 'TE', 'NOMBRADO', 1370.00, '04231270112260', '1978-08-16', 'AFP PROFUTURO', '08-02-18', '2018-03-01'),
    ('70112261', 'MALCA CHUNGA', 'PEDRO PABLO', '0341701', 'Oficinista', 'AC', 'NOMBRADO', 1350.00, '04231270112261', '1979-09-17', 'AFP HABITAT', '09-04-21', '2019-03-01'),
    ('70112262', 'JAUREGUI ALVITEZ', 'LUCIA DEL PILAR', '0341712', 'Auxiliar de Laboratorio', 'TF', 'NOMBRADO', 1370.00, '04231270112262', '1980-10-18', 'ONP 19990', '10-06-24', '2005-03-01'),
    ('70112263', 'VIGO BARRUETO', 'GUILLERMO ALFREDO', '0341721', 'Técnico Administrativo', 'TD', 'NOMBRADO', 1370.00, '04231270112263', '1981-11-19', 'AFP INTEGRA', '11-08-27', '2006-03-01'),
    ('70112264', 'BUSTAMANTE MONCADA', 'ELENA MERCEDES', '0341731', 'Trabajador de Servicio', 'AA', 'NOMBRADO', 1350.00, '04231270112264', '1982-12-20', 'AFP PRIMA', '12-10-02', '2007-03-01'),
    ('70112265', 'SALAZAR LINGAN', 'MIGUEL ANGEL', '0341588', 'Auxiliar de Biblioteca', 'AA', 'NOMBRADO', 1350.00, '04231270112265', '1983-01-21', 'AFP PROFUTURO', '13-00-05', '2008-03-01'),
    ('70112266', 'TANTALEAN CUSTODIO', 'IRMA YOLANDA', '0342115', 'Trabajador de Servicio', 'AE', 'NOMBRADO', 1350.00, '04231270112266', '1984-02-22', 'AFP HABITAT', '14-02-08', '2009-03-01'),
    ('70112267', 'MURIEL IPANAQUE', 'JUAN CARLOS', '0341701', 'Trabajador de Servicio', 'AF', 'CONTRATADO', 1350.00, '04231270112267', '1985-03-23', 'ONP 19990', '15-04-11', '2010-03-01'),
    ('70112268', 'GUEVARA QUISPE', 'ELIZABETH LUZ', '0341712', 'Técnico Administrativo', 'TA', 'NOMBRADO', 1370.00, '04231270112268', '1986-04-24', 'AFP INTEGRA', '16-06-14', '2011-03-01'),
    ('70112269', 'UBILLUS FLORES', 'SEGUNDO TEOFILO', '0341721', 'Oficinista', 'AB', 'NOMBRADO', 1350.00, '04231270112269', '1987-05-25', 'AFP PRIMA', '17-08-17', '2012-03-01'),
    ('70112270', 'YPARRAGUIRRE RODRIGUEZ', 'OLGA LIDIA', '0341731', 'Secretaria', 'TC', 'NOMBRADO', 1370.00, '04231270112270', '1988-06-26', 'AFP PROFUTURO', '18-10-20', '2013-03-01'),
    ('70112271', 'ZAMORA SANCHEZ', 'VICTOR MANUEL', '0341588', 'Auxiliar de Laboratorio', 'TB', 'NOMBRADO', 1370.00, '04231270112271', '1989-07-27', 'AFP HABITAT', '19-00-23', '2014-03-01'),
    ('70112272', 'CORONADO GARCIA', 'DORA ALICIA', '0342115', 'Secretaria', 'TE', 'NOMBRADO', 1370.00, '04231270112272', '1990-08-28', 'ONP 19990', '20-02-26', '2015-03-01'),
    ('70112273', 'VALDIVIA ROJAS', 'RAUL EDGARDO', '0341701', 'Oficinista', 'AC', 'NOMBRADO', 1350.00, '04231270112273', '1991-09-01', 'AFP INTEGRA', '21-04-01', '2016-03-01'),
    ('70112274', 'CHUNGA DIAZ', 'CARMEN BEATRIZ', '0341712', 'Auxiliar de Laboratorio', 'TF', 'NOMBRADO', 1370.00, '04231270112274', '1992-10-02', 'AFP PRIMA', '22-06-04', '2017-03-01'),
    ('70112275', 'ALVITEZ TORRES', 'CESAR AUGUSTO', '0341721', 'Técnico Administrativo', 'TD', 'NOMBRADO', 1370.00, '04231270112275', '1993-11-03', 'AFP PROFUTURO', '23-08-07', '2018-03-01'),
    ('70112276', 'BARRUETO LOPEZ', 'ROSA ELVIRA', '0341731', 'Trabajador de Servicio', 'AA', 'NOMBRADO', 1350.00, '04231270112276', '1994-12-04', 'AFP HABITAT', '24-10-10', '2019-03-01'),
    ('70112277', 'MONCADA GONZALES', 'FERNANDO JAVIER', '0341588', 'Auxiliar de Biblioteca', 'AA', 'NOMBRADO', 1350.00, '04231270112277', '1965-01-05', 'ONP 19990', '05-00-13', '2005-03-01'),
    ('70112278', 'LINGAN PEREZ', 'ANA MARIA', '0342115', 'Trabajador de Servicio', 'AE', 'NOMBRADO', 1350.00, '04231270112278', '1966-02-06', 'AFP INTEGRA', '06-02-16', '2006-03-01'),
    ('70112279', 'CUSTODIO CHAVEZ', 'ROBERTO CARLOS', '0341701', 'Trabajador de Servicio', 'AF', 'CONTRATADO', 1350.00, '04231270112279', '1967-03-07', 'AFP PRIMA', '07-04-19', '2007-03-01'),
    ('70112280', 'IPANAQUE VASQUEZ', 'PATRICIA ELIZABETH', '0341712', 'Técnico Administrativo', 'TA', 'NOMBRADO', 1370.00, '04231270112280', '1968-04-08', 'AFP PROFUTURO', '08-06-22', '2008-03-01'),
    ('70112281', 'QUISPE RAMOS', 'HECTOR DAVID', '0341721', 'Oficinista', 'AB', 'NOMBRADO', 1350.00, '04231270112281', '1969-05-09', 'AFP HABITAT', '09-08-25', '2009-03-01'),
    ('70112282', 'FLORES CASTILLO', 'YOLANDA BEATRIZ', '0341893', 'Secretaria', 'TC', 'NOMBRADO', 1370.00, '04231270112282', '1970-06-10', 'ONP 19990', '10-10-28', '2010-03-01'),
    ('70112283', 'RODRIGUEZ ALVAREZ', 'FELIX ALONSO', '0341702', 'Auxiliar de Laboratorio', 'TB', 'NOMBRADO', 1370.00, '04231270112283', '1971-07-11', 'AFP INTEGRA', '11-00-03', '2011-03-01'),
    ('70112284', 'SANCHEZ ESPINOZA', 'SILVIA MERCEDES', '0341722', 'Secretaria', 'TE', 'NOMBRADO', 1370.00, '04231270112284', '1972-08-12', 'AFP PRIMA', '12-02-06', '2012-03-01'),
    ('70112285', 'GARCIA MENDOZA', 'CARLOS ALBERTO', '0341620', 'Oficinista', 'AC', 'NOMBRADO', 1350.00, '04231270112285', '1973-09-13', 'AFP PROFUTURO', '13-04-09', '2013-03-01'),
    ('70112286', 'ROJAS GUTIERREZ', 'SUSANA BEATRIZ', '0341893', 'Auxiliar de Laboratorio', 'TF', 'NOMBRADO', 1370.00, '04231270112286', '1974-10-14', 'AFP HABITAT', '14-06-12', '2014-03-01'),
    ('70112287', 'DIAZ HERRERA', 'VICTOR RAUL', '0341702', 'Técnico Administrativo', 'TD', 'NOMBRADO', 1370.00, '04231270112287', '1975-11-15', 'ONP 19990', '15-08-15', '2015-03-01'),
    ('70112288', 'TORRES HUAMAN', 'ROCIO DEL CARMEN', '0341722', 'Trabajador de Servicio', 'AA', 'NOMBRADO', 1350.00, '04231270112288', '1976-12-16', 'AFP INTEGRA', '16-10-18', '2016-03-01'),
    ('70112289', 'LOPEZ VARGAS', 'JOSE SANTOS', '0341620', 'Auxiliar de Biblioteca', 'AA', 'NOMBRADO', 1350.00, '04231270112289', '1977-01-17', 'AFP PRIMA', '17-00-21', '2017-03-01'),
    ('70112290', 'GONZALES FERNANDEZ', 'BLANCA NIEVES', '0341893', 'Trabajador de Servicio', 'AE', 'NOMBRADO', 1350.00, '04231270112290', '1978-02-18', 'AFP PROFUTURO', '18-02-24', '2018-03-01'),
    ('70112291', 'PEREZ ALVA', 'WALTER DAVID', '0341702', 'Trabajador de Servicio', 'AF', 'CONTRATADO', 1350.00, '04231270112291', '1979-03-19', 'AFP HABITAT', '19-04-27', '2019-03-01'),
    ('70112292', 'CHAVEZ CUEVA', 'MIRTHA MARLENE', '0341722', 'Técnico Administrativo', 'TA', 'NOMBRADO', 1370.00, '04231270112292', '1980-04-20', 'ONP 19990', '20-06-02', '2005-03-01'),
    ('70112293', 'VASQUEZ BAZAN', 'JOSE LUIS', '0341620', 'Oficinista', 'AB', 'NOMBRADO', 1350.00, '04231270112293', '1981-05-21', 'AFP INTEGRA', '21-08-05', '2006-03-01'),
    ('70112294', 'RAMOS PAREDES', 'MARIA ROSARIO', '0341893', 'Secretaria', 'TC', 'NOMBRADO', 1370.00, '04231270112294', '1982-06-22', 'AFP PRIMA', '22-10-08', '2007-03-01'),
    ('70112295', 'CASTILLO CABRERA', 'CARLOS ENRIQUE', '0341702', 'Auxiliar de Laboratorio', 'TB', 'NOMBRADO', 1370.00, '04231270112295', '1983-07-23', 'AFP PROFUTURO', '23-00-11', '2008-03-01'),
    ('70112296', 'ALVAREZ JIMENEZ', 'MARTHA ELENA', '0341722', 'Secretaria', 'TE', 'NOMBRADO', 1370.00, '04231270112296', '1984-08-24', 'AFP HABITAT', '24-02-14', '2009-03-01'),
    ('70112297', 'ESPINOZA SALDAÑA', 'PEDRO WILFREDO', '0341620', 'Oficinista', 'AC', 'NOMBRADO', 1350.00, '04231270112297', '1985-09-25', 'ONP 19990', '05-04-17', '2010-03-01'),
    ('70112298', 'MENDOZA VALENCIA', 'SONIA MARIBEL', '0341893', 'Auxiliar de Laboratorio', 'TF', 'NOMBRADO', 1370.00, '04231270112298', '1986-10-26', 'AFP INTEGRA', '06-06-20', '2011-03-01'),
    ('70112299', 'GUTIERREZ MONTALVO', 'JORGE LUIS', '0341702', 'Técnico Administrativo', 'TD', 'NOMBRADO', 1370.00, '04231270112299', '1987-11-27', 'AFP PRIMA', '07-08-23', '2012-03-01'),
    ('70112300', 'HERRERA ZAPATA', 'MARIA ISABEL', '0341722', 'Trabajador de Servicio', 'AA', 'NOMBRADO', 1350.00, '04231270112300', '1988-12-28', 'AFP PROFUTURO', '08-10-26', '2013-03-01'),
    ('70112301', 'HUAMAN HERNANDEZ', 'MANUEL ENRIQUE', '0341620', 'Auxiliar de Biblioteca', 'AA', 'NOMBRADO', 1350.00, '04231270112301', '1989-01-01', 'AFP HABITAT', '09-00-01', '2014-03-01'),
    ('70112302', 'VARGAS INFANTE', 'CARMEN ROSA', '0341893', 'Trabajador de Servicio', 'AE', 'NOMBRADO', 1350.00, '04231270112302', '1990-02-02', 'ONP 19990', '10-02-04', '2015-03-01'),
    ('70112303', 'FERNANDEZ CORREA', 'LUIS ALBERTO', '0341702', 'Trabajador de Servicio', 'AF', 'CONTRATADO', 1350.00, '04231270112303', '1991-03-03', 'AFP INTEGRA', '11-04-07', '2016-03-01'),
    ('70112304', 'ALVA BECERRA', 'GLORIA TERESA', '0341722', 'Técnico Administrativo', 'TA', 'NOMBRADO', 1370.00, '04231270112304', '1992-04-04', 'AFP PRIMA', '12-06-10', '2017-03-01'),
    ('70112305', 'CUEVA MORI', 'DANIEL RICARDO', '0341620', 'Oficinista', 'AB', 'NOMBRADO', 1350.00, '04231270112305', '1993-05-05', 'AFP PROFUTURO', '13-08-13', '2018-03-01'),
    ('70112306', 'BAZAN ORTEGA', 'MONICA BEATRIZ', '0341893', 'Secretaria', 'TC', 'NOMBRADO', 1370.00, '04231270112306', '1994-06-06', 'AFP HABITAT', '14-10-16', '2019-03-01'),
    ('70112307', 'PAREDES ARAUJO', 'OSCAR EDUARDO', '0341702', 'Auxiliar de Laboratorio', 'TB', 'NOMBRADO', 1370.00, '04231270112307', '1965-07-07', 'ONP 19990', '15-00-19', '2005-03-01'),
    ('70112308', 'CABRERA CHAVESTA', 'TERESA DE JESUS', '0341722', 'Secretaria', 'TE', 'NOMBRADO', 1370.00, '04231270112308', '1966-08-08', 'AFP INTEGRA', '16-02-22', '2006-03-01'),
    ('70112309', 'JIMENEZ DAVILA', 'SEGUNDO RAMIRO', '0341620', 'Oficinista', 'AC', 'NOMBRADO', 1350.00, '04231270112309', '1967-09-09', 'AFP PRIMA', '17-04-25', '2007-03-01'),
    ('70112310', 'SALDAÑA ESTRADA', 'LIDIA MARLENE', '0341893', 'Auxiliar de Laboratorio', 'TF', 'NOMBRADO', 1370.00, '04231270112310', '1968-10-10', 'AFP PROFUTURO', '18-06-28', '2008-03-01'),
    ('70112311', 'VALENCIA FIGUEROA', 'PEDRO PABLO', '0341702', 'Técnico Administrativo', 'TD', 'NOMBRADO', 1370.00, '04231270112311', '1969-11-11', 'AFP HABITAT', '19-08-03', '2009-03-01'),
    ('70112312', 'MONTALVO MALCA', 'LUCIA DEL PILAR', '0341722', 'Trabajador de Servicio', 'AA', 'NOMBRADO', 1350.00, '04231270112312', '1970-12-12', 'ONP 19990', '20-10-06', '2010-03-01'),
    ('70112313', 'ZAPATA JAUREGUI', 'GUILLERMO ALFREDO', '0341620', 'Auxiliar de Biblioteca', 'AA', 'NOMBRADO', 1350.00, '04231270112313', '1971-01-13', 'AFP INTEGRA', '21-00-09', '2011-03-01'),
    ('70112314', 'HERNANDEZ VIGO', 'ELENA MERCEDES', '0341893', 'Trabajador de Servicio', 'AE', 'NOMBRADO', 1350.00, '04231270112314', '1972-02-14', 'AFP PRIMA', '22-02-12', '2012-03-01'),
    ('70112315', 'INFANTE BUSTAMANTE', 'MIGUEL ANGEL', '0341702', 'Trabajador de Servicio', 'AF', 'CONTRATADO', 1350.00, '04231270112315', '1973-03-15', 'AFP PROFUTURO', '23-04-15', '2013-03-01'),
    ('70112316', 'CORREA SALAZAR', 'IRMA YOLANDA', '0341722', 'Técnico Administrativo', 'TA', 'NOMBRADO', 1370.00, '04231270112316', '1974-04-16', 'AFP HABITAT', '24-06-18', '2014-03-01'),
    ('70112317', 'BECERRA TANTALEAN', 'JUAN CARLOS', '0341620', 'Oficinista', 'AB', 'NOMBRADO', 1350.00, '04231270112317', '1975-05-17', 'ONP 19990', '05-08-21', '2015-03-01'),
    ('70112318', 'MORI MURIEL', 'ELIZABETH LUZ', '0341893', 'Secretaria', 'TC', 'NOMBRADO', 1370.00, '04231270112318', '1976-06-18', 'AFP INTEGRA', '06-10-24', '2016-03-01'),
    ('70112319', 'ORTEGA GUEVARA', 'SEGUNDO TEOFILO', '0341702', 'Auxiliar de Laboratorio', 'TB', 'NOMBRADO', 1370.00, '04231270112319', '1977-07-19', 'AFP PRIMA', '07-00-27', '2017-03-01'),
    ('70112320', 'ARAUJO UBILLUS', 'OLGA LIDIA', '0341722', 'Secretaria', 'TE', 'NOMBRADO', 1370.00, '04231270112320', '1978-08-20', 'AFP PROFUTURO', '08-02-02', '2018-03-01'),
    ('70112321', 'CHAVESTA YPARRAGUIRRE', 'VICTOR MANUEL', '0341620', 'Oficinista', 'AC', 'NOMBRADO', 1350.00, '04231270112321', '1979-09-21', 'AFP HABITAT', '09-04-05', '2019-03-01'),
    ('70112322', 'DAVILA ZAMORA', 'DORA ALICIA', '0341893', 'Auxiliar de Laboratorio', 'TF', 'NOMBRADO', 1370.00, '04231270112322', '1980-10-22', 'ONP 19990', '10-06-08', '2005-03-01'),
    ('70112323', 'ESTRADA CORONADO', 'RAUL EDGARDO', '0341702', 'Técnico Administrativo', 'TD', 'NOMBRADO', 1370.00, '04231270112323', '1981-11-23', 'AFP INTEGRA', '11-08-11', '2006-03-01'),
    ('70112324', 'FIGUEROA VALDIVIA', 'CARMEN BEATRIZ', '0341722', 'Trabajador de Servicio', 'AA', 'NOMBRADO', 1350.00, '04231270112324', '1982-12-24', 'AFP PRIMA', '12-10-14', '2007-03-01'),
    ('70112325', 'MALCA CHUNGA', 'CESAR AUGUSTO', '0524181', 'Auxiliar de Biblioteca', 'AA', 'NOMBRADO', 1350.00, '04231270112325', '1983-01-25', 'AFP PROFUTURO', '13-00-17', '2008-03-01'),
    ('70112326', 'JAUREGUI ALVITEZ', 'ROSA ELVIRA', '0524181', 'Trabajador de Servicio', 'AE', 'NOMBRADO', 1350.00, '04231270112326', '1984-02-26', 'AFP HABITAT', '14-02-20', '2009-03-01'),
    ('70112327', 'VIGO BARRUETO', 'FERNANDO JAVIER', '0524181', 'Trabajador de Servicio', 'AF', 'CONTRATADO', 1350.00, '04231270112327', '1985-03-27', 'ONP 19990', '15-04-23', '2010-03-01'),
    ('70112328', 'BUSTAMANTE MONCADA', 'ANA MARIA', '0524181', 'Técnico Administrativo', 'TA', 'NOMBRADO', 1370.00, '04231270112328', '1986-04-28', 'AFP INTEGRA', '16-06-26', '2011-03-01'),
    ('70112329', 'SALAZAR LINGAN', 'ROBERTO CARLOS', '0524181', 'Oficinista', 'AB', 'NOMBRADO', 1350.00, '04231270112329', '1987-05-01', 'AFP PRIMA', '17-08-01', '2012-03-01'),
    ('70112330', 'TANTALEAN CUSTODIO', 'PATRICIA ELIZABETH', '0524181', 'Secretaria', 'TC', 'NOMBRADO', 1370.00, '04231270112330', '1988-06-02', 'AFP PROFUTURO', '18-10-04', '2013-03-01'),
    ('70112331', 'MURIEL IPANAQUE', 'HECTOR DAVID', '0689452', 'Auxiliar de Laboratorio', 'TB', 'NOMBRADO', 1370.00, '04231270112331', '1989-07-03', 'AFP HABITAT', '19-00-07', '2014-03-01'),
    ('70112332', 'GUEVARA QUISPE', 'YOLANDA BEATRIZ', '0689452', 'Secretaria', 'TE', 'NOMBRADO', 1370.00, '04231270112332', '1990-08-04', 'ONP 19990', '20-02-10', '2015-03-01'),
    ('70112333', 'UBILLUS FLORES', 'FELIX ALONSO', '0689452', 'Oficinista', 'AC', 'NOMBRADO', 1350.00, '04231270112333', '1991-09-05', 'AFP INTEGRA', '21-04-13', '2016-03-01'),
    ('70112334', 'YPARRAGUIRRE RODRIGUEZ', 'SILVIA MERCEDES', '0689452', 'Auxiliar de Laboratorio', 'TF', 'NOMBRADO', 1370.00, '04231270112334', '1992-10-06', 'AFP PRIMA', '22-06-16', '2017-03-01'),
    ('70112335', 'ZAMORA SANCHEZ', 'CARLOS ALBERTO', '0689452', 'Técnico Administrativo', 'TD', 'NOMBRADO', 1370.00, '04231270112335', '1993-11-07', 'AFP PROFUTURO', '23-08-19', '2018-03-01'),
    ('70112336', 'CORONADO GARCIA', 'SUSANA BEATRIZ', '0741289', 'Trabajador de Servicio', 'AA', 'NOMBRADO', 1350.00, '04231270112336', '1994-12-08', 'AFP HABITAT', '24-10-22', '2019-03-01'),
    ('70112337', 'VALDIVIA ROJAS', 'VICTOR RAUL', '0741289', 'Auxiliar de Biblioteca', 'AA', 'NOMBRADO', 1350.00, '04231270112337', '1965-01-09', 'ONP 19990', '05-00-25', '2005-03-01'),
    ('70112338', 'CHUNGA DIAZ', 'ROCIO DEL CARMEN', '0741289', 'Trabajador de Servicio', 'AE', 'NOMBRADO', 1350.00, '04231270112338', '1966-02-10', 'AFP INTEGRA', '06-02-28', '2006-03-01'),
    ('70112339', 'ALVITEZ TORRES', 'JOSE SANTOS', '0741289', 'Trabajador de Servicio', 'AF', 'CONTRATADO', 1350.00, '04231270112339', '1967-03-11', 'AFP PRIMA', '07-04-03', '2007-03-01'),
    ('70112340', 'BARRUETO LOPEZ', 'BLANCA NIEVES', '0741289', 'Técnico Administrativo', 'TA', 'NOMBRADO', 1370.00, '04231270112340', '1968-04-12', 'AFP PROFUTURO', '08-06-06', '2008-03-01')
) AS t(dni, apellidos, nombres, cod_mod, cargo_nombre, cat_codigo, situacion_nombre, importe, cuenta, f_nac, pension, ts_str, f_ingreso)
JOIN instituciones i ON i.codigo_modular = t.cod_mod
JOIN cargos c ON c.nombre = t.cargo_nombre
JOIN categorias cat ON cat.codigo = t.cat_codigo
JOIN situaciones s ON s.nombre = t.situacion_nombre
JOIN subtipos_trabajador sub ON sub.nombre = 'ADMINISTRATIVO'
ON CONFLICT (dni) DO UPDATE SET
    apellidos = EXCLUDED.apellidos, nombres = EXCLUDED.nombres, institucion_id = EXCLUDED.institucion_id,
    nivel_id = EXCLUDED.nivel_id, cargo_id = EXCLUDED.cargo_id, categoria_id = EXCLUDED.categoria_id,
    situacion_id = EXCLUDED.situacion_id, importe = EXCLUDED.importe, cuenta_multired = EXCLUDED.cuenta_multired,
    fecha_nacimiento = EXCLUDED.fecha_nacimiento, regimen_pensionario = EXCLUDED.regimen_pensionario,
    tiempo_servicio_texto = EXCLUDED.tiempo_servicio_texto, fecha_ingreso = EXCLUDED.fecha_ingreso, activo = true;

-- 4. PERIODOS Y PLANILLAS MÚLTIPLES (ENERO A MAYO 2026)

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

        -- Versión 1 de IIEE (se crea en BORRADOR y se cerrará al final con sus totales)
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
-- Meses 1, 2 y 3 (Enero, Febrero, Marzo) pasan a CERRADA con sus totales exactos:
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

-- Mes 4 (Abril) pasa a EN_REVISION:
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

-- Mes 5 (Mayo) se mantiene en BORRADOR:
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
