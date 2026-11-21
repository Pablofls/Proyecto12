"""Decision autorizada de disposicion e inventario recuperable (RF-18, RF-19)."""
import os

from flask import Blueprint, Flask, g

from shared import docs, respuestas
from shared.infra import (cerrar_conexion, consultar, ejecutar,
                          registrar_bitacora, salud_postgres, salud_redis)
from shared.respuestas import ErrorApi, leer_cuerpo, responder
from shared.seguridad import (ANALISTA, ENCARGADO_CENTRO, SUPERVISOR,
                              exigir_autorizacion_operacion, requiere_jwt)
from reglas import estado_inicial_inventario, validar_decision

NOMBRE = "disposicion-inventario"
CONTRATOS = os.path.join(os.path.dirname(__file__), "contratos")
api = Blueprint("disposicion_inventario", __name__,
                url_prefix="/api/v1/disposicion-inventario")


def _expediente(devolucion_id, bloquear=False):
    sql = """SELECT d.id,d.folio_devolucion,d.estado,p.id AS producto_id,
                    p.nombre AS producto,p.sku,l.numero_lote,
                    i.id AS inspeccion_id,i.apto_para_inventario,
                    i.estado_dictamen,i.recomendacion
               FROM devoluciones d
               JOIN venta_detalle vd ON vd.id=d.venta_detalle_id
               JOIN lotes l ON l.id=vd.lote_id
               JOIN productos p ON p.id=l.producto_id
          LEFT JOIN inspecciones_ref i ON i.devolucion_id=d.id
              WHERE d.id=%s AND d.eliminado_en IS NULL"""
    if bloquear:
        sql += " FOR UPDATE OF d"
    fila = consultar(sql, (devolucion_id,), uno=True)
    if not fila:
        raise ErrorApi(404, "no_encontrado",
                       f"No existe la devolucion {devolucion_id}.")
    return fila


@api.get("/pendientes")
@requiere_jwt(ANALISTA, SUPERVISOR)
def pendientes():
    datos = consultar("""SELECT d.id,d.folio_devolucion,p.nombre AS producto,
             l.numero_lote,i.apto_para_inventario,i.estado_dictamen,i.recomendacion
        FROM inspecciones_ref i JOIN devoluciones d ON d.id=i.devolucion_id
        JOIN venta_detalle vd ON vd.id=d.venta_detalle_id
        JOIN lotes l ON l.id=vd.lote_id JOIN productos p ON p.id=l.producto_id
       WHERE d.eliminado_en IS NULL
         AND NOT EXISTS (SELECT 1 FROM disposiciones ds WHERE ds.devolucion_id=d.id)
       ORDER BY i.fecha_inspeccion""")
    return responder({"datos": datos})


@api.post("/disposiciones")
@requiere_jwt(ANALISTA, SUPERVISOR)
def decidir():
    datos = leer_cuerpo(os.path.join(CONTRATOS, "disposicion.xsd"))
    try:
        devolucion_id = int(datos.get("devolucion_id"))
    except (TypeError, ValueError):
        raise ErrorApi(400, "validacion", "devolucion_id debe ser entero positivo.")
    if devolucion_id < 1:
        raise ErrorApi(400, "validacion", "devolucion_id debe ser entero positivo.")
    destino = str(datos.get("destino") or "").strip()
    justificacion = str(datos.get("justificacion") or "").strip()
    if len(justificacion) < 10:
        raise ErrorApi(400, "validacion", "La justificacion debe tener al menos 10 caracteres.")

    expediente = _expediente(devolucion_id, bloquear=True)
    if not expediente["inspeccion_id"]:
        raise ErrorApi(409, "sin_inspeccion", "No existe un dictamen tecnico.")
    problema = validar_decision(destino, expediente)
    if problema:
        raise ErrorApi(409, "decision_no_permitida", problema)
    if consultar("SELECT id FROM disposiciones WHERE devolucion_id=%s",
                 (devolucion_id,), uno=True):
        raise ErrorApi(409, "disposicion_duplicada", "Ya existe una disposicion.")

    autorizacion = exigir_autorizacion_operacion("aprobar_disposicion", devolucion_id)
    destino_db = "inventario" if destino == "reintegrar" else destino
    nueva = ejecutar("""INSERT INTO disposiciones
        (devolucion_id,analista_id,destino,justificacion,estado,autorizacion_jti)
        VALUES(%s,%s,%s,%s,'autorizada',%s)
        RETURNING id,devolucion_id,destino,justificacion,estado,fecha_decision""",
        (devolucion_id, g.usuario["id"], destino_db, justificacion,
         autorizacion["jti"]), devolver=True)
    ejecutar("UPDATE devoluciones SET estado='resuelta' WHERE id=%s",
             (devolucion_id,))
    registrar_bitacora("disposicion_autorizada", "devoluciones", devolucion_id,
                       f"Destino: {destino}; autorizacion de un solo uso consumida")
    return responder(nueva, 201, headers={"Location":
        f"/api/v1/disposicion-inventario/disposiciones/{nueva['id']}"})


