"""Estadistica explicable de tendencias, pronosticos y anomalias (sin base de datos).

Todo se calcula con la biblioteca estandar (statistics) y se puede reproducir a
mano: regresion lineal por minimos cuadrados, intervalo de prediccion del 95 %
y puntaje z robusto (mediana y MAD). Nada aqui decide una causa: son senales
para revision humana (RN-09).

Tres cuidados que evitan conclusiones falsas:
 - Una serie corta no tiene tendencia: se exigen al menos 6 puntos.
 - Un mes de ventas todavia puede recibir devoluciones; contarlo hace parecer
   que la tasa baja. `meses_validos` descarta los que aun no maduran.
 - Con poca muestra una tasa es ruido: los puntos con menos de 20 unidades
   vendidas no entran a la regresion.

Para varios factores a la vez (`analizar_cruce`) se usa el intervalo de Wilson del 95 %:
una combinacion solo se llama "distinguible" si el extremo bajo de su intervalo supera
la tasa promedio, asi una celda con pocas ventas no parece culpable por azar.

Trazabilidad: RF-23, RF-24, RF-26, RN-09, RN-16.
"""
import math
import statistics
from datetime import date, timedelta

MIN_PUNTOS = 6
MIN_UNIDADES = 20
MIN_OBJETOS_ANOMALIA = 5
UMBRAL_Z_ROBUSTO = 3.5          # Iglewicz y Hoaglin
R2_CONFIABLE = 0.3
MAX_HORIZONTE = 6
# t de Student, 95 % a dos colas, para 1 a 30 grados de libertad.
T_95 = (12.706, 4.303, 3.182, 2.776, 2.571, 2.447, 2.365, 2.306, 2.262, 2.228,
        2.201, 2.179, 2.160, 2.145, 2.131, 2.120, 2.110, 2.101, 2.093, 2.086,
        2.080, 2.074, 2.069, 2.064, 2.060, 2.056, 2.052, 2.048, 2.045, 2.042)


def t_critico(grados):
    """Con mas de 30 grados se usa 2.0, un poco conservador frente a 1.96."""
    if grados < 1:
        return float("inf")
    return T_95[grados - 1] if grados <= 30 else 2.0


def tasa(devueltas, vendidas):
    vendidas = float(vendidas or 0)
    if vendidas <= 0:
        return None
    return round(float(devueltas or 0) * 100.0 / vendidas, 2)


# --------------------------------------------------------------------------- #
# Meses
# --------------------------------------------------------------------------- #
def _fin_de_mes(anio, mes):
    siguiente = date(anio + (mes == 12), mes % 12 + 1, 1)
    return siguiente - timedelta(days=1)


def mes_anterior(anio, mes, cuantos=1):
    total = anio * 12 + (mes - 1) - cuantos
    return total // 12, total % 12 + 1


def meses_validos(hoy, cantidad, plazo_dias=None):
    """Los ultimos `cantidad` meses utilizables, del mas antiguo al mas reciente ('AAAA-MM').

    Sin plazo (devoluciones y costo por fecha de solicitud) basta que el mes haya
    terminado. Con plazo (tasa por cohorte de venta) el mes debe haber terminado
    hace al menos `plazo_dias`: antes de eso sus ultimas ventas aun pueden devolverse.
    """
    anio, mes = mes_anterior(hoy.year, hoy.month)  # el mes en curso nunca esta completo
    if plazo_dias:
        corte = hoy - timedelta(days=plazo_dias)
        while _fin_de_mes(anio, mes) > corte:
            anio, mes = mes_anterior(anio, mes)
    return [f"{a:04d}-{m:02d}" for a, m in
            (mes_anterior(anio, mes, cantidad - 1 - i) for i in range(cantidad))]


# --------------------------------------------------------------------------- #
# Tendencia y pronostico
# --------------------------------------------------------------------------- #
def ajustar(puntos):
    """Regresion lineal y = a + b x sobre [(x, y)]; None si no hay suficientes puntos."""
    if len(puntos) < MIN_PUNTOS or len({x for x, _ in puntos}) < 2:
        return None
    xs, ys = [p[0] for p in puntos], [p[1] for p in puntos]
    n = len(puntos)
    pendiente, intercepto = statistics.linear_regression(xs, ys)
    ajustados = [intercepto + pendiente * x for x in xs]
    sse = sum((y - f) ** 2 for y, f in zip(ys, ajustados))
    sst = sum((y - statistics.fmean(ys)) ** 2 for y in ys)
    sxx = sum((x - statistics.fmean(xs)) ** 2 for x in xs)
    r2 = 0.0 if sst == 0 else max(0.0, 1.0 - sse / sst)
    error = math.sqrt(sse / (n - 2))
    se_pendiente = error / math.sqrt(sxx) if sxx else float("inf")
    if se_pendiente == 0:  # ajuste perfecto
        t = math.inf if pendiente != 0 else 0.0
    else:
        t = pendiente / se_pendiente
    return {"n": n, "pendiente": pendiente, "intercepto": intercepto, "r2": r2,
            "error_estandar": error, "sxx": sxx, "x_media": statistics.fmean(xs),
            "t": t, "significativa": abs(t) >= t_critico(n - 2),
            "ajustados": ajustados}


