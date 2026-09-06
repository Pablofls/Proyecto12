"""Autenticacion, control de acceso y bitacora de auditoria.

Implementa RNF-09 (verificacion de rol y permisos antes de cada operacion),
la autorizacion por recurso descrita en 5.3 y RF-30 / RN-12 (bitacora).
"""
import uuid
from functools import wraps

from flask import abort, flash, g, redirect, request, session, url_for

from app.db import consultar, ejecutar

# Nombres tal como se insertan en el catalogo de roles (migracion 001).
# El documento usa estos mismos nombres en la matriz de perfiles (seccion 3.5).
CLIENTE = "Cliente"
INSPECTOR = "Inspector"
ENCARGADO_CENTRO = "Encargado del Centro de Devoluciones"
COORDINADOR = "Coordinador de Logistica"
ANALISTA = "Analista de Devoluciones"
ENCARGADO_REEMBOLSOS = "Encargado de Reembolsos"
ADMINISTRADOR = "Administrador"

TODOS_LOS_ROLES = (
    CLIENTE, INSPECTOR, ENCARGADO_CENTRO, COORDINADOR,
    ANALISTA, ENCARGADO_REEMBOLSOS, ADMINISTRADOR,
)

# Personal interno: todo rol que no sea el cliente.
INTERNOS = tuple(r for r in TODOS_LOS_ROLES if r != CLIENTE)


def usuario_actual():
    """Datos del usuario en sesion, o None."""
    return session.get("usuario")


def esta_autenticado():
    return usuario_actual() is not None


def rol_actual():
    usuario = usuario_actual()
    return usuario["rol"] if usuario else None


def login_required(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if not esta_autenticado():
            flash("Inicia sesion para continuar.", "aviso")
            return redirect(url_for("auth.login", siguiente=request.path))
        return vista(*args, **kwargs)
    return envoltura


def roles_required(*roles):
    """Restringe una vista a los roles indicados (RNF-09, RN-13)."""
    def decorador(vista):
        @wraps(vista)
        def envoltura(*args, **kwargs):
            if not esta_autenticado():
                flash("Inicia sesion para continuar.", "aviso")
                return redirect(url_for("auth.login", siguiente=request.path))
            if rol_actual() not in roles:
                registrar_bitacora(
                    "acceso_denegado", "ruta", None,
                    f"El rol '{rol_actual()}' intento acceder a {request.path}",
                )
                abort(403)
            return vista(*args, **kwargs)
        return envoltura
    return decorador


def devolucion_visible(devolucion_id):
    """Autorizacion por recurso (5.3).

    El cliente solo puede ver sus propias devoluciones aunque conozca el folio
    o el identificador de otra. El personal interno ve el expediente completo.
    """
    usuario = usuario_actual()
    if usuario is None:
        return False
    if usuario["rol"] != CLIENTE:
        return True

    fila = consultar(
        """
        SELECT v.cliente_id
          FROM devoluciones d
          JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
          JOIN ventas v         ON v.id = vd.venta_id
         WHERE d.id = %s AND d.eliminado_en IS NULL
        """,
        (devolucion_id,),
        uno=True,
    )
    return fila is not None and fila["cliente_id"] == usuario["id"]


def exigir_devolucion_visible(devolucion_id):
    if not devolucion_visible(devolucion_id):
        registrar_bitacora(
            "acceso_denegado", "devoluciones", devolucion_id,
            "Intento de consultar una devolucion que no corresponde al usuario",
        )
        abort(403)


def correlation_id():
    """Identificador de correlacion de la peticion (RNF-23)."""
    if "correlation_id" not in g:
        g.correlation_id = uuid.uuid4().hex[:16]
    return g.correlation_id


def registrar_bitacora(accion, entidad, entidad_id=None, detalle=None):
    """Deja constancia de una operacion importante (RF-30, RN-12).

    Nunca debe recibir contrasenas ni datos sensibles en 'detalle' (RNF-16).
    """
    usuario = usuario_actual()
    ejecutar(
        """
        INSERT INTO bitacora (usuario_id, accion, entidad, entidad_id, detalle,
                              correlation_id, ip_origen)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """,
        (
            usuario["id"] if usuario else None,
            accion,
            entidad,
            entidad_id,
            detalle,
            correlation_id(),
            request.headers.get("X-Forwarded-For", request.remote_addr),
        ),
    )
