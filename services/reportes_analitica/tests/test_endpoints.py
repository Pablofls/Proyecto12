"""Endpoints con la base simulada: filtros, formatos, encabezados y permisos.

Las consultas SQL no se ejecutan aqui (solo corren en la VM); lo que se prueba es
todo lo demas: validacion de parametros, negociacion de formato, limites,
encabezados de descarga, roles y bitacora.
Trazabilidad: RF-28, RN-13, RN-15, RNF-09, RNF-11, RNF-13, RNF-16.
"""
import json
from datetime import date
from decimal import Decimal

import pytest
from lxml import etree

import app as servicio
import datos
import formatos
import shared.seguridad as seguridad


@pytest.fixture
def api(monkeypatch):
    estado = {"rol": "Analista de Devoluciones", "bitacora": [], "limites": []}
    monkeypatch.setattr(seguridad, "decodificar", lambda token, tipo="access": {
        "sub": "7", "rol": estado["rol"], "nombre": "Prueba", "sid": "s", "jti": "j"})
    monkeypatch.setattr(seguridad, "comprobar_en_redis", lambda claims: None)
    monkeypatch.setattr(servicio, "registrar_bitacora", lambda *a, **k: estado["bitacora"].append(a))
    monkeypatch.setattr(servicio, "limitar", lambda *a, **k: estado["limites"].append((a, k)))
    filas = [{"folio": f"DEV-{i:04d}", "fecha_solicitud": date(2026, 10, 1), "estado": "cerrada",
              "motivo": "Producto dañado", "producto": "Leche", "lote": "L-1", "proveedor": "Lacteos",
              "tienda": "Centro", "cantidad_devuelta": i, "costo_total": Decimal("10.50")} for i in range(1, 46)]
    monkeypatch.setattr(datos, "reporte_devoluciones", lambda *a: filas)
    monkeypatch.setattr(datos, "reporte_costos", lambda *a: [])
    monkeypatch.setattr(datos, "tasas_por", lambda por, d, h: [
        {"id": i, "etiqueta": f"P{i}", "unidades_vendidas": 100, "unidades_devueltas": 5 + (40 if i == 6 else i % 2),
         "devoluciones": 3, "tasa_pct": 5.0 + (40 if i == 6 else i % 2)} for i in range(1, 8)])
    monkeypatch.setattr(datos, "pareto", lambda *a: {"total_general": 10.0, "categorias": [
        {"etiqueta": "a", "total": 6.0, "casos": 3, "porcentaje": 60.0, "porcentaje_acumulado": 60.0},
        {"etiqueta": "b", "total": 4.0, "casos": 2, "porcentaje": 40.0, "porcentaje_acumulado": 100.0}]})
    monkeypatch.setattr(datos, "etiqueta_objeto", lambda dim, ref: "Lacteos" if ref == 1 else None)
    monkeypatch.setattr(datos, "serie_mensual", lambda medida, meses, dim=None, ref=None: [
        {"mes": f"2026-0{m}", "unidades_vendidas": 100, "unidades_devueltas": 5, "valor": float(v), "estado": "ok"}
        for m, v in zip(range(1, 9), [1, 2, 2.5, 4, 4.2, 6, 6.1, 8])])
    monkeypatch.setattr(datos, "alertas_fraude", lambda: [{"cliente": "Ana", "razones": ["x"]}])
    cliente = servicio.create_app().test_client()
    cliente.estado = estado
    cliente.pedir = lambda ruta, rol=None, **kw: (estado.update(rol=rol or estado["rol"]) or
                                                  cliente.get(ruta, headers={"Authorization": "Bearer x", **kw.pop("headers", {})}, **kw))
    return cliente


# --------------------------------------------------------------------------- reportes JSON / XML
def test_catalogo_lista_los_cinco_reportes(api):
    r = api.pedir("/api/v1/reportes")
    assert r.status_code == 200
    assert {x["nombre"] for x in r.json["datos"]} == {"devoluciones", "costos", "tasas", "pareto", "tendencia"}
    assert r.json["datos"][0]["formatos"] == ["json", "csv", "xlsx", "pdf"]


