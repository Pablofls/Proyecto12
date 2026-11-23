"""Rutas de /api/v1/analisis, retiradas: responden 410 y dicen donde vive cada cosa.

El analisis se separo de la auditoria (correccion del profe: que cambiar el analisis nunca toque la
auditoria). Su codigo ya no existe aqui; este modulo solo evita que un cliente rezagado reciba un 404 sin
explicacion. No importa ni la auditoria ni nada de calculo: no hay logica que mantener.

    clasificar-motivo -> clasificacion-motivos (8010)  POST /api/v1/motivos/sugerencias
    alertas-fraude    -> reportes-analitica (8018)     GET  /api/v1/analitica/alertas-fraude
    pareto            -> reportes-analitica (8018)     GET  /api/v1/reportes/pareto
    sincronizar       -> ya no hace falta: 8018 calcula directo en PostgreSQL
    resumen           -> sin sucesor (solo contaba snapshots)
    eventos           -> este servicio, GET /api/v1/auditoria/eventos

Trazabilidad: RF-30, RN-12. Guia: docs/MIGRACION_ANALISIS_8008.md.
"""
from flask import Blueprint

from shared.respuestas import ErrorApi

bp = Blueprint("analisis_retirado", __name__, url_prefix="/api/v1/analisis")

SUCESORES = {
    "clasificar-motivo": "http://clasificacion-motivos:8000/api/v1/motivos/sugerencias",
    "alertas-fraude": "http://reportes-analitica:8000/api/v1/analitica/alertas-fraude",
    "pareto": "http://reportes-analitica:8000/api/v1/reportes/pareto",
    "eventos": "/api/v1/auditoria/eventos",
}
METODOS = ["GET", "POST", "PUT", "PATCH", "DELETE"]


@bp.route("", methods=METODOS)
@bp.route("/<path:resto>", methods=METODOS)
def retirado(resto=""):
    """Cualquier ruta bajo /analisis: aun sin token, porque no hay nada que proteger."""
    raise ErrorApi(410, "servicio_movido",
                   "El analisis ya no se ofrece en analisis-auditoria; solo queda la auditoria.", SUCESORES)


@bp.after_request
def _marcar_obsoleto(respuesta):
    respuesta.headers["Deprecation"] = "true"
    return respuesta
