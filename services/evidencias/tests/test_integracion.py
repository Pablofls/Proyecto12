"""Integracion real de evidencias: comentarios y archivos en PostgreSQL, metadatos en MongoDB.

Sin dobles: el token sale del servicio auth real por HTTP, la peticion va al
contenedor de evidencias y el efecto se verifica en PostgreSQL, MongoDB y el volumen de archivos. Las filas que crea
la prueba se borran al terminar. Solo corre en la VM:

    docker compose run --rm -e INTEGRACION=1 evidencias python -m pytest -v tests/test_integracion.py

Trazabilidad: RNF-28, RF-08, RF-09, RN-14, RNF-10.
"""
import json
import os
import unittest
import urllib.error
import urllib.request

import psycopg2
import psycopg2.extras

from shared import mongo

AUTH_URL = os.environ.get("AUTH_URL", "http://auth:8000")
SERVICIO_URL = os.environ.get("EVIDENCIAS_URL", "http://evidencias:8000")
PREFIJO = "/api/v1/evidencias"


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


def _http(base, metodo, ruta, cuerpo=None, token=None):
    """Peticion HTTP real; devuelve (codigo, cuerpo_json). No lanza por 4xx."""
    cabeceras = {"Content-Type": "application/json"}
    if token:
        cabeceras["Authorization"] = f"Bearer {token}"
    peticion = urllib.request.Request(
        base + ruta, method=metodo, headers=cabeceras,
        data=json.dumps(cuerpo).encode() if cuerpo is not None else None)
    try:
        with urllib.request.urlopen(peticion, timeout=15) as resp:
            return resp.status, json.loads(resp.read() or b"null")
    except urllib.error.HTTPError as exc:
        crudo = exc.read()
        try:
            return exc.code, json.loads(crudo)
        except ValueError:
            return exc.code, None


def _email_de_rol(rol):
    fila = _sql("""SELECT u.email FROM usuarios u JOIN roles r ON r.id = u.rol_id
                    WHERE r.nombre = %s AND u.estado = 'activo' AND u.eliminado_en IS NULL
                    ORDER BY u.id LIMIT 1""", (rol,), uno=True)
    if not fila:
        raise unittest.SkipTest(f"No hay usuario activo con rol {rol} (corre seed_demo)")
    return fila["email"]


def _login(rol):
    """Login real; la contrasena viene de PASSWORD_DEMO, nunca del repositorio."""
    codigo, cuerpo = _http(AUTH_URL, "POST", "/api/v1/auth/login",
                           {"email": _email_de_rol(rol), "password": os.environ["PASSWORD_DEMO"]})
    if codigo != 200:
        raise AssertionError(f"login de {rol} respondio {codigo}")
    return cuerpo["access_token"]


def _logout(token):
    _http(AUTH_URL, "POST", "/api/v1/auth/logout", token=token)


def _linea_disponible(refrigerado=None):
    """Una linea de venta con al menos 1 unidad sin devolver."""
    filtro = "" if refrigerado is None else (
        "AND p.clasificacion_temperatura = " + ("'refrigerado'" if refrigerado else "'no_refrigerado'"))
    fila = _sql(f"""
        SELECT vd.id FROM venta_detalle vd
          JOIN ventas v ON v.id = vd.venta_id
          JOIN lotes l ON l.id = vd.lote_id JOIN productos p ON p.id = l.producto_id
         WHERE v.eliminado_en IS NULL {filtro}
           AND vd.cantidad - COALESCE((SELECT SUM(d.cantidad_devuelta) FROM devoluciones d
                WHERE d.venta_detalle_id = vd.id AND d.eliminado_en IS NULL
                  AND d.estado <> 'rechazada'), 0) >= 1
         ORDER BY vd.id LIMIT 1""", uno=True)
    if not fila:
        raise unittest.SkipTest("No hay una linea de venta con unidades por devolver")
    return fila["id"]


def _sembrar_devolucion(estado, refrigerado=None):
    """Inserta por SQL una devolucion en el estado pedido (el folio lo pone la
    base, RN-02). Asi cada servicio se prueba aislado de los demas."""
    motivo = _sql("SELECT id FROM motivos WHERE activo ORDER BY id LIMIT 1", uno=True)["id"]
    return _sql("""INSERT INTO devoluciones (venta_detalle_id, motivo_id, descripcion_problema,
                                             cantidad_devuelta, estado)
                   VALUES (%s, %s, 'Prueba de integracion del servicio.', 1, %s)
                   RETURNING id, folio_devolucion""",
                (_linea_disponible(refrigerado), motivo, estado), uno=True)


def _borrar_devoluciones(ids):
    if not ids:
        return
    ids = tuple(ids)
    for paso in (
        "DELETE FROM notificaciones WHERE devolucion_id IN %s",
        "DELETE FROM evidencias WHERE devolucion_id IN %s",
        "DELETE FROM inventario_recuperado WHERE disposicion_id IN "
        "(SELECT id FROM disposiciones WHERE devolucion_id IN %s)",
        "DELETE FROM disposiciones WHERE devolucion_id IN %s",
        "DELETE FROM inspecciones_ref WHERE devolucion_id IN %s",
        "DELETE FROM recepciones WHERE devolucion_id IN %s",
        "DELETE FROM recolecciones WHERE devolucion_id IN %s",
        "DELETE FROM costos WHERE devolucion_id IN %s",
        "DELETE FROM reembolsos WHERE devolucion_id IN %s",
        "DELETE FROM devoluciones WHERE id IN %s",
    ):
        try:
            _sql(paso, (ids,))
        except Exception:  # noqa: BLE001 - limpieza de mejor esfuerzo
            pass

