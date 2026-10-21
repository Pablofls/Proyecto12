"""Acceso a PostgreSQL.

Todas las consultas usan parametros ligados; nunca se concatena entrada del
usuario dentro de una sentencia SQL (RNF-11, proteccion contra inyeccion).
"""
from flask import current_app, g
import psycopg2
import psycopg2.extras


def get_conn():
    if "conn" not in g:
        cfg = current_app.config
        g.conn = psycopg2.connect(
            host=cfg["PG_HOST"],
            port=cfg["PG_PORT"],
            dbname=cfg["PG_DB"],
            user=cfg["PG_USER"],
            password=cfg["PG_PASSWORD"],
            cursor_factory=psycopg2.extras.RealDictCursor,
        )
    return g.conn


def cerrar_conn(exc=None):
    conn = g.pop("conn", None)
    if conn is not None:
        if exc is None:
            conn.commit()
        else:
            conn.rollback()
        conn.close()


def consultar(sql, params=None, uno=False):
    """SELECT. Devuelve una lista de dicts, o un dict / None si uno=True."""
    with get_conn().cursor() as cur:
        cur.execute(sql, params or ())
        return cur.fetchone() if uno else cur.fetchall()


def ejecutar(sql, params=None, devolver=False):
    """INSERT / UPDATE / DELETE. Con devolver=True espera un RETURNING."""
    with get_conn().cursor() as cur:
        cur.execute(sql, params or ())
        return cur.fetchone() if devolver else None


def salud():
    """Comprobacion de la dependencia para el endpoint de salud (RNF-22)."""
    try:
        with get_conn().cursor() as cur:
            cur.execute("SELECT 1 AS ok")
            cur.fetchone()
        return True, None
    except Exception as exc:
        return False, str(exc)
