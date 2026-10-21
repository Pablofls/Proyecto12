"""Bandeja de notificaciones internas y campanita (RF-29, UC-25, RN-13).

Cada usuario ve unicamente las suyas: todas las consultas filtran por el
usuario_id de la sesion, y marcar como leida una notificacion ajena responde
404 para no revelar que existe (RN-13).

Trazabilidad: RF-29, UC-25, RN-13, RN-12, HU-27
"""
from flask import (
    Blueprint, abort, flash, jsonify, redirect, render_template, request, url_for,
)

from app.db import consultar, ejecutar
from app.security import login_required, registrar_bitacora, usuario_actual

bp = Blueprint("notificaciones", __name__, url_prefix="/notificaciones")

POR_PAGINA = 20
EN_CAMPANITA = 8


def _destino_seguro(url):
    """Solo rutas internas: evita que una fila manipulada saque al usuario del sitio."""
    return bool(url) and url.startswith("/") and not url.startswith("//") and "\\" not in url


@bp.get("/")
@login_required
def listar():
    usuario = usuario_actual()
    filtro = "no_leidas" if request.args.get("filtro") == "no_leidas" else "todas"
    pagina = max(request.args.get("pagina", 1, type=int), 1)

    # Fragmento fijo (no viene del usuario): el valor del filtro solo elige entre dos literales.
    condicion = "n.usuario_id = %s" + (" AND NOT n.leido" if filtro == "no_leidas" else "")
    total = consultar(
        f"SELECT COUNT(*) AS cuenta FROM notificaciones n WHERE {condicion}",
        (usuario["id"],), uno=True,
    )["cuenta"]
    filas = consultar(
        f"""
        SELECT n.id, n.tipo, n.mensaje, n.leido, n.fecha_creacion,
               d.folio_devolucion
          FROM notificaciones n
          LEFT JOIN devoluciones d ON d.id = n.devolucion_id
         WHERE {condicion}
         ORDER BY n.fecha_creacion DESC, n.id DESC
         LIMIT %s OFFSET %s
        """,
        (usuario["id"], POR_PAGINA, (pagina - 1) * POR_PAGINA),
    )
    paginas = max((total + POR_PAGINA - 1) // POR_PAGINA, 1)
    return render_template("notificaciones/listar.html", notificaciones=filas,
                           filtro=filtro, pagina=pagina, paginas=paginas, total=total)


@bp.get("/resumen")
@login_required
def resumen():
    """Contador y ultimas notificaciones para la campanita (sondeo cada ~30 s)."""
    usuario = usuario_actual()
    no_leidas = consultar(
        "SELECT COUNT(*) AS n FROM notificaciones WHERE usuario_id = %s AND NOT leido",
        (usuario["id"],), uno=True,
    )["n"]
    ultimas = consultar(
        """
        SELECT id, mensaje, leido, fecha_creacion
          FROM notificaciones
         WHERE usuario_id = %s
         ORDER BY fecha_creacion DESC, id DESC
         LIMIT %s
        """,
        (usuario["id"], EN_CAMPANITA),
    )
    respuesta = jsonify({
        "no_leidas": no_leidas,
        "ultimas": [
            {
                "id": fila["id"],
                "mensaje": fila["mensaje"],
                "leido": fila["leido"],
                "fecha": fila["fecha_creacion"].strftime("%d/%m/%Y %H:%M"),
                "leer": url_for("notificaciones.leer", notificacion_id=fila["id"]),
            }
            for fila in ultimas
        ],
    })
    respuesta.headers["Cache-Control"] = "no-store"
    return respuesta


@bp.post("/<int:notificacion_id>/leer")
@login_required
def leer(notificacion_id):
    """Marca como leida y lleva a la pantalla donde se actua."""
    usuario = usuario_actual()
    fila = consultar(
        "SELECT id, url, devolucion_id FROM notificaciones WHERE id = %s AND usuario_id = %s",
        (notificacion_id, usuario["id"]), uno=True,
    )
    if fila is None:
        abort(404)

    ejecutar("UPDATE notificaciones SET leido = TRUE WHERE id = %s AND usuario_id = %s",
             (notificacion_id, usuario["id"]))
    registrar_bitacora("leer_notificacion", "notificaciones", notificacion_id,
                       "Notificacion marcada como leida")

    if _destino_seguro(fila["url"]):
        return redirect(fila["url"])
    if fila["devolucion_id"]:
        return redirect(url_for("devoluciones.detalle", devolucion_id=fila["devolucion_id"]))
    return redirect(url_for("notificaciones.listar"))


@bp.post("/leer-todas")
@login_required
def leer_todas():
    usuario = usuario_actual()
    marcadas = consultar(
        """
        WITH marcadas AS (
            UPDATE notificaciones SET leido = TRUE
             WHERE usuario_id = %s AND NOT leido
         RETURNING 1
        )
        SELECT COUNT(*) AS n FROM marcadas
        """,
        (usuario["id"],), uno=True,
    )["n"]
    registrar_bitacora("leer_todas_notificaciones", "notificaciones", None,
                       f"{marcadas} notificacion(es) marcadas como leidas")
    flash("Notificaciones marcadas como leidas.", "ok")
    return redirect(url_for("notificaciones.listar"))
