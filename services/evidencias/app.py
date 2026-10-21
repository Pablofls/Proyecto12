"""Evidencias privadas por devolucion.

Los archivos se guardan en un volumen Docker privado; PostgreSQL conserva la
referencia oficial y MongoDB los metadatos flexibles. Nunca expone /uploads
publicamente. Solo usuarios autorizados pueden generar enlaces firmados (15m).
No modifica la tabla ni los formularios actuales del monolito.
"""
import hashlib
import hmac
import os
import re
import time
import uuid
from pathlib import Path

from flask import Blueprint, Flask, g, request, send_file
from werkzeug.utils import secure_filename

from shared import docs, mongo, respuestas
from shared.infra import (cerrar_conexion, consultar, ejecutar, registrar_bitacora,
                          salud_postgres, salud_redis)
from shared.paginacion import leer_paginacion, paginar
from shared.respuestas import ErrorApi, leer_cuerpo, responder
from shared.seguridad import (ADMINISTRADOR, ANALISTA, CLIENTE, ENCARGADO_CENTRO,
                              INSPECTOR, comprobar_en_redis, decodificar,
                              requiere_jwt, secreto, token_de_la_peticion)

NOMBRE = "evidencias"
api = Blueprint("evidencias", __name__, url_prefix="/api/v1/evidencias")
CONTRATOS = os.path.join(os.path.dirname(__file__), "contratos")
DIR = Path(os.environ.get("EVIDENCIAS_DIR", "/srv/evidencias_privadas"))
BUCKET = "orvia-evidencias-local"
MAX = 10 * 1024 * 1024
EXTENSION = {"image/jpeg": ".jpg", "image/png": ".png", "application/pdf": ".pdf"}
ETAPAS = {"solicitud", "recoleccion", "recepcion", "inspeccion"}
OBJETO_SEGURO = re.compile(r"^[0-9a-f]{32}\.(jpg|png|pdf)$")


def validar_entero(valor, nombre):
    try:
        if isinstance(valor, bool):
            raise ValueError
        n=int(valor)
        if n <= 0:
            raise ValueError
        return n
    except (ValueError, TypeError):
        raise ErrorApi(400,"validacion",f"{nombre} debe ser entero positivo.")


def contexto(devolucion_id, lectura=True):
    """Comprueba el dueño del expediente, también para enlaces de archivo."""
    exp=consultar("""
        SELECT d.id,d.estado,v.cliente_id,ir.inspector_id
          FROM devoluciones d
          JOIN venta_detalle vd ON vd.id=d.venta_detalle_id
          JOIN ventas v ON v.id=vd.venta_id
          LEFT JOIN inspecciones_ref ir ON ir.devolucion_id=d.id
         WHERE d.id=%s AND d.eliminado_en IS NULL AND v.eliminado_en IS NULL
    """,(devolucion_id,),uno=True)
    if not exp:
        raise ErrorApi(404,"no_encontrado","La devolucion no existe.")
    usuario=g.usuario
    rol=usuario["rol"]
    if rol==CLIENTE and exp["cliente_id"]!=usuario["id"]:
        raise ErrorApi(403,"sin_permiso","No tienes acceso a esa devolucion.")
    if rol==INSPECTOR and exp["inspector_id"]!=usuario["id"]:
        raise ErrorApi(403,"sin_permiso","La inspeccion no esta asignada a tu usuario.")
    if not lectura and rol not in (CLIENTE, INSPECTOR):
        raise ErrorApi(403,"sin_permiso","Solo cliente e inspector pueden adjuntar archivos.")
    return exp


def fila_evidencia(evidencia_id):
    fila=consultar("""
        SELECT e.id,e.devolucion_id,e.usuario_id,e.tipo,e.etapa,e.comentario,
               e.bucket,e.objeto,e.nombre_original,e.mime_type,e.tamano_bytes,
               e.fecha_registro
          FROM evidencias e
         WHERE e.id=%s AND e.eliminado_en IS NULL
    """,(evidencia_id,),uno=True)
    if not fila:
        raise ErrorApi(404,"no_encontrado","Evidencia inexistente.")
    return fila


