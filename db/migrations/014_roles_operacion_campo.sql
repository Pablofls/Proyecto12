-- =============================================================================
-- Migracion 014: roles de operacion en campo y supervision (tercer parcial)
-- Motivo: la aplicacion Android atiende perfiles que trabajan fuera de una
--   oficina y que el catalogo de 008 no tenia:
--   - Recolector: recoge el producto con el cliente o lo transporta; escanea
--     QR o codigo de barras, registra GPS, fotografias, incidencias y prueba
--     de recoleccion o entrega.
--   - Operador de Almacen: recibe el paquete, lo compara contra la devolucion
--     autorizada, identifica lote y serie, y lo ubica en cuarentena o
--     inspeccion.
--   - Supervisor: revisa incidencias, autoriza las excepciones permitidas y
--     recibe alertas de devoluciones recurrentes.
--   Igual que en 008, los nombres son parte del contrato del sistema: el JWT
--   los lleva en el claim "rol" y shared/seguridad.py los compara textualmente.
--   Ningun endpoint existente cambia de permisos con esta migracion: cada
--   servicio debe autorizarlos de forma explicita (minimo privilegio, RN-13).
-- Trazabilidad: RF-04, RN-13, RNF-09
-- =============================================================================

INSERT INTO roles (nombre, descripcion) VALUES
    ('Recolector',          'Recoge o transporta el producto devuelto; escanea, registra GPS, evidencia, incidencias y prueba de entrega'),
    ('Operador de Almacen', 'Recibe el producto, lo compara con la devolucion autorizada y lo ubica en cuarentena o inspeccion'),
    ('Supervisor',          'Revisa incidencias, autoriza excepciones permitidas y recibe alertas de devoluciones recurrentes')
ON CONFLICT (nombre) DO NOTHING;
