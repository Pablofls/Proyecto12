-- =============================================================================
-- Migracion 011: agregar el destino "donacion" al catalogo de disposiciones
-- Motivo: la retroalimentacion enumera REINTEGRAR INVENTARIO, REACONDICIONAR,
--   DEVOLVER PROVEEDOR, DESTRUIR, DONAR y RECICLAR como los destinos que la
--   disposicion debe poder decidir. El esquema ya cubria los primeros cinco
--   (inventario, reacondicionamiento, devolucion_proveedor, desecho, reciclaje)
--   mas 'reparacion', que el negocio ya usaba y no entra en conflicto. Faltaba
--   'donacion'.
-- Trazabilidad: RF-18, RN-07, HU-16, UC-15
-- =============================================================================

ALTER TABLE disposiciones DROP CONSTRAINT disposiciones_destino_check;
ALTER TABLE disposiciones ADD CONSTRAINT disposiciones_destino_check CHECK (destino IN (
    'inventario', 'reparacion', 'reacondicionamiento',
    'reciclaje', 'devolucion_proveedor', 'desecho', 'donacion'
));
