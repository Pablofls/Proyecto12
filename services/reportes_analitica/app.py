"""Reportes y analitica (dominios 18 y 19 del tercer parcial).

- Reportes tabulares en JSON, XML, CSV, Excel y PDF (RF-28). Los archivos se
  escriben con la biblioteca estandar (ver formatos.py).
- Datos listos para Highcharts (pareto, tendencia, tasas).
- Tendencias, pronosticos y anomalias con estadistica explicable (RN-09).
- Analisis de varios factores: cruza dos dimensiones y dice donde se concentra la tasa (GET /analitica/factores).
- Pareto y alertas de posible fraude, que antes vivian solo en analisis-auditoria.

Es de solo lectura: no escribe en el expediente. Cada descarga queda en la
bitacora con el reporte, el formato y el numero de filas, nunca con los datos.
Las series de tasa usan solo meses cuyas ventas ya cumplieron el plazo de
devolucion y los meses con menos de 20 unidades no se interpretan: una tasa
con pocas ventas es ruido.

Trazabilidad: RF-23, RF-24, RF-25, RF-26, RF-28, RN-09, RN-15, RNF-11, RNF-16.
"""
import os
from datetime import date, datetime, timezone

from flask import Blueprint, Flask, Response, g, request

import datos
import estadistica
import formatos
import graficas
from shared import docs, respuestas
from shared.infra import (cerrar_conexion, limitar, registrar_bitacora, salud_postgres, salud_redis)
from shared.paginacion import leer_paginacion, paginar
from shared.respuestas import ErrorApi, responder
from shared.seguridad import ADMINISTRADOR, ANALISTA, ENCARGADO_REEMBOLSOS, SUPERVISOR, requiere_jwt

NOMBRE = "reportes-analitica"
reportes = Blueprint("reportes", __name__, url_prefix="/api/v1/reportes")
grafica = Blueprint("graficas", __name__, url_prefix="/api/v1/graficas")
analitica = Blueprint("analitica", __name__, url_prefix="/api/v1/analitica")

LECTORES = (ADMINISTRADOR, ANALISTA, SUPERVISOR, ENCARGADO_REEMBOLSOS)
SOLO_ANALISIS = (ADMINISTRADOR, ANALISTA)  # las alertas de fraude nombran clientes (RN-15)
ESTADOS_DEV = ("solicitada", "en_revision", "autorizada", "rechazada", "en_recoleccion",
               "recibida", "en_inspeccion", "resuelta", "cerrada")
MEDIDAS_SERIE = ("tasa", "devoluciones", "costo")
FORMATOS = ("json",) + tuple(formatos.FORMATOS)

# nombre -> (titulo, filtros, roles). filtro: (nombre, tipo, opciones/limites, valor por omision)
CATALOGO = {
    "devoluciones": ("Reporte de devoluciones",
                     [("desde", "fecha", None, None), ("hasta", "fecha", None, None),
                      ("estado", "enum", ESTADOS_DEV, None), ("proveedor_id", "entero", None, None),
                      ("tienda_id", "entero", None, None)], LECTORES),
    "costos": ("Costos por devolucion y etapa",
               [("desde", "fecha", None, None), ("hasta", "fecha", None, None)], LECTORES),
    "tasas": ("Tasa de devolucion",
              [("por", "enum", tuple(datos.DIMENSIONES_TASA), "proveedor"),
               ("desde", "fecha", None, None), ("hasta", "fecha", None, None)], LECTORES),
    "pareto": ("Pareto de devoluciones",
               [("dimension", "enum", datos.DIMENSIONES_PARETO, "motivo"),
                ("medida", "enum", tuple(datos.MEDIDAS_PARETO), "frecuencia"),
                ("desde", "fecha", None, None), ("hasta", "fecha", None, None)], LECTORES),
    "tendencia": ("Tendencia mensual",
                  [("medida", "enum", MEDIDAS_SERIE, "tasa"), ("meses", "entero", (6, 36), 12),
                   ("dimension", "enum", tuple(datos.COLUMNA_OBJETO), None),
                   ("referencia_id", "entero", None, None)], LECTORES),
}
PARAMETROS_COMUNES = {"formato", "pagina", "por_pagina"}


