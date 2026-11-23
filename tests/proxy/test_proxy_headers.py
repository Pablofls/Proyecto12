import sys
import types

from flask import Flask

# Esta prueba sólo ejercita el tratamiento de encabezados. El entorno ligero de
# CI no necesita instalar los clientes de PostgreSQL/Redis para importarlo.
if "psycopg2" not in sys.modules:
    psycopg2 = types.ModuleType("psycopg2")
    psycopg2.extras = types.ModuleType("psycopg2.extras")
    psycopg2.extras.RealDictCursor = object
    sys.modules["psycopg2"] = psycopg2
    sys.modules["psycopg2.extras"] = psycopg2.extras
if "redis" not in sys.modules:
    sys.modules["redis"] = types.ModuleType("redis")

from shared.infra import ip_origen


def test_no_confia_en_cabecera_si_proxy_no_esta_habilitado(monkeypatch):
    monkeypatch.delenv("TRUST_PROXY_HEADERS", raising=False)
    app = Flask(__name__)
    with app.test_request_context(
        "/", headers={"X-Forwarded-For": "203.0.113.50"},
        environ_base={"REMOTE_ADDR": "127.0.0.1"},
    ):
        assert ip_origen() == "127.0.0.1"


def test_usa_el_ultimo_salto_agregado_por_nginx(monkeypatch):
    monkeypatch.setenv("TRUST_PROXY_HEADERS", "true")
    app = Flask(__name__)
    with app.test_request_context(
        "/",
        headers={"X-Forwarded-For": "198.51.100.77, 203.0.113.8"},
        environ_base={"REMOTE_ADDR": "172.20.0.2"},
    ):
        assert ip_origen() == "203.0.113.8"
