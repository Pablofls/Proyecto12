"""Microservicio de inspecciones y disposicion (RF-16 a RF-19, RN-05 a RN-07)."""
import os
from datetime import datetime, timezone
from flask import Blueprint, Flask, g, request
from shared import docs, mongo, respuestas
from shared.infra import cerrar_conexion, consultar, ejecutar, registrar_bitacora, salud_postgres, salud_redis
from shared.respuestas import ErrorApi, leer_cuerpo, responder
from shared.seguridad import ANALISTA, ENCARGADO_CENTRO, INSPECTOR, requiere_jwt

NOMBRE="inspecciones"; CONTRATOS=os.path.join(os.path.dirname(__file__),"contratos")
api=Blueprint(NOMBRE,__name__,url_prefix="/api/v1/inspecciones")
DESTINOS={"inventario","reparacion","reacondicionamiento","reciclaje","devolucion_proveedor","desecho","donacion"}

def _bool(v): return v is True or str(v).strip().lower() in ("true","1","si")
def _bool_estricto(v, campo):
    if isinstance(v, bool): return v
    if isinstance(v, str) and v.strip().lower() in ("true","1","si"): return True
    if isinstance(v, str) and v.strip().lower() in ("false","0","no"): return False
    raise ErrorApi(400,"validacion",f"{campo} debe ser booleano.")
def evaluar_aptitud(refrigerado, danos, caducidad_vencida, cadena_frio_rota, minutos_fuera):
    motivos=[]
    if danos: motivos.append("danos fisicos visibles")
    if caducidad_vencida: motivos.append("caducidad vencida")
    if refrigerado and cadena_frio_rota: motivos.append("cadena de frio rota")
    if refrigerado and minutos_fuera is not None and minutos_fuera > 30: motivos.append("mas de 30 minutos fuera de refrigeracion")
    return not motivos, motivos

def _expediente(dev_id, bloquear=False):
    fila=consultar("""SELECT d.id,d.folio_devolucion,d.estado,p.clasificacion_temperatura,p.id AS producto_id
      FROM devoluciones d JOIN venta_detalle vd ON vd.id=d.venta_detalle_id JOIN lotes l ON l.id=vd.lote_id JOIN productos p ON p.id=l.producto_id
      WHERE d.id=%s AND d.eliminado_en IS NULL""" + (" FOR UPDATE OF d" if bloquear else ""),(dev_id,),uno=True)
    if not fila: raise ErrorApi(404,"no_encontrado",f"No existe la devolucion {dev_id}.")
    return fila