# --------------------------------------------------------------------------- #
# Lectura de filtros
# --------------------------------------------------------------------------- #
def _leer_filtros(especificacion, extras=()):
    permitidos = {f[0] for f in especificacion} | PARAMETROS_COMUNES | set(extras)
    desconocidos = set(request.args) - permitidos
    if desconocidos:
        raise ErrorApi(400, "validacion", "Parametros desconocidos.",
                       [{"campo": c, "problema": "no existe para este reporte"} for c in sorted(desconocidos)])
    valores = {}
    for nombre, tipo, opciones, defecto in especificacion:
        bruto = request.args.get(nombre)
        if bruto in (None, ""):
            valores[nombre] = defecto
            continue
        if tipo == "fecha":
            try:
                valores[nombre] = date.fromisoformat(bruto)
            except ValueError:
                raise ErrorApi(400, "validacion", f"{nombre} debe tener formato AAAA-MM-DD.")
        elif tipo == "enum":
            if bruto not in opciones:
                raise ErrorApi(400, "validacion", f"{nombre} debe ser uno de: " + ", ".join(opciones) + ".")
            valores[nombre] = bruto
        else:
            minimo, maximo = opciones or (1, 10 ** 9)
            if not bruto.isdigit() or not minimo <= int(bruto) <= maximo:
                raise ErrorApi(400, "validacion", f"{nombre} debe ser un entero entre {minimo} y {maximo}.")
            valores[nombre] = int(bruto)
    desde, hasta = valores.get("desde"), valores.get("hasta")
    if desde and hasta and hasta < desde:
        raise ErrorApi(400, "validacion", "hasta no puede ser menor que desde.")
    return valores


def _objeto(valores):
    """dimension + referencia_id van juntas y el objeto debe existir."""
    dimension, ref = valores.get("dimension"), valores.get("referencia_id")
    if (dimension is None) != (ref is None):
        raise ErrorApi(400, "validacion", "dimension y referencia_id se indican juntas.")
    if dimension and datos.etiqueta_objeto(dimension, ref) is None:
        raise ErrorApi(404, "no_encontrado", f"No existe {dimension} con ese id.")
    return dimension, ref


def _texto_filtros(valores):
    partes = [f"{k}={v}" for k, v in valores.items() if v is not None]
    return ", ".join(partes) if partes else "sin filtros"


# --------------------------------------------------------------------------- #
# Construccion de cada reporte
# --------------------------------------------------------------------------- #
def _filas_tendencia(valores):
    dimension, ref = _objeto(valores)
    puntos = datos.serie_mensual(valores["medida"], valores["meses"], dimension, ref)
    return puntos


def _construir(nombre, v):
    if nombre == "devoluciones":
        filas = datos.reporte_devoluciones(v["desde"], v["hasta"], v["estado"], v["proveedor_id"], v["tienda_id"])
    elif nombre == "costos":
        filas = datos.reporte_costos(v["desde"], v["hasta"])
    elif nombre == "tasas":
        filas = datos.tasas_por(v["por"], v["desde"], v["hasta"])
    elif nombre == "pareto":
        filas = datos.pareto(v["dimension"], v["medida"], v["desde"], v["hasta"])["categorias"]
    else:
        filas = _filas_tendencia(v)
    return datos.COLUMNAS[nombre], filas


def _descarga(contenido, formato, nombre):
    mime, ext = formatos.FORMATOS[formato]
    cabeceras = {"Content-Disposition": f'attachment; filename="reporte_{nombre}_{date.today():%Y%m%d}.{ext}"',
                 # Datos de negocio: ni cache ni que el navegador adivine otro tipo.
                 "Cache-Control": "no-store", "X-Content-Type-Options": "nosniff"}
    return Response(contenido, content_type=mime, headers=cabeceras)


@reportes.get("")
@requiere_jwt(*LECTORES)
def catalogo():
    lista = [{"nombre": n, "titulo": t, "formatos": list(FORMATOS),
              "filtros": [{"nombre": f[0], "tipo": f[1], "opciones": list(f[2]) if f[1] == "enum" else None,
                           "por_omision": f[3]} for f in filtros]}
             for n, (t, filtros, _) in CATALOGO.items()]
    return responder({"datos": lista, "total": len(lista)}, raiz="reportes")


