"""Integracion real de inspecciones: inspeccion en MongoDB, referencia y disposicion en PostgreSQL.

Sin dobles: el token sale del servicio auth real por HTTP, la peticion va al
contenedor de inspecciones y el efecto se verifica en PostgreSQL y MongoDB. Las filas que crea
la prueba se borran al terminar. Solo corre en la VM:

    docker compose run --rm -e INTEGRACION=1 inspecciones python -m pytest -v tests/test_integracion.py

Trazabilidad: RNF-28, RF-16, RF-17, RF-18, RF-19, RN-05, RN-06, RN-07.
"""
import json
import os
import unittest
import urllib.error
import urllib.request

import psycopg2
import psycopg2.extras

from shared import mongo

AUTH_URL = os.environ.get("AUTH_URL", "http://auth:8000")
SERVICIO_URL = os.environ.get("INSPECCIONES_URL", "http://inspecciones:8000")
PREFIJO = "/api/v1/inspecciones"


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
class IntegracionInspecciones(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inspector = _login("Inspector")
        cls.analista = _login("Analista de Devoluciones")
        cls.centro = _login("Encargado del Centro de Devoluciones")
        cls.cliente = _login("Cliente")
        cls.ids = []

    @classmethod
    def tearDownClass(cls):
        if cls.ids:
            mongo.get_mongo().inspecciones.delete_many({"devolucion_id": {"$in": cls.ids}})
        _borrar_devoluciones(cls.ids)
        for token in (cls.inspector, cls.analista, cls.centro, cls.cliente):
            _logout(token)

    def _inspeccionar(self, dev_id, **extra):
        cuerpo = {"devolucion_id": dev_id, "estado_empaque": "Caja abierta",
                  "temperatura_recepcion": 4.0, "minutos_fuera_refrigeracion": 10,
                  "danos": False, "caducidad_vencida": False, "cadena_frio_rota": False}
        cuerpo.update(extra)
        return _http(SERVICIO_URL, "POST", PREFIJO, cuerpo, self.inspector)

    def test_inspeccion_apta_va_a_mongo_y_postgres_y_se_etiqueta(self):
        dev = _sembrar_devolucion("recibida", refrigerado=True)
        self.ids.append(dev["id"])
        codigo, resp = self._inspeccionar(dev["id"])
        self.assertEqual(codigo, 201, resp)
        doc = mongo.get_mongo().inspecciones.find_one({"devolucion_id": dev["id"]})
        self.assertIsNotNone(doc)  # detalle semiestructurado en MongoDB
        ref = _sql("SELECT mongo_doc_id, apto_para_inventario FROM inspecciones_ref "
                   "WHERE devolucion_id = %s", (dev["id"],), uno=True)
        self.assertEqual(ref["mongo_doc_id"], str(doc["_id"]))  # el enlace PG -> Mongo
        self.assertTrue(ref["apto_para_inventario"])

        # PATCH solo toca el detalle de MongoDB.
        codigo, _ = _http(SERVICIO_URL, "PATCH", f"{PREFIJO}/{dev['id']}",
                          {"observaciones": "Revisado de nuevo"}, self.inspector)
        self.assertEqual(codigo, 200)
        doc = mongo.get_mongo().inspecciones.find_one({"devolucion_id": dev["id"]})
        self.assertEqual(doc["observaciones"], "Revisado de nuevo")

        codigo, disp = _http(SERVICIO_URL, "POST", f"{PREFIJO}/{dev['id']}/disposicion",
                             {"destino": "inventario", "justificacion": "Apto"}, self.analista)
        self.assertEqual(codigo, 201, disp)
        codigo, inv = _http(SERVICIO_URL, "POST", f"{PREFIJO}/inventario/{disp['id']}/etiqueta",
                            None, self.centro)
        self.assertEqual(codigo, 201, inv)
        self.assertTrue(_sql("SELECT 1 FROM inventario_recuperado WHERE disposicion_id = %s",
                             (disp["id"],), uno=True))

    def test_refrigerado_con_cadena_rota_no_vuelve_a_inventario(self):  # RN-06, RN-07
        dev = _sembrar_devolucion("recibida", refrigerado=True)
        self.ids.append(dev["id"])
        codigo, resp = self._inspeccionar(dev["id"], cadena_frio_rota=True)
        self.assertEqual(codigo, 201)
        self.assertFalse(resp["apto_para_inventario"])
        codigo, resp = _http(SERVICIO_URL, "POST", f"{PREFIJO}/{dev['id']}/disposicion",
                             {"destino": "inventario"}, self.analista)
        self.assertEqual(codigo, 409)
        self.assertEqual(resp["error"]["tipo"], "no_apto_inventario")
        self.assertIsNone(_sql("SELECT 1 FROM disposiciones WHERE devolucion_id = %s",
                               (dev["id"],), uno=True))

    def test_refrigerado_exige_temperatura_y_tiempo(self):  # RN-05
        dev = _sembrar_devolucion("recibida", refrigerado=True)
        self.ids.append(dev["id"])
        codigo, _ = _http(SERVICIO_URL, "POST", PREFIJO,
                          {"devolucion_id": dev["id"], "estado_empaque": "Caja"}, self.inspector)
        self.assertEqual(codigo, 400)
        self.assertIsNone(mongo.get_mongo().inspecciones.find_one({"devolucion_id": dev["id"]}))

    def test_solo_se_inspecciona_lo_recibido(self):
        dev = _sembrar_devolucion("autorizada", refrigerado=True)
        self.ids.append(dev["id"])
        codigo, _ = self._inspeccionar(dev["id"])
        self.assertEqual(codigo, 409)

    def test_el_cliente_no_inspecciona(self):
        codigo, _ = _http(SERVICIO_URL, "POST", PREFIJO, {}, self.cliente)
        self.assertEqual(codigo, 403)


if __name__ == "__main__":
    unittest.main()
