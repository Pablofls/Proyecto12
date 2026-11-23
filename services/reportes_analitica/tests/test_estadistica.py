"""Estadistica de tendencias, pronosticos y anomalias. No necesita base de datos.

Trazabilidad: RF-23, RF-26, RN-09, RN-16.
"""
from datetime import date

import pytest

import estadistica as e

RECTA = [(i, 2 * i + 1) for i in range(6)]            # y = 2x + 1, sin ruido
PLANA = [(i, v) for i, v in enumerate([10, 12, 9, 11, 10, 12])]
SUBE = [(i, v) for i, v in enumerate([1, 2, 2.5, 4, 4.2, 6, 6.1, 8])]
BAJA = [(i, 10 - 2 * i) for i in range(6)]


def test_tasa():
    assert e.tasa(18, 96) == 18.75
    assert e.tasa(0, 0) is None and e.tasa(3, None) is None


# --------------------------------------------------------------------------- meses
def test_meses_sin_plazo_excluyen_el_mes_en_curso():
    assert e.meses_validos(date(2026, 11, 21), 3) == ["2026-08", "2026-09", "2026-10"]


def test_meses_con_plazo_excluyen_los_que_aun_pueden_recibir_devoluciones():
    # Octubre termina el 31/10: faltan 21 dias, menos que el plazo de 30; septiembre si maduro.
    assert e.meses_validos(date(2026, 11, 21), 3, 30) == ["2026-07", "2026-08", "2026-09"]


def test_mes_justo_en_el_limite_del_plazo():
    assert e.meses_validos(date(2026, 11, 30), 2, 30)[-1] == "2026-10"   # 31/10 + 30 dias = 30/11
    assert e.meses_validos(date(2026, 11, 29), 2, 30)[-1] == "2026-09"


def test_meses_cruzan_el_cambio_de_anio():
    assert e.meses_validos(date(2026, 1, 5), 3) == ["2025-10", "2025-11", "2025-12"]


def test_mes_anterior():
    assert e.mes_anterior(2026, 1) == (2025, 12)
    assert e.mes_anterior(2026, 3, 14) == (2025, 1)
    assert e.mes_anterior(2026, 12, -1) == (2027, 1)


# --------------------------------------------------------------------------- regresion
def test_recta_perfecta():
    a = e.ajustar(RECTA)
    assert (round(a["pendiente"], 6), round(a["intercepto"], 6), round(a["r2"], 6)) == (2.0, 1.0, 1.0)
    assert a["significativa"]


def test_serie_corta_no_tiene_tendencia():
    assert e.ajustar(RECTA[:5]) is None
    assert e.tendencia(RECTA[:5])["estado"] == "sin_datos"
    assert e.pronosticar(RECTA[:5], 3, 4)["estado"] == "sin_datos"


def test_serie_sin_variacion_en_x():
    assert e.ajustar([(1, 5)] * 8) is None


def test_ruido_no_es_tendencia():
    t = e.tendencia(PLANA)
    assert (t["estado"], t["direccion"], t["significativa"]) == ("ok", "estable", False)


def test_subida_clara():
    t = e.tendencia(SUBE)
    assert t["direccion"] == "sube" and t["significativa"] and t["pendiente_por_mes"] > 0.8


def test_bajada_clara():
    assert e.tendencia(BAJA)["direccion"] == "baja"


def test_serie_constante_es_estable():
    t = e.tendencia([(i, 5.0) for i in range(6)])
    assert t["direccion"] == "estable" and t["r2"] == 0.0


@pytest.mark.parametrize("gl,esperado", [(1, 12.706), (4, 2.776), (30, 2.042), (31, 2.0), (500, 2.0)])
def test_t_critico(gl, esperado):
    assert e.t_critico(gl) == esperado


# --------------------------------------------------------------------------- pronostico
def test_pronostico_de_recta_perfecta_no_tiene_banda():
    p = e.pronosticar(RECTA, 2, 5)
    assert [x["valor"] for x in p["puntos"]] == [13.0, 15.0]
    assert all(x["limite_inferior"] == x["valor"] == x["limite_superior"] for x in p["puntos"])
    assert p["confiable"] and p["confianza_pct"] == 95


def test_banda_se_ensancha_al_alejarse():
    p = e.pronosticar(SUBE, 3, 7)["puntos"]
    anchos = [x["limite_superior"] - x["limite_inferior"] for x in p]
    assert anchos[0] < anchos[1] < anchos[2]


def test_pronostico_no_baja_de_cero_ni_pasa_del_tope():
    bajando = e.pronosticar(BAJA, 3, 5)["puntos"]
    assert [x["valor"] for x in bajando] == [0.0, 0.0, 0.0]
    assert all(x["limite_inferior"] >= 0 for x in bajando)
    subiendo = e.pronosticar([(i, 90 + 2 * i) for i in range(6)], 3, 5, tope_superior=100.0)["puntos"]
    assert all(x["limite_superior"] <= 100.0 and x["valor"] <= 100.0 for x in subiendo)


