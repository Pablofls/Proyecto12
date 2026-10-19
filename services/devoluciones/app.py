"""Microservicio de devoluciones (segundo parcial).

Responsabilidad: el inicio del proceso de negocio. El cliente registra la
devolucion sobre una linea de venta y el analista la autoriza, la rechaza o
pide informacion. Los estados posteriores (recoleccion, inspeccion,
reembolso) los mueven sus propios servicios.

Mismas reglas que el monolito (app/blueprints/devoluciones.py), ahora como API
REST con JWT, JSON/XML, eventos en MongoDB y notificaciones al cliente.

Trazabilidad: RF-06, RF-07, RF-08, RF-10, RF-11, RF-29, RF-30, RN-01, RN-02,
RN-12, RNF-09, RNF-30, HU-06 a HU-11, UC-06 a UC-09.

Endpoints (JSON o XML):
  POST   /api/v1/devoluciones                    Registrar (Cliente, Analista)
  GET    /api/v1/devoluciones                    Listar con filtros y paginacion
  GET    /api/v1/devoluciones/<id>               Expediente, historial y eventos
  PUT    /api/v1/devoluciones/<id>               Corregir la solicitud (Cliente)
  PATCH  /api/v1/devoluciones/<id>/resolucion    Autorizar/rechazar/pedir info (Analista)
  DELETE /api/v1/devoluciones/<id>               Cancelar, eliminacion logica (Cliente)
  GET    /health, /docs, /contratos/<nombre>.xsd
"""
import logging
import os

from flask import Blueprint, Flask, g, request

from shared import docs, mongo, respuestas
from shared.infra import (cerrar_conexion, consultar, ejecutar, limitar,
                          registrar_bitacora, salud_postgres, salud_redis)
from shared.paginacion import leer_paginacion, paginar
from shared.respuestas import ErrorApi, leer_cuerpo, responder
from shared.seguridad import ANALISTA, CLIENTE, requiere_jwt

import reglas

NOMBRE = "devoluciones"
CONTRATOS = os.path.join(os.path.dirname(__file__), "contratos")
CREAR_POR_MINUTO = int(os.environ.get("DEVOLUCIONES_MAX_POR_MINUTO", "20"))

log = logging.getLogger("servicio")
api = Blueprint("devoluciones", __name__, url_prefix="/api/v1/devoluciones")


# --------------------------------------------------------------------------- #
# Consultas
# --------------------------------------------------------------------------- #
_EXPEDIENTE = """
    SELECT d.id, d.folio_devolucion, d.estado, d.descripcion_problema,
           d.cantidad_devuelta, d.fecha_solicitud, d.fecha_autorizacion,
           d.fecha_cierre, d.motivo_id, m.nombre AS motivo,
           d.venta_detalle_id, vd.cantidad AS cantidad_comprada,
           vd.precio_unitario,
           (vd.precio_unitario * d.cantidad_devuelta) AS valor_devuelto,
           v.folio_venta, v.cliente_id, cli.nombre AS cliente,
           p.nombre AS producto, p.sku, p.clasificacion_temperatura,
           l.numero_lote, d.analista_id, ana.nombre AS analista
      FROM devoluciones d
      JOIN motivos m        ON m.id = d.motivo_id
      JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
      JOIN ventas v         ON v.id = vd.venta_id
      JOIN usuarios cli     ON cli.id = v.cliente_id
      JOIN lotes l          ON l.id = vd.lote_id
      JOIN productos p      ON p.id = l.producto_id
      LEFT JOIN usuarios ana ON ana.id = d.analista_id
     WHERE d.id = %s AND d.eliminado_en IS NULL
"""


def _expediente(devolucion_id, bloquear=False):
    """Expediente vigente o 404. Con bloquear=True toma la fila de la
    devolucion hasta el commit: dos analistas no pueden resolverla a la vez."""
    sql = _EXPEDIENTE + (" FOR UPDATE OF d" if bloquear else "")
    exp = consultar(sql, (devolucion_id,), uno=True)
    if exp is None:
        raise ErrorApi(404, "no_encontrado",
                       f"No existe la devolucion {devolucion_id}.")
    return exp


