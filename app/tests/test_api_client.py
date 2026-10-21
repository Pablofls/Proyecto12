import io
import json
import unittest
from unittest.mock import patch
from urllib.error import HTTPError, URLError

from flask import Flask, session

from app import api_client
from app.blueprints.auth import _abrir_sesion_distribuida


class Respuesta:
    def __init__(self, datos, codigo=200):
        self.datos = datos
        self.status = codigo

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return json.dumps(self.datos).encode()


class PruebaClienteApi(unittest.TestCase):
    def setUp(self):
        self.app = Flask(__name__)
        self.app.secret_key = "prueba"
        self.app.config.update(
            USE_MICROSERVICES=True,
            MICROSERVICE_TIMEOUT=1,
            SERVICE_URLS={"auth": "http://auth:8000"},
        )

    @patch("app.api_client.urllib.request.urlopen")
    def test_login_guarda_tokens_solo_en_sesion_servidor(self, abrir):
        abrir.return_value = Respuesta({
            "usuario": {"id": 9, "nombre": "Pablo", "rol": "Administrador"},
            "access_token": "access",
            "refresh_token": "refresh",
            "expires_in": 900,
        })
        with self.app.test_request_context("/login", method="POST"):
            _abrir_sesion_distribuida("pablo@demo.mx", "secreto")
            self.assertEqual(session["access_token"], "access")
            self.assertEqual(session["usuario"]["rol"], "Administrador")
            peticion = abrir.call_args.args[0]
            self.assertEqual(peticion.full_url, "http://auth:8000/api/v1/auth/login")
            self.assertNotIn("Authorization", dict(peticion.header_items()))

    @patch("app.api_client.urllib.request.urlopen", side_effect=URLError("caido"))
    def test_falla_de_red_se_traduce_a_503(self, _abrir):
        with self.app.test_request_context("/"):
            with self.assertRaises(api_client.ErrorServicio) as contexto:
                api_client.solicitar("auth", "GET", "/health", autenticado=False)
            self.assertEqual(contexto.exception.codigo, 503)

    @patch("app.api_client.urllib.request.urlopen")
    def test_401_renueva_token_y_reintenta_una_vez(self, abrir):
        error = HTTPError("http://auth", 401, "Unauthorized", {},
                          io.BytesIO(json.dumps({"error": {
                              "mensaje": "expirado", "tipo": "token_expirado"
                          }}).encode()))
        abrir.side_effect = [
            error,
            Respuesta({"access_token": "access-nuevo", "expires_in": 900}),
            Respuesta({"ok": True}),
        ]
        with self.app.test_request_context("/"):
            session["access_token"] = "access-viejo"
            session["refresh_token"] = "refresh"
            resultado = api_client.solicitar("auth", "GET", "/api/v1/auth/sesion")
            self.assertTrue(resultado["ok"])
            self.assertEqual(session["access_token"], "access-nuevo")
            self.assertEqual(abrir.call_count, 3)


if __name__ == "__main__":
    unittest.main()
