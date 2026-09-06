-- =============================================================================
-- Migracion 005: eliminacion logica y politicas de retencion
-- Motivo: RNF-30 exige eliminacion logica cuando sea necesario conservar el
--   historial de una devolucion. El esquema base solo tenia banderas 'activo'
--   en los catalogos, no en las tablas del expediente.
-- Trazabilidad: RNF-30, RN-12
-- =============================================================================

ALTER TABLE usuarios      ADD COLUMN eliminado_en TIMESTAMPTZ;
ALTER TABLE ventas        ADD COLUMN eliminado_en TIMESTAMPTZ;
ALTER TABLE devoluciones  ADD COLUMN eliminado_en TIMESTAMPTZ;
ALTER TABLE evidencias    ADD COLUMN eliminado_en TIMESTAMPTZ;
ALTER TABLE reembolsos    ADD COLUMN eliminado_en TIMESTAMPTZ;

COMMENT ON COLUMN devoluciones.eliminado_en IS 'Eliminacion logica: el expediente se conserva para auditoria (RNF-30).';

-- Los registros vigentes son los que tienen eliminado_en IS NULL.
CREATE INDEX idx_devoluciones_vigentes ON devoluciones(estado) WHERE eliminado_en IS NULL;
CREATE INDEX idx_usuarios_vigentes     ON usuarios(email)      WHERE eliminado_en IS NULL;
