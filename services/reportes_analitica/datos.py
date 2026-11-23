"""Consultas de reportes y series para analitica (solo lectura).

Las columnas y expresiones SQL salen de listas blancas de este modulo; los
valores del usuario viajan siempre como parametros ligados (RNF-11).
Reutiliza el mismo cruce y los mismos conteos que el panel de causas del web
(apps/web/app/blueprints/panel.py), asi el panel y los reportes no discrepan.

Trazabilidad: RF-23, RF-26, RF-27, RF-28, RN-09, RN-16.
"""
from datetime import date

import estadistica
from formatos import MAX_FILAS
from shared.infra import consultar

TOPE_FILAS = max(MAX_FILAS.values()) + 1   # una de mas para detectar el desborde

DIMENSIONES_TASA = {
    "proveedor": ("pr.id", "pr.nombre"),
    "tienda": ("t.id", "t.nombre"),
    "producto": ("p.id", "p.nombre"),
    "lote": ("l.id", "l.numero_lote || ' (' || p.nombre || ')'"),
}
COLUMNA_OBJETO = {"proveedor": "l.proveedor_id", "tienda": "v.tienda_id",
                  "producto": "l.producto_id", "lote": "vd.lote_id"}
DIMENSIONES_PARETO = ("motivo", "producto", "lote", "proveedor", "tienda", "ruta", "transportista", "estado")
MEDIDAS_PARETO = {"frecuencia": "1", "cantidad": "cantidad_devuelta", "costo": "costo_total"}

CRUCE_DEV = """
  FROM devoluciones d
  JOIN motivos m ON m.id = d.motivo_id
  JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
  JOIN ventas v ON v.id = vd.venta_id
  JOIN tiendas t ON t.id = v.tienda_id
  JOIN lotes l ON l.id = vd.lote_id
  JOIN productos p ON p.id = l.producto_id
  JOIN proveedores pr ON pr.id = l.proveedor_id
  LEFT JOIN recolecciones rec ON rec.devolucion_id = d.id
  LEFT JOIN rutas ru ON ru.id = rec.ruta_id
  LEFT JOIN transportistas tr ON tr.id = rec.transportista_id
  LEFT JOIN vista_costo_devolucion vc ON vc.devolucion_id = d.id
 WHERE d.eliminado_en IS NULL
"""


def _fechas(columna, desde, hasta):
    cond, params = "", []
    if desde:
        cond += f" AND {columna} >= %s"
        params.append(desde)
    if hasta:
        cond += f" AND {columna} < (%s::date + INTERVAL '1 day')"
        params.append(hasta)
    return cond, params


# --------------------------------------------------------------------------- #
# Reportes tabulares
# --------------------------------------------------------------------------- #
COLUMNAS = {
    "devoluciones": [("folio", "Folio", "texto"), ("fecha_solicitud", "Fecha", "fecha"),
                     ("estado", "Estado", "texto"), ("motivo", "Motivo", "texto"),
                     ("producto", "Producto", "texto"), ("lote", "Lote", "texto"),
                     ("proveedor", "Proveedor", "texto"), ("tienda", "Tienda", "texto"),
                     ("cantidad_devuelta", "Unidades", "entero"), ("costo_total", "Costo total", "dinero")],
    "costos": [("folio", "Folio", "texto"), ("fecha_solicitud", "Fecha", "fecha"),
               ("costo_transporte", "Transporte", "dinero"), ("costo_inspeccion", "Inspeccion", "dinero"),
               ("costo_almacenamiento", "Almacenamiento", "dinero"),
               ("costo_reacondicionamiento", "Reacondicionamiento", "dinero"),
               ("costo_destruccion", "Destruccion", "dinero"), ("monto_reembolsado", "Reembolso", "dinero"),
               ("costo_otros", "Otros", "dinero"), ("costo_total", "Total", "dinero")],
    "tasas": [("etiqueta", "Nombre", "texto"), ("unidades_vendidas", "Unidades vendidas", "entero"),
              ("unidades_devueltas", "Unidades devueltas", "entero"), ("devoluciones", "Casos", "entero"),
              ("tasa_pct", "Tasa (%)", "decimal")],
    "pareto": [("etiqueta", "Categoria", "texto"), ("total", "Total", "decimal"), ("casos", "Casos", "entero"),
               ("porcentaje", "% del total", "decimal"), ("porcentaje_acumulado", "% acumulado", "decimal")],
    "tendencia": [("mes", "Mes", "texto"), ("unidades_vendidas", "Unidades vendidas", "entero"),
                  ("unidades_devueltas", "Unidades devueltas", "entero"), ("valor", "Valor", "decimal"),
                  ("estado", "Estado del dato", "texto")],
}


