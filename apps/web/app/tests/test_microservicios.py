import io
import json
import unittest
from unittest.mock import patch

from app.microservicios import consultar_salud


class RespuestaFalsa:
    status = 200

    def __enter__(self):
        return self

    def __exit__(self, *_):
        return False

    def read(self):
        return json.dumps({"estado": "ok", "dependencias": {"redis": {"ok": True}}}).encode()


class PruebaClienteMicroservicios(unittest.TestCase):
    @patch("app.microservicios.urllib.request.urlopen", return_value=RespuestaFalsa())
    def test_servicio_sano(self, _urlopen):
        resultado = consultar_salud("auth", "URL_INEXISTENTE", "http://auth:8000")
        self.assertTrue(resultado["disponible"])
        self.assertEqual(resultado["codigo_http"], 200)

    @patch("app.microservicios.urllib.request.urlopen", side_effect=TimeoutError())
    def test_timeout_degrada_sin_romper_web(self, _urlopen):
        resultado = consultar_salud("auth", "URL_INEXISTENTE", "http://auth:8000")
        self.assertFalse(resultado["disponible"])
        self.assertEqual(resultado["estado"], "no_disponible")

    @patch("app.microservicios.urllib.request.urlopen")
    def test_json_invalido_degrada(self, urlopen):
        respuesta = RespuestaFalsa()
        respuesta.read = lambda: b"no-json"
        urlopen.return_value = respuesta
        resultado = consultar_salud("auth", "URL_INEXISTENTE", "http://auth:8000")
        self.assertFalse(resultado["disponible"])


if __name__ == "__main__":
    unittest.main()
