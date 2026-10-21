"""Administracion de usuarios, roles y permisos.

Trazabilidad: RF-03, RF-04, RNF-07, RNF-30, HU-03, HU-04, UC-03, UC-04
"""
from flask import Blueprint, flash, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash

from app.db import consultar, ejecutar
from app.security import ADMINISTRADOR, ANALISTA, registrar_bitacora, roles_required

bp = Blueprint("usuarios", __name__, url_prefix="/usuarios")


@bp.get("/")
@roles_required(ADMINISTRADOR, ANALISTA)
def listar():
    usuarios = consultar(
        """
        SELECT u.id, u.nombre, u.email, u.estado, u.bloqueado_hasta,
               r.nombre AS rol, u.fecha_creacion
          FROM usuarios u
          JOIN roles r ON r.id = u.rol_id
         WHERE u.eliminado_en IS NULL
         ORDER BY r.nombre, u.nombre
        """
    )
    return render_template("usuarios/listar.html", usuarios=usuarios)


@bp.route("/nuevo", methods=["GET", "POST"])
@roles_required(ADMINISTRADOR)
def nuevo():
    roles = consultar("SELECT id, nombre FROM roles ORDER BY nombre")

    if request.method == "POST":
        nombre = (request.form.get("nombre") or "").strip()
        email = (request.form.get("email") or "").strip().lower()
        password = request.form.get("password") or ""
        rol_id = request.form.get("rol_id")

        if not nombre or not email or not rol_id:
            flash("Nombre, correo y rol son obligatorios.", "error")
            return render_template("usuarios/formulario.html", roles=roles, usuario=None), 400
        if len(password) < 8:
            flash("La contrasena debe tener al menos 8 caracteres.", "error")
            return render_template("usuarios/formulario.html", roles=roles, usuario=None), 400

        existente = consultar("SELECT id FROM usuarios WHERE lower(email) = %s", (email,), uno=True)
        if existente:
            flash("Ya existe un usuario con ese correo.", "error")
            return render_template("usuarios/formulario.html", roles=roles, usuario=None), 409

        fila = ejecutar(
            """
            INSERT INTO usuarios (nombre, email, password_hash, rol_id)
            VALUES (%s, %s, %s, %s) RETURNING id
            """,
            (nombre, email, generate_password_hash(password), rol_id),
            devolver=True,
        )
        registrar_bitacora("alta_usuario", "usuarios", fila["id"], f"Alta del usuario {email}")
        flash("Usuario registrado.", "ok")
        return redirect(url_for("usuarios.listar"))

    return render_template("usuarios/formulario.html", roles=roles, usuario=None)


@bp.route("/<int:usuario_id>/editar", methods=["GET", "POST"])
@roles_required(ADMINISTRADOR)
def editar(usuario_id):
    roles = consultar("SELECT id, nombre FROM roles ORDER BY nombre")
    usuario = consultar(
        "SELECT id, nombre, email, estado, rol_id FROM usuarios WHERE id = %s AND eliminado_en IS NULL",
        (usuario_id,), uno=True,
    )
    if usuario is None:
        flash("El usuario no existe.", "error")
        return redirect(url_for("usuarios.listar"))

    if request.method == "POST":
        nombre = (request.form.get("nombre") or "").strip()
        rol_id = request.form.get("rol_id")
        estado = request.form.get("estado")
        password = request.form.get("password") or ""

        if estado not in ("activo", "inactivo", "bloqueado"):
            flash("Estado invalido.", "error")
            return render_template("usuarios/formulario.html", roles=roles, usuario=usuario), 400

        ejecutar(
            "UPDATE usuarios SET nombre = %s, rol_id = %s, estado = %s WHERE id = %s",
            (nombre, rol_id, estado, usuario_id),
        )
        if password:
            if len(password) < 8:
                flash("La contrasena debe tener al menos 8 caracteres.", "error")
                return render_template("usuarios/formulario.html", roles=roles, usuario=usuario), 400
            ejecutar("UPDATE usuarios SET password_hash = %s, bloqueado_hasta = NULL WHERE id = %s",
                     (generate_password_hash(password), usuario_id))
            registrar_bitacora("cambio_password", "usuarios", usuario_id,
                               "Se restablecio la contrasena del usuario")

        registrar_bitacora("edicion_usuario", "usuarios", usuario_id,
                           f"Se actualizo el usuario a rol {rol_id} y estado {estado}")
        flash("Usuario actualizado.", "ok")
        return redirect(url_for("usuarios.listar"))

    return render_template("usuarios/formulario.html", roles=roles, usuario=usuario)


@bp.post("/<int:usuario_id>/desactivar")
@roles_required(ADMINISTRADOR)
def desactivar(usuario_id):
    """Baja logica: la cuenta se conserva para no romper el historial (RNF-30)."""
    ejecutar(
        "UPDATE usuarios SET estado = 'inactivo', eliminado_en = CURRENT_TIMESTAMP WHERE id = %s",
        (usuario_id,),
    )
    registrar_bitacora("baja_usuario", "usuarios", usuario_id, "Baja logica del usuario")
    flash("Usuario dado de baja.", "ok")
    return redirect(url_for("usuarios.listar"))


@bp.post("/<int:usuario_id>/desbloquear")
@roles_required(ADMINISTRADOR)
def desbloquear(usuario_id):
    ejecutar("UPDATE usuarios SET bloqueado_hasta = NULL, estado = 'activo' WHERE id = %s",
             (usuario_id,))
    registrar_bitacora("desbloqueo_usuario", "usuarios", usuario_id, "Desbloqueo manual")
    flash("Cuenta desbloqueada.", "ok")
    return redirect(url_for("usuarios.listar"))
