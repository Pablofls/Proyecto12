"""Integracion real de reportes-analitica contra la VM (PostgreSQL, Redis y auth reales).

    docker compose run --rm -e INTEGRACION=1 -e PASSWORD_DEMO=... reportes-analitica \
        python -m pytest -v tests/test_integracion.py

Es la prueba que ejecuta TODAS las consultas SQL del servicio, que en local solo
se simulan. Las cifras se contrastan contra consultas independientes sobre las
mismas tablas, para que un JOIN que duplique filas o un filtro mal puesto salte.
El ultimo caso agota el limite de descargas del Administrador (20 por minuto):
no lo corras dos veces seguidas.
Trazabilidad: RF-23, RF-25, RF-26, RF-28, RN-13, RN-15, RNF-13, RNF-28.
"""
import csv
import io
import json
import os
import unittest
import urllib.error
import urllib.request
import zipfile
from datetime import date, timedelta

import psycopg2
import psycopg2.extras

AUTH_URL = os.environ.get("AUTH_URL", "http://auth:8000")
SERVICIO_URL = os.environ.get("REPORTES_URL", "http://reportes-analitica:8000")
BASE = "/api/v1"
SKIP = unittest.skipUnless(os.environ.get("INTEGRACION") == "1",
                           "Solo en la VM: INTEGRACION=1 y el entorno levantado")


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


def _pedir(base, metodo, ruta, cuerpo=None, token=None, aceptar=None):
    """Devuelve (codigo, cabeceras, bytes); no lanza por 4xx."""
    cabeceras = {"Content-Type": "application/json"}
    if token:
        cabeceras["Authorization"] = f"Bearer {token}"
    if aceptar:
        cabeceras["Accept"] = aceptar
    peticion = urllib.request.Request(base + ruta, method=metodo, headers=cabeceras,
                                      data=json.dumps(cuerpo).encode() if cuerpo is not None else None)
    try:
        with urllib.request.urlopen(peticion, timeout=60) as resp:
            return resp.status, dict(resp.headers), resp.read()
    except urllib.error.HTTPError as exc:
        return exc.code, dict(exc.headers), exc.read()


def _login(rol):
    fila = _sql("""SELECT u.email FROM usuarios u JOIN roles r ON r.id = u.rol_id
                    WHERE r.nombre = %s AND u.estado = 'activo' AND u.eliminado_en IS NULL
                    ORDER BY u.id LIMIT 1""", (rol,), uno=True)
    if not fila:
        raise unittest.SkipTest(f"No hay usuario activo con rol {rol} (corre seed_demo)")
    codigo, _, cuerpo = _pedir(AUTH_URL, "POST", "/api/v1/auth/login",
                               {"email": fila["email"], "password": os.environ["PASSWORD_DEMO"]})
    if codigo != 200:
        raise AssertionError(f"login de {rol} respondio {codigo}")
    return json.loads(cuerpo)["access_token"]


