-- =============================================================================
-- Migracion 012: fecha de cierre del expediente
-- Motivo: el panel ejecutivo pedido en la retroalimentacion necesita el KPI
--   "tiempo promedio de resolucion". Reconstruirlo desde texto libre de la
--   bitacora seria fragil (habria que parsear el detalle de cada accion). Se
--   agrega una columna atomica, dependiente solo de la llave primaria de
--   devoluciones (no rompe 3FN/4FN), poblada por
--   app/blueprints/devoluciones.py:cambiar_estado cuando el expediente llega a
--   un estado terminal ('cerrada' o 'rechazada').
-- Trazabilidad: RF-26, HU-22, UC-22
-- =============================================================================

ALTER TABLE devoluciones ADD COLUMN fecha_cierre TIMESTAMPTZ;
COMMENT ON COLUMN devoluciones.fecha_cierre IS 'Momento en que el expediente llega a un estado terminal (cerrada o rechazada). NULL mientras el caso sigue abierto (RF-26).';

-- El panel ejecutivo filtra y agrupa por fecha; antes de este bloque ninguna
-- consulta la usaba en el WHERE (RNF-18: respuesta maxima de 3 segundos).
CREATE INDEX idx_devoluciones_fecha_solicitud ON devoluciones(fecha_solicitud);
