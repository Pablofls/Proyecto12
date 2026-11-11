"""Microservicio de sincronizacion offline (dominio 20 del tercer parcial).

Las apps Android y de escritorio guardan operaciones mientras no hay red y las
envian aqui cuando vuelve la conexion. Reglas:

- Idempotencia: cada operacion trae un id_operacion (UUID del dispositivo). Si
  llega dos veces (reintento, respuesta perdida, doble toque) se devuelve el
  resultado guardado y NO se vuelve a aplicar. La fila de operaciones_offline y
  el efecto se guardan en la misma transaccion.
- Conflictos: el dispositivo manda el estado que vio (estado_esperado). Si el
  servidor cambio mientras estaba sin red, la operacion queda en "conflicto" con
  el estado del servidor y no se aplica.
- Confirmacion: una recoleccion o recepcion solo esta confirmada cuando la
  operacion vuelve con estado "aceptada". La transaccion se confirma ANTES de
  responder.
- Operaciones de dinero, autorizaciones y disposiciones nunca se aceptan desde
  la cola offline (reglas.SOLO_EN_LINEA).
- Evidencias: la foto viaja en base64 con su SHA-256; si no coincide, se
  rechaza (llego incompleta o alterada).

Trazabilidad: RF-09, RF-12 a RF-15, RN-12, RNF-09, RNF-11, RNF-16, RNF-23.
"""
import base64
import binascii
import hashlib
import json
import logging
import os
import re
import uuid
from collections import Counter
from datetime import date, datetime, timezone
from pathlib import Path

from flask import Blueprint, Flask, g, request
from werkzeug.utils import secure_filename

import reglas
from shared import docs, mongo, respuestas
from shared.infra import (cerrar_conexion, confirmar, consultar, ejecutar, limitar,
                          registrar_bitacora, salud_postgres, salud_redis)
from shared.paginacion import leer_paginacion, paginar
from shared.respuestas import ErrorApi, leer_cuerpo, responder
from shared.seguridad import (ADMINISTRADOR, SUPERVISOR, condicion_tienda,
                              exigir_tienda, requiere_jwt)

NOMBRE = "sincronizacion"
CONTRATOS = os.path.join(os.path.dirname(__file__), "contratos")
api = Blueprint(NOMBRE, __name__, url_prefix="/api/v1/sincronizacion")
log = logging.getLogger("servicio")

ROLES = reglas.roles_que_sincronizan()
VEN_TODO = (SUPERVISOR, ADMINISTRADOR)

# Mismo volumen privado y mismo formato de objeto que el servicio de evidencias.
DIR = Path(os.environ.get("EVIDENCIAS_DIR", "/srv/evidencias_privadas"))
BUCKET = "orvia-evidencias-local"
EXTENSION = {"image/jpeg": ".jpg", "image/png": ".png", "application/pdf": ".pdf"}
DISPOSITIVO = re.compile(r"^[A-Za-z0-9_.:-]{1,64}$")
ESTADOS = ("aceptada", "conflicto", "rechazada")


# --------------------------------------------------------------------------- #
# Utilidades
# --------------------------------------------------------------------------- #
def _iso(valor):
    if isinstance(valor, (datetime, date)):
        return valor.isoformat()
    raise TypeError(type(valor).__name__)


def _plano(valor):
    """Lo que se guarda en JSONB y lo que se responde es exactamente lo mismo,
    asi el primer envio y un reintento reciben la misma respuesta."""
    return json.loads(json.dumps(valor, default=_iso))


def _entero(datos, campo):
    valor = datos.get(campo)
    try:
        if isinstance(valor, bool):
            raise ValueError
        numero = int(valor)
    except (TypeError, ValueError):
        numero = 0
    if numero < 1:
        raise ErrorApi(400, "validacion", f"{campo} debe ser entero positivo.")
    return numero


