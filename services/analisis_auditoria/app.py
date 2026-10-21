"""Analisis y auditoria, servicio no destructivo.

PostgreSQL es la fuente oficial; se crean snapshots derivados en la coleccion
existente MongoDB 'resultados_analisis'. Los Pareto se calculan mediante un
pipeline aggregate real y se cachean en Redis 10 min. No modifica estados,
reembolsos ni el panel web original y NUNCA decide una causa automaticamente.
"""
import hashlib
import json
import os
import uuid
import unicodedata
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from flask import Blueprint, Flask, g, request
from pymongo import UpdateOne

from shared import docs, mongo, respuestas
from shared.infra import (PREFIJO, cerrar_conexion, consultar, get_redis,
                          registrar_bitacora, salud_postgres, salud_redis)
from shared.paginacion import leer_paginacion, paginar
from shared.respuestas import ErrorApi, leer_cuerpo, responder
from shared.seguridad import ADMINISTRADOR, ANALISTA, CLIENTE, requiere_jwt

NOMBRE="analisis-auditoria"
api=Blueprint("analisis",__name__,url_prefix="/api/v1/analisis")
auditoria=Blueprint("auditoria",__name__,url_prefix="/api/v1/auditoria")
DIMENSIONES={"motivo","producto","lote","proveedor","tienda","ruta","transportista","estado"}
MEDIDAS={"frecuencia","cantidad","costo"}
TTL=600
CONTRATOS=os.path.join(os.path.dirname(__file__),"contratos")
PALABRAS_MOTIVO={
    "Producto danado":["roto","danado","golpe","quebrado","aplastado","derrame"],
    "Caducidad vencida":["caduc","vencido","expirado"],
    "Cadena de frio rota":["caliente","temperatura","refriger","descongelado","frio"],
    "Error en el pedido":["incorrecto","equivocado","otro producto","no pedi"],
    "Calidad inferior":["mal sabor","olor","color","calidad","textura"],
    "Etiqueta incorrecta":["etiqueta","rotulo","informacion incorrecta"],
}

# JOIN idéntico a BASE_CAUSAS de app/blueprints/panel.py, con UNA fila por
# devolucion. La vista de costo ya agrega costos a una sola fila por caso.
SQL_SNAPSHOTS="""
SELECT d.id AS devolucion_id,d.folio_devolucion,d.estado,d.fecha_solicitud,
       d.cantidad_devuelta, m.nombre AS motivo,p.nombre AS producto,
       l.numero_lote AS lote,pr.nombre AS proveedor,t.nombre AS tienda,
       COALESCE(ru.origen || ' -> ' || ru.destino,'Sin ruta asignada') AS ruta,
       COALESCE(tr.nombre,'Sin transportista') AS transportista,
       COALESCE(vc.costo_total,0) AS costo_total
  FROM devoluciones d
  JOIN motivos m ON m.id=d.motivo_id
  JOIN venta_detalle vd ON vd.id=d.venta_detalle_id
  JOIN ventas v ON v.id=vd.venta_id
  JOIN tiendas t ON t.id=v.tienda_id
  JOIN lotes l ON l.id=vd.lote_id
  JOIN productos p ON p.id=l.producto_id
  JOIN proveedores pr ON pr.id=l.proveedor_id
  LEFT JOIN recolecciones rec ON rec.devolucion_id=d.id
  LEFT JOIN rutas ru ON ru.id=rec.ruta_id
  LEFT JOIN transportistas tr ON tr.id=rec.transportista_id
  LEFT JOIN vista_costo_devolucion vc ON vc.devolucion_id=d.id
 WHERE d.eliminado_en IS NULL
"""


def _filtro_fecha(valor,nombre):
    if not valor:
        return None
    try:return date.fromisoformat(valor)
    except ValueError:
        raise ErrorApi(400,"validacion",f"{nombre} debe tener formato AAAA-MM-DD.")


def _parametros_pareto():
    dim=request.args.get("dimension","motivo")
    medida=request.args.get("medida","frecuencia")
    if dim not in DIMENSIONES or medida not in MEDIDAS:
        raise ErrorApi(400,"validacion","Dimension o medida desconocida.")
    desde=_filtro_fecha(request.args.get("desde"),"desde")
    hasta=_filtro_fecha(request.args.get("hasta"),"hasta")
    if desde and hasta and hasta<desde:
        raise ErrorApi(400,"validacion","hasta no puede ser menor que desde.")
    return dim,medida,desde,hasta


