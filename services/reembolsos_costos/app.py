"""Microservicio de reembolsos y costos (RF-20, RF-21, RF-27, RN-03, RN-04)."""
import os, uuid
from decimal import Decimal, InvalidOperation
import psycopg2
from flask import Blueprint, Flask, g, request
from shared import docs, respuestas
from shared.infra import PREFIJO, cerrar_conexion, consultar, ejecutar, get_redis, registrar_bitacora, salud_postgres, salud_redis
from shared.respuestas import ErrorApi, leer_cuerpo, responder
from shared.seguridad import (ANALISTA, COORDINADOR, ENCARGADO_CENTRO,
                              ENCARGADO_REEMBOLSOS, INSPECTOR, requiere_jwt)

NOMBRE="reembolsos-costos"; CONTRATOS=os.path.join(os.path.dirname(__file__),"contratos")
api=Blueprint("reembolsos_costos",__name__,url_prefix="/api/v1/reembolsos-costos")
METODOS={"transferencia","tarjeta","efectivo","vale"}; ESTADOS={"aprobado","rechazado"}
ETAPAS={"transporte","inspeccion","almacenamiento","reacondicionamiento","destruccion","reembolso","otros"}
ETAPAS_POR_ROL={
    COORDINADOR:{"transporte"},
    ENCARGADO_CENTRO:{"almacenamiento"},
    INSPECTOR:{"inspeccion"},
    ANALISTA:{"reacondicionamiento","destruccion","otros"},
    ENCARGADO_REEMBOLSOS:{"reembolso"},
}

def _decimal(datos,campo):
    try: valor=Decimal(str(datos.get(campo))).quantize(Decimal("0.01"))
    except (InvalidOperation, TypeError, ValueError): valor=Decimal("-1")
    if not valor.is_finite() or valor<0: raise ErrorApi(400,"validacion",f"{campo} debe ser un monto decimal finito no negativo.")
    return valor
def _devolucion(dev_id,bloquear=False):
    fila=consultar("""SELECT d.id,d.folio_devolucion,d.estado,d.fecha_cierre,vd.precio_unitario*d.cantidad_devuelta AS valor_devuelto,v.cliente_id
      FROM devoluciones d JOIN venta_detalle vd ON vd.id=d.venta_detalle_id JOIN ventas v ON v.id=vd.venta_id
      WHERE d.id=%s AND d.eliminado_en IS NULL"""+(" FOR UPDATE OF d" if bloquear else ""),(dev_id,),uno=True)
    if not fila: raise ErrorApi(404,"no_encontrado",f"No existe la devolucion {dev_id}.")
    return fila

@api.post("/reembolsos")
@requiere_jwt(ENCARGADO_REEMBOLSOS)
def registrar_reembolso():
    datos=leer_cuerpo(os.path.join(CONTRATOS,"reembolso.xsd"))
    try: dev_id=int(datos.get("devolucion_id"))
    except (TypeError,ValueError): raise ErrorApi(400,"validacion","devolucion_id debe ser entero.")
    if dev_id < 1: raise ErrorApi(400,"validacion","devolucion_id debe ser entero positivo.")
    decision=str(datos.get("estado") or "").strip(); metodo=str(datos.get("metodo") or "").strip(); monto=_decimal(datos,"monto")
    if decision not in ESTADOS: raise ErrorApi(400,"validacion","estado debe ser aprobado o rechazado.")
    if decision=="aprobado" and metodo not in METODOS: raise ErrorApi(400,"validacion","Metodo de reembolso invalido.")
    if decision=="rechazado": monto,metodo=0,None
    llave=f"{PREFIJO}lock:reembolso:{dev_id}"; valor=uuid.uuid4().hex; r=get_redis()
    if not r.set(llave,valor,nx=True,ex=30): raise ErrorApi(409,"reembolso_en_proceso","Otro proceso esta resolviendo este reembolso.")
    try:
        dev=_devolucion(dev_id,True)
        if dev["estado"] in ("solicitada","en_revision","rechazada"): raise ErrorApi(409,"estado_no_permite","La devolucion debe estar autorizada.")
        if monto>float(dev["valor_devuelto"]): raise ErrorApi(409,"monto_excedido","El reembolso excede el valor devuelto.",{"maximo":float(dev["valor_devuelto"])})
        if consultar("SELECT id FROM reembolsos WHERE devolucion_id=%s AND eliminado_en IS NULL",(dev_id,),uno=True): raise ErrorApi(409,"reembolso_duplicado","La devolucion ya tiene un reembolso valido.")
        nuevo=ejecutar("""INSERT INTO reembolsos(devolucion_id,encargado_id,monto,metodo,estado,fecha_resolucion)
          VALUES(%s,%s,%s,%s,%s,CURRENT_TIMESTAMP) RETURNING id,devolucion_id,monto,metodo,estado,fecha_resolucion""",(dev_id,g.usuario["id"],monto,metodo,decision),devolver=True)
        if decision=="aprobado": ejecutar("INSERT INTO costos(devolucion_id,etapa,monto) VALUES(%s,'reembolso',%s)",(dev_id,monto))
        if dev["estado"]=="resuelta": ejecutar("UPDATE devoluciones SET estado='cerrada',fecha_cierre=CURRENT_TIMESTAMP WHERE id=%s",(dev_id,))
        ejecutar("INSERT INTO notificaciones(usuario_id,devolucion_id,tipo,mensaje) VALUES(%s,%s,%s,%s)",(dev["cliente_id"],dev_id,"reembolso_"+decision,f"El reembolso de {dev['folio_devolucion']} fue {decision}."))
        registrar_bitacora("reembolso_"+decision,"devoluciones",dev_id,f"Monto {monto}; metodo {metodo or 'no aplica'}")
        return responder(nuevo,201,headers={"Location":f"/api/v1/reembolsos-costos/reembolsos/{nuevo['id']}"})
    finally:
        # Liberacion con compare-and-delete para no borrar el lock de otro proceso.
        r.eval("if redis.call('get',KEYS[1])==ARGV[1] then return redis.call('del',KEYS[1]) else return 0 end",1,llave,valor)

