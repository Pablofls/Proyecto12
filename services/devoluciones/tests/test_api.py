"""Pruebas unitarias de la API: seguridad, contratos y validacion.

Cubren lo que se resuelve antes de tocar PostgreSQL, con un Redis en memoria.
El flujo con datos reales esta en test_integracion.py.
"""
import os
import time
import unittest
import uuid

import jwt

os.environ.setdefault("JWT_SECRET", "x" * 48)

import app as servicio  # noqa: E402
from shared import infra, seguridad, xsd  # noqa: E402

CONTRATOS_COMUNES = os.path.join(os.path.dirname(xsd.__file__), "contratos")


class RedisFalso:
    def __init__(self):
        self.datos = {}

    def exists(self, k):
        return int(k in self.datos)

    def incr(self, k):
        self.datos[k] = int(self.datos.get(k, 0)) + 1
        return self.datos[k]

    def expire(self, k, seg):
        return True

    def ttl(self, k):
        return 60


class PruebaApi(unittest.TestCase):
    def setUp(self):
        self.redis = RedisFalso()
        self._originales = []
        for modulo, nombre, valor in [
            (seguridad, "get_redis", lambda: self.redis),
            (infra, "get_redis", lambda: self.redis),
            # Si algo intentara llegar a la base, la prueba debe fallar.
            (servicio, "consultar", self._sin_base),
            (servicio, "ejecutar", self._sin_base),
        ]:
            self._originales.append((modulo, nombre, getattr(modulo, nombre)))
            setattr(modulo, nombre, valor)
        self.cliente = servicio.create_app().test_client()

    def tearDown(self):
        for modulo, nombre, valor in self._originales:
            setattr(modulo, nombre, valor)

    @staticmethod
    def _sin_base(*a, **k):
        raise AssertionError("La peticion no debia llegar a PostgreSQL")

    def token(self, rol, usuario_id=7):
        """JWT igual al que emite auth, con su sesion activa en Redis."""
        sid = uuid.uuid4().hex
        self.redis.datos[seguridad.clave_sesion(sid)] = "1"
        ahora = int(time.time())
        return jwt.encode({"iss": seguridad.EMISOR, "sub": str(usuario_id),
                           "rol": rol, "nombre": "Prueba", "sid": sid,
                           "jti": uuid.uuid4().hex, "typ": "access",
                           "iat": ahora, "exp": ahora + 600},
                          os.environ["JWT_SECRET"], algorithm="HS256")

    def headers(self, rol, xml=False):
        tipo = "application/xml" if xml else "application/json"
        return {"Authorization": f"Bearer {self.token(rol)}",
                "Content-Type": tipo, "Accept": tipo}

    # -- autenticacion y autorizacion ---------------------------------------- #
    def test_sin_token_responde_401(self):
        resp = self.cliente.get("/api/v1/devoluciones")
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.get_json()["error"]["tipo"], "no_autenticado")

    def test_token_revocado_responde_401(self):
        h = self.headers(seguridad.CLIENTE)
        claims = jwt.decode(h["Authorization"][7:], options={"verify_signature": False})
        self.redis.datos[seguridad.clave_revocado(claims["jti"])] = "1"
        resp = self.cliente.get("/api/v1/devoluciones", headers=h)
        self.assertEqual(resp.get_json()["error"]["tipo"], "token_revocado")

    def test_cliente_no_puede_resolver(self):
        resp = self.cliente.patch("/api/v1/devoluciones/1/resolucion",
                                  headers=self.headers(seguridad.CLIENTE),
                                  json={"decision": "autorizar"})
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.get_json()["error"]["detalles"]["roles_permitidos"],
                         [seguridad.ANALISTA])

    def test_inspector_no_puede_registrar(self):
        resp = self.cliente.post("/api/v1/devoluciones",
                                 headers=self.headers(seguridad.INSPECTOR), json={})
        self.assertEqual(resp.status_code, 403)

    def test_analista_no_puede_cancelar(self):
        resp = self.cliente.delete("/api/v1/devoluciones/1",
                                   headers=self.headers(seguridad.ANALISTA))
        self.assertEqual(resp.status_code, 403)

    # -- validacion y contratos ---------------------------------------------- #
    def test_registro_con_datos_invalidos(self):
        resp = self.cliente.post("/api/v1/devoluciones",
                                 headers=self.headers(seguridad.CLIENTE),
                                 json={"venta_detalle_id": "x", "descripcion_problema": "roto"})
        self.assertEqual(resp.status_code, 400)
        campos = {d["campo"] for d in resp.get_json()["error"]["detalles"]}
        self.assertEqual(campos, {"venta_detalle_id", "motivo_id", "descripcion_problema"})

    def test_resolucion_rechazo_sin_justificacion(self):
        resp = self.cliente.patch("/api/v1/devoluciones/1/resolucion",
                                  headers=self.headers(seguridad.ANALISTA),
                                  json={"decision": "rechazar"})
        self.assertEqual(resp.status_code, 400)

    def test_xml_que_no_cumple_xsd(self):
        resp = self.cliente.patch(
            "/api/v1/devoluciones/1/resolucion",
            headers=self.headers(seguridad.ANALISTA, xml=True),
            data="<resolucion><decision>aprobar</decision></resolucion>")
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"<tipo>xml_no_cumple_xsd</tipo>", resp.data)
        self.assertEqual(xsd.errores(resp.data, os.path.join(CONTRATOS_COMUNES,
                                                             "error.xsd")), [])

    def test_xml_de_registro_incompleto(self):
        resp = self.cliente.post(
            "/api/v1/devoluciones", headers=self.headers(seguridad.CLIENTE, xml=True),
            data="<devolucion><motivo_id>1</motivo_id></devolucion>")
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"xml_no_cumple_xsd", resp.data)

    def test_filtro_de_estado_invalido(self):
        resp = self.cliente.get("/api/v1/devoluciones?estado=perdida",
                                headers=self.headers(seguridad.ANALISTA))
        self.assertEqual(resp.status_code, 400)

    def test_paginacion_invalida(self):
        resp = self.cliente.get("/api/v1/devoluciones?por_pagina=500",
                                headers=self.headers(seguridad.ANALISTA))
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.get_json()["error"]["detalles"][0]["campo"], "por_pagina")

    def test_rate_limit_de_registro(self):
        h = self.headers(seguridad.CLIENTE)
        for _ in range(servicio.CREAR_POR_MINUTO):
            self.cliente.post("/api/v1/devoluciones", headers=h, json={})
        resp = self.cliente.post("/api/v1/devoluciones", headers=h, json={})
        self.assertEqual(resp.status_code, 429)

    def test_contratos_publicados(self):
        for nombre in ("devolucion_nueva.xsd", "devolucion_edicion.xsd",
                       "resolucion.xsd", "devolucion_creada.xsd", "error.xsd"):
            self.assertEqual(self.cliente.get(f"/contratos/{nombre}").status_code, 200)


if __name__ == "__main__":
    unittest.main()
