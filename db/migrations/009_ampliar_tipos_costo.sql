-- =============================================================================
-- Migracion 009: ampliar catalogo de etapas de costo
-- Motivo: retroalimentacion del profesor sobre el primer parcial senala que el
--   modelo de costos no permite calcular el costo total de una devolucion
--   (transporte + inspeccion + almacenamiento + reacondicionamiento +
--   destruccion + reembolso + otros costos). El enum anterior ('recoleccion',
--   'inspeccion', 'almacenamiento', 'reembolso', 'disposicion') no distinguia
--   reacondicionamiento de destruccion dentro de "disposicion" y no tenia una
--   categoria abierta para costos no previstos.
-- Trazabilidad: RF-27, RN-10, HU-23, UC-23
-- =============================================================================

-- El CHECK viejo se quita primero: si se reclasifican los datos mientras
-- sigue activo, el propio UPDATE lo viola (el CHECK anterior no conocia
-- 'transporte' ni 'otros' como valores permitidos).
ALTER TABLE costos DROP CONSTRAINT costos_etapa_check;

-- Reclasificacion de datos existentes, ya sin el CHECK viejo de por medio.
-- 'recoleccion' pasa a 'transporte' (mismo hecho, nombre mas preciso).
-- 'disposicion' no distinguia destino: se reclasifica como 'otros' hasta que
-- el analista la corrija manualmente por caso.
UPDATE costos SET etapa = 'transporte' WHERE etapa = 'recoleccion';
UPDATE costos SET etapa = 'otros'      WHERE etapa = 'disposicion';

ALTER TABLE costos ADD CONSTRAINT costos_etapa_check CHECK (etapa IN (
    'transporte', 'inspeccion', 'almacenamiento', 'reacondicionamiento',
    'destruccion', 'reembolso', 'otros'
));

COMMENT ON COLUMN costos.etapa IS 'Categoria del costo acumulado por devolucion (RF-27). Ampliada en la migracion 009 para separar reacondicionamiento de destruccion y permitir otros costos.';
