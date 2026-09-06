-- =============================================================================
-- Migracion 004: registro de intentos fallidos y bloqueo temporal
-- Motivo: RNF-12 exige registrar los intentos fallidos de inicio de sesion y
--   bloquear la cuenta temporalmente. El conteo vivo se lleva en Redis para no
--   escribir en Postgres en cada intento, pero el historial debe ser auditable
--   y el bloqueo debe sobrevivir a un reinicio de Redis.
-- Trazabilidad: RNF-12, RNF-13, HU-01, UC-01
-- =============================================================================

CREATE TABLE intentos_acceso (
    id              SERIAL PRIMARY KEY,
    email           VARCHAR(150) NOT NULL,
    usuario_id      INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    exitoso         BOOLEAN NOT NULL,
    ip_origen       VARCHAR(45),
    user_agent      VARCHAR(255),
    fecha           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE intentos_acceso IS 'Historial de intentos de inicio de sesion, exitosos y fallidos (RNF-12).';

CREATE INDEX idx_intentos_email ON intentos_acceso(email, fecha DESC);

ALTER TABLE usuarios ADD COLUMN bloqueado_hasta TIMESTAMPTZ;
COMMENT ON COLUMN usuarios.bloqueado_hasta IS 'Fin del bloqueo temporal por intentos fallidos (RNF-12).';

-- La bitacora tambien debe poder registrar el origen de la peticion (RNF-23).
ALTER TABLE bitacora ADD COLUMN ip_origen VARCHAR(45);
