"""Microservicio de autenticacion (segundo parcial).

Responsabilidad: identificar al usuario y administrar el ciclo de vida de sus
tokens. Es el unico servicio que emite JWT; los demas solo los validan con
shared/seguridad.py.

Trazabilidad: RF-01, RF-04, RNF-07, RNF-08, RNF-09, RNF-12, RNF-13, RNF-16,
RNF-23, RF-30, HU-01, UC-01.

Endpoints (todos aceptan y devuelven JSON o XML):
  POST   /api/v1/auth/login                      Emite access y refresh token
  POST   /api/v1/auth/refresh                    Nuevo access token
  POST   /api/v1/auth/logout                     Revoca el token y la sesion
  GET    /api/v1/auth/sesion                     Datos de la sesion actual
  DELETE /api/v1/auth/usuarios/<id>/sesiones     Cierra todas las sesiones de
                                                 un usuario (Administrador)
  GET    /health                                 Estado y dependencias
  GET    /docs                                   Swagger UI
  GET    /contratos/<nombre>.xsd                 Contratos XML (XSD)
"""
import os
import re
import time
import uuid
from datetime import datetime, timedelta, timezone

import jwt
from flask import Blueprint, Flask, g, request
from werkzeug.security import check_password_hash

from shared import docs, respuestas
from shared.infra import (PREFIJO, cerrar_conexion, consultar, ejecutar,
                          get_redis, ip_origen, limitar, registrar_bitacora,
                          salud_postgres, salud_redis)
from shared.respuestas import ErrorApi, leer_cuerpo, responder
from shared.seguridad import (ADMINISTRADOR, ALGORITMO, EMISOR,
                              clave_revocado, clave_sesion,
                              clave_sesiones_usuario, comprobar_en_redis,
                              decodificar, requiere_jwt, secreto)

NOMBRE = "auth"
MINUTOS_ACCESO = int(os.environ.get("JWT_MINUTOS_ACCESO", "15"))
HORAS_REFRESH = int(os.environ.get("JWT_HORAS_REFRESH", "8"))
MAX_INTENTOS = int(os.environ.get("MAX_INTENTOS_FALLIDOS", "5"))
MINUTOS_BLOQUEO = int(os.environ.get("MINUTOS_BLOQUEO", "15"))
LOGIN_POR_MINUTO = int(os.environ.get("LOGIN_MAX_POR_MINUTO", "10"))

EMAIL_VALIDO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# Contratos XSD de los cuerpos XML (seccion 6); tambien se publican en
# GET /contratos/<nombre>.xsd.
CONTRATOS = os.path.join(os.path.dirname(__file__), "contratos")

api = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


# --------------------------------------------------------------------------- #
# Emision de tokens
# --------------------------------------------------------------------------- #
def _token(usuario, sid, tipo, duracion):
    ahora = datetime.now(timezone.utc)
    claims = {
        "iss": EMISOR,
        "sub": str(usuario["id"]),
        "rol": usuario["rol"],
        "nombre": usuario["nombre"],
        "sid": sid,
        "jti": uuid.uuid4().hex,
        "typ": tipo,
        "iat": ahora,
        "exp": ahora + duracion,
    }
    return jwt.encode(claims, secreto(), algorithm=ALGORITMO)


def _abrir_sesion(usuario):
    """Crea la sesion en Redis y emite el par de tokens.

    La sesion dura lo mismo que el refresh token. Mientras exista, los access
    tokens de esa sesion son aceptados; al borrarla, todos dejan de servir.
    """
    sid = uuid.uuid4().hex
    ttl = HORAS_REFRESH * 3600
    r = get_redis()
    r.hset(clave_sesion(sid), mapping={
        "usuario_id": usuario["id"], "rol": usuario["rol"],
        "ip": ip_origen(), "creada": datetime.now(timezone.utc).isoformat(),
    })
    r.expire(clave_sesion(sid), ttl)
    r.sadd(clave_sesiones_usuario(usuario["id"]), sid)
    r.expire(clave_sesiones_usuario(usuario["id"]), ttl)
    return {
        "token_type": "Bearer",
        "access_token": _token(usuario, sid, "access",
                               timedelta(minutes=MINUTOS_ACCESO)),
        "expires_in": MINUTOS_ACCESO * 60,
        "refresh_token": _token(usuario, sid, "refresh",
                                timedelta(hours=HORAS_REFRESH)),
        "refresh_expires_in": ttl,
        "usuario": usuario,
    }


