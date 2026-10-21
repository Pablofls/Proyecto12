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

    # En esta rama el web actua como cliente de las API. El interruptor permite
    # volver temporalmente al monolito durante una contingencia sin tocar el
    # codigo ni perder la version estable que vive en otra rama.
    USE_MICROSERVICES = os.environ.get("USE_MICROSERVICES", "true").lower() in (
        "1", "true", "yes", "si",
    )
    MICROSERVICE_TIMEOUT = float(os.environ.get("MICROSERVICE_TIMEOUT", "5"))
    SERVICE_URLS = {
        "auth": os.environ.get("AUTH_SERVICE_URL", "http://auth:8000"),
        "devoluciones": os.environ.get("DEVOLUCIONES_SERVICE_URL", "http://devoluciones:8000"),
        "logistica": os.environ.get("LOGISTICA_SERVICE_URL", "http://logistica:8000"),
        "inspecciones": os.environ.get("INSPECCIONES_SERVICE_URL", "http://inspecciones:8000"),
        "reembolsos": os.environ.get("REEMBOLSOS_SERVICE_URL", "http://reembolsos-costos:8000"),
        "ventas": os.environ.get("VENTAS_SERVICE_URL", "http://ventas-catalogos:8000"),
        "evidencias": os.environ.get("EVIDENCIAS_SERVICE_URL", "http://evidencias:8000"),
        "analisis": os.environ.get("ANALISIS_SERVICE_URL", "http://analisis-auditoria:8000"),
    }

    # Jinja compila las plantillas una vez y las guarda en memoria. Bajo gunicorn
    # eso significa que editar una plantilla no surte efecto hasta reiniciar el
    # contenedor, lo cual confunde durante el desarrollo. Con FLASK_ENV=development
    # se recargan al vuelo; en produccion se deja la cache, que es mas rapida.
    TEMPLATES_AUTO_RELOAD = os.environ.get("FLASK_ENV", "") == "development"

    @classmethod
    def session_redis(cls):
        return redis.Redis(host=cls.REDIS_HOST, port=cls.REDIS_PORT, db=0)