@reportes.get("/<nombre>")
@requiere_jwt(*LECTORES)
def reporte(nombre):
    if nombre not in CATALOGO:
        raise ErrorApi(404, "no_encontrado", "No existe ese reporte.")
    titulo, especificacion, roles = CATALOGO[nombre]
    if g.usuario["rol"] not in roles:
        raise ErrorApi(403, "sin_permiso", "Tu rol no puede consultar este reporte.")
    formato = request.args.get("formato", "json")
    if formato not in FORMATOS:
        raise ErrorApi(400, "validacion", "formato debe ser: " + ", ".join(FORMATOS) + ".")
    valores = _leer_filtros(especificacion)
    if formato != "json":
        # Un archivo cuesta mas que una pagina; se limita por usuario (RNF-13).
        limitar("exportar_reporte", 20, 60, sujeto=str(g.usuario["id"]))
    columnas, filas = _construir(nombre, valores)
    generado = datetime.now(timezone.utc).replace(microsecond=0)
    filtros_txt = _texto_filtros(valores)

    if formato == "json":
        pag = leer_paginacion()
        pagina = filas[pag.desplazamiento:pag.desplazamiento + pag.limite]
        cuerpo = paginar(pagina, len(filas), pag)
        return responder({"reporte": nombre, "titulo": titulo, "generado_en": generado.isoformat(),
                          "filtros": {k: (v.isoformat() if isinstance(v, date) else v)
                                      for k, v in valores.items() if v is not None},
                          "columnas": [{"clave": c[0], "titulo": c[1], "tipo": c[2]} for c in columnas],
                          **cuerpo}, raiz="reporte")
    try:
        if formato == "csv":
            contenido = formatos.a_csv(columnas, filas)
        elif formato == "xlsx":
            contenido = formatos.a_xlsx(titulo, columnas, filas,
                                        [("Generado", generado.isoformat()), ("Filtros", filtros_txt),
                                         ("Filas", str(len(filas))),
                                         ("Nota", "Informacion para revision humana; no determina causas.")])
        else:
            contenido = formatos.a_pdf(titulo, [f"Generado: {generado:%Y-%m-%d %H:%M} UTC",
                                                f"Filtros: {filtros_txt}", f"Filas: {len(filas)}"],
                                       columnas, filas)
    except formatos.DemasiadasFilas as exc:
        raise ErrorApi(422, "demasiadas_filas",
                       f"El reporte tiene {exc.filas} filas y {exc.formato} admite "
                       f"{formatos.MAX_FILAS[exc.formato]}. Acota el periodo con desde y hasta.")
    registrar_bitacora("exportar_reporte", "reportes", None,
                       f"{nombre} {formato} filas={len(filas)} filtros={filtros_txt}")
    return _descarga(contenido, formato, nombre)


# --------------------------------------------------------------------------- #
# Graficas para Highcharts
# --------------------------------------------------------------------------- #
def _solo_json():
    if respuestas.quiere_xml():
        raise ErrorApi(406, "solo_json", "Las opciones de Highcharts solo se entregan en JSON.")


def _meses_siguientes(ultimo_mes, cantidad):
    anio, mes = int(ultimo_mes[:4]), int(ultimo_mes[5:])
    salida = []
    for _ in range(cantidad):
        anio, mes = estadistica.mes_anterior(anio, mes, -1)
        salida.append(f"{anio:04d}-{mes:02d}")
    return salida


def _puntos_regresion(puntos):
    return [(i, p["valor"]) for i, p in enumerate(puntos) if p["valor"] is not None]


