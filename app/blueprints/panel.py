"""Panel principal, analisis de causa raiz, costos y bitacora de auditoria.

Trazabilidad: RF-23, RF-24, RF-26, RF-27, RF-30, RN-09, RN-10,
              HU-27, UC-22, UC-23, UC-26
"""
from flask import Blueprint, render_template, request

from app.db import consultar
from app.security import (
    ADMINISTRADOR, ANALISTA, CLIENTE, ENCARGADO_REEMBOLSOS, TODOS_LOS_ROLES,
    login_required, roles_required, usuario_actual,
)

bp = Blueprint("panel", __name__)

# =============================================================================
# Filtros del panel de causas (RF-23, RF-26). Cada filtro tiene una plantilla
# para el lado de las devoluciones y, cuando aplica, otra para el lado de las
# ventas: la tasa de devolucion necesita el total vendido (denominador), que
# se calcula sobre venta_detalle sin pasar por devoluciones ni motivos.
# =============================================================================
FILTROS_CAUSA_RAIZ = [
    ("fecha_inicio", "fecha", "d.fecha_solicitud >= %s", "v.fecha_venta >= %s"),
    ("fecha_fin", "fecha",
     "d.fecha_solicitud < (%s::date + INTERVAL '1 day')",
     "v.fecha_venta < (%s::date + INTERVAL '1 day')"),
    ("producto_id", "int", "p.id = %s", "p.id = %s"),
    ("lote", "like", "l.numero_lote ILIKE %s", "l.numero_lote ILIKE %s"),
    ("proveedor_id", "int", "pr.id = %s", "pr.id = %s"),
    ("tienda_id", "int", "t.id = %s", "t.id = %s"),
    ("ruta_id", "int", "ru.id = %s", None),
    ("motivo_id", "int", "m.id = %s", None),
    ("estado", "str", "d.estado = %s", None),
]


def _leer_filtros(args):
    valores = {}
    for campo, tipo, _, _ in FILTROS_CAUSA_RAIZ:
        if tipo == "int":
            valores[campo] = args.get(campo, type=int)
        elif tipo == "like":
            texto = (args.get(campo) or "").strip()
            valores[campo] = f"%{texto}%" if texto else None
        else:
            valores[campo] = (args.get(campo) or "").strip() or None
    return valores


def _condiciones(valores, lado):
    """lado: 'devolucion' o 'venta'. Devuelve (lista_sql, parametros)."""
    indice = 2 if lado == "devolucion" else 3
    condiciones, parametros = [], []
    for fila in FILTROS_CAUSA_RAIZ:
        campo, plantilla = fila[0], fila[indice]
        valor = valores.get(campo)
        if valor and plantilla:
            condiciones.append(plantilla)
            parametros.append(valor)
    return condiciones, parametros


# Esqueleto de JOIN compartido por las consultas de causa raiz que parten de
# devoluciones. Cruza producto-lote-proveedor-tienda (RF-23) y, con LEFT JOIN
# porque una devolucion puede no tener recoleccion todavia, ruta y
# transportista (RF-24, el cruce que pide la retroalimentacion del profesor).
BASE_CAUSAS = """
      FROM devoluciones d
      JOIN motivos m        ON m.id = d.motivo_id
      JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
      JOIN ventas v         ON v.id = vd.venta_id
      JOIN tiendas t        ON t.id = v.tienda_id
      JOIN lotes l          ON l.id = vd.lote_id
      JOIN productos p      ON p.id = l.producto_id
      JOIN proveedores pr   ON pr.id = l.proveedor_id
      LEFT JOIN recolecciones rec ON rec.devolucion_id = d.id
      LEFT JOIN rutas ru          ON ru.id = rec.ruta_id
      LEFT JOIN transportistas tr ON tr.id = rec.transportista_id
"""

