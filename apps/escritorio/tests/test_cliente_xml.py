from pathlib import Path
import sys

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))
from cliente_xml import ClienteXml, crear_xml, validar_xsd


def test_login_xml_valido_cumple_xsd():
    xml = crear_xml("login", {"email": "inspector@demo.com", "password": "Demo1234!"})
    xsd = Path(__file__).parents[3] / "services" / "auth" / "contratos" / "login.xsd"
    validar_xsd(xml, xsd)


def test_xml_invalido_se_rechaza_antes_de_red():
    xml = crear_xml("login", {"email": "no-es-correo", "password": ""})
    xsd = Path(__file__).parents[3] / "services" / "auth" / "contratos" / "login.xsd"
    with pytest.raises(ValueError): validar_xsd(xml, xsd)


class Respuesta:
    status_code = 200
    content = b"<respuesta><datos><item><id>1</id></item></datos></respuesta>"


class HttpFalso:
    def request(self, metodo, url, **kwargs):
        assert kwargs["headers"]["Accept"] == "application/xml"
        assert "application/json" not in kwargs["headers"].values()
        return Respuesta()


def test_cliente_solo_solicita_xml(tmp_path):
    config = tmp_path / "config.json"
    config.write_text('{"disposicion":"http://servicio"}', encoding="utf-8")
    cliente = ClienteXml(config, HttpFalso()); cliente.access_token = "jwt"
    assert cliente.solicitar("disposicion", "GET", "/inventario")["datos"][0]["id"] == "1"
