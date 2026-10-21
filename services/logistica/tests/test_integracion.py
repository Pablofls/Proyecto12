"""Integracion real de logistica: recoleccion y recepcion sobre PostgreSQL.

Sin dobles: el token sale del servicio auth real por HTTP, la peticion va al
contenedor de logistica y el efecto se verifica en PostgreSQL. Las filas que crea
la prueba se borran al terminar. Solo corre en la VM:

    docker compose run --rm -e INTEGRACION=1 logistica python -m pytest -v tests/test_integracion.py

Trazabilidad: RNF-28, RF-12, RF-13, RF-14, RF-15, RN-08, RN-12.
"""
import json
import os
import unittest
import urllib.error
import urllib.request

import psycopg2
import psycopg2.extras

AUTH_URL = os.environ.get("AUTH_URL", "http://auth:8000")
SERVICIO_URL = os.environ.get("LOGISTICA_URL", "http://logistica:8000")
PREFIJO = "/api/v1/logistica"


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
class IntegracionLogistica(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.coord = _login("Coordinador de Logistica")
        cls.centro = _login("Encargado del Centro de Devoluciones")
        cls.cliente = _login("Cliente")
        cls.ids = []

    @classmethod
    def tearDownClass(cls):
        _borrar_devoluciones(cls.ids)
        for token in (cls.coord, cls.centro, cls.cliente):
            _logout(token)

    def test_programar_asignar_transitar_completar_y_recibir(self):
        dev = _sembrar_devolucion("autorizada")
        self.ids.append(dev["id"])
        ruta = _sql("SELECT id FROM rutas WHERE activo ORDER BY id LIMIT 1", uno=True)["id"]
        transp = _sql("SELECT id FROM transportistas WHERE activo ORDER BY id LIMIT 1", uno=True)["id"]
        manana = _sql("SELECT (CURRENT_DATE + 1)::text AS f", uno=True)["f"]

        codigo, rec = _http(SERVICIO_URL, "POST", PREFIJO + "/recolecciones", token=self.coord,
                            cuerpo={"devolucion_id": dev["id"], "fecha_programada": manana,
                                    "lugar": "Tienda de prueba"})
        self.assertEqual(codigo, 201, rec)
        fila = _sql("SELECT estado FROM recolecciones WHERE id = %s", (rec["id"],), uno=True)
        self.assertEqual(fila["estado"], "programada")
        self.assertEqual(_sql("SELECT estado FROM devoluciones WHERE id = %s", (dev["id"],),
                              uno=True)["estado"], "en_recoleccion")
        # Una recoleccion por devolucion.
        codigo, _ = _http(SERVICIO_URL, "POST", PREFIJO + "/recolecciones", token=self.coord,
                          cuerpo={"devolucion_id": dev["id"], "fecha_programada": manana,
                                  "lugar": "Otra"})
        self.assertEqual(codigo, 409)

        base = f"{PREFIJO}/recolecciones/{rec['id']}"
        codigo, _ = _http(SERVICIO_URL, "PATCH", base + "/asignacion", token=self.coord,
                          cuerpo={"ruta_id": ruta, "transportista_id": transp})
        self.assertEqual(codigo, 200)
        # No se puede saltar de asignada a completada.
        codigo, _ = _http(SERVICIO_URL, "PATCH", base + "/estado", token=self.coord,
                          cuerpo={"estado": "completada"})
        self.assertEqual(codigo, 409)
        for estado in ("en_transito", "completada"):
            codigo, _ = _http(SERVICIO_URL, "PATCH", base + "/estado", token=self.coord,
                              cuerpo={"estado": estado})
            self.assertEqual(codigo, 200)
        fila = _sql("SELECT estado, ruta_id, transportista_id FROM recolecciones WHERE id = %s",
                    (rec["id"],), uno=True)
        self.assertEqual((fila["estado"], fila["ruta_id"], fila["transportista_id"]),
                         ("completada", ruta, transp))

        codigo, _ = _http(SERVICIO_URL, "POST", PREFIJO + "/recepciones", token=self.centro,
                          cuerpo={"devolucion_id": dev["id"], "coincide_expediente": True})
        self.assertEqual(codigo, 201)
        self.assertEqual(_sql("SELECT estado FROM devoluciones WHERE id = %s", (dev["id"],),
                              uno=True)["estado"], "recibida")
        self.assertTrue(_sql("SELECT 1 FROM bitacora WHERE accion = 'recepcion_confirmada' "
                             "AND entidad_id = %s", (dev["id"],), uno=True))

    def test_no_se_programa_una_devolucion_sin_autorizar(self):
        dev = _sembrar_devolucion("solicitada")
        self.ids.append(dev["id"])
        manana = _sql("SELECT (CURRENT_DATE + 1)::text AS f", uno=True)["f"]
        codigo, cuerpo = _http(SERVICIO_URL, "POST", PREFIJO + "/recolecciones", token=self.coord,
                               cuerpo={"devolucion_id": dev["id"], "fecha_programada": manana,
                                       "lugar": "Tienda"})
        self.assertEqual(codigo, 409)
        self.assertEqual(cuerpo["error"]["tipo"], "estado_no_permite")
        self.assertIsNone(_sql("SELECT 1 FROM recolecciones WHERE devolucion_id = %s",
                               (dev["id"],), uno=True))

    def test_el_cliente_no_puede_programar(self):
        codigo, _ = _http(SERVICIO_URL, "POST", PREFIJO + "/recolecciones", token=self.cliente,
                          cuerpo={})
        self.assertEqual(codigo, 403)


if __name__ == "__main__":
    unittest.main()
