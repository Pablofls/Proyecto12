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

# Nombres identicos al catalogo de roles (migracion 001) y a app/security.py.
CLIENTE = "Cliente"
INSPECTOR = "Inspector"
ENCARGADO_CENTRO = "Encargado del Centro de Devoluciones"
COORDINADOR = "Coordinador de Logistica"
ANALISTA = "Analista de Devoluciones"
ENCARGADO_REEMBOLSOS = "Encargado de Reembolsos"
ADMINISTRADOR = "Administrador"


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
    """Protege un endpoint. Sin roles: basta con estar autenticado."""
    def decorador(vista):
        @wraps(vista)
        def envoltura(*args, **kwargs):
            claims = decodificar(token_de_la_peticion(), "access")
            comprobar_en_redis(claims)
            g.claims = claims
            g.usuario = {"id": int(claims["sub"]), "rol": claims.get("rol"),
                         "nombre": claims.get("nombre")}
            if roles and g.usuario["rol"] not in roles:
                raise ErrorApi(403, "sin_permiso",
                               "Tu rol no tiene permiso para esta operacion.",
                               {"rol": g.usuario["rol"],
                                "roles_permitidos": list(roles)})
            return vista(*args, **kwargs)
        return envoltura
    return decorador