@grafica.get("/<nombre>")
@requiere_jwt(*LECTORES)
def grafica_highcharts(nombre):
    _solo_json()
    if nombre not in ("pareto", "tendencia", "tasas"):
        raise ErrorApi(404, "no_encontrado", "Graficas disponibles: pareto, tendencia, tasas.")
    titulo, especificacion, _ = CATALOGO[nombre]
    valores = _leer_filtros(especificacion, extras=("horizonte",))
    if nombre == "pareto":
        resultado = datos.pareto(valores["dimension"], valores["medida"], valores["desde"], valores["hasta"])
        opciones = graficas.pareto_opciones(f"Pareto por {valores['dimension']}", resultado, valores["medida"])
    elif nombre == "tasas":
        filas = datos.tasas_por(valores["por"], valores["desde"], valores["hasta"])
        opciones = graficas.tasas_opciones(f"Tasa de devolucion por {valores['por']}", filas)
    else:
        dimension, ref = _objeto(valores)
        puntos = datos.serie_mensual(valores["medida"], valores["meses"], dimension, ref)
        horizonte = _horizonte()
        regresion = _puntos_regresion(puntos)
        pron = estadistica.pronosticar(regresion, horizonte, len(puntos) - 1,
                                       100.0 if valores["medida"] == "tasa" else None)
        rotulo = datos.etiqueta_objeto(dimension, ref) if dimension else "todos"
        opciones = graficas.tendencia_opciones(
            f"{graficas.UNIDADES[valores['medida']]}: {rotulo}", valores["medida"], puntos,
            estadistica.ajustar(regresion), pron["puntos"], _meses_siguientes(puntos[-1]["mes"], horizonte))
    return responder({"opciones": opciones,
                      "nota": "Pasa `opciones` tal cual a Highcharts.chart(contenedor, opciones)."}, raiz="grafica")


def _horizonte():
    bruto = request.args.get("horizonte", "3")
    if not bruto.isdigit() or not 1 <= int(bruto) <= estadistica.MAX_HORIZONTE:
        raise ErrorApi(400, "validacion", f"horizonte debe ser un entero entre 1 y {estadistica.MAX_HORIZONTE}.")
    return int(bruto)


# --------------------------------------------------------------------------- #
# Analitica
# --------------------------------------------------------------------------- #
ESPEC_SERIE = CATALOGO["tendencia"][1]


def _serie(valores):
    dimension, ref = _objeto(valores)
    puntos = datos.serie_mensual(valores["medida"], valores["meses"], dimension, ref)
    return puntos, {"medida": valores["medida"], "dimension": dimension, "referencia_id": ref,
                    "objeto": datos.etiqueta_objeto(dimension, ref) if dimension else "todos",
                    "meses": [p["mes"] for p in puntos]}


@analitica.get("/tendencias")
@requiere_jwt(*LECTORES)
def tendencias():
    valores = _leer_filtros(ESPEC_SERIE)
    puntos, contexto = _serie(valores)
    resultado = estadistica.tendencia(_puntos_regresion(puntos))
    return responder({**contexto, "serie": puntos, "tendencia": resultado,
                      "nota": "Los meses con menos de 20 unidades vendidas y los que aun pueden recibir "
                              "devoluciones no se usan para la tasa."}, raiz="tendencias")


@analitica.get("/pronosticos")
@requiere_jwt(*LECTORES)
def pronosticos():
    valores = _leer_filtros(ESPEC_SERIE, extras=("horizonte",))
    horizonte = _horizonte()
    puntos, contexto = _serie(valores)
    regresion = _puntos_regresion(puntos)
    tope = 100.0 if valores["medida"] == "tasa" else None
    pron = estadistica.pronosticar(regresion, horizonte, len(puntos) - 1, tope)
    meses = _meses_siguientes(puntos[-1]["mes"], horizonte)
    for p, mes in zip(pron["puntos"], meses):
        p["mes"] = mes
    return responder({**contexto, "horizonte": horizonte, "pronostico": pron,
                      "referencia_promedio_movil_3": estadistica.promedio_movil([p["valor"] for p in puntos]),
                      "nota": "Pronostico de los meses siguientes al ultimo mes utilizable, no de hoy."},
                     raiz="pronosticos")


