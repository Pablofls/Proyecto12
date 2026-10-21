"""Exportacion CSV de los reportes del sistema (RF-28, UC-24).

Cada ruta replica el control de acceso y los filtros de la pantalla de origen:
quien no puede ver el listado tampoco puede descargarlo, y el archivo contiene
exactamente lo que filtra la pantalla (sin su tope de filas de pantalla; el
tope de la exportacion esta en app/exportacion.py).

Trazabilidad: RF-28, UC-24, RF-30, RN-12, RN-13, RNF-09, RNF-11
"""
from flask import Blueprint, request

from app.blueprints.panel import _condiciones, _leer_filtros, sql_pareto
from app.db import get_conn
from app.exportacion import respuesta_csv
from app.security import (
    ADMINISTRADOR, ANALISTA, CLIENTE, ENCARGADO_REEMBOLSOS, TODOS_LOS_ROLES,
    registrar_bitacora, roles_required, usuario_actual,
)

bp = Blueprint("reportes", __name__, url_prefix="/reportes")


def _auditar(tipo, filtros):
    """Deja constancia de la exportacion (RF-30, RN-12). Solo tipo y filtros
    activos: nunca el contenido del reporte (RNF-16). La transaccion se
    confirma aqui porque el streaming termina despues de que la vista regresa."""
    activos = ", ".join(f"{k}={v}" for k, v in filtros.items() if v not in (None, ""))
    registrar_bitacora("exportar_reporte", "reportes", None,
                       f"Reporte {tipo}. Filtros: {activos or 'ninguno'}")
    get_conn().commit()


@bp.get("/devoluciones.csv")
@roles_required(*TODOS_LOS_ROLES)
def devoluciones():
    """Listado de devoluciones con los filtros de /devoluciones (+ fechas, motivo, tienda)."""
    usuario = usuario_actual()
    filtros = {
        "estado": (request.args.get("estado") or "").strip(),
        "q": (request.args.get("q") or "").strip(),
        "fecha_inicio": (request.args.get("fecha_inicio") or "").strip(),
        "fecha_fin": (request.args.get("fecha_fin") or "").strip(),
        "motivo_id": request.args.get("motivo_id", type=int),
        "tienda_id": request.args.get("tienda_id", type=int),
    }
    condiciones, parametros = ["d.eliminado_en IS NULL"], []
    if usuario["rol"] == CLIENTE:
        # Autorizacion por recurso (5.3): el cliente solo exporta sus casos.
        condiciones.append("v.cliente_id = %s")
        parametros.append(usuario["id"])
    if filtros["estado"]:
        condiciones.append("d.estado = %s")
        parametros.append(filtros["estado"])
    if filtros["q"]:
        condiciones.append("(d.folio_devolucion ILIKE %s OR p.nombre ILIKE %s)")
        parametros.extend([f"%{filtros['q']}%"] * 2)
    if filtros["fecha_inicio"]:
        condiciones.append("d.fecha_solicitud >= %s::date")
        parametros.append(filtros["fecha_inicio"])
    if filtros["fecha_fin"]:
        condiciones.append("d.fecha_solicitud < (%s::date + INTERVAL '1 day')")
        parametros.append(filtros["fecha_fin"])
    if filtros["motivo_id"]:
        condiciones.append("m.id = %s")
        parametros.append(filtros["motivo_id"])
    if filtros["tienda_id"]:
        condiciones.append("t.id = %s")
        parametros.append(filtros["tienda_id"])

    _auditar("devoluciones", filtros)
    return respuesta_csv(
        "devoluciones",
        [("Folio", "folio_devolucion"), ("Estado", "estado"),
         ("Fecha de solicitud", "fecha_solicitud"), ("Motivo", "motivo"),
         ("Tienda", "tienda"), ("Folio de venta", "folio_venta"),
         ("Producto", "producto"), ("Tipo", "clasificacion_temperatura"),
         ("Lote", "numero_lote"), ("Cliente", "cliente"),
         ("Cantidad", "cantidad_devuelta")],
        f"""
        SELECT d.folio_devolucion, d.estado, d.fecha_solicitud, m.nombre AS motivo,
               t.nombre AS tienda, v.folio_venta, p.nombre AS producto,
               p.clasificacion_temperatura, l.numero_lote, cli.nombre AS cliente,
               d.cantidad_devuelta
          FROM devoluciones d
          JOIN motivos m        ON m.id = d.motivo_id
          JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
          JOIN ventas v         ON v.id = vd.venta_id
          JOIN tiendas t        ON t.id = v.tienda_id
          JOIN usuarios cli     ON cli.id = v.cliente_id
          JOIN lotes l          ON l.id = vd.lote_id
          JOIN productos p      ON p.id = l.producto_id
         WHERE {' AND '.join(condiciones)}
         ORDER BY d.fecha_solicitud DESC, d.id DESC
        """,
        parametros,
    )


