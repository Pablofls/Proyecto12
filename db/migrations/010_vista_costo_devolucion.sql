-- =============================================================================
-- Migracion 010: vista de costo total por devolucion
-- Motivo: el impacto economico de cada devolucion (RF-27) y del analisis de
--   causa raiz (RF-26) necesita el costo total, desglosado por etapa. Se
--   resuelve con una vista, no con una columna calculada sobre devoluciones,
--   para no duplicar datos que ya viven en costos: una columna asi tendria
--   dependencia funcional sobre otra tabla, no sobre su propia llave, y abre
--   la puerta a que quede desincronizada (rompe 3FN/4FN). La vista siempre
--   lee el dato vivo.
-- Trazabilidad: RF-26, RF-27, RN-10, HU-23, UC-23
-- =============================================================================

CREATE VIEW vista_costo_devolucion AS
SELECT
    devolucion_id,
    COALESCE(SUM(monto) FILTER (WHERE etapa = 'transporte'), 0)          AS costo_transporte,
    COALESCE(SUM(monto) FILTER (WHERE etapa = 'inspeccion'), 0)          AS costo_inspeccion,
    COALESCE(SUM(monto) FILTER (WHERE etapa = 'almacenamiento'), 0)      AS costo_almacenamiento,
    COALESCE(SUM(monto) FILTER (WHERE etapa = 'reacondicionamiento'), 0) AS costo_reacondicionamiento,
    COALESCE(SUM(monto) FILTER (WHERE etapa = 'destruccion'), 0)         AS costo_destruccion,
    COALESCE(SUM(monto) FILTER (WHERE etapa = 'reembolso'), 0)           AS monto_reembolsado,
    COALESCE(SUM(monto) FILTER (WHERE etapa = 'otros'), 0)               AS costo_otros,
    SUM(monto)                                                           AS costo_total
FROM costos
GROUP BY devolucion_id;

COMMENT ON VIEW vista_costo_devolucion IS 'Costo total por devolucion desglosado por etapa (RF-26, RF-27). Vista de solo lectura sobre costos; no almacena datos redundantes.';