def _booleano(valor, campo):
    if isinstance(valor, bool):
        return valor
    if isinstance(valor, str) and valor.strip().lower() in ("true", "1", "si"):
        return True
    if isinstance(valor, str) and valor.strip().lower() in ("false", "0", "no"):
        return False
    raise ErrorApi(400, "validacion", f"{campo} debe ser booleano.")


def _expediente(devolucion_id, bloquear=False):
    """Devolucion visible para el usuario, con control por sucursal."""
    fila = consultar("""
        SELECT d.id, d.estado, v.tienda_id
          FROM devoluciones d
          JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
          JOIN ventas v ON v.id = vd.venta_id
         WHERE d.id = %s AND d.eliminado_en IS NULL""" + (" FOR UPDATE OF d" if bloquear else ""),
        (devolucion_id,), uno=True)
    if not fila:
        raise ErrorApi(404, "no_encontrado", f"No existe la devolucion {devolucion_id}.")
    exigir_tienda(fila["tienda_id"])
    return fila


def _tipo_real(datos):
    if datos.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if datos.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if datos.startswith(b"%PDF-"):
        return "application/pdf"
    return None


def _guardar_base64(archivo):
    """Foto o PDF capturado sin conexion. Se comprueba el SHA-256 que calculo el
    dispositivo: si no coincide, el archivo llego incompleto o alterado."""
    if not isinstance(archivo, dict):
        raise ErrorApi(400, "validacion", "archivo debe tener nombre, contenido_base64 y sha256.")
    nombre = secure_filename(str(archivo.get("nombre") or ""))[:255]
    contenido = str(archivo.get("contenido_base64") or "")
    esperado = str(archivo.get("sha256") or "").strip().lower()
    if not nombre or not contenido or not re.fullmatch(r"[0-9a-f]{64}", esperado):
        raise ErrorApi(400, "validacion", "archivo debe tener nombre, contenido_base64 y sha256.")
    if len(contenido) > (reglas.MAX_ARCHIVO * 4) // 3 + 4:
        raise ErrorApi(413, "archivo_grande", "El archivo supera 5 MB.")
    try:
        crudo = base64.b64decode(contenido, validate=True)
    except (binascii.Error, ValueError):
        raise ErrorApi(400, "validacion", "contenido_base64 no es base64 valido.")
    if len(crudo) > reglas.MAX_ARCHIVO:
        raise ErrorApi(413, "archivo_grande", "El archivo supera 5 MB.")
    if hashlib.sha256(crudo).hexdigest() != esperado:
        raise ErrorApi(400, "archivo_corrupto",
                       "El archivo llego incompleto o alterado: el SHA-256 no coincide.")
    tipo = _tipo_real(crudo[:16])
    if tipo not in EXTENSION:
        raise ErrorApi(415, "formato_no_soportado", "Solo se permiten JPG, PNG o PDF reales.")
    DIR.mkdir(parents=True, exist_ok=True, mode=0o700)
    objeto = uuid.uuid4().hex + EXTENSION[tipo]
    ruta = DIR / objeto
    with open(ruta, "xb") as salida:
        salida.write(crudo)
    ruta.chmod(0o600)
    g.archivos.append(ruta)
    return {"objeto": objeto, "nombre_original": nombre, "mime_type": tipo,
            "tamano_bytes": len(crudo), "sha256": esperado}


def _borrar_archivos(desde):
    while len(g.archivos) > desde:
        g.archivos.pop().unlink(missing_ok=True)


