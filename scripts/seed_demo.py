"""Carga datos de demostracion: usuarios, ventas y devoluciones en varios estados.

Se ejecuta DESPUES de las migraciones y del seed de catalogos:

    docker compose exec app python scripts/migrate.py
    docker compose exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB < db/seeds/001_catalogos.sql
    docker compose exec app python scripts/seed_demo.py

Para cambiar la contrasena de las cuentas que ya existen:

    docker compose exec app python scripts/seed_demo.py --rotar

La contrasena NO vive en este archivo: se toma de PASSWORD_DEMO en el .env, que
esta fuera de git. Si esa variable esta vacia, el script genera una al azar y la
imprime una sola vez. Asi el repositorio puede ser publico sin regalar el acceso
(RNF-14, RNF-16).

Es idempotente: si los usuarios de demostracion ya existen, no los duplica. Las
contrasenas se guardan con el mismo hash que usa la aplicacion (RNF-07).

Plazo de devolucion (RN-16, migracion 016): las ventas historicas son de agosto
de 2026 y ya estan fuera de plazo (sirven para demostrar el 409). Cada vez que
se corre, el script agrega un juego de ventas RECIENTES fechadas en los ultimos
6 dias, dentro del plazo de 7 dias de los refrigerados. Correlo el dia de la
demostracion para tener compras que se puedan devolver.
"""
import os
import random
import secrets
import sys
from datetime import date, timedelta

import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash


def obtener_password():
    """Devuelve (password, fue_generada).

    Preferimos la del .env para que el equipo comparta la misma. Si no esta
    definida, generamos una al azar: es preferible una contrasena que hay que
    anotar a una escrita en un repositorio publico.
    """
    definida = os.environ.get("PASSWORD_DEMO", "").strip()
    if definida:
        return definida, False
    return secrets.token_urlsafe(12), True

USUARIOS = [
    ("Ana Lopez Garcia",   "ana.cliente@demo.mx",       "Cliente"),
    ("Miguel Ramos Soto",  "miguel.cliente@demo.mx",    "Cliente"),
    ("Sofia Herrera",      "sofia.cliente@demo.mx",     "Cliente"),
    ("Valentina Perez",    "valentina.inspector@demo.mx", "Inspector"),
    ("Roberto Sandoval",   "roberto.centro@demo.mx",    "Encargado del Centro de Devoluciones"),
    ("David Munoz",        "david.logistica@demo.mx",   "Coordinador de Logistica"),
    ("Josue Berdeal",      "josue.analista@demo.mx",    "Analista de Devoluciones"),
    ("Carla Trevino",      "carla.reembolsos@demo.mx",  "Encargado de Reembolsos"),
    ("Pablo Flores",       "pablo.admin@demo.mx",       "Administrador"),
    # Tercer parcial (migracion 014): perfiles de la aplicacion Android.
    ("Luis Garza",         "luis.recolector@demo.mx",   "Recolector"),
    ("Marta Cantu",        "marta.almacen@demo.mx",     "Operador de Almacen"),
    ("Jorge Salinas",      "jorge.supervisor@demo.mx",  "Supervisor"),
]

# Control por sucursal (migracion 015). Quien no aparece aqui opera en todas
# las sucursales; el supervisor es regional a proposito.
SUCURSAL_DEMO = {
    "luis.recolector@demo.mx": "Tienda Centro",
    "marta.almacen@demo.mx": "Tienda Centro",
}


def conectar():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "postgres"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def crear_usuarios(cur, password):
    hash_demo = generate_password_hash(password)
    cur.execute("SELECT id, nombre FROM roles")
    roles = {fila["nombre"]: fila["id"] for fila in cur.fetchall()}

    for nombre, email, rol in USUARIOS:
        cur.execute(
            """
            INSERT INTO usuarios (nombre, email, password_hash, rol_id)
            VALUES (%s, %s, %s, %s)
            ON CONFLICT (email) DO NOTHING
            """,
            (nombre, email, hash_demo, roles[rol]),
        )
    for email, tienda in SUCURSAL_DEMO.items():
        # Solo si no tiene sucursal: no pisa lo que el administrador ya cambio.
        cur.execute(
            """
            UPDATE usuarios SET tienda_id = (SELECT id FROM tiendas WHERE nombre = %s)
             WHERE email = %s AND tienda_id IS NULL
            """,
            (tienda, email),
        )
    cur.execute("SELECT id, email FROM usuarios")
    return {fila["email"]: fila["id"] for fila in cur.fetchall()}


