"""Autenticacion y autorizacion comun a todos los microservicios.

Cada peticion protegida pasa por las mismas comprobaciones (seccion 5.1 y 6.3
del documento; RNF-08, RNF-09):
  1. Header 'Authorization: Bearer <token>' presente.
  2. Firma, emisor y vigencia del JWT validos.
  3. El token no esta revocado:   devoluciones:jwt_revocado:<jti>
  4. La sesion sigue activa:       devoluciones:sesion_api:<sid>
  5. El rol tiene permiso sobre el endpoint.

Si Redis no responde, se niega el acceso (falla cerrada): sin poder consultar
la revocacion no hay forma de saber si el token sigue siendo valido.
"""
import os
from functools import wraps

import jwt
from flask import g, request

from shared.infra import PREFIJO, get_redis
from shared.respuestas import ErrorApi

ALGORITMO = "HS256"
EMISOR = "devoluciones-auth"

# Nombres identicos al catalogo de roles (migracion 001) y a apps/web/app/security.py.
CLIENTE = "Cliente"
INSPECTOR = "Inspector"
ENCARGADO_CENTRO = "Encargado del Centro de Devoluciones"
COORDINADOR = "Coordinador de Logistica"
ANALISTA = "Analista de Devoluciones"
ENCARGADO_REEMBOLSOS = "Encargado de Reembolsos"
ADMINISTRADOR = "Administrador"
# Tercer parcial (migracion 014): perfiles de la aplicacion Android.
RECOLECTOR = "Recolector"
OPERADOR_ALMACEN = "Operador de Almacen"
SUPERVISOR = "Supervisor"

# requiere_jwt() sin roles acepta solo ROLES_BASE: un rol nuevo no hereda acceso
# a los endpoints que ya existian; cada servicio lo autoriza nombrandolo (RN-13).
ROLES_BASE = (CLIENTE, INSPECTOR, ENCARGADO_CENTRO, COORDINADOR, ANALISTA,
              ENCARGADO_REEMBOLSOS, ADMINISTRADOR)
ROLES_CAMPO = (RECOLECTOR, OPERADOR_ALMACEN, SUPERVISOR)
TODOS_LOS_ROLES = ROLES_BASE + ROLES_CAMPO

# Operaciones que exigen confirmar la contrasena antes de ejecutarse, y los
# roles que pueden pedir esa confirmacion. El servicio que ejecuta la operacion
# llama a exigir_autorizacion_operacion(); auth emite el permiso en
# POST /api/v1/auth/autorizar-operacion.
OPERACIONES_CRITICAS = {
    "aprobar_reembolso": (ENCARGADO_REEMBOLSOS,),
    "aprobar_disposicion": (ANALISTA, SUPERVISOR),
    "reincorporar_inventario": (ENCARGADO_CENTRO, SUPERVISOR),
    "cerrar_investigacion": (SUPERVISOR,),
}
HEADER_OPERACION = "X-Autorizacion-Operacion"
MINUTOS_OPERACION = 5


def secreto():
    valor = os.environ.get("JWT_SECRET", "")
    if len(valor) < 32:
        # Un secreto corto o vacio permitiria falsificar tokens: mejor no
        # arrancar que arrancar inseguro (RNF-14).
        raise RuntimeError("JWT_SECRET debe definirse en el .env con al "
                           "menos 32 caracteres.")
    return valor


def clave_revocado(jti):
    return f"{PREFIJO}jwt_revocado:{jti}"


def clave_sesion(sid):
    return f"{PREFIJO}sesion_api:{sid}"


def clave_sesiones_usuario(usuario_id):
    return f"{PREFIJO}sesiones_usuario:{usuario_id}"


def clave_operacion(jti):
    return f"{PREFIJO}operacion_autorizada:{jti}"


def decodificar(token, tipo_esperado="access"):
    try:
        claims = jwt.decode(
            token, secreto(), algorithms=[ALGORITMO], issuer=EMISOR,
            options={"require": ["exp", "iat", "sub", "jti", "sid", "typ"]},
        )
    except jwt.ExpiredSignatureError:
        raise ErrorApi(401, "token_expirado",
                       "El token expiro. Renuevalo o inicia sesion de nuevo.")
    except jwt.InvalidTokenError:
        raise ErrorApi(401, "token_invalido", "El token no es valido.")
    if claims.get("typ") != tipo_esperado:
        raise ErrorApi(401, "token_invalido",
                       f"Se esperaba un token de tipo '{tipo_esperado}'.")
    return claims


def comprobar_en_redis(claims):
    try:
        r = get_redis()
        revocado = r.exists(clave_revocado(claims["jti"]))
        sesion_activa = r.exists(clave_sesion(claims["sid"]))
    except Exception:
        raise ErrorApi(503, "seguridad_no_disponible",
                       "No se pudo verificar la sesion. Intenta mas tarde.")
    if revocado:
        raise ErrorApi(401, "token_revocado",
                       "El token fue revocado. Inicia sesion de nuevo.")
    if not sesion_activa:
        raise ErrorApi(401, "sesion_inactiva",
                       "La sesion ya no esta activa. Inicia sesion de nuevo.")