def reporte_devoluciones(desde, hasta, estado, proveedor_id, tienda_id):
    cond, params = _fechas("d.fecha_solicitud", desde, hasta)
    for valor, sql in ((estado, " AND d.estado = %s"), (proveedor_id, " AND pr.id = %s"),
                       (tienda_id, " AND t.id = %s")):
        if valor is not None:
            cond += sql
            params.append(valor)
    return consultar(f"""
        SELECT d.folio_devolucion AS folio, d.fecha_solicitud::date AS fecha_solicitud, d.estado,
               m.nombre AS motivo, p.nombre AS producto, l.numero_lote AS lote, pr.nombre AS proveedor,
               t.nombre AS tienda, d.cantidad_devuelta, COALESCE(vc.costo_total, 0) AS costo_total
        {CRUCE_DEV}{cond} ORDER BY d.fecha_solicitud DESC, d.id DESC LIMIT %s""",
                     tuple(params) + (TOPE_FILAS,))


def reporte_costos(desde, hasta):
    cond, params = _fechas("d.fecha_solicitud", desde, hasta)
    return consultar(f"""
        SELECT d.folio_devolucion AS folio, d.fecha_solicitud::date AS fecha_solicitud,
               vc.costo_transporte, vc.costo_inspeccion, vc.costo_almacenamiento,
               vc.costo_reacondicionamiento, vc.costo_destruccion, vc.monto_reembolsado,
               vc.costo_otros, vc.costo_total
          FROM devoluciones d JOIN vista_costo_devolucion vc ON vc.devolucion_id = d.id
         WHERE d.eliminado_en IS NULL{cond} ORDER BY d.fecha_solicitud DESC, d.id DESC LIMIT %s""",
                     tuple(params) + (TOPE_FILAS,))


def tasas_por(dimension, desde, hasta):
    """Unidades devueltas entre vendidas por proveedor, tienda, producto o lote."""
    clave, etiqueta = DIMENSIONES_TASA[dimension]
    c_dev, p_dev = _fechas("fecha_solicitud", desde, hasta)
    c_ven, p_ven = _fechas("v.fecha_venta", desde, hasta)
    filas = consultar(f"""
        WITH dev AS (SELECT venta_detalle_id, SUM(cantidad_devuelta) AS u, COUNT(*) AS c
                       FROM devoluciones WHERE eliminado_en IS NULL{c_dev} GROUP BY venta_detalle_id)
        SELECT {clave} AS id, {etiqueta} AS etiqueta, SUM(vd.cantidad) AS unidades_vendidas,
               COALESCE(SUM(dev.u), 0) AS unidades_devueltas, COALESCE(SUM(dev.c), 0) AS devoluciones
          FROM venta_detalle vd JOIN ventas v ON v.id = vd.venta_id
          JOIN tiendas t ON t.id = v.tienda_id JOIN lotes l ON l.id = vd.lote_id
          JOIN productos p ON p.id = l.producto_id JOIN proveedores pr ON pr.id = l.proveedor_id
          LEFT JOIN dev ON dev.venta_detalle_id = vd.id
         WHERE v.eliminado_en IS NULL{c_ven} GROUP BY {clave}, {etiqueta}""",
                     tuple(p_dev + p_ven))
    for f in filas:
        f["unidades_vendidas"], f["unidades_devueltas"] = int(f["unidades_vendidas"]), int(f["unidades_devueltas"])
        f["devoluciones"] = int(f["devoluciones"])
        f["tasa_pct"] = estadistica.tasa(f["unidades_devueltas"], f["unidades_vendidas"])
    filas.sort(key=lambda f: (f["tasa_pct"] is None, -(f["tasa_pct"] or 0), f["etiqueta"]))
    return filas


