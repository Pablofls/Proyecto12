"""Pruebas de integracion: auth + devoluciones + PostgreSQL + MongoDB + Redis.

No usan dobles. Los tokens se obtienen del servicio auth real por HTTP y las
operaciones se verifican directamente en PostgreSQL y MongoDB. Al terminar se
borran las devoluciones de prueba y se cierran las sesiones.

Solo corren en la VM, con el entorno levantado:
    docker compose run --rm -e INTEGRACION=1 devoluciones python -m pytest -v tests/test_integracion.py

Trazabilidad: RF-07, RF-10, RF-11, RF-29, RN-01, RNF-08, RNF-09, RNF-23.
"""
import json
import os
import unittest
import urllib.error
import urllib.request

import psycopg2
import psycopg2.extras

import app as servicio
from shared import mongo

AUTH_URL = os.environ.get("AUTH_URL", "http://auth:8000")
ANALISTA = "josue.analista@demo.mx"
DESCRIPCION = "Prueba de integracion: el empaque llego roto."


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


def _auth(ruta, cuerpo=None, token=None):
    """Llamada HTTP real al contenedor de auth."""
    peticion = urllib.request.Request(
        AUTH_URL + ruta, method="POST",
        data=json.dumps(cuerpo or {}).encode(),
        headers={"Content-Type": "application/json",
                 **({"Authorization": f"Bearer {token}"} if token else {})})
    with urllib.request.urlopen(peticion, timeout=10) as resp:
        return json.loads(resp.read())


@unittest.skipUnless(os.environ.get("INTEGRACION") == "1",
                     "Solo en la VM: INTEGRACION=1 y el entorno levantado")