def test_reporte_json_pagina_y_describe_sus_columnas(api):
    r = api.pedir("/api/v1/reportes/devoluciones?por_pagina=10&pagina=2&estado=cerrada&desde=2026-10-01")
    assert r.status_code == 200
    j = r.json
    assert len(j["datos"]) == 10 and j["paginacion"] == {"pagina": 2, "por_pagina": 10, "total": 45, "paginas": 5}
    assert j["filtros"] == {"estado": "cerrada", "desde": "2026-10-01"}
    assert j["columnas"][0] == {"clave": "folio", "titulo": "Folio", "tipo": "texto"}
    assert api.estado["limites"] == [] and api.estado["bitacora"] == []   # consultar no cuenta como descarga


def test_reporte_xml_valida_contra_el_xsd(api):
    r = api.pedir("/api/v1/reportes/devoluciones", headers={"Accept": "application/xml"})
    assert r.status_code == 200 and r.mimetype == "application/xml"
    esquema = etree.XMLSchema(etree.parse(servicio.os.path.join(servicio.os.path.dirname(servicio.__file__),
                                                               "contratos", "reporte.xsd")))
    assert esquema.validate(etree.fromstring(r.data)), esquema.error_log


# --------------------------------------------------------------------------- descargas
def test_csv_descarga_con_encabezados_seguros_y_bitacora_sin_datos(api):
    r = api.pedir("/api/v1/reportes/devoluciones?formato=csv&desde=2026-10-01")
    assert r.status_code == 200 and r.data.startswith("﻿".encode())
    assert r.headers["Content-Type"].startswith("text/csv")
    assert r.headers["Content-Disposition"].startswith('attachment; filename="reporte_devoluciones_')
    assert r.headers["Content-Disposition"].endswith('.csv"')
    assert r.headers["Cache-Control"] == "no-store" and r.headers["X-Content-Type-Options"] == "nosniff"
    assert len(api.estado["limites"]) == 1
    accion, entidad, _, detalle = api.estado["bitacora"][0]
    assert accion == "exportar_reporte" and "filas=45" in detalle and "csv" in detalle
    assert "Producto" not in detalle and "DEV-0001" not in detalle      # nunca los datos (RNF-16)


def test_xlsx_y_pdf_son_archivos_validos(api):
    x = api.pedir("/api/v1/reportes/devoluciones?formato=xlsx")
    assert x.status_code == 200 and x.data[:2] == b"PK" and "spreadsheetml" in x.headers["Content-Type"]
    p = api.pedir("/api/v1/reportes/devoluciones?formato=pdf")
    assert p.status_code == 200 and p.data.startswith(b"%PDF-1.4") and p.headers["Content-Type"] == "application/pdf"
    assert len(api.estado["bitacora"]) == 2


def test_demasiadas_filas_responde_422_con_la_salida(api, monkeypatch):
    monkeypatch.setitem(formatos.MAX_FILAS, "pdf", 10)
    r = api.pedir("/api/v1/reportes/devoluciones?formato=pdf")
    assert r.status_code == 422 and r.json["error"]["tipo"] == "demasiadas_filas"
    assert "desde y hasta" in r.json["error"]["mensaje"]
    assert api.estado["bitacora"] == []                                  # no se entrego nada
    assert api.pedir("/api/v1/reportes/devoluciones?formato=csv").status_code == 200


# --------------------------------------------------------------------------- validacion
@pytest.mark.parametrize("consulta", [
    "formato=docx", "desde=2026-13-01", "estado=inventado", "proveedor_id=abc", "tienda_id=-1",
    "desde=2026-11-02&hasta=2026-11-01", "no_existe=1", "pagina=0", "por_pagina=101",
])
def test_parametros_invalidos_400(api, consulta):
    assert api.pedir(f"/api/v1/reportes/devoluciones?{consulta}").status_code == 400


def test_reporte_inexistente_404(api):
    assert api.pedir("/api/v1/reportes/inventado").status_code == 404


