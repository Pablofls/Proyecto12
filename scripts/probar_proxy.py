"""Prueba de humo del único punto de entrada público de Orvia."""
import argparse
import json
import sys
import urllib.error
import urllib.request

SERVICIOS = (
    "auth", "devoluciones", "logistica", "inspecciones",
    "reembolsos-costos", "ventas-catalogos", "evidencias", "auditoria",
    "reportes-analitica", "causa-raiz", "sincronizacion", "proveedores",
    "integraciones-monitoreo", "clasificacion-motivos",
)


def pedir(base, ruta):
    peticion = urllib.request.Request(
        base.rstrip("/") + ruta,
        headers={"Accept": "application/json", "X-Correlation-ID": "smoke-proxy"},
    )
    with urllib.request.urlopen(peticion, timeout=15) as respuesta:
        return respuesta.status, dict(respuesta.headers), respuesta.read()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1")
    parser.add_argument(
        "--servicios",
        help="Lista separada por comas; por defecto valida todos los servicios.",
    )
    args = parser.parse_args()
    servicios = SERVICIOS
    if args.servicios:
        servicios = tuple(
            nombre.strip() for nombre in args.servicios.split(",") if nombre.strip()
        )
        desconocidos = sorted(set(servicios) - set(SERVICIOS))
        if desconocidos:
            parser.error("servicios desconocidos: " + ", ".join(desconocidos))
    fallos = []
    for nombre, ruta in [("proxy", "/proxy-health")] + [
        (servicio, f"/servicios/{servicio}/health") for servicio in servicios
    ]:
        try:
            codigo, headers, cuerpo = pedir(args.base, ruta)
            json.loads(cuerpo)
            correlacion = headers.get("X-Correlation-ID")
            print(f"OK  {nombre:28} HTTP {codigo} correlation={correlacion or '-'}")
            if codigo != 200:
                fallos.append(f"{nombre}: HTTP {codigo}")
        except (OSError, ValueError, urllib.error.HTTPError) as exc:
            print(f"ERROR {nombre:25} {exc}")
            fallos.append(f"{nombre}: {exc}")
    if fallos:
        print("\nFallos:\n- " + "\n- ".join(fallos), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
