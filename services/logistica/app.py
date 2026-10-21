"""Microservicio de logistica inversa (RF-12 a RF-15, RN-12)."""
import os
from datetime import date
from flask import Blueprint, Flask, g, request
from shared import docs, respuestas
from shared.infra import cerrar_conexion, consultar, ejecutar, registrar_bitacora, salud_postgres, salud_redis
from shared.respuestas import ErrorApi, leer_cuerpo, responder
from shared.seguridad import COORDINADOR, ENCARGADO_CENTRO, requiere_jwt

NOMBRE = "logistica"
CONTRATOS = os.path.join(os.path.dirname(__file__), "contratos")
api = Blueprint(NOMBRE, __name__, url_prefix="/api/v1/logistica")

def _devolucion(devolucion_id, bloquear=False):
    fila = consultar("SELECT id, folio_devolucion, estado FROM devoluciones WHERE id=%s AND eliminado_en IS NULL" + (" FOR UPDATE" if bloquear else ""), (devolucion_id,), uno=True)
    if not fila:
        raise ErrorApi(404, "no_encontrado", f"No existe la devolucion {devolucion_id}.")
    return fila

def _positivo(datos, campo):
    try: valor = int(datos.get(campo))
    except (TypeError, ValueError): valor = 0
    if valor < 1:
        raise ErrorApi(400, "validacion", "Datos de logistica invalidos.", [{"campo": campo, "problema": "debe ser entero positivo"}])
    return valor

def _fecha_programada(valor):
    """Valida antes de llegar a PostgreSQL para responder 400 y no 500."""
    try:
        fecha = date.fromisoformat(str(valor or "").strip())
    except ValueError:
        raise ErrorApi(400, "validacion", "fecha_programada debe usar AAAA-MM-DD.")
    if fecha < date.today():
        raise ErrorApi(400, "validacion", "fecha_programada no puede estar en el pasado.")
    return fecha.isoformat()

def _booleano_estricto(valor, campo):
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str) and valor.strip().lower() in ("true", "1", "si"):
        return True
    if isinstance(valor, str) and valor.strip().lower() in ("false", "0", "no"):
        return False
    raise ErrorApi(400, "validacion", f"{campo} debe ser booleano.")

@api.post("/recolecciones")
@requiere_jwt(COORDINADOR)
def programar():
    datos = leer_cuerpo(os.path.join(CONTRATOS, "recoleccion.xsd"))
    dev_id = _positivo(datos, "devolucion_id")
    dev = _devolucion(dev_id, True)
    if dev["estado"] != "autorizada":
        raise ErrorApi(409, "estado_no_permite", "Solo se programan devoluciones autorizadas.", {"estado_actual": dev["estado"]})
    fecha = _fecha_programada(datos.get("fecha_programada"))
    lugar = str(datos.get("lugar") or "").strip()
    if not lugar or len(lugar) > 255:
        raise ErrorApi(400, "validacion", "lugar debe contener entre 1 y 255 caracteres.")
    if consultar("SELECT id FROM recolecciones WHERE devolucion_id=%s", (dev_id,), uno=True):
        raise ErrorApi(409, "recoleccion_duplicada", "La devolucion ya tiene recoleccion.")
    nueva = ejecutar("""INSERT INTO recolecciones(devolucion_id,fecha_programada,lugar,coordinador_id,estado)
        VALUES(%s,%s,%s,%s,'programada') RETURNING id,devolucion_id,fecha_programada,lugar,estado""",
        (dev_id, fecha, lugar, g.usuario["id"]), devolver=True)
    ejecutar("UPDATE devoluciones SET estado='en_recoleccion' WHERE id=%s", (dev_id,))
    registrar_bitacora("recoleccion_programada", "devoluciones", dev_id, f"Recoleccion {nueva['id']} programada por API")
    return responder(nueva, 201, headers={"Location": f"/api/v1/logistica/recolecciones/{nueva['id']}"})

@api.get("/recolecciones")
@requiere_jwt(COORDINADOR, ENCARGADO_CENTRO)
def listar():
    estado = (request.args.get("estado") or "").strip()
    permitidos = ("programada", "asignada", "en_transito", "completada", "fallida")
    if estado and estado not in permitidos:
        raise ErrorApi(400, "validacion", "Estado de recoleccion invalido.")
    sql = """SELECT r.*, d.folio_devolucion,
                    concat(ru.origen, ' -> ', ru.destino) AS ruta,
                    t.nombre AS transportista
             FROM recolecciones r JOIN devoluciones d ON d.id=r.devolucion_id
             LEFT JOIN rutas ru ON ru.id=r.ruta_id LEFT JOIN transportistas t ON t.id=r.transportista_id"""
    return responder({"datos": consultar(sql + (" WHERE r.estado=%s" if estado else "") + " ORDER BY r.id DESC", (estado,) if estado else ())})