def test_tendencia_exige_dimension_y_referencia_juntas_y_que_existan(api):
    assert api.pedir("/api/v1/reportes/tendencia?dimension=proveedor").status_code == 400
    assert api.pedir("/api/v1/reportes/tendencia?referencia_id=1").status_code == 400
    assert api.pedir("/api/v1/reportes/tendencia?dimension=proveedor&referencia_id=99").status_code == 404
    assert api.pedir("/api/v1/reportes/tendencia?dimension=proveedor&referencia_id=1").status_code == 200
    assert api.pedir("/api/v1/reportes/tendencia?meses=5").status_code == 400
    assert api.pedir("/api/v1/reportes/tendencia?meses=37").status_code == 400


# --------------------------------------------------------------------------- roles (RN-13, RN-15)
@pytest.mark.parametrize("rol", ["Cliente", "Inspector", "Coordinador de Logistica", "Recolector"])
def test_roles_sin_permiso_403(api, rol):
    for ruta in ("/api/v1/reportes", "/api/v1/reportes/devoluciones", "/api/v1/analitica/tendencias"):
        assert api.pedir(ruta, rol=rol).status_code == 403, (rol, ruta)


def test_alertas_de_fraude_solo_para_administrador_y_analista(api):
    assert api.pedir("/api/v1/analitica/alertas-fraude", rol="Analista de Devoluciones").status_code == 200
    assert api.pedir("/api/v1/analitica/alertas-fraude", rol="Administrador").status_code == 200
    for rol in ("Supervisor", "Encargado de Reembolsos"):
        assert api.pedir("/api/v1/analitica/alertas-fraude", rol=rol).status_code == 403
    assert api.pedir("/api/v1/reportes/costos", rol="Encargado de Reembolsos").status_code == 200


# --------------------------------------------------------------------------- graficas
def test_grafica_pareto_devuelve_opciones_de_highcharts(api):
    r = api.pedir("/api/v1/graficas/pareto?dimension=proveedor&medida=costo")
    assert r.status_code == 200
    o = r.json["opciones"]
    assert o["series"][0]["type"] == "column" and o["xAxis"]["categories"] == ["a", "b"]


def test_grafica_tendencia_trae_pronostico_alineado(api):
    r = api.pedir("/api/v1/graficas/tendencia?horizonte=2")
    s = {x["name"]: x["data"] for x in r.json["opciones"]["series"]}
    assert len(r.json["opciones"]["xAxis"]["categories"]) == 10
    assert r.json["opciones"]["xAxis"]["categories"][-2:] == ["2026-09", "2026-10"]
    assert set(s) == {"Observado", "Tendencia", "Pronostico", "Limite inferior", "Limite superior"}
    assert all(len(v) == 10 for v in s.values())


def test_graficas_solo_json_y_solo_las_conocidas(api):
    assert api.pedir("/api/v1/graficas/pareto", headers={"Accept": "application/xml"}).status_code == 406
    assert api.pedir("/api/v1/graficas/inventada").status_code == 404
    assert api.pedir("/api/v1/graficas/tendencia?horizonte=7").status_code == 400
    assert api.pedir("/api/v1/graficas/tendencia?horizonte=0").status_code == 400


# --------------------------------------------------------------------------- analitica
def test_tendencias_resume_la_direccion(api):
    r = api.pedir("/api/v1/analitica/tendencias?medida=tasa&dimension=proveedor&referencia_id=1")
    j = r.json
    assert r.status_code == 200 and j["objeto"] == "Lacteos" and len(j["serie"]) == 8
    assert j["tendencia"]["direccion"] == "sube" and j["tendencia"]["significativa"]


def test_pronosticos_etiqueta_los_meses_siguientes_y_da_referencia(api):
    r = api.pedir("/api/v1/analitica/pronosticos?horizonte=3")
    j = r.json
    assert [p["mes"] for p in j["pronostico"]["puntos"]] == ["2026-09", "2026-10", "2026-11"]
    assert j["pronostico"]["metodo"] == "regresion_lineal" and j["pronostico"]["confianza_pct"] == 95
    assert j["referencia_promedio_movil_3"] == 6.7          # promedio de 6, 6.1 y 8
    assert "no de hoy" in j["nota"]