def token_de_la_peticion():
    cabecera = request.headers.get("Authorization", "")
    tipo, _, token = cabecera.partition(" ")
    if tipo.lower() != "bearer" or not token.strip():
        raise ErrorApi(401, "no_autenticado",
                       "Falta el header 'Authorization: Bearer <token>'.")
    return token.strip()


def requiere_jwt(*roles):
    """Protege un endpoint. Sin roles acepta los ROLES_BASE; los roles de campo
    (y cualquiera que se agregue despues) deben nombrarse explicitamente."""
    permitidos = roles or ROLES_BASE

    def decorador(vista):
        @wraps(vista)
        def envoltura(*args, **kwargs):
            claims = decodificar(token_de_la_peticion(), "access")
            comprobar_en_redis(claims)
            g.claims = claims
            g.usuario = {"id": int(claims["sub"]), "rol": claims.get("rol"),
                         "nombre": claims.get("nombre"),
                         # None: sin sucursal asignada, opera en todas.
                         "tienda_id": claims.get("tienda_id")}
            if g.usuario["rol"] not in permitidos:
                raise ErrorApi(403, "sin_permiso",
                               "Tu rol no tiene permiso para esta operacion.",
                               {"rol": g.usuario["rol"],
                                "roles_permitidos": list(permitidos)})
            return vista(*args, **kwargs)
        return envoltura
    return decorador


# --------------------------------------------------------------------------- #
# Control por sucursal
# --------------------------------------------------------------------------- #
def condicion_tienda(columna):
    """Filtro SQL para listados: (condicion, parametros), o (None, ()) si el
    usuario no tiene sucursal. `columna` la escribe el servicio, nunca viene
    de la peticion; el valor va como parametro ligado (RNF-11)."""
    tienda = g.usuario.get("tienda_id")
    if tienda is None:
        return None, ()
    return f"{columna} = %s", (tienda,)


def exigir_tienda(tienda_id):
    """Un usuario con sucursal solo opera registros de su tienda. Quien llama
    decide si deja constancia en la bitacora."""
    propia = g.usuario.get("tienda_id")
    if propia is not None and tienda_id != propia:
        raise ErrorApi(403, "fuera_de_sucursal",
                       "El registro pertenece a otra sucursal.",
                       {"tienda_usuario": propia, "tienda_registro": tienda_id})


# --------------------------------------------------------------------------- #
# Operaciones criticas
# --------------------------------------------------------------------------- #
def exigir_autorizacion_operacion(operacion, recurso_id):
    """Consume el permiso que emite auth tras confirmar la contrasena.

    El permiso viaja en el header X-Autorizacion-Operacion, vale para una sola
    operacion sobre un solo registro, dentro de la misma sesion, durante 5
    minutos, y se borra de Redis al usarse: un segundo intento (doble clic o
    peticiones simultaneas) recibe 403. Llamar despues de @requiere_jwt.
    """
    if g.usuario["rol"] not in OPERACIONES_CRITICAS.get(operacion, ()):
        raise ErrorApi(403, "sin_permiso",
                       "Tu rol no puede autorizar esta operacion.",
                       {"rol": g.usuario["rol"], "operacion": operacion})
    token = request.headers.get(HEADER_OPERACION, "").strip()
    if not token:
        raise ErrorApi(403, "autorizacion_operacion_requerida",
                       "Esta operacion requiere confirmar tu contrasena en "
                       "POST /api/v1/auth/autorizar-operacion.",
                       {"operacion": operacion, "recurso_id": str(recurso_id),
                        "header": HEADER_OPERACION})
    try:
        claims = decodificar(token, "operacion")
    except ErrorApi:
        raise ErrorApi(403, "autorizacion_operacion_invalida",
                       "La autorizacion no es valida o ya expiro. Confirma "
                       "tu contrasena de nuevo.")
    if (claims["sub"] != str(g.usuario["id"]) or claims["sid"] != g.claims["sid"]
            or claims.get("op") != operacion or claims.get("recurso") != str(recurso_id)):
        raise ErrorApi(403, "autorizacion_operacion_invalida",
                       "La autorizacion corresponde a otra operacion, registro "
                       "o sesion.")
    try:
        # DELETE es atomico: de dos peticiones simultaneas solo una obtiene 1.
        consumida = get_redis().delete(clave_operacion(claims["jti"]))
    except Exception:
        raise ErrorApi(503, "seguridad_no_disponible",
                       "No se pudo verificar la autorizacion. Intenta mas tarde.")
    if not consumida:
        raise ErrorApi(403, "autorizacion_operacion_usada",
                       "La autorizacion ya se uso. Confirma tu contrasena de nuevo.")
    return claims