@api.get("/disposiciones/<int:devolucion_id>")
@requiere_jwt(ANALISTA, SUPERVISOR, ENCARGADO_CENTRO)
def consultar_disposicion(devolucion_id):
    fila = consultar("""SELECT ds.id,ds.devolucion_id,ds.destino,ds.justificacion,
        ds.estado,ds.fecha_decision,u.nombre AS autorizado_por
        FROM disposiciones ds JOIN usuarios u ON u.id=ds.analista_id
        WHERE ds.devolucion_id=%s""", (devolucion_id,), uno=True)
    if not fila:
        raise ErrorApi(404, "no_encontrado", "No existe disposicion.")
    return responder(fila)


@api.post("/inventario/<int:disposicion_id>/cuarentena")
@requiere_jwt(ENCARGADO_CENTRO, SUPERVISOR)
def ingresar_cuarentena(disposicion_id):
    datos = leer_cuerpo(os.path.join(CONTRATOS, "cuarentena.xsd"))
    ubicacion = str(datos.get("ubicacion") or "").strip()
    if len(ubicacion) < 2:
        raise ErrorApi(400, "validacion", "La ubicacion es obligatoria.")
    fila = consultar("""SELECT ds.id,ds.destino,ds.estado,d.id AS devolucion_id,
        d.folio_devolucion,p.id AS producto_id FROM disposiciones ds
        JOIN devoluciones d ON d.id=ds.devolucion_id
        JOIN venta_detalle vd ON vd.id=d.venta_detalle_id
        JOIN lotes l ON l.id=vd.lote_id JOIN productos p ON p.id=l.producto_id
        WHERE ds.id=%s FOR UPDATE OF ds""", (disposicion_id,), uno=True)
    if not fila:
        raise ErrorApi(404, "no_encontrado", "No existe la disposicion.")
    if fila["destino"] not in ("inventario", "reintegrar") or fila["estado"] != "autorizada":
        raise ErrorApi(409, "destino_no_reintegrable",
                       "La disposicion no autoriza el reintegro.")
    etiqueta = f"REC-{fila['folio_devolucion'].replace('DEV-', '')}"
    nueva = ejecutar("""INSERT INTO inventario_recuperado
        (disposicion_id,producto_id,etiqueta_codigo,estado,ubicacion,motivo_bloqueo)
        VALUES(%s,%s,%s,%s,%s,'Pendiente de reincorporacion autorizada')
        ON CONFLICT(disposicion_id) DO UPDATE SET ubicacion=EXCLUDED.ubicacion
        RETURNING *""", (disposicion_id, fila["producto_id"], etiqueta,
                           estado_inicial_inventario(), ubicacion), devolver=True)
    registrar_bitacora("inventario_en_cuarentena", "devoluciones",
                       fila["devolucion_id"], f"{etiqueta}; ubicacion {ubicacion}")
    return responder(nueva, 201)


