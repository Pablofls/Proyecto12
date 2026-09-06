-- =============================================================================
-- Seed 001: catalogos de la distribuidora hipotetica
-- Escenario descrito en la seccion 1.2 del documento: un almacen, un centro de
-- devoluciones y tres tiendas en el area metropolitana de Monterrey.
-- Es idempotente: puede ejecutarse varias veces sin duplicar registros.
-- =============================================================================

INSERT INTO proveedores (nombre, contacto) VALUES
    ('Lacteos del Norte',        'contacto@lacteosnorte.mx'),
    ('CampoVerde Agricola',      'ventas@campoverde.mx'),
    ('Avicola Real',             'pedidos@avicolareal.mx'),
    ('Abarrotes Monterrey',      'contacto@abarrotesmty.mx')
ON CONFLICT DO NOTHING;

INSERT INTO productos (sku, nombre, clasificacion_temperatura, proveedor_id) VALUES
    ('LAC-001', 'Leche entera 1 L',          'refrigerado',    1),
    ('LAC-002', 'Yogurt natural 125 g',      'refrigerado',    1),
    ('LAC-003', 'Queso panela 400 g',        'refrigerado',    1),
    ('AGR-001', 'Lechuga romana',            'refrigerado',    2),
    ('AGR-002', 'Tomate saladette 1 kg',     'refrigerado',    2),
    ('AGR-003', 'Frijol envasado 900 g',     'no_refrigerado', 2),
    ('AVI-001', 'Pechuga de pollo 1 kg',     'refrigerado',    3),
    ('ABA-001', 'Arroz blanco 1 kg',         'no_refrigerado', 4),
    ('ABA-002', 'Aceite vegetal 1 L',        'no_refrigerado', 4),
    ('ABA-003', 'Galletas surtidas 500 g',   'no_refrigerado', 4)
ON CONFLICT (sku) DO NOTHING;

INSERT INTO lotes (producto_id, proveedor_id, numero_lote, fecha_fabricacion, fecha_caducidad) VALUES
    (1, 1, 'L-2026-045', '2026-08-01', '2026-09-15'),
    (1, 1, 'L-2026-052', '2026-08-14', '2026-09-28'),
    (2, 1, 'L-2026-061', '2026-08-05', '2026-09-20'),
    (3, 1, 'L-2026-070', '2026-07-28', '2026-10-01'),
    (4, 2, 'L-2026-112', '2026-08-20', '2026-09-05'),
    (5, 2, 'L-2026-118', '2026-08-22', '2026-09-08'),
    (6, 2, 'L-2026-125', '2026-05-10', '2027-05-10'),
    (7, 3, 'L-2026-201', '2026-08-25', '2026-09-10'),
    (8, 4, 'L-2026-301', '2026-03-01', '2027-03-01'),
    (9, 4, 'L-2026-305', '2026-02-15', '2027-08-15'),
    (10, 4, 'L-2026-312', '2026-06-01', '2027-01-01')
ON CONFLICT (producto_id, numero_lote) DO NOTHING;

INSERT INTO tiendas (nombre, direccion) VALUES
    ('Tienda Centro',       'Av. Constitucion 450, Monterrey'),
    ('Tienda Valle Oriente','Av. Lazaro Cardenas 1200, San Pedro Garza Garcia'),
    ('Tienda Cumbres',      'Av. Paseo de los Leones 3400, Monterrey')
ON CONFLICT DO NOTHING;

INSERT INTO rutas (origen, destino) VALUES
    ('Tienda Centro',        'Centro de Devoluciones Norte'),
    ('Tienda Valle Oriente', 'Centro de Devoluciones Norte'),
    ('Tienda Cumbres',       'Centro de Devoluciones Norte'),
    ('Domicilio del cliente','Centro de Devoluciones Norte')
ON CONFLICT DO NOTHING;

INSERT INTO transportistas (nombre, empresa) VALUES
    ('Juan Perez',      'Transportes Rapidos SA'),
    ('Maria Gonzalez',  'Transportes Rapidos SA'),
    ('Carlos Medina',   'Fletes del Norte'),
    ('Laura Cruz',      'Fletes del Norte')
ON CONFLICT DO NOTHING;

INSERT INTO motivos (nombre, descripcion) VALUES
    ('Producto danado',        'El empaque o el producto llego danado'),
    ('Caducidad vencida',      'El producto supero su fecha de caducidad'),
    ('Caducidad proxima',      'El producto esta proximo a vencer y no puede comercializarse'),
    ('Cadena de frio rota',    'El producto refrigerado no conservo su temperatura'),
    ('Error en el pedido',     'Se entrego un producto diferente al solicitado'),
    ('Calidad inferior',       'El producto no cumple con los estandares de calidad esperados'),
    ('Etiqueta incorrecta',    'La informacion de la etiqueta no coincide con el producto')
ON CONFLICT DO NOTHING;