# --------------------------------------------------------------------------- #
# Efecto de cada tipo de operacion. Lanzan ErrorApi igual que logistica:
# 409 = conflicto con el servidor; lo demas = rechazo.
# --------------------------------------------------------------------------- #
def _estado_recoleccion(id_op, datos, capturado):
    """RF-13: el Recolector avanza la recoleccion en campo."""
    recoleccion_id = _entero(datos, "recoleccion_id")
    esperado = str(datos.get("estado_esperado") or "").strip()
    nuevo = str(datos.get("estado") or "").strip()
    if not esperado or not nuevo:
        raise ErrorApi(400, "validacion", "estado_esperado y estado son obligatorios.")
    try:
        ubicacion = reglas.ubicacion_valida(datos.get("ubicacion"))
    except ValueError as exc:
        raise ErrorApi(400, "validacion", str(exc))
    fila = consultar("SELECT id, devolucion_id, estado FROM recolecciones WHERE id = %s FOR UPDATE",
                     (recoleccion_id,), uno=True)
    if not fila:
        raise ErrorApi(404, "no_encontrado", f"No existe la recoleccion {recoleccion_id}.")
    _expediente(fila["devolucion_id"])
    if fila["estado"] != esperado:
        raise ErrorApi(409, "conflicto_estado",
                       "La recoleccion cambio en el servidor mientras el dispositivo estaba sin conexion.",
                       {"estado_esperado": esperado, "estado_servidor": fila["estado"],
                        "estado_solicitado": nuevo})
    if not reglas.transicion_permitida(esperado, nuevo):
        raise ErrorApi(400, "transicion_invalida", f"No se puede pasar de {esperado} a {nuevo}.")
    ejecutar("UPDATE recolecciones SET estado = %s WHERE id = %s", (nuevo, recoleccion_id))
    detalle = f"Estado logistico: {nuevo}. Capturado sin conexion el {capturado.isoformat()}"
    if ubicacion:
        detalle += f" en {ubicacion['latitud']:.5f},{ubicacion['longitud']:.5f}"
    registrar_bitacora("estado_recoleccion", "devoluciones", fila["devolucion_id"], detalle)
    return fila["devolucion_id"], {"recoleccion_id": recoleccion_id, "estado_anterior": esperado,
                                   "estado": nuevo, "ubicacion": ubicacion}


def _recepcion(id_op, datos, capturado):
    """RF-15: recepcion en el centro. La fecha es la de la captura, cuando el
    producto llego fisicamente, no la de la sincronizacion."""
    devolucion_id = _entero(datos, "devolucion_id")
    coincide = _booleano(datos.get("coincide_expediente", True), "coincide_expediente")
    _expediente(devolucion_id, bloquear=True)
    recoleccion = consultar("SELECT estado FROM recolecciones WHERE devolucion_id = %s",
                            (devolucion_id,), uno=True)
    if not recoleccion or recoleccion["estado"] != "completada":
        raise ErrorApi(409, "estado_no_permite", "La recoleccion debe estar completada antes de recibir.",
                       {"estado_recoleccion": recoleccion["estado"] if recoleccion else None})
    previa = consultar("SELECT id FROM recepciones WHERE devolucion_id = %s", (devolucion_id,), uno=True)
    if previa:
        raise ErrorApi(409, "recepcion_duplicada", "La devolucion ya fue recibida.",
                       {"recepcion_id": previa["id"]})
    nueva = ejecutar("""INSERT INTO recepciones (devolucion_id, encargado_id, fecha_recepcion, coincide_expediente)
                        VALUES (%s, %s, %s, %s) RETURNING id, fecha_recepcion""",
                     (devolucion_id, g.usuario["id"], capturado, coincide), devolver=True)
    ejecutar("UPDATE devoluciones SET estado = 'recibida' WHERE id = %s", (devolucion_id,))
    registrar_bitacora("recepcion_confirmada", "devoluciones", devolucion_id,
                       f"Coincide expediente: {coincide}. Capturada sin conexion")
    return devolucion_id, {"recepcion_id": nueva["id"], "fecha_recepcion": nueva["fecha_recepcion"],
                           "coincide_expediente": coincide}


