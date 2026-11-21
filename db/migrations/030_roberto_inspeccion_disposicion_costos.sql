-- =============================================================================
-- Migracion 030: cierre tecnico de inspeccion, disposicion e impacto economico
-- Responsable: Roberto Sandoval Villarreal
--
-- Se usa el rango 030-039 para evitar colisiones con los cambios paralelos del
-- equipo. Inspecciones conserva el dictamen tecnico; disposicion_inventario es
-- dueno de la decision autorizada y del movimiento fisico; reembolsos_costos
-- es dueno del impacto economico.
-- =============================================================================

ALTER TABLE inspecciones_ref
    ADD COLUMN IF NOT EXISTS estado_dictamen VARCHAR(30) NOT NULL DEFAULT 'concluido'
        CHECK (estado_dictamen IN ('concluido', 'evidencia_insuficiente')),
    ADD COLUMN IF NOT EXISTS recomendacion VARCHAR(30)
        CHECK (recomendacion IN (
            'reintegrar', 'reparar', 'reacondicionar', 'devolver_proveedor',
            'reciclar', 'descartar', 'investigar'
        ));

COMMENT ON COLUMN inspecciones_ref.estado_dictamen IS
    'Estado del dictamen tecnico; evidencia_insuficiente impide decidir disposicion.';
COMMENT ON COLUMN inspecciones_ref.recomendacion IS
    'Recomendacion tecnica no vinculante. La decision pertenece a disposicion-inventario.';

ALTER TABLE disposiciones
    ADD COLUMN IF NOT EXISTS estado VARCHAR(20) NOT NULL DEFAULT 'autorizada'
        CHECK (estado IN ('autorizada', 'ejecutada', 'cancelada')),
    ADD COLUMN IF NOT EXISTS autorizacion_jti VARCHAR(64),
    ADD COLUMN IF NOT EXISTS autorizada_en TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP;

ALTER TABLE inventario_recuperado
    ADD COLUMN IF NOT EXISTS ubicacion VARCHAR(100),
    ADD COLUMN IF NOT EXISTS motivo_bloqueo VARCHAR(255),
    ADD COLUMN IF NOT EXISTS reincorporado_por INTEGER REFERENCES usuarios(id) ON DELETE RESTRICT,
    ADD COLUMN IF NOT EXISTS fecha_reincorporacion TIMESTAMPTZ;

ALTER TABLE inventario_recuperado DROP CONSTRAINT IF EXISTS inventario_recuperado_estado_check;
ALTER TABLE inventario_recuperado
    ALTER COLUMN estado SET DEFAULT 'cuarentena';
ALTER TABLE inventario_recuperado
    ADD CONSTRAINT inventario_recuperado_estado_check
    CHECK (estado IN ('cuarentena', 'bloqueado', 'disponible', 'reservado', 'vendido'));

COMMENT ON COLUMN inventario_recuperado.estado IS
    'Todo articulo ingresa en cuarentena. Solo una reincorporacion autorizada lo vuelve disponible.';

-- Los nombres canonicos del servicio nuevo se agregan sin invalidar datos
-- historicos. "inventario" equivale a "reintegrar" para compatibilidad.
ALTER TABLE disposiciones DROP CONSTRAINT IF EXISTS disposiciones_destino_check;
ALTER TABLE disposiciones ADD CONSTRAINT disposiciones_destino_check CHECK (destino IN (
    'inventario', 'reintegrar', 'reparacion', 'reacondicionamiento',
    'reciclaje', 'devolucion_proveedor', 'desecho', 'donacion'
));

-- El trigger anterior permitia insertar directamente en inventario. Ahora la
-- barrera adicional exige una disposicion autorizada y crea cuarentena.
CREATE OR REPLACE FUNCTION fn_validar_alta_inventario_recuperado()
RETURNS TRIGGER AS $$
DECLARE
    v_destino VARCHAR(30);
    v_estado  VARCHAR(20);
BEGIN
    SELECT destino, estado INTO v_destino, v_estado
      FROM disposiciones WHERE id = NEW.disposicion_id;
    IF v_destino NOT IN ('inventario', 'reintegrar') OR v_estado <> 'autorizada' THEN
        RAISE EXCEPTION 'El articulo requiere disposicion de reintegro autorizada.';
    END IF;
    IF NEW.estado = 'disponible' AND TG_OP = 'INSERT' THEN
        RAISE EXCEPTION 'Un articulo recuperado debe ingresar primero a cuarentena.';
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_validar_alta_inventario_recuperado ON inventario_recuperado;
CREATE TRIGGER trg_validar_alta_inventario_recuperado
    BEFORE INSERT ON inventario_recuperado
    FOR EACH ROW EXECUTE FUNCTION fn_validar_alta_inventario_recuperado();

ALTER TABLE costos DROP CONSTRAINT IF EXISTS costos_etapa_check;
ALTER TABLE costos ADD CONSTRAINT costos_etapa_check CHECK (etapa IN (
    'recoleccion', 'transporte', 'inspeccion', 'almacenamiento', 'reparacion',
    'reacondicionamiento', 'destruccion', 'reembolso', 'otros'
));

CREATE TABLE IF NOT EXISTS recuperaciones_valor (
    id              SERIAL PRIMARY KEY,
    devolucion_id   INTEGER NOT NULL REFERENCES devoluciones(id) ON DELETE RESTRICT,
    disposicion_id  INTEGER REFERENCES disposiciones(id) ON DELETE RESTRICT,
    monto           NUMERIC(10,2) NOT NULL CHECK (monto >= 0),
    concepto        VARCHAR(120) NOT NULL,
    registrado_por  INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    fecha           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_recuperaciones_devolucion
    ON recuperaciones_valor(devolucion_id);

CREATE OR REPLACE VIEW vista_impacto_economico_devolucion AS
SELECT d.id AS devolucion_id,
       COALESCE(c.costo_total, 0) AS costo_total,
       COALESCE(r.valor_recuperado, 0) AS valor_recuperado,
       COALESCE(c.costo_total, 0) - COALESCE(r.valor_recuperado, 0) AS costo_neto
  FROM devoluciones d
  LEFT JOIN (
      SELECT devolucion_id, SUM(monto) AS costo_total
        FROM costos GROUP BY devolucion_id
  ) c ON c.devolucion_id = d.id
  LEFT JOIN (
      SELECT devolucion_id, SUM(monto) AS valor_recuperado
        FROM recuperaciones_valor GROUP BY devolucion_id
  ) r ON r.devolucion_id = d.id;

COMMENT ON VIEW vista_impacto_economico_devolucion IS
    'Costo bruto, valor recuperado y costo neto sin duplicar datos transaccionales.';
