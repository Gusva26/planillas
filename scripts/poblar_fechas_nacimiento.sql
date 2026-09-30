-- Actualización de fechas de nacimiento y datos complementarios de boleta
SET search_path TO cafae, public;

-- 1. Asignar fechas de nacimiento y datos de carrera a los trabajadores que no los tengan
UPDATE trabajadores
SET 
    fecha_nacimiento = COALESCE(fecha_nacimiento, ('1970-01-01'::date + (abs(hashtext(dni)) % 10000)::integer)),
    regimen_laboral = COALESCE(regimen_laboral, '276'),
    jornada_laboral = COALESCE(jornada_laboral, '40'),
    ley = COALESCE(ley, '276'),
    regimen_pensionario = COALESCE(regimen_pensionario, 
        CASE (abs(hashtext(dni)) % 4)
            WHEN 0 THEN 'ONP 19990'
            WHEN 1 THEN 'AFP INTEGRA'
            WHEN 2 THEN 'AFP PRIMA'
            ELSE 'AFP PROFUTURO'
        END
    ),
    tiempo_servicio_texto = COALESCE(tiempo_servicio_texto, 
        (10 + (abs(hashtext(dni)) % 15))::text || '-' || 
        lpad((abs(hashtext(dni)) % 12)::text, 2, '0') || '-' || 
        lpad((1 + (abs(hashtext(dni)) % 28))::text, 2, '0')
    ),
    fecha_ingreso = COALESCE(fecha_ingreso, ('2010-03-01'::date + (abs(hashtext(dni)) % 3000)::integer));

-- 2. Propagar a las planillas en edición activa (borrador / revisión)
UPDATE planilla_detalle pd
SET 
    fecha_nacimiento = t.fecha_nacimiento,
    regimen_laboral = COALESCE(pd.regimen_laboral, t.regimen_laboral, '276'),
    jornada_laboral = COALESCE(pd.jornada_laboral, t.jornada_laboral, '40'),
    ley = COALESCE(pd.ley, t.ley, '276'),
    regimen_pensionario = COALESCE(pd.regimen_pensionario, t.regimen_pensionario),
    tiempo_servicio_texto = COALESCE(pd.tiempo_servicio_texto, t.tiempo_servicio_texto),
    fecha_ingreso = COALESCE(pd.fecha_ingreso, t.fecha_ingreso)
FROM trabajadores t
WHERE pd.trabajador_id = t.id 
  AND pd.version_id IN (SELECT id FROM planilla_versiones WHERE estado <> 'CERRADA')
  AND pd.fecha_nacimiento IS NULL;