@SKIP
class IntegracionReportes(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.analista = _login("Analista de Devoluciones")
        cls.admin = _login("Administrador")
        cls.cliente = _login("Cliente")
        cls.reembolsos = _login("Encargado de Reembolsos")

    def get(self, ruta, token=None, aceptar=None):
        return _pedir(SERVICIO_URL, "GET", BASE + ruta, token=token or self.analista, aceptar=aceptar)

    def json(self, ruta, token=None):
        codigo, _, cuerpo = self.get(ruta, token)
        self.assertEqual(codigo, 200, f"{ruta}: {cuerpo[:300]}")
        return json.loads(cuerpo)

    # ------------------------------------------------------------------ seguridad
    def test_seguridad(self):
        self.assertEqual(_pedir(SERVICIO_URL, "GET", BASE + "/reportes")[0], 401)
        for ruta in ("/reportes", "/reportes/devoluciones", "/analitica/tendencias", "/graficas/pareto"):
            self.assertEqual(self.get(ruta, self.cliente)[0], 403, ruta)
        # Las alertas de fraude nombran clientes: solo Administrador y Analista (RN-15).
        self.assertEqual(self.get("/analitica/alertas-fraude", self.reembolsos)[0], 403)
        self.assertEqual(self.get("/analitica/alertas-fraude")[0], 200)

    # ------------------------------------------------------------------ cifras contra consultas independientes
    def test_devoluciones_coinciden_con_la_base(self):
        esperado = _sql("SELECT COUNT(*) AS n, COALESCE(SUM(cantidad_devuelta),0) AS u FROM devoluciones "
                        "WHERE eliminado_en IS NULL", uno=True)
        r = self.json("/reportes/devoluciones?por_pagina=100")
        self.assertEqual(r["paginacion"]["total"], esperado["n"])     # ningun JOIN duplica ni pierde filas
        codigo, cab, crudo = self.get("/reportes/devoluciones?formato=csv")
        filas = list(csv.reader(io.StringIO(crudo.decode("utf-8-sig"))))
        self.assertEqual(len(filas) - 1, esperado["n"])
        self.assertEqual(sum(int(f[8]) for f in filas[1:]), esperado["u"])

    def test_costos_suman_lo_mismo_que_la_vista(self):
        esperado = _sql("SELECT COALESCE(SUM(vc.costo_total),0) AS t FROM vista_costo_devolucion vc "
                        "JOIN devoluciones d ON d.id = vc.devolucion_id WHERE d.eliminado_en IS NULL", uno=True)["t"]
        _, _, crudo = self.get("/reportes/costos?formato=csv")
        filas = list(csv.reader(io.StringIO(crudo.decode("utf-8-sig"))))
        self.assertAlmostEqual(sum(float(f[9]) for f in filas[1:]), float(esperado), places=2)

    def test_factores_cada_combinacion_coincide_con_la_base(self):
        """Cada celda del cruce proveedor x tienda se contrasta con una consulta independiente."""
        r = self.json("/analitica/factores?por=proveedor&con=tienda&limite=100")
        self.assertEqual(r["estado"], "ok")
        self.assertGreaterEqual(len(r["celdas"]), 1)
        for c in r["celdas"][:10]:
            esperado = _sql("""
                SELECT SUM(vd.cantidad) AS vendidas,
                       COALESCE(SUM((SELECT SUM(d.cantidad_devuelta) FROM devoluciones d
                                      WHERE d.venta_detalle_id = vd.id AND d.eliminado_en IS NULL)), 0) AS devueltas
                  FROM venta_detalle vd JOIN ventas v ON v.id = vd.venta_id JOIN lotes l ON l.id = vd.lote_id
                 WHERE v.eliminado_en IS NULL AND l.proveedor_id = %s AND v.tienda_id = %s""",
                (c["a_id"], c["b_id"]), uno=True)
            self.assertEqual((c["unidades_vendidas"], c["unidades_devueltas"]),
                             (int(esperado["vendidas"]), int(esperado["devueltas"])), (c["a_etiqueta"], c["b_etiqueta"]))
            self.assertLessEqual(c["intervalo_95_pct"]["bajo"], c["tasa_pct"])
            self.assertGreaterEqual(c["intervalo_95_pct"]["alto"], c["tasa_pct"])
        tasas = [c["tasa_pct"] for c in r["celdas"]]
        self.assertEqual(tasas, sorted(tasas, reverse=True))

    def test_factores_senala_el_lote_problematico_de_la_demo(self):
        r = self.json("/analitica/factores?por=lote&con=proveedor&solo_distinguibles=true&limite=100")
        lote = [c for c in r["celdas"] if "L-2026-PROB-01" in c["a_etiqueta"]]
        self.assertEqual(len(lote), 1, "el lote problematico debe aparecer como distinguible")
        self.assertTrue(lote[0]["distinguible"])
        self.assertIsNotNone(lote[0]["lectura"])
        self.assertGreaterEqual(lote[0]["veces_promedio"], 2)

    def test_factores_valida_y_exige_permiso(self):
        self.assertEqual(self.get("/analitica/factores?por=tienda&con=tienda")[0], 400)
        self.assertEqual(self.get("/analitica/factores?por=ruta")[0], 400)
        self.assertEqual(self.get("/analitica/factores", self.cliente)[0], 403)

    def test_tasas_suman_las_unidades_de_toda_la_base(self):
        vendidas = _sql("SELECT COALESCE(SUM(vd.cantidad),0) AS n FROM venta_detalle vd JOIN ventas v "
                        "ON v.id = vd.venta_id WHERE v.eliminado_en IS NULL", uno=True)["n"]
        devueltas = _sql("SELECT COALESCE(SUM(d.cantidad_devuelta),0) AS n FROM devoluciones d "
                         "JOIN venta_detalle vd ON vd.id = d.venta_detalle_id JOIN ventas v ON v.id = vd.venta_id "
                         "WHERE d.eliminado_en IS NULL AND v.eliminado_en IS NULL", uno=True)["n"]
        for por in ("proveedor", "tienda", "producto", "lote"):
            _, _, crudo = self.get(f"/reportes/tasas?por={por}&formato=csv")
            filas = list(csv.reader(io.StringIO(crudo.decode("utf-8-sig"))))[1:]
            self.assertEqual(sum(int(f[1]) for f in filas), vendidas, por)
            self.assertEqual(sum(int(f[2]) for f in filas), devueltas, por)
            for f in filas:
                if int(f[1]):
                    self.assertAlmostEqual(float(f[4]), int(f[2]) * 100 / int(f[1]), places=1)

    def test_pareto_acumula_hasta_cien_y_cada_dimension_funciona(self):
        n = _sql("SELECT COUNT(*) AS n FROM devoluciones WHERE eliminado_en IS NULL", uno=True)["n"]
        for dim in ("motivo", "producto", "lote", "proveedor", "tienda", "ruta", "transportista", "estado"):
            r = self.json(f"/reportes/pareto?dimension={dim}&por_pagina=100")
            cats = r["datos"]
            self.assertEqual(sum(c["casos"] for c in cats), n, dim)
            if cats:
                self.assertAlmostEqual(cats[-1]["porcentaje_acumulado"], 100.0, places=1)
                self.assertEqual([c["total"] for c in cats], sorted((c["total"] for c in cats), reverse=True))
        for medida in ("frecuencia", "cantidad", "costo"):
            self.assertEqual(self.get(f"/reportes/pareto?medida={medida}")[0], 200, medida)

    def test_filtro_de_fechas_acota(self):
        hoy = date.today()
        r = self.json(f"/reportes/devoluciones?desde={hoy:%Y-%m-%d}&hasta={hoy:%Y-%m-%d}&por_pagina=100")
        esperado = _sql("SELECT COUNT(*) AS n FROM devoluciones WHERE eliminado_en IS NULL "
                        "AND fecha_solicitud::date = CURRENT_DATE", uno=True)["n"]
        self.assertEqual(r["paginacion"]["total"], esperado)
        sin = self.json("/reportes/devoluciones?desde=2000-01-01&hasta=2000-01-02")
        self.assertEqual(sin["paginacion"]["total"], 0)

    # ------------------------------------------------------------------ formatos
    def test_los_cuatro_formatos(self):
        codigo, cab, crudo = self.get("/reportes/tasas?formato=xlsx")
        self.assertEqual(codigo, 200)
        self.assertEqual(zipfile.ZipFile(io.BytesIO(crudo)).testzip(), None)
        self.assertIn("attachment", cab["Content-Disposition"])
        self.assertEqual(cab["Cache-Control"], "no-store")
        codigo, cab, crudo = self.get("/reportes/tasas?formato=pdf")
        self.assertEqual((codigo, crudo[:8]), (200, b"%PDF-1.4"))
        codigo, cab, crudo = self.get("/reportes/tasas", aceptar="application/xml")
        self.assertEqual(codigo, 200)
        self.assertTrue(crudo.lstrip().startswith(b"<?xml"))
        self.assertEqual(self.get("/reportes/tasas?formato=docx")[0], 400)

    def test_la_descarga_queda_en_bitacora_sin_los_datos(self):
        antes = _sql("SELECT COALESCE(MAX(id),0) AS m FROM bitacora", uno=True)["m"]
        self.assertEqual(self.get("/reportes/devoluciones?formato=csv")[0], 200)
        fila = _sql("SELECT detalle FROM bitacora WHERE id > %s AND accion = 'exportar_reporte' "
                    "ORDER BY id DESC LIMIT 1", (antes,), uno=True)
        self.assertIsNotNone(fila)
        self.assertIn("devoluciones csv filas=", fila["detalle"])

    # ------------------------------------------------------------------ analitica
    def test_series_de_las_tres_medidas_y_con_objeto(self):
        proveedor = _sql("SELECT id FROM proveedores ORDER BY id LIMIT 1", uno=True)["id"]
        plazo = _sql("SELECT MAX(dias_plazo) AS d FROM politicas_devolucion", uno=True)["d"]
        for medida in ("tasa", "devoluciones", "costo"):
            for extra in ("", f"&dimension=proveedor&referencia_id={proveedor}"):
                r = self.json(f"/analitica/tendencias?medida={medida}&meses=12{extra}")
                self.assertEqual(len(r["serie"]), 12, (medida, extra))
                self.assertIn(r["tendencia"]["estado"], ("ok", "sin_datos"))
        # La tasa solo usa meses maduros: el ultimo termino hace mas que el plazo de devolucion.
        ultimo = self.json("/analitica/tendencias?medida=tasa")["serie"][-1]["mes"]
        anio, mes = int(ultimo[:4]), int(ultimo[5:])
        fin = (date(anio + (mes == 12), mes % 12 + 1, 1) - timedelta(days=1))
        self.assertLessEqual(fin, date.today() - timedelta(days=plazo))
        # Las demas no incluyen el mes en curso.
        ultimo = self.json("/analitica/tendencias?medida=devoluciones")["serie"][-1]["mes"]
        self.assertLess(ultimo, date.today().strftime("%Y-%m"))

    def test_pronostico_y_graficas(self):
        r = self.json("/analitica/pronosticos?medida=devoluciones&horizonte=3")
        self.assertEqual(r["pronostico"]["estado"] in ("ok", "sin_datos"), True)
        if r["pronostico"]["estado"] == "ok":
            for p in r["pronostico"]["puntos"]:
                self.assertTrue(0 <= p["limite_inferior"] <= p["valor"] <= p["limite_superior"])
        for ruta in ("/graficas/pareto", "/graficas/tasas?por=lote", "/graficas/tendencia?medida=costo&horizonte=2"):
            self.assertIn("series", self.json(ruta)["opciones"], ruta)
        self.assertEqual(self.get("/graficas/pareto", aceptar="application/xml")[0], 406)

    def test_anomalias(self):
        for por in ("proveedor", "tienda", "producto", "lote"):
            r = self.json(f"/analitica/anomalias?tipo=objetos&por={por}")
            self.assertIn(r["estado"], ("ok", "sin_datos"))
        self.assertIn(self.json("/analitica/anomalias?tipo=meses&medida=devoluciones")["estado"], ("ok", "sin_datos"))
        self.assertEqual(self.get("/analitica/anomalias?tipo=raros")[0], 400)

    def test_objeto_inexistente_404_y_dimension_sola_400(self):
        self.assertEqual(self.get("/analitica/tendencias?dimension=lote&referencia_id=99999999")[0], 404)
        self.assertEqual(self.get("/analitica/tendencias?dimension=lote")[0], 400)

    # ------------------------------------------------------------------ limite de descargas (RNF-13)
    def test_zz_las_descargas_estan_limitadas_por_usuario(self):
        codigos = [self.get("/reportes/costos?formato=csv", self.admin)[0] for _ in range(22)]
        self.assertEqual(codigos[:20], [200] * 20)
        self.assertIn(429, codigos[20:])
        # Consultar en JSON no cuenta como descarga; sigue disponible.
        self.assertEqual(self.get("/reportes/costos", self.admin)[0], 200)


if __name__ == "__main__":
    unittest.main()
