"""La IP registrada no puede inventarla el cliente (RNF-13, RNF-16)."""
from flask import Flask

from app.security import ip_cliente


def _ip(monkeypatch, confiar, xff, remoto="172.20.0.2"):
    if confiar is None:
        monkeypatch.delenv("TRUST_PROXY_HEADERS", raising=False)
    else:
        monkeypatch.setenv("TRUST_PROXY_HEADERS", confiar)
    cabeceras = {"X-Forwarded-For": xff} if xff else {}
    with Flask(__name__).test_request_context("/", headers=cabeceras, environ_base={"REMOTE_ADDR": remoto}):
        return ip_cliente()


def test_sin_proxy_confiable_se_ignora_la_cabecera(monkeypatch):
    assert _ip(monkeypatch, None, "1.2.3.4") == "172.20.0.2"


def test_con_proxy_se_usa_el_ultimo_salto_no_el_inventado(monkeypatch):
    assert _ip(monkeypatch, "true", "1.2.3.4, 203.0.113.8") == "203.0.113.8"


def test_sin_cabecera_cae_a_la_ip_remota(monkeypatch):
    assert _ip(monkeypatch, "true", "") == "172.20.0.2"


def test_cabecera_larga_no_rebasa_la_columna(monkeypatch):
    assert len(_ip(monkeypatch, "true", "x" * 300)) <= 64
