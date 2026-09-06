"""Autenticacion: inicio y cierre de sesion, intentos fallidos y bloqueo.

Trazabilidad: RF-01, RNF-07, RNF-08, RNF-12, HU-01, UC-01
"""
from datetime import datetime, timedelta, timezone

from flask import Blueprint, current_app, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from app.cache import limpiar_intentos, registrar_intento_fallido, segundos_bloqueo_restantes
from app.db import consultar, ejecutar
from app.security import login_required, registrar_bitacora, usuario_actual

bp = Blueprint("auth", __name__)


def _registrar_intento(email, usuario_id, exitoso):
    """Historial auditable del intento (RNF-12)."""
    ejecutar(
        """
        INSERT INTO intentos_acceso (email, usuario_id, exitoso, ip_origen, user_agent)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (
            email[:150],
            usuario_id,
            exitoso,
            request.headers.get("X-Forwarded-For", request.remote_addr),
            (request.user_agent.string or "")[:255],
        ),
    )


def _bloqueado(usuario, email):
    """True si la cuenta esta bloqueada, ya sea en Redis o en PostgreSQL.

    Redis lleva el conteo vivo; PostgreSQL conserva el bloqueo si Redis se
    reinicia, de manera que la restriccion no se pierde (RNF-12, RNF-21).
    """
    if segundos_bloqueo_restantes(email) > 0:
        return True
    if usuario and usuario.get("bloqueado_hasta"):
        return usuario["bloqueado_hasta"] > datetime.now(timezone.utc)
    return False


@bp.route("/", methods=["GET"])
def inicio():
    if usuario_actual():
        return redirect(url_for("panel.principal"))
    return redirect(url_for("auth.login"))


@bp.route("/login", methods=["GET", "POST"])
def login():
    if usuario_actual():
        return redirect(url_for("panel.principal"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""

        if not email or not password:
            flash("Captura tu correo y tu contrasena.", "error")
            return render_template("auth/login.html"), 400

        usuario = consultar(
            """
            SELECT u.id, u.nombre, u.email, u.password_hash, u.estado,
                   u.bloqueado_hasta, r.nombre AS rol
              FROM usuarios u
              JOIN roles r ON r.id = u.rol_id
             WHERE lower(u.email) = %s AND u.eliminado_en IS NULL
            """,
            (email,),
            uno=True,
        )

        if _bloqueado(usuario, email):
            _registrar_intento(email, usuario["id"] if usuario else None, False)
            registrar_bitacora("login_bloqueado", "usuarios",
                               usuario["id"] if usuario else None,
                               "Intento de acceso sobre una cuenta bloqueada")
            flash(
                f"La cuenta esta bloqueada temporalmente. Intenta de nuevo en "
                f"{current_app.config['MINUTOS_BLOQUEO']} minutos.",
                "error",
            )
            return render_template("auth/login.html"), 429

        credenciales_ok = (
            usuario is not None
            and usuario["estado"] == "activo"
            and check_password_hash(usuario["password_hash"], password)
        )

        if not credenciales_ok:
            _registrar_intento(email, usuario["id"] if usuario else None, False)
            bloqueada, intentos = registrar_intento_fallido(email)
            if bloqueada and usuario:
                hasta = datetime.now(timezone.utc) + timedelta(
                    minutes=current_app.config["MINUTOS_BLOQUEO"]
                )
                ejecutar("UPDATE usuarios SET bloqueado_hasta = %s WHERE id = %s",
                         (hasta, usuario["id"]))
                registrar_bitacora("cuenta_bloqueada", "usuarios", usuario["id"],
                                   f"Bloqueo temporal tras {intentos} intentos fallidos")
            # Mensaje deliberadamente generico: no revela si el correo existe (RNF-16).
            flash("Correo o contrasena incorrectos.", "error")
            return render_template("auth/login.html"), 401

        limpiar_intentos(email)
        ejecutar("UPDATE usuarios SET bloqueado_hasta = NULL WHERE id = %s", (usuario["id"],))
        _registrar_intento(email, usuario["id"], True)

        session.clear()
        session["usuario"] = {
            "id": usuario["id"],
            "nombre": usuario["nombre"],
            "email": usuario["email"],
            "rol": usuario["rol"],
        }
        registrar_bitacora("login", "usuarios", usuario["id"], "Inicio de sesion correcto")

        siguiente = request.args.get("siguiente")
        if siguiente and siguiente.startswith("/"):
            return redirect(siguiente)
        return redirect(url_for("panel.principal"))

    return render_template("auth/login.html")


@bp.post("/logout")
@login_required
def logout():
    registrar_bitacora("logout", "usuarios", usuario_actual()["id"], "Cierre de sesion")
    session.clear()
    flash("Sesion cerrada.", "ok")
    return redirect(url_for("auth.login"))
