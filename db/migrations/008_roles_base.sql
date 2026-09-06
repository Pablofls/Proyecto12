-- =============================================================================
-- Migracion 008: catalogo de roles
-- Motivo: los nombres de los roles no son datos de demostracion, son parte del
--   contrato del sistema: app/security.py los usa para decidir permisos. Por eso
--   viven en una migracion y no en el seed, que es opcional.
--   Los nombres corresponden a la matriz de perfiles de la seccion 3.5 del
--   documento. El texto de 5.3 decia "Trabajador del centro de devoluciones";
--   se unifico a "Encargado del Centro de Devoluciones".
-- Trazabilidad: RF-04, RN-13, seccion 3.5
-- =============================================================================

INSERT INTO roles (nombre, descripcion) VALUES
    ('Cliente',                             'Solicita devoluciones, adjunta evidencia y consulta el estado de sus casos'),
    ('Inspector',                           'Escanea e inspecciona los productos devueltos y registra sus condiciones'),
    ('Encargado del Centro de Devoluciones','Confirma recepcion, imprime etiquetas y controla el inventario recuperado'),
    ('Coordinador de Logistica',            'Programa y asigna recolecciones, rutas y transportistas'),
    ('Analista de Devoluciones',            'Autoriza solicitudes, decide el destino del producto y revisa causas y reportes'),
    ('Encargado de Reembolsos',             'Aprueba o rechaza reembolsos y registra su estado'),
    ('Administrador',                       'Gestiona usuarios, roles, catalogos y el monitoreo de servicios')
ON CONFLICT (nombre) DO NOTHING;
