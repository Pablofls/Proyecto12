import os
import sys
import time
import uuid
from pathlib import Path

import jwt

sys.path.insert(0, str(Path(__file__).parents[1]))
sys.path.insert(0, str(Path(__file__).parents[3]))
os.environ.setdefault("JWT_SECRET", "x" * 48)

import app as servicio
from shared import seguridad


class RedisFalso:
    def __init__(self): self.datos = {}
    def exists(self, clave): return int(clave in self.datos)


def token(redis, rol):
    sid = uuid.uuid4().hex; redis.datos[seguridad.clave_sesion(sid)] = "1"
    ahora = int(time.time())
    return jwt.encode({"iss": seguridad.EMISOR, "sub": "7", "rol": rol,
        "nombre": "Prueba", "sid": sid, "jti": uuid.uuid4().hex, "typ": "access",
        "iat": ahora, "exp": ahora + 600}, os.environ["JWT_SECRET"], algorithm="HS256")


def test_disposicion_exige_autorizacion_y_persiste(monkeypatch):
    redis = RedisFalso(); monkeypatch.setattr(seguridad, "get_redis", lambda: redis)
    expediente = {"id": 9, "folio_devolucion": "DEV-9", "estado": "en_inspeccion",
        "producto_id": 2, "producto": "Producto", "sku": "P-1", "numero_lote": "L-1",
        "inspeccion_id": 3, "apto_para_inventario": True,
        "estado_dictamen": "concluido", "recomendacion": "reintegrar"}
    monkeypatch.setattr(servicio, "_expediente", lambda *a, **k: expediente)
    monkeypatch.setattr(servicio, "consultar", lambda *a, **k: None)
    guardado = {}
    def ejecutar(sql, params=None, devolver=False):
        if "INSERT INTO disposiciones" in sql:
            guardado["params"] = params
            return {"id": 4, "devolucion_id": 9, "destino": "inventario",
                    "justificacion": params[3], "estado": "autorizada",
                    "fecha_decision": None}
    monkeypatch.setattr(servicio, "ejecutar", ejecutar)
    monkeypatch.setattr(servicio, "registrar_bitacora", lambda *a, **k: None)
    monkeypatch.setattr(servicio, "exigir_autorizacion_operacion",
                        lambda op, recurso: {"jti": "un-solo-uso"})
    cliente = servicio.create_app().test_client()
    respuesta = cliente.post("/api/v1/disposicion-inventario/disposiciones",
        headers={"Authorization": "Bearer " + token(redis, seguridad.ANALISTA)},
        json={"devolucion_id": 9, "destino": "reintegrar",
              "justificacion": "Dictamen tecnico favorable"})
    assert respuesta.status_code == 201
    assert guardado["params"][2] == "inventario"
    assert guardado["params"][4] == "un-solo-uso"


def test_cliente_no_puede_decidir(monkeypatch):
    redis = RedisFalso(); monkeypatch.setattr(seguridad, "get_redis", lambda: redis)
    cliente = servicio.create_app().test_client()
    respuesta = cliente.post("/api/v1/disposicion-inventario/disposiciones",
        headers={"Authorization": "Bearer " + token(redis, seguridad.CLIENTE)}, json={})
    assert respuesta.status_code == 403


def test_xml_no_conforme_se_rechaza(monkeypatch):
    redis = RedisFalso(); monkeypatch.setattr(seguridad, "get_redis", lambda: redis)
    cliente = servicio.create_app().test_client()
    respuesta = cliente.post("/api/v1/disposicion-inventario/disposiciones",
        headers={"Authorization": "Bearer " + token(redis, seguridad.ANALISTA),
                 "Content-Type": "application/xml", "Accept": "application/xml"},
        data="<disposicion><devolucion_id>9</devolucion_id></disposicion>")
    assert respuesta.status_code == 400
    assert b"xml_no_cumple_xsd" in respuesta.data