@api.patch("/recolecciones/<int:recoleccion_id>/asignacion")
@requiere_jwt(COORDINADOR)
def asignar(recoleccion_id):
    datos = leer_cuerpo(os.path.join(CONTRATOS, "asignacion.xsd"))
    ruta_id, transportista_id = _positivo(datos, "ruta_id"), _positivo(datos, "transportista_id")
    fila = consultar("SELECT id,devolucion_id,estado FROM recolecciones WHERE id=%s FOR UPDATE", (recoleccion_id,), uno=True)
    if not fila: raise ErrorApi(404, "no_encontrado", f"No existe la recoleccion {recoleccion_id}.")
    if fila["estado"] not in ("programada", "asignada"):
        raise ErrorApi(409, "estado_no_permite", "La recoleccion ya inicio.")
    if not consultar("SELECT id FROM rutas WHERE id=%s AND activo", (ruta_id,), uno=True) or not consultar("SELECT id FROM transportistas WHERE id=%s AND activo", (transportista_id,), uno=True):
        raise ErrorApi(400, "validacion", "Ruta o transportista inexistente/inactivo.")
    ejecutar("UPDATE recolecciones SET ruta_id=%s,transportista_id=%s,estado='asignada' WHERE id=%s", (ruta_id, transportista_id, recoleccion_id))
    registrar_bitacora("recoleccion_asignada", "devoluciones", fila["devolucion_id"], f"Ruta {ruta_id}, transportista {transportista_id}")
    return responder({"id": recoleccion_id, "estado": "asignada", "ruta_id": ruta_id, "transportista_id": transportista_id})

@api.patch("/recolecciones/<int:recoleccion_id>/estado")
@requiere_jwt(COORDINADOR)
def cambiar_estado(recoleccion_id):
    datos = leer_cuerpo(os.path.join(CONTRATOS, "estado_recoleccion.xsd"))
    nuevo = str(datos.get("estado") or "").strip()
    transiciones = {"asignada": {"en_transito", "fallida"}, "en_transito": {"completada", "fallida"}}
    fila = consultar("SELECT id,devolucion_id,estado FROM recolecciones WHERE id=%s FOR UPDATE", (recoleccion_id,), uno=True)
    if not fila: raise ErrorApi(404, "no_encontrado", f"No existe la recoleccion {recoleccion_id}.")
    if nuevo not in transiciones.get(fila["estado"], set()):
        raise ErrorApi(409, "transicion_invalida", f"No se puede pasar de {fila['estado']} a {nuevo}.")
    ejecutar("UPDATE recolecciones SET estado=%s WHERE id=%s", (nuevo, recoleccion_id))
    registrar_bitacora("estado_recoleccion", "devoluciones", fila["devolucion_id"], f"Estado logistico: {nuevo}")
    return responder({"id": recoleccion_id, "estado": nuevo})

@api.post("/recepciones")
@requiere_jwt(ENCARGADO_CENTRO)
def recibir():
    datos = leer_cuerpo(os.path.join(CONTRATOS, "recepcion.xsd"))
    dev_id = _positivo(datos, "devolucion_id")
    dev = _devolucion(dev_id, True)
    rec = consultar("SELECT estado FROM recolecciones WHERE devolucion_id=%s", (dev_id,), uno=True)
    if not rec or rec["estado"] != "completada":
        raise ErrorApi(409, "estado_no_permite", "La recoleccion debe estar completada antes de recibir.")
    if consultar("SELECT id FROM recepciones WHERE devolucion_id=%s", (dev_id,), uno=True):
        raise ErrorApi(409, "recepcion_duplicada", "La devolucion ya fue recibida.")
    coincide = _booleano_estricto(datos.get("coincide_expediente", True), "coincide_expediente")
    nueva = ejecutar("""INSERT INTO recepciones(devolucion_id,encargado_id,coincide_expediente)
        VALUES(%s,%s,%s) RETURNING id,devolucion_id,fecha_recepcion,coincide_expediente""", (dev_id, g.usuario["id"], coincide), devolver=True)
    ejecutar("UPDATE devoluciones SET estado='recibida' WHERE id=%s", (dev_id,))
    registrar_bitacora("recepcion_confirmada", "devoluciones", dev_id, f"Coincide expediente: {coincide}")
    return responder(nueva, 201)

def create_app():
    app = Flask(__name__); app.json.sort_keys = False
    respuestas.registrar(app, NOMBRE); app.teardown_appcontext(cerrar_conexion); app.register_blueprint(api)
    docs.registrar(app, os.path.join(os.path.dirname(__file__), "openapi.yaml"))
    @app.get("/health")
    def health():
        deps={"postgresql": salud_postgres(), "redis": salud_redis()}; ok=all(x["ok"] for x in deps.values())
        return responder({"servicio":NOMBRE,"version":"v1","estado":"ok" if ok else "degradado","dependencias":deps},200 if ok else 503)
    return app
