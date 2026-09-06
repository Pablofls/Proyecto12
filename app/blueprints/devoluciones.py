"""Expediente de la devolucion: registro, evidencias, autorizacion y consulta.

Es el modulo central del sistema. Toda devolucion nace de una linea de venta
(RN-01) y avanza por los estados definidos en el esquema.

Trazabilidad: RF-06 a RF-11, RF-21, RN-01, RN-02, RN-12,
              HU-06 a HU-11, UC-06, UC-07, UC-08, UC-09
"""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from app.db import consultar, ejecutar
from app.security import (
    ANALISTA, CLIENTE, INSPECTOR, TODOS_LOS_ROLES,
    exigir_devolucion_visible, registrar_bitacora, roles_required, usuario_actual,
)

bp = Blueprint("devoluciones", __name__, url_prefix="/devoluciones")

# Estados desde los que el analista todavia puede resolver la solicitud (RF-10).
ESTADOS_REVISABLES = ("solicitada", "en_revision")


def obtener_expediente(devolucion_id):
    """Encabezado del expediente con todo lo que se necesita para mostrarlo."""
    return consultar(
        """
        SELECT d.id, d.folio_devolucion, d.estado, d.descripcion_problema,
               d.cantidad_devuelta, d.fecha_solicitud, d.fecha_autorizacion,
               m.nombre AS motivo,
               vd.id AS venta_detalle_id, vd.cantidad AS cantidad_comprada,
               vd.precio_unitario,
               (vd.precio_unitario * d.cantidad_devuelta) AS valor_devuelto,
               v.id AS venta_id, v.folio_venta, v.fecha_venta,
               cli.id AS cliente_id, cli.nombre AS cliente, cli.email AS cliente_email,
               t.nombre AS tienda,
               p.id AS producto_id, p.nombre AS producto, p.sku,
               p.clasificacion_temperatura,
               l.numero_lote, l.fecha_caducidad,
               pr.nombre AS proveedor,
               ana.nombre AS analista
          FROM devoluciones d
          JOIN motivos m        ON m.id = d.motivo_id
          JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
          JOIN ventas v         ON v.id = vd.venta_id
          JOIN usuarios cli     ON cli.id = v.cliente_id
          JOIN tiendas t        ON t.id = v.tienda_id
          JOIN lotes l          ON l.id = vd.lote_id
          JOIN productos p      ON p.id = l.producto_id
          JOIN proveedores pr   ON pr.id = l.proveedor_id
          LEFT JOIN usuarios ana ON ana.id = d.analista_id
         WHERE d.id = %s AND d.eliminado_en IS NULL
        """,
        (devolucion_id,), uno=True,
    )


def cambiar_estado(devolucion_id, nuevo_estado, detalle):
    """Cambia el estado del expediente y lo deja registrado (RN-12)."""
    ejecutar("UPDATE devoluciones SET estado = %s WHERE id = %s", (nuevo_estado, devolucion_id))
    registrar_bitacora("cambio_estado", "devoluciones", devolucion_id, detalle)


@bp.get("/")
@roles_required(*TODOS_LOS_ROLES)
def listar():
    usuario = usuario_actual()
    estado = (request.args.get("estado") or "").strip()
    busqueda = (request.args.get("q") or "").strip()

    condiciones = ["d.eliminado_en IS NULL"]
    parametros = []

    if usuario["rol"] == CLIENTE:
        condiciones.append("v.cliente_id = %s")
        parametros.append(usuario["id"])
    if estado:
        condiciones.append("d.estado = %s")
        parametros.append(estado)
    if busqueda:
        condiciones.append("(d.folio_devolucion ILIKE %s OR p.nombre ILIKE %s)")
        parametros.extend([f"%{busqueda}%", f"%{busqueda}%"])

    devoluciones = consultar(
        f"""
        SELECT d.id, d.folio_devolucion, d.estado, d.fecha_solicitud,
               m.nombre AS motivo, p.nombre AS producto,
               p.clasificacion_temperatura, l.numero_lote,
               cli.nombre AS cliente, v.folio_venta
          FROM devoluciones d
          JOIN motivos m        ON m.id = d.motivo_id
          JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
          JOIN ventas v         ON v.id = vd.venta_id
          JOIN usuarios cli     ON cli.id = v.cliente_id
          JOIN lotes l          ON l.id = vd.lote_id
          JOIN productos p      ON p.id = l.producto_id
         WHERE {' AND '.join(condiciones)}
         ORDER BY d.fecha_solicitud DESC
         LIMIT 200
        """,
        tuple(parametros),
    )
    return render_template("devoluciones/listar.html", devoluciones=devoluciones,
                           estado=estado, busqueda=busqueda)


