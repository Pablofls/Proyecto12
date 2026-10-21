"""Acceso a Redis: intentos fallidos, bloqueo temporal y limitacion de peticiones."""
from datetime import datetime, timedelta, timezone

from flask import current_app
import redis

_cliente = None


def get_redis():
    global _cliente
    if _cliente is None:
        _cliente = redis.Redis(
            host=current_app.config["REDIS_HOST"],
            port=current_app.config["REDIS_PORT"],
            db=0,
            decode_responses=True,
        )
    return _cliente


def _clave_intentos(email):
    return f"devoluciones:intentos:{email.lower()}"


def _clave_bloqueo(email):
    return f"devoluciones:bloqueo:{email.lower()}"


def registrar_intento_fallido(email):
    """Suma un intento fallido y bloquea si se supero el limite (RNF-12).

    Devuelve (bloqueado, intentos_actuales).
    """
    cfg = current_app.config
    r = get_redis()
    clave = _clave_intentos(email)
    intentos = r.incr(clave)
    if intentos == 1:
        r.expire(clave, cfg["MINUTOS_BLOQUEO"] * 60)

    if intentos >= cfg["MAX_INTENTOS_FALLIDOS"]:
        hasta = datetime.now(timezone.utc) + timedelta(minutes=cfg["MINUTOS_BLOQUEO"])
        r.setex(_clave_bloqueo(email), cfg["MINUTOS_BLOQUEO"] * 60, hasta.isoformat())
        return True, intentos
    return False, intentos


def limpiar_intentos(email):
    r = get_redis()
    r.delete(_clave_intentos(email), _clave_bloqueo(email))


def segundos_bloqueo_restantes(email):
    """0 si la cuenta no esta bloqueada en Redis."""
    ttl = get_redis().ttl(_clave_bloqueo(email))
    return ttl if ttl and ttl > 0 else 0


def salud():
    """Comprobacion de la dependencia para el endpoint de salud (RNF-22)."""
    try:
        get_redis().ping()
        return True, None
    except Exception as exc:
        return False, str(exc)