def _exigir_visible(exp):
    """Autorizacion por recurso (5.3): el cliente solo ve sus devoluciones,
    aunque conozca el id de otra. El personal interno ve todas."""
    if g.usuario["rol"] == CLIENTE and exp["cliente_id"] != g.usuario["id"]:
        registrar_bitacora("acceso_denegado", "devoluciones", exp["id"],
                           "Intento de acceder a una devolucion de otro cliente (API)")
        raise ErrorApi(403, "sin_permiso",
                       "La devolucion no pertenece a tu cuenta.")


def _linea_de_venta(venta_detalle_id, excluir_devolucion=None):
    """Linea de venta bloqueada y cantidad que aun se puede devolver (RN-01).

    El bloqueo evita que dos solicitudes simultaneas sobre la misma linea
    superen juntas la cantidad comprada.
    """
    linea = consultar(
        """
        SELECT vd.id, vd.cantidad, v.cliente_id, v.folio_venta
          FROM venta_detalle vd
          JOIN ventas v ON v.id = vd.venta_id
         WHERE vd.id = %s AND v.eliminado_en IS NULL
           FOR UPDATE OF vd
        """,
        (venta_detalle_id,), uno=True,
    )
    if linea is None:
        raise ErrorApi(404, "no_encontrado",
                       f"No existe la linea de venta {venta_detalle_id}.")
    devuelto = consultar(
        """
        SELECT COALESCE(SUM(cantidad_devuelta), 0) AS n
          FROM devoluciones
         WHERE venta_detalle_id = %s AND eliminado_en IS NULL
           AND estado <> 'rechazada' AND id <> %s
        """,
        (venta_detalle_id, excluir_devolucion or 0), uno=True,
    )["n"]
    linea["disponible"] = linea["cantidad"] - devuelto
    return linea


def _exigir_cantidad(linea, cantidad):
    if linea["disponible"] <= 0:
        raise ErrorApi(409, "sin_disponible",
                       "Todos los articulos de esta linea ya tienen una "
                       "devolucion registrada.")
    if cantidad > linea["disponible"]:
        raise ErrorApi(409, "cantidad_excedida",
                       f"Solo se pueden devolver {linea['disponible']} "
                       "articulo(s) de esta linea.",
                       {"disponible": linea["disponible"],
                        "solicitada": cantidad})


def _exigir_motivo(motivo_id):
    if not consultar("SELECT id FROM motivos WHERE id = %s AND activo",
                     (motivo_id,), uno=True):
        raise ErrorApi(400, "validacion", "El motivo no existe o esta inactivo.",
                       [{"campo": "motivo_id", "problema": "no existe o esta inactivo"}])


def _notificar(usuario_id, devolucion_id, tipo, mensaje):
    """Notificacion interna al cliente (RF-29); la web la muestra en su panel."""
    ejecutar(
        """
        INSERT INTO notificaciones (usuario_id, devolucion_id, tipo, mensaje)
        VALUES (%s, %s, %s, %s)
        """,
        (usuario_id, devolucion_id, tipo, mensaje[:500]),
    )


def _evento(tipo, exp, **extra):
    mongo.registrar_evento(NOMBRE, tipo, {
        "devolucion_id": exp["id"], "folio": exp["folio_devolucion"], **extra})


_indice_eventos = False