@bp.route("/nueva", methods=["GET", "POST"])
@roles_required(CLIENTE, ANALISTA)
def nueva():
    """Registra la solicitud a partir de una linea de venta (RN-01)."""
    usuario = usuario_actual()
    venta_detalle_id = request.values.get("venta_detalle_id", type=int)
    if not venta_detalle_id:
        flash("Selecciona primero el producto que deseas devolver.", "aviso")
        return redirect(url_for("ventas.listar"))

    linea = consultar(
        """
        SELECT vd.id, vd.cantidad, vd.precio_unitario,
               v.id AS venta_id, v.folio_venta, v.fecha_venta, v.cliente_id,
               p.nombre AS producto, p.sku, p.clasificacion_temperatura,
               l.numero_lote, l.fecha_caducidad,
               (SELECT COALESCE(SUM(d.cantidad_devuelta), 0)
                  FROM devoluciones d
                 WHERE d.venta_detalle_id = vd.id
                   AND d.eliminado_en IS NULL
                   AND d.estado <> 'rechazada') AS ya_devuelto
          FROM venta_detalle vd
          JOIN ventas v    ON v.id = vd.venta_id
          JOIN lotes l     ON l.id = vd.lote_id
          JOIN productos p ON p.id = l.producto_id
         WHERE vd.id = %s AND v.eliminado_en IS NULL
        """,
        (venta_detalle_id,), uno=True,
    )
    if linea is None:
        abort(404)
    if usuario["rol"] == CLIENTE and linea["cliente_id"] != usuario["id"]:
        abort(403)

    disponible = linea["cantidad"] - linea["ya_devuelto"]
    motivos = consultar("SELECT id, nombre FROM motivos WHERE activo = TRUE ORDER BY nombre")

    if request.method == "POST":
        motivo_id = request.form.get("motivo_id", type=int)
        descripcion = (request.form.get("descripcion_problema") or "").strip()
        cantidad = request.form.get("cantidad_devuelta", type=int) or 1

        errores = []
        if not motivo_id:
            errores.append("Selecciona un motivo.")
        if len(descripcion) < 10:
            errores.append("Describe el problema con al menos 10 caracteres.")
        if cantidad < 1 or cantidad > disponible:
            errores.append(f"La cantidad debe estar entre 1 y {disponible}.")

        if errores:
            for e in errores:
                flash(e, "error")
            return render_template("devoluciones/nueva.html", linea=linea,
                                   motivos=motivos, disponible=disponible), 400

        fila = ejecutar(
            """
            INSERT INTO devoluciones (venta_detalle_id, motivo_id, descripcion_problema,
                                      cantidad_devuelta, estado)
            VALUES (%s, %s, %s, %s, 'solicitada')
            RETURNING id, folio_devolucion
            """,
            (venta_detalle_id, motivo_id, descripcion, cantidad),
            devolver=True,
        )
        registrar_bitacora("alta_devolucion", "devoluciones", fila["id"],
                           f"Se registro la devolucion {fila['folio_devolucion']} "
                           f"sobre la venta {linea['folio_venta']}")
        flash(f"Devolucion registrada con folio {fila['folio_devolucion']}.", "ok")
        return redirect(url_for("devoluciones.detalle", devolucion_id=fila["id"]))

    if disponible <= 0:
        flash("Todos los articulos de esta linea ya tienen una devolucion registrada.", "aviso")
        return redirect(url_for("ventas.detalle", venta_id=linea["venta_id"]))

    return render_template("devoluciones/nueva.html", linea=linea,
                           motivos=motivos, disponible=disponible)