def autenticar_descarga():
    """Verifica el JWT cuando no existe un enlace firmado valido."""
    claims=decodificar(token_de_la_peticion())
    comprobar_en_redis(claims)
    g.usuario={"id":int(claims["sub"]), "rol":claims.get("rol"),
               "nombre":claims.get("nombre")}


def _firma(evidencia_id, vence):
    mensaje=f"{evidencia_id}:{vence}".encode("ascii")
    return hmac.new(secreto().encode("utf-8"),mensaje,hashlib.sha256).hexdigest()


def firma_valida(evidencia_id, exp, firma):
    try:
        vencimiento=int(exp)
    except (ValueError,TypeError):
        return False
    # Evita enlaces demasiado largos aunque estén bien firmados.
    ahora=int(time.time())
    if vencimiento < ahora or vencimiento > ahora+900:
        return False
    return isinstance(firma,str) and hmac.compare_digest(_firma(evidencia_id,vencimiento),firma)


def _tipo_real(datos):
    if datos.startswith(b"\xff\xd8\xff"):
        return "image/jpeg"
    if datos.startswith(b"\x89PNG\r\n\x1a\n"):
        return "image/png"
    if datos.startswith(b"%PDF-"):
        return "application/pdf"
    return None


def guardar_archivo(archivo):
    """Escribe en streaming hasta MAX bytes; la extensión del cliente no manda."""
    nombre=secure_filename(archivo.filename or "")[:255]
    if not nombre:
        raise ErrorApi(400,"validacion","Archivo sin nombre.")
    intro=archivo.stream.read(16)
    tipo=_tipo_real(intro)
    if tipo not in EXTENSION:
        raise ErrorApi(415,"formato_no_soportado","Solo se permiten JPG, PNG o PDF reales.")
    DIR.mkdir(parents=True,exist_ok=True,mode=0o700)
    objeto=uuid.uuid4().hex+EXTENSION[tipo]
    ruta=DIR/objeto
    total=0
    try:
        with open(ruta,"xb") as salida:
            for bloque in (intro,):
                total+=len(bloque)
                salida.write(bloque)
            while True:
                bloque=archivo.stream.read(65536)
                if not bloque:break
                total+=len(bloque)
                if total>MAX:
                    raise ErrorApi(413,"archivo_grande","El archivo supera 10 MB.")
                salida.write(bloque)
        ruta.chmod(0o600)
    except Exception:
        ruta.unlink(missing_ok=True)
        raise
    return {"objeto":objeto,"nombre_original":nombre,"mime_type":tipo,
            "tamano_bytes":total,"ruta":ruta}


