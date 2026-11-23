import pytest
from pathlib import Path

RAIZ = Path(__file__).parents[2]
COMPOSE = (RAIZ / "docker-compose.yml").read_text(encoding="utf-8")
HTTP = (RAIZ / "infra/nginx/conf.d/orvia-http.conf").read_text(encoding="utf-8")
TLS = (RAIZ / "infra/nginx/conf.d/orvia-tls.conf").read_text(encoding="utf-8")

SERVICIOS = {
    "app", "auth", "devoluciones", "logistica", "inspecciones",
    "disposicion-inventario", "reembolsos-costos", "ventas-catalogos", "evidencias",
    "analisis-auditoria", "reportes-analitica", "causa-raiz",
    "sincronizacion", "proveedores", "integraciones-monitoreo",
    "clasificacion-motivos",
}


def test_solo_proxy_publica_puertos_de_aplicacion():
    assert '"0.0.0.0:${PROXY_HTTP_PORT:-80}:8080"' in COMPOSE
    for nombre in SERVICIOS:
        inicio = COMPOSE.index(f"  {nombre}:\n")
        siguientes = [p for p in (COMPOSE.find(f"\n  {otro}:\n", inicio + 1)
                                   for otro in SERVICIOS | {"proxy"}) if p >= 0]
        fin = min(siguientes, default=len(COMPOSE))
        bloque = COMPOSE[inicio:fin]
        assert "    ports:" not in bloque, nombre
        assert '    expose: ["8000"]' in bloque, nombre


def test_backend_no_publica_puertos_y_proxy_tiene_dos_redes():
    # No se usa `internal: true`: evidencias e integraciones necesitan salida a
    # GCS/POS/ERP. La ausencia de `ports` impide la entrada directa desde host.
    assert "    networks: [default, public]" in COMPOSE


def test_todas_las_api_tienen_destino_en_http_y_tls():
    destinos = {
        "auth", "devoluciones", "logistica", "inspecciones",
        "disposicion-inventario", "reembolsos-costos", "ventas-catalogos", "evidencias",
        "analisis-auditoria", "reportes-analitica", "causa-raiz",
        "sincronizacion", "proveedores", "integraciones-monitoreo",
        "clasificacion-motivos",
    }
    for destino in destinos:
        expresion = f"set $destino {destino};"
        assert expresion in HTTP, destino
        assert expresion in TLS, destino


def test_tls_redirige_y_no_admite_protocolos_obsoletos():
    assert "return 308 https://$host$request_uri" in TLS
    assert "ssl_protocols TLSv1.2 TLSv1.3;" in TLS
    assert "TLSv1.1" not in TLS


def test_nginx_resuelve_los_nombres_en_cada_peticion():
    # Con IPs fijadas al arrancar, recrear un contenedor enruta al equivocado.
    base = (RAIZ / "infra/nginx/nginx.conf").read_text(encoding="utf-8")
    assert "resolver 127.0.0.11" in base
    for conf in (HTTP, TLS):
        assert "proxy_pass http://$destino:8000;" in conf
        # proxy_pass sin variable (literal) volveria a fijar la IP al arrancar
        for linea in conf.splitlines():
            if "proxy_pass" in linea:
                assert "$destino" in linea, linea


def test_los_prefijos_de_servicios_se_recortan_con_rewrite():
    for conf in (HTTP, TLS):
        assert "rewrite ^/servicios/auth/(.*)$ /$1 break;" in conf


def test_cabecera_de_correlacion_no_se_duplica():
    comun = (RAIZ / "infra/nginx/snippets/proxy-common.conf").read_text(encoding="utf-8")
    assert "proxy_hide_header X-Correlation-ID;" in comun


def test_openapi_no_apunta_a_puertos_directos():
    for archivo in (RAIZ / "services").glob("*/openapi.yaml"):
        assert "localhost:80" not in archivo.read_text(encoding="utf-8"), archivo


def test_healthcheck_del_proxy_usa_ipv4_explicito():
    # `localhost` resuelve a ::1 en Alpine y Nginx solo escucha IPv4: quedaba unhealthy.
    assert "http://127.0.0.1:8080/proxy-health" in COMPOSE
    assert "localhost:8080" not in COMPOSE


def test_toda_ruta_de_los_openapi_tiene_location_en_nginx():
    """Si alguien agrega un endpoint o servicio, esta prueba falla hasta que Nginx lo enrute."""
    import re
    yaml = pytest.importorskip("yaml")
    for nombre, conf in (("http", HTTP), ("tls", TLS)):
        prefijos = re.findall(r"location (?:\^~ |= )?(/api/v1/[^ ]*) ", conf)
        assert prefijos, nombre
        for archivo in sorted((RAIZ / "services").glob("*/openapi.yaml")):
            spec = yaml.safe_load(archivo.read_text(encoding="utf-8"))
            for ruta in (spec.get("paths") or {}):
                if ruta.startswith("/api/v1"):
                    assert any(ruta.startswith(p) for p in prefijos), (nombre, archivo.parent.name, ruta)