def crear_ventas(cur, clientes):
    """Genera ventas con varias lineas cada una."""
    cur.execute("SELECT id FROM lotes ORDER BY id")
    lotes = [f["id"] for f in cur.fetchall()]
    cur.execute("SELECT id FROM tiendas ORDER BY id")
    tiendas = [f["id"] for f in cur.fetchall()]

    detalles = []
    for i in range(1, 26):
        folio = f"VTA-2026-{i:04d}"
        cur.execute("SELECT id FROM ventas WHERE folio_venta = %s", (folio,))
        if cur.fetchone():
            continue

        cliente_id = random.choice(clientes)
        fecha = date(2026, 8, 1) + timedelta(days=random.randint(0, 30))
        cur.execute(
            """
            INSERT INTO ventas (folio_venta, cliente_id, tienda_id, fecha_venta)
            VALUES (%s, %s, %s, %s) RETURNING id
            """,
            (folio, cliente_id, random.choice(tiendas), fecha),
        )
        venta_id = cur.fetchone()["id"]

        for lote_id in random.sample(lotes, random.randint(1, 4)):
            cur.execute(
                """
                INSERT INTO venta_detalle (venta_id, lote_id, cantidad, precio_unitario)
                VALUES (%s, %s, %s, %s) RETURNING id
                """,
                (venta_id, lote_id, random.randint(1, 3), round(random.uniform(18, 260), 2)),
            )
            detalles.append(cur.fetchone()["id"])
    return detalles


def crear_ventas_recientes(cur, clientes):
    """Ventas dentro del plazo de devolucion (RN-16), relativas a hoy.

    Seis ventas fechadas de hoy a hace 6 dias, cada una con dos productos
    refrigerados y uno no refrigerado, 3 unidades por linea. El folio lleva la
    fecha de hoy: correr el script otro dia agrega un juego nuevo y no toca los
    anteriores. No usa random, para no alterar los datos reproducibles del resto
    del seed.
    """
    hoy = date.today()
    cur.execute("SELECT id FROM tiendas ORDER BY id")
    tiendas = [f["id"] for f in cur.fetchall()]
    # El lote problematico queda fuera: sus 24 unidades y su 66.7 % de devolucion
    # son exactos para la demo de causa raiz y para test_integracion_trazabilidad.
    cur.execute("""
        SELECT l.id, p.clasificacion_temperatura
          FROM lotes l JOIN productos p ON p.id = l.producto_id
         WHERE l.numero_lote <> %s
         ORDER BY l.id""", (LOTE_PROBLEMATICO,))
    lotes = cur.fetchall()
    refrigerados = [l["id"] for l in lotes if l["clasificacion_temperatura"] == "refrigerado"]
    normales = [l["id"] for l in lotes if l["clasificacion_temperatura"] != "refrigerado"]
    if not (tiendas and refrigerados and normales):
        return 0

    creadas = 0
    for n, dias_atras in enumerate((0, 1, 2, 3, 5, 6), start=1):
        folio = f"VTA-{hoy:%Y%m%d}-R{n}"
        cur.execute("SELECT 1 FROM ventas WHERE folio_venta = %s", (folio,))
        if cur.fetchone():
            continue
        cur.execute(
            """
            INSERT INTO ventas (folio_venta, cliente_id, tienda_id, fecha_venta)
            VALUES (%s, %s, %s, %s) RETURNING id
            """,
            (folio, clientes[n % len(clientes)], tiendas[n % len(tiendas)],
             hoy - timedelta(days=dias_atras)),
        )
        venta_id = cur.fetchone()["id"]
        lineas = (refrigerados[n % len(refrigerados)],
                  refrigerados[(n + 1) % len(refrigerados)],
                  normales[n % len(normales)])
        for lote_id in dict.fromkeys(lineas):  # sin repetir lote en la venta
            cur.execute(
                """
                INSERT INTO venta_detalle (venta_id, lote_id, cantidad, precio_unitario)
                VALUES (%s, %s, 3, %s)
                """,
                (venta_id, lote_id, 45 + 10 * n),
            )
        creadas += 1
    return creadas


