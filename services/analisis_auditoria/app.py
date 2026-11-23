"""Auditoria (bitacora y traza de eventos). Este servicio queda solo con eso.

El analisis (clasificar, Pareto, alertas de fraude) se separo y su codigo se retiro: lo sustituyen
clasificacion-motivos (8010) y reportes-analitica (8018). Las rutas de /api/v1/analisis responden
410 servicio_movido con los sucesores (retirado.py), para que un cliente rezagado sepa a donde ir.

Trazabilidad: RF-30, RN-12, RNF-23. Guia: docs/MIGRACION_ANALISIS_8008.md.
"""
import os

from flask import Flask

import auditoria
import retirado
from shared import docs, mongo, respuestas
from shared.infra import cerrar_conexion, salud_postgres, salud_redis
from shared.respuestas import responder

NOMBRE = "analisis-auditoria"


def create_app():
    app = Flask(__name__)
    app.json.sort_keys = False
    respuestas.registrar(app, NOMBRE)
    app.teardown_appcontext(cerrar_conexion)
    app.register_blueprint(auditoria.bp)
    app.register_blueprint(retirado.bp)
    docs.registrar(app, os.path.join(os.path.dirname(__file__), "openapi.yaml"))

    @app.get("/health")
    def health():
        deps = {"postgresql": salud_postgres(), "redis": salud_redis(),
                "mongodb": mongo.salud_mongo()}
        ok = all(x["ok"] for x in deps.values())
        return responder({"servicio": NOMBRE, "version": "v1", "estado": "ok" if ok else "degradado",
                          "dependencias": deps,
                          "analisis": "retirado"},
                         200 if ok else 503)
    return app
