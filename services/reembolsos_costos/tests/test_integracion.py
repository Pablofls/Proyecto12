"""Integracion real de reembolsos y costos: reembolso unico con lock de Redis y costos en PostgreSQL.

Sin dobles: el token sale del servicio auth real por HTTP, la peticion va al
contenedor de reembolsos-costos y el efecto se verifica en PostgreSQL y Redis. Las filas que crea
la prueba se borran al terminar. Solo corre en la VM:

    docker compose run --rm -e INTEGRACION=1 reembolsos-costos python -m pytest -v tests/test_integracion.py

Trazabilidad: RNF-28, RF-20, RF-21, RF-27, RN-03, RN-04, RNF-13.
"""
import json
import os
import unittest
import urllib.error
import urllib.request

import psycopg2
import psycopg2.extras

from shared.infra import get_redis

AUTH_URL = os.environ.get("AUTH_URL", "http://auth:8000")
SERVICIO_URL = os.environ.get("REEMBOLSOS_URL", "http://reembolsos-costos:8000")
PREFIJO = "/api/v1/reembolsos-costos"


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
class IntegracionReembolsos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.encargado = _login("Encargado de Reembolsos")
        cls.coord = _login("Coordinador de Logistica")
        cls.analista = _login("Analista de Devoluciones")
        cls.cliente = _login("Cliente")
        cls.ids = []

    @classmethod
    def tearDownClass(cls):
        _borrar_devoluciones(cls.ids)
        for token in (cls.encargado, cls.coord, cls.analista, cls.cliente):
            _logout(token)

    def _valor(self, dev_id):
        return float(_sql("""SELECT vd.precio_unitario * d.cantidad_devuelta AS v
                               FROM devoluciones d JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
                              WHERE d.id = %s""", (dev_id,), uno=True)["v"])

    def test_un_solo_reembolso_por_devolucion(self):  # RN-03
        dev = _sembrar_devolucion("resuelta")
        self.ids.append(dev["id"])
        cuerpo = {"devolucion_id": dev["id"], "estado": "aprobado", "metodo": "transferencia",
                  "monto": self._valor(dev["id"])}
        codigo, resp = _http(SERVICIO_URL, "POST", PREFIJO + "/reembolsos", cuerpo, self.encargado)
        self.assertEqual(codigo, 201, resp)
        self.assertEqual(_sql("SELECT COUNT(*) AS n FROM reembolsos WHERE devolucion_id = %s",
                              (dev["id"],), uno=True)["n"], 1)
        # Aprobar un reembolso de una devolucion ya resuelta la cierra y avisa al cliente.
        self.assertEqual(_sql("SELECT estado FROM devoluciones WHERE id = %s", (dev["id"],),
                              uno=True)["estado"], "cerrada")
        self.assertTrue(_sql("SELECT 1 FROM notificaciones WHERE devolucion_id = %s "
                             "AND tipo = 'reembolso_aprobado'", (dev["id"],), uno=True))
        codigo, resp = _http(SERVICIO_URL, "POST", PREFIJO + "/reembolsos", cuerpo, self.encargado)
        self.assertEqual(codigo, 409)
        self.assertEqual(resp["error"]["tipo"], "reembolso_duplicado")
        self.assertEqual(_sql("SELECT COUNT(*) AS n FROM reembolsos WHERE devolucion_id = %s",
                              (dev["id"],), uno=True)["n"], 1)

    def test_lock_de_redis_bloquea_la_resolucion_concurrente(self):
        dev = _sembrar_devolucion("autorizada")
        self.ids.append(dev["id"])
        llave = f"devoluciones:lock:reembolso:{dev['id']}"
        r = get_redis()
        r.set(llave, "otro-proceso", ex=30)
        try:
            codigo, resp = _http(SERVICIO_URL, "POST", PREFIJO + "/reembolsos",
                                 {"devolucion_id": dev["id"], "estado": "aprobado",
                                  "metodo": "tarjeta", "monto": 1}, self.encargado)
            self.assertEqual(codigo, 409)
            self.assertEqual(resp["error"]["tipo"], "reembolso_en_proceso")
            self.assertEqual(r.get(llave), "otro-proceso")  # no libero el lock ajeno
        finally:
            r.delete(llave)
        self.assertIsNone(_sql("SELECT 1 FROM reembolsos WHERE devolucion_id = %s",
                               (dev["id"],), uno=True))

    def test_no_reembolsa_si_no_esta_autorizada_ni_mas_del_valor(self):  # RN-04
        sin = _sembrar_devolucion("solicitada")
        self.ids.append(sin["id"])
        codigo, resp = _http(SERVICIO_URL, "POST", PREFIJO + "/reembolsos",
                             {"devolucion_id": sin["id"], "estado": "aprobado",
                              "metodo": "tarjeta", "monto": 1}, self.encargado)
        self.assertEqual(codigo, 409)
        self.assertEqual(resp["error"]["tipo"], "estado_no_permite")
        aut = _sembrar_devolucion("autorizada")
        self.ids.append(aut["id"])
        codigo, resp = _http(SERVICIO_URL, "POST", PREFIJO + "/reembolsos",
                             {"devolucion_id": aut["id"], "estado": "aprobado",
                              "metodo": "tarjeta", "monto": self._valor(aut["id"]) + 1000},
                             self.encargado)
        self.assertEqual(codigo, 409)
        self.assertEqual(resp["error"]["tipo"], "monto_excedido")
        self.assertIsNone(_sql("SELECT 1 FROM reembolsos WHERE devolucion_id IN (%s, %s)",
                               (sin["id"], aut["id"]), uno=True))

    def test_costos_por_etapa_y_total(self):  # RF-27
        dev = _sembrar_devolucion("autorizada")
        self.ids.append(dev["id"])
        codigo, _ = _http(SERVICIO_URL, "POST", PREFIJO + "/costos",
                          {"devolucion_id": dev["id"], "etapa": "transporte", "monto": 100}, self.coord)
        self.assertEqual(codigo, 201)
        # Cada rol solo registra sus etapas: el coordinador no puede cargar un reembolso.
        codigo, _ = _http(SERVICIO_URL, "POST", PREFIJO + "/costos",
                          {"devolucion_id": dev["id"], "etapa": "reembolso", "monto": 5}, self.coord)
        self.assertEqual(codigo, 403)
        codigo, _ = _http(SERVICIO_URL, "POST", PREFIJO + "/costos",
                          {"devolucion_id": dev["id"], "etapa": "otros", "monto": 20.5}, self.analista)
        self.assertEqual(codigo, 201)
        codigo, resumen = _http(SERVICIO_URL, "GET", f"{PREFIJO}/costos/{dev['id']}",
                                token=self.analista)
        self.assertEqual(codigo, 200)
        self.assertAlmostEqual(resumen["costo_total"], 120.5)
        self.assertEqual(float(_sql("SELECT SUM(monto) AS s FROM costos WHERE devolucion_id = %s",
                                    (dev["id"],), uno=True)["s"]), 120.5)

    def test_el_cliente_no_reembolsa(self):
        codigo, _ = _http(SERVICIO_URL, "POST", PREFIJO + "/reembolsos", {}, self.cliente)
        self.assertEqual(codigo, 403)


if __name__ == "__main__":
    unittest.main()
