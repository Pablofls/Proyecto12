"""Mismo endpoint en JSON y en XML (Accept / Content-Type), contra HTTP real.

- Las respuestas XML de auth se validan contra sus XSD de respuesta
  (services/auth/contratos/tokens.xsd y sesion.xsd) con shared/xsd.py.
- Los demas servicios solo publican XSD de PETICION: se valida cada cuerpo XML
  contra su XSD *antes* de enviarlo (el contrato y el servicio deben coincidir)
  y de la respuesta se comprueba que sea XML bien formado con la raiz esperada.

Trazabilidad: RNF-28; RF-31, RNF-17 (JSON/XML), seccion 6 del enunciado (XSD).
"""
import os
from datetime import date, timedelta
from pathlib import Path

import pytest

from . import cliente as c
from . import flujo

P = c.PREFIJO_API
RAIZ = Path(__file__).resolve().parents[2]


def xsd(servicio, nombre):
    return str(RAIZ / "services" / servicio / "contratos" / nombre)


def cumple(documento, ruta):
    from shared import xsd as validador
    texto = documento.encode() if isinstance(documento, str) else documento
    return validador.errores(texto, ruta)


@pytest.fixture(autouse=True, scope="module")
def _sin_limite_previo(ctx):
    c.liberar_limite_login()


def test_login_en_xml_y_respuesta_valida_contra_tokens_xsd(ctx):
    xml = (f"<login><email>{ctx.emails[c.CLIENTE]}</email>"
           f"<password>{os.environ['PASSWORD_DEMO']}</password></login>")
    assert cumple(xml, xsd("auth", "login.xsd")) == []
    resp = c.llamar("auth", "POST", P["auth"] + "/login", xml=xml, accept="application/xml")
    assert resp.status == 200
    assert resp.headers["Content-Type"].startswith("application/xml")
    assert cumple(resp.texto, xsd("auth", "tokens.xsd")) == []
    token = resp.datos.findtext("access_token")

    sesion = c.llamar("auth", "GET", P["auth"] + "/sesion", token=token,
                      accept="application/xml")
    assert sesion.status == 200
    assert cumple(sesion.texto, xsd("auth", "sesion.xsd")) == []
    c.cerrar_sesion(token)


def test_mismo_listado_en_json_y_xml_trae_el_mismo_total(ctx):
    token = ctx.h(c.ANALISTA)
    en_json = c.llamar("ventas", "GET", P["ventas"] + "?por_pagina=5", token=token)
    en_xml = c.llamar("ventas", "GET", P["ventas"] + "?por_pagina=5", token=token,
                      accept="application/xml")
    assert en_json.status == en_xml.status == 200
    assert en_xml.datos is not None and en_xml.datos.tag == "ventas"
    assert int(en_xml.datos.findtext("paginacion/total")) == en_json.datos["paginacion"]["total"]


def test_error_en_xml_sigue_el_formato_comun(ctx):
    resp = c.llamar("devoluciones", "GET", P["devoluciones"] + "/99999999",
                    token=ctx.h(c.ANALISTA), accept="application/xml")
    assert resp.status == 404 and resp.datos.tag == "error"
    assert resp.datos.findtext("tipo") == "no_encontrado"
    assert resp.datos.findtext("correlation_id") == resp.headers["X-Correlation-ID"]


