-- =============================================================================
-- Proyecto: Plataforma para gestion y analisis de devoluciones
--           (productos refrigerados y no refrigerados)
-- Motor: PostgreSQL
-- Modelo: version normalizada a 3FN
--   (VENTAS sin producto_id, DEVOLUCIONES sin cliente_id -- ver seccion 4.3.1)
-- =============================================================================

-- =============================================================================
-- 1. CATALOGOS
-- =============================================================================

CREATE TABLE roles (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(60) NOT NULL UNIQUE,
    descripcion     VARCHAR(255)
);
COMMENT ON TABLE roles IS 'Catalogo de roles del sistema (RF-04, 3.5 Perfiles y permisos)';

CREATE TABLE proveedores (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(150) NOT NULL,
    contacto        VARCHAR(150),
    activo          BOOLEAN NOT NULL DEFAULT TRUE
);
COMMENT ON TABLE proveedores IS 'Catalogo de proveedores (RF-05)';

CREATE TABLE productos (
    id                          SERIAL PRIMARY KEY,
    sku                         VARCHAR(50) NOT NULL UNIQUE,
    nombre                      VARCHAR(150) NOT NULL,
    clasificacion_temperatura   VARCHAR(20) NOT NULL
        CHECK (clasificacion_temperatura IN ('refrigerado', 'no_refrigerado')),
    proveedor_id                INTEGER NOT NULL REFERENCES proveedores(id) ON DELETE RESTRICT,
    activo                      BOOLEAN NOT NULL DEFAULT TRUE
);
COMMENT ON TABLE productos IS 'Catalogo de productos, clasificados como refrigerado/no_refrigerado (RF-05, RN-05)';

CREATE TABLE lotes (
    id                  SERIAL PRIMARY KEY,
    producto_id         INTEGER NOT NULL REFERENCES productos(id) ON DELETE RESTRICT,
    proveedor_id        INTEGER NOT NULL REFERENCES proveedores(id) ON DELETE RESTRICT,
    numero_lote         VARCHAR(50) NOT NULL,
    fecha_fabricacion   DATE,
    fecha_caducidad     DATE,
    activo              BOOLEAN NOT NULL DEFAULT TRUE,
    UNIQUE (producto_id, numero_lote)
);
COMMENT ON TABLE lotes IS 'Lotes de fabricacion de cada producto (RF-05)';

CREATE TABLE tiendas (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(150) NOT NULL,
    direccion       VARCHAR(255),
    activo          BOOLEAN NOT NULL DEFAULT TRUE
);
COMMENT ON TABLE tiendas IS 'Catalogo de tiendas (RF-05)';

CREATE TABLE rutas (
    id              SERIAL PRIMARY KEY,
    origen          VARCHAR(150) NOT NULL,
    destino         VARCHAR(150) NOT NULL,
    activo          BOOLEAN NOT NULL DEFAULT TRUE
);
COMMENT ON TABLE rutas IS 'Catalogo de rutas de logistica inversa (RF-05)';

CREATE TABLE transportistas (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(150) NOT NULL,
    empresa         VARCHAR(150),
    activo          BOOLEAN NOT NULL DEFAULT TRUE
);
COMMENT ON TABLE transportistas IS 'Catalogo de transportistas (RF-05, RF-13)';

CREATE TABLE motivos (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(100) NOT NULL,
    descripcion     VARCHAR(255),
    activo          BOOLEAN NOT NULL DEFAULT TRUE
);
COMMENT ON TABLE motivos IS 'Catalogo de motivos de devolucion (RF-05, RF-07)';

-- =============================================================================
-- 2. USUARIOS Y VENTAS
-- =============================================================================

