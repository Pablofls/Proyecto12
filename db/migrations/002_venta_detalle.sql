-- =============================================================================
-- Migracion 002: detalle de venta
-- Motivo: el documento (5.1) establece que la devolucion debe vincularse con el
--   detalle especifico de una venta y no con la venta completa, para soportar
--   compras de varios articulos donde el cliente devuelve solo uno.
-- Trazabilidad: RF-06, RN-01, HU-06, UC-06
-- =============================================================================

CREATE TABLE venta_detalle (
    id              SERIAL PRIMARY KEY,
    venta_id        INTEGER NOT NULL REFERENCES ventas(id) ON DELETE RESTRICT,
    lote_id         INTEGER NOT NULL REFERENCES lotes(id) ON DELETE RESTRICT,
    cantidad        INTEGER NOT NULL CHECK (cantidad > 0),
    precio_unitario NUMERIC(10, 2) NOT NULL CHECK (precio_unitario >= 0)
);
COMMENT ON TABLE venta_detalle IS 'Lineas de una venta. Cada linea es un lote y una cantidad (RF-06, RN-01).';

-- La venta pasa a ser el encabezado: los datos del articulo viven en el detalle.
ALTER TABLE ventas DROP COLUMN lote_id;
ALTER TABLE ventas DROP COLUMN cantidad;
ALTER TABLE ventas DROP COLUMN precio;
COMMENT ON TABLE ventas IS 'Encabezado de la venta original; el articulo vendido vive en venta_detalle (RN-01).';

-- La devolucion apunta a la linea concreta, no a la venta completa.
ALTER TABLE devoluciones DROP COLUMN venta_id;
ALTER TABLE devoluciones ADD COLUMN venta_detalle_id INTEGER NOT NULL
    REFERENCES venta_detalle(id) ON DELETE RESTRICT;
ALTER TABLE devoluciones ADD COLUMN cantidad_devuelta INTEGER NOT NULL DEFAULT 1
    CHECK (cantidad_devuelta > 0);
COMMENT ON COLUMN devoluciones.venta_detalle_id IS 'Linea de venta devuelta. Sustituye a venta_id (RN-01).';

DROP INDEX IF EXISTS idx_ventas_lote;
DROP INDEX IF EXISTS idx_devoluciones_venta;
CREATE INDEX idx_venta_detalle_venta      ON venta_detalle(venta_id);
CREATE INDEX idx_venta_detalle_lote       ON venta_detalle(lote_id);
CREATE INDEX idx_devoluciones_detalle     ON devoluciones(venta_detalle_id);

-- Una misma linea de venta no puede devolverse mas veces de lo que se compro.
-- Se valida en la aplicacion; aqui se deja el indice de apoyo para la consulta.
