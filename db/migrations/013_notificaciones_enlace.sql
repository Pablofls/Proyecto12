-- =============================================================================
-- Migracion 013: enlace de destino e indice de bandeja en notificaciones
-- Motivo: la tabla notificaciones (001) solo guardaba el texto. Para que la
--   campanita lleve a la pantalla donde el usuario debe actuar (autorizar,
--   programar, inspeccionar...) cada notificacion necesita su ruta destino.
--   El indice acelera el contador de no leidas y la bandeja por usuario, que
--   se consultan en cada pagina y por sondeo cada 30 s.
--   Es nullable: las filas anteriores y las que inserta un servicio sin url
--   siguen siendo validas (la web cae al expediente de la devolucion).
-- Trazabilidad: RF-29, UC-25, RN-13
-- =============================================================================

ALTER TABLE notificaciones
    ADD COLUMN IF NOT EXISTS url VARCHAR(255);

CREATE INDEX IF NOT EXISTS idx_notificaciones_bandeja
    ON notificaciones (usuario_id, leido, fecha_creacion DESC);
