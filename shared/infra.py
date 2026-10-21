"""Conexiones a PostgreSQL y Redis, bitacora y limitacion de peticiones.

Mismas reglas que el monolito: SQL con parametros ligados, nunca concatenado
(RNF-11), y toda configuracion desde variables de entorno (RNF-14).
"""
import logging
import os

import psycopg2
import psycopg2.extras
import redis
from flask import g, request

from shared.respuestas import ErrorApi

log = logging.getLogger("servicio")

PREFIJO = "devoluciones:"
_redis = None


# --------------------------------------------------------------------------- #
# PostgreSQL
# --------------------------------------------------------------------------- #
def _conexion():
    if "pg" not in g:
        g.pg = psycopg2.connect(
            host=os.environ.get("POSTGRES_HOST", "postgres"),
            port=os.environ.get("POSTGRES_PORT", "5432"),
            dbname=os.environ.get("POSTGRES_DB", "devoluciones"),
            user=os.environ.get("POSTGRES_USER", "devoluciones_app"),
            password=os.environ.get("POSTGRES_PASSWORD", ""),
            cursor_factory=psycopg2.extras.RealDictCursor,
            connect_timeout=5,
        )
    return g.pg


def cerrar_conexion(exc=None):
    conn = g.pop("pg", None)
    if conn is not None:
        # El manejador de errores atrapa las excepciones no controladas, asi
        # que aqui llegan con exc=None; respuestas.py marca g.error_interno
        # para que un 500 no confirme cambios a medias.
        if exc is None and not g.get("error_interno"):
            conn.commit()
        else:
            conn.rollback()
        conn.close()


def consultar(sql, params=None, uno=False):
    with _conexion().cursor() as cur:
        cur.execute(sql, params or ())
        return cur.fetchone() if uno else cur.fetchall()


def ejecutar(sql, params=None, devolver=False):
    with _conexion().cursor() as cur:
        cur.execute(sql, params or ())
        return cur.fetchone() if devolver else None


# --------------------------------------------------------------------------- #
# Redis
# --------------------------------------------------------------------------- #
def get_redis():
    global _redis
    if _redis is None:
        _redis = redis.Redis(
            host=os.environ.get("REDIS_HOST", "redis"),
            port=int(os.environ.get("REDIS_PORT", "6379")),
            db=0, decode_responses=True, socket_timeout=3,
        )
    return _redis


def limitar(recurso, maximo, ventana_seg, sujeto=None):
    """Rate limiting por ventana fija (RNF-13).

    Clave: devoluciones:limite:<sujeto>:<recurso>, con TTL = ventana.
    El sujeto es el usuario autenticado o, si no hay, la IP de origen.
    """
    sujeto = sujeto or ip_origen()
    clave = f"{PREFIJO}limite:{sujeto}:{recurso}"
    r = get_redis()
    cuenta = r.incr(clave)
    if cuenta == 1:
        r.expire(clave, ventana_seg)
    if cuenta > maximo:
        espera = max(r.ttl(clave), 1)
        raise ErrorApi(429, "demasiadas_peticiones",
                       f"Limite de {maximo} peticiones en {ventana_seg} s. "
                       f"Intenta de nuevo en {espera} s.",
                       headers={"Retry-After": str(espera)})


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #
def ip_origen():
    # No se lee X-Forwarded-For: no hay proxy delante de los servicios y el
    # cliente podria inventar ese header para saltarse el rate limit (RNF-13).
    return request.remote_addr or "-"


def registrar_bitacora(accion, entidad, entidad_id=None, detalle=None,
                       usuario_id=None):
    """Bitacora de auditoria compartida con el monolito (RF-30, RN-12).

    Nunca recibe contrasenas ni tokens en 'detalle' (RNF-16).
    """
    if usuario_id is None:
        usuario_id = (g.get("usuario") or {}).get("id")
    ejecutar(
        """
        INSERT INTO bitacora (usuario_id, accion, entidad, entidad_id, detalle,
                              correlation_id, ip_origen)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (usuario_id, accion, entidad, entidad_id, detalle,
         g.get("correlation_id"), ip_origen()),
    )


def _salud(nombre, prueba):
    # El detalle de la excepcion (host, usuario) va al log, no al cliente
    # (RNF-16): /health es publico.
    try:
        prueba()
        return {"ok": True, "error": None}
    except Exception:
        log.exception("Dependencia %s no responde", nombre)
        return {"ok": False, "error": "no responde"}


def salud_postgres():
    return _salud("postgresql", lambda: consultar("SELECT 1 AS ok", uno=True))


def salud_redis():
    return _salud("redis", lambda: get_redis().ping())
