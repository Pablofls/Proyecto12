"""Integracion real de analisis y auditoria: proyeccion a MongoDB, Pareto con cache en Redis y auditoria.

Sin dobles: el token sale del servicio auth real por HTTP, la peticion va al
contenedor de analisis-auditoria y el efecto se verifica en MongoDB, Redis y PostgreSQL. Las filas que crea
la prueba se borran al terminar. Solo corre en la VM:

    docker compose run --rm -e INTEGRACION=1 analisis-auditoria python -m pytest -v tests/test_integracion.py

Trazabilidad: RNF-28, RF-23, RF-24, RF-25, RN-09, RN-11, RNF-23.
"""
import json
import os
import unittest
import urllib.error
import urllib.request

import psycopg2
import psycopg2.extras

from shared import mongo
from shared.infra import get_redis

AUTH_URL = os.environ.get("AUTH_URL", "http://auth:8000")
SERVICIO_URL = os.environ.get("ANALISIS_URL", "http://analisis-auditoria:8000")
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
class IntegracionAnalisis(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analista = _login("Analista de Devoluciones")
        cls.cliente = _login("Cliente")

    @classmethod
    def tearDownClass(cls):
        _logout(cls.analista)
        _logout(cls.cliente)

    def test_sincronizar_proyecta_postgres_en_mongo_sin_modificar_postgres(self):
        antes = _sql("SELECT COUNT(*) AS n, COALESCE(MAX(id), 0) AS m FROM devoluciones "
                     "WHERE eliminado_en IS NULL", uno=True)
        codigo, resp = _http(SERVICIO_URL, "POST", PREFIJO + "/analisis/sincronizar",
                             token=self.analista)
        self.assertEqual(codigo, 200, resp)
        self.assertEqual(resp["casos_sincronizados"], antes["n"])
        vigentes = mongo.get_mongo().resultados_analisis.count_documents(
            {"tipo_analisis": "snapshot_devolucion", "vigente": True})
        self.assertEqual(vigentes, antes["n"])
        despues = _sql("SELECT COUNT(*) AS n, COALESCE(MAX(id), 0) AS m FROM devoluciones "
                       "WHERE eliminado_en IS NULL", uno=True)
        self.assertEqual(antes, despues)  # solo lectura sobre PostgreSQL

    def test_pareto_primero_calcula_y_luego_sale_del_cache_con_ttl(self):
        codigo, _ = _http(SERVICIO_URL, "POST", PREFIJO + "/analisis/sincronizar", token=self.analista)
        self.assertEqual(codigo, 200)  # sube la version del cache: la primera lectura es miss
        ruta = PREFIJO + "/analisis/pareto?dimension=motivo&medida=frecuencia"
        _, primera = _http(SERVICIO_URL, "GET", ruta, token=self.analista)
        _, segunda = _http(SERVICIO_URL, "GET", ruta, token=self.analista)
        self.assertEqual(primera["cache"], "miss")
        self.assertEqual(segunda["cache"], "hit")
        self.assertEqual(primera["categorias"], segunda["categorias"])
        r = get_redis()
        claves = list(r.scan_iter("devoluciones:cache:causas:*"))
        self.assertTrue(claves)
        self.assertTrue(all(0 < r.ttl(k) <= 600 for k in claves))
        # El calculo se conserva en MongoDB para trazabilidad.
        self.assertTrue(mongo.get_mongo().resultados_analisis.find_one({"tipo_analisis": "pareto"}))
        if primera["categorias"]:
            acumulados = [c["porcentaje_acumulado"] for c in primera["categorias"]]
            self.assertEqual(acumulados, sorted(acumulados))
            self.assertAlmostEqual(acumulados[-1], 100.0, places=1)

    def test_clasificar_motivo_solo_sugiere(self):  # RN-11
        antes = _sql("SELECT COUNT(*) AS n FROM devoluciones", uno=True)["n"]
        codigo, resp = _http(SERVICIO_URL, "POST", PREFIJO + "/analisis/clasificar-motivo",
                             {"descripcion": "El producto llego caducado y con mal olor"}, self.cliente)
        self.assertEqual(codigo, 200)
        self.assertTrue(resp["requiere_confirmacion"])
        self.assertEqual(antes, _sql("SELECT COUNT(*) AS n FROM devoluciones", uno=True)["n"])

    def test_auditoria_y_eventos_solo_para_analista_o_admin(self):
        codigo, cuerpo = _http(SERVICIO_URL, "GET", PREFIJO + "/auditoria?por_pagina=5",
                               token=self.analista)
        self.assertEqual(codigo, 200)
        self.assertEqual(cuerpo["paginacion"]["total"],
                         _sql("SELECT COUNT(*) AS n FROM bitacora", uno=True)["n"])
        codigo, _ = _http(SERVICIO_URL, "GET", PREFIJO + "/auditoria", token=self.cliente)
        self.assertEqual(codigo, 403)
        codigo, _ = _http(SERVICIO_URL, "GET", PREFIJO + "/analisis/eventos", token=self.cliente)
        self.assertEqual(codigo, 403)


if __name__ == "__main__":
    unittest.main()
