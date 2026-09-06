"""Panel principal, panel basico de causas, costos y bitacora de auditoria.

Trazabilidad: RF-26 (version basica), RF-27, RF-30, HU-27, UC-22, UC-23, UC-26
"""
from flask import Blueprint, render_template, request

from app.db import consultar
from app.security import (
    ADMINISTRADOR, ANALISTA, CLIENTE, ENCARGADO_REEMBOLSOS, TODOS_LOS_ROLES,
    login_required, roles_required, usuario_actual,
)

bp = Blueprint("panel", __name__)


@bp.get("/panel")
@roles_required(*TODOS_LOS_ROLES)
def principal():
    usuario = usuario_actual()

    if usuario["rol"] == CLIENTE:
        resumen = consultar(
            """
            SELECT d.estado, COUNT(*) AS total
              FROM devoluciones d
              JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
              JOIN ventas v         ON v.id = vd.venta_id
             WHERE v.cliente_id = %s AND d.eliminado_en IS NULL
             GROUP BY d.estado
            """,
            (usuario["id"],),
        )
        recientes = consultar(
            """
            SELECT d.id, d.folio_devolucion, d.estado, d.fecha_solicitud,
                   p.nombre AS producto
              FROM devoluciones d
              JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
              JOIN ventas v         ON v.id = vd.venta_id
              JOIN lotes l          ON l.id = vd.lote_id
              JOIN productos p      ON p.id = l.producto_id
             WHERE v.cliente_id = %s AND d.eliminado_en IS NULL
             ORDER BY d.fecha_solicitud DESC LIMIT 10
            """,
            (usuario["id"],),
        )
        return render_template("panel/cliente.html", resumen=resumen, recientes=recientes)

    resumen = consultar(
        "SELECT estado, COUNT(*) AS total FROM devoluciones "
        "WHERE eliminado_en IS NULL GROUP BY estado"
    )
    recientes = consultar(
        """
        SELECT d.id, d.folio_devolucion, d.estado, d.fecha_solicitud,
               p.nombre AS producto, p.clasificacion_temperatura,
               m.nombre AS motivo, cli.nombre AS cliente
          FROM devoluciones d
          JOIN motivos m        ON m.id = d.motivo_id
          JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
          JOIN ventas v         ON v.id = vd.venta_id
          JOIN usuarios cli     ON cli.id = v.cliente_id
          JOIN lotes l          ON l.id = vd.lote_id
          JOIN productos p      ON p.id = l.producto_id
         WHERE d.eliminado_en IS NULL
         ORDER BY d.fecha_solicitud DESC LIMIT 10
        """
    )
    total = sum(f["total"] for f in resumen) or 0
    return render_template("panel/interno.html", resumen=resumen,
                           recientes=recientes, total=total)


@bp.get("/panel/causas")
@roles_required(ANALISTA, ADMINISTRADOR)
def causas():
    """Panel basico de causas: agrupacion por motivo, producto, lote y proveedor.

    Es la version inicial de RF-26. El analisis de Pareto, el agrupamiento
    automatico y el ranking de causas se implementan en el microservicio de
    causa raiz durante el segundo y tercer parcial.
    """
    def agrupar(sql):
        return consultar(sql)

    por_motivo = agrupar(
        """
        SELECT m.nombre AS etiqueta, COUNT(*) AS total
          FROM devoluciones d JOIN motivos m ON m.id = d.motivo_id
         WHERE d.eliminado_en IS NULL
         GROUP BY m.nombre ORDER BY total DESC
        """
    )
    por_producto = agrupar(
        """
        SELECT p.nombre AS etiqueta, COUNT(*) AS total
          FROM devoluciones d
          JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
          JOIN lotes l ON l.id = vd.lote_id JOIN productos p ON p.id = l.producto_id
         WHERE d.eliminado_en IS NULL
         GROUP BY p.nombre ORDER BY total DESC LIMIT 10
        """
    )
    por_lote = agrupar(
        """
        SELECT l.numero_lote AS etiqueta, COUNT(*) AS total
          FROM devoluciones d
          JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
          JOIN lotes l ON l.id = vd.lote_id
         WHERE d.eliminado_en IS NULL
         GROUP BY l.numero_lote ORDER BY total DESC LIMIT 10
        """
    )
    por_proveedor = agrupar(
        """
        SELECT pr.nombre AS etiqueta, COUNT(*) AS total
          FROM devoluciones d
          JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
          JOIN lotes l ON l.id = vd.lote_id JOIN proveedores pr ON pr.id = l.proveedor_id
         WHERE d.eliminado_en IS NULL
         GROUP BY pr.nombre ORDER BY total DESC
        """
    )
    por_clasificacion = agrupar(
        """
        SELECT p.clasificacion_temperatura AS etiqueta, COUNT(*) AS total
          FROM devoluciones d
          JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
          JOIN lotes l ON l.id = vd.lote_id JOIN productos p ON p.id = l.producto_id
         WHERE d.eliminado_en IS NULL
         GROUP BY p.clasificacion_temperatura ORDER BY total DESC
        """
    )
    return render_template("panel/causas.html", por_motivo=por_motivo,
                           por_producto=por_producto, por_lote=por_lote,
                           por_proveedor=por_proveedor, por_clasificacion=por_clasificacion)


@bp.get("/panel/costos")
@roles_required(ANALISTA, ENCARGADO_REEMBOLSOS, ADMINISTRADOR)
def costos():
    """Costos acumulados por etapa del proceso (RF-27, UC-23)."""
    por_etapa = consultar(
        "SELECT etapa, COUNT(*) AS casos, SUM(monto) AS total "
        "FROM costos GROUP BY etapa ORDER BY total DESC"
    )
    detalle = consultar(
        """
        SELECT c.etapa, c.monto, c.fecha, d.folio_devolucion, d.id AS devolucion_id
          FROM costos c JOIN devoluciones d ON d.id = c.devolucion_id
         ORDER BY c.fecha DESC, c.id DESC LIMIT 100
        """
    )
    total_general = sum((f["total"] or 0) for f in por_etapa)
    return render_template("panel/costos.html", por_etapa=por_etapa,
                           detalle=detalle, total_general=total_general)


@bp.get("/bitacora")
@roles_required(ADMINISTRADOR, ANALISTA)
def bitacora():
    """Consulta de la bitacora de auditoria (RF-30, HU-27, UC-26)."""
    accion = (request.args.get("accion") or "").strip()
    entidad = (request.args.get("entidad") or "").strip()

    condiciones, parametros = ["1 = 1"], []
    if accion:
        condiciones.append("b.accion = %s")
        parametros.append(accion)
    if entidad:
        condiciones.append("b.entidad = %s")
        parametros.append(entidad)

    registros = consultar(
        f"""
        SELECT b.id, b.accion, b.entidad, b.entidad_id, b.detalle,
               b.correlation_id, b.ip_origen, b.fecha, u.nombre AS usuario
          FROM bitacora b LEFT JOIN usuarios u ON u.id = b.usuario_id
         WHERE {' AND '.join(condiciones)}
         ORDER BY b.fecha DESC LIMIT 200
        """,
        tuple(parametros),
    )
    acciones = consultar("SELECT DISTINCT accion FROM bitacora ORDER BY accion")
    entidades = consultar("SELECT DISTINCT entidad FROM bitacora ORDER BY entidad")
    return render_template("panel/bitacora.html", registros=registros,
                           acciones=acciones, entidades=entidades,
                           accion=accion, entidad=entidad)