def tendencia(puntos):
    """Direccion de la serie con su respaldo estadistico, en lenguaje llano."""
    ajuste = ajustar(puntos)
    if ajuste is None:
        return {"estado": "sin_datos",
                "motivo": f"Se requieren al menos {MIN_PUNTOS} meses con datos suficientes."}
    if not ajuste["significativa"]:
        direccion = "estable"
    else:
        direccion = "sube" if ajuste["pendiente"] > 0 else "baja"
    return {"estado": "ok", "direccion": direccion, "meses_usados": ajuste["n"],
            "pendiente_por_mes": round(ajuste["pendiente"], 4), "r2": round(ajuste["r2"], 3),
            "significativa": ajuste["significativa"],
            "interpretacion": ("El cambio mes a mes es estadisticamente distinguible del ruido."
                               if ajuste["significativa"] else
                               "No hay evidencia suficiente de que la serie suba o baje.")}


def pronosticar(puntos, horizonte, ultimo_x, tope_superior=None):
    """Proyeccion lineal con intervalo de prediccion del 95 %.

    Es una extrapolacion: orienta, no garantiza. `confiable` solo es verdadero
    si la recta explica al menos 30 % de la variacion. Los limites no bajan de 0
    (una tasa, un conteo o un costo no son negativos).
    """
    ajuste = ajustar(puntos)
    if ajuste is None:
        return {"estado": "sin_datos",
                "motivo": f"Se requieren al menos {MIN_PUNTOS} meses con datos suficientes.",
                "puntos": []}
    horizonte = max(1, min(int(horizonte), MAX_HORIZONTE))
    t = t_critico(ajuste["n"] - 2)
    salida = []
    for paso in range(1, horizonte + 1):
        x = ultimo_x + paso
        centro = ajuste["intercepto"] + ajuste["pendiente"] * x
        amplitud = t * ajuste["error_estandar"] * math.sqrt(
            1 + 1 / ajuste["n"] + (x - ajuste["x_media"]) ** 2 / ajuste["sxx"])
        bajo, alto = max(0.0, centro - amplitud), centro + amplitud
        centro = max(0.0, centro)
        if tope_superior is not None:
            centro, alto, bajo = (min(v, tope_superior) for v in (centro, alto, bajo))
        salida.append({"paso": paso, "valor": round(centro, 2),
                       "limite_inferior": round(bajo, 2), "limite_superior": round(alto, 2)})
    return {"estado": "ok", "metodo": "regresion_lineal", "confianza_pct": 95,
            "meses_usados": ajuste["n"], "r2": round(ajuste["r2"], 3),
            "confiable": ajuste["r2"] >= R2_CONFIABLE, "puntos": salida,
            "advertencia": ("Extrapolacion lineal de la serie historica; no considera estacionalidad "
                            "ni cambios futuros. Usala como referencia, no como compromiso.")}


def promedio_movil(valores, ventana=3):
    """Pronostico plano de referencia: el promedio de los ultimos puntos."""
    validos = [v for v in valores if v is not None][-ventana:]
    if len(validos) < ventana:
        return None
    return round(statistics.fmean(validos), 2)


# --------------------------------------------------------------------------- #
# Anomalias
# --------------------------------------------------------------------------- #
def z_robusto(valores):
    """Puntaje z con mediana y MAD: un valor extremo no esconde a los demas.

    z = 0.6745 (x - mediana) / MAD. Si el MAD es 0 (mas de la mitad de los valores
    iguales) se usa la desviacion media absoluta, z = (x - mediana) / (1.253314 DMA).
    Con todos iguales no hay anomalia posible y devuelve ceros.
    """
    if not valores:
        return []
    mediana = statistics.median(valores)
    mad = statistics.median(abs(v - mediana) for v in valores)
    if mad > 0:
        return [0.6745 * (v - mediana) / mad for v in valores]
    dma = statistics.fmean(abs(v - mediana) for v in valores)
    if dma == 0:
        return [0.0] * len(valores)
    return [(v - mediana) / (1.253314 * dma) for v in valores]


