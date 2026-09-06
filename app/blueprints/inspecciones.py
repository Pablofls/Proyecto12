"""Inspeccion del producto, decision de disposicion e inventario recuperado.

La inspeccion es el punto donde se determina si el producto puede volver al
inventario. El veredicto se calcula aqui y se guarda en la columna
inspecciones_ref.apto_para_inventario, que es la que el trigger de PostgreSQL
consulta para impedir una disposicion invalida (RN-06, RN-07).

Trazabilidad: RF-16, RF-17, RF-18, RF-19, RN-05, RN-06, RN-07,
              HU-14 a HU-17, UC-14, UC-15, UC-16
"""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
import psycopg2

from app.db import consultar, ejecutar, get_conn
from app.security import (
    ANALISTA, ENCARGADO_CENTRO, INSPECTOR, registrar_bitacora, roles_required, usuario_actual,
)
from app.blueprints.devoluciones import cambiar_estado, obtener_expediente

bp = Blueprint("inspecciones", __name__, url_prefix="/inspecciones")

# Tiempo maximo que un producto refrigerado puede permanecer fuera de
# refrigeracion antes de considerarse no apto para inventario (RN-06).
# Se deja como constante del modulo para poder ajustarla por categoria cuando
# el catalogo de productos incorpore ese dato.
MINUTOS_MAX_FUERA_REFRIGERACION = 240

DESTINOS = [
    ("inventario", "Regresar a inventario"),
    ("reparacion", "Reparacion"),
    ("reacondicionamiento", "Reacondicionamiento"),
    ("reciclaje", "Reciclaje"),
    ("devolucion_proveedor", "Devolucion al proveedor"),
    ("desecho", "Desecho"),
]


def evaluar_aptitud(refrigerado, danos, caducidad_vencida, cadena_frio_rota, minutos_fuera):
    """Aplica RN-06 y RN-07. Devuelve (apto, motivos).

    Un producto con danos fisicos visibles o caducidad vencida nunca es apto.
    Si ademas es refrigerado, se revisa la cadena de frio y el tiempo fuera de
    refrigeracion.
    """
    motivos = []
    if danos:
        motivos.append("danos fisicos visibles")
    if caducidad_vencida:
        motivos.append("fecha de caducidad vencida")
    if refrigerado:
        if cadena_frio_rota:
            motivos.append("ruptura documentada de la cadena de frio")
        if minutos_fuera is not None and minutos_fuera > MINUTOS_MAX_FUERA_REFRIGERACION:
            motivos.append(
                f"permanecio {minutos_fuera} minutos fuera de refrigeracion "
                f"(limite {MINUTOS_MAX_FUERA_REFRIGERACION})"
            )
    return (len(motivos) == 0), motivos


@bp.get("/")
@roles_required(INSPECTOR, ANALISTA, ENCARGADO_CENTRO)
def listar():
    """Cola de trabajo del inspector: productos recibidos sin inspeccionar."""
    pendientes = consultar(
        """
        SELECT d.id, d.folio_devolucion, d.estado, p.nombre AS producto,
               p.clasificacion_temperatura, l.numero_lote, l.fecha_caducidad,
               m.nombre AS motivo
          FROM devoluciones d
          JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
          JOIN lotes l          ON l.id = vd.lote_id
          JOIN productos p      ON p.id = l.producto_id
          JOIN motivos m        ON m.id = d.motivo_id
         WHERE d.estado IN ('recibida', 'en_inspeccion')
           AND d.eliminado_en IS NULL
           AND NOT EXISTS (SELECT 1 FROM inspecciones_ref i WHERE i.devolucion_id = d.id)
         ORDER BY d.fecha_solicitud
        """
    )
    realizadas = consultar(
        """
        SELECT i.id, i.fecha_inspeccion, i.resultado_general, i.apto_para_inventario,
               d.id AS devolucion_id, d.folio_devolucion,
               p.nombre AS producto, u.nombre AS inspector
          FROM inspecciones_ref i
          JOIN devoluciones d   ON d.id = i.devolucion_id
          JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
          JOIN lotes l          ON l.id = vd.lote_id
          JOIN productos p      ON p.id = l.producto_id
          JOIN usuarios u       ON u.id = i.inspector_id
         WHERE d.eliminado_en IS NULL
         ORDER BY i.fecha_inspeccion DESC
         LIMIT 50
        """
    )
    return render_template("inspecciones/listar.html", pendientes=pendientes,
                           realizadas=realizadas)


