-- =============================================================================
-- Migracion 003: evidencias
-- Motivo: RF-09 exige adjuntar fotografias, documentos y comentarios, y RNF-15
--   exige que los archivos privados se consulten mediante enlaces firmados de
--   duracion limitada. El esquema base no tenia donde registrarlos.
-- Trazabilidad: RF-09, RNF-15, RN-14, HU-07, UC-07
-- =============================================================================

CREATE TABLE evidencias (
    id              SERIAL PRIMARY KEY,
    devolucion_id   INTEGER NOT NULL REFERENCES devoluciones(id) ON DELETE RESTRICT,
    usuario_id      INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    tipo            VARCHAR(20) NOT NULL
        CHECK (tipo IN ('fotografia', 'documento', 'comentario')),
    etapa           VARCHAR(20) NOT NULL DEFAULT 'solicitud'
        CHECK (etapa IN ('solicitud', 'recoleccion', 'recepcion', 'inspeccion')),
    comentario      TEXT,
    -- Para 'fotografia' y 'documento': ubicacion del objeto en el bucket.
    -- Nunca se guarda una URL publica: el enlace firmado se genera al consultar.
    bucket          VARCHAR(100),
    objeto          VARCHAR(255),
    nombre_original VARCHAR(255),
    mime_type       VARCHAR(100),
    tamano_bytes    BIGINT CHECK (tamano_bytes IS NULL OR tamano_bytes >= 0),
    fecha_registro  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (
        (tipo = 'comentario' AND comentario IS NOT NULL)
        OR (tipo <> 'comentario' AND objeto IS NOT NULL)
    )
);
COMMENT ON TABLE evidencias IS 'Evidencias del caso. Los archivos viven en el bucket; aqui solo su referencia (RF-09, RNF-15).';

CREATE INDEX idx_evidencias_devolucion ON evidencias(devolucion_id);
CREATE INDEX idx_evidencias_usuario    ON evidencias(usuario_id);
