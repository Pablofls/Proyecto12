-- =============================================================================
-- Migracion 007: generacion del folio de devolucion
-- Motivo: RN-02 exige un folio unico e irrepetible desde el momento del
--   registro. Calcularlo contando filas es incorrecto en cuanto dos usuarios
--   registran al mismo tiempo (RNF-19), asi que se delega a una secuencia.
-- Trazabilidad: RF-08, RN-02, HU-08, UC-06
-- =============================================================================

CREATE SEQUENCE seq_folio_devolucion START 1;

CREATE OR REPLACE FUNCTION fn_nuevo_folio_devolucion()
RETURNS VARCHAR AS $$
BEGIN
    RETURN 'DEV-' || to_char(CURRENT_DATE, 'YYYY') || '-' ||
           lpad(nextval('seq_folio_devolucion')::text, 4, '0');
END;
$$ LANGUAGE plpgsql;

ALTER TABLE devoluciones ALTER COLUMN folio_devolucion SET DEFAULT fn_nuevo_folio_devolucion();
