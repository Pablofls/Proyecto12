"""Fixture de contexto de la suite E2E (RNF-28).

Una sola vez por corrida: libera el rate limit de login, inicia sesion con un
usuario de cada rol (leidos de la base, contrasena de PASSWORD_DEMO), elige una
linea de venta refrigerada con unidades disponibles y, al terminar, borra lo
creado y cierra las sesiones.

Solo corre con INTEGRACION=1 dentro de la red del compose (ver docs/PRUEBAS.md).
"""
import os

import pytest

from . import cliente as c

ROLES = (c.CLIENTE, c.ANALISTA, c.COORDINADOR, c.ENCARGADO_CENTRO, c.INSPECTOR,
         c.ENCARGADO_REEMBOLSOS, c.ADMINISTRADOR)


def pytest_collection_modifyitems(config, items):
    if os.environ.get("INTEGRACION") == "1":
        return
    saltar = pytest.mark.skip(reason="Solo en la VM: INTEGRACION=1 y el entorno levantado")
    for item in items:
        if "tests/e2e" in str(item.fspath).replace(os.sep, "/"):
            item.add_marker(saltar)


class Contexto:
    """Estado compartido entre pasos: tokens, ids y lo que hay que limpiar."""

    def __init__(self):
        self.tokens = {}
        self.emails = {}
        self.creadas = []  # ids de devoluciones creadas por la suite
        self.sesiones_a_cerrar = []

    def h(self, rol):
        return self.tokens[rol]

    def registrar_devolucion(self, dev_id):
        self.creadas.append(dev_id)


@pytest.fixture(scope="session")
def ctx():
    if os.environ.get("INTEGRACION") != "1":
        pytest.skip("Solo en la VM: INTEGRACION=1")
    x = Contexto()
    c.liberar_limite_login()

    x.linea = c.sql("""
        SELECT vd.id, v.folio_venta, v.id AS venta_id, u.email, p.id AS producto_id,
               vd.cantidad - COALESCE((
                   SELECT SUM(d.cantidad_devuelta) FROM devoluciones d
                    WHERE d.venta_detalle_id = vd.id AND d.eliminado_en IS NULL
                      AND d.estado <> 'rechazada'), 0) AS disponible
          FROM venta_detalle vd
          JOIN ventas v    ON v.id = vd.venta_id
          JOIN usuarios u  ON u.id = v.cliente_id
          JOIN lotes l     ON l.id = vd.lote_id
          JOIN productos p ON p.id = l.producto_id
         WHERE v.eliminado_en IS NULL AND p.clasificacion_temperatura = 'refrigerado'
         ORDER BY disponible DESC, vd.id
         LIMIT 1""", uno=True)
    if not x.linea or x.linea["disponible"] < 2:
        pytest.skip("No hay una linea de venta refrigerada con al menos 2 unidades disponibles")
    x.motivo = c.sql("SELECT id FROM motivos WHERE activo ORDER BY id LIMIT 1",
                     uno=True)["id"]

    x.emails[c.CLIENTE] = x.linea["email"]
    x.otro_cliente = c.email_de_rol(c.CLIENTE, excluir=(x.linea["email"],))
    for rol in ROLES[1:]:
        x.emails[rol] = c.email_de_rol(rol)
        assert x.emails[rol], f"No hay un usuario activo con rol {rol}: corre seed_demo"
    assert x.otro_cliente, "Se necesita un segundo cliente para probar el aislamiento"

    # 7 roles + el segundo cliente = 8 logins, debajo del limite de 10/min.
    for rol in ROLES:
        x.tokens[rol] = c.iniciar_sesion(x.emails[rol])
    x.token_otro_cliente = c.iniciar_sesion(x.otro_cliente)

    yield x

    for token in list(x.tokens.values()) + [x.token_otro_cliente]:
        try:
            c.cerrar_sesion(token)
        except Exception:  # noqa: BLE001 - puede estar cerrada por una prueba
            pass
    c.borrar_devoluciones(x.creadas)