# Mismo cruce pero partiendo de venta_detalle, sin devoluciones ni motivos:
# es el universo completo de lo vendido, para calcular tasas (RF-23).
BASE_VENTAS = """
      FROM venta_detalle vd
      JOIN ventas v       ON v.id = vd.venta_id
      JOIN tiendas t      ON t.id = v.tienda_id
      JOIN lotes l        ON l.id = vd.lote_id
      JOIN productos p    ON p.id = l.producto_id
      JOIN proveedores pr ON pr.id = l.proveedor_id
"""


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
    """Analisis de causa raiz (RF-23, RF-24, RF-26, RN-09, RN-10).

    Cruza venta-producto-lote-proveedor-tienda-ruta-transportista-motivo,
    calcula tasas de devolucion (no solo conteos), Pareto de motivos, lotes y
    tiendas con comportamiento atipico, rutas relacionadas con dano, y el
    impacto economico por motivo usando vista_costo_devolucion. RN-09: el
    panel es apoyo para el analista, no asigna responsabilidad automaticamente.
    """
    valores = _leer_filtros(request.args)
    cond_dev, param_dev = _condiciones(valores, "devolucion")
    cond_venta, param_venta = _condiciones(valores, "venta")
    where_dev = " AND ".join(["d.eliminado_en IS NULL"] + cond_dev)
    where_venta = " AND ".join(["v.eliminado_en IS NULL"] + cond_venta)

    # --- Agrupaciones simples (RN-10: por los atributos que define el negocio) ---
    por_motivo = consultar(
        f"SELECT m.nombre AS etiqueta, COUNT(*) AS total {BASE_CAUSAS}"
        f" WHERE {where_dev} GROUP BY m.nombre ORDER BY total DESC",
        tuple(param_dev),
    )
    por_producto = consultar(
        f"SELECT p.nombre AS etiqueta, COUNT(*) AS total {BASE_CAUSAS}"
        f" WHERE {where_dev} GROUP BY p.nombre ORDER BY total DESC LIMIT 10",
        tuple(param_dev),
    )
    por_lote = consultar(
        f"SELECT l.numero_lote AS etiqueta, COUNT(*) AS total {BASE_CAUSAS}"
        f" WHERE {where_dev} GROUP BY l.numero_lote ORDER BY total DESC LIMIT 10",
        tuple(param_dev),
    )
    por_proveedor = consultar(
        f"SELECT pr.nombre AS etiqueta, COUNT(*) AS total {BASE_CAUSAS}"
        f" WHERE {where_dev} GROUP BY pr.nombre ORDER BY total DESC",
        tuple(param_dev),
    )
    por_tienda = consultar(
        f"SELECT t.nombre AS etiqueta, COUNT(*) AS total {BASE_CAUSAS}"
        f" WHERE {where_dev} GROUP BY t.nombre ORDER BY total DESC LIMIT 10",
        tuple(param_dev),
    )
    por_ruta = consultar(
        f"""SELECT COALESCE(ru.origen || ' -> ' || ru.destino, 'Sin ruta asignada') AS etiqueta,
                   COUNT(*) AS total
            {BASE_CAUSAS}
            WHERE {where_dev}
            GROUP BY ru.origen, ru.destino ORDER BY total DESC LIMIT 10""",
        tuple(param_dev),
    )
    por_clasificacion = consultar(
        f"SELECT p.clasificacion_temperatura AS etiqueta, COUNT(*) AS total {BASE_CAUSAS}"
        f" WHERE {where_dev} GROUP BY p.clasificacion_temperatura ORDER BY total DESC",
        tuple(param_dev),
    )

    # --- Pareto de motivos (RF-26): 20% de causas que explican la mayoria ---
    # Los porcentajes se castean a double precision: la plantilla manda
    # porcentaje_acumulado a Highcharts con |tojson, y Flask no serializa
    # Decimal (lo que devolveria ROUND sobre una division de NUMERIC).
    pareto_motivos = consultar(
        f"""
        WITH conteo AS (
            SELECT m.nombre AS etiqueta, COUNT(*) AS total {BASE_CAUSAS}
             WHERE {where_dev} GROUP BY m.nombre
        )
        SELECT etiqueta, total,
               ROUND((total * 100.0 / SUM(total) OVER ())::numeric, 1)::double precision
                   AS porcentaje,
               ROUND((SUM(total) OVER (ORDER BY total DESC
                     ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
                     * 100.0 / SUM(total) OVER ())::numeric, 1)::double precision
                   AS porcentaje_acumulado
          FROM conteo
         ORDER BY total DESC
        """,
        tuple(param_dev),
    )

    # --- Cruce multidimensional (RF-24): el hallazgo tipo
    # "68% de las devoluciones del lote L pasaron por la ruta R" ---
    cruce_causas = consultar(
        f"""
        SELECT p.nombre AS producto, l.numero_lote AS lote, pr.nombre AS proveedor,
               COALESCE(ru.origen || ' -> ' || ru.destino, 'Sin ruta asignada') AS ruta,
               t.nombre AS tienda, COUNT(*) AS total,
               ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY l.id), 1)
                   AS porcentaje_del_lote
        {BASE_CAUSAS}
        WHERE {where_dev}
        GROUP BY p.nombre, l.id, l.numero_lote, pr.nombre, ru.origen, ru.destino, t.nombre
        ORDER BY total DESC LIMIT 20
        """,
        tuple(param_dev),
    )

    # --- Tasa de devolucion por producto (RF-23): conteo contra lo vendido,
    # tambien identifica productos reincidentes (mas devoluciones) ---
    tasa_producto = consultar(
        f"""
        WITH ventas_producto AS (
            SELECT p.id, SUM(vd.cantidad) AS unidades_vendidas {BASE_VENTAS}
             WHERE {where_venta} GROUP BY p.id
        ),
        devoluciones_producto AS (
            SELECT p.id, p.nombre AS producto, COUNT(*) AS devoluciones,
                   SUM(d.cantidad_devuelta) AS unidades_devueltas
            {BASE_CAUSAS}
            WHERE {where_dev} GROUP BY p.id, p.nombre
        )
        SELECT dp.producto, dp.devoluciones, dp.unidades_devueltas,
               COALESCE(vp.unidades_vendidas, 0) AS unidades_vendidas,
               ROUND(dp.unidades_devueltas * 100.0 / NULLIF(vp.unidades_vendidas, 0), 2)
                   AS tasa_devolucion
          FROM devoluciones_producto dp
          LEFT JOIN ventas_producto vp ON vp.id = dp.id
         ORDER BY tasa_devolucion DESC NULLS LAST LIMIT 15
        """,
        tuple(param_venta + param_dev),
    )

    # --- Lotes anomalos (RF-23): tasa del lote contra el promedio de los
    # lotes que aparecen en el mismo filtro ---
    lotes_anomalos = consultar(
        f"""
        WITH ventas_lote AS (
            SELECT l.id, SUM(vd.cantidad) AS unidades_vendidas {BASE_VENTAS}
             WHERE {where_venta} GROUP BY l.id
        ),
        devoluciones_lote AS (
            SELECT l.id, l.numero_lote, p.nombre AS producto, pr.nombre AS proveedor,
                   COUNT(*) AS devoluciones, SUM(d.cantidad_devuelta) AS unidades_devueltas
            {BASE_CAUSAS}
            WHERE {where_dev}
            GROUP BY l.id, l.numero_lote, p.nombre, pr.nombre
        ),
        tasas AS (
            SELECT dl.numero_lote, dl.producto, dl.proveedor, dl.devoluciones,
                   COALESCE(vl.unidades_vendidas, 0) AS unidades_vendidas,
                   dl.unidades_devueltas * 100.0 / NULLIF(vl.unidades_vendidas, 0) AS tasa
              FROM devoluciones_lote dl
              LEFT JOIN ventas_lote vl ON vl.id = dl.id
             WHERE vl.unidades_vendidas IS NOT NULL
        )
        SELECT numero_lote, producto, proveedor, devoluciones, unidades_vendidas,
               ROUND(tasa, 2) AS tasa, ROUND(AVG(tasa) OVER (), 2) AS tasa_promedio
          FROM tasas
         ORDER BY tasa DESC LIMIT 10
        """,
        tuple(param_venta + param_dev),
    )

    # --- Tiendas atipicas (RF-23): mismo calculo, agrupado por tienda ---
    tiendas_atipicas = consultar(
        f"""
        WITH ventas_tienda AS (
            SELECT t.id, SUM(vd.cantidad) AS unidades_vendidas {BASE_VENTAS}
             WHERE {where_venta} GROUP BY t.id
        ),
        devoluciones_tienda AS (
            SELECT t.id, t.nombre AS tienda,
                   COUNT(*) AS devoluciones, SUM(d.cantidad_devuelta) AS unidades_devueltas
            {BASE_CAUSAS}
            WHERE {where_dev}
            GROUP BY t.id, t.nombre
        ),
        tasas AS (
            SELECT dt.tienda, dt.devoluciones,
                   COALESCE(vt.unidades_vendidas, 0) AS unidades_vendidas,
                   dt.unidades_devueltas * 100.0 / NULLIF(vt.unidades_vendidas, 0) AS tasa
              FROM devoluciones_tienda dt
              LEFT JOIN ventas_tienda vt ON vt.id = dt.id
             WHERE vt.unidades_vendidas IS NOT NULL
        )
        SELECT tienda, devoluciones, unidades_vendidas,
               ROUND(tasa, 2) AS tasa, ROUND(AVG(tasa) OVER (), 2) AS tasa_promedio
          FROM tasas
         ORDER BY tasa DESC LIMIT 10
        """,
        tuple(param_venta + param_dev),
    )

    # --- Rutas relacionadas con dano (RF-23): recolecciones cuya inspeccion
    # marco el producto como no apto para inventario ---
    rutas_dano = consultar(
        f"""
        SELECT COALESCE(ru.origen || ' -> ' || ru.destino, 'Sin ruta asignada') AS ruta,
               tr.nombre AS transportista, COUNT(*) AS total_recolecciones,
               COUNT(*) FILTER (WHERE ir.apto_para_inventario = FALSE) AS no_aptas,
               ROUND(COUNT(*) FILTER (WHERE ir.apto_para_inventario = FALSE) * 100.0
                     / COUNT(*), 1) AS porcentaje_dano
        {BASE_CAUSAS}
        LEFT JOIN inspecciones_ref ir ON ir.devolucion_id = d.id
        WHERE {where_dev} AND ru.id IS NOT NULL
        GROUP BY ru.origen, ru.destino, tr.nombre
        HAVING COUNT(*) FILTER (WHERE ir.apto_para_inventario = FALSE) > 0
        ORDER BY porcentaje_dano DESC LIMIT 10
        """,
        tuple(param_dev),
    )

    # --- Costo por causa (RF-26, RF-27): impacto economico, no solo conteo ---
    # Cast a double precision: la plantilla manda esta serie a Highcharts con
    # |tojson, y el codificador JSON de Flask no serializa Decimal (NUMERIC).
    costo_por_causa = consultar(
        f"""
        SELECT m.nombre AS motivo, COUNT(*) AS casos,
               COALESCE(SUM(vcd.costo_total), 0)::double precision AS costo_total
        {BASE_CAUSAS}
        LEFT JOIN vista_costo_devolucion vcd ON vcd.devolucion_id = d.id
        WHERE {where_dev}
        GROUP BY m.nombre ORDER BY costo_total DESC
        """,
        tuple(param_dev),
    )

    # Catalogos para el formulario de filtros.
    productos = consultar("SELECT id, nombre FROM productos WHERE activo = TRUE ORDER BY nombre")
    proveedores = consultar("SELECT id, nombre FROM proveedores WHERE activo = TRUE ORDER BY nombre")
    tiendas = consultar("SELECT id, nombre FROM tiendas WHERE activo = TRUE ORDER BY nombre")
    rutas = consultar("SELECT id, origen, destino FROM rutas WHERE activo = TRUE ORDER BY origen")
    motivos = consultar("SELECT id, nombre FROM motivos WHERE activo = TRUE ORDER BY nombre")

    return render_template(
        "panel/causas.html",
        filtros=valores,
        por_motivo=por_motivo, por_producto=por_producto, por_lote=por_lote,
        por_proveedor=por_proveedor, por_tienda=por_tienda, por_ruta=por_ruta,
        por_clasificacion=por_clasificacion, pareto_motivos=pareto_motivos,
        cruce_causas=cruce_causas, tasa_producto=tasa_producto,
        lotes_anomalos=lotes_anomalos, tiendas_atipicas=tiendas_atipicas,
        rutas_dano=rutas_dano, costo_por_causa=costo_por_causa,
        productos=productos, proveedores=proveedores, tiendas=tiendas,
        rutas=rutas, motivos=motivos,
    )


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
    # Top de devoluciones con mayor costo total, usando la vista de la
    # migracion 010 (no se recalcula el desglose aqui).
    mas_costosas = consultar(
        """
        SELECT d.id AS devolucion_id, d.folio_devolucion, p.nombre AS producto,
               v.costo_transporte, v.costo_inspeccion, v.costo_almacenamiento,
               v.costo_reacondicionamiento, v.costo_destruccion,
               v.monto_reembolsado, v.costo_otros, v.costo_total
          FROM vista_costo_devolucion v
          JOIN devoluciones d   ON d.id = v.devolucion_id
          JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
          JOIN lotes l          ON l.id = vd.lote_id
          JOIN productos p      ON p.id = l.producto_id
         WHERE d.eliminado_en IS NULL
         ORDER BY v.costo_total DESC LIMIT 15
        """
    )
    total_general = sum((f["total"] or 0) for f in por_etapa)
    return render_template("panel/costos.html", por_etapa=por_etapa,
                           detalle=detalle, mas_costosas=mas_costosas,
                           total_general=total_general)


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