def tasas_cruzadas(dimension_a, dimension_b, desde, hasta):
    """Unidades vendidas y devueltas por cada combinacion de dos factores (mismos conteos que tasas_por).

    Solo las dimensiones con venta (proveedor, tienda, producto, lote): la tasa necesita un denominador.
    """
    clave_a, etiqueta_a = DIMENSIONES_TASA[dimension_a]
    clave_b, etiqueta_b = DIMENSIONES_TASA[dimension_b]
    c_dev, p_dev = _fechas("fecha_solicitud", desde, hasta)
    c_ven, p_ven = _fechas("v.fecha_venta", desde, hasta)
    filas = consultar(f"""
        WITH dev AS (SELECT venta_detalle_id, SUM(cantidad_devuelta) AS u, COUNT(*) AS c
                       FROM devoluciones WHERE eliminado_en IS NULL{c_dev} GROUP BY venta_detalle_id)
        SELECT {clave_a} AS a_id, {etiqueta_a} AS a_etiqueta, {clave_b} AS b_id, {etiqueta_b} AS b_etiqueta,
               SUM(vd.cantidad) AS unidades_vendidas, COALESCE(SUM(dev.u), 0) AS unidades_devueltas,
               COALESCE(SUM(dev.c), 0) AS devoluciones
          FROM venta_detalle vd JOIN ventas v ON v.id = vd.venta_id
          JOIN tiendas t ON t.id = v.tienda_id JOIN lotes l ON l.id = vd.lote_id
          JOIN productos p ON p.id = l.producto_id JOIN proveedores pr ON pr.id = l.proveedor_id
          LEFT JOIN dev ON dev.venta_detalle_id = vd.id
         WHERE v.eliminado_en IS NULL{c_ven}
         GROUP BY {clave_a}, {etiqueta_a}, {clave_b}, {etiqueta_b}""", tuple(p_dev + p_ven))
    for f in filas:
        f["unidades_vendidas"], f["unidades_devueltas"] = int(f["unidades_vendidas"]), int(f["unidades_devueltas"])
        f["devoluciones"] = int(f["devoluciones"])
    return filas


def pareto(dimension, medida, desde, hasta):
    """Pareto por SQL: una fila por devolucion y se agrupa por la dimension elegida."""
    exprs = {"motivo": "m.nombre", "producto": "p.nombre", "lote": "l.numero_lote || ' (' || p.nombre || ')'",
             "proveedor": "pr.nombre", "tienda": "t.nombre",
             "ruta": "COALESCE(ru.origen || ' -> ' || ru.destino, 'Sin ruta asignada')",
             "transportista": "COALESCE(tr.nombre, 'Sin transportista')", "estado": "d.estado"}
    cond, params = _fechas("d.fecha_solicitud", desde, hasta)
    suma = MEDIDAS_PARETO[medida]
    filas = consultar(f"""
        SELECT etiqueta, SUM({suma}) AS total, COUNT(*) AS casos FROM (
            SELECT {exprs[dimension]} AS etiqueta, d.cantidad_devuelta, COALESCE(vc.costo_total, 0) AS costo_total
            {CRUCE_DEV}{cond}) x GROUP BY etiqueta""", tuple(params))
    return estadistica.pareto([(f["etiqueta"], f["total"], f["casos"]) for f in filas])


# --------------------------------------------------------------------------- #
# Series mensuales
# --------------------------------------------------------------------------- #
def plazo_maximo():
    fila = consultar("SELECT MAX(dias_plazo) AS d FROM politicas_devolucion", uno=True)
    return int(fila["d"]) if fila and fila["d"] else 30


def etiqueta_objeto(dimension, referencia_id):
    sql = {"proveedor": "SELECT nombre AS e FROM proveedores WHERE id=%s",
           "tienda": "SELECT nombre AS e FROM tiendas WHERE id=%s",
           "producto": "SELECT nombre AS e FROM productos WHERE id=%s",
           "lote": "SELECT l.numero_lote || ' (' || p.nombre || ')' AS e FROM lotes l "
                   "JOIN productos p ON p.id = l.producto_id WHERE l.id=%s"}[dimension]
    fila = consultar(sql, (referencia_id,), uno=True)
    return fila["e"] if fila else None


