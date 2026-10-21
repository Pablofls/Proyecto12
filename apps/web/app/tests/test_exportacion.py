"""Exportacion de reportes a CSV (RF-28, UC-24)."""
import csv
import io
import unittest
from datetime import datetime
from decimal import Decimal
from unittest.mock import MagicMock, patch

from app.exportacion import BLOQUE_FILAS, celda_segura, generar_csv
from app.security import (
    ADMINISTRADOR, ANALISTA, CLIENTE, COORDINADOR, ENCARGADO_REEMBOLSOS, INSPECTOR,
)
from app.tests.dobles import PruebaWeb


def leer(respuesta_o_bytes):
    datos = respuesta_o_bytes if isinstance(respuesta_o_bytes, bytes) else respuesta_o_bytes.data
    return list(csv.reader(io.StringIO(datos.decode("utf-8-sig"))))


class PruebaCeldaSegura(unittest.TestCase):
    def test_neutraliza_formulas_en_texto(self):
        for peligroso in ("=1+1", "+cmd|' /C calc'!A0", "-2+3", "@SUM(A1)", "\tx", "\rx"):
            self.assertEqual(celda_segura(peligroso), "'" + peligroso)

    def test_texto_normal_y_vacios_no_cambian(self):
        self.assertEqual(celda_segura("Leche entera"), "Leche entera")
        self.assertEqual(celda_segura(None), "")
        self.assertEqual(celda_segura(""), "")

    def test_numeros_negativos_no_se_prefijan(self):
        self.assertEqual(celda_segura(-5), "-5")
        self.assertEqual(celda_segura(Decimal("-12.50")), "-12.50")
        self.assertEqual(celda_segura(True), "si")

    def test_fechas_en_formato_estable(self):
        self.assertEqual(celda_segura(datetime(2026, 10, 21, 9, 5, 3)), "2026-10-21 09:05:03")


class PruebaGenerarCsv(unittest.TestCase):
    COLUMNAS = [("Folio", "folio"), ("Nota", "nota")]

    def test_bom_encabezados_y_acentos(self):
        crudo = b"".join(generar_csv(self.COLUMNAS, [{"folio": "DEV-1", "nota": "Dañado, con coma"}]))
        self.assertTrue(crudo.startswith(b"\xef\xbb\xbf"))
        self.assertEqual(leer(crudo), [["Folio", "Nota"], ["DEV-1", "Dañado, con coma"]])

    def test_escapa_formulas_en_el_archivo(self):
        crudo = b"".join(generar_csv(self.COLUMNAS, [{"folio": "DEV-1", "nota": "=HYPERLINK(\"x\")"}]))
        self.assertEqual(leer(crudo)[1][1], "'=HYPERLINK(\"x\")")

    def test_entrega_en_bloques_sin_acumular_todo(self):
        filas = ({"folio": f"DEV-{i}", "nota": "x"} for i in range(BLOQUE_FILAS * 2 + 3))
        bloques = list(generar_csv(self.COLUMNAS, filas))
        self.assertGreaterEqual(len(bloques), 3)
        self.assertEqual(len(leer(b"".join(bloques))), BLOQUE_FILAS * 2 + 3 + 1)

    def test_sin_filas_solo_encabezado(self):
        self.assertEqual(leer(b"".join(generar_csv(self.COLUMNAS, []))), [["Folio", "Nota"]])