@bp.get("/<int:devolucion_id>")
@roles_required(*TODOS_LOS_ROLES)
def detalle(devolucion_id):
    exigir_devolucion_visible(devolucion_id)
    expediente = obtener_expediente(devolucion_id)
    if expediente is None:
        abort(404)

    evidencias = consultar(
        """
        SELECT e.id, e.tipo, e.etapa, e.comentario, e.nombre_original,
               e.objeto, e.fecha_registro, u.nombre AS autor
          FROM evidencias e
          JOIN usuarios u ON u.id = e.usuario_id
         WHERE e.devolucion_id = %s AND e.eliminado_en IS NULL
         ORDER BY e.fecha_registro DESC
        """,
        (devolucion_id,),
    )
    recoleccion = consultar(
        """
        SELECT r.*, ru.origen, ru.destino, tr.nombre AS transportista,
               co.nombre AS coordinador
          FROM recolecciones r
          LEFT JOIN rutas ru          ON ru.id = r.ruta_id
          LEFT JOIN transportistas tr ON tr.id = r.transportista_id
          LEFT JOIN usuarios co       ON co.id = r.coordinador_id
         WHERE r.devolucion_id = %s
        """,
        (devolucion_id,), uno=True,
    )
    recepcion = consultar(
        """
        SELECT rc.*, u.nombre AS encargado
          FROM recepciones rc JOIN usuarios u ON u.id = rc.encargado_id
         WHERE rc.devolucion_id = %s
        """,
        (devolucion_id,), uno=True,
    )
    inspeccion = consultar(
        """
        SELECT i.*, u.nombre AS inspector
          FROM inspecciones_ref i JOIN usuarios u ON u.id = i.inspector_id
         WHERE i.devolucion_id = %s
        """,
        (devolucion_id,), uno=True,
    )
    disposicion = consultar(
        """
        SELECT ds.*, u.nombre AS analista
          FROM disposiciones ds JOIN usuarios u ON u.id = ds.analista_id
         WHERE ds.devolucion_id = %s
        """,
        (devolucion_id,), uno=True,
    )
    reembolso = consultar(
        """
        SELECT rb.*, u.nombre AS encargado
          FROM reembolsos rb JOIN usuarios u ON u.id = rb.encargado_id
         WHERE rb.devolucion_id = %s AND rb.eliminado_en IS NULL
        """,
        (devolucion_id,), uno=True,
    )
    # El historial del caso se reconstruye desde la bitacora (RF-11, RF-30).
    historial = consultar(
        """
        SELECT b.accion, b.detalle, b.fecha, u.nombre AS usuario
          FROM bitacora b LEFT JOIN usuarios u ON u.id = b.usuario_id
         WHERE b.entidad = 'devoluciones' AND b.entidad_id = %s
         ORDER BY b.fecha DESC
        """,
        (devolucion_id,),
    )
    costos = consultar(
        "SELECT etapa, monto, fecha FROM costos WHERE devolucion_id = %s ORDER BY fecha",
        (devolucion_id,),
    )

    return render_template(
        "devoluciones/detalle.html", d=expediente, evidencias=evidencias,
        recoleccion=recoleccion, recepcion=recepcion, inspeccion=inspeccion,
        disposicion=disposicion, reembolso=reembolso, historial=historial, costos=costos,
        estados_revisables=ESTADOS_REVISABLES,
    )


