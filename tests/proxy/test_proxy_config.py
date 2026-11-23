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
        expresion = f"proxy_pass http://{destino}:8000"
        assert expresion in HTTP, destino
        assert expresion in TLS, destino


def test_tls_redirige_y_no_admite_protocolos_obsoletos():
    assert "return 308 https://$host$request_uri" in TLS
    assert "ssl_protocols TLSv1.2 TLSv1.3;" in TLS
    assert "TLSv1.1" not in TLS