def calcular_pareto(coleccion,dimension,medida,desde=None,hasta=None):
    """MongoDB hace GROUP y SUM reales, no agrupar una lista en Python."""
    match={"tipo_analisis":"snapshot_devolucion","vigente":True}
    if desde or hasta:
        rango={}
        if desde:
            rango["$gte"]=datetime.combine(desde,time.min,tzinfo=timezone.utc)
        if hasta:
            rango["$lt"]=datetime.combine(hasta+timedelta(days=1),time.min,tzinfo=timezone.utc)
        match["fecha_solicitud"]=rango
    suma={"frecuencia":1,"cantidad":"$cantidad_devuelta","costo":"$costo_total"}[medida]
    pipeline=[{"$match":match},
              {"$group":{"_id":"$"+dimension,"total":{"$sum":suma},
                         "casos":{"$sum":1}}},
              {"$sort":{"total":-1,"_id":1}}]
    filas=list(coleccion.aggregate(pipeline))
    total=sum(float(x["total"]) for x in filas)
    acumulado=0.0
    salida=[]
    for x in filas:
        valor=float(x["total"])
        acumulado+=valor
        salida.append({"etiqueta":str(x["_id"] or "Sin dato"),
                       "total":round(valor,2),"casos":x["casos"],
                       "porcentaje":round(valor/total*100,2) if total else 0,
                       "porcentaje_acumulado":round(acumulado/total*100,2) if total else 0})
    return {"dimension":dimension,"medida":medida,"total_general":round(total,2),
            "categorias":salida,"interpretacion":"Patrones para revision humana; no confirman causalidad."}


def clasificar_descripcion(descripcion):
    """Ranking explicable por palabras; siempre es sugerencia (RN-11)."""
    texto="".join(c for c in unicodedata.normalize("NFD",descripcion.lower())
                  if unicodedata.category(c)!="Mn")
    candidatos=[]
    for motivo,palabras in PALABRAS_MOTIVO.items():
        coincidencias=sorted({p for p in palabras if p in texto})
        if coincidencias:
            candidatos.append({"motivo":motivo,"puntaje":len(coincidencias),
                               "coincidencias":coincidencias})
    candidatos.sort(key=lambda x:(-x["puntaje"],x["motivo"]))
    return candidatos


@api.post("/clasificar-motivo")
@requiere_jwt(CLIENTE,ADMINISTRADOR,ANALISTA)
def clasificar_motivo():
    datos=leer_cuerpo(os.path.join(CONTRATOS,"clasificacion.xsd"))
    descripcion=str(datos.get("descripcion") or "").strip()
    if len(descripcion)<10 or len(descripcion)>2000:
        raise ErrorApi(400,"validacion","descripcion debe contener entre 10 y 2000 caracteres.")
    sugerencias=clasificar_descripcion(descripcion)
    activos={x["nombre"]:x["id"] for x in consultar("SELECT id,nombre FROM motivos WHERE activo=TRUE")}
    salida=[{**s,"motivo_id":activos[s["motivo"]]} for s in sugerencias if s["motivo"] in activos]
    return responder({"sugerencias":salida[:3],"requiere_confirmacion":True,
                     "explicacion":"La clasificacion orienta; el usuario confirma el motivo."},
                    raiz="clasificacion")