def anomalias_objetos(filas):
    """Objetos con una tasa atipica frente a sus pares.

    filas: dicts con id, etiqueta, unidades_vendidas, unidades_devueltas. Los que
    tienen menos de 20 unidades no se juzgan (su tasa es ruido) y se listan aparte.
    """
    juzgables = [f for f in filas if f["unidades_vendidas"] >= MIN_UNIDADES]
    omitidos = len(filas) - len(juzgables)
    if len(juzgables) < MIN_OBJETOS_ANOMALIA:
        return {"estado": "sin_datos", "omitidos_por_muestra": omitidos,
                "motivo": f"Se requieren al menos {MIN_OBJETOS_ANOMALIA} objetos con {MIN_UNIDADES} unidades vendidas o mas.",
                "datos": []}
    tasas = [tasa(f["unidades_devueltas"], f["unidades_vendidas"]) for f in juzgables]
    zs = z_robusto(tasas)
    mediana = statistics.median(tasas)
    datos = []
    for f, t, z in zip(juzgables, tasas, zs):
        datos.append({"id": f["id"], "etiqueta": f["etiqueta"], "unidades_vendidas": f["unidades_vendidas"],
                      "unidades_devueltas": f["unidades_devueltas"], "tasa_pct": t, "z_robusto": round(z, 2),
                      "anomalia": abs(z) >= UMBRAL_Z_ROBUSTO,
                      "direccion": "alta" if z > 0 else "baja" if z < 0 else "normal"})
    datos.sort(key=lambda d: (-abs(d["z_robusto"]), d["etiqueta"]))
    return {"estado": "ok", "tasa_mediana_pct": round(mediana, 2), "umbral_z": UMBRAL_Z_ROBUSTO,
            "omitidos_por_muestra": omitidos, "datos": datos}


def anomalias_serie(puntos):
    """Meses atipicos frente a la tendencia de la propia serie (por residuos)."""
    ajuste = ajustar(puntos)
    if ajuste is None:
        return {"estado": "sin_datos",
                "motivo": f"Se requieren al menos {MIN_PUNTOS} meses con datos suficientes.", "datos": []}
    residuos = [y - f for (_, y), f in zip(puntos, ajuste["ajustados"])]
    zs = z_robusto(residuos)
    datos = [{"x": x, "valor": round(y, 2), "esperado": round(f, 2), "z_robusto": round(z, 2),
              "anomalia": abs(z) >= UMBRAL_Z_ROBUSTO}
             for (x, y), f, z in zip(puntos, ajuste["ajustados"], zs)]
    return {"estado": "ok", "umbral_z": UMBRAL_Z_ROBUSTO, "datos": datos}


# --------------------------------------------------------------------------- #
# Varios factores: cruce de dos dimensiones
# --------------------------------------------------------------------------- #
Z_95 = 1.96
LECTURAS = {
    "combinacion": "La tasa de esta combinacion supera a la de cada factor por separado: el problema parece concentrarse en esa combinacion.",
    "factor_a": "El primer factor ya tiene una tasa alta en conjunto y el segundo no: el exceso parece venir del primero.",
    "factor_b": "El segundo factor ya tiene una tasa alta en conjunto y el primero no: el exceso parece venir del segundo.",
    "ambos_factores": "Los dos factores tienen una tasa alta por separado: hay que revisar los dos antes de asignar el exceso a uno.",
    "sin_atribucion": "La combinacion destaca, pero ningun factor por separado explica el exceso con esta muestra.",
}


def intervalo_wilson(exitos, n, z=Z_95):
    """Intervalo de confianza (%) de una proporcion; cada unidad vendida se devuelve o no.

    Es mas confiable que el normal simple con pocas unidades o tasas cercanas a 0 o 100.
    """
    if n <= 0:
        return None
    p = min(max(float(exitos), 0.0), float(n)) / n
    denominador = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / denominador
    mitad = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominador
    return round(max(0.0, centro - mitad) * 100, 2), round(min(1.0, centro + mitad) * 100, 2)


def _bajo_wilson(devueltas, vendidas):
    intervalo = intervalo_wilson(devueltas, vendidas)
    return intervalo[0] if intervalo else None