@api.post("")
@requiere_jwt(CLIENTE, INSPECTOR)
def crear():
    """multipart con 'archivo' o JSON/XML con tipo='comentario'."""
    es_archivo=request.mimetype=="multipart/form-data"
    if es_archivo:
        datos=request.form
        archivo=request.files.get("archivo")
        if not archivo:
            raise ErrorApi(400,"validacion","Falta el campo archivo.")
        tipo="fotografia" if _tipo_real(archivo.stream.read(16)) in ("image/jpeg","image/png") else "documento"
        archivo.stream.seek(0)
    else:
        datos=leer_cuerpo(os.path.join(CONTRATOS,"comentario.xsd"))
        tipo=datos.get("tipo")
        if tipo!="comentario":
            raise ErrorApi(400,"validacion","Para archivos usa multipart/form-data; JSON/XML solo para comentarios.")
    devolucion_id=validar_entero(datos.get("devolucion_id"),"devolucion_id")
    exp=contexto(devolucion_id,lectura=False)
    etapa=(datos.get("etapa") or "solicitud").strip()
    if etapa not in ETAPAS:
        raise ErrorApi(400,"validacion","Etapa no permitida.")
    if g.usuario["rol"]==CLIENTE and (etapa!="solicitud" or exp["estado"] not in ("solicitada","en_revision")):
        raise ErrorApi(409,"estado_no_permite","El cliente solo adjunta durante la solicitud o revision.")
    if g.usuario["rol"]==INSPECTOR and etapa!="inspeccion":
        raise ErrorApi(403,"sin_permiso","El inspector registra evidencias de inspeccion.")
    comentario=str(datos.get("comentario") or "").strip()
    if len(comentario)>2000:
        raise ErrorApi(400,"validacion","Comentario demasiado largo (maximo 2000).")
    if not es_archivo and not comentario:
        raise ErrorApi(400,"validacion","Comentario obligatorio.")
    guardado=None
    mongo_id=None
    try:
        if es_archivo:
            guardado=guardar_archivo(archivo)
            tipo="fotografia" if guardado["mime_type"].startswith("image/") else "documento"
        fila=ejecutar("""
            INSERT INTO evidencias (devolucion_id,usuario_id,tipo,etapa,comentario,
                                    bucket,objeto,nombre_original,mime_type,tamano_bytes)
            VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s,%s) RETURNING id
        """, (devolucion_id,g.usuario["id"],tipo,etapa,comentario or None,
               BUCKET if guardado else None,guardado["objeto"] if guardado else None,
               guardado["nombre_original"] if guardado else None,
               guardado["mime_type"] if guardado else None,
               guardado["tamano_bytes"] if guardado else None), devolver=True)
        metadatos={"evidencia_id":fila["id"],"devolucion_id":devolucion_id,
                   "usuario_id":g.usuario["id"],"tipo":tipo,"etapa":etapa,
                   "nombre_original":guardado["nombre_original"] if guardado else None,
                   "mime_type":guardado["mime_type"] if guardado else None,
                   "tamano_bytes":guardado["tamano_bytes"] if guardado else None}
        # Debe existir una insercion REAL en Mongo, no un simple contenedor.
        mongo_id=mongo.get_mongo().evidencias_metadatos.insert_one(metadatos).inserted_id
        registrar_bitacora("evidencia_agregada","evidencias",fila["id"],
                           "Evidencia asociada a una devolucion (API)")
    except Exception:
        # El manejador compartido confirma transacciones sin excepcion en teardown:
        # esta marca obliga al rollback y evita guardar una referencia huerfana.
        g.error_interno=True
        if mongo_id is not None:
            try:mongo.get_mongo().evidencias_metadatos.delete_one({"_id":mongo_id})
            except Exception:pass
        if guardado:
            guardado["ruta"].unlink(missing_ok=True)
        raise
    return responder({"id":fila["id"],"devolucion_id":devolucion_id,
                     "tipo":tipo,"metadatos_id":str(mongo_id)},201,"evidencia",
                    {"Location":f"/api/v1/evidencias/{fila['id']}"})


@api.get("")
@requiere_jwt()
def listar():
    dev=validar_entero(request.args.get("devolucion_id"),"devolucion_id")
    contexto(dev)
    pag=leer_paginacion()
    total=consultar("SELECT COUNT(*) AS n FROM evidencias WHERE devolucion_id=%s AND eliminado_en IS NULL",
                   (dev,),uno=True)["n"]
    filas=consultar("""
        SELECT id,devolucion_id,usuario_id,tipo,etapa,comentario,nombre_original,
               mime_type,tamano_bytes,fecha_registro FROM evidencias
         WHERE devolucion_id=%s AND eliminado_en IS NULL
         ORDER BY fecha_registro DESC,id DESC LIMIT %s OFFSET %s
    """,(dev,pag.limite,pag.desplazamiento))
    return responder(paginar(filas,total,pag),raiz="evidencias")


@api.get("/<int:evidencia_id>")
@requiere_jwt()
def detalle(evidencia_id):
    fila=fila_evidencia(evidencia_id)
    contexto(fila["devolucion_id"])
    # No se devuelve nombre interno del archivo ni bucket al cliente.
    fila.pop("objeto",None)
    fila.pop("bucket",None)
    docs_mongo=list(mongo.get_mongo().evidencias_metadatos.find(
        {"evidencia_id":evidencia_id},{"_id":0,"usuario_id":0}))
    fila["metadatos"]=mongo.a_json(docs_mongo)
    return responder(fila,raiz="evidencia")


