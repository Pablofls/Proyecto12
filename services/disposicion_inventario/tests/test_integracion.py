"""Integracion real: auth + PostgreSQL + servicio 8014. Solo corre en la VM."""
import json
import os
import unittest
import urllib.error
import urllib.request

import psycopg2
import psycopg2.extras

AUTH_URL = os.environ.get("AUTH_URL", "http://auth:8000")
URL = os.environ.get("DISPOSICION_URL", "http://disposicion-inventario:8000")
PREFIJO = "/api/v1/disposicion-inventario"


def sql(sentencia, params=(), uno=False):
    conexion = psycopg2.connect(host=os.environ.get("POSTGRES_HOST", "postgres"),
        dbname=os.environ.get("POSTGRES_DB", "devoluciones"),
        user=os.environ.get("POSTGRES_USER", "devoluciones_app"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
        cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        with conexion, conexion.cursor() as cursor:
            cursor.execute(sentencia, params)
            return (cursor.fetchone() if uno else cursor.fetchall()) if cursor.description else None
    finally: conexion.close()


def http(base, metodo, ruta, cuerpo=None, token=None, extras=None):
    headers={"Content-Type":"application/json","Accept":"application/json",**(extras or {})}
    if token: headers["Authorization"]="Bearer "+token
    req=urllib.request.Request(base+ruta,method=metodo,headers=headers,
        data=json.dumps(cuerpo).encode() if cuerpo is not None else None)
    try:
        with urllib.request.urlopen(req,timeout=15) as resp:
            return resp.status,json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as exc:
        return exc.code,json.loads(exc.read() or b"null")


def login(rol):
    usuario=sql("""SELECT u.email FROM usuarios u JOIN roles r ON r.id=u.rol_id
        WHERE r.nombre=%s AND u.estado='activo' AND u.eliminado_en IS NULL
        ORDER BY u.id LIMIT 1""",(rol,),uno=True)
    if not usuario: raise unittest.SkipTest(f"Falta usuario {rol}")
    codigo,cuerpo=http(AUTH_URL,"POST","/api/v1/auth/login",
        {"email":usuario["email"],"password":os.environ["PASSWORD_DEMO"]})
    if codigo != 200: raise AssertionError(cuerpo)
    return cuerpo["access_token"]


def permiso(token, operacion, recurso):
    codigo,cuerpo=http(AUTH_URL,"POST","/api/v1/auth/autorizar-operacion",
        {"operacion":operacion,"recurso_id":str(recurso),
         "password":os.environ["PASSWORD_DEMO"]},token)
    if codigo != 201: raise AssertionError(cuerpo)
    return {"X-Autorizacion-Operacion":cuerpo["token_operacion"]}


def sembrar():
    linea=sql("""SELECT vd.id FROM venta_detalle vd JOIN ventas v ON v.id=vd.venta_id
        WHERE v.eliminado_en IS NULL AND vd.cantidad > COALESCE((SELECT SUM(d.cantidad_devuelta)
        FROM devoluciones d WHERE d.venta_detalle_id=vd.id AND d.eliminado_en IS NULL),0)
        ORDER BY vd.id LIMIT 1""",uno=True)
    inspector=sql("""SELECT u.id FROM usuarios u JOIN roles r ON r.id=u.rol_id
        WHERE r.nombre='Inspector' ORDER BY u.id LIMIT 1""",uno=True)
    if not linea or not inspector: raise unittest.SkipTest("Faltan datos seed")
    motivo=sql("SELECT id FROM motivos WHERE activo ORDER BY id LIMIT 1",uno=True)
    dev=sql("""INSERT INTO devoluciones(venta_detalle_id,motivo_id,descripcion_problema,
        cantidad_devuelta,estado) VALUES(%s,%s,'Integracion disposicion',1,'en_inspeccion')
        RETURNING id""",(linea["id"],motivo["id"]),uno=True)
    sql("""INSERT INTO inspecciones_ref(devolucion_id,inspector_id,resultado_general,
        apto_para_inventario,estado_dictamen,recomendacion)
        VALUES(%s,%s,'apto',TRUE,'concluido','reintegrar')""",(dev["id"],inspector["id"]))
    return dev["id"]


SKIP=unittest.skipUnless(os.environ.get("INTEGRACION")=="1","Solo VM con INTEGRACION=1")


@SKIP
class IntegracionDisposicion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analista=login("Analista de Devoluciones")
        cls.centro=login("Encargado del Centro de Devoluciones")
        cls.ids=[]

    @classmethod
    def tearDownClass(cls):
        for dev in cls.ids:
            sql("DELETE FROM inventario_recuperado WHERE disposicion_id IN (SELECT id FROM disposiciones WHERE devolucion_id=%s)",(dev,))
            sql("DELETE FROM disposiciones WHERE devolucion_id=%s",(dev,))
            sql("DELETE FROM inspecciones_ref WHERE devolucion_id=%s",(dev,))
            sql("DELETE FROM devoluciones WHERE id=%s",(dev,))

    def test_reintegro_pasa_por_autorizacion_y_cuarentena(self):
        dev=sembrar(); self.ids.append(dev)
        cuerpo={"devolucion_id":dev,"destino":"reintegrar",
                "justificacion":"Dictamen tecnico favorable y empaque integro"}
        codigo,error=http(URL,"POST",PREFIJO+"/disposiciones",cuerpo,self.analista)
        self.assertEqual(codigo,403); self.assertEqual(error["error"]["tipo"],"autorizacion_operacion_requerida")
        codigo,disp=http(URL,"POST",PREFIJO+"/disposiciones",cuerpo,self.analista,
                         permiso(self.analista,"aprobar_disposicion",dev))
        self.assertEqual(codigo,201,disp)
        codigo,inv=http(URL,"POST",f"{PREFIJO}/inventario/{disp['id']}/cuarentena",
                        {"ubicacion":"CUARENTENA-A-01"},self.centro)
        self.assertEqual(codigo,201,inv); self.assertEqual(inv["estado"],"cuarentena")
        codigo,_=http(URL,"POST",f"{PREFIJO}/inventario/{inv['id']}/reincorporar",{},self.centro)
        self.assertEqual(codigo,403)
        codigo,disponible=http(URL,"POST",f"{PREFIJO}/inventario/{inv['id']}/reincorporar",{},
            self.centro,permiso(self.centro,"reincorporar_inventario",inv["id"]))
        self.assertEqual(codigo,200,disponible); self.assertEqual(disponible["estado"],"disponible")


if __name__ == "__main__": unittest.main()
