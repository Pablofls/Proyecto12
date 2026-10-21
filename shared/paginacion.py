"""Paginacion comun para los listados de todos los servicios.

Contrato (igual en JSON y XML):
    GET /api/v1/...?pagina=2&por_pagina=20
    {"datos": [...],
     "paginacion": {"pagina": 2, "por_pagina": 20, "total": 57, "paginas": 3}}

En PostgreSQL:
    pag = leer_paginacion()
    filas = consultar("SELECT ... ORDER BY id LIMIT %s OFFSET %s",
                      (pag.limite, pag.desplazamiento))
    total = consultar("SELECT count(*) AS n FROM ...", uno=True)["n"]
    return responder(paginar(filas, total, pag))

En MongoDB: .skip(pag.desplazamiento).limit(pag.limite) y count_documents().
"""
from collections import namedtuple

from flask import request

from shared.respuestas import ErrorApi

MAXIMO_POR_PAGINA = 100

Paginacion = namedtuple("Paginacion", "pagina por_pagina limite desplazamiento")


def _entero(nombre, defecto, minimo, maximo):
    texto = request.args.get(nombre)
    if texto is None:
        return defecto
    try:
        valor = int(texto)
    except ValueError:
        valor = None
    if valor is None or not minimo <= valor <= maximo:
        raise ErrorApi(400, "validacion", "Parametro de paginacion invalido.",
                       [{"campo": nombre,
                         "problema": f"debe ser un entero entre {minimo} y {maximo}"}])
    return valor


def leer_paginacion(por_pagina_defecto=20):
    pagina = _entero("pagina", 1, 1, 100000)
    por_pagina = _entero("por_pagina", por_pagina_defecto, 1, MAXIMO_POR_PAGINA)
    return Paginacion(pagina, por_pagina, por_pagina,
                      (pagina - 1) * por_pagina)


def paginar(datos, total, pag):
    return {
        "datos": list(datos),
        "paginacion": {
            "pagina": pag.pagina,
            "por_pagina": pag.por_pagina,
            "total": total,
            "paginas": (total + pag.por_pagina - 1) // pag.por_pagina,
        },
    }
