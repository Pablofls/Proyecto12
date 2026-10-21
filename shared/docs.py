"""Swagger UI para cada servicio, sin dependencias extra de Python.

El contrato vive en el openapi.yaml de cada servicio. Swagger UI se carga
desde CDN en el navegador y ejecuta peticiones reales contra el servicio.
"""
import os

import yaml
from flask import Response, jsonify, send_from_directory

from shared.respuestas import ErrorApi

_HTML = """<!doctype html>
<html lang="es"><head><meta charset="utf-8"><title>{titulo}</title>
<link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5.17.14/swagger-ui.css">
</head><body><div id="swagger"></div>
<script src="https://unpkg.com/swagger-ui-dist@5.17.14/swagger-ui-bundle.js"></script>
<script>SwaggerUIBundle({{url: "openapi.json", dom_id: "#swagger",
  persistAuthorization: true}});</script>
</body></html>"""


def registrar(app, ruta_yaml):
    with open(ruta_yaml, encoding="utf-8") as f:
        especificacion = yaml.safe_load(f)
    titulo = especificacion.get("info", {}).get("title", "API")
    # Contratos XSD publicados: los del servicio y el del error comun.
    carpetas = [os.path.join(os.path.dirname(ruta_yaml), "contratos"),
                os.path.join(os.path.dirname(__file__), "contratos")]

    @app.get("/openapi.json")
    def _openapi():
        return jsonify(especificacion)

    @app.get("/contratos/<nombre>")
    def _contrato(nombre):
        if nombre.endswith(".xsd"):
            for carpeta in carpetas:
                if os.path.isfile(os.path.join(carpeta, nombre)):
                    # send_from_directory impide salir de la carpeta (../).
                    return send_from_directory(carpeta, nombre,
                                               mimetype="application/xml")
        raise ErrorApi(404, "no_encontrado", f"No existe el contrato {nombre}.")

    @app.get("/docs")
    def _docs():
        return Response(_HTML.format(titulo=titulo), mimetype="text/html")
