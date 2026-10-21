"""Integracion real de auth: sesion JWT en Redis, historial de acceso en PostgreSQL y revocacion.

Sin dobles: el token sale del servicio auth real por HTTP, la peticion va al
contenedor de auth y el efecto se verifica en Redis y PostgreSQL. Las filas que crea
la prueba se borran al terminar. Solo corre en la VM:

    docker compose run --rm -e INTEGRACION=1 auth python -m pytest -v tests/test_integracion.py

Trazabilidad: RNF-28, RF-01, RNF-08, RNF-12, RNF-13, RNF-16.
"""
import json
import os
import unittest
import urllib.error
import urllib.request

import psycopg2
import psycopg2.extras

import jwt
from shared.infra import get_redis

AUTH_URL = os.environ.get("AUTH_URL", "http://auth:8000")
SERVICIO_URL = os.environ.get("AUTH_URL", "http://auth:8000")
PREFIJO = "/api/v1/auth"


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


def _claims(token):
    return jwt.decode(token, options={"verify_signature": False})


@SKIP
class IntegracionAuth(unittest.TestCase):
    def setUp(self):
        # Contador de login limpio: la suite E2E tambien usa este endpoint.
        r = get_redis()
        for clave in r.scan_iter("devoluciones:limite:*:login"):
            r.delete(clave)
        self.abiertos = []

    def tearDown(self):
        for token in self.abiertos:
            _logout(token)

    def _abrir(self, rol):
        email = _email_de_rol(rol)
        codigo, cuerpo = _http(SERVICIO_URL, "POST", PREFIJO + "/login",
                               {"email": email, "password": os.environ["PASSWORD_DEMO"]})
        self.assertEqual(codigo, 200)
        self.abiertos.append(cuerpo["access_token"])
        return email, cuerpo

    def test_login_crea_sesion_en_redis_historial_y_bitacora(self):
        email, tokens = self._abrir("Cliente")
        claims = _claims(tokens["access_token"])
        r = get_redis()
        clave = f"devoluciones:sesion_api:{claims['sid']}"
        self.assertEqual(r.exists(clave), 1)
        self.assertTrue(0 < r.ttl(clave) <= 8 * 3600)
        self.assertTrue(r.sismember(f"devoluciones:sesiones_usuario:{claims['sub']}", claims["sid"]))
        self.assertTrue(_sql("SELECT 1 FROM intentos_acceso WHERE email = %s AND exitoso "
                             "ORDER BY fecha DESC LIMIT 1", (email,), uno=True))
        self.assertTrue(_sql("SELECT 1 FROM bitacora WHERE accion = 'login_api' AND usuario_id = %s",
                             (int(claims["sub"]),), uno=True))
        # RNF-16: ni la bitacora ni el historial guardan el token.
        self.assertIsNone(_sql("SELECT 1 FROM bitacora WHERE detalle LIKE %s",
                               ("%" + tokens["access_token"][:30] + "%",), uno=True))

    def test_logout_revoca_el_token_y_borra_la_sesion(self):
        _, tokens = self._abrir("Cliente")
        token, claims = tokens["access_token"], _claims(tokens["access_token"])
        codigo, _ = _http(SERVICIO_URL, "POST", PREFIJO + "/logout", token=token)
        self.assertEqual(codigo, 200)
        r = get_redis()
        self.assertEqual(r.exists(f"devoluciones:jwt_revocado:{claims['jti']}"), 1)
        self.assertEqual(r.exists(f"devoluciones:sesion_api:{claims['sid']}"), 0)
        codigo, cuerpo = _http(SERVICIO_URL, "GET", PREFIJO + "/sesion", token=token)
        self.assertEqual(codigo, 401)
        self.assertEqual(cuerpo["error"]["tipo"], "token_revocado")

    def test_refresh_emite_un_access_nuevo_de_la_misma_sesion(self):
        _, tokens = self._abrir("Cliente")
        codigo, nuevo = _http(SERVICIO_URL, "POST", PREFIJO + "/refresh",
                              {"refresh_token": tokens["refresh_token"]})
        self.assertEqual(codigo, 200)
        self.assertEqual(_claims(nuevo["access_token"])["sid"], _claims(tokens["access_token"])["sid"])
        # Un access token no sirve para renovar.
        codigo, _ = _http(SERVICIO_URL, "POST", PREFIJO + "/refresh",
                          {"refresh_token": tokens["access_token"]})
        self.assertEqual(codigo, 401)

    def test_admin_cierra_todas_las_sesiones_de_un_usuario(self):  # RNF-08
        _, admin = self._abrir("Administrador")
        email, victima = self._abrir("Cliente")
        uid = int(_claims(victima["access_token"])["sub"])
        codigo, resp = _http(SERVICIO_URL, "DELETE", f"{PREFIJO}/usuarios/{uid}/sesiones",
                             token=admin["access_token"])
        self.assertEqual(codigo, 200)
        self.assertGreaterEqual(resp["sesiones_cerradas"], 1)
        codigo, cuerpo = _http(SERVICIO_URL, "GET", PREFIJO + "/sesion", token=victima["access_token"])
        self.assertEqual(codigo, 401)
        self.assertEqual(cuerpo["error"]["tipo"], "sesion_inactiva")
        # Un cliente no puede cerrar sesiones ajenas.
        _, otro = self._abrir("Cliente")
        codigo, _ = _http(SERVICIO_URL, "DELETE", f"{PREFIJO}/usuarios/{uid}/sesiones",
                          token=otro["access_token"])
        self.assertEqual(codigo, 403)

    def test_credenciales_malas_quedan_en_el_historial_sin_revelar_nada(self):
        email = _email_de_rol("Cliente")
        codigo, cuerpo = _http(SERVICIO_URL, "POST", PREFIJO + "/login",
                               {"email": email, "password": "contrasena-incorrecta"})
        self.assertEqual(codigo, 401)
        self.assertEqual(cuerpo["error"]["tipo"], "credenciales_invalidas")
        self.assertTrue(_sql("SELECT 1 FROM intentos_acceso WHERE email = %s AND NOT exitoso "
                             "ORDER BY fecha DESC LIMIT 1", (email,), uno=True))
        # Un login valido reinicia el contador de intentos (RNF-12).
        self._abrir("Cliente")
        self.assertEqual(get_redis().exists(f"devoluciones:intentos:{email}"), 0)


if __name__ == "__main__":
    unittest.main()