CREATE TABLE usuarios (
    id              SERIAL PRIMARY KEY,
    nombre          VARCHAR(150) NOT NULL,
    email           VARCHAR(150) NOT NULL UNIQUE,
    password_hash   VARCHAR(255) NOT NULL,
    rol_id          INTEGER NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    estado          VARCHAR(20) NOT NULL DEFAULT 'activo'
        CHECK (estado IN ('activo', 'inactivo', 'bloqueado')),
    fecha_creacion  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE usuarios IS 'Usuarios del sistema, cualquier rol (RF-01, RF-02, RF-03, RF-04)';

CREATE TABLE ventas (
    id              SERIAL PRIMARY KEY,
    folio_venta     VARCHAR(50) NOT NULL UNIQUE,
    cliente_id      INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    lote_id         INTEGER NOT NULL REFERENCES lotes(id) ON DELETE RESTRICT,
    tienda_id       INTEGER NOT NULL REFERENCES tiendas(id) ON DELETE RESTRICT,
    fecha_venta     DATE NOT NULL,
    cantidad        INTEGER NOT NULL CHECK (cantidad > 0),
    precio          NUMERIC(10, 2) NOT NULL CHECK (precio >= 0)
    -- Nota (3FN): el producto de la venta se obtiene via lote_id -> lotes.producto_id
);
COMMENT ON TABLE ventas IS 'Ventas originales; base para toda devolucion (RN-01). Normalizado a 3FN: sin producto_id.';

-- =============================================================================
-- 3. PROCESO PRINCIPAL DE LA DEVOLUCION
-- =============================================================================

CREATE TABLE devoluciones (
    id                      SERIAL PRIMARY KEY,
    folio_devolucion        VARCHAR(50) NOT NULL UNIQUE,
    venta_id                INTEGER NOT NULL REFERENCES ventas(id) ON DELETE RESTRICT,
    motivo_id               INTEGER NOT NULL REFERENCES motivos(id) ON DELETE RESTRICT,
    descripcion_problema    TEXT NOT NULL,
    estado                  VARCHAR(30) NOT NULL DEFAULT 'solicitada'
        CHECK (estado IN (
            'solicitada', 'en_revision', 'autorizada', 'rechazada',
            'en_recoleccion', 'recibida', 'en_inspeccion', 'resuelta', 'cerrada'
        )),
    analista_id             INTEGER REFERENCES usuarios(id) ON DELETE RESTRICT,
    fecha_solicitud         TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_autorizacion      TIMESTAMPTZ
    -- Nota (3FN): el cliente de la devolucion se obtiene via venta_id -> ventas.cliente_id
);
COMMENT ON TABLE devoluciones IS 'Expediente central de cada devolucion (RF-06 a RF-11). Normalizado a 3FN: sin cliente_id. RN-01: venta_id NOT NULL. RN-02: folio_devolucion UNIQUE.';

CREATE TABLE recolecciones (
    id                  SERIAL PRIMARY KEY,
    devolucion_id       INTEGER NOT NULL UNIQUE REFERENCES devoluciones(id) ON DELETE RESTRICT,
    fecha_programada    DATE,
    lugar               VARCHAR(255),
    ruta_id             INTEGER REFERENCES rutas(id) ON DELETE RESTRICT,
    transportista_id    INTEGER REFERENCES transportistas(id) ON DELETE RESTRICT,
    coordinador_id      INTEGER REFERENCES usuarios(id) ON DELETE RESTRICT,
    estado              VARCHAR(20) NOT NULL DEFAULT 'programada'
        CHECK (estado IN ('programada', 'asignada', 'en_transito', 'completada', 'fallida'))
);
COMMENT ON TABLE recolecciones IS 'Recoleccion del producto devuelto (RF-12, RF-13). devolucion_id UNIQUE (1 a 0..1).';

CREATE TABLE recepciones (
    id                      SERIAL PRIMARY KEY,
    devolucion_id           INTEGER NOT NULL UNIQUE REFERENCES devoluciones(id) ON DELETE RESTRICT,
    encargado_id            INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    fecha_recepcion         TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    coincide_expediente     BOOLEAN NOT NULL DEFAULT TRUE
);
COMMENT ON TABLE recepciones IS 'Confirmacion de recepcion en el centro de devoluciones (RF-15). devolucion_id UNIQUE (1 a 0..1).';

CREATE TABLE inspecciones_ref (
    id                      SERIAL PRIMARY KEY,
    devolucion_id           INTEGER NOT NULL UNIQUE REFERENCES devoluciones(id) ON DELETE RESTRICT,
    inspector_id            INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    fecha_inspeccion        TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    resultado_general       VARCHAR(50),
    mongo_doc_id            VARCHAR(100),
        -- referencia al documento de detalle en MongoDB (coleccion "inspecciones", 4.4)
    apto_para_inventario    BOOLEAN NOT NULL DEFAULT TRUE
        -- bandera calculada por el microservicio de inspeccion a partir del documento de MongoDB:
        -- pasa a FALSE si el producto tiene danos, caducidad vencida, o (si es refrigerado)
        -- excedio el tiempo permitido fuera de refrigeracion / rompio cadena de frio (RN-06, RN-07).
        -- Esta columna es lo que permite que Postgres SI pueda validar RN-06/RN-07 con un trigger,
        -- aunque el detalle completo de la inspeccion viva en MongoDB.
);
COMMENT ON TABLE inspecciones_ref IS 'Referencia liviana a la inspeccion detallada, cuyo detalle vive en MongoDB (RF-16, RF-17). devolucion_id UNIQUE. apto_para_inventario sincroniza el veredicto de RN-06/RN-07 para poder validarlo en disposiciones.';

CREATE TABLE disposiciones (
    id                  SERIAL PRIMARY KEY,
    devolucion_id       INTEGER NOT NULL UNIQUE REFERENCES devoluciones(id) ON DELETE RESTRICT,
    analista_id         INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    destino             VARCHAR(30) NOT NULL
        CHECK (destino IN (
            'inventario', 'reparacion', 'reacondicionamiento',
            'reciclaje', 'devolucion_proveedor', 'desecho'
        )),
    justificacion       TEXT,
    fecha_decision      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE disposiciones IS 'Decision del destino final del producto (RF-18). devolucion_id UNIQUE (1 a 0..1).';

-- =============================================================================
-- 4. CIERRE Y SOPORTE
-- =============================================================================

CREATE TABLE inventario_recuperado (
    id                  SERIAL PRIMARY KEY,
    disposicion_id      INTEGER NOT NULL UNIQUE REFERENCES disposiciones(id) ON DELETE RESTRICT,
    producto_id         INTEGER NOT NULL REFERENCES productos(id) ON DELETE RESTRICT,
    etiqueta_codigo     VARCHAR(50) NOT NULL UNIQUE,
    fecha_ingreso       TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    estado              VARCHAR(20) NOT NULL DEFAULT 'disponible'
        CHECK (estado IN ('disponible', 'reservado', 'vendido'))
);
COMMENT ON TABLE inventario_recuperado IS 'Inventario de productos recuperados y etiquetados (RF-19, HU-17). disposicion_id UNIQUE: no viola 3FN (es llave candidata).';

CREATE TABLE reembolsos (
    id                  SERIAL PRIMARY KEY,
    devolucion_id       INTEGER NOT NULL UNIQUE REFERENCES devoluciones(id) ON DELETE RESTRICT,
    encargado_id        INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    monto               NUMERIC(10, 2) NOT NULL CHECK (monto >= 0),
    metodo              VARCHAR(30)
        CHECK (metodo IN ('transferencia', 'tarjeta', 'efectivo', 'vale')),
    estado              VARCHAR(20) NOT NULL DEFAULT 'pendiente'
        CHECK (estado IN ('pendiente', 'aprobado', 'rechazado')),
    fecha_resolucion    TIMESTAMPTZ
);
COMMENT ON TABLE reembolsos IS 'Reembolso de una devolucion (RF-20). devolucion_id UNIQUE: garantiza RN-03 (nunca mas de un reembolso valido).';

CREATE TABLE costos (
    id              SERIAL PRIMARY KEY,
    devolucion_id   INTEGER NOT NULL REFERENCES devoluciones(id) ON DELETE RESTRICT,
    etapa           VARCHAR(30) NOT NULL
        CHECK (etapa IN ('recoleccion', 'inspeccion', 'almacenamiento', 'reembolso', 'disposicion')),
    monto           NUMERIC(10, 2) NOT NULL CHECK (monto >= 0),
    fecha           DATE NOT NULL DEFAULT CURRENT_DATE
);
COMMENT ON TABLE costos IS 'Costos acumulados por devolucion y etapa (RF-27)';

CREATE TABLE notificaciones (
    id              SERIAL PRIMARY KEY,
    usuario_id      INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE CASCADE,
    devolucion_id   INTEGER REFERENCES devoluciones(id) ON DELETE CASCADE,
    tipo            VARCHAR(50) NOT NULL,
    mensaje         VARCHAR(500) NOT NULL,
    leido           BOOLEAN NOT NULL DEFAULT FALSE,
    fecha_creacion  TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE notificaciones IS 'Notificaciones automaticas a los usuarios (RF-29)';

CREATE TABLE bitacora (
    id              SERIAL PRIMARY KEY,
    usuario_id      INTEGER REFERENCES usuarios(id) ON DELETE SET NULL,
    accion          VARCHAR(100) NOT NULL,
    entidad         VARCHAR(60) NOT NULL,
    entidad_id      INTEGER,
    detalle         TEXT,
    correlation_id  VARCHAR(100),
    fecha           TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE bitacora IS 'Bitacora de auditoria de operaciones importantes (RF-30, RNF-23)';

-- =============================================================================
-- 5. VALIDACIONES AUTOMATICAS (triggers)
-- Estas reglas viven en las historias/casos de uso (RN-06, RN-07) pero sin un
-- trigger se quedarian solo "en el papel": cualquier microservicio con un bug
-- podria mandar destino='inventario' para un producto danado. Este trigger lo
-- impide directamente en la base de datos, sin depender de que el codigo de
-- aplicacion lo valide correctamente cada vez.
-- =============================================================================

CREATE OR REPLACE FUNCTION fn_validar_destino_inventario()
RETURNS TRIGGER AS $$
DECLARE
    v_apto BOOLEAN;
BEGIN
    IF NEW.destino = 'inventario' THEN
        SELECT apto_para_inventario INTO v_apto
        FROM inspecciones_ref
        WHERE devolucion_id = NEW.devolucion_id;

        IF v_apto IS NULL THEN
            RAISE EXCEPTION
                'No se puede decidir destino=inventario para la devolucion %: no existe una inspeccion registrada (RF-16/RF-17).',
                NEW.devolucion_id;
        ELSIF v_apto = FALSE THEN
            RAISE EXCEPTION
                'No se puede regresar a inventario la devolucion %: la inspeccion indica dano, caducidad vencida o ruptura de cadena de frio (RN-06, RN-07).',
                NEW.devolucion_id;
        END IF;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trg_validar_destino_inventario
    BEFORE INSERT OR UPDATE ON disposiciones
    FOR EACH ROW
    EXECUTE FUNCTION fn_validar_destino_inventario();

-- =============================================================================
-- 6. INDICES DE APOYO
-- Postgres no indexa automaticamente las columnas FK; se agregan aqui
-- para las consultas mas frecuentes (RNF-18: respuesta maxima de 3 segundos)
-- =============================================================================

CREATE INDEX idx_productos_proveedor       ON productos(proveedor_id);
CREATE INDEX idx_lotes_producto            ON lotes(producto_id);
CREATE INDEX idx_lotes_proveedor           ON lotes(proveedor_id);
CREATE INDEX idx_usuarios_rol              ON usuarios(rol_id);
CREATE INDEX idx_ventas_cliente            ON ventas(cliente_id);
CREATE INDEX idx_ventas_lote               ON ventas(lote_id);
CREATE INDEX idx_ventas_tienda             ON ventas(tienda_id);
CREATE INDEX idx_devoluciones_venta        ON devoluciones(venta_id);
CREATE INDEX idx_devoluciones_motivo       ON devoluciones(motivo_id);
CREATE INDEX idx_devoluciones_analista     ON devoluciones(analista_id);
CREATE INDEX idx_devoluciones_estado       ON devoluciones(estado);
CREATE INDEX idx_recolecciones_ruta        ON recolecciones(ruta_id);
CREATE INDEX idx_recolecciones_transp      ON recolecciones(transportista_id);
CREATE INDEX idx_inventario_producto       ON inventario_recuperado(producto_id);
CREATE INDEX idx_costos_devolucion         ON costos(devolucion_id);
CREATE INDEX idx_notificaciones_usuario    ON notificaciones(usuario_id);
CREATE INDEX idx_notificaciones_devolucion ON notificaciones(devolucion_id);
CREATE INDEX idx_bitacora_usuario          ON bitacora(usuario_id);

-- =============================================================================
-- 7. DATOS INICIALES (seed) -- para poder probar el login y el flujo completo
-- =============================================================================

INSERT INTO roles (nombre, descripcion) VALUES
    ('Cliente', 'Solicita devoluciones y consulta su estado'),
    ('Inspector', 'Escanea e inspecciona productos devueltos'),
    ('Encargado del Centro de Devoluciones', 'Confirma recepcion y controla inventario recuperado'),
    ('Coordinador de Logistica', 'Programa y asigna recolecciones'),
    ('Analista de Devoluciones', 'Autoriza solicitudes y decide el destino del producto'),
    ('Encargado de Reembolsos', 'Aprueba y registra reembolsos'),
    ('Administrador', 'Gestiona usuarios, catalogos y monitoreo');

-- Ejemplo de catalogos minimos para poder hacer pruebas de extremo a extremo
INSERT INTO proveedores (nombre, contacto) VALUES ('Lacteos del Norte', 'contacto@lacteosnorte.com');
INSERT INTO productos (sku, nombre, clasificacion_temperatura, proveedor_id) VALUES ('LAC-001', 'Leche Entera 1L', 'refrigerado', 1);
INSERT INTO lotes (producto_id, proveedor_id, numero_lote, fecha_fabricacion, fecha_caducidad) VALUES (1, 1, 'L-2026-045', '2026-08-01', '2026-09-15');
INSERT INTO tiendas (nombre, direccion) VALUES ('Tienda Centro', 'Av. Principal 123');
INSERT INTO rutas (origen, destino) VALUES ('Tienda Centro', 'Centro de Devoluciones Norte');
INSERT INTO transportistas (nombre, empresa) VALUES ('Juan Perez', 'Transportes Rapidos SA');
INSERT INTO motivos (nombre, descripcion) VALUES ('Producto dañado', 'El empaque o el producto llego danado');