def crear_devoluciones(cur, detalles, usuarios):
    """Genera devoluciones repartidas entre los estados del proceso.

    La concentracion no es uniforme a proposito: algunos lotes y proveedores
    acumulan mas casos para que el panel de causas muestre algo interpretable.
    """
    cur.execute("SELECT id FROM motivos WHERE activo = TRUE ORDER BY id")
    motivos = [f["id"] for f in cur.fetchall()]

    cur.execute("SELECT COUNT(*) AS total FROM devoluciones")
    if cur.fetchone()["total"] > 0:
        print("  Ya existen devoluciones; no se generan mas.")
        return

    analista = usuarios["josue.analista@demo.mx"]
    inspector = usuarios["valentina.inspector@demo.mx"]
    encargado_centro = usuarios["roberto.centro@demo.mx"]
    coordinador = usuarios["david.logistica@demo.mx"]
    encargado_reembolsos = usuarios["carla.reembolsos@demo.mx"]

    descripciones = [
        "El empaque llego roto y el contenido estaba derramado.",
        "El producto tenia mal olor al abrirlo.",
        "La fecha de caducidad ya habia pasado cuando lo recibi.",
        "El producto llego tibio, no venia refrigerado.",
        "Me entregaron un producto distinto al que pedi.",
        "La etiqueta no corresponde con el contenido del empaque.",
        "El sabor y la textura no son los habituales del producto.",
    ]
    reparto = (
        ["solicitada"] * 5 + ["en_revision"] * 3 + ["autorizada"] * 4 +
        ["rechazada"] * 2 + ["en_recoleccion"] * 4 + ["recibida"] * 3 +
        ["en_inspeccion"] * 3 + ["resuelta"] * 3 + ["cerrada"] * 5
    )

    cur.execute("SELECT id FROM rutas ORDER BY id")
    rutas = [f["id"] for f in cur.fetchall()]
    cur.execute("SELECT id FROM transportistas ORDER BY id")
    transportistas = [f["id"] for f in cur.fetchall()]

    seleccion = random.sample(detalles, min(len(reparto), len(detalles)))

    for estado, detalle_id in zip(reparto, seleccion):
        cur.execute(
            """
            INSERT INTO devoluciones (venta_detalle_id, motivo_id, descripcion_problema,
                                      cantidad_devuelta, estado, analista_id,
                                      fecha_autorizacion)
            VALUES (%s, %s, %s, 1, %s, %s, %s) RETURNING id, folio_devolucion
            """,
            (
                detalle_id,
                random.choice(motivos),
                random.choice(descripciones),
                estado,
                analista if estado not in ("solicitada",) else None,
                "2026-09-01" if estado not in ("solicitada", "en_revision", "rechazada") else None,
            ),
        )
        fila = cur.fetchone()
        devolucion_id = fila["id"]

        cur.execute(
            """
            INSERT INTO bitacora (usuario_id, accion, entidad, entidad_id, detalle, correlation_id)
            VALUES (%s, 'alta_devolucion', 'devoluciones', %s, %s, 'seed-demo')
            """,
            (None, devolucion_id, f"Se registro la devolucion {fila['folio_devolucion']} (datos de demostracion)"),
        )

        avanzadas = ("en_recoleccion", "recibida", "en_inspeccion", "resuelta", "cerrada")
        if estado in avanzadas:
            cur.execute(
                """
                INSERT INTO recolecciones (devolucion_id, fecha_programada, lugar, ruta_id,
                                           transportista_id, coordinador_id, estado)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                """,
                (devolucion_id, "2026-09-03", "Domicilio del cliente",
                 random.choice(rutas), random.choice(transportistas), coordinador,
                 "completada" if estado != "en_recoleccion" else "en_transito"),
            )
            cur.execute(
                "INSERT INTO costos (devolucion_id, etapa, monto) VALUES (%s, 'transporte', %s)",
                (devolucion_id, round(random.uniform(60, 180), 2)),
            )

        if estado in ("recibida", "en_inspeccion", "resuelta", "cerrada"):
            cur.execute(
                """
                INSERT INTO recepciones (devolucion_id, encargado_id, coincide_expediente)
                VALUES (%s, %s, TRUE)
                """,
                (devolucion_id, encargado_centro),
            )

        if estado in ("en_inspeccion", "resuelta", "cerrada"):
            apto = random.random() < 0.4
            cur.execute(
                """
                INSERT INTO inspecciones_ref (devolucion_id, inspector_id, resultado_general,
                                              apto_para_inventario)
                VALUES (%s, %s, %s, %s)
                """,
                (devolucion_id, inspector,
                 "apto para inventario" if apto else "no apto: danos fisicos visibles", apto),
            )
            cur.execute(
                "INSERT INTO costos (devolucion_id, etapa, monto) VALUES (%s, 'inspeccion', %s)",
                (devolucion_id, round(random.uniform(30, 90), 2)),
            )

            if estado in ("resuelta", "cerrada"):
                destino = "inventario" if apto else random.choice(["reciclaje", "desecho",
                                                                   "devolucion_proveedor"])
                cur.execute(
                    """
                    INSERT INTO disposiciones (devolucion_id, analista_id, destino, justificacion)
                    VALUES (%s, %s, %s, %s)
                    """,
                    (devolucion_id, analista, destino,
                     "Decision tomada a partir del resultado de la inspeccion."),
                )

        if estado == "cerrada":
            cur.execute(
                """
                SELECT vd.precio_unitario * d.cantidad_devuelta AS maximo
                  FROM devoluciones d JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
                 WHERE d.id = %s
                """,
                (devolucion_id,),
            )
            maximo = float(cur.fetchone()["maximo"])
            cur.execute(
                """
                INSERT INTO reembolsos (devolucion_id, encargado_id, monto, metodo,
                                        estado, fecha_resolucion)
                VALUES (%s, %s, %s, %s, 'aprobado', CURRENT_TIMESTAMP)
                """,
                (devolucion_id, encargado_reembolsos, round(maximo, 2),
                 random.choice(["transferencia", "tarjeta", "vale"])),
            )
            cur.execute(
                "INSERT INTO costos (devolucion_id, etapa, monto) VALUES (%s, 'reembolso', %s)",
                (devolucion_id, round(maximo, 2)),
            )


