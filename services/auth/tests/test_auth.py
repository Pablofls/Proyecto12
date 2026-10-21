"""Pruebas unitarias del servicio auth.

Se ejecutan dentro del contenedor:
    docker compose run --rm auth python -m pytest -v
"""
import os
import time
import unittest
from datetime import datetime, timedelta, timezone

import jwt

os.environ.setdefault("JWT_SECRET", "x" * 48)

import app as servicio  # noqa: E402
from shared import infra, seguridad, xsd  # noqa: E402
from tests.dobles import PASSWORD, BaseFalsa, RedisFalso  # noqa: E402

CONTRATOS = servicio.CONTRATOS
CONTRATOS_COMUNES = os.path.join(os.path.dirname(xsd.__file__), "contratos")


class PruebaAuth(unittest.TestCase):
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
        self.cliente = servicio.create_app().test_client()

    def tearDown(self):
        for modulo, nombre, valor in self._originales:
            setattr(modulo, nombre, valor)

    # -- utilidades --------------------------------------------------------- #
    def login(self, email="analista@demo.com", password=PASSWORD):
        return self.cliente.post("/api/v1/auth/login",
                                 json={"email": email, "password": password})

    def token(self, email="analista@demo.com"):
        return self.login(email).get_json()

    @staticmethod
    def bearer(token):
        return {"Authorization": f"Bearer {token}"}

    # -- login -------------------------------------------------------------- #
    def test_login_correcto_emite_tokens_y_sesion(self):
        resp = self.login()
        self.assertEqual(resp.status_code, 200)
        cuerpo = resp.get_json()
        self.assertEqual(cuerpo["token_type"], "Bearer")
        claims = jwt.decode(cuerpo["access_token"], os.environ["JWT_SECRET"],
                            algorithms=["HS256"], issuer="devoluciones-auth")
        self.assertEqual(claims["rol"], "Analista de Devoluciones")
        self.assertTrue(self.redis.exists(f"devoluciones:sesion_api:{claims['sid']}"))
        self.assertIn("X-Correlation-ID", resp.headers)

    def test_login_en_xml(self):
        resp = self.cliente.post(
            "/api/v1/auth/login",
            data=f"<login><email>analista@demo.com</email>"
                 f"<password>{PASSWORD}</password></login>",
            headers={"Content-Type": "application/xml",
                     "Accept": "application/xml"})
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.mimetype, "application/xml")
        self.assertIn(b"<access_token>", resp.data)

    def test_password_incorrecta_responde_401_generico(self):
        resp = self.login(password="mala")
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.get_json()["error"]["tipo"], "credenciales_invalidas")
        self.assertEqual(self.redis.datos["devoluciones:intentos:analista@demo.com"], 1)

    def test_bloqueo_tras_intentos_fallidos(self):
        for _ in range(5):
            self.login(password="mala")
        resp = self.login()  # aun con la contrasena correcta
        self.assertEqual(resp.status_code, 423)
        self.assertEqual(resp.get_json()["error"]["tipo"], "cuenta_bloqueada")
        self.assertTrue(any("bloqueado_hasta" in s for s in self.base.sentencias))

    def test_validacion_de_campos(self):
        resp = self.login(email="no-es-correo", password="")
        self.assertEqual(resp.status_code, 400)
        campos = {d["campo"] for d in resp.get_json()["error"]["detalles"]}
        self.assertEqual(campos, {"email", "password"})

    def test_xml_mal_formado(self):
        resp = self.cliente.post("/api/v1/auth/login", data="<login><email>",
                                 content_type="application/xml")
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.get_json()["error"]["tipo"], "xml_invalido")

    def test_formato_no_soportado(self):
        resp = self.cliente.post("/api/v1/auth/login", data="hola",
                                 content_type="text/plain")
        self.assertEqual(resp.status_code, 415)

    def test_rate_limit_de_login(self):
        for _ in range(10):
            self.login(password="mala")
        resp = self.login()
        self.assertEqual(resp.status_code, 429)
        self.assertIn("Retry-After", resp.headers)

    # -- tokens y sesiones -------------------------------------------------- #
    def test_sin_token_responde_401(self):
        resp = self.cliente.get("/api/v1/auth/sesion")
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.get_json()["error"]["tipo"], "no_autenticado")

    def test_sesion_con_token_valido(self):
        t = self.token()["access_token"]
        resp = self.cliente.get("/api/v1/auth/sesion", headers=self.bearer(t))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.get_json()["usuario"]["id"], 3)

    def test_logout_revoca_token(self):
        t = self.token()["access_token"]
        self.assertEqual(self.cliente.post("/api/v1/auth/logout",
                                           headers=self.bearer(t)).status_code, 200)
        resp = self.cliente.get("/api/v1/auth/sesion", headers=self.bearer(t))
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.get_json()["error"]["tipo"], "token_revocado")

    def test_refresh_funciona_y_muere_con_logout(self):
        tokens = self.token()
        cuerpo = {"refresh_token": tokens["refresh_token"]}
        self.assertEqual(self.cliente.post("/api/v1/auth/refresh",
                                           json=cuerpo).status_code, 200)
        self.cliente.post("/api/v1/auth/logout",
                          headers=self.bearer(tokens["access_token"]))
        resp = self.cliente.post("/api/v1/auth/refresh", json=cuerpo)
        self.assertEqual(resp.status_code, 401)
        self.assertEqual(resp.get_json()["error"]["tipo"], "sesion_inactiva")

    def test_access_token_no_sirve_como_refresh(self):
        t = self.token()["access_token"]
        resp = self.cliente.post("/api/v1/auth/refresh", json={"refresh_token": t})
        self.assertEqual(resp.status_code, 401)

    def test_token_con_firma_falsa(self):
        falso = jwt.encode({"sub": "1", "rol": "Administrador", "sid": "a",
                            "jti": "b", "typ": "access", "iss": "devoluciones-auth",
                            "iat": int(time.time()), "exp": int(time.time()) + 600},
                           "otro-secreto-" * 4, algorithm="HS256")
        resp = self.cliente.get("/api/v1/auth/sesion", headers=self.bearer(falso))
        self.assertEqual(resp.get_json()["error"]["tipo"], "token_invalido")

    def test_token_expirado(self):
        ahora = datetime.now(timezone.utc)
        viejo = jwt.encode({"sub": "3", "rol": "Cliente", "sid": "a", "jti": "b",
                            "typ": "access", "iss": "devoluciones-auth",
                            "iat": ahora - timedelta(hours=1),
                            "exp": ahora - timedelta(minutes=1)},
                           os.environ["JWT_SECRET"], algorithm="HS256")
        resp = self.cliente.get("/api/v1/auth/sesion", headers=self.bearer(viejo))
        self.assertEqual(resp.get_json()["error"]["tipo"], "token_expirado")

    def test_administrador_cierra_sesiones_de_otro(self):
        analista = self.token()["access_token"]
        admin = self.token("admin@demo.com")["access_token"]
        resp = self.cliente.delete("/api/v1/auth/usuarios/3/sesiones",
                                   headers=self.bearer(admin))
        self.assertEqual(resp.get_json()["sesiones_cerradas"], 1)
        resp = self.cliente.get("/api/v1/auth/sesion", headers=self.bearer(analista))
        self.assertEqual(resp.get_json()["error"]["tipo"], "sesion_inactiva")

    def test_rol_sin_permiso_responde_403(self):
        analista = self.token()["access_token"]
        resp = self.cliente.delete("/api/v1/auth/usuarios/1/sesiones",
                                   headers=self.bearer(analista))
        self.assertEqual(resp.status_code, 403)

    def test_usuario_inexistente_responde_404(self):
        admin = self.token("admin@demo.com")["access_token"]
        resp = self.cliente.delete("/api/v1/auth/usuarios/999/sesiones",
                                   headers=self.bearer(admin))
        self.assertEqual(resp.status_code, 404)

    def test_redis_caido_niega_acceso(self):
        t = self.token()["access_token"]
        self.redis.caido = True
        resp = self.cliente.get("/api/v1/auth/sesion", headers=self.bearer(t))
        self.assertEqual(resp.status_code, 503)

    def test_error_en_xml(self):
        resp = self.cliente.get("/api/v1/auth/sesion",
                                headers={"Accept": "application/xml"})
        self.assertEqual(resp.mimetype, "application/xml")
        self.assertIn(b"<tipo>no_autenticado</tipo>", resp.data)

    # -- contratos XSD ------------------------------------------------------ #
    def xml(self, ruta, cuerpo, token=None):
        headers = {"Content-Type": "application/xml", "Accept": "application/xml"}
        if token:
            headers.update(self.bearer(token))
        return self.cliente.post(ruta, data=cuerpo, headers=headers)

    def cumple(self, resp, nombre):
        ruta = os.path.join(CONTRATOS if nombre != "error.xsd" else
                            CONTRATOS_COMUNES, nombre)
        self.assertEqual(xsd.errores(resp.data, ruta), [])

    def test_xml_que_no_cumple_xsd(self):
        resp = self.xml("/api/v1/auth/login",
                        "<login><correo>analista@demo.com</correo>"
                        "<password>x</password></login>")
        self.assertEqual(resp.status_code, 400)
        self.assertIn(b"<tipo>xml_no_cumple_xsd</tipo>", resp.data)
        self.cumple(resp, "error.xsd")

    def test_respuesta_de_login_cumple_xsd(self):
        resp = self.xml("/api/v1/auth/login",
                        f"<login><password>{PASSWORD}</password>"
                        "<email>analista@demo.com</email></login>")
        self.assertEqual(resp.status_code, 200)
        self.cumple(resp, "tokens.xsd")

    def test_refresh_en_xml_cumple_xsd(self):
        refresh = self.token()["refresh_token"]
        resp = self.xml("/api/v1/auth/refresh",
                        f"<refresh><refresh_token>{refresh}</refresh_token></refresh>")
        self.assertEqual(resp.status_code, 200)
        self.cumple(resp, "tokens.xsd")

    def test_respuesta_de_sesion_cumple_xsd(self):
        t = self.token()["access_token"]
        resp = self.cliente.get("/api/v1/auth/sesion", headers={
            **self.bearer(t), "Accept": "application/xml"})
        self.cumple(resp, "sesion.xsd")

    def test_errores_en_xml_cumplen_xsd(self):
        sin_token = self.cliente.get("/api/v1/auth/sesion",
                                     headers={"Accept": "application/xml"})
        con_detalles = self.xml("/api/v1/auth/refresh", "<refresh></refresh>")
        self.cumple(sin_token, "error.xsd")
        self.cumple(con_detalles, "error.xsd")

    def test_contratos_publicados(self):
        resp = self.cliente.get("/contratos/login.xsd")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"<xs:schema", resp.data)
        self.assertEqual(self.cliente.get("/contratos/error.xsd").status_code, 200)
        self.assertEqual(self.cliente.get("/contratos/nada.xsd").status_code, 404)

    def test_ruta_inexistente_formato_estandar(self):
        resp = self.cliente.get("/api/v1/auth/nada")
        self.assertEqual(resp.status_code, 404)
        self.assertEqual(resp.get_json()["error"]["tipo"], "no_encontrado")


if __name__ == "__main__":
    unittest.main()