def _eventos_de(devolucion_id):
    """Eventos de la devolucion en MongoDB, del mas reciente al mas antiguo.

    El indice se crea la primera vez (create_index es idempotente): init.js
    solo indexa correlation_id y fecha, y aqui se filtra por devolucion.
    Si MongoDB no responde, el expediente se entrega igual sin eventos.
    """
    global _indice_eventos
    try:
        coleccion = mongo.get_mongo().eventos
        if not _indice_eventos:
            coleccion.create_index([("datos.devolucion_id", 1), ("fecha", -1)],
                                   name="idx_devolucion_fecha")
            _indice_eventos = True
        cursor = (coleccion.find({"datos.devolucion_id": devolucion_id},
                                 {"_id": 0})
                  .sort("fecha", -1).limit(50))
        return mongo.a_json(list(cursor))
    except Exception:
        log.exception("No se pudieron leer los eventos de %s", devolucion_id)
        return None


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #
@api.post("")
@requiere_jwt(CLIENTE, ANALISTA)
def registrar():
    """RF-07, RN-01: toda devolucion nace de una linea de venta."""
    limitar("crear_devolucion", CREAR_POR_MINUTO, 60,
            sujeto=f"usuario{g.usuario['id']}")
    datos = leer_cuerpo(xsd=os.path.join(CONTRATOS, "devolucion_nueva.xsd"))
    valores, errores = reglas.validar_nueva(datos)
    if errores:
        raise ErrorApi(400, "validacion", "Datos de la devolucion incompletos.",
                       errores)

    linea = _linea_de_venta(valores["venta_detalle_id"])
    if g.usuario["rol"] == CLIENTE and linea["cliente_id"] != g.usuario["id"]:
        registrar_bitacora("acceso_denegado", "ventas", linea["id"],
                           "Intento de devolver una compra de otro cliente (API)")
        raise ErrorApi(403, "sin_permiso", "La compra no pertenece a tu cuenta.")
    _exigir_motivo(valores["motivo_id"])
    _exigir_cantidad(linea, valores["cantidad_devuelta"])

    nueva = ejecutar(
        """
        INSERT INTO devoluciones (venta_detalle_id, motivo_id, descripcion_problema,
                                  cantidad_devuelta, estado)
        VALUES (%s, %s, %s, %s, 'solicitada')
        RETURNING id, folio_devolucion, estado, fecha_solicitud
        """,
        (valores["venta_detalle_id"], valores["motivo_id"],
         valores["descripcion_problema"], valores["cantidad_devuelta"]),
        devolver=True,
    )
    registrar_bitacora("alta_devolucion", "devoluciones", nueva["id"],
                       f"Se registro la devolucion {nueva['folio_devolucion']} "
                       f"sobre la venta {linea['folio_venta']} (API)")
    _evento("devolucion_registrada", nueva,
            venta_detalle_id=valores["venta_detalle_id"],
            cantidad=valores["cantidad_devuelta"])
    return responder({**nueva, **valores}, 201, headers={
        "Location": f"/api/v1/devoluciones/{nueva['id']}"})


@api.get("")
@requiere_jwt()
def listar():
    """RF-11: busqueda por estado, folio o producto, con paginacion."""
    estado, errores = reglas.validar_estado(request.args.get("estado"))
    if errores:
        raise ErrorApi(400, "validacion", "Filtro invalido.", errores)
    busqueda = (request.args.get("q") or "").strip()[:100]
    pag = leer_paginacion()

    condiciones, parametros = ["d.eliminado_en IS NULL"], []
    if g.usuario["rol"] == CLIENTE:
        condiciones.append("v.cliente_id = %s")
        parametros.append(g.usuario["id"])
    if estado:
        condiciones.append("d.estado = %s")
        parametros.append(estado)
    if busqueda:
        condiciones.append("(d.folio_devolucion ILIKE %s OR p.nombre ILIKE %s)")
        parametros += [f"%{busqueda}%", f"%{busqueda}%"]
    # Solo se concatenan condiciones fijas; los valores van ligados (RNF-11).
    desde = f"""
          FROM devoluciones d
          JOIN motivos m        ON m.id = d.motivo_id
          JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
          JOIN ventas v         ON v.id = vd.venta_id
          JOIN usuarios cli     ON cli.id = v.cliente_id
          JOIN lotes l          ON l.id = vd.lote_id
          JOIN productos p      ON p.id = l.producto_id
         WHERE {' AND '.join(condiciones)}
    """
    total = consultar("SELECT count(*) AS n " + desde, tuple(parametros), uno=True)["n"]
    filas = consultar(
        """
        SELECT d.id, d.folio_devolucion, d.estado, d.fecha_solicitud,
               d.cantidad_devuelta, m.nombre AS motivo, p.nombre AS producto,
               p.clasificacion_temperatura, l.numero_lote,
               cli.nombre AS cliente, v.folio_venta
        """ + desde + " ORDER BY d.fecha_solicitud DESC, d.id DESC LIMIT %s OFFSET %s",
        tuple(parametros) + (pag.limite, pag.desplazamiento),
    )
    return responder(paginar(filas, total, pag))