@bp.route("/<int:devolucion_id>/registrar", methods=["GET", "POST"])
@roles_required(INSPECTOR)
def registrar(devolucion_id):
    """Registra la inspeccion. Los campos obligatorios dependen de si el
    producto es refrigerado o no (RN-05)."""
    expediente = obtener_expediente(devolucion_id)
    if expediente is None:
        abort(404)
    if expediente["estado"] not in ("recibida", "en_inspeccion"):
        flash("Solo se puede inspeccionar un producto ya recibido en el centro.", "error")
        return redirect(url_for("devoluciones.detalle", devolucion_id=devolucion_id))

    ya_existe = consultar("SELECT id FROM inspecciones_ref WHERE devolucion_id = %s",
                          (devolucion_id,), uno=True)
    if ya_existe:
        flash("Esta devolucion ya tiene una inspeccion registrada.", "aviso")
        return redirect(url_for("devoluciones.detalle", devolucion_id=devolucion_id))

    refrigerado = expediente["clasificacion_temperatura"] == "refrigerado"

    if request.method == "POST":
        danos = request.form.get("danos") == "si"
        caducidad_vencida = request.form.get("caducidad_vencida") == "si"
        estado_empaque = (request.form.get("estado_empaque") or "").strip()
        observaciones = (request.form.get("observaciones") or "").strip()

        cadena_frio_rota = False
        minutos_fuera = None
        temperatura = None
        if refrigerado:
            cadena_frio_rota = request.form.get("cadena_frio_rota") == "si"
            minutos_fuera = request.form.get("minutos_fuera", type=int)
            temperatura = request.form.get("temperatura_recepcion", type=float)
            if minutos_fuera is None or temperatura is None:
                flash("En un producto refrigerado la temperatura y el tiempo fuera de "
                      "refrigeracion son obligatorios (RN-05).", "error")
                return render_template("inspecciones/registrar.html", d=expediente,
                                       refrigerado=refrigerado), 400
        if not estado_empaque:
            flash("Describe el estado del empaque.", "error")
            return render_template("inspecciones/registrar.html", d=expediente,
                                   refrigerado=refrigerado), 400

        apto, motivos = evaluar_aptitud(refrigerado, danos, caducidad_vencida,
                                        cadena_frio_rota, minutos_fuera)
        resultado = "apto para inventario" if apto else "no apto: " + "; ".join(motivos)

        # El detalle extenso de la inspeccion vivira en MongoDB (4.4). Mientras
        # esa coleccion no se habilita, se conserva en el resumen y en la
        # evidencia asociada, y mongo_doc_id queda en NULL.
        ejecutar(
            """
            INSERT INTO inspecciones_ref (devolucion_id, inspector_id, resultado_general,
                                          apto_para_inventario, mongo_doc_id)
            VALUES (%s, %s, %s, %s, NULL)
            """,
            (devolucion_id, usuario_actual()["id"], resultado[:50], apto),
        )

        detalle_partes = [f"Empaque: {estado_empaque}"]
        if refrigerado:
            detalle_partes.append(f"Temperatura de recepcion: {temperatura} C")
            detalle_partes.append(f"Minutos fuera de refrigeracion: {minutos_fuera}")
            detalle_partes.append(f"Cadena de frio rota: {'si' if cadena_frio_rota else 'no'}")
        detalle_partes.append(f"Danos visibles: {'si' if danos else 'no'}")
        detalle_partes.append(f"Caducidad vencida: {'si' if caducidad_vencida else 'no'}")
        if observaciones:
            detalle_partes.append(f"Observaciones: {observaciones}")

        ejecutar(
            """
            INSERT INTO evidencias (devolucion_id, usuario_id, tipo, etapa, comentario)
            VALUES (%s, %s, 'comentario', 'inspeccion', %s)
            """,
            (devolucion_id, usuario_actual()["id"], " | ".join(detalle_partes)),
        )

        cambiar_estado(devolucion_id, "en_inspeccion",
                       f"Inspeccion registrada. Resultado: {resultado}")
        flash(f"Inspeccion registrada. Resultado: {resultado}.", "ok" if apto else "aviso")
        return redirect(url_for("devoluciones.detalle", devolucion_id=devolucion_id))

    return render_template("inspecciones/registrar.html", d=expediente, refrigerado=refrigerado)


