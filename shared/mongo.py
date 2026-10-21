"""Acceso a MongoDB para los servicios que lo usan (seccion 5.4, RNF-06).

Va separado de infra.py para que los servicios sin MongoDB (auth, catalogos)
no necesiten instalar pymongo. Quien lo use agrega a su requirements.txt:
    pymongo==4.8.0

PostgreSQL guarda el expediente y las relaciones; MongoDB guarda el detalle
semiestructurado (inspecciones, metadatos de evidencias, eventos, resultados
de analisis). El enlace es un id de PostgreSQL dentro del documento
(devolucion_id) y, en sentido contrario, inspecciones_ref.mongo_doc_id.
"""
import logging
import os
from datetime import datetime, timezone

from bson import ObjectId
from bson.errors import InvalidId
from flask import g
from pymongo import MongoClient

from shared.respuestas import ErrorApi

log = logging.getLogger("servicio")
_cliente = None


def get_mongo():
    """Base de datos de la aplicacion, con el usuario de minimo privilegio."""
    global _cliente
    if _cliente is None:
        _cliente = MongoClient(
            host=os.environ.get("MONGO_HOST", "mongo"),
            port=int(os.environ.get("MONGO_PORT", "27017")),
            username=os.environ.get("MONGO_APP_USER"),
            password=os.environ.get("MONGO_APP_PASSWORD"),
            # init.js crea el usuario dentro de la base de la aplicacion.
            authSource=os.environ.get("MONGO_DB", "devoluciones"),
            serverSelectionTimeoutMS=3000,
            tz_aware=True,
        )
    return _cliente[os.environ.get("MONGO_DB", "devoluciones")]


def id_objeto(texto):
    """Convierte el id de la URL; un id mal formado es un 404, no un 500."""
    try:
        return ObjectId(texto)
    except (InvalidId, TypeError):
        raise ErrorApi(404, "no_encontrado", f"No existe el documento {texto}.")


def a_json(doc):
    """Documento de Mongo listo para responder() en JSON o XML."""
    if isinstance(doc, list):
        return [a_json(d) for d in doc]
    if isinstance(doc, dict):
        return {("id" if k == "_id" else k): a_json(v) for k, v in doc.items()}
    if isinstance(doc, ObjectId):
        return str(doc)
    if isinstance(doc, datetime):
        return doc.isoformat()
    return doc


def registrar_evento(servicio, tipo, datos=None):
    """Publica un evento en la coleccion 'eventos' (RNF-23).

    Con el correlation_id se reconstruye una operacion que paso por varios
    servicios. Un fallo aqui no debe tumbar la operacion de negocio, que ya
    quedo guardada en PostgreSQL: se registra en el log y se sigue.
    """
    try:
        get_mongo().eventos.insert_one({
            "servicio": servicio,
            "tipo": tipo,
            "datos": datos or {},
            "usuario_id": (g.get("usuario") or {}).get("id"),
            "correlation_id": g.get("correlation_id"),
            "fecha": datetime.now(timezone.utc),
        })
    except Exception:
        log.exception("No se pudo registrar el evento %s", tipo)


def salud_mongo():
    try:
        get_mongo().command("ping")
        return {"ok": True, "error": None}
    except Exception:
        log.exception("Dependencia mongodb no responde")
        return {"ok": False, "error": "no responde"}