class PruebaIntegracion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Una linea de venta con algo por devolver y su dueno.
        cls.linea = _sql(
            """
            SELECT vd.id, u.email,
                   vd.cantidad - COALESCE((
                       SELECT SUM(d.cantidad_devuelta) FROM devoluciones d
                        WHERE d.venta_detalle_id = vd.id AND d.eliminado_en IS NULL
                          AND d.estado <> 'rechazada'), 0) AS disponible
              FROM venta_detalle vd
              JOIN ventas v   ON v.id = vd.venta_id
              JOIN usuarios u ON u.id = v.cliente_id
             WHERE v.eliminado_en IS NULL
             ORDER BY disponible DESC, vd.id
             LIMIT 1
            """, uno=True)
        if not cls.linea or cls.linea["disponible"] < 2:
            raise unittest.SkipTest("No hay lineas de venta con al menos 2 unidades disponibles")
        cls.otro_cliente = _sql(
            """
            SELECT u.email FROM usuarios u JOIN roles r ON r.id = u.rol_id
             WHERE r.nombre = 'Cliente' AND u.email <> %s AND u.eliminado_en IS NULL
             LIMIT 1
            """, (cls.linea["email"],), uno=True)["email"]
        cls.motivo = _sql("SELECT id FROM motivos WHERE activo ORDER BY id LIMIT 1",
                          uno=True)["id"]

        password = os.environ["PASSWORD_DEMO"]
        cls.tokens = {email: _auth("/api/v1/auth/login",
                                   {"email": email, "password": password})["access_token"]
                      for email in (cls.linea["email"], cls.otro_cliente, ANALISTA)}
        cls.creadas = []
        cls.cliente = servicio.create_app().test_client()

    @classmethod
    def tearDownClass(cls):
        if cls.creadas:
            ids = tuple(cls.creadas)
            _sql("DELETE FROM notificaciones WHERE devolucion_id IN %s", (ids,))
            _sql("DELETE FROM devoluciones WHERE id IN %s", (ids,))
            mongo.get_mongo().eventos.delete_many({"datos.devolucion_id": {"$in": list(ids)}})
        for token in cls.tokens.values():
            try:
                _auth("/api/v1/auth/logout", token=token)
            except urllib.error.HTTPError:
                pass  # ya cerrada por la prueba de revocacion

    # -- utilidades --------------------------------------------------------- #
    def h(self, email):
        return {"Authorization": f"Bearer {self.tokens[email]}"}

    def registrar(self, cantidad=1):
        resp = self.cliente.post("/api/v1/devoluciones", headers=self.h(self.linea["email"]),
                                 json={"venta_detalle_id": self.linea["id"],
                                       "motivo_id": self.motivo,
                                       "descripcion_problema": DESCRIPCION,
                                       "cantidad_devuelta": cantidad})
        if resp.status_code == 201:
            self.creadas.append(resp.get_json()["id"])
        return resp

    # -- flujo completo ------------------------------------------------------ #
    def test_1_flujo_registro_revision_y_autorizacion(self):
        dueno, analista = self.linea["email"], ANALISTA

        # 1. El cliente registra: 201, fila en PostgreSQL y evento en MongoDB.
        resp = self.registrar()
        self.assertEqual(resp.status_code, 201, resp.get_json())
        dev = resp.get_json()
        self.assertEqual(resp.headers["Location"], f"/api/v1/devoluciones/{dev['id']}")
        fila = _sql("SELECT estado FROM devoluciones WHERE id = %s", (dev["id"],), uno=True)
        self.assertEqual(fila["estado"], "solicitada")
        evento = mongo.get_mongo().eventos.find_one(
            {"datos.devolucion_id": dev["id"], "tipo": "devolucion_registrada"})
        self.assertIsNotNone(evento)
        self.assertEqual(evento["servicio"], "devoluciones")

        # 2. Otro cliente no puede verla y queda constancia en la bitacora.
        resp = self.cliente.get(f"/api/v1/devoluciones/{dev['id']}",
                                headers=self.h(self.otro_cliente))
        self.assertEqual(resp.status_code, 403)
        self.assertTrue(_sql("SELECT 1 FROM bitacora WHERE accion = 'acceso_denegado' "
                             "AND entidad_id = %s", (dev["id"],), uno=True))

        # 3. Regla de negocio: no se puede devolver mas de lo comprado.
        resp = self.registrar(cantidad=self.linea["disponible"] + 5)
        self.assertEqual(resp.status_code, 409)
        self.assertEqual(resp.get_json()["error"]["tipo"], "cantidad_excedida")

        # 4. El analista pide informacion y el cliente corrige con PUT.
        resp = self.cliente.patch(f"/api/v1/devoluciones/{dev['id']}/resolucion",
                                  headers=self.h(analista),
                                  json={"decision": "informacion",
                                        "justificacion": "Describe el sello."})
        self.assertEqual(resp.get_json()["estado"], "en_revision")
        resp = self.cliente.put(f"/api/v1/devoluciones/{dev['id']}", headers=self.h(dueno),
                                json={"motivo_id": self.motivo, "cantidad_devuelta": 1,
                                      "descripcion_problema": DESCRIPCION + " Sello abierto."})
        self.assertEqual(resp.status_code, 200)
        self.assertTrue(resp.get_json()["descripcion_problema"].endswith("Sello abierto."))

        # 5. Ya revisada, el cliente no puede cancelarla.
        resp = self.cliente.delete(f"/api/v1/devoluciones/{dev['id']}", headers=self.h(dueno))
        self.assertEqual(resp.status_code, 409)

        # 6. El analista autoriza: estado, notificacion al cliente (RF-29).
        resp = self.cliente.patch(f"/api/v1/devoluciones/{dev['id']}/resolucion",
                                  headers=self.h(analista), json={"decision": "autorizar"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["estado"], "autorizada")
        notas = _sql("SELECT tipo FROM notificaciones WHERE devolucion_id = %s ORDER BY id",
                     (dev["id"],))
        self.assertEqual([n["tipo"] for n in notas], ["solicitud_informacion", "autorizacion"])

        # 7. Ya no se puede resolver otra vez.
        resp = self.cliente.patch(f"/api/v1/devoluciones/{dev['id']}/resolucion",
                                  headers=self.h(analista), json={"decision": "rechazar",
                                                                  "justificacion": "x"})
        self.assertEqual(resp.status_code, 409)

        # 8. El expediente junta bitacora (PostgreSQL) y eventos (MongoDB).
        exp = self.cliente.get(f"/api/v1/devoluciones/{dev['id']}",
                               headers=self.h(analista)).get_json()
        acciones = {h["accion"] for h in exp["historial"]}
        self.assertTrue({"alta_devolucion", "solicitud_informacion",
                         "actualizacion_solicitud", "autorizacion"} <= acciones)
        tipos = [e["tipo"] for e in exp["eventos"]]
        self.assertEqual(tipos[0], "devolucion_autorizacion")  # el mas reciente primero
        self.assertIn("devolucion_registrada", tipos)

    def test_2_cancelacion_logica(self):
        dueno = self.linea["email"]
        dev = self.registrar().get_json()
        resp = self.cliente.delete(f"/api/v1/devoluciones/{dev['id']}", headers=self.h(dueno))
        self.assertEqual(resp.status_code, 200)
        # La fila se conserva para auditoria (RNF-30) pero la API ya no la muestra.
        fila = _sql("SELECT eliminado_en FROM devoluciones WHERE id = %s", (dev["id"],), uno=True)
        self.assertIsNotNone(fila["eliminado_en"])
        resp = self.cliente.get(f"/api/v1/devoluciones/{dev['id']}", headers=self.h(dueno))
        self.assertEqual(resp.status_code, 404)

    def test_3_listado_del_cliente_solo_trae_lo_suyo(self):
        dueno = self.linea["email"]
        resp = self.cliente.get("/api/v1/devoluciones?por_pagina=100", headers=self.h(dueno))
        self.assertEqual(resp.status_code, 200)
        cuerpo = resp.get_json()
        nombres = {d["cliente"] for d in cuerpo["datos"]}
        self.assertLessEqual(len(nombres), 1)
        self.assertEqual(cuerpo["paginacion"]["pagina"], 1)

    def test_4_logout_en_auth_revoca_el_token_en_devoluciones(self):
        """Comunicacion entre servicios por Redis: auth revoca y devoluciones
        rechaza el mismo token de inmediato (RNF-08)."""
        token = self.tokens[self.otro_cliente]
        self.assertEqual(self.cliente.get("/api/v1/devoluciones",
                                          headers={"Authorization": f"Bearer {token}"}
                                          ).status_code, 200)
        _auth("/api/v1/auth/logout", token=token)
        resp = self.cliente.get("/api/v1/devoluciones",
                                headers={"Authorization": f"Bearer {token}"})
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.get_json()["error"]["tipo"], "token_revocado")


if __name__ == "__main__":
    unittest.main()