def _evidencia(id_op, datos, capturado):
    """RF-09: comentario o foto de campo. La etapa la decide el rol."""
    devolucion_id = _entero(datos, "devolucion_id")
    etapa = reglas.ETAPA_POR_ROL[g.usuario["rol"]]
    _expediente(devolucion_id)
    recoleccion = consultar("SELECT estado FROM recolecciones WHERE devolucion_id = %s",
                            (devolucion_id,), uno=True)
    estado = recoleccion["estado"] if recoleccion else None
    if etapa == "recoleccion" and estado in (None, "programada"):
        raise ErrorApi(409, "estado_no_permite", "La recoleccion no esta en curso.",
                       {"estado_recoleccion": estado})
    if etapa == "recepcion" and estado != "completada":
        raise ErrorApi(409, "estado_no_permite", "La recoleccion aun no termina.",
                       {"estado_recoleccion": estado})
    comentario = str(datos.get("comentario") or "").strip()
    if len(comentario) > 2000:
        raise ErrorApi(400, "validacion", "Comentario demasiado largo (maximo 2000).")
    archivo = datos.get("archivo") or None
    if not comentario and not archivo:
        raise ErrorApi(400, "validacion", "La evidencia necesita comentario o archivo.")
    guardado = _guardar_base64(archivo) if archivo else None
    if guardado:
        tipo = "fotografia" if guardado["mime_type"].startswith("image/") else "documento"
    else:
        tipo = "comentario"
    fila = ejecutar("""
        INSERT INTO evidencias (devolucion_id, usuario_id, tipo, etapa, comentario, bucket, objeto,
                                nombre_original, mime_type, tamano_bytes, fecha_registro)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
        (devolucion_id, g.usuario["id"], tipo, etapa, comentario or None,
         BUCKET if guardado else None, guardado["objeto"] if guardado else None,
         guardado["nombre_original"] if guardado else None,
         guardado["mime_type"] if guardado else None,
         guardado["tamano_bytes"] if guardado else None, capturado), devolver=True)
    # Llave id_operacion: si el commit fallara y la app reintenta, Mongo no
    # queda con dos documentos para la misma evidencia.
    mongo.get_mongo().evidencias_metadatos.update_one(
        {"id_operacion": id_op},
        {"$set": {"evidencia_id": fila["id"], "devolucion_id": devolucion_id,
                  "usuario_id": g.usuario["id"], "tipo": tipo, "etapa": etapa,
                  "origen": "sincronizacion_offline", "capturado_en": capturado,
                  "nombre_original": guardado["nombre_original"] if guardado else None,
                  "mime_type": guardado["mime_type"] if guardado else None,
                  "tamano_bytes": guardado["tamano_bytes"] if guardado else None,
                  "sha256": guardado["sha256"] if guardado else None}},
        upsert=True)
    registrar_bitacora("evidencia_agregada", "evidencias", fila["id"],
                       "Evidencia capturada sin conexion (sincronizacion)")
    return devolucion_id, {"evidencia_id": fila["id"], "tipo": tipo, "etapa": etapa}


APLICAR = {"estado_recoleccion": _estado_recoleccion, "recepcion": _recepcion,
           "evidencia": _evidencia}


# --------------------------------------------------------------------------- #
# Procesamiento de una operacion
# --------------------------------------------------------------------------- #
def _sin_guardar(id_op, tipo, codigo, tipo_error, mensaje):
    """Respuesta para lo que ni siquiera se puede registrar (id invalido o
    id de otro usuario/contenido)."""
    return {"id_operacion": id_op, "tipo": tipo, "estado": "rechazada", "repetida": False,
            "motivo": {"codigo": codigo, "tipo": tipo_error, "mensaje": mensaje, "detalles": None}}


def _repetida(id_op, tipo, huella):
    fila = consultar("""SELECT usuario_id, huella, resultado FROM operaciones_offline
                         WHERE id_operacion = %s FOR UPDATE""", (id_op,), uno=True)
    if fila["usuario_id"] != g.usuario["id"] or fila["huella"] != huella:
        # No se dice de quien es ni que contenia (RNF-16).
        return _sin_guardar(id_op, tipo, 409, "id_reutilizado",
                            "Ese id_operacion ya se uso con otros datos. Genera un id nuevo.")
    ejecutar("UPDATE operaciones_offline SET envios = envios + 1 WHERE id_operacion = %s", (id_op,))
    resultado = dict(fila["resultado"])
    resultado["repetida"] = True
    return resultado


def _aplicar(id_op, tipo, operacion, capturado, ahora):
    resultado = {"id_operacion": id_op, "tipo": tipo, "capturado_en": capturado}
    devolucion_id = None
    archivos_previos = len(g.archivos)
    ejecutar("SAVEPOINT efecto")
    try:
        if tipo in reglas.SOLO_EN_LINEA:
            raise ErrorApi(403, "requiere_conexion",
                           "Esta operacion solo se hace en linea: el servidor debe comprobar permisos y estado en el momento.")
        if tipo not in reglas.TIPOS_OFFLINE:
            raise ErrorApi(400, "tipo_desconocido", f"Tipo de operacion no soportado: {tipo or '(vacio)'}.")
        if g.usuario["rol"] not in reglas.TIPOS_OFFLINE[tipo]["roles"]:
            raise ErrorApi(403, "sin_permiso", "Tu rol no puede enviar este tipo de operacion.")
        problema = reglas.problema_de_captura(capturado, ahora)
        if problema:
            raise ErrorApi(400, "captura_invalida", problema)
        datos = operacion.get("datos")
        if not isinstance(datos, dict):
            raise ErrorApi(400, "validacion", "datos debe ser un objeto.")
        devolucion_id, respuesta = APLICAR[tipo](id_op, datos, capturado)
        ejecutar("RELEASE SAVEPOINT efecto")
        resultado.update(estado="aceptada", devolucion_id=devolucion_id, respuesta=respuesta)
    except ErrorApi as exc:
        # Se deshace el efecto a medias pero se GUARDA la decision: si la app
        # reintenta con el mismo id recibe el mismo conflicto o rechazo.
        ejecutar("ROLLBACK TO SAVEPOINT efecto")
        _borrar_archivos(archivos_previos)
        devolucion_id = None
        resultado.update(estado=reglas.estado_por_codigo(exc.codigo),
                         motivo={"codigo": exc.codigo, "tipo": exc.tipo,
                                 "mensaje": exc.mensaje, "detalles": exc.detalles})
    resultado["procesado_en"] = ahora
    resultado = _plano(resultado)
    ejecutar("""UPDATE operaciones_offline SET estado = %s, resultado = %s::jsonb, devolucion_id = %s
                 WHERE id_operacion = %s""",
             (resultado["estado"], json.dumps(resultado), devolucion_id, id_op))
    resultado["repetida"] = False
    return resultado


def _procesar(operacion, dispositivo, ahora):
    if not isinstance(operacion, dict):
        return _sin_guardar(None, None, 400, "validacion", "Cada operacion debe ser un objeto.")
    tipo = str(operacion.get("tipo") or "").strip()[:40]
    id_op = reglas.id_operacion_valido(operacion.get("id_operacion"))
    if not id_op:
        return _sin_guardar(operacion.get("id_operacion"), tipo, 400, "validacion",
                            "id_operacion debe ser un UUID generado por el dispositivo.")
    huella = reglas.huella(operacion)
    capturado = reglas.leer_fecha_captura(operacion.get("capturado_en"))
    archivos_previos = len(g.archivos)
    ejecutar("SAVEPOINT operacion")
    try:
        # Primero se aparta el id. Si otra peticion trae el mismo id al mismo
        # tiempo, PostgreSQL la hace esperar en la llave primaria y despues
        # cae en ON CONFLICT: nunca se aplican las dos.
        nueva = ejecutar("""
            INSERT INTO operaciones_offline (id_operacion, usuario_id, dispositivo_id, tipo, huella,
                                             estado, resultado, capturado_en)
            VALUES (%s, %s, %s, %s, %s, 'rechazada', '{}'::jsonb, %s)
            ON CONFLICT (id_operacion) DO NOTHING RETURNING id_operacion""",
            (id_op, g.usuario["id"], dispositivo, tipo, huella, capturado or ahora), devolver=True)
        if nueva:
            resultado = _aplicar(id_op, tipo, operacion, capturado, ahora)
        else:
            resultado = _repetida(id_op, tipo, huella)
        ejecutar("RELEASE SAVEPOINT operacion")
        return resultado
    except Exception:
        # Falla inesperada (Mongo caido, disco lleno...): no se guarda nada de
        # esta operacion y la app la vuelve a enviar con el mismo id.
        log.exception("Operacion %s no procesada cid=%s", id_op, g.get("correlation_id"))
        ejecutar("ROLLBACK TO SAVEPOINT operacion")
        _borrar_archivos(archivos_previos)
        return {"id_operacion": id_op, "tipo": tipo, "estado": "reintentar", "repetida": False,
                "motivo": {"codigo": 503, "tipo": "error_temporal",
                           "mensaje": "No se pudo procesar ahora. Vuelve a enviarla con el mismo id_operacion.",
                           "detalles": None}}


# --------------------------------------------------------------------------- #
# Endpoints
# --------------------------------------------------------------------------- #
@api.post("/operaciones")
@requiere_jwt(*ROLES)
def sincronizar():
    """Recibe la cola de operaciones pendientes del dispositivo, en orden."""
    limitar("sincronizacion", 30, 60, sujeto=f"usuario{g.usuario['id']}")
    datos = leer_cuerpo(os.path.join(CONTRATOS, "lote.xsd"))
    dispositivo = str(datos.get("dispositivo_id") or "").strip()
    if not DISPOSITIVO.fullmatch(dispositivo):
        raise ErrorApi(400, "validacion", "dispositivo_id: 1 a 64 letras, numeros, _ . : o -.")
    operaciones = datos.get("operaciones")
    if not isinstance(operaciones, list) or not 1 <= len(operaciones) <= reglas.MAX_OPERACIONES:
        raise ErrorApi(400, "validacion",
                       f"operaciones debe ser una lista de 1 a {reglas.MAX_OPERACIONES} elementos.")
    ahora = datetime.now(timezone.utc)
    g.archivos = []
    resultados = [_procesar(op, dispositivo, ahora) for op in operaciones]
    try:
        confirmar()
    except Exception:
        _borrar_archivos(0)
        raise
    for r in resultados:
        if r["estado"] == "aceptada" and not r["repetida"]:
            mongo.registrar_evento(NOMBRE, "operacion_offline_aceptada",
                                   {"id_operacion": r["id_operacion"], "tipo": r["tipo"],
                                    "devolucion_id": r.get("devolucion_id"),
                                    "dispositivo_id": dispositivo})
    resumen = Counter(r["estado"] for r in resultados)
    return responder({
        "dispositivo_id": dispositivo,
        "recibidas": len(resultados),
        "resumen": {e: resumen.get(e, 0) for e in (*ESTADOS, "reintentar")},
        "repetidas": sum(1 for r in resultados if r["repetida"]),
        "resultados": resultados,
    }, 200, "sincronizacion")


@api.get("/tipos")
@requiere_jwt(*ROLES, *VEN_TODO)
def tipos():
    """Catalogo para que la app arme sus menus y su cola offline."""
    rol = g.usuario["rol"]
    return responder({
        "tipos": [{"tipo": t, "descripcion": d["descripcion"], "campos": d["campos"],
                   "permitido_para_tu_rol": rol in d["roles"]}
                  for t, d in reglas.TIPOS_OFFLINE.items()],
        "solo_en_linea": list(reglas.SOLO_EN_LINEA),
        "limites": {"operaciones_por_envio": reglas.MAX_OPERACIONES,
                    "dias_maximos_sin_sincronizar": reglas.MAX_DIAS_OFFLINE,
                    "bytes_por_archivo": reglas.MAX_ARCHIVO},
    }, 200, "tipos")


_COLUMNAS = """o.id_operacion::text AS id_operacion, o.usuario_id, o.dispositivo_id, o.tipo,
               o.devolucion_id, o.estado, o.capturado_en, o.recibido_en, o.envios, o.resultado"""
_DESDE = """FROM operaciones_offline o
            LEFT JOIN devoluciones d ON d.id = o.devolucion_id
            LEFT JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
            LEFT JOIN ventas v ON v.id = vd.venta_id"""


def _filtro_visibilidad():
    """Cada quien ve sus operaciones; Supervisor y Administrador ven las de
    todos (el Supervisor con sucursal, solo las de su tienda)."""
    if g.usuario["rol"] in VEN_TODO:
        return condicion_tienda("v.tienda_id")
    return "o.usuario_id = %s", (g.usuario["id"],)


@api.get("/operaciones")
@requiere_jwt(*ROLES, *VEN_TODO)
def listar():
    condiciones, params = [], []
    sql, valores = _filtro_visibilidad()
    if sql:
        condiciones.append(sql); params.extend(valores)
    estado = (request.args.get("estado") or "").strip()
    if estado:
        if estado not in ESTADOS:
            raise ErrorApi(400, "validacion", f"estado debe ser uno de {', '.join(ESTADOS)}.")
        condiciones.append("o.estado = %s"); params.append(estado)
    dispositivo = (request.args.get("dispositivo_id") or "").strip()
    if dispositivo:
        condiciones.append("o.dispositivo_id = %s"); params.append(dispositivo)
    if request.args.get("devolucion_id"):
        condiciones.append("o.devolucion_id = %s")
        params.append(_entero(request.args, "devolucion_id"))
    where = (" WHERE " + " AND ".join(condiciones)) if condiciones else ""
    pag = leer_paginacion()
    filas = consultar(f"SELECT {_COLUMNAS} {_DESDE}{where} ORDER BY o.recibido_en DESC LIMIT %s OFFSET %s",
                      (*params, pag.limite, pag.desplazamiento))
    total = consultar(f"SELECT count(*) AS n {_DESDE}{where}", tuple(params), uno=True)["n"]
    return responder(paginar(filas, total, pag), 200, "operaciones")


@api.get("/operaciones/<id_operacion>")
@requiere_jwt(*ROLES, *VEN_TODO)
def detalle(id_operacion):
    """La app pregunta por una operacion cuya respuesta no le llego."""
    id_op = reglas.id_operacion_valido(id_operacion)
    if not id_op:
        raise ErrorApi(404, "no_encontrado", "No existe esa operacion.")
    sql, valores = _filtro_visibilidad()
    fila = consultar(f"SELECT {_COLUMNAS} {_DESDE} WHERE o.id_operacion = %s" + (f" AND {sql}" if sql else ""),
                     (id_op, *valores), uno=True)
    if not fila:
        # 404 tambien si es de otro usuario: no se confirma que exista.
        raise ErrorApi(404, "no_encontrado", "No existe esa operacion.")
    return responder(fila, 200, "operacion")


def create_app():
    app = Flask(__name__)
    app.json.sort_keys = False
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
    respuestas.registrar(app, NOMBRE)
    app.teardown_appcontext(cerrar_conexion)
    app.register_blueprint(api)
    docs.registrar(app, os.path.join(os.path.dirname(__file__), "openapi.yaml"))

    @app.get("/health")
    def health():
        deps = {"postgresql": salud_postgres(), "redis": salud_redis(), "mongodb": mongo.salud_mongo()}
        ok = all(x["ok"] for x in deps.values())
        return responder({"servicio": NOMBRE, "version": "v1", "estado": "ok" if ok else "degradado",
                          "dependencias": deps}, 200 if ok else 503)
    return app