@api.get("/<int:evidencia_id>/enlace")
@requiere_jwt()
def enlace(evidencia_id):
    fila=fila_evidencia(evidencia_id)
    contexto(fila["devolucion_id"])
    if fila["tipo"]=="comentario":
        raise ErrorApi(409,"sin_archivo","Un comentario no tiene archivo asociado.")
    exp=int(time.time())+900
    ruta=f"/api/v1/evidencias/{evidencia_id}/archivo?exp={exp}&firma={_firma(evidencia_id,exp)}"
    return responder({"url_relativa":ruta,"vigencia_segundos":900},raiz="enlace")


@api.get("/<int:evidencia_id>/archivo")
def descargar(evidencia_id):
    firma=request.args.get("firma")
    exp=request.args.get("exp")
    # Un enlace firmado concede acceso SOLO al archivo y caduca en <=15 min.
    if not firma_valida(evidencia_id,exp,firma):
        # Acceso directo alternativo para clientes autenticados por JWT.
        autenticar_descarga()
        fila=fila_evidencia(evidencia_id)
        contexto(fila["devolucion_id"])
    else:
        fila=fila_evidencia(evidencia_id)
    objeto=fila["objeto"]
    if fila["bucket"]!=BUCKET or not objeto or not OBJETO_SEGURO.fullmatch(objeto):
        raise ErrorApi(404,"no_encontrado","Archivo no disponible.")
    ruta=DIR/objeto
    if not ruta.is_file():
        raise ErrorApi(404,"no_encontrado","Archivo no disponible.")
    return send_file(ruta,mimetype=fila["mime_type"],as_attachment=True,
                     download_name=fila["nombre_original"] or "evidencia")


@api.delete("/<int:evidencia_id>")
@requiere_jwt(CLIENTE, INSPECTOR)
def eliminar(evidencia_id):
    fila=fila_evidencia(evidencia_id)
    exp=contexto(fila["devolucion_id"])
    if fila["usuario_id"]!=g.usuario["id"]:
        raise ErrorApi(403,"sin_permiso","Solo puedes retirar evidencias propias.")
    if g.usuario["rol"]==CLIENTE and exp["estado"] not in ("solicitada","en_revision"):
        raise ErrorApi(409,"estado_no_permite","No se puede retirar evidencia de un caso procesado.")
    ejecutar("UPDATE evidencias SET eliminado_en=NOW() WHERE id=%s",(evidencia_id,))
    registrar_bitacora("evidencia_retirada","evidencias",evidencia_id,
                       "Retiro logico de evidencia por API")
    # Archivo permanece para auditoria (RN-12) hasta la politica de retencion.
    return responder({"id":evidencia_id,"eliminada":True},raiz="evidencia")


def create_app():
    app=Flask(__name__)
    app.json.sort_keys=False
    # Limite de cuerpo con margen multipart; max real se comprueba al streaming.
    app.config["MAX_CONTENT_LENGTH"]=MAX+1024*64
    respuestas.registrar(app,NOMBRE)
    app.teardown_appcontext(cerrar_conexion)
    app.register_blueprint(api)
    docs.registrar(app,os.path.join(os.path.dirname(__file__),"openapi.yaml"))

    @app.get("/health")
    def health():
        try:
            DIR.mkdir(parents=True,exist_ok=True,mode=0o700)
            directorio={"ok":os.access(DIR,os.W_OK),"error":None}
        except OSError:
            directorio={"ok":False,"error":"no responde"}
        deps={"postgresql":salud_postgres(),"redis":salud_redis(),
              "mongodb":mongo.salud_mongo(),"almacen_privado":directorio}
        ok=all(x["ok"] for x in deps.values())
        return responder({"servicio":NOMBRE,"version":"v1","estado":"ok" if ok else "degradado",
                         "dependencias":deps},200 if ok else 503)
    return app

