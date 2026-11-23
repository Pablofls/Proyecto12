"""El reverse proxy Nginx enruta, propaga cabeceras y limita sin romper la API.

Estas pruebas SI pasan por Nginx (PROXY_URL, por defecto http://proxy:8080); el
resto de la suite va directo a cada contenedor. Corre al final de su archivo la
prueba del limite de login, que agota la cuota por IP del proxy durante un minuto.

Trazabilidad: RNF-28, RNF-12, RNF-13, RNF-23, RNF-16.
"""
import os
import urllib.error
import urllib.request
import uuid

import pytest

from . import cliente as c

PROXY = os.environ.get("PROXY_URL", "http://proxy:8080").rstrip("/")

# Nombre del prefijo bajo /servicios/ de cada servicio (docs/REVERSE_PROXY.md).
SERVICIOS_HEALTH = (
    "auth", "devoluciones", "logistica", "inspecciones", "disposicion-inventario",
    "reembolsos-costos", "ventas-catalogos", "evidencias", "auditoria",
    "reportes-analitica", "causa-raiz", "sincronizacion", "proveedores",
    "integraciones-monitoreo", "clasificacion-motivos",
)


def pedir(metodo, ruta, cuerpo=None, cabeceras=None):
    peticion = urllib.request.Request(PROXY + ruta, data=cuerpo, method=metodo,
                                      headers=cabeceras or {})
    try:
        with urllib.request.urlopen(peticion, timeout=30) as r:
            return r.status, r.headers, r.read()
    except urllib.error.HTTPError as e:
        return e.code, e.headers, e.read()


def test_salud_del_proxy():
    estado, _, cuerpo = pedir("GET", "/proxy-health")
    assert estado == 200 and b"orvia-proxy" in cuerpo


@pytest.mark.parametrize("servicio", SERVICIOS_HEALTH)
def test_cada_servicio_responde_salud_por_el_proxy(servicio):
    estado, _, _ = pedir("GET", f"/servicios/{servicio}/health")
    assert estado == 200, servicio


@pytest.mark.parametrize("clave", sorted(c.PREFIJO_API))
def test_el_proxy_enruta_igual_que_el_servicio_directo(clave):
    """Mismo codigo por el proxy y directo: la ruta llega al servicio correcto."""
    if clave not in c.SERVICIOS:
        pytest.skip("sin URL directa")
    prefijo = c.PREFIJO_API[clave]
    directo = c.llamar(clave, "GET", prefijo).status
    por_proxy, _, _ = pedir("GET", prefijo, cabeceras={"Accept": "application/json"})
    assert por_proxy == directo, (clave, prefijo)


def test_correlation_id_se_propaga_y_no_se_duplica():
    cid = "e2e-" + uuid.uuid4().hex[:12]
    _, cabeceras, _ = pedir("GET", "/servicios/auth/health", cabeceras={"X-Correlation-ID": cid})
    assert cabeceras.get_all("X-Correlation-ID") == [cid]


def test_ip_falsificada_en_x_forwarded_for_no_se_registra():
    falsa = "9.9.9.9"
    correo = f"xff.{uuid.uuid4().hex[:8]}@demo.mx"
    cuerpo = ('{"email":"%s","password":"x"}' % correo).encode()
    estado, _, _ = pedir("POST", "/api/v1/auth/login", cuerpo,
                         {"Content-Type": "application/json", "X-Forwarded-For": falsa})
    assert estado == 401
    fila = c.sql("SELECT ip_origen FROM intentos_acceso WHERE email=%s ORDER BY id DESC LIMIT 1",
                 (correo,), uno=True)
    assert fila and fila["ip_origen"] != falsa
    # Evita dejar el correo de prueba en la cuenta de bloqueo.
    c.liberar_limite_login()


def test_subida_de_9_mb_pasa_el_proxy_y_31_mb_se_rechazan_en_el_proxy():
    # Sin token: el servicio responde 401 si el cuerpo llego; Nginx 413 si no cabe (30 MB).
    estado, _, _ = pedir("POST", "/api/v1/evidencias", b"x" * (9 * 1024 * 1024),
                         {"Content-Type": "application/octet-stream"})
    assert estado != 413
    estado, _, _ = pedir("POST", "/api/v1/evidencias", b"x" * (31 * 1024 * 1024),
                         {"Content-Type": "application/octet-stream"})
    assert estado == 413


def test_limite_de_login_del_proxy_responde_429():
    # Va al final: agota los 10/min (+5 de rafaga) por IP en Nginx.
    estados = []
    for i in range(25):
        cuerpo = ('{"email":"nginx%d.%s@demo.mx","password":"x"}' % (i, uuid.uuid4().hex[:6])).encode()
        estados.append(pedir("POST", "/api/v1/auth/login", cuerpo,
                             {"Content-Type": "application/json"})[0])
    assert 429 in estados
    c.liberar_limite_login()