def backfill_fecha_cierre(cur):
    """Llena fecha_cierre en devoluciones 'cerrada'/'rechazada' sembradas antes
    de existir esa columna (migracion 012).

    Los datos de demostracion se insertan directo con
    'INSERT INTO devoluciones (..., estado)', sin pasar por
    devoluciones.py:cambiar_estado, que es donde la app normalmente llena
    fecha_cierre. Sin este backfill, el KPI de tiempo de resolucion del panel
    ejecutivo (RF-26) se queda en NULL para siempre en un ambiente sembrado
    antes de la migracion 012. Es idempotente: solo toca filas con
    fecha_cierre todavia en NULL, asi que correrlo de nuevo no cambia nada.
    """
    cur.execute(
        """
        UPDATE devoluciones
           SET fecha_cierre = fecha_solicitud + INTERVAL '5 days'
         WHERE estado IN ('cerrada', 'rechazada') AND fecha_cierre IS NULL
        """
    )
    return cur.rowcount


LOTE_PROBLEMATICO = "L-2026-PROB-01"
UNIDADES_POR_VENTA = 6
# Una fila por venta: (indice de tienda, unidades devueltas, estado, motivo). Centro (0) concentra 3 de 4.
CASOS_LOTE_PROBLEMATICO = [
    (0, 4, "cerrada", "frio"), (0, 4, "cerrada", "frio"),
    (0, 4, "en_inspeccion", "danado"), (1, 4, "autorizada", "frio"),
]