SKIP = unittest.skipUnless(os.environ.get("INTEGRACION") == "1",
                         "Solo en la VM: INTEGRACION=1 y el entorno levantado")
PNG = (b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01"
       b"\x08\x06\x00\x00\x00\x1f\x15\xc4\x89\x00\x00\x00\rIDATx\x9cc\xf8\xff"
       b"\xff?\x00\x05\xfe\x02\xfe\xdc\xccY\xe7\x00\x00\x00\x00IEND\xaeB`\x82")


def _subir(token, dev_id, nombre, contenido):
    """multipart/form-data real (urllib no lo trae hecho)."""
    frontera = "integracion0123456789"
    cuerpo = (f'--{frontera}\r\nContent-Disposition: form-data; name="devolucion_id"\r\n\r\n{dev_id}\r\n'
              f'--{frontera}\r\nContent-Disposition: form-data; name="archivo"; filename="{nombre}"\r\n'
              "Content-Type: application/octet-stream\r\n\r\n").encode() + contenido + \
        f"\r\n--{frontera}--\r\n".encode()
    peticion = urllib.request.Request(
        SERVICIO_URL + PREFIJO, data=cuerpo, method="POST",
        headers={"Authorization": f"Bearer {token}",
                 "Content-Type": f"multipart/form-data; boundary={frontera}"})
    try:
        with urllib.request.urlopen(peticion, timeout=15) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        return exc.code, None


@SKIP
class IntegracionEvidencias(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dev = _sembrar_devolucion("solicitada")
        dueno = _sql("""SELECT u.email FROM devoluciones d JOIN venta_detalle vd ON vd.id = d.venta_detalle_id
                          JOIN ventas v ON v.id = vd.venta_id JOIN usuarios u ON u.id = v.cliente_id
                         WHERE d.id = %s""", (cls.dev["id"],), uno=True)["email"]
        codigo, cuerpo = _http(AUTH_URL, "POST", "/api/v1/auth/login",
                               {"email": dueno, "password": os.environ["PASSWORD_DEMO"]})
        assert codigo == 200
        cls.dueno = cuerpo["access_token"]
        cls.otro = _login("Analista de Devoluciones")

    @classmethod
    def tearDownClass(cls):
        mongo.get_mongo().evidencias_metadatos.delete_many({"devolucion_id": cls.dev["id"]})
        _borrar_devoluciones([cls.dev["id"]])
        _logout(cls.dueno)
        _logout(cls.otro)

    def test_comentario_json_y_archivo_png(self):
        codigo, com = _http(SERVICIO_URL, "POST", PREFIJO,
                            {"devolucion_id": self.dev["id"], "tipo": "comentario",
                             "comentario": "El empaque llego roto."}, self.dueno)
        self.assertEqual(codigo, 201, com)
        self.assertEqual(_sql("SELECT tipo FROM evidencias WHERE id = %s", (com["id"],),
                              uno=True)["tipo"], "comentario")

        codigo, foto = _subir(self.dueno, self.dev["id"], "foto.png", PNG)
        self.assertEqual(codigo, 201)
        fila = _sql("SELECT tipo, mime_type, tamano_bytes FROM evidencias WHERE id = %s",
                    (foto["id"],), uno=True)
        self.assertEqual((fila["tipo"], fila["mime_type"], fila["tamano_bytes"]),
                         ("fotografia", "image/png", len(PNG)))
        meta = mongo.get_mongo().evidencias_metadatos.find_one({"evidencia_id": foto["id"]})
        self.assertIsNotNone(meta)
        self.assertEqual(str(meta["_id"]), foto["metadatos_id"])

        # Enlace temporal firmado (RN-14): sirve sin token y no dura mas de 15 min.
        codigo, enlace = _http(SERVICIO_URL, "GET", f"{PREFIJO}/{foto['id']}/enlace", token=self.dueno)
        self.assertEqual(codigo, 200)
        self.assertLessEqual(enlace["vigencia_segundos"], 900)
        peticion = urllib.request.Request(SERVICIO_URL + enlace["url_relativa"])
        with urllib.request.urlopen(peticion, timeout=15) as resp:
            self.assertEqual(resp.read(), PNG)

    def test_un_archivo_que_no_es_imagen_ni_pdf_se_rechaza(self):  # RNF-10
        codigo, _ = _subir(self.dueno, self.dev["id"], "falso.png", b"MZ esto es un ejecutable")
        self.assertEqual(codigo, 415)
        self.assertEqual(_sql("SELECT COUNT(*) AS n FROM evidencias WHERE devolucion_id = %s "
                              "AND nombre_original = 'falso.png'", (self.dev["id"],), uno=True)["n"], 0)

    def test_otro_rol_no_adjunta(self):
        codigo, _ = _http(SERVICIO_URL, "POST", PREFIJO,
                          {"devolucion_id": self.dev["id"], "tipo": "comentario", "comentario": "x"},
                          self.otro)
        self.assertEqual(codigo, 403)

    def test_archivo_sin_firma_ni_token_no_se_descarga(self):
        codigo, _ = _http(SERVICIO_URL, "GET", f"{PREFIJO}/1/archivo")
        self.assertEqual(codigo, 401)


if __name__ == "__main__":
    unittest.main()
