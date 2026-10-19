"""Respuestas uniformes en JSON o XML y manejo estandarizado de errores.

Todos los servicios negocian el formato con el header Accept:
- Accept: application/json (o sin header) -> JSON
- Accept: application/xml                 -> XML
y aceptan cuerpos con Content-Type application/json o application/xml.

Formato de error comun (RNF-16: nunca expone trazas ni datos internos):
    {"error": {"codigo": 404, "tipo": "no_encontrado", "mensaje": "...",
               "detalles": [...], "correlation_id": "..."}}
"""
import logging
import time
import uuid
import xml.etree.ElementTree as ET
from datetime import date, datetime
from decimal import Decimal

from flask import Response, g, jsonify, request
from werkzeug.exceptions import HTTPException

log = logging.getLogger("servicio")

TIPOS_XML = ("application/xml", "text/xml")


class ErrorApi(Exception):
    """Error de negocio o de validacion que se traduce en una respuesta HTTP."""

    def __init__(self, codigo, tipo, mensaje, detalles=None, headers=None):
        super().__init__(mensaje)
        self.codigo = codigo
        self.tipo = tipo
        self.mensaje = mensaje
        self.detalles = detalles
        self.headers = headers or {}


# --------------------------------------------------------------------------- #
# Conversion a XML
# --------------------------------------------------------------------------- #
def _texto(valor):
    if isinstance(valor, bool):
        return "true" if valor else "false"
    return str(valor)


def _agregar(padre, nombre, valor):
    elem = ET.SubElement(padre, nombre)
    if isinstance(valor, dict):
        for k, v in valor.items():
            _agregar(elem, k, v)
    elif isinstance(valor, (list, tuple)):
        for v in valor:
            _agregar(elem, "item", v)
    elif valor is not None:
        elem.text = _texto(valor)
    # None -> elemento vacio: el campo existe pero no tiene valor.


def a_xml(raiz, datos):
    """Convierte un dict en un documento XML con declaracion UTF-8."""
    elem = ET.Element(raiz)
    for k, v in (datos or {}).items():
        _agregar(elem, k, v)
    return ET.tostring(elem, encoding="utf-8", xml_declaration=True)


def _elemento_a_valor(elem):
    hijos = list(elem)
    if not hijos:
        return (elem.text or "").strip()
    if all(h.tag == "item" for h in hijos):
        return [_elemento_a_valor(h) for h in hijos]
    return {h.tag: _elemento_a_valor(h) for h in hijos}


# --------------------------------------------------------------------------- #
# Negociacion y respuesta
# --------------------------------------------------------------------------- #
def quiere_xml():
    mejor = request.accept_mimetypes.best_match(["application/json", *TIPOS_XML])
    return mejor in TIPOS_XML


def _normalizar(valor):
    """Tipos de PostgreSQL a valores del contrato: fechas en ISO 8601 (jsonify
    las pondria en formato RFC 822) y montos NUMERIC como numero."""
    if isinstance(valor, dict):
        return {k: _normalizar(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_normalizar(v) for v in valor]
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    if isinstance(valor, Decimal):
        return float(valor)
    return valor


def responder(datos, codigo=200, raiz="respuesta", headers=None):
    """Respuesta exitosa en el formato que pidio el cliente."""
    datos = _normalizar(datos)
    if quiere_xml():
        resp = Response(a_xml(raiz, datos), status=codigo,
                        mimetype="application/xml")
    else:
        resp = jsonify(datos)
        resp.status_code = codigo
    for k, v in (headers or {}).items():
        resp.headers[k] = v
    return resp


def responder_error(codigo, tipo, mensaje, detalles=None, headers=None):
    cuerpo = {
        "codigo": codigo,
        "tipo": tipo,
        "mensaje": mensaje,
        "detalles": detalles,
        "correlation_id": g.get("correlation_id"),
    }
    if quiere_xml():
        return responder(cuerpo, codigo, raiz="error", headers=headers)
    return responder({"error": cuerpo}, codigo, headers=headers)


def leer_cuerpo(xsd=None):
    """Devuelve el cuerpo de la peticion como dict, venga en JSON o en XML.

    Con 'xsd' (ruta a un esquema), un cuerpo XML se valida contra el contrato
    antes de procesarse; ver shared/xsd.py.
    """
    tipo = (request.mimetype or "").lower()
    if tipo == "application/json":
        datos = request.get_json(silent=True)
        if not isinstance(datos, dict):
            raise ErrorApi(400, "json_invalido",
                           "El cuerpo no es un objeto JSON valido.")
        return datos
    if tipo in TIPOS_XML:
        try:
            raiz = ET.fromstring(request.get_data())
        except ET.ParseError as exc:
            raise ErrorApi(400, "xml_invalido",
                           "El cuerpo no es un documento XML bien formado.",
                           [str(exc)])
        if xsd:
            # Import diferido: solo los servicios con contratos XSD instalan lxml.
            from shared import xsd as validador
            validador.exigir(request.get_data(), xsd)
        valor = _elemento_a_valor(raiz)
        return valor if isinstance(valor, dict) else {}
    raise ErrorApi(415, "formato_no_soportado",
                   "Usa Content-Type application/json o application/xml.")


# --------------------------------------------------------------------------- #
# Registro en la aplicacion
# --------------------------------------------------------------------------- #
_NOMBRES_HTTP = {
    400: "peticion_invalida", 401: "no_autenticado", 403: "sin_permiso",
    404: "no_encontrado", 405: "metodo_no_permitido",
    415: "formato_no_soportado", 429: "demasiadas_peticiones",
}


def registrar(app, nombre_servicio):
    """Correlation id, registro de actividad y manejadores de error comunes."""
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s %(message)s")

    @app.before_request
    def _inicio():
        # Se respeta el id que mande otro servicio para seguir la operacion
        # completa entre servicios (RNF-23).
        g.correlation_id = (request.headers.get("X-Correlation-ID")
                            or uuid.uuid4().hex[:16])
        g.inicio = time.perf_counter()

    @app.after_request
    def _fin(resp):
        resp.headers["X-Correlation-ID"] = g.get("correlation_id", "")
        ms = (time.perf_counter() - g.get("inicio", time.perf_counter())) * 1000
        usuario = (g.get("usuario") or {}).get("id", "-")
        log.info("%s %s %s %s %d %.0fms usuario=%s cid=%s",
                 nombre_servicio, request.remote_addr, request.method,
                 request.path, resp.status_code, ms, usuario,
                 g.get("correlation_id"))
        return resp

    @app.errorhandler(ErrorApi)
    def _error_api(exc):
        return responder_error(exc.codigo, exc.tipo, exc.mensaje,
                               exc.detalles, exc.headers)

    @app.errorhandler(HTTPException)
    def _error_http(exc):
        tipo = _NOMBRES_HTTP.get(exc.code, "error_http")
        return responder_error(exc.code, tipo, exc.description)

    @app.errorhandler(Exception)
    def _error_interno(exc):
        # La traza completa va al log del contenedor, nunca al cliente (RNF-16).
        log.exception("Error no controlado cid=%s", g.get("correlation_id"))
        g.error_interno = True  # infra.cerrar_conexion hace rollback
        return responder_error(500, "error_interno",
                               "Ocurrio un error inesperado. Reporta el "
                               "correlation_id al administrador.")