@api.get("/reembolsos")
@requiere_jwt(ENCARGADO_REEMBOLSOS,ANALISTA)
def listar_reembolsos():
    return responder({"datos":consultar("""SELECT rb.id,rb.devolucion_id,rb.monto,rb.metodo,rb.estado,rb.fecha_resolucion,d.folio_devolucion,u.nombre AS encargado
      FROM reembolsos rb JOIN devoluciones d ON d.id=rb.devolucion_id JOIN usuarios u ON u.id=rb.encargado_id WHERE rb.eliminado_en IS NULL ORDER BY rb.id DESC LIMIT 100""")})

@api.post("/costos")
@requiere_jwt(COORDINADOR,ENCARGADO_CENTRO,INSPECTOR,ANALISTA,ENCARGADO_REEMBOLSOS)
def registrar_costo():
    datos=leer_cuerpo(os.path.join(CONTRATOS,"costo.xsd"))
    try: dev_id=int(datos.get("devolucion_id"))
    except (TypeError,ValueError): raise ErrorApi(400,"validacion","devolucion_id debe ser entero.")
    if dev_id < 1: raise ErrorApi(400,"validacion","devolucion_id debe ser entero positivo.")
    etapa=str(datos.get("etapa") or "").strip(); monto=_decimal(datos,"monto")
    if etapa not in ETAPAS: raise ErrorApi(400,"validacion","Etapa de costo invalida.")
    if etapa not in ETAPAS_POR_ROL.get(g.usuario["rol"],set()):
        raise ErrorApi(403,"sin_permiso","Tu rol no puede registrar costos de esta etapa.")
    _devolucion(dev_id)
    nuevo=ejecutar("INSERT INTO costos(devolucion_id,etapa,monto) VALUES(%s,%s,%s) RETURNING id,devolucion_id,etapa,monto,fecha",(dev_id,etapa,monto),devolver=True)
    registrar_bitacora("costo_registrado","devoluciones",dev_id,f"{etapa}: {monto}"); return responder(nuevo,201)

@api.get("/costos/<int:devolucion_id>")
@requiere_jwt(ENCARGADO_REEMBOLSOS,ANALISTA)
def costos(devolucion_id):
    _devolucion(devolucion_id); desglose=consultar("SELECT etapa,SUM(monto) AS subtotal FROM costos WHERE devolucion_id=%s GROUP BY etapa ORDER BY etapa",(devolucion_id,)); total=sum(float(x["subtotal"]) for x in desglose)
    return responder({"devolucion_id":devolucion_id,"desglose":desglose,"costo_total":total})

def create_app():
    app=Flask(__name__); app.json.sort_keys=False; respuestas.registrar(app,NOMBRE); app.teardown_appcontext(cerrar_conexion); app.register_blueprint(api); docs.registrar(app,os.path.join(os.path.dirname(__file__),"openapi.yaml"))
    @app.get("/health")
    def health():
        deps={"postgresql":salud_postgres(),"redis":salud_redis()}; ok=all(x["ok"] for x in deps.values()); return responder({"servicio":NOMBRE,"version":"v1","estado":"ok" if ok else "degradado","dependencias":deps},200 if ok else 503)
    return app