def test_anomalias_de_objetos_marca_al_atipico(api):
    r = api.pedir("/api/v1/analitica/anomalias?tipo=objetos&por=proveedor")
    marcados = [d["etiqueta"] for d in r.json["datos"] if d["anomalia"]]
    assert r.status_code == 200 and marcados == ["P6"] and "z robusto" in r.json["metodo"]


def test_anomalias_de_meses_devuelve_el_mes_no_el_indice(api):
    r = api.pedir("/api/v1/analitica/anomalias?tipo=meses")
    assert r.status_code == 200 and "mes" in r.json["datos"][0] and "x" not in r.json["datos"][0]


def test_anomalias_rechaza_parametros_invalidos(api):
    assert api.pedir("/api/v1/analitica/anomalias?tipo=raros").status_code == 400
    assert api.pedir("/api/v1/analitica/anomalias?por=ruta").status_code == 400


# --------------------------------------------------------------------------- #
# Varios factores
# --------------------------------------------------------------------------- #
def _simular_cruce(monkeypatch, recibido=None):
    filas = [{"a_id": a, "a_etiqueta": f"P{a}", "b_id": b, "b_etiqueta": f"T{b}", "unidades_vendidas": 100,
              "unidades_devueltas": 40 if (a, b) == (1, 1) else 5, "devoluciones": 3} for a in (1, 2, 3) for b in (1, 2, 3)]

    def falso(a, b, desde, hasta):
        if recibido is not None:
            recibido.append((a, b, desde, hasta))
        return filas
    monkeypatch.setattr(datos, "tasas_cruzadas", falso)


def test_factores_marca_la_combinacion_y_explica_la_lectura(api, monkeypatch):
    _simular_cruce(monkeypatch)
    r = api.pedir("/api/v1/analitica/factores?por=proveedor&con=tienda")
    j = r.json
    assert r.status_code == 200 and (j["por"], j["con"], j["estado"]) == ("proveedor", "tienda", "ok")
    primera = j["celdas"][0]
    assert (primera["a_etiqueta"], primera["b_etiqueta"], primera["lectura"]) == ("P1", "T1", "combinacion")
    assert "RN-09" in j["nota"] and "Wilson" in j["metodo"] and j["total_celdas"] == 9


def test_factores_pasa_el_periodo_y_las_dimensiones_a_la_consulta(api, monkeypatch):
    recibido = []
    _simular_cruce(monkeypatch, recibido)
    api.pedir("/api/v1/analitica/factores?por=lote&con=producto&desde=2026-01-01&hasta=2026-06-30")
    assert recibido == [("lote", "producto", date(2026, 1, 1), date(2026, 6, 30))]


def test_factores_limite_y_solo_distinguibles(api, monkeypatch):
    _simular_cruce(monkeypatch)
    assert len(api.pedir("/api/v1/analitica/factores?limite=3").json["celdas"]) == 3
    solo = api.pedir("/api/v1/analitica/factores?solo_distinguibles=true").json
    assert solo["total_celdas"] == 1 and solo["celdas"][0]["distinguible"] is True


def test_factores_responde_xml(api, monkeypatch):
    _simular_cruce(monkeypatch)
    r = api.pedir("/api/v1/analitica/factores", headers={"Accept": "application/xml"})
    assert r.status_code == 200 and r.mimetype == "application/xml" and b"<factores>" in r.data


def test_factores_rechaza_parametros_invalidos(api, monkeypatch):
    _simular_cruce(monkeypatch)
    for consulta in ("por=ruta", "con=transportista", "por=tienda&con=tienda", "limite=0", "limite=101",
                     "solo_distinguibles=quizas", "desde=ayer", "desde=2026-06-01&hasta=2026-01-01", "raro=1"):
        assert api.pedir("/api/v1/analitica/factores?" + consulta).status_code == 400, consulta


def test_factores_solo_lo_ven_los_roles_de_lectura(api, monkeypatch):
    _simular_cruce(monkeypatch)
    for rol, esperado in (("Supervisor", 200), ("Encargado de Reembolsos", 200), ("Cliente", 403), ("Inspector", 403)):
        assert api.pedir("/api/v1/analitica/factores", rol=rol).status_code == esperado, rol