def serie_mensual(medida, meses, dimension=None, referencia_id=None):
    """Puntos mensuales {mes, unidades_vendidas, unidades_devueltas, valor, estado}.

    tasa: por cohorte de venta, solo meses que ya maduraron (el plazo maximo de
    devolucion); un mes con menos de 20 unidades vendidas queda como
    'muestra_insuficiente' y no entra a la regresion.
    devoluciones y costo: por fecha de solicitud, solo meses completos.
    """
    hoy = date.today()
    lista = estadistica.meses_validos(hoy, meses, plazo_maximo() if medida == "tasa" else None)
    desde, hasta = lista[0] + "-01", lista[-1] + "-28"
    objeto = ""
    params_obj = []
    if dimension:
        objeto = f" AND {COLUMNA_OBJETO[dimension]} = %s"
        params_obj = [referencia_id]
    if medida == "tasa":
        filas = consultar(f"""
            WITH dev AS (SELECT venta_detalle_id, SUM(cantidad_devuelta) AS u FROM devoluciones
                          WHERE eliminado_en IS NULL GROUP BY venta_detalle_id)
            SELECT to_char(date_trunc('month', v.fecha_venta), 'YYYY-MM') AS mes,
                   SUM(vd.cantidad) AS vendidas, COALESCE(SUM(dev.u), 0) AS devueltas
              FROM venta_detalle vd JOIN ventas v ON v.id = vd.venta_id
              JOIN lotes l ON l.id = vd.lote_id LEFT JOIN dev ON dev.venta_detalle_id = vd.id
             WHERE v.eliminado_en IS NULL AND v.fecha_venta >= %s::date
               AND v.fecha_venta < (date_trunc('month', %s::date) + INTERVAL '1 month'){objeto}
             GROUP BY 1""", tuple([desde, hasta] + params_obj))
    else:
        filas = consultar(f"""
            SELECT to_char(date_trunc('month', d.fecha_solicitud), 'YYYY-MM') AS mes,
                   COUNT(*) AS casos, COALESCE(SUM(vc.costo_total), 0) AS costo
              FROM devoluciones d JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
              JOIN ventas v ON v.id = vd.venta_id JOIN lotes l ON l.id = vd.lote_id
              LEFT JOIN vista_costo_devolucion vc ON vc.devolucion_id = d.id
             WHERE d.eliminado_en IS NULL AND d.fecha_solicitud >= %s::date
               AND d.fecha_solicitud < (date_trunc('month', %s::date) + INTERVAL '1 month'){objeto}
             GROUP BY 1""", tuple([desde, hasta] + params_obj))
    por_mes = {f["mes"]: f for f in filas}
    puntos = []
    for mes in lista:
        f = por_mes.get(mes)
        if medida == "tasa":
            vendidas = int(f["vendidas"]) if f else 0
            devueltas = int(f["devueltas"]) if f else 0
            suficiente = vendidas >= estadistica.MIN_UNIDADES
            puntos.append({"mes": mes, "unidades_vendidas": vendidas, "unidades_devueltas": devueltas,
                           "valor": estadistica.tasa(devueltas, vendidas) if suficiente else None,
                           "estado": "ok" if suficiente else "muestra_insuficiente"})
        else:
            valor = float(f["casos"] if medida == "devoluciones" else f["costo"]) if f else 0.0
            puntos.append({"mes": mes, "unidades_vendidas": 0, "unidades_devueltas": 0,
                           "valor": round(valor, 2), "estado": "ok"})
    return puntos


# --------------------------------------------------------------------------- #
# Alertas de posible fraude (traidas de analisis-auditoria; RF-25)
# --------------------------------------------------------------------------- #
def alertas_fraude():
    """Senales explicables; no acusan ni bloquean. Mismos umbrales que 8008."""
    filas = consultar("""
        SELECT v.cliente_id, u.nombre AS cliente, COUNT(DISTINCT d.id) AS devoluciones_90_dias,
               COUNT(DISTINCT d.id) FILTER (WHERE d.estado = 'rechazada') AS rechazadas,
               COALESCE(SUM(rb.monto) FILTER (WHERE rb.estado = 'aprobado'), 0) AS monto_reembolsado
          FROM devoluciones d JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
          JOIN ventas v ON v.id = vd.venta_id JOIN usuarios u ON u.id = v.cliente_id
          LEFT JOIN reembolsos rb ON rb.devolucion_id = d.id AND rb.eliminado_en IS NULL
         WHERE d.eliminado_en IS NULL AND d.fecha_solicitud >= CURRENT_TIMESTAMP - INTERVAL '90 days'
         GROUP BY v.cliente_id, u.nombre
        HAVING COUNT(DISTINCT d.id) >= 3
            OR COUNT(DISTINCT d.id) FILTER (WHERE d.estado = 'rechazada') >= 2
            OR COALESCE(SUM(rb.monto) FILTER (WHERE rb.estado = 'aprobado'), 0) >= 5000
         ORDER BY devoluciones_90_dias DESC, monto_reembolsado DESC""")
    for f in filas:
        razones = []
        if f["devoluciones_90_dias"] >= 3:
            razones.append("frecuencia alta en 90 dias")
        if f["rechazadas"] >= 2:
            razones.append("multiples solicitudes rechazadas")
        if float(f["monto_reembolsado"]) >= 5000:
            razones.append("monto reembolsado elevado")
        f["razones"] = razones
        f["requiere_revision_humana"] = True
    return filas
