"""Pruebas unitarias de los endpoints de sincronizacion que no tocan la base."""
import os
import time
import unittest
import uuid

import jwt

os.environ.setdefault("JWT_SECRET", "x" * 48)
import app as servicio  # noqa: E402
from shared import infra, seguridad  # noqa: E402

URL = "/api/v1/sincronizacion"


class RedisFalso:
    def __init__(self):
        self.datos = {}

    def exists(self, k):
        return int(k in self.datos)

    def incr(self, k):
        self.datos[k] = int(self.datos.get(k, 0)) + 1
        return self.datos[k]

    def expire(self, k, s):
        return True

    def ttl(self, k):
        return 60


class PruebaSincronizacionApi(unittest.TestCase):
    def setUp(self):
        self.r = RedisFalso()
        self.originales = (seguridad.get_redis, infra.get_redis)
        seguridad.get_redis = infra.get_redis = lambda: self.r
        self.cliente = servicio.create_app().test_client()

    def tearDown(self):
        seguridad.get_redis, infra.get_redis = self.originales

    def token(self, rol):
        sid = uuid.uuid4().hex
        self.r.datos[seguridad.clave_sesion(sid)] = "1"
        ahora = int(time.time())
        return jwt.encode({"iss": seguridad.EMISOR, "sub": "7", "rol": rol, "nombre": "Prueba",
                           "sid": sid, "jti": uuid.uuid4().hex, "typ": "access",
                           "iat": ahora, "exp": ahora + 600},
                          os.environ["JWT_SECRET"], algorithm="HS256")

    def cabeceras(self, rol, **extra):
        return {"Authorization": "Bearer " + self.token(rol), **extra}

    def test_sin_token(self):
        self.assertEqual(self.cliente.post(URL + "/operaciones", json={}).status_code, 401)

    def test_cliente_no_sincroniza(self):
        r = self.cliente.post(URL + "/operaciones", json={}, headers=self.cabeceras(seguridad.CLIENTE))
        self.assertEqual(r.status_code, 403)

    def test_catalogo_de_tipos_por_rol(self):
        r = self.cliente.get(URL + "/tipos", headers=self.cabeceras(seguridad.RECOLECTOR))
        self.assertEqual(r.status_code, 200)
        permitidos = {t["tipo"]: t["permitido_para_tu_rol"] for t in r.get_json()["tipos"]}
        self.assertTrue(permitidos["estado_recoleccion"])
        self.assertFalse(permitidos["recepcion"])
        self.assertIn("aprobar_reembolso", r.get_json()["solo_en_linea"])

    def test_dispositivo_invalido(self):
        r = self.cliente.post(URL + "/operaciones", headers=self.cabeceras(seguridad.RECOLECTOR),
                              json={"dispositivo_id": "tel <1>", "operaciones": [{}]})
        self.assertEqual(r.status_code, 400)

    def test_lote_vacio_o_demasiado_grande(self):
        for ops in ([], [{}] * 51, "nada"):
            r = self.cliente.post(URL + "/operaciones", headers=self.cabeceras(seguridad.RECOLECTOR),
                                  json={"dispositivo_id": "tel-1", "operaciones": ops})
            self.assertEqual(r.status_code, 400)

    def test_xml_que_no_cumple_el_contrato(self):
        r = self.cliente.post(URL + "/operaciones",
                              headers=self.cabeceras(seguridad.RECOLECTOR,
                                                     **{"Content-Type": "application/xml",
                                                        "Accept": "application/xml"}),
                              data="<sincronizacion><dispositivo_id>tel-1</dispositivo_id></sincronizacion>")
        self.assertEqual(r.status_code, 400)
        self.assertIn(b"xml_no_cumple_xsd", r.data)

    def test_detalle_con_id_mal_formado_es_404(self):
        r = self.cliente.get(URL + "/operaciones/123", headers=self.cabeceras(seguridad.RECOLECTOR))
        self.assertEqual(r.status_code, 404)

    def test_limite_de_envios(self):
        self.r.datos["devoluciones:limite:usuario7:sincronizacion"] = 30
        r = self.cliente.post(URL + "/operaciones", headers=self.cabeceras(seguridad.RECOLECTOR),
                              json={"dispositivo_id": "tel-1", "operaciones": [{}]})
        self.assertEqual(r.status_code, 429)


if __name__ == "__main__":
    unittest.main()