def test_serie_ruidosa_no_es_confiable_y_lo_dice():
    p = e.pronosticar(PLANA, 2, 5)
    assert p["confiable"] is False and "no considera estacionalidad" in p["advertencia"]


def test_horizonte_se_limita():
    assert len(e.pronosticar(RECTA, 99, 5)["puntos"]) == e.MAX_HORIZONTE
    assert len(e.pronosticar(RECTA, 0, 5)["puntos"]) == 1


def test_promedio_movil():
    assert e.promedio_movil([1, 2, None, 4, 6, 8]) == 6.0
    assert e.promedio_movil([1, 2]) is None


# --------------------------------------------------------------------------- anomalias
def test_z_robusto_detecta_el_extremo_sin_que_este_esconda_a_los_demas():
    z = e.z_robusto([10, 11, 12, 13, 14, 50])
    assert z[-1] > 15 and all(abs(x) < 2 for x in z[:-1])


def test_z_robusto_con_mad_cero_usa_la_desviacion_media():
    z = e.z_robusto([1, 1, 1, 1, 10])
    assert z[:4] == [0.0] * 4 and z[4] >= e.UMBRAL_Z_ROBUSTO


def test_z_robusto_degenerados():
    assert e.z_robusto([]) == []
    assert e.z_robusto([5, 5, 5, 5]) == [0.0] * 4


def fila(i, vendidas, devueltas):
    return {"id": i, "etiqueta": f"Proveedor {i}", "unidades_vendidas": vendidas, "unidades_devueltas": devueltas}


def test_anomalias_de_objetos():
    filas = [fila(1, 100, 5), fila(2, 100, 6), fila(3, 100, 5), fila(4, 100, 4), fila(5, 100, 5),
             fila(6, 100, 40), fila(7, 10, 9)]
    r = e.anomalias_objetos(filas)
    assert r["estado"] == "ok" and r["omitidos_por_muestra"] == 1
    assert [d["etiqueta"] for d in r["datos"] if d["anomalia"]] == ["Proveedor 6"]
    assert r["datos"][0]["etiqueta"] == "Proveedor 6" and r["datos"][0]["direccion"] == "alta"
    assert "Proveedor 7" not in [d["etiqueta"] for d in r["datos"]]   # 10 unidades no se juzgan


def test_pocos_objetos_no_se_juzgan():
    r = e.anomalias_objetos([fila(1, 100, 5), fila(2, 100, 50), fila(3, 100, 6), fila(4, 100, 5)])
    assert r["estado"] == "sin_datos" and r["datos"] == []


def test_todos_iguales_no_hay_anomalia():
    r = e.anomalias_objetos([fila(i, 100, 5) for i in range(6)])
    assert r["estado"] == "ok" and not any(d["anomalia"] for d in r["datos"])


def test_anomalia_de_serie_ignora_la_tendencia():
    """Una serie que sube de forma regular no tiene meses anomalos; un pico si."""
    regular = [(i, 2 * i + 1 + (0.1 if i % 2 else -0.1)) for i in range(10)]
    assert not any(d["anomalia"] for d in e.anomalias_serie(regular)["datos"])
    con_pico = list(regular)
    con_pico[6] = (6, 60.0)
    marcados = [d["x"] for d in e.anomalias_serie(con_pico)["datos"] if d["anomalia"]]
    assert marcados == [6]


def test_anomalia_de_serie_corta_sin_datos():
    assert e.anomalias_serie(RECTA[:4])["estado"] == "sin_datos"


# --------------------------------------------------------------------------- pareto
def test_pareto_ordena_y_acumula():
    r = e.pareto([("b", 30, 3), ("a", 50, 5), ("c", 20, 2)])
    assert [c["etiqueta"] for c in r["categorias"]] == ["a", "b", "c"]
    assert [c["porcentaje"] for c in r["categorias"]] == [50.0, 30.0, 20.0]
    assert [c["porcentaje_acumulado"] for c in r["categorias"]] == [50.0, 80.0, 100.0]
    assert r["total_general"] == 100.0


def test_pareto_vacio_y_con_etiqueta_nula():
    assert e.pareto([]) == {"total_general": 0.0, "categorias": []}
    assert e.pareto([(None, 5, 1)])["categorias"][0]["etiqueta"] == "Sin dato"
    assert e.pareto([("a", 0, 0)])["categorias"][0]["porcentaje"] == 0.0


def test_pareto_desempata_por_nombre():
    assert [c["etiqueta"] for c in e.pareto([("z", 5, 1), ("a", 5, 1)])["categorias"]] == ["a", "z"]


# --------------------------------------------------------------------------- #
# Varios factores (analizar_cruce, intervalo de Wilson)
# --------------------------------------------------------------------------- #
def _cruce(celdas):
    """celdas: {(a, b): (vendidas, devueltas)} -> filas como las entrega datos.tasas_cruzadas."""
    return [{"a_id": a, "a_etiqueta": f"P{a}", "b_id": b, "b_etiqueta": f"T{b}", "unidades_vendidas": v,
             "unidades_devueltas": d, "devoluciones": d} for (a, b), (v, d) in celdas.items()]