@analitica.get("/anomalias")
@requiere_jwt(*LECTORES)
def anomalias():
    espec = ESPEC_SERIE + [("tipo", "enum", ("objetos", "meses"), "objetos"),
                           ("por", "enum", tuple(datos.DIMENSIONES_TASA), "proveedor"),
                           ("desde", "fecha", None, None), ("hasta", "fecha", None, None)]
    valores = _leer_filtros(espec)
    if valores["tipo"] == "objetos":
        filas = datos.tasas_por(valores["por"], valores["desde"], valores["hasta"])
        resultado = estadistica.anomalias_objetos(filas)
        return responder({"tipo": "objetos", "por": valores["por"], **resultado,
                          "metodo": "puntaje z robusto (mediana y MAD); anomalia con |z| >= 3.5",
                          "nota": "Una anomalia es un dato distinto de sus pares, no una causa (RN-09)."},
                         raiz="anomalias")
    puntos, contexto = _serie(valores)
    regresion = _puntos_regresion(puntos)
    resultado = estadistica.anomalias_serie(regresion)
    for fila in resultado["datos"]:
        fila["mes"] = puntos[fila.pop("x")]["mes"]
    return responder({"tipo": "meses", **contexto, **resultado,
                      "metodo": "puntaje z robusto de los residuos de la tendencia lineal",
                      "nota": "Una anomalia es un dato distinto de lo esperado, no una causa (RN-09)."},
                     raiz="anomalias")


@analitica.get("/factores")
@requiere_jwt(*LECTORES)
def factores():
    """Cruza dos factores (p. ej. proveedor y tienda) para ver donde se concentra la tasa de devolucion.

    Cada combinacion lleva su intervalo de confianza del 95 % y una lectura explicable: viene de un factor,
    del otro, de ambos o solo de la combinacion. Orienta la investigacion; no determina causas (RN-09).
    """
    espec = [("por", "enum", tuple(datos.DIMENSIONES_TASA), "proveedor"),
             ("con", "enum", tuple(datos.DIMENSIONES_TASA), "tienda"),
             ("desde", "fecha", None, None), ("hasta", "fecha", None, None),
             ("limite", "entero", (1, 100), 20), ("solo_distinguibles", "enum", ("true", "false"), "false")]
    valores = _leer_filtros(espec)
    if valores["por"] == valores["con"]:
        raise ErrorApi(400, "validacion", "por y con deben ser factores distintos.")
    resultado = estadistica.analizar_cruce(datos.tasas_cruzadas(valores["por"], valores["con"],
                                                                valores["desde"], valores["hasta"]))
    celdas = resultado["celdas"]
    if valores["solo_distinguibles"] == "true":
        celdas = [c for c in celdas if c["distinguible"]]
    resultado = {**resultado, "total_celdas": len(celdas), "celdas": celdas[:valores["limite"]]}
    return responder({"por": valores["por"], "con": valores["con"], **resultado,
                      "metodo": "tasa = unidades devueltas / vendidas por combinacion; intervalo de Wilson del 95 %; "
                                "una combinacion es distinguible si el extremo bajo del intervalo supera la tasa promedio",
                      "nota": "Es una senal para revisar donde investigar, no una causa (RN-09). "
                              "Solo se juzgan combinaciones con 20 unidades vendidas o mas."},
                     raiz="factores")


@analitica.get("/alertas-fraude")
@requiere_jwt(*SOLO_ANALISIS)
def alertas_fraude():
    """Senales explicables; no acusan ni bloquean automaticamente (RF-25)."""
    filas = datos.alertas_fraude()
    registrar_bitacora("consulta_alertas_fraude", "reportes", None, f"{len(filas)} alertas")
    return responder({"datos": filas, "total": len(filas),
                      "aviso": "Son indicadores preventivos, no una determinacion de fraude."},
                     raiz="alertas_fraude")


def create_app():
    app = Flask(__name__)
    app.json.sort_keys = False
    respuestas.registrar(app, NOMBRE)
    app.teardown_appcontext(cerrar_conexion)
    for bp in (reportes, grafica, analitica):
        app.register_blueprint(bp)
    docs.registrar(app, os.path.join(os.path.dirname(__file__), "openapi.yaml"))

    @app.get("/health")
    def health():
        deps = {"postgresql": salud_postgres(), "redis": salud_redis()}
        ok = all(x["ok"] for x in deps.values())
        return responder({"servicio": NOMBRE, "version": "v1",
                          "estado": "ok" if ok else "degradado", "dependencias": deps},
                         200 if ok else 503)
    return app