@api.post("/inventario/<int:inventario_id>/reincorporar")
@requiere_jwt(ENCARGADO_CENTRO, SUPERVISOR)
def reincorporar(inventario_id):
    articulo = consultar("""SELECT ir.*,ds.devolucion_id FROM inventario_recuperado ir
        JOIN disposiciones ds ON ds.id=ir.disposicion_id WHERE ir.id=%s FOR UPDATE OF ir""",
        (inventario_id,), uno=True)
    if not articulo:
        raise ErrorApi(404, "no_encontrado", "No existe el articulo recuperado.")
    if articulo["estado"] not in ("cuarentena", "bloqueado"):
        raise ErrorApi(409, "estado_no_permite", "El articulo no esta en cuarentena.")
    exigir_autorizacion_operacion("reincorporar_inventario", inventario_id)
    actualizado = ejecutar("""UPDATE inventario_recuperado SET estado='disponible',
        motivo_bloqueo=NULL,reincorporado_por=%s,fecha_reincorporacion=CURRENT_TIMESTAMP
        WHERE id=%s RETURNING *""", (g.usuario["id"], inventario_id), devolver=True)
    ejecutar("UPDATE disposiciones SET estado='ejecutada' WHERE id=%s",
             (articulo["disposicion_id"],))
    registrar_bitacora("inventario_reincorporado", "devoluciones",
                       articulo["devolucion_id"], f"Articulo {inventario_id}")
    return responder(actualizado)


@api.get("/inventario")
@requiere_jwt(ENCARGADO_CENTRO, ANALISTA, SUPERVISOR)
def inventario():
    return responder({"datos": consultar("""SELECT ir.id,ir.etiqueta_codigo,
        ir.estado,ir.ubicacion,ir.motivo_bloqueo,ir.fecha_ingreso,
        p.nombre AS producto,p.sku,d.id AS devolucion_id,d.folio_devolucion
        FROM inventario_recuperado ir JOIN productos p ON p.id=ir.producto_id
        JOIN disposiciones ds ON ds.id=ir.disposicion_id
        JOIN devoluciones d ON d.id=ds.devolucion_id ORDER BY ir.fecha_ingreso DESC""")})


@api.get("/inventario/pendientes")
@requiere_jwt(ENCARGADO_CENTRO, ANALISTA, SUPERVISOR)
def inventario_pendiente():
    datos = consultar("""SELECT ds.id AS disposicion_id,d.id AS devolucion_id,
        d.folio_devolucion,p.nombre AS producto,p.sku
        FROM disposiciones ds JOIN devoluciones d ON d.id=ds.devolucion_id
        JOIN venta_detalle vd ON vd.id=d.venta_detalle_id
        JOIN lotes l ON l.id=vd.lote_id JOIN productos p ON p.id=l.producto_id
        WHERE ds.destino IN ('inventario','reintegrar') AND ds.estado='autorizada'
        AND NOT EXISTS (SELECT 1 FROM inventario_recuperado ir
                        WHERE ir.disposicion_id=ds.id)
        ORDER BY ds.fecha_decision""")
    return responder({"datos": datos})


def create_app():
    app = Flask(__name__)
    app.json.sort_keys = False
    respuestas.registrar(app, NOMBRE)
    app.teardown_appcontext(cerrar_conexion)
    app.register_blueprint(api)
    docs.registrar(app, os.path.join(os.path.dirname(__file__), "openapi.yaml"))

    @app.get("/health")
    def health():
        deps = {"postgresql": salud_postgres(), "redis": salud_redis()}
        ok = all(x["ok"] for x in deps.values())
        return responder({"servicio": NOMBRE, "version": "v1",
                          "estado": "ok" if ok else "degradado",
                          "dependencias": deps}, 200 if ok else 503)
    return app
