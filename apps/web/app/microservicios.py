"""Cliente HTTP pequeno para supervisar la arquitectura distribuida.

El monolito sigue funcionando si los servicios estan apagados: cada fallo se
convierte en estado degradado y nunca impide navegar el sistema web.
"""
import json
import os
import time
import urllib.error
import urllib.request


SERVICIOS = (
    ("auth", "AUTH_SERVICE_URL", "http://auth:8000"),
    ("devoluciones", "DEVOLUCIONES_SERVICE_URL", "http://devoluciones:8000"),
    ("logistica", "LOGISTICA_SERVICE_URL", "http://logistica:8000"),
    ("inspecciones", "INSPECCIONES_SERVICE_URL", "http://inspecciones:8000"),
    ("reembolsos-costos", "REEMBOLSOS_SERVICE_URL", "http://reembolsos-costos:8000"),
    ("ventas-catalogos", "VENTAS_SERVICE_URL", "http://ventas-catalogos:8000"),
    ("evidencias", "EVIDENCIAS_SERVICE_URL", "http://evidencias:8000"),
    ("analisis-auditoria", "ANALISIS_SERVICE_URL", "http://analisis-auditoria:8000"),
)


def consultar_salud(nombre, variable, predeterminado, timeout=2.0):
    """Consulta /health con limite estricto y respuesta segura para la UI."""
    base = os.environ.get(variable, predeterminado).rstrip("/")
    inicio = time.perf_counter()
    try:
        peticion = urllib.request.Request(
            base + "/health", headers={"Accept": "application/json"}
        )
        with urllib.request.urlopen(peticion, timeout=timeout) as respuesta:
            cuerpo = json.loads(respuesta.read().decode("utf-8"))
            codigo = respuesta.status
        estado = cuerpo.get("estado", "desconocido")
        disponible = codigo == 200 and estado == "ok"
        error = None if disponible else "El servicio reporto estado degradado."
    except (urllib.error.URLError, TimeoutError, OSError, ValueError, json.JSONDecodeError):
        codigo, cuerpo, estado, disponible = None, {}, "no_disponible", False
        error = "No fue posible consultar el servicio."
    return {
        "nombre": nombre,
        "url": base,
        "codigo_http": codigo,
        "estado": estado,
        "disponible": disponible,
        "dependencias": cuerpo.get("dependencias", {}),
        "latencia_ms": round((time.perf_counter() - inicio) * 1000),
        "error": error,
    }


def estado_arquitectura():
    return [consultar_salud(*servicio) for servicio in SERVICIOS]
