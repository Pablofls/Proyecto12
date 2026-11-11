"""Integracion real de la sincronizacion offline sobre PostgreSQL.

Sin dobles: el token sale del servicio auth real, la peticion va al contenedor
de sincronizacion y el efecto se verifica en PostgreSQL y en el volumen de
evidencias. Cubre la prueba del profesor "se captura un evento permitido offline
y se sincroniza sin duplicaciones". Las filas que crea se borran al terminar.
Solo corre en la VM:

    docker compose run --rm -e INTEGRACION=1 sincronizacion python -m pytest -v tests/test_integracion.py

Trazabilidad: RNF-28, RF-09, RF-12 a RF-15, dominio 20.
"""
import base64
import hashlib
import json
import os
import threading
import unittest
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path

import psycopg2
import psycopg2.extras

AUTH_URL = os.environ.get("AUTH_URL", "http://auth:8000")
SERVICIO_URL = os.environ.get("SINCRONIZACION_URL", "http://sincronizacion:8000")
PREFIJO = "/api/v1/sincronizacion"
RECOLECTOR = "luis.recolector@demo.mx"
ALMACEN = "marta.almacen@demo.mx"
DIR = Path(os.environ.get("EVIDENCIAS_DIR", "/srv/evidencias_privadas"))
PNG = b"\x89PNG\r\n\x1a\n" + b"prueba de foto capturada sin conexion" * 20


