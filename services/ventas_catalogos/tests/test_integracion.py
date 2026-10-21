"""Integracion real de ventas y catalogos: consulta de ventas por dueno y altas de catalogo en PostgreSQL.

Sin dobles: el token sale del servicio auth real por HTTP, la peticion va al
contenedor de ventas-catalogos y el efecto se verifica en PostgreSQL. Las filas que crea
la prueba se borran al terminar. Solo corre en la VM:

    docker compose run --rm -e INTEGRACION=1 ventas-catalogos python -m pytest -v tests/test_integracion.py

Trazabilidad: RNF-28, RF-04, RF-05, RF-06, RN-13, RNF-09.
"""
import json
import os
import unittest
import urllib.error
import urllib.request

import psycopg2
import psycopg2.extras

AUTH_URL = os.environ.get("AUTH_URL", "http://auth:8000")
SERVICIO_URL = os.environ.get("VENTAS_URL", "http://ventas-catalogos:8000")
PREFIJO = "/api/v1"


def _sql(sentencia, params=(), uno=False):
    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "postgres"),
        dbname=os.environ.get("POSTGRES_DB", "devoluciones"),
        user=os.environ.get("POSTGRES_USER", "devoluciones_app"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
        cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        with conn, conn.cursor() as cur:
            cur.execute(sentencia, params)
            if cur.description is None:
                return None
            return cur.fetchone() if uno else cur.fetchall()
    finally:
        conn.close()


def _http(base, metodo, ruta, cuerpo=None, token=None):
    """Peticion HTTP real; devuelve (codigo, cuerpo_json). No lanza por 4xx."""
    cabeceras = {"Content-Type": "application/json"}
    if token:
        cabeceras["Authorization"] = f"Bearer {token}"
    peticion = urllib.request.Request(
        base + ruta, method=metodo, headers=cabeceras,
        data=json.dumps(cuerpo).encode() if cuerpo is not None else None)
    try:
        with urllib.request.urlopen(peticion, timeout=15) as resp:
            return resp.status, json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as exc:
        crudo = exc.read()
        try:
            return exc.code, json.loads(crudo)
        except ValueError:
            return exc.code, None


def _email_de_rol(rol):
    fila = _sql("""SELECT u.email FROM usuarios u JOIN roles r ON r.id = u.rol_id
                    WHERE r.nombre = %s AND u.estado = 'activo' AND u.eliminado_en IS NULL
                    ORDER BY u.id LIMIT 1""", (rol,), uno=True)
    if not fila:
        raise unittest.SkipTest(f"No hay usuario activo con rol {rol} (corre seed_demo)")
    return fila["email"]


def _login(rol):
    """Login real; la contrasena viene de PASSWORD_DEMO, nunca del repositorio."""
    codigo, cuerpo = _http(AUTH_URL, "POST", "/api/v1/auth/login",
                           {"email": _email_de_rol(rol), "password": os.environ["PASSWORD_DEMO"]})
    if codigo != 200:
        raise AssertionError(f"login de {rol} respondio {codigo}")
    return cuerpo["access_token"]


def _logout(token):
    _http(AUTH_URL, "POST", "/api/v1/auth/logout", token=token)


def _linea_disponible(refrigerado=None):
    """Una linea de venta con al menos 1 unidad sin devolver."""
    filtro = "" if refrigerado is None else (
        "AND p.clasificacion_temperatura = " + ("'refrigerado'" if refrigerado else "'no_refrigerado'"))
    fila = _sql(f"""
        SELECT vd.id FROM venta_detalle vd
          JOIN ventas v ON v.id = vd.venta_id
          JOIN lotes l ON l.id = vd.lote_id JOIN productos p ON p.id = l.producto_id
         WHERE v.eliminado_en IS NULL {filtro}
           AND vd.cantidad - COALESCE((SELECT SUM(d.cantidad_devuelta) FROM devoluciones d
                WHERE d.venta_detalle_id = vd.id AND d.eliminado_en IS NULL
                  AND d.estado <> 'rechazada'), 0) >= 1
         ORDER BY vd.id LIMIT 1""", uno=True)
    if not fila:
        raise unittest.SkipTest("No hay una linea de venta con unidades por devolver")
    return fila["id"]


def _sembrar_devolucion(estado, refrigerado=None):
    """Inserta por SQL una devolucion en el estado pedido (el folio lo pone la
    base, RN-02). Asi cada servicio se prueba aislado de los demas."""
    motivo = _sql("SELECT id FROM motivos WHERE activo ORDER BY id LIMIT 1", uno=True)["id"]
    return _sql("""INSERT INTO devoluciones (venta_detalle_id, motivo_id, descripcion_problema,
                                             cantidad_devuelta, estado)
                   VALUES (%s, %s, 'Prueba de integracion del servicio.', 1, %s)
                   RETURNING id, folio_devolucion""",
                (_linea_disponible(refrigerado), motivo, estado), uno=True)


def _borrar_devoluciones(ids):
    if not ids:
        return
    ids = tuple(ids)
    for paso in (
        "DELETE FROM notificaciones WHERE devolucion_id IN %s",
        "DELETE FROM evidencias WHERE devolucion_id IN %s",
        "DELETE FROM inventario_recuperado WHERE disposicion_id IN "
        "(SELECT id FROM disposiciones WHERE devolucion_id IN %s)",
        "DELETE FROM disposiciones WHERE devolucion_id IN %s",
        "DELETE FROM inspecciones_ref WHERE devolucion_id IN %s",
        "DELETE FROM recepciones WHERE devolucion_id IN %s",
        "DELETE FROM recolecciones WHERE devolucion_id IN %s",
        "DELETE FROM costos WHERE devolucion_id IN %s",
        "DELETE FROM reembolsos WHERE devolucion_id IN %s",
        "DELETE FROM devoluciones WHERE id IN %s",
    ):
        try:
            _sql(paso, (ids,))
        except Exception:  # noqa: BLE001 - limpieza de mejor esfuerzo
            pass

SKIP = unittest.skipUnless(os.environ.get("INTEGRACION") == "1",
                         "Solo en la VM: INTEGRACION=1 y el entorno levantado")


@SKIP
class IntegracionVentasCatalogos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.admin = _login("Administrador")
        cls.analista = _login("Analista de Devoluciones")
        cls.cliente_email = _email_de_rol("Cliente")
        codigo, cuerpo = _http(AUTH_URL, "POST", "/api/v1/auth/login",
                               {"email": cls.cliente_email, "password": os.environ["PASSWORD_DEMO"]})
        assert codigo == 200
        cls.cliente = cuerpo["access_token"]
        cls.motivos = []

    @classmethod
    def tearDownClass(cls):
        if cls.motivos:
            try:
                _sql("DELETE FROM motivos WHERE id IN %s", (tuple(cls.motivos),))
            except Exception:  # noqa: BLE001 - limpieza de mejor esfuerzo
                pass
        for token in (cls.admin, cls.analista, cls.cliente):
            _logout(token)

    def test_cliente_solo_ve_sus_ventas_con_paginacion(self):
        codigo, cuerpo = _http(SERVICIO_URL, "GET", PREFIJO + "/ventas?por_pagina=100",
                               token=self.cliente)
        self.assertEqual(codigo, 200)
        propias = _sql("""SELECT COUNT(*) AS n FROM ventas v JOIN usuarios u ON u.id = v.cliente_id
                           WHERE u.email = %s AND v.eliminado_en IS NULL""",
                       (self.cliente_email,), uno=True)["n"]
        self.assertEqual(cuerpo["paginacion"]["total"], propias)
        self.assertEqual({v["cliente_id"] for v in cuerpo["datos"]}, {
            _sql("SELECT id FROM usuarios WHERE email = %s", (self.cliente_email,), uno=True)["id"]
        } if propias else set())

    def test_cliente_no_abre_la_venta_de_otro(self):
        ajena = _sql("""SELECT v.id FROM ventas v JOIN usuarios u ON u.id = v.cliente_id
                         WHERE u.email <> %s AND v.eliminado_en IS NULL LIMIT 1""",
                     (self.cliente_email,), uno=True)
        if not ajena:
            self.skipTest("No hay ventas de otros clientes")
        codigo, _ = _http(SERVICIO_URL, "GET", f"{PREFIJO}/ventas/{ajena['id']}", token=self.cliente)
        self.assertEqual(codigo, 403)

    def test_alta_edicion_y_baja_logica_de_catalogo(self):
        nombre = "Motivo de prueba de integracion"
        codigo, alta = _http(SERVICIO_URL, "POST", PREFIJO + "/catalogos/motivos",
                             {"nombre": nombre, "descripcion": "Se borra al terminar"}, self.admin)
        self.assertEqual(codigo, 201, alta)
        self.motivos.append(alta["id"])
        fila = _sql("SELECT nombre, activo FROM motivos WHERE id = %s", (alta["id"],), uno=True)
        self.assertEqual((fila["nombre"], fila["activo"]), (nombre, True))

        codigo, _ = _http(SERVICIO_URL, "PUT", f"{PREFIJO}/catalogos/motivos/{alta['id']}",
                          {"nombre": nombre + " v2"}, self.admin)
        self.assertEqual(codigo, 200)
        self.assertEqual(_sql("SELECT nombre FROM motivos WHERE id = %s", (alta["id"],),
                              uno=True)["nombre"], nombre + " v2")

        # DELETE desactiva, no borra (RNF-30): la fila sigue para la auditoria.
        codigo, _ = _http(SERVICIO_URL, "DELETE", f"{PREFIJO}/catalogos/motivos/{alta['id']}",
                          token=self.admin)
        self.assertEqual(codigo, 200)
        self.assertFalse(_sql("SELECT activo FROM motivos WHERE id = %s", (alta["id"],),
                              uno=True)["activo"])
        self.assertTrue(_sql("SELECT 1 FROM bitacora WHERE accion = 'alta_catalogo' "
                             "AND entidad_id = %s AND entidad = 'motivos'", (alta["id"],), uno=True))

    def test_catalogo_inexistente_y_rol_sin_permiso(self):
        codigo, _ = _http(SERVICIO_URL, "GET", PREFIJO + "/catalogos/no_existe", token=self.admin)
        self.assertEqual(codigo, 404)
        codigo, _ = _http(SERVICIO_URL, "POST", PREFIJO + "/catalogos/motivos",
                          {"nombre": "x"}, self.analista)
        self.assertEqual(codigo, 403)
        codigo, _ = _http(SERVICIO_URL, "GET", PREFIJO + "/catalogos/productos", token=self.cliente)
        self.assertEqual(codigo, 403)  # el cliente solo lee motivos


if __name__ == "__main__":
    unittest.main()