@api.get("/<int:devolucion_id>")
@requiere_jwt()
def detalle(devolucion_id):
    """RF-11: expediente, historial (bitacora, RF-30) y eventos (MongoDB)."""
    exp = _expediente(devolucion_id)
    _exigir_visible(exp)
    historial = consultar(
        """
        SELECT b.fecha, b.accion, b.detalle, u.nombre AS usuario
          FROM bitacora b LEFT JOIN usuarios u ON u.id = b.usuario_id
         WHERE b.entidad = 'devoluciones' AND b.entidad_id = %s
         ORDER BY b.fecha DESC
         LIMIT 50
        """,
        (devolucion_id,),
    )
    return responder({**exp, "historial": historial,
                      "eventos": _eventos_de(devolucion_id)})


@api.put("/<int:devolucion_id>")
@requiere_jwt(CLIENTE)
def corregir(devolucion_id):
    """RF-10: el cliente corrige su solicitud cuando el analista le pidio
    informacion. Solo mientras nadie la haya resuelto."""
    datos = leer_cuerpo(xsd=os.path.join(CONTRATOS, "devolucion_edicion.xsd"))
    valores, errores = reglas.validar_edicion(datos)
    if errores:
        raise ErrorApi(400, "validacion", "Datos de la devolucion incompletos.",
                       errores)
    exp = _expediente(devolucion_id, bloquear=True)
    _exigir_visible(exp)
    if exp["estado"] not in reglas.ESTADOS_REVISABLES:
        raise ErrorApi(409, "estado_no_permite",
                       "La devolucion ya fue resuelta y no se puede modificar.",
                       {"estado_actual": exp["estado"]})
    _exigir_motivo(valores["motivo_id"])
    linea = _linea_de_venta(exp["venta_detalle_id"], excluir_devolucion=devolucion_id)
    _exigir_cantidad(linea, valores["cantidad_devuelta"])

    ejecutar(
        """
        UPDATE devoluciones
           SET motivo_id = %s, descripcion_problema = %s, cantidad_devuelta = %s
         WHERE id = %s
        """,
        (valores["motivo_id"], valores["descripcion_problema"],
         valores["cantidad_devuelta"], devolucion_id),
    )
    registrar_bitacora("actualizacion_solicitud", "devoluciones", devolucion_id,
                       "El cliente corrigio la solicitud (API)")
    _evento("devolucion_corregida", exp, **valores)
    return responder(_expediente(devolucion_id))