def crear_lote_problematico(cur, usuarios, clientes):
    """Lote refrigerado con devoluciones recurrentes, para la demo de causa raiz.

    La demo del tercer parcial pide "un lote con problemas recurrentes": 4 ventas
    de 6 unidades del mismo lote de leche que devuelven 4 unidades cada una (16 de
    24, 66.7 %), casi todas por cadena de frio rota y 3 de las 4 en Tienda Centro
    por una misma ruta. Asi las tasas por lote, tienda y ruta senalan el mismo patron.

    EL TAMANO IMPORTA. El lote pesa en el promedio global contra el que se compara
    (la alerta pide al menos 2 veces el promedio). La base de demostracion es chica y
    de devoluciones altas (273 unidades vendidas, 60 devueltas, 22 %): un lote de 96
    unidades era el 35 % de todo lo vendido y ni devolviendo todo habria llegado a 2
    veces el promedio. Con 24 unidades y 66.7 % llega a ~2.3 veces y supera las 20
    unidades y los 3 casos minimos para alertar. Se comprobo en la VM.

    No usa random (no altera los datos reproducibles del resto del seed) y es
    idempotente: si el lote ya existe no hace nada (para rehacerlo, --rehacer-lote).
    Las series PROB01-#### se ligan a las lineas de venta (migracion 040).
    Trazabilidad: RF-23, RF-24.
    """
    cur.execute("SELECT 1 FROM lotes l JOIN productos p ON p.id = l.producto_id "
                "WHERE l.numero_lote = %s AND p.sku = 'LAC-001'", (LOTE_PROBLEMATICO,))
    if cur.fetchone():
        return 0
    cur.execute("SELECT id, proveedor_id FROM productos WHERE sku = 'LAC-001'")
    producto = cur.fetchone()
    cur.execute("SELECT id FROM motivos WHERE nombre = 'Cadena de frio rota'")
    frio = cur.fetchone()
    cur.execute("SELECT id FROM motivos WHERE nombre = 'Producto danado'")
    danado = cur.fetchone()
    cur.execute("SELECT id, nombre FROM tiendas ORDER BY id")
    tiendas = cur.fetchall()
    if not (producto and frio and danado and len(tiendas) >= 2):
        return 0
    cur.execute("SELECT id FROM rutas WHERE origen = %s ORDER BY id LIMIT 1",
                (tiendas[0]["nombre"],))
    ruta = cur.fetchone()
    cur.execute("SELECT id FROM transportistas ORDER BY id LIMIT 1")
    transportista = cur.fetchone()

    cur.execute(
        """INSERT INTO lotes (producto_id, proveedor_id, numero_lote,
                              fecha_fabricacion, fecha_caducidad)
           VALUES (%s, %s, %s, '2026-09-20', '2026-11-30') RETURNING id""",
        (producto["id"], producto["proveedor_id"], LOTE_PROBLEMATICO),
    )
    lote_id = cur.fetchone()["id"]

    analista = usuarios["josue.analista@demo.mx"]
    inspector = usuarios["valentina.inspector@demo.mx"]
    encargado = usuarios["roberto.centro@demo.mx"]
    coordinador = usuarios["david.logistica@demo.mx"]
    serie = 0
    for n, (tienda_i, devueltas, estado, clave_motivo) in enumerate(CASOS_LOTE_PROBLEMATICO):
        cur.execute(
            """INSERT INTO ventas (folio_venta, cliente_id, tienda_id, fecha_venta)
               VALUES (%s, %s, %s, %s) RETURNING id""",
            (f"VTA-PROB-{n + 1:02d}", clientes[n % len(clientes)],
             tiendas[tienda_i]["id"], date(2026, 10, 1) + timedelta(days=n)),
        )
        venta_id = cur.fetchone()["id"]
        cur.execute(
            """INSERT INTO venta_detalle (venta_id, lote_id, cantidad, precio_unitario)
               VALUES (%s, %s, %s, 32.50) RETURNING id""",
            (venta_id, lote_id, UNIDADES_POR_VENTA),
        )
        detalle_id = cur.fetchone()["id"]
        for _ in range(UNIDADES_POR_VENTA):
            serie += 1
            cur.execute(
                """INSERT INTO series_producto (lote_id, numero_serie, venta_detalle_id)
                   VALUES (%s, %s, %s)""",
                (lote_id, f"PROB01-{serie:04d}", detalle_id),
            )
        motivo = frio["id"] if clave_motivo == "frio" else danado["id"]
        cur.execute(
            """INSERT INTO devoluciones (venta_detalle_id, motivo_id, descripcion_problema,
                                         cantidad_devuelta, estado, analista_id,
                                         fecha_solicitud, fecha_autorizacion)
               VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id, folio_devolucion""",
            (detalle_id, motivo,
             "El producto llego tibio y con mal olor." if clave_motivo == "frio"
             else "El empaque llego abollado y con fuga.",
             devueltas, estado, analista,
             date(2026, 10, 3) + timedelta(days=n), date(2026, 10, 4) + timedelta(days=n)),
        )
        dev = cur.fetchone()
        cur.execute(
            """INSERT INTO bitacora (usuario_id, accion, entidad, entidad_id, detalle, correlation_id)
               VALUES (NULL, 'alta_devolucion', 'devoluciones', %s, %s, 'seed-demo')""",
            (dev["id"], f"Devolucion {dev['folio_devolucion']} del lote {LOTE_PROBLEMATICO} (demostracion)"),
        )
        if estado == "autorizada":
            continue
        cur.execute(
            """INSERT INTO recolecciones (devolucion_id, fecha_programada, lugar, ruta_id,
                                          transportista_id, coordinador_id, estado)
               VALUES (%s, %s, 'Domicilio del cliente', %s, %s, %s, 'completada')""",
            (dev["id"], date(2026, 10, 6) + timedelta(days=n),
             ruta["id"] if ruta else None,
             transportista["id"] if transportista else None, coordinador),
        )
        cur.execute("INSERT INTO costos (devolucion_id, etapa, monto) VALUES (%s, 'transporte', 95)",
                    (dev["id"],))
        cur.execute(
            "INSERT INTO recepciones (devolucion_id, encargado_id, coincide_expediente) "
            "VALUES (%s, %s, TRUE)", (dev["id"], encargado))
        cur.execute(
            """INSERT INTO inspecciones_ref (devolucion_id, inspector_id, resultado_general,
                                             apto_para_inventario)
               VALUES (%s, %s, 'no apto: cadena de frio rota', FALSE)""",
            (dev["id"], inspector))
        cur.execute("INSERT INTO costos (devolucion_id, etapa, monto) VALUES (%s, 'inspeccion', 45)",
                    (dev["id"],))
        if estado == "cerrada":
            cur.execute(
                """INSERT INTO disposiciones (devolucion_id, analista_id, destino, justificacion)
                   VALUES (%s, %s, 'desecho', 'Producto refrigerado fuera de temperatura.')""",
                (dev["id"], analista))
    return len(CASOS_LOTE_PROBLEMATICO)


