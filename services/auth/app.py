"""Microservicio de autenticacion (segundo parcial).

Responsabilidad: identificar al usuario y administrar el ciclo de vida de sus
tokens. Es el unico servicio que emite JWT; los demas solo los validan con
shared/seguridad.py.

Trazabilidad: RF-01, RF-04, RN-13, RNF-07, RNF-08, RNF-09, RNF-12, RNF-13, RNF-16,
RNF-23, RF-30, HU-01, UC-01.

Endpoints (todos aceptan y devuelven JSON o XML):
  POST   /api/v1/auth/login                      Emite access y refresh token
  POST   /api/v1/auth/refresh                    Nuevo access token
  POST   /api/v1/auth/logout                     Revoca el token y la sesion
  GET    /api/v1/auth/sesion                     Datos de la sesion actual
  DELETE /api/v1/auth/usuarios/<id>/sesiones     Cierra todas las sesiones de
                                                 un usuario (Administrador)
  POST   /api/v1/auth/autorizar-operacion        Confirma la contrasena y emite
                                                 un permiso de un solo uso para
                                                 una operacion critica
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
                              HEADER_OPERACION, MINUTOS_OPERACION,
                              OPERACIONES_CRITICAS, TODOS_LOS_ROLES,
                              clave_operacion, clave_revocado, clave_sesion,
                              clave_sesiones_usuario, comprobar_en_redis,
                              decodificar, requiere_jwt, secreto)

NOMBRE = "auth"
MINUTOS_ACCESO = int(os.environ.get("JWT_MINUTOS_ACCESO", "15"))
HORAS_REFRESH = int(os.environ.get("JWT_HORAS_REFRESH", "8"))
MAX_INTENTOS = int(os.environ.get("MAX_INTENTOS_FALLIDOS", "5"))
MINUTOS_BLOQUEO = int(os.environ.get("MINUTOS_BLOQUEO", "15"))
LOGIN_POR_MINUTO = int(os.environ.get("LOGIN_MAX_POR_MINUTO", "10"))

EMAIL_VALIDO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
# Identificador del registro sobre el que se autoriza una operacion: entero de
# PostgreSQL u ObjectId de MongoDB.
RECURSO_VALIDO = re.compile(r"^[A-Za-z0-9_-]{1,64}$")
# Contratos XSD de los cuerpos XML (seccion 6); tambien se publican en
# GET /contratos/<nombre>.xsd.
CONTRATOS = os.path.join(os.path.dirname(__file__), "contratos")

api = Blueprint("auth", __name__, url_prefix="/api/v1/auth")


# --------------------------------------------------------------------------- #
# Emision de tokens
# --------------------------------------------------------------------------- #
def _token(usuario, sid, tipo, duracion, **extra):
    ahora = datetime.now(timezone.utc)
    claims = {
        "iss": EMISOR,
        "sub": str(usuario["id"]),
        "rol": usuario["rol"],
        "nombre": usuario["nombre"],
        # Sucursal del usuario; None si opera en todas (control por sucursal).
        "tienda_id": usuario.get("tienda_id"),
        "sid": sid,
        "jti": uuid.uuid4().hex,
        "typ": tipo,
        "iat": ahora,
        "exp": ahora + duracion,
        **extra,
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
               u.bloqueado_hasta, u.tienda_id, r.nombre AS rol
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
               "email": usuario["email"], "rol": usuario["rol"],
               "tienda_id": usuario.get("tienda_id")}
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
               "nombre": claims["nombre"], "tienda_id": claims.get("tienda_id")}
    return responder({
        "token_type": "Bearer",
        "access_token": _token(usuario, claims["sid"], "access",
                               timedelta(minutes=MINUTOS_ACCESO)),
        "expires_in": MINUTOS_ACCESO * 60,
    })


@api.post("/logout")
@requiere_jwt(*TODOS_LOS_ROLES)
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
@requiere_jwt(*TODOS_LOS_ROLES)
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


@api.post("/autorizar-operacion")
@requiere_jwt(*TODOS_LOS_ROLES)
def autorizar_operacion():
    """Reconfirmacion de contrasena para operaciones criticas (RN-13, RNF-09).

    Emite un permiso (JWT de tipo "operacion") valido para una sola operacion
    sobre un solo registro, dentro de la sesion actual, por 5 minutos. El
    servicio que ejecuta la operacion lo consume con
    shared.seguridad.exigir_autorizacion_operacion(); al consumirse se borra de
    Redis, asi que no puede usarse dos veces.
    """
    limitar("autorizar_operacion", 10, 60, sujeto=f"usuario{g.usuario['id']}")
    datos = leer_cuerpo(xsd=os.path.join(CONTRATOS, "autorizar_operacion.xsd"))
    operacion = str(datos.get("operacion") or "").strip()
    recurso_id = str(datos.get("recurso_id") or "").strip()
    password = str(datos.get("password") or "")

    errores = []
    if operacion not in OPERACIONES_CRITICAS:
        errores.append({"campo": "operacion",
                        "problema": "debe ser una de: " + ", ".join(OPERACIONES_CRITICAS)})
    if not RECURSO_VALIDO.match(recurso_id):
        errores.append({"campo": "recurso_id",
                        "problema": "letras, numeros, guion o guion bajo (maximo 64)"})
    if not password:
        errores.append({"campo": "password", "problema": "es obligatorio"})
    if errores:
        raise ErrorApi(400, "validacion", "Datos de la autorizacion incompletos.",
                       errores)
    if g.usuario["rol"] not in OPERACIONES_CRITICAS[operacion]:
        raise ErrorApi(403, "sin_permiso",
                       "Tu rol no puede autorizar esta operacion.",
                       {"rol": g.usuario["rol"], "operacion": operacion,
                        "roles_permitidos": list(OPERACIONES_CRITICAS[operacion])})

    usuario = consultar(
        """
        SELECT u.id, u.email, u.password_hash, u.estado, u.bloqueado_hasta
          FROM usuarios u
         WHERE u.id = %s AND u.eliminado_en IS NULL
        """,
        (g.usuario["id"],), uno=True,
    )
    if usuario is None or usuario["estado"] != "activo":
        raise ErrorApi(401, "sesion_inactiva",
                       "La cuenta ya no esta activa. Inicia sesion de nuevo.")
    email = usuario["email"].lower()
    if _bloqueado(usuario, email):
        raise ErrorApi(423, "cuenta_bloqueada",
                       "La cuenta esta bloqueada temporalmente. Intenta de "
                       f"nuevo en {MINUTOS_BLOQUEO} minutos.")
    if not check_password_hash(usuario["password_hash"], password):
        # Cuenta para el bloqueo igual que un login fallido (RNF-12).
        _historial(email, usuario["id"], False)
        _intento_fallido(email, usuario)
        registrar_bitacora("autorizacion_rechazada", "usuarios", usuario["id"],
                           f"Contrasena incorrecta al autorizar {operacion} "
                           f"sobre {recurso_id}")
        raise ErrorApi(401, "credenciales_invalidas", "Contrasena incorrecta.")

    permiso = _token(g.usuario, g.claims["sid"], "operacion",
                     timedelta(minutes=MINUTOS_OPERACION),
                     op=operacion, recurso=recurso_id)
    jti = decodificar(permiso, "operacion")["jti"]
    get_redis().setex(clave_operacion(jti), MINUTOS_OPERACION * 60, operacion)
    registrar_bitacora("autorizacion_operacion", "usuarios", usuario["id"],
                       f"Autorizo {operacion} sobre {recurso_id}")
    return responder({
        "token_operacion": permiso,
        "expires_in": MINUTOS_OPERACION * 60,
        "operacion": operacion,
        "recurso_id": recurso_id,
        "header": HEADER_OPERACION,
    }, 201)


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

