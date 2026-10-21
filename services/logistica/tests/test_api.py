import os, time, unittest, uuid
import jwt
os.environ.setdefault("JWT_SECRET","x"*48)
import app as servicio
from shared import seguridad

class RedisFalso:
    def __init__(self): self.datos={}
    def exists(self,k): return int(k in self.datos)

class PruebaLogistica(unittest.TestCase):
    def setUp(self):
        self.r=RedisFalso(); self.original=seguridad.get_redis; seguridad.get_redis=lambda:self.r
        self.cliente=servicio.create_app().test_client()
    def tearDown(self): seguridad.get_redis=self.original
    def token(self,rol):
        sid=uuid.uuid4().hex; self.r.datos[seguridad.clave_sesion(sid)]="1"; ahora=int(time.time())
        return jwt.encode({"iss":seguridad.EMISOR,"sub":"7","rol":rol,"nombre":"Prueba","sid":sid,"jti":uuid.uuid4().hex,"typ":"access","iat":ahora,"exp":ahora+600},os.environ["JWT_SECRET"],algorithm="HS256")
    def test_sin_token(self): self.assertEqual(self.cliente.get("/api/v1/logistica/recolecciones").status_code,401)
    def test_inspector_no_programa(self):
        r=self.cliente.post("/api/v1/logistica/recolecciones",headers={"Authorization":"Bearer "+self.token(seguridad.INSPECTOR)},json={})
        self.assertEqual(r.status_code,403)
    def test_xml_invalido(self):
        r=self.cliente.post("/api/v1/logistica/recolecciones",headers={"Authorization":"Bearer "+self.token(seguridad.COORDINADOR),"Content-Type":"application/xml","Accept":"application/xml"},data="<recoleccion><devolucion_id>0</devolucion_id></recoleccion>")
        self.assertEqual(r.status_code,400); self.assertIn(b"xml_no_cumple_xsd",r.data)
    def test_fecha_invalida_se_rechaza_antes_de_bd(self):
        with self.assertRaises(servicio.ErrorApi) as error:
            servicio._fecha_programada("31/12/2026")
        self.assertEqual(error.exception.codigo,400)
    def test_booleano_invalido_no_se_convierte_a_false(self):
        with self.assertRaises(servicio.ErrorApi):
            servicio._booleano_estricto("tal vez","coincide_expediente")

if __name__=="__main__": unittest.main()