@api.get("/alertas-fraude")
@requiere_jwt(ADMINISTRADOR,ANALISTA)
def alertas_fraude():
    """Senales explicables; no acusa ni bloquea automaticamente (RF-25)."""
    filas=consultar("""
        SELECT v.cliente_id,u.nombre AS cliente,COUNT(DISTINCT d.id) AS devoluciones_90_dias,
               COUNT(DISTINCT d.id) FILTER (WHERE d.estado='rechazada') AS rechazadas,
               COALESCE(SUM(rb.monto) FILTER (WHERE rb.estado='aprobado'),0) AS monto_reembolsado
          FROM devoluciones d JOIN venta_detalle vd ON vd.id=d.venta_detalle_id
          JOIN ventas v ON v.id=vd.venta_id JOIN usuarios u ON u.id=v.cliente_id
          LEFT JOIN reembolsos rb ON rb.devolucion_id=d.id AND rb.eliminado_en IS NULL
         WHERE d.eliminado_en IS NULL AND d.fecha_solicitud>=CURRENT_TIMESTAMP-INTERVAL '90 days'
         GROUP BY v.cliente_id,u.nombre
        HAVING COUNT(DISTINCT d.id)>=3
            OR COUNT(DISTINCT d.id) FILTER (WHERE d.estado='rechazada')>=2
            OR COALESCE(SUM(rb.monto) FILTER (WHERE rb.estado='aprobado'),0)>=5000
         ORDER BY devoluciones_90_dias DESC,monto_reembolsado DESC
    """)
    alertas=[]
    for fila in filas:
        razones=[]
        if fila["devoluciones_90_dias"]>=3: razones.append("frecuencia alta en 90 dias")
        if fila["rechazadas"]>=2: razones.append("multiples solicitudes rechazadas")
        if float(fila["monto_reembolsado"])>=5000: razones.append("monto reembolsado elevado")
        alertas.append({**fila,"razones":razones,"requiere_revision_humana":True})
    return responder({"datos":alertas,"total":len(alertas),
                     "aviso":"Son indicadores preventivos, no una determinacion de fraude."},
                    raiz="alertas_fraude")


@api.post("/sincronizar")
@requiere_jwt(ADMINISTRADOR,ANALISTA)
def sincronizar():
    """Proyeccion incremental; no hace UPDATE ni DELETE de PostgreSQL.

    Requerido tras agregar o modificar casos/costos, o antes de la demo.
    Los registros desaparecidos se marcan no vigentes al finalizar el lote.
    """
    filas=consultar(SQL_SNAPSHOTS)
    coleccion=mongo.get_mongo().resultados_analisis
    # Unico SOLO para la subcoleccion de snapshots, no afecta Pareto previo.
    coleccion.create_index([("tipo_analisis",1),("devolucion_id",1)],unique=True,
        partialFilterExpression={"tipo_analisis":"snapshot_devolucion"},
        name="idx_snapshot_devolucion_unico")
    lote=uuid.uuid4().hex
    ahora=datetime.now(timezone.utc)
    operaciones=[]
    for fila in filas:
        documento={k:(float(v) if isinstance(v,Decimal) else v) for k,v in fila.items()}
        documento.update({"tipo_analisis":"snapshot_devolucion","vigente":True,
                          "lote_actualizacion":lote,"fecha_calculo":ahora})
        operaciones.append(UpdateOne({"tipo_analisis":"snapshot_devolucion",
                                     "devolucion_id":fila["devolucion_id"]},
                                    {"$set":documento},upsert=True))
    if operaciones:
        coleccion.bulk_write(operaciones,ordered=False)
    coleccion.update_many({"tipo_analisis":"snapshot_devolucion",
                           "lote_actualizacion":{"$ne":lote}},
                          {"$set":{"vigente":False,"fecha_calculo":ahora}})
    coleccion.insert_one({"tipo_analisis":"sincronizacion",
                          "fecha_calculo":ahora,"lote_actualizacion":lote,
                          "casos":len(filas),"correlation_id":g.correlation_id})
    r=get_redis()
    version=r.incr(PREFIJO+"analisis:version")
    r.expire(PREFIJO+"analisis:version",86400)
    registrar_bitacora("analisis_sincronizado","resultados_analisis",None,
                      f"Actualizados {len(filas)} casos en MongoDB")
    return responder({"casos_sincronizados":len(filas),"version_cache":version,
                     "fecha":ahora.isoformat(),"solo_lectura_postgresql":True},raiz="sincronizacion")


