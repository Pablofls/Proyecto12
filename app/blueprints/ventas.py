"""Consulta de ventas y su detalle. Es el punto de entrada de toda devolucion.

Trazabilidad: RF-06, RN-01, HU-06, UC-06
"""
from flask import Blueprint, abort, render_template, request

from app.db import consultar
from app.security import CLIENTE, TODOS_LOS_ROLES, login_required, roles_required, usuario_actual

bp = Blueprint("ventas", __name__, url_prefix="/ventas")


@bp.get("/")
@roles_required(*TODOS_LOS_ROLES)
def listar():
    """El cliente ve unicamente sus compras; el personal interno ve todas."""
    usuario = usuario_actual()
    busqueda = (request.args.get("q") or "").strip()

    condiciones = ["v.eliminado_en IS NULL"]
    parametros = []

    if usuario["rol"] == CLIENTE:
        condiciones.append("v.cliente_id = %s")
        parametros.append(usuario["id"])

    if busqueda:
        condiciones.append("v.folio_venta ILIKE %s")
        parametros.append(f"%{busqueda}%")

    ventas = consultar(
        f"""
        SELECT v.id, v.folio_venta, v.fecha_venta,
               u.nombre AS cliente, t.nombre AS tienda,
               COUNT(vd.id)                       AS lineas,
               COALESCE(SUM(vd.precio_unitario * vd.cantidad), 0) AS total
          FROM ventas v
          JOIN usuarios u       ON u.id = v.cliente_id
          JOIN tiendas t        ON t.id = v.tienda_id
          LEFT JOIN venta_detalle vd ON vd.venta_id = v.id
         WHERE {' AND '.join(condiciones)}
         GROUP BY v.id, u.nombre, t.nombre
         ORDER BY v.fecha_venta DESC, v.id DESC
         LIMIT 100
        """,
        tuple(parametros),
    )
    return render_template("ventas/listar.html", ventas=ventas, busqueda=busqueda)


@bp.get("/<int:venta_id>")
@roles_required(*TODOS_LOS_ROLES)
def detalle(venta_id):
    usuario = usuario_actual()
    venta = consultar(
        """
        SELECT v.id, v.folio_venta, v.fecha_venta, v.cliente_id,
               u.nombre AS cliente, t.nombre AS tienda
          FROM ventas v
          JOIN usuarios u ON u.id = v.cliente_id
          JOIN tiendas t  ON t.id = v.tienda_id
         WHERE v.id = %s AND v.eliminado_en IS NULL
        """,
        (venta_id,), uno=True,
    )
    if venta is None:
        abort(404)
    # Autorizacion por recurso: el cliente solo consulta sus propias ventas (5.3).
    if usuario["rol"] == CLIENTE and venta["cliente_id"] != usuario["id"]:
        abort(403)

    lineas = consultar(
        """
        SELECT vd.id, vd.cantidad, vd.precio_unitario,
               p.nombre AS producto, p.sku, p.clasificacion_temperatura,
               l.numero_lote, l.fecha_caducidad, pr.nombre AS proveedor,
               (SELECT COALESCE(SUM(d.cantidad_devuelta), 0)
                  FROM devoluciones d
                 WHERE d.venta_detalle_id = vd.id
                   AND d.eliminado_en IS NULL
                   AND d.estado <> 'rechazada') AS ya_devuelto
          FROM venta_detalle vd
          JOIN lotes l       ON l.id = vd.lote_id
          JOIN productos p   ON p.id = l.producto_id
          JOIN proveedores pr ON pr.id = l.proveedor_id
         WHERE vd.venta_id = %s
         ORDER BY vd.id
        """,
        (venta_id,),
    )
    return render_template("ventas/detalle.html", venta=venta, lineas=lineas)