@bp.route("/<int:devolucion_id>/disposicion", methods=["GET", "POST"])
@roles_required(ANALISTA)
def disposicion(devolucion_id):
    """Decide el destino final del producto (RF-18, UC-15).

    El trigger trg_validar_destino_inventario de PostgreSQL impide enviar a
    inventario un producto que la inspeccion marco como no apto, de modo que la
    regla se cumple aunque el codigo de aplicacion fallara (RN-06, RN-07).
    """
    expediente = obtener_expediente(devolucion_id)
    if expediente is None:
        abort(404)

    inspeccion = consultar(
        "SELECT * FROM inspecciones_ref WHERE devolucion_id = %s", (devolucion_id,), uno=True)
    if inspeccion is None:
        flash("No se puede decidir el destino sin una inspeccion registrada.", "error")
        return redirect(url_for("devoluciones.detalle", devolucion_id=devolucion_id))

    existente = consultar("SELECT id FROM disposiciones WHERE devolucion_id = %s",
                          (devolucion_id,), uno=True)
    if existente:
        flash("Esta devolucion ya tiene una disposicion registrada.", "aviso")
        return redirect(url_for("devoluciones.detalle", devolucion_id=devolucion_id))

    if request.method == "POST":
        destino = request.form.get("destino")
        justificacion = (request.form.get("justificacion") or "").strip()
        if destino not in dict(DESTINOS):
            abort(400)

        try:
            ejecutar(
                """
                INSERT INTO disposiciones (devolucion_id, analista_id, destino, justificacion)
                VALUES (%s, %s, %s, %s)
                """,
                (devolucion_id, usuario_actual()["id"], destino, justificacion or None),
            )
        except psycopg2.errors.RaiseException as exc:
            # El mensaje del trigger ya explica cual regla se violo.
            get_conn().rollback()
            flash(str(exc).split("CONTEXT:")[0].strip(), "error")
            return render_template("inspecciones/disposicion.html", d=expediente,
                                   inspeccion=inspeccion, destinos=DESTINOS), 409

        cambiar_estado(devolucion_id, "resuelta", f"Destino asignado: {destino}. {justificacion}".strip())
        flash("Disposicion registrada.", "ok")
        return redirect(url_for("devoluciones.detalle", devolucion_id=devolucion_id))

    return render_template("inspecciones/disposicion.html", d=expediente,
                           inspeccion=inspeccion, destinos=DESTINOS)


@bp.get("/inventario")
@roles_required(ENCARGADO_CENTRO, ANALISTA)
def inventario():
    """Inventario de productos recuperados y sus etiquetas (RF-19, HU-17)."""
    articulos = consultar(
        """
        SELECT ir.id, ir.etiqueta_codigo, ir.estado, ir.fecha_ingreso,
               p.nombre AS producto, p.sku, d.folio_devolucion, d.id AS devolucion_id
          FROM inventario_recuperado ir
          JOIN productos p     ON p.id = ir.producto_id
          JOIN disposiciones ds ON ds.id = ir.disposicion_id
          JOIN devoluciones d   ON d.id = ds.devolucion_id
         ORDER BY ir.fecha_ingreso DESC
        """
    )
    por_etiquetar = consultar(
        """
        SELECT ds.id AS disposicion_id, d.id AS devolucion_id, d.folio_devolucion,
               p.id AS producto_id, p.nombre AS producto, p.sku
          FROM disposiciones ds
          JOIN devoluciones d   ON d.id = ds.devolucion_id
          JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
          JOIN lotes l          ON l.id = vd.lote_id
          JOIN productos p      ON p.id = l.producto_id
         WHERE ds.destino = 'inventario'
           AND NOT EXISTS (SELECT 1 FROM inventario_recuperado ir
                            WHERE ir.disposicion_id = ds.id)
         ORDER BY ds.fecha_decision
        """
    )
    return render_template("inspecciones/inventario.html", articulos=articulos,
                           por_etiquetar=por_etiquetar)


@bp.post("/inventario/<int:disposicion_id>/etiquetar")
@roles_required(ENCARGADO_CENTRO)
def etiquetar(disposicion_id):
    """Genera la etiqueta e ingresa el articulo al inventario recuperado (RF-19)."""
    disposicion = consultar(
        """
        SELECT ds.id, ds.destino, d.id AS devolucion_id, d.folio_devolucion, p.id AS producto_id
          FROM disposiciones ds
          JOIN devoluciones d   ON d.id = ds.devolucion_id
          JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
          JOIN lotes l          ON l.id = vd.lote_id
          JOIN productos p      ON p.id = l.producto_id
         WHERE ds.id = %s
        """,
        (disposicion_id,), uno=True,
    )
    if disposicion is None:
        abort(404)
    if disposicion["destino"] != "inventario":
        flash("Solo se etiquetan los productos cuyo destino es el inventario.", "error")
        return redirect(url_for("inspecciones.inventario"))

    etiqueta = f"REC-{disposicion['folio_devolucion'].replace('DEV-', '')}"
    ejecutar(
        """
        INSERT INTO inventario_recuperado (disposicion_id, producto_id, etiqueta_codigo)
        VALUES (%s, %s, %s)
        ON CONFLICT (disposicion_id) DO NOTHING
        """,
        (disposicion_id, disposicion["producto_id"], etiqueta),
    )
    registrar_bitacora("alta_inventario_recuperado", "devoluciones",
                       disposicion["devolucion_id"],
                       f"Articulo ingresado al inventario recuperado con etiqueta {etiqueta}")
    flash(f"Articulo etiquetado como {etiqueta}.", "ok")
    return redirect(url_for("inspecciones.inventario"))
