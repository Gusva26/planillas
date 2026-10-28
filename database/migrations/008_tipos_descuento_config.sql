-- Migración 008: Configuración dinámica de tipos de descuento (activos, alcance IIEE vs SEDE)
SET search_path = cafae, public;

ALTER TABLE tipos_descuento 
    ADD COLUMN IF NOT EXISTS activo BOOLEAN NOT NULL DEFAULT true,
    ADD COLUMN IF NOT EXISTS aplica_iiee BOOLEAN NOT NULL DEFAULT true,
    ADD COLUMN IF NOT EXISTS aplica_sede BOOLEAN NOT NULL DEFAULT true;

ALTER TABLE tipos_descuento DROP CONSTRAINT IF EXISTS tipos_descuento_codigo_check;
ALTER TABLE tipos_descuento DROP CONSTRAINT IF EXISTS tipos_descuento_orden_check;

DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM pg_constraint WHERE conname = 'tipos_descuento_orden_positivo'
    ) THEN
        ALTER TABLE tipos_descuento ADD CONSTRAINT tipos_descuento_orden_positivo CHECK (orden >= 1);
    END IF;
END $$;