def _revocar(claims):
    """Agrega el token a la lista de revocacion hasta que expire solo."""
    restante = int(claims["exp"] - time.time())
    if restante > 0:
        get_redis().setex(clave_revocado(claims["jti"]), restante, "1")


# --------------------------------------------------------------------------- #
# Bloqueo por intentos fallidos (mismas claves que el monolito, RNF-12)
# --------------------------------------------------------------------------- #
def _clave_intentos(email):
    return f"{PREFIJO}intentos:{email}"


def _clave_bloqueo(email):
    return f"{PREFIJO}bloqueo:{email}"


def _bloqueado(usuario, email):
    if get_redis().ttl(_clave_bloqueo(email)) > 0:
        return True
    hasta = usuario and usuario.get("bloqueado_hasta")
    return bool(hasta and hasta > datetime.now(timezone.utc))


def _intento_fallido(email, usuario):
    r = get_redis()
    intentos = r.incr(_clave_intentos(email))
    if intentos == 1:
        r.expire(_clave_intentos(email), MINUTOS_BLOQUEO * 60)
    if intentos >= MAX_INTENTOS:
        hasta = datetime.now(timezone.utc) + timedelta(minutes=MINUTOS_BLOQUEO)
        r.setex(_clave_bloqueo(email), MINUTOS_BLOQUEO * 60, hasta.isoformat())
        if usuario:
            # PostgreSQL conserva el bloqueo si Redis se reinicia (RNF-21).
            ejecutar("UPDATE usuarios SET bloqueado_hasta = %s WHERE id = %s",
                     (hasta, usuario["id"]))
            registrar_bitacora("cuenta_bloqueada", "usuarios", usuario["id"],
                               f"Bloqueo temporal tras {intentos} intentos "
                               "fallidos (API)", usuario_id=usuario["id"])