@api.get("/pareto")
@requiere_jwt(ADMINISTRADOR,ANALISTA)
def pareto():
    dim,medida,desde,hasta=_parametros_pareto()
    r=get_redis()
    version=r.get(PREFIJO+"analisis:version") or "0"
    valores=f"{version}|{dim}|{medida}|{desde}|{hasta}"
    cache_key=PREFIJO+"cache:causas:"+hashlib.sha256(valores.encode()).hexdigest()[:24]
    cache=r.get(cache_key)
    if cache:
        datos=json.loads(cache)
        datos["cache"]="hit"
        return responder(datos,raiz="pareto")
    coleccion=mongo.get_mongo().resultados_analisis
    if not coleccion.find_one({"tipo_analisis":"sincronizacion"}, {"_id":1}):
        raise ErrorApi(409,"analisis_sin_datos",
                       "Primero ejecuta POST /api/v1/analisis/sincronizar.")
    datos=calcular_pareto(coleccion,dim,medida,desde,hasta)
    datos["cache"]="miss"
    datos["version_datos"]=version
    # Se conserva tambien el resultado del analisis en MongoDB para trazabilidad.
    coleccion.insert_one({"tipo_analisis":"pareto","dimension":dim,"medida":medida,
                          "desde":desde.isoformat() if desde else None,
                          "hasta":hasta.isoformat() if hasta else None,
                          "fecha_calculo":datetime.now(timezone.utc),
                          "usuario_id":g.usuario["id"],"correlation_id":g.correlation_id,
                          "resultado":datos})
    r.setex(cache_key,TTL,json.dumps(datos))
    return responder(datos,raiz="pareto")


@api.get("/resumen")
@requiere_jwt(ADMINISTRADOR,ANALISTA)
def resumen():
    coleccion=mongo.get_mongo().resultados_analisis
    total=coleccion.count_documents({"tipo_analisis":"snapshot_devolucion","vigente":True})
    total_pareto=coleccion.count_documents({"tipo_analisis":"pareto"})
    return responder({"casos_sincronizados":total,"reportes_pareto":total_pareto,
                     "nota":"No implica causa raiz comprobada."},raiz="resumen")


@api.get("/eventos")
@requiere_jwt(ADMINISTRADOR,ANALISTA)
def eventos():
    pag=leer_paginacion()
    filtro={}
    cid=(request.args.get("correlation_id") or "").strip()
    if cid:
        if len(cid)>100:
            raise ErrorApi(400,"validacion","correlation_id demasiado largo.")
        filtro["correlation_id"]=cid
    servicio=(request.args.get("servicio") or "").strip()
    if servicio:
        if len(servicio)>60:
            raise ErrorApi(400,"validacion","servicio demasiado largo.")
        filtro["servicio"]=servicio
    coleccion=mongo.get_mongo().eventos
    total=coleccion.count_documents(filtro)
    docs_mongo=list(coleccion.find(filtro,{"datos":0})
                    .sort("fecha",-1).skip(pag.desplazamiento).limit(pag.limite))
    return responder(paginar(mongo.a_json(docs_mongo),total,pag),raiz="eventos")


@auditoria.get("")
@requiere_jwt(ADMINISTRADOR,ANALISTA)
def bitacora():
    pag=leer_paginacion()
    condiciones=["1=1"]
    parametros=[]
    for campo in ("accion","entidad","correlation_id"):
        valor=(request.args.get(campo) or "").strip()
        if valor:
            if len(valor)>100:
                raise ErrorApi(400,"validacion",f"Filtro {campo} demasiado largo.")
            condiciones.append(f"b.{campo}=%s")
            parametros.append(valor)
    where=" AND ".join(condiciones)
    total=consultar(f"SELECT COUNT(*) AS n FROM bitacora b WHERE {where}",
                   tuple(parametros),uno=True)["n"]
    filas=consultar(f"""
        SELECT b.id,b.accion,b.entidad,b.entidad_id,b.detalle,
               b.correlation_id,b.fecha,u.nombre AS usuario
          FROM bitacora b LEFT JOIN usuarios u ON u.id=b.usuario_id
         WHERE {where} ORDER BY b.fecha DESC,b.id DESC LIMIT %s OFFSET %s
    """,tuple(parametros)+(pag.limite,pag.desplazamiento))
    return responder(paginar(filas,total,pag),raiz="bitacora")


def create_app():
    app=Flask(__name__)
    app.json.sort_keys=False
    respuestas.registrar(app,NOMBRE)
    app.teardown_appcontext(cerrar_conexion)
    app.register_blueprint(api)
    app.register_blueprint(auditoria)
    docs.registrar(app,os.path.join(os.path.dirname(__file__),"openapi.yaml"))

    @app.get("/health")
    def health():
        deps={"postgresql":salud_postgres(),"redis":salud_redis(),
              "mongodb":mongo.salud_mongo()}
        ok=all(x["ok"] for x in deps.values())
        return responder({"servicio":NOMBRE,"version":"v1","estado":"ok" if ok else "degradado",
                         "dependencias":deps},200 if ok else 503)
    return app

