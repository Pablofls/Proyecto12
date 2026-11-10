"""Pruebas unitarias del tercer parcial: roles de campo, sucursal en el token y
autorizacion de operaciones criticas (RF-04, RN-13, RNF-09, RNF-12).

Mismos dobles en memoria que test_auth.py. La operacion critica se ejecuta en
una ruta de prueba que usa shared.seguridad.exigir_autorizacion_operacion, igual
que lo haran reembolsos, disposicion y causa raiz.
"""
import os
import unittest

import jwt

os.environ.setdefault("JWT_SECRET", "x" * 48)

import app as servicio  # noqa: E402
from shared import infra, seguridad, xsd  # noqa: E402
from shared.respuestas import responder  # noqa: E402
from tests.dobles import PASSWORD, BaseFalsa, RedisFalso  # noqa: E402

AUTORIZAR = "/api/v1/auth/autorizar-operacion"


def _claims(token):
    return jwt.decode(token, options={"verify_signature": False})


class PruebaOperaciones(unittest.TestCase):
    def setUp(self):
        self.redis, self.base = RedisFalso(), BaseFalsa()
        self._originales = []
        for modulo, nombre, valor in [
            (servicio, "get_redis", lambda: self.redis),
            (seguridad, "get_redis", lambda: self.redis),
            (infra, "get_redis", lambda: self.redis),
            (servicio, "consultar", self.base.consultar),
            (servicio, "ejecutar", self.base.ejecutar),
            (servicio, "registrar_bitacora", lambda *a, **k: None),
        ]:
            self._originales.append((modulo, nombre, getattr(modulo, nombre)))
            setattr(modulo, nombre, valor)
        app = servicio.create_app()

        # Rutas de prueba: una operacion critica y un endpoint sin roles.
        @app.post("/prueba/disposicion/<int:devolucion_id>")
        @seguridad.requiere_jwt(seguridad.ANALISTA, seguridad.SUPERVISOR)
        def _disposicion(devolucion_id):
            seguridad.exigir_autorizacion_operacion("aprobar_disposicion", devolucion_id)
            return responder({"ok": True})

        @app.get("/prueba/sin-roles")
        @seguridad.requiere_jwt()
        def _sin_roles():
            return responder({"ok": True})

        self.cliente = app.test_client()

    def tearDown(self):
        for modulo, nombre, valor in self._originales:
            setattr(modulo, nombre, valor)

    # -- utilidades --------------------------------------------------------- #
    def token(self, email="analista@demo.com"):
        resp = self.cliente.post("/api/v1/auth/login",
                                 json={"email": email, "password": PASSWORD})
        self.assertEqual(resp.status_code, 200)
        return resp.get_json()["access_token"]

    @staticmethod
    def bearer(token, **extra):
        return {"Authorization": f"Bearer {token}", **extra}

    def autorizar(self, token, operacion="aprobar_disposicion", recurso="57",
                  password=PASSWORD):
        return self.cliente.post(AUTORIZAR, headers=self.bearer(token), json={
            "operacion": operacion, "recurso_id": recurso, "password": password})

    def ejecutar_disposicion(self, token, devolucion_id, permiso=None):
        extra = {seguridad.HEADER_OPERACION: permiso} if permiso else {}
        return self.cliente.post(f"/prueba/disposicion/{devolucion_id}",
                                 headers=self.bearer(token, **extra))

    # -- roles y sucursal --------------------------------------------------- #
    def test_token_lleva_la_sucursal(self):
        self.assertEqual(_claims(self.token("almacen@demo.com"))["tienda_id"], 2)
        self.assertIsNone(_claims(self.token())["tienda_id"])

    def test_refresh_conserva_la_sucursal(self):
        resp = self.cliente.post("/api/v1/auth/login", json={
            "email": "almacen@demo.com", "password": PASSWORD})
        refresh = resp.get_json()["refresh_token"]
        nuevo = self.cliente.post("/api/v1/auth/refresh",
                                  json={"refresh_token": refresh}).get_json()
        self.assertEqual(_claims(nuevo["access_token"])["tienda_id"], 2)

    def test_rol_de_campo_no_entra_a_endpoint_sin_roles(self):
        """requiere_jwt() sin roles solo acepta los 7 roles originales."""
        resp = self.cliente.get("/prueba/sin-roles",
                                headers=self.bearer(self.token("almacen@demo.com")))
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.get_json()["error"]["tipo"], "sin_permiso")
        resp = self.cliente.get("/prueba/sin-roles", headers=self.bearer(self.token()))
        self.assertEqual(resp.status_code, 200)

    def test_rol_de_campo_puede_consultar_y_cerrar_su_sesion(self):
        t = self.token("almacen@demo.com")
        resp = self.cliente.get("/api/v1/auth/sesion", headers=self.bearer(t))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["usuario"]["tienda_id"], 2)
        self.assertEqual(self.cliente.post("/api/v1/auth/logout",
                                           headers=self.bearer(t)).status_code, 200)

    # -- operaciones criticas ----------------------------------------------- #
    def test_permiso_de_un_solo_uso(self):
        t = self.token()
        resp = self.autorizar(t)
        self.assertEqual(resp.status_code, 201)
        permiso = resp.get_json()["token_operacion"]
        claims = _claims(permiso)
        self.assertEqual((claims["typ"], claims["op"], claims["recurso"]),
                         ("operacion", "aprobar_disposicion", "57"))
        clave = seguridad.clave_operacion(claims["jti"])
        self.assertTrue(0 < self.redis.ttl(clave) <= 300)
        self.assertEqual(self.ejecutar_disposicion(t, 57, permiso).status_code, 200)
        self.assertFalse(self.redis.exists(clave))
        resp = self.ejecutar_disposicion(t, 57, permiso)
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.get_json()["error"]["tipo"], "autorizacion_operacion_usada")

    def test_sin_permiso_la_operacion_se_rechaza(self):
        resp = self.ejecutar_disposicion(self.token(), 57)
        self.assertEqual(resp.status_code, 403)
        error = resp.get_json()["error"]
        self.assertEqual(error["tipo"], "autorizacion_operacion_requerida")
        self.assertEqual(error["detalles"]["header"], seguridad.HEADER_OPERACION)

    def test_permiso_de_otro_registro_no_sirve(self):
        t = self.token()
        permiso = self.autorizar(t, recurso="57").get_json()["token_operacion"]
        resp = self.ejecutar_disposicion(t, 58, permiso)
        self.assertEqual(resp.get_json()["error"]["tipo"], "autorizacion_operacion_invalida")

    def test_permiso_de_otra_sesion_no_sirve(self):
        permiso = self.autorizar(self.token()).get_json()["token_operacion"]
        otra_sesion = self.token()  # mismo usuario, otro login
        resp = self.ejecutar_disposicion(otra_sesion, 57, permiso)
        self.assertEqual(resp.get_json()["error"]["tipo"], "autorizacion_operacion_invalida")

    def test_permiso_falsificado_no_sirve(self):
        t = self.token()
        claims = _claims(self.autorizar(t).get_json()["token_operacion"])
        falso = jwt.encode(claims, "otro-secreto-" * 4, algorithm="HS256")
        resp = self.ejecutar_disposicion(t, 57, falso)
        self.assertEqual(resp.get_json()["error"]["tipo"], "autorizacion_operacion_invalida")

    def test_contrasena_incorrecta_cuenta_como_intento_fallido(self):
        resp = self.autorizar(self.token(), password="mala")
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.get_json()["error"]["tipo"], "credenciales_invalidas")
        self.assertEqual(self.redis.datos["devoluciones:intentos:analista@demo.com"], 1)

    def test_rol_sin_derecho_a_la_operacion(self):
        resp = self.autorizar(self.token(), operacion="aprobar_reembolso")
        self.assertEqual(resp.status_code, 403)
        self.assertEqual(resp.get_json()["error"]["detalles"]["roles_permitidos"],
                         [seguridad.ENCARGADO_REEMBOLSOS])
        resp = self.autorizar(self.token("reembolsos@demo.com"),
                              operacion="aprobar_reembolso")
        self.assertEqual(resp.status_code, 201)

    def test_validacion_de_campos(self):
        resp = self.autorizar(self.token(), operacion="borrar_todo",
                              recurso="57; DROP TABLE", password="")
        self.assertEqual(resp.status_code, 400)
        campos = {d["campo"] for d in resp.get_json()["error"]["detalles"]}
        self.assertEqual(campos, {"operacion", "recurso_id", "password"})

    def test_autorizacion_en_xml_cumple_contrato(self):
        t = self.token()
        cabeceras = self.bearer(t, **{"Content-Type": "application/xml",
                                      "Accept": "application/xml"})
        resp = self.cliente.post(AUTORIZAR, headers=cabeceras, data=(
            "<autorizacion><operacion>aprobar_disposicion</operacion>"
            f"<recurso_id>57</recurso_id><password>{PASSWORD}</password></autorizacion>"))
        self.assertEqual(resp.status_code, 201)
        self.assertIn(b"<token_operacion>", resp.data)
        resp = self.cliente.post(AUTORIZAR, headers=cabeceras, data=(
            "<autorizacion><operacion>aprobar</operacion>"
            "<recurso_id>57</recurso_id><password>x</password></autorizacion>"))
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"<tipo>xml_no_cumple_xsd</tipo>", resp.data)

    def test_contrato_publicado(self):
        resp = self.cliente.get("/contratos/autorizar_operacion.xsd")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"cerrar_investigacion", resp.data)

    def test_respuestas_con_sucursal_cumplen_xsd(self):
        resp = self.cliente.post("/api/v1/auth/login", headers={"Accept": "application/xml"},
                                 json={"email": "almacen@demo.com", "password": PASSWORD})
        self.assertIn(b"<tienda_id>2</tienda_id>", resp.data)
        self.assertEqual(xsd.errores(resp.data, os.path.join(servicio.CONTRATOS, "tokens.xsd")), [])


if __name__ == "__main__":
    unittest.main()
