"""Validacion de mensajes XML contra su esquema XSD (seccion 6 del parcial).

Cada servicio guarda sus contratos en services/<servicio>/contratos/*.xsd; el
del error estandar vive en shared/contratos/error.xsd. Requiere lxml (la
biblioteca estandar de Python no valida XSD):
    lxml==5.3.0

Uso en un endpoint:
    datos = leer_cuerpo(xsd=os.path.join(CONTRATOS, "login.xsd"))
"""
from functools import lru_cache

from lxml import etree

from shared.respuestas import ErrorApi

# Sin entidades externas ni red: un XML de un cliente no debe poder leer
# archivos del contenedor ni hacer peticiones (XXE).
_PARSER = etree.XMLParser(resolve_entities=False, no_network=True,
                          load_dtd=False, huge_tree=False)


@lru_cache(maxsize=None)
def esquema(ruta):
    return etree.XMLSchema(etree.parse(ruta))


def errores(documento, ruta):
    """Lista de problemas del documento frente al XSD; vacia si cumple."""
    xsd = esquema(ruta)
    arbol = etree.fromstring(documento, _PARSER)
    if xsd.validate(arbol):
        return []
    return [{"linea": e.line, "problema": e.message} for e in xsd.error_log]


def exigir(documento, ruta):
    problemas = errores(documento, ruta)
    if problemas:
        raise ErrorApi(400, "xml_no_cumple_xsd",
                       "El XML no cumple el contrato del endpoint.", problemas)