def _historial(email, usuario_id, exitoso):
    ejecutar(
        """
        INSERT INTO intentos_acceso (email, usuario_id, exitoso, ip_origen,
                                     user_agent)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (email[:150], usuario_id, exitoso, ip_origen(),
         (request.user_agent.string or "")[:255]),
    )


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #
@api.post("/login")
def login():
    limitar("login", LOGIN_POR_MINUTO, 60)
    datos = leer_cuerpo(xsd=os.path.join(CONTRATOS, "login.xsd"))
    email = str(datos.get("email") or "").strip().lower()
    password = str(datos.get("password") or "")

    errores = []
    if not EMAIL_VALIDO.match(email):
        errores.append({"campo": "email", "problema": "formato invalido"})
    if not password:
        errores.append({"campo": "password", "problema": "es obligatorio"})
    if errores:
        raise ErrorApi(400, "validacion", "Datos de acceso incompletos.",
                       errores)

    usuario = consultar(
        """
        SELECT u.id, u.nombre, u.email, u.password_hash, u.estado,
               u.bloqueado_hasta, r.nombre AS rol
          FROM usuarios u
          JOIN roles r ON r.id = u.rol_id
         WHERE lower(u.email) = %s AND u.eliminado_en IS NULL
        """,
        (email,), uno=True,
    )
    usuario_id = usuario["id"] if usuario else None

    if _bloqueado(usuario, email):
        _historial(email, usuario_id, False)
        registrar_bitacora("login_bloqueado", "usuarios", usuario_id,
                           "Intento de acceso por API sobre cuenta bloqueada",
                           usuario_id=usuario_id)
        raise ErrorApi(423, "cuenta_bloqueada",
                       "La cuenta esta bloqueada temporalmente. Intenta de "
                       f"nuevo en {MINUTOS_BLOQUEO} minutos.")

    valido = (usuario is not None and usuario["estado"] == "activo"
              and check_password_hash(usuario["password_hash"], password))
    if not valido:
        _historial(email, usuario_id, False)
        _intento_fallido(email, usuario)
        # Mensaje generico: no revela si el correo existe (RNF-16).
        raise ErrorApi(401, "credenciales_invalidas",
                       "Correo o contrasena incorrectos.")

    get_redis().delete(_clave_intentos(email), _clave_bloqueo(email))
    ejecutar("UPDATE usuarios SET bloqueado_hasta = NULL WHERE id = %s",
             (usuario["id"],))
    _historial(email, usuario["id"], True)

    publico = {"id": usuario["id"], "nombre": usuario["nombre"],
               "email": usuario["email"], "rol": usuario["rol"]}
    tokens = _abrir_sesion(publico)
    g.usuario = publico
    registrar_bitacora("login_api", "usuarios", usuario["id"],
                       "Inicio de sesion por API, JWT emitido")
    return responder(tokens, 200)


@api.post("/refresh")
def refresh():
    limitar("refresh", 30, 60)
    datos = leer_cuerpo(xsd=os.path.join(CONTRATOS, "refresh.xsd"))
    token = str(datos.get("refresh_token") or "")
    if not token:
        raise ErrorApi(400, "validacion", "Falta refresh_token.",
                       [{"campo": "refresh_token", "problema": "es obligatorio"}])
    claims = decodificar(token, "refresh")
    comprobar_en_redis(claims)
    usuario = {"id": int(claims["sub"]), "rol": claims["rol"],
               "nombre": claims["nombre"]}
    return responder({
        "token_type": "Bearer",
        "access_token": _token(usuario, claims["sid"], "access",
                               timedelta(minutes=MINUTOS_ACCESO)),
        "expires_in": MINUTOS_ACCESO * 60,
    })


@api.post("/logout")
@requiere_jwt()
def logout():
    claims = g.claims
    _revocar(claims)
    r = get_redis()
    r.delete(clave_sesion(claims["sid"]))
    r.srem(clave_sesiones_usuario(g.usuario["id"]), claims["sid"])
    registrar_bitacora("logout_api", "usuarios", g.usuario["id"],
                       "Cierre de sesion por API: token y sesion revocados")
    return responder({"mensaje": "Sesion cerrada. El token ya no es valido."})


@api.get("/sesion")
@requiere_jwt()
def sesion():
    claims = g.claims
    ttl = get_redis().ttl(clave_sesion(claims["sid"]))
    return responder({
        "usuario": g.usuario,
        "sesion_id": claims["sid"],
        "sesion_expira_en_seg": ttl,
        "token_expira": datetime.fromtimestamp(
            claims["exp"], timezone.utc).isoformat(),
    })


@api.delete("/usuarios/<int:usuario_id>/sesiones")
@requiere_jwt(ADMINISTRADOR)
def cerrar_sesiones_de_usuario(usuario_id):
    """RNF-08: al cambiar contrasena o perder permisos, sus tokens dejan de
    servir de inmediato, sin esperar a que expiren."""
    existe = consultar("SELECT id FROM usuarios WHERE id = %s", (usuario_id,),
                       uno=True)
    if not existe:
        raise ErrorApi(404, "no_encontrado",
                       f"No existe el usuario {usuario_id}.")
    r = get_redis()
    clave = clave_sesiones_usuario(usuario_id)
    sesiones = list(r.smembers(clave))
    if sesiones:
        r.delete(*[clave_sesion(s) for s in sesiones])
    r.delete(clave)
    registrar_bitacora("revocar_sesiones", "usuarios", usuario_id,
                       f"El administrador cerro {len(sesiones)} sesion(es)")
    return responder({"usuario_id": usuario_id,
                      "sesiones_cerradas": len(sesiones)})


# --------------------------------------------------------------------------- #
# Aplicacion
# --------------------------------------------------------------------------- #
def create_app():
    secreto()  # Falla al arrancar si JWT_SECRET no esta bien definido.
    app = Flask(__name__)
    app.json.sort_keys = False
    respuestas.registrar(app, NOMBRE)
    app.teardown_appcontext(cerrar_conexion)
    app.register_blueprint(api)
    docs.registrar(app, os.path.join(os.path.dirname(__file__),
                                     "openapi.yaml"))

    @app.get("/health")
    def health():
        """RNF-22, RF-32: estado del servicio y de sus dependencias."""
        deps = {"postgresql": salud_postgres(), "redis": salud_redis()}
        ok = all(d["ok"] for d in deps.values())
        return responder({"servicio": NOMBRE, "version": "v1",
                          "estado": "ok" if ok else "degradado",
                          "dependencias": deps}, 200 if ok else 503)

    return app

