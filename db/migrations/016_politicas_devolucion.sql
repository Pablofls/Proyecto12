-- =============================================================================
-- Migracion 016: politica de plazo de devolucion por clasificacion
-- Motivo: la retroalimentacion del segundo parcial pide validar plazos y
--   elegibilidad al crear una devolucion, y que las decisiones respondan a
--   politicas formalmente definidas. Se agrega la regla de negocio RN-16:
--     - Producto no refrigerado: hasta 30 dias naturales desde la venta.
--     - Producto refrigerado:    hasta 7 dias naturales desde la venta.
--   El ultimo dia del plazo todavia se acepta.
--   El plazo vive en esta tabla y no en el codigo para que el servicio de
--   devoluciones y la web en modo monolitico lean la MISMA politica: si cambia,
--   cambia para los dos caminos a la vez.
--   No se usa un trigger: el seed y las pruebas siembran devoluciones historicas
--   sobre ventas de hace meses, y un trigger las rechazaria. La regla se aplica
--   al registrar una solicitud nueva (API y web).
-- Trazabilidad: RF-07, RN-01, RN-16
-- =============================================================================

CREATE TABLE IF NOT EXISTS politicas_devolucion (
    clasificacion_temperatura   VARCHAR(20) PRIMARY KEY
        CHECK (clasificacion_temperatura IN ('refrigerado', 'no_refrigerado')),
    dias_plazo                  INTEGER NOT NULL CHECK (dias_plazo BETWEEN 1 AND 365),
    actualizado_en              TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE politicas_devolucion IS
    'Plazo maximo para solicitar una devolucion segun la clasificacion del producto (RN-16).';

INSERT INTO politicas_devolucion (clasificacion_temperatura, dias_plazo) VALUES
    ('no_refrigerado', 30),
    ('refrigerado',     7)
ON CONFLICT (clasificacion_temperatura) DO NOTHING;