def _rejilla(modificaciones=None, vendidas=100, base=5):
    celdas = {(a, b): (vendidas, base) for a in (1, 2, 3) for b in (1, 2, 3)}
    celdas.update(modificaciones or {})
    return celdas


def test_wilson_acota_la_tasa_y_se_estrecha_con_mas_muestra():
    bajo, alto = e.intervalo_wilson(16, 24)
    assert bajo < 16 / 24 * 100 < alto and 46 < bajo < 47 and 82 < alto < 83     # valores reproducibles a mano
    ancho_chico = e.intervalo_wilson(10, 100)
    ancho_grande = e.intervalo_wilson(100, 1000)
    assert ancho_grande[1] - ancho_grande[0] < ancho_chico[1] - ancho_chico[0]


def test_wilson_con_cero_devoluciones_no_baja_de_cero_y_sin_ventas_no_hay_intervalo():
    assert e.intervalo_wilson(0, 50)[0] == 0.0 and e.intervalo_wilson(0, 50)[1] > 0
    assert e.intervalo_wilson(5, 0) is None


def test_una_combinacion_que_supera_a_sus_dos_factores_se_lee_como_combinacion():
    r = e.analizar_cruce(_cruce(_rejilla({(1, 1): (100, 40)})))
    cabeza = r["celdas"][0]
    assert r["estado"] == "ok" and (cabeza["a_etiqueta"], cabeza["b_etiqueta"]) == ("P1", "T1")
    assert cabeza["distinguible"] and cabeza["lectura"] == "combinacion"
    assert r["distinguibles"] == 1 and all(c["lectura"] is None for c in r["celdas"][1:])


def test_si_todo_un_factor_esta_alto_el_exceso_se_atribuye_a_ese_factor():
    celdas = _rejilla({(1, 1): (100, 30), (1, 2): (100, 30), (1, 3): (100, 30)})   # P1 en todas las tiendas
    r = e.analizar_cruce(_cruce(celdas))
    asignadas = {(c["a_etiqueta"], c["b_etiqueta"]): c["lectura"] for c in r["celdas"] if c["distinguible"]}
    assert asignadas and set(asignadas.values()) == {"factor_a"}
    assert {a for a, _ in asignadas} == {"P1"}


def test_si_todo_el_segundo_factor_esta_alto_se_atribuye_al_segundo():
    celdas = _rejilla({(1, 2): (100, 30), (2, 2): (100, 30), (3, 2): (100, 30)})   # la tienda T2 en todos los proveedores
    r = e.analizar_cruce(_cruce(celdas))
    assert {c["lectura"] for c in r["celdas"] if c["distinguible"]} == {"factor_b"}


def test_las_combinaciones_con_poca_muestra_no_se_juzgan_aunque_su_tasa_sea_enorme():
    r = e.analizar_cruce(_cruce(_rejilla({(1, 1): (4, 4)})))        # 100 % de 4 unidades: ruido
    assert r["omitidas_por_muestra"] == 1
    assert all((c["a_etiqueta"], c["b_etiqueta"]) != ("P1", "T1") for c in r["celdas"])


def test_sin_devoluciones_o_sin_muestra_dice_sin_datos_y_por_que():
    assert e.analizar_cruce(_cruce(_rejilla(base=0)))["estado"] == "sin_datos"
    pocas = e.analizar_cruce(_cruce(_rejilla(vendidas=10)))
    assert pocas["estado"] == "sin_datos" and "20 unidades" in pocas["motivo"] and pocas["omitidas_por_muestra"] == 9
    assert e.analizar_cruce([])["estado"] == "sin_datos"


def test_una_rejilla_pareja_no_marca_nada_y_las_celdas_salen_de_mayor_a_menor_tasa():
    r = e.analizar_cruce(_cruce(_rejilla({(2, 2): (100, 8)})))
    assert r["distinguibles"] == 0
    tasas = [c["tasa_pct"] for c in r["celdas"]]
    assert tasas == sorted(tasas, reverse=True) and r["celdas"][0]["tasa_pct"] == 8.0


def test_la_celda_trae_sus_tasas_por_factor_y_su_intervalo():
    r = e.analizar_cruce(_cruce(_rejilla({(1, 1): (100, 40)})))
    c = r["celdas"][0]
    assert c["tasa_factor_a_pct"] == round((40 + 5 + 5) / 300 * 100, 2) and c["tasa_factor_b_pct"] == c["tasa_factor_a_pct"]
    assert c["intervalo_95_pct"]["bajo"] < c["tasa_pct"] < c["intervalo_95_pct"]["alto"]
    assert c["veces_promedio"] == round(c["tasa_pct"] / r["tasa_promedio_pct"], 2)