@api.post("")
@requiere_jwt(INSPECTOR)
def registrar():
    datos=leer_cuerpo(os.path.join(CONTRATOS,"inspeccion.xsd"))
    try: dev_id=int(datos.get("devolucion_id")); minutos=int(datos["minutos_fuera_refrigeracion"]) if datos.get("minutos_fuera_refrigeracion") not in (None,"") else None
    except (TypeError,ValueError): raise ErrorApi(400,"validacion","devolucion_id o minutos invalidos.")
    if dev_id < 1 or (minutos is not None and minutos < 0): raise ErrorApi(400,"validacion","devolucion_id debe ser positivo y minutos no puede ser negativo.")
    exp=_expediente(dev_id,True)
    if exp["estado"] not in ("recibida","en_inspeccion"): raise ErrorApi(409,"estado_no_permite","El producto debe estar recibido.",{"estado_actual":exp["estado"]})
    if consultar("SELECT id FROM inspecciones_ref WHERE devolucion_id=%s",(dev_id,),uno=True): raise ErrorApi(409,"inspeccion_duplicada","La devolucion ya tiene inspeccion.")
    empaque=str(datos.get("estado_empaque") or "").strip()
    if len(empaque)<3: raise ErrorApi(400,"validacion","Describe el estado del empaque.")
    refrigerado=exp["clasificacion_temperatura"]=="refrigerado"
    temperatura=datos.get("temperatura_recepcion")
    if refrigerado and (temperatura in (None,"") or minutos is None): raise ErrorApi(400,"validacion","Temperatura y minutos son obligatorios para producto refrigerado.")
    danos=_bool_estricto(datos.get("danos",False),"danos")
    caducidad=_bool_estricto(datos.get("caducidad_vencida",False),"caducidad_vencida")
    cadena=_bool_estricto(datos.get("cadena_frio_rota",False),"cadena_frio_rota")
    apto,motivos=evaluar_aptitud(refrigerado,danos,caducidad,cadena,minutos)
    doc={"devolucion_id":dev_id,"inspector_id":g.usuario["id"],"fecha":datetime.now(timezone.utc),"producto":{"clasificacion_temperatura":exp["clasificacion_temperatura"]},"condiciones":{"estado_empaque":empaque,"danos":danos,"caducidad_vencida":caducidad,"cadena_frio_rota":cadena,"minutos_fuera_refrigeracion":minutos,"temperatura_recepcion":temperatura},"observaciones":str(datos.get("observaciones") or ""),"resultado":{"apto_para_inventario":apto,"motivos":motivos}}
    col=mongo.get_mongo().inspecciones; col.create_index("devolucion_id",unique=True,name="uq_inspeccion_devolucion")
    insertado=col.insert_one(doc)
    try:
        nueva=ejecutar("""INSERT INTO inspecciones_ref(devolucion_id,inspector_id,resultado_general,mongo_doc_id,apto_para_inventario)
          VALUES(%s,%s,%s,%s,%s) RETURNING id,devolucion_id,resultado_general,mongo_doc_id,apto_para_inventario,fecha_inspeccion""",(dev_id,g.usuario["id"],("apto" if apto else "no apto: "+", ".join(motivos))[:50],str(insertado.inserted_id),apto),devolver=True)
        ejecutar("UPDATE devoluciones SET estado='en_inspeccion' WHERE id=%s",(dev_id,))
    except Exception:
        col.delete_one({"_id":insertado.inserted_id}); raise
    registrar_bitacora("inspeccion_registrada","devoluciones",dev_id,f"Resultado: {'apto' if apto else 'no apto'}; Mongo {insertado.inserted_id}")
    return responder({**nueva,"detalle":mongo.a_json(doc)},201,headers={"Location":f"/api/v1/inspecciones/{dev_id}"})

@api.get("/<int:devolucion_id>")
@requiere_jwt(INSPECTOR,ANALISTA,ENCARGADO_CENTRO)
def detalle(devolucion_id):
    ref=consultar("SELECT * FROM inspecciones_ref WHERE devolucion_id=%s",(devolucion_id,),uno=True)
    if not ref: raise ErrorApi(404,"no_encontrado",f"No existe inspeccion para la devolucion {devolucion_id}.")
    doc=mongo.get_mongo().inspecciones.find_one({"devolucion_id":devolucion_id})
    return responder({"referencia":ref,"detalle":mongo.a_json(doc) if doc else None})

@api.patch("/<int:devolucion_id>")
@requiere_jwt(INSPECTOR)
def actualizar(devolucion_id):
    datos=leer_cuerpo(os.path.join(CONTRATOS,"inspeccion_actualizacion.xsd")); ref=consultar("SELECT * FROM inspecciones_ref WHERE devolucion_id=%s FOR UPDATE",(devolucion_id,),uno=True)
    if not ref: raise ErrorApi(404,"no_encontrado",f"No existe inspeccion para la devolucion {devolucion_id}.")
    cambios={k:datos[k] for k in ("estado_empaque","observaciones") if k in datos}
    if not cambios: raise ErrorApi(400,"validacion","No hay campos actualizables.")
    set_mongo={f"condiciones.{k}":v for k,v in cambios.items() if k=="estado_empaque"}; set_mongo.update({k:v for k,v in cambios.items() if k=="observaciones"})
    mongo.get_mongo().inspecciones.update_one({"devolucion_id":devolucion_id},{"$set":set_mongo})
    registrar_bitacora("inspeccion_actualizada","devoluciones",devolucion_id,"Se actualizo el detalle semiestructurado en MongoDB")
    return detalle(devolucion_id)