def retirar_lote_problematico(cur):
    """Borra SOLO lo que crea crear_lote_problematico, para poder rehacerlo (--rehacer-lote).

    Va en orden de llaves foraneas y se detiene con error, sin borrar nada a medias, si
    alguien ya colgo algo del lote (una investigacion, una reclamacion, una evidencia):
    ese dato no es del seed y no se toca. La bitacora no se modifica: es de solo agregar.
    """
    cur.execute("SELECT l.id FROM lotes l JOIN productos p ON p.id = l.producto_id "
                "WHERE l.numero_lote = %s AND p.sku = 'LAC-001'", (LOTE_PROBLEMATICO,))
    fila = cur.fetchone()
    if not fila:
        return 0
    lote_id = fila["id"]
    cur.execute("SELECT d.id FROM devoluciones d JOIN venta_detalle vd ON vd.id = d.venta_detalle_id "
                "WHERE vd.lote_id = %s", (lote_id,))
    devs = [f["id"] for f in cur.fetchall()]
    if devs:
        cur.execute("DELETE FROM inventario_recuperado WHERE disposicion_id IN "
                    "(SELECT id FROM disposiciones WHERE devolucion_id = ANY(%s))", (devs,))
        for tabla in ("disposiciones", "inspecciones_ref", "recepciones", "recolecciones", "costos"):
            cur.execute(f"DELETE FROM {tabla} WHERE devolucion_id = ANY(%s)", (devs,))  # nombre fijo, no del usuario
        cur.execute("DELETE FROM devoluciones WHERE id = ANY(%s)", (devs,))
    cur.execute("DELETE FROM series_producto WHERE lote_id = %s", (lote_id,))
    cur.execute("DELETE FROM venta_detalle WHERE lote_id = %s", (lote_id,))
    cur.execute("DELETE FROM ventas WHERE folio_venta LIKE 'VTA-PROB-%' AND NOT EXISTS "
                "(SELECT 1 FROM venta_detalle vd WHERE vd.venta_id = ventas.id)")
    cur.execute("DELETE FROM lotes WHERE id = %s", (lote_id,))
    return len(devs)


