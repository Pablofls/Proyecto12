"""Cliente HTTP exclusivamente XML para la aplicacion de escritorio."""
import json
import os
import sys
import uuid
from pathlib import Path

import requests
from lxml import etree


def raiz_recursos():
    """Raiz del repositorio en desarrollo o del paquete temporal de PyInstaller."""
    return Path(getattr(sys, "_MEIPASS", Path(__file__).parents[2]))


def ruta_configuracion():
    """Permite configurar el ejecutable sin reconstruirlo."""
    configurada = os.environ.get("DEVOLUCIONES_DESKTOP_CONFIG")
    if configurada:
        return Path(configurada)
    if getattr(sys, "frozen", False):
        externa = Path(sys.executable).with_name("config.json")
        if externa.exists():
            return externa
        return raiz_recursos() / "apps" / "escritorio" / "config.example.json"
    return Path(__file__).with_name("config.json")


class ErrorServicio(Exception):
    def __init__(self, codigo, tipo, mensaje, correlation_id=None):
        super().__init__(mensaje)
        self.codigo, self.tipo = codigo, tipo
        self.correlation_id = correlation_id


def _valor(elemento):
    hijos = list(elemento)
    if not hijos:
        return (elemento.text or "").strip()
    if all(h.tag == "item" for h in hijos):
        return [_valor(h) for h in hijos]
    resultado = {}
    for hijo in hijos:
        valor = _valor(hijo)
        if hijo.tag in resultado:
            actual = resultado[hijo.tag]
            resultado[hijo.tag] = actual + [valor] if isinstance(actual, list) else [actual, valor]
        else:
            resultado[hijo.tag] = valor
    return resultado


def crear_xml(raiz, datos):
    nodo = etree.Element(raiz)
    for nombre, valor in datos.items():
        hijo = etree.SubElement(nodo, nombre)
        if valor is not None:
            if isinstance(valor, bool):
                hijo.text = "true" if valor else "false"
            else:
                hijo.text = str(valor)
    return etree.tostring(nodo, xml_declaration=True, encoding="UTF-8")


def validar_xsd(xml, ruta):
    esquema = etree.XMLSchema(etree.parse(str(ruta)))
    documento = etree.fromstring(xml, etree.XMLParser(resolve_entities=False,
                                                       no_network=True,
                                                       load_dtd=False))
    if not esquema.validate(documento):
        raise ValueError("; ".join(e.message for e in esquema.error_log))


class ClienteXml:
    def __init__(self, configuracion=None, sesion=None):
        ruta = Path(configuracion) if configuracion else ruta_configuracion()
        if ruta.exists():
            self.servicios = json.loads(ruta.read_text(encoding="utf-8"))
        else:
            ejemplo = raiz_recursos() / "apps" / "escritorio" / "config.example.json"
            self.servicios = json.loads(ejemplo.read_text(encoding="utf-8"))
        self.http = sesion or requests.Session()
        self.access_token = None
        self.refresh_token = None
        self.usuario = None

    def solicitar(self, servicio, metodo, ruta, *, raiz=None, datos=None,
                  xsd=None, respuesta_xsd=None, token_operacion=None, autenticado=True):
        cuerpo = None
        if datos is not None:
            cuerpo = crear_xml(raiz, datos)
            if xsd:
                validar_xsd(cuerpo, xsd)  # falla antes de tocar la red
        cabeceras = {"Accept": "application/xml",
                     "X-Correlation-ID": uuid.uuid4().hex[:16]}
        if cuerpo is not None:
            cabeceras["Content-Type"] = "application/xml"
        if autenticado:
            if not self.access_token:
                raise ErrorServicio(401, "token_ausente", "Inicia sesion.")
            cabeceras["Authorization"] = f"Bearer {self.access_token}"
        if token_operacion:
            cabeceras["X-Autorizacion-Operacion"] = token_operacion
        respuesta = self.http.request(metodo, self.servicios[servicio].rstrip("/") + ruta,
                                      data=cuerpo, headers=cabeceras, timeout=12)
        try:
            if respuesta_xsd and respuesta.status_code < 400:
                validar_xsd(respuesta.content, respuesta_xsd)
            if respuesta.status_code >= 400:
                error_xsd = raiz_recursos() / "shared" / "contratos" / "error.xsd"
                validar_xsd(respuesta.content, error_xsd)
            xml = etree.fromstring(respuesta.content)
            contenido = _valor(xml)
        except etree.XMLSyntaxError as exc:
            raise ErrorServicio(502, "respuesta_no_xml",
                                 "El servicio no devolvio XML valido.") from exc
        if respuesta.status_code >= 400:
            raise ErrorServicio(respuesta.status_code,
                                 contenido.get("tipo", "error_http"),
                                 contenido.get("mensaje", "Operacion rechazada."),
                                 contenido.get("correlation_id"))
        return contenido

    def login(self, email, password):
        xsd = raiz_recursos() / "services" / "auth" / "contratos" / "login.xsd"
        respuesta_xsd = raiz_recursos() / "services" / "auth" / "contratos" / "tokens.xsd"
        respuesta = self.solicitar("auth", "POST", "/api/v1/auth/login",
            raiz="login", datos={"email": email, "password": password}, xsd=xsd,
            respuesta_xsd=respuesta_xsd, autenticado=False)
        self.access_token, self.refresh_token = respuesta["access_token"], respuesta["refresh_token"]
        self.usuario = respuesta.get("usuario") or {}
        return respuesta

    def cerrar_sesion_local(self):
        """El cliente de escritorio no persiste secretos entre sesiones."""
        self.access_token = None
        self.refresh_token = None
        self.usuario = None
        self.http.cookies.clear()

    def autorizar(self, operacion, recurso_id, password):
        xsd = raiz_recursos() / "services" / "auth" / "contratos" / "autorizar_operacion.xsd"
        return self.solicitar("auth", "POST", "/api/v1/auth/autorizar-operacion",
            raiz="autorizacion", datos={"operacion": operacion,
            "recurso_id": recurso_id, "password": password}, xsd=xsd)["token_operacion"]