def analizar_cruce(filas, min_unidades=MIN_UNIDADES):
    """Cruza dos factores: tasa de cada combinacion y de donde parece venir el exceso.

    filas: dicts con a_id, a_etiqueta, b_id, b_etiqueta, unidades_vendidas, unidades_devueltas, devoluciones.
    Una combinacion con menos de `min_unidades` vendidas no se juzga (su tasa es ruido). Para las que si:
      - `distinguible`: el extremo bajo del intervalo de Wilson 95 % supera la tasa promedio global;
      - `lectura`: si la combinacion supera a ambos factores por separado es una `combinacion`; si no,
        se atribuye al factor cuya tasa conjunta ya es distinguible, a `ambos_factores` o a `sin_atribucion`.
    No determina causas: orienta donde investigar (RN-09).
    """
    vendidas = sum(f["unidades_vendidas"] for f in filas)
    devueltas = sum(f["unidades_devueltas"] for f in filas)
    promedio = tasa(devueltas, vendidas)
    if not promedio:
        return {"estado": "sin_datos", "motivo": "No hay devoluciones que analizar en el periodo.",
                "omitidas_por_muestra": len(filas), "celdas": []}
    margen_a, margen_b = {}, {}
    for f in filas:
        for margen, clave in ((margen_a, f["a_id"]), (margen_b, f["b_id"])):
            acumulado = margen.setdefault(clave, [0, 0])
            acumulado[0] += f["unidades_vendidas"]
            acumulado[1] += f["unidades_devueltas"]

    def destaca(v, d):
        bajo = _bajo_wilson(d, v) if v >= min_unidades else None
        return bajo is not None and bajo > promedio

    celdas, omitidas = [], 0
    for f in filas:
        v, d = f["unidades_vendidas"], f["unidades_devueltas"]
        if v < min_unidades:
            omitidas += 1
            continue
        bajo, alto = intervalo_wilson(d, v)
        t = tasa(d, v)
        va, da = margen_a[f["a_id"]]
        vb, db = margen_b[f["b_id"]]
        distinguible = bajo > promedio
        lectura = None
        if distinguible:
            if bajo > max(tasa(da, va) or 0, tasa(db, vb) or 0):
                lectura = "combinacion"
            elif destaca(va, da) and destaca(vb, db):
                lectura = "ambos_factores"
            elif destaca(va, da):
                lectura = "factor_a"
            elif destaca(vb, db):
                lectura = "factor_b"
            else:
                lectura = "sin_atribucion"
        celdas.append({"a_id": f["a_id"], "a_etiqueta": f["a_etiqueta"], "b_id": f["b_id"], "b_etiqueta": f["b_etiqueta"],
                       "unidades_vendidas": v, "unidades_devueltas": d, "devoluciones": f.get("devoluciones", 0),
                       "tasa_pct": t, "veces_promedio": round(t / promedio, 2),
                       "intervalo_95_pct": {"bajo": bajo, "alto": alto},
                       "tasa_factor_a_pct": tasa(da, va), "tasa_factor_b_pct": tasa(db, vb),
                       "distinguible": distinguible, "lectura": lectura,
                       "lectura_texto": LECTURAS.get(lectura)})
    if not celdas:
        return {"estado": "sin_datos", "tasa_promedio_pct": promedio, "omitidas_por_muestra": omitidas,
                "motivo": f"Ninguna combinacion llega a {min_unidades} unidades vendidas.", "celdas": []}
    celdas.sort(key=lambda c: (-c["tasa_pct"], str(c["a_etiqueta"]), str(c["b_etiqueta"])))
    return {"estado": "ok", "tasa_promedio_pct": promedio, "muestra_minima_unidades": min_unidades,
            "omitidas_por_muestra": omitidas, "distinguibles": sum(1 for c in celdas if c["distinguible"]),
            "celdas": celdas}


# --------------------------------------------------------------------------- #
# Pareto
# --------------------------------------------------------------------------- #
def pareto(filas):
    """filas: [(etiqueta, total, casos)] -> categorias con % y % acumulado, de mayor a menor."""
    ordenadas = sorted(filas, key=lambda f: (-float(f[1]), str(f[0])))
    total = sum(float(f[1]) for f in ordenadas)
    acumulado, salida = 0.0, []
    for etiqueta, valor, casos in ordenadas:
        valor = float(valor)
        acumulado += valor
        salida.append({"etiqueta": str(etiqueta or "Sin dato"), "total": round(valor, 2), "casos": int(casos),
                       "porcentaje": round(valor / total * 100, 2) if total else 0.0,
                       "porcentaje_acumulado": round(acumulado / total * 100, 2) if total else 0.0})
    return {"total_general": round(total, 2), "categorias": salida}