@bp.post("/<int:devolucion_id>/evidencias")
@roles_required(CLIENTE, INSPECTOR, ANALISTA)
def agregar_evidencia(devolucion_id):
    """Registra una evidencia del caso (RF-09).

    En el primer parcial se registran comentarios y la referencia del archivo.
    La carga real al bucket y los enlaces firmados se implementan cuando se
    habilite Google Cloud Storage (RNF-15).
    """
    exigir_devolucion_visible(devolucion_id)
    usuario = usuario_actual()
    tipo = request.form.get("tipo") or "comentario"
    comentario = (request.form.get("comentario") or "").strip()
    nombre_archivo = (request.form.get("nombre_original") or "").strip()
    etapa = request.form.get("etapa") or "solicitud"

    if tipo not in ("comentario", "fotografia", "documento"):
        abort(400)
    if tipo == "comentario" and not comentario:
        flash("El comentario no puede quedar vacio.", "error")
        return redirect(url_for("devoluciones.detalle", devolucion_id=devolucion_id))
    if tipo != "comentario" and not nombre_archivo:
        flash("Indica el nombre del archivo de evidencia.", "error")
        return redirect(url_for("devoluciones.detalle", devolucion_id=devolucion_id))

    ejecutar(
        """
        INSERT INTO evidencias (devolucion_id, usuario_id, tipo, etapa, comentario,
                                bucket, objeto, nombre_original)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """,
        (
            devolucion_id, usuario["id"], tipo, etapa,
            comentario or None,
            None if tipo == "comentario" else "pendiente-gcs",
            None if tipo == "comentario" else f"devoluciones/{devolucion_id}/{nombre_archivo}",
            nombre_archivo or None,
        ),
    )
    registrar_bitacora("alta_evidencia", "devoluciones", devolucion_id,
                       f"Se agrego una evidencia de tipo {tipo}")
    flash("Evidencia registrada.", "ok")
    return redirect(url_for("devoluciones.detalle", devolucion_id=devolucion_id))


@bp.post("/<int:devolucion_id>/resolver")
@roles_required(ANALISTA)
def resolver(devolucion_id):
    """Autoriza, rechaza o solicita informacion adicional (RF-10, UC-09)."""
    expediente = obtener_expediente(devolucion_id)
    if expediente is None:
        abort(404)
    if expediente["estado"] not in ESTADOS_REVISABLES:
        flash(f"La devolucion ya no esta en revision (estado actual: {expediente['estado']}).",
              "error")
        return redirect(url_for("devoluciones.detalle", devolucion_id=devolucion_id))

    decision = request.form.get("decision")
    justificacion = (request.form.get("justificacion") or "").strip()
    usuario = usuario_actual()

    if decision == "autorizar":
        ejecutar(
            """
            UPDATE devoluciones
               SET estado = 'autorizada', analista_id = %s,
                   fecha_autorizacion = CURRENT_TIMESTAMP
             WHERE id = %s
            """,
            (usuario["id"], devolucion_id),
        )
        registrar_bitacora("autorizacion", "devoluciones", devolucion_id,
                           f"Devolucion autorizada. {justificacion}".strip())
        flash("Devolucion autorizada.", "ok")

    elif decision == "rechazar":
        if not justificacion:
            flash("Indica el motivo del rechazo.", "error")
            return redirect(url_for("devoluciones.detalle", devolucion_id=devolucion_id))
        ejecutar(
            "UPDATE devoluciones SET estado = 'rechazada', analista_id = %s WHERE id = %s",
            (usuario["id"], devolucion_id),
        )
        registrar_bitacora("rechazo", "devoluciones", devolucion_id,
                           f"Devolucion rechazada. {justificacion}")
        flash("Devolucion rechazada.", "ok")

    elif decision == "informacion":
        ejecutar(
            "UPDATE devoluciones SET estado = 'en_revision', analista_id = %s WHERE id = %s",
            (usuario["id"], devolucion_id),
        )
        registrar_bitacora("solicitud_informacion", "devoluciones", devolucion_id,
                           f"Se solicito informacion adicional. {justificacion}".strip())
        flash("Se solicito informacion adicional al cliente.", "ok")

    else:
        abort(400)

    return redirect(url_for("devoluciones.detalle", devolucion_id=devolucion_id))
