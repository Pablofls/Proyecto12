-- =============================================================================
-- Migracion 015: sucursal del usuario
-- Motivo: la retroalimentacion del segundo parcial pide control por sucursal.
--   Hasta ahora ningun usuario pertenecia a una tienda, asi que un operador de
--   la Tienda Centro podia consultar y modificar devoluciones de Cumbres.
--   tienda_id es nullable a proposito: NULL significa que el usuario opera en
--   todas las sucursales (analista, administrador, supervisor regional) y los
--   clientes no dependen de una tienda (su limite es la propiedad de la compra).
--   El servicio auth copia el valor al claim "tienda_id" del JWT y
--   shared/seguridad.py (condicion_tienda, exigir_tienda) lo aplica. La sucursal
--   de una devolucion es la de su venta: ventas.tienda_id.
-- Trazabilidad: RF-04, RN-13, RNF-09
-- =============================================================================

ALTER TABLE usuarios
    ADD COLUMN IF NOT EXISTS tienda_id INTEGER REFERENCES tiendas(id) ON DELETE RESTRICT;

COMMENT ON COLUMN usuarios.tienda_id IS
    'Sucursal donde opera el usuario; NULL = todas las sucursales (RN-13).';

CREATE INDEX IF NOT EXISTS idx_usuarios_tienda ON usuarios(tienda_id);
