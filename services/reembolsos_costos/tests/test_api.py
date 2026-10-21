import os, time, unittest, uuid
from decimal import Decimal
import jwt
os.environ.setdefault("JWT_SECRET","x"*48)
import app as servicio
from shared import seguridad

class RedisFalso:
    def __init__(self): self.datos={}
    def exists(self,k): return int(k in self.datos)
    def set(self,k,v,nx=False,ex=None):
        if nx and k in self.datos: return None
        self.datos[k]=v; return True
    def eval(self,script,n,k,v):
        if self.datos.get(k)==v: del self.datos[k]

class PruebaReembolsos(unittest.TestCase):
    def setUp(self):
        self.r=RedisFalso(); self.original=seguridad.get_redis; seguridad.get_redis=lambda:self.r
        self.cliente=servicio.create_app().test_client()
    def tearDown(self): seguridad.get_redis=self.original
    def token(self,rol):
        sid=uuid.uuid4().hex; self.r.datos[seguridad.clave_sesion(sid)]="1"; ahora=int(time.time())
        return jwt.encode({"iss":seguridad.EMISOR,"sub":"7","rol":rol,"nombre":"Prueba","sid":sid,"jti":uuid.uuid4().hex,"typ":"access","iat":ahora,"exp":ahora+600},os.environ["JWT_SECRET"],algorithm="HS256")
    def test_sin_token(self): self.assertEqual(self.cliente.get("/api/v1/reembolsos-costos/reembolsos").status_code,401)
    def test_analista_no_resuelve_reembolso(self):
        r=self.cliente.post("/api/v1/reembolsos-costos/reembolsos",headers={"Authorization":"Bearer "+self.token(seguridad.ANALISTA)},json={})
        self.assertEqual(r.status_code,403)
    def test_monto_negativo(self):
        r=self.cliente.post("/api/v1/reembolsos-costos/reembolsos",headers={"Authorization":"Bearer "+self.token(seguridad.ENCARGADO_REEMBOLSOS)},json={"devolucion_id":1,"monto":-1,"estado":"aprobado","metodo":"tarjeta"})
        self.assertEqual(r.status_code,400)
    def test_montos_no_finitos(self):
        for valor in ("NaN","Infinity","-Infinity"):
            with self.subTest(valor=valor):
                with self.assertRaises(servicio.ErrorApi):
                    servicio._decimal({"monto":valor},"monto")
    def test_xml_invalido(self):
        r=self.cliente.post("/api/v1/reembolsos-costos/costos",headers={"Authorization":"Bearer "+self.token(seguridad.ANALISTA),"Content-Type":"application/xml","Accept":"application/xml"},data="<costo><devolucion_id>1</devolucion_id><etapa>inventada</etapa><monto>1</monto></costo>")
        self.assertEqual(r.status_code,400); self.assertIn(b"xml_no_cumple_xsd",r.data)
    def _reembolso(self,monto,valor=Decimal("227.17")):
        # Postgres entrega el valor devuelto como Decimal; el doble reproduce eso sin base (RN-04).
        dev={"id":5,"folio_devolucion":"DEV-2026-5","estado":"autorizada","fecha_cierre":None,"valor_devuelto":valor,"cliente_id":3}
        def consultar(sql,params=None,uno=False): return dev if "FROM devoluciones" in sql else None
        def ejecutar(sql,params=None,devolver=False): return {"id":1,"devolucion_id":5,"monto":params[2],"metodo":"tarjeta","estado":"aprobado","fecha_resolucion":None} if devolver else None
        originales=(servicio.consultar,servicio.ejecutar,servicio.registrar_bitacora,servicio.get_redis)
        servicio.consultar,servicio.ejecutar,servicio.registrar_bitacora,servicio.get_redis=consultar,ejecutar,lambda *a,**k:None,lambda:self.r
        try:
            return self.cliente.post("/api/v1/reembolsos-costos/reembolsos",headers={"Authorization":"Bearer "+self.token(seguridad.ENCARGADO_REEMBOLSOS)},json={"devolucion_id":5,"monto":monto,"estado":"aprobado","metodo":"tarjeta"})
        finally: servicio.consultar,servicio.ejecutar,servicio.registrar_bitacora,servicio.get_redis=originales
    def test_reembolso_por_el_monto_maximo_exacto_se_acepta(self):
        # Regresion H-11: Decimal("227.17") > float(227.17) era True y se rechazaba el maximo.
        self.assertEqual(self._reembolso(227.17).status_code,201)
    def test_reembolso_un_centavo_arriba_del_maximo_se_rechaza(self):
        r=self._reembolso(227.18)
        self.assertEqual(r.status_code,409); detalle=r.get_json()["error"]
        self.assertEqual(detalle["tipo"],"monto_excedido"); self.assertEqual(detalle["detalles"]["maximo"],227.17)
    def test_etapas_separadas_por_responsabilidad(self):
        self.assertEqual(servicio.ETAPAS_POR_ROL[seguridad.COORDINADOR],{"transporte"})
        self.assertNotIn("reembolso",servicio.ETAPAS_POR_ROL[seguridad.ANALISTA])

if __name__=="__main__": unittest.main()
