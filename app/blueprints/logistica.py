"""Logistica inversa: programacion de recoleccion y recepcion en el centro.

Trazabilidad: RF-12, RF-13, RF-15, RN-08, HU-12, HU-13, UC-10, UC-11, UC-13
"""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app.db import consultar, ejecutar
from app.security import (
    COORDINADOR, ENCARGADO_CENTRO, registrar_bitacora, roles_required, usuario_actual,
)
from app.blueprints.devoluciones import cambiar_estado, obtener_expediente

bp = Blueprint("logistica", __name__, url_prefix="/logistica")

ESTADOS_RECOLECCION = ("programada", "asignada", "en_transito", "completada", "fallida")


@bp.get("/recolecciones")
@roles_required(COORDINADOR, ENCARGADO_CENTRO)
def listar():
    recolecciones = consultar(
        """
        SELECT r.id, r.estado, r.fecha_programada, r.lugar,
               d.id AS devolucion_id, d.folio_devolucion, d.estado AS estado_devolucion,
               p.nombre AS producto, p.clasificacion_temperatura,
               ru.origen, ru.destino, tr.nombre AS transportista
          FROM recolecciones r
          JOIN devoluciones d   ON d.id = r.devolucion_id
          JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
          JOIN lotes l          ON l.id = vd.lote_id
          JOIN productos p      ON p.id = l.producto_id
          LEFT JOIN rutas ru          ON ru.id = r.ruta_id
          LEFT JOIN transportistas tr ON tr.id = r.transportista_id
         WHERE d.eliminado_en IS NULL
         ORDER BY r.fecha_programada DESC NULLS LAST, r.id DESC
        """
    )
    pendientes = consultar(
        """
        SELECT d.id, d.folio_devolucion, d.fecha_autorizacion, p.nombre AS producto
          FROM devoluciones d
          JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
          JOIN lotes l          ON l.id = vd.lote_id
          JOIN productos p      ON p.id = l.producto_id
         WHERE d.estado = 'autorizada'
           AND d.eliminado_en IS NULL
           AND NOT EXISTS (SELECT 1 FROM recolecciones r WHERE r.devolucion_id = d.id)
         ORDER BY d.fecha_autorizacion
        """
    )
    return render_template("logistica/listar.html", recolecciones=recolecciones,
                           pendientes=pendientes)


@bp.route("/recolecciones/<int:devolucion_id>/programar", methods=["GET", "POST"])
@roles_required(COORDINADOR)
def programar(devolucion_id):
    """Programa la recoleccion de una devolucion autorizada (RF-12)."""
    expediente = obtener_expediente(devolucion_id)
    if expediente is None:
        abort(404)
    if expediente["estado"] != "autorizada":
        flash("Solo se puede programar la recoleccion de una devolucion autorizada.", "error")
        return redirect(url_for("devoluciones.detalle", devolucion_id=devolucion_id))

    existente = consultar("SELECT id FROM recolecciones WHERE devolucion_id = %s",
                          (devolucion_id,), uno=True)
    if existente:
        flash("Esta devolucion ya tiene una recoleccion registrada.", "aviso")
        return redirect(url_for("devoluciones.detalle", devolucion_id=devolucion_id))

    rutas = consultar("SELECT id, origen, destino FROM rutas WHERE activo = TRUE ORDER BY origen")
    transportistas = consultar(
        "SELECT id, nombre, empresa FROM transportistas WHERE activo = TRUE ORDER BY nombre")

    if request.method == "POST":
        fecha = request.form.get("fecha_programada") or None
        lugar = (request.form.get("lugar") or "").strip()
        ruta_id = request.form.get("ruta_id", type=int)
        transportista_id = request.form.get("transportista_id", type=int)

        if not fecha or not lugar:
            flash("La fecha y el lugar de recoleccion son obligatorios.", "error")
            return render_template("logistica/programar.html", d=expediente, rutas=rutas,
                                   transportistas=transportistas), 400

        ejecutar(
            """
            INSERT INTO recolecciones (devolucion_id, fecha_programada, lugar, ruta_id,
                                       transportista_id, coordinador_id, estado)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            """,
            (devolucion_id, fecha, lugar, ruta_id, transportista_id,
             usuario_actual()["id"],
             "asignada" if (ruta_id and transportista_id) else "programada"),
        )
        cambiar_estado(devolucion_id, "en_recoleccion",
                       f"Recoleccion programada para el {fecha} en {lugar}")
        flash("Recoleccion programada.", "ok")
        return redirect(url_for("devoluciones.detalle", devolucion_id=devolucion_id))

    return render_template("logistica/programar.html", d=expediente, rutas=rutas,
                           transportistas=transportistas)


