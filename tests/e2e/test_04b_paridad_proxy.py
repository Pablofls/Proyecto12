"""Paridad del proxy: cada endpoint del OpenAPI responde igual por Nginx y directo.

Para TODAS las rutas y metodos de los 15 openapi.yaml compara el codigo HTTP y el
tipo de error del contenedor (directo) contra Nginx:
  - sin token, todos los metodos (401/400 antes de tocar datos: no escribe nada);
  - con token de Administrador, solo GET (lectura).
Las rutas fuera de /api/v1 (/health, /docs, /openapi.json, /contratos/...) se piden
bajo /servicios/<nombre>/. Va antes de test_05 porque este agota el limite de
login de Nginx. Se excluyen /auth/login y /auth/refresh (los cubre test_05 y la
suite, y comparten el limite de login).

Trazabilidad: RNF-28, RNF-12, RNF-23.
"""
import json
import os
import re
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest
import yaml

from . import cliente as c

RAIZ = Path(__file__).parents[2]
PROXY = os.environ.get("PROXY_URL", "http://proxy:8080").rstrip("/")
METODOS = ("get", "post", "put", "patch", "delete")
EXCLUIDAS = ("/api/v1/auth/login", "/api/v1/auth/refresh")
# carpeta del servicio -> clave del cliente E2E (el nombre bajo /servicios/ sale de c.PREFIJO_PROXY)
CARPETAS = {
    "auth": "auth", "devoluciones": "devoluciones", "logistica": "logistica",
    "inspecciones": "inspecciones", "disposicion_inventario": "disposicion",
    "reembolsos_costos": "reembolsos", "ventas_catalogos": "ventas",
    "evidencias": "evidencias", "analisis_auditoria": "auditoria",
    "clasificacion_motivos": "motivos", "causa_raiz": "causa_raiz",
    "proveedores": "proveedores", "reportes_analitica": "reportes",
    "sincronizacion": "sincronizacion", "integraciones_monitoreo": "integraciones",
}


def _casos():
    casos = []
    for carpeta, clave in CARPETAS.items():
        spec = yaml.safe_load((RAIZ / "services" / carpeta / "openapi.yaml").read_text(encoding="utf-8"))
        for ruta, operaciones in (spec.get("paths") or {}).items():
            if ruta in EXCLUIDAS:
                continue
            real = re.sub(r"\{[^}]+\}", "1", ruta)
            for metodo in operaciones:
                if metodo in METODOS:
                    casos.append((clave, metodo.upper(), real))
    return casos


CASOS = _casos()


def _pedir(url, metodo, token=None):
    cabeceras = {"Accept": "application/json"}
    if token:
        cabeceras["Authorization"] = f"Bearer {token}"
    cuerpo = b"{}" if metodo in ("POST", "PUT", "PATCH") else None
    if cuerpo:
        cabeceras["Content-Type"] = "application/json"
    try:
        with urllib.request.urlopen(urllib.request.Request(url, data=cuerpo, method=metodo,
                                                           headers=cabeceras), timeout=60) as r:
            estado, texto = r.status, r.read()
    except urllib.error.HTTPError as e:
        estado, texto = e.code, e.read()
    try:
        tipo = (json.loads(texto).get("error") or {}).get("tipo")
    except (ValueError, AttributeError):
        tipo = None
    return estado, tipo


def _por_proxy(clave, ruta):
    if ruta.startswith("/api/v1"):
        return PROXY + ruta
    return f"{PROXY}/servicios/{c.PREFIJO_PROXY[clave]}{ruta}"


def _comparar(clave, metodo, ruta, token=None):
    directo = _pedir(c.url_directa(clave) + ruta, metodo, token)
    time.sleep(0.03)  # sin rafagas: limit_req de Nginx es 60 r/s por IP
    por_proxy = _pedir(_por_proxy(clave, ruta), metodo, token)
    assert por_proxy == directo, f"{metodo} {ruta}: directo={directo} proxy={por_proxy}"


def test_el_openapi_declara_endpoints():
    assert len(CASOS) > 100, len(CASOS)


@pytest.mark.parametrize("clave,metodo,ruta", CASOS)
def test_sin_token_responde_igual_por_el_proxy(clave, metodo, ruta):
    _comparar(clave, metodo, ruta)


@pytest.mark.parametrize("clave,metodo,ruta", [x for x in CASOS if x[1] == "GET"])
def test_lectura_con_token_responde_igual_por_el_proxy(ctx, clave, metodo, ruta):
    _comparar(clave, metodo, ruta, ctx.h(c.ADMINISTRADOR))
