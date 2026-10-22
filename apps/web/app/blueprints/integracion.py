
"""Panel web de integracion y salud de microservicios (RNF-22, RF-32)."""

from concurrent.futures import ThreadPoolExecutor

from flask import Blueprint, jsonify, render_template

from app.microservicios import SERVICIOS, consultar_salud
from app.security import ADMINISTRADOR, roles_required


bp = Blueprint(
    "integracion",
    __name__,
    url_prefix="/integracion"
)


def obtener_estados():
    """Consulta los microservicios en paralelo."""

    with ThreadPoolExecutor(max_workers=len(SERVICIOS)) as executor:
        estados = list(
            executor.map(
                lambda servicio: consultar_salud(*servicio),
                SERVICIOS
            )
        )

    return estados


@bp.get("/servicios")
@roles_required(ADMINISTRADOR)
def servicios():
    """Muestra el panel de arquitectura distribuida."""

    estados = obtener_estados()

    disponibles = sum(
        1 for servicio in estados
        if servicio["disponible"]
    )

    return render_template(
        "integracion/servicios.html",
        estados=estados,
        disponibles=disponibles,
    )


@bp.get("/servicios/estado")
@roles_required(ADMINISTRADOR)
def servicios_estado():
    """Devuelve las mediciones actuales en formato JSON."""

    estados = obtener_estados()

    disponibles = sum(
        1 for servicio in estados
        if servicio["disponible"]
    )

    latencias = [
        servicio["latencia_ms"]
        for servicio in estados
        if servicio["disponible"]
    ]

    promedio = (
        round(sum(latencias) / len(latencias))
        if latencias
        else None
    )

    return jsonify({
        "estados": estados,
        "disponibles": disponibles,
        "total": len(estados),
        "alertas": len(estados) - disponibles,
        "latencia_promedio_ms": promedio,
    })