class PruebaRutas(PruebaWeb):
    """Control de rol, filtros y bitacora de cada reporte."""

    def setUp(self):
        super().setUp()
        self.llamadas = []

        def filas_falsas(sql, parametros, limite):
            self.llamadas.append((sql, parametros, limite))
            return iter([{"folio_devolucion": "DEV-1", "estado": "autorizada",
                          "fecha_solicitud": datetime(2026, 10, 1), "motivo": "Danado",
                          "tienda": "Centro", "folio_venta": "V-1", "producto": "=Leche",
                          "clasificacion_temperatura": "refrigerado", "numero_lote": "L1",
                          "cliente": "Ana", "cantidad_devuelta": 1}])

        for parche in (patch("app.exportacion._filas", filas_falsas),
                       patch("app.blueprints.reportes.get_conn", MagicMock())):
            parche.start()
            self.addCleanup(parche.stop)

    def get(self, rol, ruta, usuario_id=1):
        return self.cliente_como(rol, usuario_id).get(ruta)

    def acciones_bitacora(self):
        return [(p[1], p[4]) for p in self.bd.insertadas("bitacora")]

    def test_sin_sesion_redirige(self):
        self.assertEqual(self.app.test_client().get("/reportes/costos.csv").status_code, 302)

    def test_403_por_rol_en_cada_reporte(self):
        prohibidos = {
            "/reportes/costos.csv": (CLIENTE, INSPECTOR, COORDINADOR),
            "/reportes/causas.csv": (CLIENTE, ENCARGADO_REEMBOLSOS, COORDINADOR),
            "/reportes/bitacora.csv": (CLIENTE, ENCARGADO_REEMBOLSOS, INSPECTOR),
            "/reportes/reembolsos.csv": (CLIENTE, ADMINISTRADOR, INSPECTOR),
        }
        for ruta, roles in prohibidos.items():
            for rol in roles:
                self.assertEqual(self.get(rol, ruta).status_code, 403, (ruta, rol))
        self.assertEqual(self.llamadas, [])

    def test_descarga_con_cabeceras_de_archivo(self):
        resp = self.get(ANALISTA, "/reportes/devoluciones.csv")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers["Content-Type"], "text/csv; charset=utf-8")
        self.assertIn('attachment; filename="devoluciones_', resp.headers["Content-Disposition"])
        filas = leer(resp)
        self.assertEqual(filas[0][0], "Folio")
        self.assertEqual(filas[1][6], "'=Leche")

    def test_filtros_llegan_como_parametros_ligados(self):
        self.get(ANALISTA, "/reportes/devoluciones.csv?estado=autorizada&q=le%27che"
                           "&fecha_inicio=2026-10-01&motivo_id=3&tienda_id=2")
        sql, parametros, limite = self.llamadas[0]
        self.assertEqual(parametros, ("autorizada", "%le'che%", "%le'che%", "2026-10-01", 3, 2))
        self.assertNotIn("le'che", sql)
        self.assertEqual(limite, 50000)

    def test_cliente_solo_exporta_sus_devoluciones(self):
        self.get(CLIENTE, "/reportes/devoluciones.csv?estado=cerrada", usuario_id=9)
        sql, parametros, _ = self.llamadas[0]
        self.assertIn("v.cliente_id = %s", sql)
        self.assertEqual(parametros[0], 9)

    def test_bitacora_de_exportacion_lleva_tipo_y_filtros_sin_contenido(self):
        self.get(ANALISTA, "/reportes/devoluciones.csv?estado=autorizada")
        (accion, detalle), = self.acciones_bitacora()
        self.assertEqual(accion, "exportar_reporte")
        self.assertIn("devoluciones", detalle)
        self.assertIn("estado=autorizada", detalle)
        self.assertNotIn("DEV-1", detalle)

    def test_causas_usa_los_mismos_filtros_del_panel(self):
        self.get(ANALISTA, "/reportes/causas.csv?fecha_inicio=2026-09-01&tienda_id=4&lote=A1")
        sql, parametros, _ = self.llamadas[0]
        self.assertEqual(parametros, ("2026-09-01", "%A1%", 4))
        self.assertIn("WITH conteo", sql)
        self.assertIn("d.fecha_solicitud >= %s", sql)

    def test_bitacora_y_costos_y_reembolsos_responden_csv(self):
        for rol, ruta in ((ADMINISTRADOR, "/reportes/bitacora.csv?accion=autorizacion"),
                          (ENCARGADO_REEMBOLSOS, "/reportes/costos.csv"),
                          (ENCARGADO_REEMBOLSOS, "/reportes/reembolsos.csv"),
                          (ADMINISTRADOR, "/reportes/causas.csv")):
            self.assertEqual(self.get(rol, ruta).status_code, 200, ruta)
        self.assertEqual(self.llamadas[0][1], ("autorizacion",))


if __name__ == "__main__":
    unittest.main()