@bp.get("/costos.csv")
@roles_required(ANALISTA, ENCARGADO_REEMBOLSOS, ADMINISTRADOR)
def costos():
    """Costo por devolucion y por etapa (vista_costo_devolucion, RF-27)."""
    _auditar("costos", {})
    return respuesta_csv(
        "costos",
        [("Folio", "folio_devolucion"), ("Producto", "producto"),
         ("Transporte", "costo_transporte"), ("Inspeccion", "costo_inspeccion"),
         ("Almacenamiento", "costo_almacenamiento"),
         ("Reacondicionamiento", "costo_reacondicionamiento"),
         ("Destruccion", "costo_destruccion"),
         ("Reembolso", "monto_reembolsado"), ("Otros", "costo_otros"),
         ("Costo total", "costo_total")],
        """
        SELECT d.folio_devolucion, p.nombre AS producto,
               v.costo_transporte, v.costo_inspeccion, v.costo_almacenamiento,
               v.costo_reacondicionamiento, v.costo_destruccion,
               v.monto_reembolsado, v.costo_otros, v.costo_total
          FROM vista_costo_devolucion v
          JOIN devoluciones d   ON d.id = v.devolucion_id
          JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
          JOIN lotes l          ON l.id = vd.lote_id
          JOIN productos p      ON p.id = l.producto_id
         WHERE d.eliminado_en IS NULL
         ORDER BY v.costo_total DESC, d.id
        """,
    )


@bp.get("/causas.csv")
@roles_required(ANALISTA, ADMINISTRADOR)
def causas():
    """Pareto de motivos con los mismos filtros que /panel/causas (RF-26)."""
    valores = _leer_filtros(request.args)
    condiciones, parametros = _condiciones(valores, "devolucion")
    where_dev = " AND ".join(["d.eliminado_en IS NULL"] + condiciones)
    _auditar("causas_pareto", valores)
    return respuesta_csv(
        "causas_pareto",
        [("Motivo", "etiqueta"), ("Devoluciones", "total"),
         ("Porcentaje", "porcentaje"), ("Porcentaje acumulado", "porcentaje_acumulado")],
        sql_pareto(where_dev),
        parametros,
    )


@bp.get("/bitacora.csv")
@roles_required(ADMINISTRADOR, ANALISTA)
def bitacora():
    """Bitacora de auditoria con los filtros de /bitacora (RF-30)."""
    filtros = {
        "accion": (request.args.get("accion") or "").strip(),
        "entidad": (request.args.get("entidad") or "").strip(),
    }
    condiciones, parametros = ["1 = 1"], []
    if filtros["accion"]:
        condiciones.append("b.accion = %s")
        parametros.append(filtros["accion"])
    if filtros["entidad"]:
        condiciones.append("b.entidad = %s")
        parametros.append(filtros["entidad"])
    _auditar("bitacora", filtros)
    return respuesta_csv(
        "bitacora",
        [("Fecha", "fecha"), ("Usuario", "usuario"), ("Accion", "accion"),
         ("Entidad", "entidad"), ("Id entidad", "entidad_id"), ("Detalle", "detalle"),
         ("Correlacion", "correlation_id"), ("IP", "ip_origen")],
        f"""
        SELECT b.fecha, u.nombre AS usuario, b.accion, b.entidad, b.entidad_id,
               b.detalle, b.correlation_id, b.ip_origen
          FROM bitacora b LEFT JOIN usuarios u ON u.id = b.usuario_id
         WHERE {' AND '.join(condiciones)}
         ORDER BY b.fecha DESC, b.id DESC
        """,
        parametros,
    )


@bp.get("/reembolsos.csv")
@roles_required(ENCARGADO_REEMBOLSOS, ANALISTA)
def reembolsos():
    """Reembolsos registrados (aprobados y rechazados), como /reembolsos."""
    _auditar("reembolsos", {})
    return respuesta_csv(
        "reembolsos",
        [("Folio", "folio_devolucion"), ("Cliente", "cliente"), ("Estado", "estado"),
         ("Monto", "monto"), ("Metodo", "metodo"), ("Encargado", "encargado"),
         ("Fecha de resolucion", "fecha_resolucion")],
        """
        SELECT d.folio_devolucion, cli.nombre AS cliente, rb.estado, rb.monto,
               rb.metodo, u.nombre AS encargado, rb.fecha_resolucion
          FROM reembolsos rb
          JOIN devoluciones d   ON d.id = rb.devolucion_id
          JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
          JOIN ventas v         ON v.id = vd.venta_id
          JOIN usuarios cli     ON cli.id = v.cliente_id
          JOIN usuarios u       ON u.id = rb.encargado_id
         WHERE rb.eliminado_en IS NULL
         ORDER BY rb.id DESC
        """,
    )