def test_devolucion_creada_con_cuerpo_xml(ctx):
    xml = (f"<devolucion><venta_detalle_id>{ctx.linea['id']}</venta_detalle_id>"
           f"<motivo_id>{ctx.motivo}</motivo_id>"
           f"<descripcion_problema>{flujo.DESCRIPCION}</descripcion_problema>"
           "<cantidad_devuelta>1</cantidad_devuelta></devolucion>")
    assert cumple(xml, xsd("devoluciones", "devolucion_nueva.xsd")) == []
    resp = c.llamar("devoluciones", "POST", P["devoluciones"], xml=xml,
                    token=ctx.h(c.CLIENTE), accept="application/xml")
    assert resp.status == 201, resp.texto
    dev_id = int(resp.datos.findtext("id"))
    ctx.registrar_devolucion(dev_id)
    assert c.sql("SELECT estado FROM devoluciones WHERE id = %s", (dev_id,),
                 uno=True)["estado"] == "solicitada"

    resolucion = "<resolucion><decision>autorizar</decision></resolucion>"
    assert cumple(resolucion, xsd("devoluciones", "resolucion.xsd")) == []
    r = c.llamar("devoluciones", "PATCH", f"{P['devoluciones']}/{dev_id}/resolucion",
                 xml=resolucion, token=ctx.h(c.ANALISTA), accept="application/xml")
    assert r.status == 200 and r.datos.findtext("estado") == "autorizada"

    # Logistica por XML: el orden de los elementos lo fija el XSD (xs:sequence).
    manana = (date.today() + timedelta(days=1)).isoformat()
    rec = (f"<recoleccion><devolucion_id>{dev_id}</devolucion_id>"
           f"<fecha_programada>{manana}</fecha_programada>"
           "<lugar>Tienda de prueba XML</lugar></recoleccion>")
    assert cumple(rec, xsd("logistica", "recoleccion.xsd")) == []
    r = c.llamar("logistica", "POST", P["logistica"] + "/recolecciones", xml=rec,
                 token=ctx.h(c.COORDINADOR), accept="application/xml")
    assert r.status == 201, r.texto
    rec_id = int(r.datos.findtext("id"))
    ruta, transp = flujo.ruta_y_transportista()
    asig = f"<asignacion><ruta_id>{ruta}</ruta_id><transportista_id>{transp}</transportista_id></asignacion>"
    assert cumple(asig, xsd("logistica", "asignacion.xsd")) == []
    r = c.llamar("logistica", "PATCH", f"{P['logistica']}/recolecciones/{rec_id}/asignacion",
                 xml=asig, token=ctx.h(c.COORDINADOR), accept="application/xml")
    assert r.status == 200 and r.datos.findtext("estado") == "asignada"
    estado = "<estado_recoleccion><estado>en_transito</estado></estado_recoleccion>"
    assert cumple(estado, xsd("logistica", "estado_recoleccion.xsd")) == []
    r = c.llamar("logistica", "PATCH", f"{P['logistica']}/recolecciones/{rec_id}/estado",
                 xml=estado, token=ctx.h(c.COORDINADOR), accept="application/xml")
    assert r.status == 200

    costo = (f"<costo><devolucion_id>{dev_id}</devolucion_id><etapa>transporte</etapa>"
             "<monto>99.90</monto></costo>")
    assert cumple(costo, xsd("reembolsos_costos", "costo.xsd")) == []
    r = c.llamar("reembolsos", "POST", P["reembolsos"] + "/costos", xml=costo,
                 token=ctx.h(c.COORDINADOR), accept="application/xml")
    assert r.status == 201, r.texto


def test_xml_que_no_cumple_el_xsd_responde_400(ctx):
    sin_motivo = (f"<devolucion><venta_detalle_id>{ctx.linea['id']}</venta_detalle_id>"
                  f"<descripcion_problema>{flujo.DESCRIPCION}</descripcion_problema></devolucion>")
    assert cumple(sin_motivo, xsd("devoluciones", "devolucion_nueva.xsd")) != []
    resp = c.llamar("devoluciones", "POST", P["devoluciones"], xml=sin_motivo,
                    token=ctx.h(c.CLIENTE))
    assert resp.status == 400 and c.error_tipo(resp) == "xml_no_cumple_xsd"


def test_xml_mal_formado_responde_400(ctx):
    resp = c.llamar("devoluciones", "POST", P["devoluciones"], xml="<devolucion><x>",
                    token=ctx.h(c.CLIENTE))
    assert resp.status == 400 and c.error_tipo(resp) == "xml_invalido"


def test_xml_no_resuelve_entidades_externas(ctx):
    """Intento de XXE: el servicio no debe leer archivos del contenedor (RNF-11)."""
    xml = ('<?xml version="1.0"?><!DOCTYPE login [<!ENTITY x SYSTEM "file:///etc/passwd">]>'
           "<login><email>&x;</email><password>abc</password></login>")
    resp = c.llamar("auth", "POST", P["auth"] + "/login", xml=xml)
    assert resp.status in (400, 401)
    assert "root:" not in resp.texto


def test_pruebas_no_dejan_credenciales_en_el_repositorio():
    """RNF-16: ningun archivo de la suite contiene la contrasena de demo."""
    valor = os.environ.get("PASSWORD_DEMO", "")
    if len(valor) < 6:
        pytest.skip("PASSWORD_DEMO no definida")
    for archivo in Path(__file__).parent.glob("*.py"):
        assert valor not in archivo.read_text(encoding="utf-8"), archivo.name
