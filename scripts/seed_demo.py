"""Carga datos de demostracion: usuarios, ventas y devoluciones en varios estados.

Se ejecuta DESPUES de las migraciones y del seed de catalogos:

    docker compose exec app python scripts/migrate.py
    docker compose exec -T postgres psql -U $POSTGRES_USER -d $POSTGRES_DB < db/seeds/001_catalogos.sql
    docker compose exec app python scripts/seed_demo.py

Es idempotente: si los usuarios de demostracion ya existen, no hace nada.
Las contrasenas se generan con el mismo hash que usa la aplicacion (RNF-07);
son credenciales de demostracion y no deben usarse fuera de la VM del proyecto.
"""
import os
import random
from datetime import date, timedelta

import psycopg2
import psycopg2.extras
from werkzeug.security import generate_password_hash

PASSWORD_DEMO = "Devoluciones2026"

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
]


def conectar():
    return psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "postgres"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        dbname=os.environ["POSTGRES_DB"],
        user=os.environ["POSTGRES_USER"],
        password=os.environ["POSTGRES_PASSWORD"],
        cursor_factory=psycopg2.extras.RealDictCursor,
    )


def crear_usuarios(cur):
    hash_demo = generate_password_hash(PASSWORD_DEMO)
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

    cur.execute("SELECT id, ruta_id FROM rutas LIMIT 1")
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
                "INSERT INTO costos (devolucion_id, etapa, monto) VALUES (%s, 'recoleccion', %s)",
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


def main():
    random.seed(12)  # Datos reproducibles entre integrantes del equipo.
    with conectar() as conn:
        with conn.cursor() as cur:
            print("Creando usuarios de demostracion ...")
            usuarios = crear_usuarios(cur)
            clientes = [usuarios[e] for _, e, r in USUARIOS if r == "Cliente"]

            print("Creando ventas ...")
            detalles = crear_ventas(cur, clientes)
            if not detalles:
                cur.execute("SELECT id FROM venta_detalle ORDER BY id")
                detalles = [f["id"] for f in cur.fetchall()]

            print("Creando devoluciones ...")
            crear_devoluciones(cur, detalles, usuarios)
        conn.commit()

    print("\nDatos de demostracion listos.")
    print(f"Contrasena para todas las cuentas de demostracion: {PASSWORD_DEMO}")
    for nombre, email, rol in USUARIOS:
        print(f"  {rol:<38} {email}")


if __name__ == "__main__":
    main()
