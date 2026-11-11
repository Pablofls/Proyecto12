-- =============================================================================
-- Migracion 017: registro de operaciones capturadas sin conexion
-- Motivo: el tercer parcial agrega el dominio 20 (sincronizacion offline). La
--   app Android y la de escritorio guardan operaciones mientras no hay red y las
--   envian despues, a veces mas de una vez (reintentos, cortes a la mitad).
--   Cada operacion trae un id_operacion (UUID) que genera el dispositivo. Esta
--   tabla es la llave de idempotencia: el id es PRIMARY KEY, asi que la misma
--   operacion nunca se aplica dos veces aunque llegue repetida o en paralelo.
--   La fila y el efecto (recepcion, cambio de estado, evidencia) se guardan en la
--   MISMA transaccion: o quedan los dos o ninguno.
--   'huella' es el SHA-256 del contenido: si un dispositivo reutiliza un id con
--   datos distintos se rechaza en lugar de devolver un resultado que no le toca.
--   Una operacion solo cuenta como confirmada cuando estado = 'aceptada'.
-- Trazabilidad: RF-12 a RF-15, RNF-09, RNF-28, dominio 20 del tercer parcial
-- =============================================================================

CREATE TABLE IF NOT EXISTS operaciones_offline (
    id_operacion    UUID PRIMARY KEY,
    usuario_id      INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    dispositivo_id  VARCHAR(64) NOT NULL,
    tipo            VARCHAR(40) NOT NULL,
    devolucion_id   INTEGER REFERENCES devoluciones(id) ON DELETE RESTRICT,
    huella          CHAR(64) NOT NULL,
    estado          VARCHAR(20) NOT NULL
        CHECK (estado IN ('aceptada', 'conflicto', 'rechazada')),
    resultado       JSONB NOT NULL,
    capturado_en    TIMESTAMPTZ NOT NULL,
    recibido_en     TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    envios          INTEGER NOT NULL DEFAULT 1 CHECK (envios >= 1)
);
COMMENT ON TABLE operaciones_offline IS
    'Operaciones enviadas por las apps despues de trabajar sin conexion. id_operacion es la llave de idempotencia (dominio 20).';
COMMENT ON COLUMN operaciones_offline.envios IS
    'Cuantas veces llego la misma operacion. Mas de 1 = reintento que no se volvio a aplicar.';

CREATE INDEX IF NOT EXISTS idx_operaciones_offline_usuario
    ON operaciones_offline (usuario_id, recibido_en DESC);
CREATE INDEX IF NOT EXISTS idx_operaciones_offline_devolucion
    ON operaciones_offline (devolucion_id);