def rotar_passwords(cur, password):
    """Cambia la contrasena de todas las cuentas de demostracion y las desbloquea."""
    nuevo_hash = generate_password_hash(password)
    correos = [email for _, email, _ in USUARIOS]
    cur.execute(
        """
        UPDATE usuarios
           SET password_hash = %s, bloqueado_hasta = NULL, estado = 'activo'
         WHERE email = ANY(%s)
        """,
        (nuevo_hash, correos),
    )
    return cur.rowcount


def main():
    random.seed(12)  # Datos reproducibles entre integrantes del equipo.
    password, generada = obtener_password()

    if "--rotar" in sys.argv:
        with conectar() as conn:
            with conn.cursor() as cur:
                actualizadas = rotar_passwords(cur, password)
            conn.commit()
        print(f"Contrasena actualizada en {actualizadas} cuentas de demostracion.")
        anunciar_password(password, generada)
        return

    with conectar() as conn:
        with conn.cursor() as cur:
            print("Creando usuarios de demostracion ...")
            usuarios = crear_usuarios(cur, password)
            clientes = [usuarios[e] for _, e, r in USUARIOS if r == "Cliente"]

            print("Creando ventas ...")
            detalles = crear_ventas(cur, clientes)
            if not detalles:
                cur.execute("SELECT id FROM venta_detalle ORDER BY id")
                detalles = [f["id"] for f in cur.fetchall()]

            print("Creando devoluciones ...")
            crear_devoluciones(cur, detalles, usuarios)

            # Despues de las devoluciones historicas: estas ventas quedan libres
            # para registrar devoluciones nuevas dentro del plazo (RN-16).
            recientes = crear_ventas_recientes(cur, clientes)
            print(f"Ventas recientes dentro del plazo de devolucion: {recientes} nuevas.")

            if "--rehacer-lote" in sys.argv:
                retiradas = retirar_lote_problematico(cur)
                print(f"Lote problematico retirado ({retiradas} devoluciones) para rehacerlo.")
            problematico = crear_lote_problematico(cur, usuarios, clientes)
            if problematico:
                print(f"Lote problematico {LOTE_PROBLEMATICO}: {problematico} ventas con series y devoluciones.")

            actualizadas = backfill_fecha_cierre(cur)
            if actualizadas:
                print(f"  fecha_cierre completada en {actualizadas} devoluciones existentes.")
        conn.commit()

    print("\nDatos de demostracion listos.")
    anunciar_password(password, generada)


def anunciar_password(password, generada):
    print()
    for nombre, email, rol in USUARIOS:
        print(f"  {rol:<38} {email}")
    print()
    print(f"  Contrasena de todas las cuentas: {password}")
    if generada:
        print()
        print("  Se genero al azar porque PASSWORD_DEMO no esta definida en el .env.")
        print("  Anotala: no vuelve a mostrarse. Para fijarla, agrega al .env de la VM")
        print(f"    PASSWORD_DEMO={password}")
        print("  y vuelve a ejecutar este script con --rotar.")
    print()
    print("  Nunca escribas esta contrasena en el repositorio.")


if __name__ == "__main__":
    main()
