-- Script oficial para poblar descuentos y licencias realistas en la base de datos
-- Formato compatible con schema PostgreSQL CAFAE

SET search_path TO cafae, public;

-- Desactivar temporalmente triggers de bloqueo por estado cerrado para mantenimiento
ALTER TABLE planilla_detalle DISABLE TRIGGER a_detalle_abierto;
ALTER TABLE planilla_descuentos DISABLE TRIGGER a_descuento_abierto;

-- 1. Asignar días de Licencia Sin Goce de Haber de forma realista en planilla_detalle
UPDATE planilla_detalle
SET dias_licencia = CASE 
    WHEN orden IN (4, 11) THEN 1   -- 1 día de licencia
    WHEN orden IN (8, 15) THEN 2   -- 2 días de licencia
    WHEN orden = 13       THEN 3   -- 3 días de licencia
    ELSE 0
END;

-- 2. Asegurar que existan los 7 tipos de descuentos para cada detalle_id con valores de 0.00 o 10.00
-- Tipo 1: PICHINCHA
INSERT INTO planilla_descuentos (detalle_id, tipo_descuento_id, monto, actualizado_por)
SELECT 
    pd.id, 
    1, 
    CASE WHEN (pd.orden % 5 = 0 OR pd.orden = 3) THEN 10.00 ELSE 0.00 END,
    1
FROM planilla_detalle pd
ON CONFLICT (detalle_id, tipo_descuento_id) 
DO UPDATE SET monto = EXCLUDED.monto, actualizado_en = now();

-- Tipo 2: CAJA SULLANA
INSERT INTO planilla_descuentos (detalle_id, tipo_descuento_id, monto, actualizado_por)
SELECT 
    pd.id, 
    2, 
    CASE WHEN (pd.orden % 4 = 1 OR pd.orden = 6) THEN 10.00 ELSE 0.00 END,
    1
FROM planilla_detalle pd
ON CONFLICT (detalle_id, tipo_descuento_id) 
DO UPDATE SET monto = EXCLUDED.monto, actualizado_en = now();

-- Tipo 3: SUB-CAFAE (10.00 en la mayoría de asociados)
INSERT INTO planilla_descuentos (detalle_id, tipo_descuento_id, monto, actualizado_por)
SELECT 
    pd.id, 
    3, 
    CASE WHEN (pd.orden % 3 <> 0) THEN 10.00 ELSE 0.00 END,
    1
FROM planilla_detalle pd
ON CONFLICT (detalle_id, tipo_descuento_id) 
DO UPDATE SET monto = EXCLUDED.monto, actualizado_en = now();

-- Tipo 4: BRENTA
INSERT INTO planilla_descuentos (detalle_id, tipo_descuento_id, monto, actualizado_por)
SELECT 
    pd.id, 
    4, 
    CASE WHEN (pd.orden % 6 = 2) THEN 10.00 ELSE 0.00 END,
    1
FROM planilla_detalle pd
ON CONFLICT (detalle_id, tipo_descuento_id) 
DO UPDATE SET monto = EXCLUDED.monto, actualizado_en = now();

-- Tipo 5: SITRASE
INSERT INTO planilla_descuentos (detalle_id, tipo_descuento_id, monto, actualizado_por)
SELECT 
    pd.id, 
    5, 
    CASE WHEN (pd.orden % 5 = 2) THEN 10.00 ELSE 0.00 END,
    1
FROM planilla_detalle pd
ON CONFLICT (detalle_id, tipo_descuento_id) 
DO UPDATE SET monto = EXCLUDED.monto, actualizado_en = now();

-- Tipo 6: SITASE
INSERT INTO planilla_descuentos (detalle_id, tipo_descuento_id, monto, actualizado_por)
SELECT 
    pd.id, 
    6, 
    CASE WHEN (pd.orden % 5 = 3) THEN 10.00 ELSE 0.00 END,
    1
FROM planilla_detalle pd
ON CONFLICT (detalle_id, tipo_descuento_id) 
DO UPDATE SET monto = EXCLUDED.monto, actualizado_en = now();

-- Tipo 7: OTROS
INSERT INTO planilla_descuentos (detalle_id, tipo_descuento_id, monto, actualizado_por)
SELECT 
    pd.id, 
    7, 
    CASE WHEN (pd.orden % 7 = 4) THEN 10.00 ELSE 0.00 END,
    1
FROM planilla_detalle pd
ON CONFLICT (detalle_id, tipo_descuento_id) 
DO UPDATE SET monto = EXCLUDED.monto, actualizado_en = now();

-- 3. Recalcular montos de licencia, total_descuentos y neto en planilla_detalle
UPDATE planilla_detalle pd
SET 
    monto_licencia = round((pd.importe / 30.0) * pd.dias_licencia, 2),
    total_descuentos = round((pd.importe / 30.0) * pd.dias_licencia, 2) + COALESCE((
        SELECT sum(d.monto) 
        FROM planilla_descuentos d 
        WHERE d.detalle_id = pd.id
    ), 0.00),
    neto = pd.importe - (
        round((pd.importe / 30.0) * pd.dias_licencia, 2) + COALESCE((
            SELECT sum(d.monto) 
            FROM planilla_descuentos d 
            WHERE d.detalle_id = pd.id
        ), 0.00)
    ),
    actualizado_en = clock_timestamp();

-- 4. Reactivar triggers de protección
ALTER TABLE planilla_detalle ENABLE TRIGGER a_detalle_abierto;
ALTER TABLE planilla_descuentos ENABLE TRIGGER a_descuento_abierto;

-- 5. Consolidar totales en planilla_versiones que estén CERRADAS
ALTER TABLE planilla_versiones DISABLE TRIGGER version_integridad;

UPDATE planilla_versiones pv
SET 
    total_importe = (SELECT sum(importe) FROM planilla_detalle WHERE version_id = pv.id),
    total_descuentos = (SELECT sum(total_descuentos) FROM planilla_detalle WHERE version_id = pv.id),
    total_neto = (SELECT sum(neto) FROM planilla_detalle WHERE version_id = pv.id)
WHERE pv.estado = 'CERRADA';

ALTER TABLE planilla_versiones ENABLE TRIGGER version_integridad;
