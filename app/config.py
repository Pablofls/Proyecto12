"""Configuracion de la aplicacion. Todo sale del entorno: nada de secretos en el codigo (RNF-14)."""
import os

import redis


class Config:
    SECRET_KEY = os.environ.get("FLASK_SECRET_KEY", "clave-de-desarrollo-no-usar-en-produccion")

    # PostgreSQL -- expediente transaccional (RNF-06)
    PG_HOST = os.environ.get("POSTGRES_HOST", "postgres")
    PG_PORT = os.environ.get("POSTGRES_PORT", "5432")
    PG_DB = os.environ.get("POSTGRES_DB", "devoluciones")
    PG_USER = os.environ.get("POSTGRES_USER", "devoluciones_app")
    PG_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "")

    # Redis -- sesiones, bloqueo temporal y conteo de intentos (RNF-06, RNF-12)
    REDIS_HOST = os.environ.get("REDIS_HOST", "redis")
    REDIS_PORT = int(os.environ.get("REDIS_PORT", "6379"))

    # Politica de acceso (RNF-12)
    MAX_INTENTOS_FALLIDOS = int(os.environ.get("MAX_INTENTOS_FALLIDOS", "5"))
    MINUTOS_BLOQUEO = int(os.environ.get("MINUTOS_BLOQUEO", "15"))

    # Sesion del servidor almacenada en Redis
    SESSION_TYPE = "redis"
    SESSION_PERMANENT = False
    SESSION_USE_SIGNER = True
    SESSION_KEY_PREFIX = "devoluciones:sesion:"
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    GCS_BUCKET = os.environ.get("GCS_BUCKET", "")

    @classmethod
    def session_redis(cls):
        return redis.Redis(host=cls.REDIS_HOST, port=cls.REDIS_PORT, db=0)