@bp.post("/recolecciones/<int:recoleccion_id>/estado")
@roles_required(COORDINADOR)
def actualizar_estado(recoleccion_id):
    """Actualiza ruta, transportista y estado de la recoleccion (RF-13, RN-08)."""
    nuevo = request.form.get("estado")
    ruta_id = request.form.get("ruta_id", type=int)
    transportista_id = request.form.get("transportista_id", type=int)

    if nuevo not in ESTADOS_RECOLECCION:
        abort(400)

    recoleccion = consultar("SELECT * FROM recolecciones WHERE id = %s", (recoleccion_id,), uno=True)
    if recoleccion is None:
        abort(404)

    ruta_final = ruta_id or recoleccion["ruta_id"]
    transportista_final = transportista_id or recoleccion["transportista_id"]

    # RN-08: una recoleccion solo puede marcarse completada con fecha, lugar,
    # ruta y transportista asignados.
    if nuevo == "completada" and not all(
        [recoleccion["fecha_programada"], recoleccion["lugar"], ruta_final, transportista_final]
    ):
        flash("Para completar la recoleccion faltan fecha, lugar, ruta o transportista (RN-08).",
              "error")
        return redirect(url_for("devoluciones.detalle",
                                devolucion_id=recoleccion["devolucion_id"]))

    ejecutar(
        "UPDATE recolecciones SET estado = %s, ruta_id = %s, transportista_id = %s WHERE id = %s",
        (nuevo, ruta_final, transportista_final, recoleccion_id),
    )
    registrar_bitacora("estado_recoleccion", "devoluciones", recoleccion["devolucion_id"],
                       f"La recoleccion paso al estado '{nuevo}'")
    flash("Recoleccion actualizada.", "ok")
    return redirect(url_for("devoluciones.detalle", devolucion_id=recoleccion["devolucion_id"]))


@bp.post("/recepciones/<int:devolucion_id>")
@roles_required(ENCARGADO_CENTRO)
def registrar_recepcion(devolucion_id):
    """Confirma la llegada del articulo al centro de devoluciones (RF-15, UC-13)."""
    expediente = obtener_expediente(devolucion_id)
    if expediente is None:
        abort(404)
    if expediente["estado"] != "en_recoleccion":
        flash("Solo se puede recibir un producto que esta en recoleccion.", "error")
        return redirect(url_for("devoluciones.detalle", devolucion_id=devolucion_id))

    coincide = request.form.get("coincide_expediente") == "si"
    ejecutar(
        """
        INSERT INTO recepciones (devolucion_id, encargado_id, coincide_expediente)
        VALUES (%s, %s, %s)
        ON CONFLICT (devolucion_id) DO NOTHING
        """,
        (devolucion_id, usuario_actual()["id"], coincide),
    )
    ejecutar("UPDATE recolecciones SET estado = 'completada' WHERE devolucion_id = %s",
             (devolucion_id,))
    cambiar_estado(
        devolucion_id, "recibida",
        "Producto recibido en el centro de devoluciones. "
        + ("Coincide con el expediente." if coincide else "NO coincide con el expediente."),
    )
    flash("Recepcion registrada.", "ok")
    return redirect(url_for("devoluciones.detalle", devolucion_id=devolucion_id))