@api.patch("/<int:devolucion_id>/resolucion")
@requiere_jwt(ANALISTA)
def resolver(devolucion_id):
    """RF-10, UC-09: autorizar, rechazar o solicitar informacion adicional."""
    datos = leer_cuerpo(xsd=os.path.join(CONTRATOS, "resolucion.xsd"))
    valores, errores = reglas.validar_resolucion(datos)
    if errores:
        raise ErrorApi(400, "validacion", "Resolucion incompleta.", errores)
    exp = _expediente(devolucion_id, bloquear=True)
    if exp["estado"] not in reglas.ESTADOS_REVISABLES:
        raise ErrorApi(409, "estado_no_permite",
                       "La devolucion ya no esta en revision.",
                       {"estado_actual": exp["estado"]})

    decision, nota = valores["decision"], valores["justificacion"]
    analista = g.usuario["id"]
    folio = exp["folio_devolucion"]
    if decision == "autorizar":
        ejecutar(
            """
            UPDATE devoluciones
               SET estado = 'autorizada', analista_id = %s,
                   fecha_autorizacion = CURRENT_TIMESTAMP
             WHERE id = %s
            """,
            (analista, devolucion_id),
        )
        accion, mensaje = "autorizacion", (
            f"Tu devolucion {folio} fue autorizada. Pronto programaremos la recoleccion.")
    elif decision == "rechazar":
        # Estado terminal: fecha_cierre alimenta el KPI de resolucion (RF-26).
        ejecutar(
            """
            UPDATE devoluciones
               SET estado = 'rechazada', analista_id = %s,
                   fecha_cierre = CURRENT_TIMESTAMP
             WHERE id = %s
            """,
            (analista, devolucion_id),
        )
        accion, mensaje = "rechazo", f"Tu devolucion {folio} fue rechazada: {nota}"
    else:
        ejecutar(
            "UPDATE devoluciones SET estado = 'en_revision', analista_id = %s WHERE id = %s",
            (analista, devolucion_id),
        )
        accion, mensaje = "solicitud_informacion", (
            f"Necesitamos mas informacion sobre tu devolucion {folio}. {nota}".strip())

    registrar_bitacora(accion, "devoluciones", devolucion_id,
                       f"Decision '{decision}' por API. {nota}".strip())
    _notificar(exp["cliente_id"], devolucion_id, accion, mensaje)
    _evento(f"devolucion_{accion}", exp, decision=decision, analista_id=analista)
    actualizado = _expediente(devolucion_id)
    return responder({"id": devolucion_id, "folio_devolucion": folio,
                      "estado": actualizado["estado"], "decision": decision,
                      "analista": actualizado["analista"],
                      "notificacion_cliente": mensaje})


@api.delete("/<int:devolucion_id>")
@requiere_jwt(CLIENTE)
def cancelar(devolucion_id):
    """RNF-30: la cancelacion es eliminacion logica; el expediente se conserva
    para auditoria. Solo antes de que un analista la revise."""
    exp = _expediente(devolucion_id, bloquear=True)
    _exigir_visible(exp)
    if exp["estado"] != "solicitada" or exp["analista_id"] is not None:
        raise ErrorApi(409, "estado_no_permite",
                       "Solo se puede cancelar una devolucion que nadie ha revisado.",
                       {"estado_actual": exp["estado"]})
    ejecutar("UPDATE devoluciones SET eliminado_en = CURRENT_TIMESTAMP WHERE id = %s",
             (devolucion_id,))
    registrar_bitacora("cancelacion", "devoluciones", devolucion_id,
                       f"El cliente cancelo la devolucion {exp['folio_devolucion']} (API)")
    _evento("devolucion_cancelada", exp)
    return responder({"id": devolucion_id, "folio_devolucion": exp["folio_devolucion"],
                      "mensaje": "Devolucion cancelada."})


# --------------------------------------------------------------------------- #
# Aplicacion
# --------------------------------------------------------------------------- #
def create_app():
    app = Flask(__name__)
    app.json.sort_keys = False
    respuestas.registrar(app, NOMBRE)
    app.teardown_appcontext(cerrar_conexion)
    app.register_blueprint(api)
    docs.registrar(app, os.path.join(os.path.dirname(__file__), "openapi.yaml"))

    @app.get("/health")
    def health():
        """RNF-22: estado del servicio y de sus tres dependencias."""
        deps = {"postgresql": salud_postgres(), "redis": salud_redis(),
                "mongodb": mongo.salud_mongo()}
        ok = all(d["ok"] for d in deps.values())
        return responder({"servicio": NOMBRE, "version": "v1",
                          "estado": "ok" if ok else "degradado",
                          "dependencias": deps}, 200 if ok else 503)

    return app