@api.post("/<int:devolucion_id>/disposicion")
@requiere_jwt(ANALISTA)
def disponer(devolucion_id):
    datos=leer_cuerpo(os.path.join(CONTRATOS,"disposicion.xsd")); destino=str(datos.get("destino") or "").strip(); just=str(datos.get("justificacion") or "").strip()
    if destino not in DESTINOS: raise ErrorApi(400,"validacion","Destino invalido.")
    exp=_expediente(devolucion_id,True); insp=consultar("SELECT apto_para_inventario FROM inspecciones_ref WHERE devolucion_id=%s",(devolucion_id,),uno=True)
    if not insp: raise ErrorApi(409,"sin_inspeccion","No se decide disposicion sin inspeccion.")
    if destino=="inventario" and not insp["apto_para_inventario"]: raise ErrorApi(409,"no_apto_inventario","La inspeccion impide regresar el producto a inventario.")
    if consultar("SELECT id FROM disposiciones WHERE devolucion_id=%s",(devolucion_id,),uno=True): raise ErrorApi(409,"disposicion_duplicada","Ya existe una disposicion.")
    nueva=ejecutar("INSERT INTO disposiciones(devolucion_id,analista_id,destino,justificacion) VALUES(%s,%s,%s,%s) RETURNING *",(devolucion_id,g.usuario["id"],destino,just or None),devolver=True)
    ejecutar("UPDATE devoluciones SET estado='resuelta' WHERE id=%s",(devolucion_id,)); registrar_bitacora("disposicion_registrada","devoluciones",devolucion_id,f"Destino: {destino}")
    return responder(nueva,201)

@api.post("/inventario/<int:disposicion_id>/etiqueta")
@requiere_jwt(ENCARGADO_CENTRO)
def etiquetar(disposicion_id):
    fila=consultar("""SELECT ds.id,ds.destino,d.id AS devolucion_id,d.folio_devolucion,p.id AS producto_id FROM disposiciones ds JOIN devoluciones d ON d.id=ds.devolucion_id JOIN venta_detalle vd ON vd.id=d.venta_detalle_id JOIN lotes l ON l.id=vd.lote_id JOIN productos p ON p.id=l.producto_id WHERE ds.id=%s""",(disposicion_id,),uno=True)
    if not fila: raise ErrorApi(404,"no_encontrado",f"No existe la disposicion {disposicion_id}.")
    if fila["destino"]!="inventario": raise ErrorApi(409,"destino_no_etiquetable","Solo se etiqueta destino inventario.")
    etiqueta=f"REC-{fila['folio_devolucion'].replace('DEV-','')}"
    nueva=ejecutar("INSERT INTO inventario_recuperado(disposicion_id,producto_id,etiqueta_codigo) VALUES(%s,%s,%s) ON CONFLICT(disposicion_id) DO UPDATE SET disposicion_id=EXCLUDED.disposicion_id RETURNING *",(disposicion_id,fila["producto_id"],etiqueta),devolver=True)
    registrar_bitacora("inventario_recuperado","devoluciones",fila["devolucion_id"],f"Etiqueta {etiqueta}"); return responder(nueva,201)

def create_app():
    app=Flask(__name__); app.json.sort_keys=False; respuestas.registrar(app,NOMBRE); app.teardown_appcontext(cerrar_conexion); app.register_blueprint(api); docs.registrar(app,os.path.join(os.path.dirname(__file__),"openapi.yaml"))
    @app.get("/health")
    def health():
        deps={"postgresql":salud_postgres(),"redis":salud_redis(),"mongodb":mongo.salud_mongo()}; ok=all(x["ok"] for x in deps.values()); return responder({"servicio":NOMBRE,"version":"v1","estado":"ok" if ok else "degradado","dependencias":deps},200 if ok else 503)
    return app
