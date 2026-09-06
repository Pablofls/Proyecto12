"""Gestion del reembolso de una devolucion.

Trazabilidad: RF-20, RF-21, RN-03, RN-04, HU-18, UC-17
"""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
import psycopg2

from app.db import consultar, ejecutar, get_conn
from app.security import (
    ANALISTA, ENCARGADO_REEMBOLSOS, registrar_bitacora, roles_required, usuario_actual,
)
from app.blueprints.devoluciones import cambiar_estado, obtener_expediente

bp = Blueprint("reembolsos", __name__, url_prefix="/reembolsos")

METODOS = [("transferencia", "Transferencia"), ("tarjeta", "Tarjeta"),
           ("efectivo", "Efectivo"), ("vale", "Vale")]


@bp.get("/")
@roles_required(ENCARGADO_REEMBOLSOS, ANALISTA)
def listar():
    # RN-04: solo aparecen devoluciones que ya pasaron por autorizacion.
    pendientes = consultar(
        """
        SELECT d.id, d.folio_devolucion, d.estado, d.cantidad_devuelta,
               vd.precio_unitario,
               (vd.precio_unitario * d.cantidad_devuelta) AS valor_devuelto,
               p.nombre AS producto, cli.nombre AS cliente
          FROM devoluciones d
          JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
          JOIN ventas v         ON v.id = vd.venta_id
          JOIN usuarios cli     ON cli.id = v.cliente_id
          JOIN lotes l          ON l.id = vd.lote_id
          JOIN productos p      ON p.id = l.producto_id
         WHERE d.estado IN ('autorizada', 'en_recoleccion', 'recibida',
                            'en_inspeccion', 'resuelta')
           AND d.eliminado_en IS NULL
           AND NOT EXISTS (SELECT 1 FROM reembolsos rb
                            WHERE rb.devolucion_id = d.id AND rb.eliminado_en IS NULL)
         ORDER BY d.fecha_autorizacion
        """
    )
    registrados = consultar(
        """
        SELECT rb.id, rb.monto, rb.metodo, rb.estado, rb.fecha_resolucion,
               d.id AS devolucion_id, d.folio_devolucion,
               u.nombre AS encargado, cli.nombre AS cliente
          FROM reembolsos rb
          JOIN devoluciones d   ON d.id = rb.devolucion_id
          JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
          JOIN ventas v         ON v.id = vd.venta_id
          JOIN usuarios cli     ON cli.id = v.cliente_id
          JOIN usuarios u       ON u.id = rb.encargado_id
         WHERE rb.eliminado_en IS NULL
         ORDER BY rb.id DESC
         LIMIT 100
        """
    )
    return render_template("reembolsos/listar.html", pendientes=pendientes,
                           registrados=registrados)


@bp.route("/<int:devolucion_id>/registrar", methods=["GET", "POST"])
@roles_required(ENCARGADO_REEMBOLSOS)
def registrar(devolucion_id):
    expediente = obtener_expediente(devolucion_id)
    if expediente is None:
        abort(404)

    # RN-03: una devolucion no puede tener mas de un reembolso valido.
    existente = consultar(
        "SELECT id FROM reembolsos WHERE devolucion_id = %s AND eliminado_en IS NULL",
        (devolucion_id,), uno=True,
    )
    if existente:
        flash("Esta devolucion ya tiene un reembolso registrado (RN-03).", "aviso")
        return redirect(url_for("devoluciones.detalle", devolucion_id=devolucion_id))

    # RN-04: no se registra un reembolso sobre una solicitud sin autorizar.
    if expediente["estado"] in ("solicitada", "en_revision", "rechazada"):
        flash("La devolucion debe estar autorizada antes de gestionar el reembolso (RN-04).",
              "error")
        return redirect(url_for("devoluciones.detalle", devolucion_id=devolucion_id))

    if request.method == "POST":
        decision = request.form.get("decision")
        monto = request.form.get("monto", type=float)
        metodo = request.form.get("metodo")

        if decision not in ("aprobado", "rechazado"):
            abort(400)
        if decision == "aprobado":
            if monto is None or monto < 0:
                flash("Captura un monto valido.", "error")
                return render_template("reembolsos/registrar.html", d=expediente,
                                       metodos=METODOS), 400
            if metodo not in dict(METODOS):
                flash("Selecciona un metodo de reembolso.", "error")
                return render_template("reembolsos/registrar.html", d=expediente,
                                       metodos=METODOS), 400
        else:
            monto, metodo = 0, None

        try:
            ejecutar(
                """
                INSERT INTO reembolsos (devolucion_id, encargado_id, monto, metodo,
                                        estado, fecha_resolucion)
                VALUES (%s, %s, %s, %s, %s, CURRENT_TIMESTAMP)
                """,
                (devolucion_id, usuario_actual()["id"], monto, metodo, decision),
            )
        except psycopg2.errors.RaiseException as exc:
            # El trigger fn_validar_reembolso bloquea montos excesivos o
            # devoluciones sin autorizar.
            get_conn().rollback()
            flash(str(exc).split("CONTEXT:")[0].strip(), "error")
            return render_template("reembolsos/registrar.html", d=expediente,
                                   metodos=METODOS), 409

        if decision == "aprobado":
            ejecutar(
                "INSERT INTO costos (devolucion_id, etapa, monto) VALUES (%s, 'reembolso', %s)",
                (devolucion_id, monto),
            )
            registrar_bitacora("reembolso_aprobado", "devoluciones", devolucion_id,
                               f"Reembolso aprobado por {monto} via {metodo}")
        else:
            registrar_bitacora("reembolso_rechazado", "devoluciones", devolucion_id,
                               "Reembolso rechazado")

        if expediente["estado"] == "resuelta":
            cambiar_estado(devolucion_id, "cerrada",
                           "Caso cerrado tras resolver el reembolso")

        flash("Reembolso registrado.", "ok")
        return redirect(url_for("devoluciones.detalle", devolucion_id=devolucion_id))

    return render_template("reembolsos/registrar.html", d=expediente, metodos=METODOS)