def _sql(sentencia, params=(), uno=False):
    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "postgres"),
        dbname=os.environ.get("POSTGRES_DB", "devoluciones"),
        user=os.environ.get("POSTGRES_USER", "devoluciones_app"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
        cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        with conn, conn.cursor() as cur:
            cur.execute(sentencia, params)
            if cur.description is None:
                return None
            return cur.fetchone() if uno else cur.fetchall()
    finally:
        conn.close()


def _http(metodo, ruta, cuerpo=None, token=None, base=SERVICIO_URL, xml=None):
    cabeceras = {"Content-Type": "application/xml" if xml else "application/json",
                 "Accept": "application/xml" if xml else "application/json"}
    if token:
        cabeceras["Authorization"] = f"Bearer {token}"
    datos = xml.encode() if xml else (json.dumps(cuerpo).encode() if cuerpo is not None else None)
    peticion = urllib.request.Request(base + ruta, method=metodo, headers=cabeceras, data=datos)
    try:
        with urllib.request.urlopen(peticion, timeout=20) as resp:
            crudo = resp.read()
            return resp.status, (crudo if xml else json.loads(crudo or b"null"))
    except urllib.error.HTTPError as exc:
        crudo = exc.read()
        try:
            return exc.code, json.loads(crudo)
        except ValueError:
            return exc.code, crudo


def _login(email):
    codigo, cuerpo = _http("POST", "/api/v1/auth/login",
                           {"email": email, "password": os.environ["PASSWORD_DEMO"]}, base=AUTH_URL)
    if codigo != 200:
        raise unittest.SkipTest(f"login de {email} respondio {codigo} (corre seed_demo)")
    return cuerpo["access_token"]


def _tienda(email):
    fila = _sql("SELECT tienda_id FROM usuarios WHERE email = %s", (email,), uno=True)
    return fila["tienda_id"] if fila else None


def _linea(tienda_id, misma=True):
    fila = _sql(f"""
        SELECT vd.id FROM venta_detalle vd JOIN ventas v ON v.id = vd.venta_id
         WHERE v.eliminado_en IS NULL AND v.tienda_id {'=' if misma else '<>'} %s
         ORDER BY vd.id LIMIT 1""", (tienda_id,), uno=True)
    if not fila:
        raise unittest.SkipTest("No hay una linea de venta de esa sucursal")
    return fila["id"]


def _ahora(menos_minutos=0):
    return (datetime.now(timezone.utc) - timedelta(minutes=menos_minutos)).isoformat()


def _op(tipo, datos, menos_minutos=30):
    return {"id_operacion": str(uuid.uuid4()), "tipo": tipo,
            "capturado_en": _ahora(menos_minutos), "datos": datos}


SKIP = unittest.skipUnless(os.environ.get("INTEGRACION") == "1",
                           "Solo en la VM: INTEGRACION=1 y el entorno levantado")


@SKIP
class IntegracionSincronizacion(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tienda = _tienda(RECOLECTOR)
        if cls.tienda is None:
            raise unittest.SkipTest("luis.recolector no tiene sucursal (corre seed_demo)")
        cls.recolector = _login(RECOLECTOR)
        cls.almacen = _login(ALMACEN)
        cls.devoluciones, cls.operaciones, cls.objetos = [], [], []

    @classmethod
    def tearDownClass(cls):
        for objeto in cls.objetos:
            (DIR / objeto).unlink(missing_ok=True)
        if cls.operaciones:
            _sql("DELETE FROM operaciones_offline WHERE id_operacion::text IN %s", (tuple(cls.operaciones),))
        if cls.devoluciones:
            ids = tuple(cls.devoluciones)
            for paso in ("DELETE FROM operaciones_offline WHERE devolucion_id IN %s",
                         "DELETE FROM evidencias WHERE devolucion_id IN %s",
                         "DELETE FROM recepciones WHERE devolucion_id IN %s",
                         "DELETE FROM recolecciones WHERE devolucion_id IN %s",
                         "DELETE FROM devoluciones WHERE id IN %s"):
                _sql(paso, (ids,))
        for token in (getattr(cls, "recolector", None), getattr(cls, "almacen", None)):
            if token:
                _http("POST", "/api/v1/auth/logout", token=token, base=AUTH_URL)

    # ------------------------------------------------------------------ #
    def _caso(self, estado_recoleccion="asignada", misma_sucursal=True):
        """Devolucion en recoleccion con su recoleccion, sembradas por SQL."""
        motivo = _sql("SELECT id FROM motivos WHERE activo ORDER BY id LIMIT 1", uno=True)["id"]
        dev = _sql("""INSERT INTO devoluciones (venta_detalle_id, motivo_id, descripcion_problema,
                                                cantidad_devuelta, estado)
                      VALUES (%s, %s, 'Prueba de sincronizacion offline.', 1, 'en_recoleccion')
                      RETURNING id""", (_linea(self.tienda, misma_sucursal), motivo), uno=True)["id"]
        self.devoluciones.append(dev)
        rec = _sql("""INSERT INTO recolecciones (devolucion_id, fecha_programada, lugar, estado)
                      VALUES (%s, CURRENT_DATE, 'Prueba', %s) RETURNING id""",
                   (dev, estado_recoleccion), uno=True)["id"]
        return dev, rec

    def _enviar(self, operaciones, token=None, dispositivo="tel-prueba-1"):
        for op in operaciones:
            self.operaciones.append(op["id_operacion"])
        codigo, cuerpo = _http("POST", PREFIJO + "/operaciones",
                               {"dispositivo_id": dispositivo, "operaciones": operaciones},
                               token=token or self.recolector)
        self.assertEqual(codigo, 200, cuerpo)
        for r in cuerpo["resultados"]:
            objeto = None
            if r.get("tipo") == "evidencia" and r["estado"] == "aceptada":
                objeto = _sql("SELECT objeto FROM evidencias WHERE id = %s",
                              (r["respuesta"]["evidencia_id"],), uno=True)["objeto"]
            if objeto:
                self.objetos.append(objeto)
        return cuerpo

    # ------------------------------------------------------------------ #
    def test_1_captura_offline_se_aplica_y_un_reintento_no_duplica(self):
        dev, rec = self._caso()
        lote = [
            _op("estado_recoleccion", {"recoleccion_id": rec, "estado_esperado": "asignada",
                                       "estado": "en_transito",
                                       "ubicacion": {"latitud": 25.6866, "longitud": -100.3161}}, 40),
            _op("evidencia", {"devolucion_id": dev, "comentario": "Caja abollada al recoger."}, 35),
            _op("estado_recoleccion", {"recoleccion_id": rec, "estado_esperado": "en_transito",
                                       "estado": "completada"}, 30),
        ]
        primero = self._enviar(lote)
        self.assertEqual(primero["resumen"]["aceptada"], 3, primero)
        self.assertEqual(primero["repetidas"], 0)
        self.assertEqual(_sql("SELECT estado FROM recolecciones WHERE id = %s", (rec,), uno=True)["estado"],
                         "completada")
        # La respuesta se perdio y la app manda TODO otra vez: nada se duplica.
        segundo = self._enviar(lote)
        self.assertEqual(segundo["repetidas"], 3)
        self.assertEqual([r["estado"] for r in segundo["resultados"]], ["aceptada"] * 3)
        self.assertEqual(segundo["resultados"][1]["respuesta"], primero["resultados"][1]["respuesta"])
        self.assertEqual(_sql("SELECT count(*) AS n FROM evidencias WHERE devolucion_id = %s",
                              (dev,), uno=True)["n"], 1)
        envios = _sql("SELECT envios FROM operaciones_offline WHERE id_operacion = %s",
                      (lote[1]["id_operacion"],), uno=True)["envios"]
        self.assertEqual(envios, 2)

    def test_2_mismo_id_con_otros_datos_se_rechaza(self):
        dev, _ = self._caso()
        op = _op("evidencia", {"devolucion_id": dev, "comentario": "Primera version."})
        self.assertEqual(self._enviar([op])["resultados"][0]["estado"], "aceptada")
        alterada = dict(op, datos={"devolucion_id": dev, "comentario": "Otra cosa."})
        r = self._enviar([alterada])["resultados"][0]
        self.assertEqual((r["estado"], r["motivo"]["tipo"]), ("rechazada", "id_reutilizado"))
        self.assertEqual(_sql("SELECT count(*) AS n FROM evidencias WHERE devolucion_id = %s",
                              (dev,), uno=True)["n"], 1)

    def test_3_dos_envios_simultaneos_del_mismo_id_aplican_una_vez(self):
        dev, _ = self._caso()
        op = _op("evidencia", {"devolucion_id": dev, "comentario": "Doble toque en el boton."})
        respuestas = []

        def enviar():
            respuestas.append(_http("POST", PREFIJO + "/operaciones",
                                    {"dispositivo_id": "tel-prueba-1", "operaciones": [op]},
                                    token=self.recolector))
        hilos = [threading.Thread(target=enviar) for _ in range(2)]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join()
        self.operaciones.append(op["id_operacion"])
        self.assertEqual([c for c, _ in respuestas], [200, 200])
        repetidas = sorted(c["resultados"][0]["repetida"] for _, c in respuestas)
        self.assertEqual(repetidas, [False, True])
        fila = _sql("SELECT objeto FROM evidencias WHERE devolucion_id = %s", (dev,))
        self.assertEqual(len(fila), 1)

    def test_4_conflicto_si_el_servidor_cambio(self):
        dev, rec = self._caso()
        # Mientras el celular estaba sin red, el coordinador la marco fallida.
        _sql("UPDATE recolecciones SET estado = 'fallida' WHERE id = %s", (rec,))
        op = _op("estado_recoleccion", {"recoleccion_id": rec, "estado_esperado": "asignada",
                                        "estado": "en_transito"})
        r = self._enviar([op])["resultados"][0]
        self.assertEqual(r["estado"], "conflicto", r)
        self.assertEqual(r["motivo"]["detalles"]["estado_servidor"], "fallida")
        self.assertEqual(_sql("SELECT estado FROM recolecciones WHERE id = %s", (rec,), uno=True)["estado"],
                         "fallida")
        otra = self._enviar([op])["resultados"][0]
        self.assertEqual((otra["estado"], otra["repetida"]), ("conflicto", True))

    def test_5_recepcion_y_foto_con_integridad(self):
        dev, _ = self._caso(estado_recoleccion="completada")
        capturada = _ahora(90)
        recepcion = {"id_operacion": str(uuid.uuid4()), "tipo": "recepcion", "capturado_en": capturada,
                     "datos": {"devolucion_id": dev, "coincide_expediente": True}}
        foto = {"nombre": "caja.png", "contenido_base64": base64.b64encode(PNG).decode(),
                "sha256": hashlib.sha256(PNG).hexdigest()}
        buena = _op("evidencia", {"devolucion_id": dev, "archivo": foto}, 85)
        mala = _op("evidencia", {"devolucion_id": dev, "archivo": dict(foto, sha256="0" * 64)}, 80)
        cuerpo = self._enviar([recepcion, buena, mala], token=self.almacen, dispositivo="tablet-almacen")
        estados = [r["estado"] for r in cuerpo["resultados"]]
        self.assertEqual(estados, ["aceptada", "aceptada", "rechazada"], cuerpo)
        self.assertEqual(cuerpo["resultados"][2]["motivo"]["tipo"], "archivo_corrupto")
        fila = _sql("SELECT fecha_recepcion FROM recepciones WHERE devolucion_id = %s", (dev,), uno=True)
        self.assertEqual(fila["fecha_recepcion"], datetime.fromisoformat(capturada))
        self.assertEqual(_sql("SELECT estado FROM devoluciones WHERE id = %s", (dev,), uno=True)["estado"],
                         "recibida")
        evidencia = _sql("SELECT etapa, tipo, objeto FROM evidencias WHERE devolucion_id = %s", (dev,))
        self.assertEqual(len(evidencia), 1)
        self.assertEqual((evidencia[0]["etapa"], evidencia[0]["tipo"]), ("recepcion", "fotografia"))
        self.assertEqual((DIR / evidencia[0]["objeto"]).read_bytes(), PNG)

    def test_6_lo_que_no_se_permite_offline(self):
        dev, rec = self._caso()
        ops = [
            _op("aprobar_reembolso", {"devolucion_id": dev}),
            _op("recepcion", {"devolucion_id": dev}),  # el recolector no recibe
            _op("estado_recoleccion", {"recoleccion_id": rec, "estado_esperado": "asignada",
                                       "estado": "en_transito"}, 60 * 24 * 8),  # 8 dias
        ]
        r = self._enviar(ops)["resultados"]
        self.assertEqual([x["motivo"]["tipo"] for x in r],
                         ["requiere_conexion", "sin_permiso", "captura_invalida"])
        self.assertEqual({x["estado"] for x in r}, {"rechazada"})
        self.assertEqual(_sql("SELECT estado FROM recolecciones WHERE id = %s", (rec,), uno=True)["estado"],
                         "asignada")

    def test_7_otra_sucursal_se_rechaza(self):
        dev, rec = self._caso(misma_sucursal=False)
        r = self._enviar([_op("estado_recoleccion", {"recoleccion_id": rec, "estado_esperado": "asignada",
                                                     "estado": "en_transito"})])["resultados"][0]
        self.assertEqual((r["estado"], r["motivo"]["tipo"]), ("rechazada", "fuera_de_sucursal"))

    def test_8_envio_en_xml(self):
        dev, _ = self._caso()
        id_op = str(uuid.uuid4())
        self.operaciones.append(id_op)
        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<sincronizacion><dispositivo_id>escritorio-1</dispositivo_id><operaciones><item>
<id_operacion>{id_op}</id_operacion><tipo>evidencia</tipo><capturado_en>{_ahora(10)}</capturado_en>
<datos><devolucion_id>{dev}</devolucion_id><comentario>Capturado en la app de escritorio.</comentario></datos>
</item></operaciones></sincronizacion>"""
        codigo, cuerpo = _http("POST", PREFIJO + "/operaciones", token=self.recolector, xml=xml)
        self.assertEqual(codigo, 200, cuerpo)
        self.assertIn(b"<estado>aceptada</estado>", cuerpo)
        self.assertEqual(_sql("SELECT estado FROM operaciones_offline WHERE id_operacion = %s",
                              (id_op,), uno=True)["estado"], "aceptada")

    def test_9_consulta_de_una_operacion(self):
        dev, _ = self._caso()
        op = _op("evidencia", {"devolucion_id": dev, "comentario": "Para consultar despues."})
        self._enviar([op])
        codigo, cuerpo = _http("GET", f"{PREFIJO}/operaciones/{op['id_operacion']}", token=self.recolector)
        self.assertEqual((codigo, cuerpo["estado"], cuerpo["envios"]), (200, "aceptada", 1))
        # Otro usuario no la ve ni sabe que existe.
        codigo, _ = _http("GET", f"{PREFIJO}/operaciones/{op['id_operacion']}", token=self.almacen)
        self.assertEqual(codigo, 404)
        codigo, lista = _http("GET", f"{PREFIJO}/operaciones?devolucion_id={dev}", token=self.recolector)
        self.assertEqual((codigo, lista["paginacion"]["total"]), (200, 1))


if __name__ == "__main__":
    unittest.main()
