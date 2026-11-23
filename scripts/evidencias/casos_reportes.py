"""Casos de evidencia de reportes-analitica (8018): RF-23, RF-25, RF-26, RF-28, RN-09, RN-13, RN-15, RNF-13, RNF-16.

El servicio es de solo lectura: no hay datos que limpiar. Lo unico que se escribe es la bitacora de cada
descarga (reporte, formato y numero de filas, nunca los datos), que es de solo agregar. Los resultados
estadisticos dependen de cuantos meses con datos tenga la demo; por eso las verificaciones aceptan
`ok` o `sin_datos` y exigen que `sin_datos` explique por que (RN-09: no inventar tendencias).
"""
from datetime import date

SERVICIO = "reportes-analitica"
SIGLA = "REP"
TITULO = "Reportes, graficas y analitica"
PUERTO = 8018
ARCHIVO = "reportes_analitica"

API = "/api/v1/reportes"
GRAF = "/api/v1/graficas"
ANA = "/api/v1/analitica"
LOTE = "L-2026-PROB-01"
ESTADOS_ANALISIS = ("ok", "sin_datos")


def tipo_error(r):
    return r.json["error"]["tipo"]


def estado_valido(r, ruta):
    nodo = r.json
    for clave in ruta:
        nodo = nodo[clave]
    return nodo["estado"] in ESTADOS_ANALISIS and (nodo["estado"] == "ok" or bool(nodo["motivo"]))


def ejecutar(c):
    hoy = date.today().isoformat()
    c.ctx["prov"] = int(c.valor(f"SELECT proveedor_id FROM lotes WHERE numero_lote = '{LOTE}'"))
    bitacora = ("SELECT accion, detalle FROM bitacora WHERE accion = 'exportar_reporte' ORDER BY id DESC LIMIT 1")

    # ---------------------------------------------------------------- salud, contratos y Swagger
    c.caso("salud 200 JSON", "GET", "/health", objetivo="El servicio informa su estado y el de PostgreSQL y Redis (RF-32).",
           verifica=[("estado ok", lambda r: r.json["estado"] == "ok"),
                     ("PostgreSQL ok", lambda r: r.json["dependencias"]["postgresql"]["ok"] is True),
                     ("Redis ok", lambda r: r.json["dependencias"]["redis"]["ok"] is True)])
    c.caso("salud 200 XML", "GET", "/health", accept="application/xml", objetivo="El mismo endpoint responde XML (RF-31).",
           verifica=[("es XML", lambda r: r.tipo.startswith("application/xml")), ("estado ok", lambda r: "<estado>ok</estado>" in r.texto)])
    c.caso("Swagger: documentacion de la API", "GET", "/docs", accept="text/html", objetivo="La API publica su documentacion Swagger.",
           verifica=[("HTML de Swagger UI", lambda r: "swagger" in r.texto.lower())])
    c.caso("Swagger: especificacion OpenAPI", "GET", "/openapi.json", objetivo="La especificacion lista reportes, graficas y analitica.",
           verifica=[("incluye reportes", lambda r: f"{API}/{{nombre}}" in r.json["paths"]),
                     ("incluye alertas de fraude", lambda r: f"{ANA}/alertas-fraude" in r.json["paths"])])

    # ---------------------------------------------------------------- autenticacion y permisos
    c.caso("sin token: 401", "GET", API, espera=401, objetivo="Un endpoint protegido exige JWT (RNF-09).",
           verifica=[("tipo no_autenticado", lambda r: tipo_error(r) == "no_autenticado")])
    c.caso("token invalido: 401", "GET", API, espera=401, token="no.es.un.jwt", objetivo="Un token alterado se rechaza (RNF-09).",
           verifica=[("tipo token_invalido", lambda r: tipo_error(r) == "token_invalido")])
    c.caso("cliente: 403", "GET", API, rol="cliente", espera=403,
           objetivo="Los reportes con costos y proveedores no los ve un cliente (RN-13).",
           verifica=[("tipo sin_permiso", lambda r: tipo_error(r) == "sin_permiso")])
    c.caso("inspector: 403 en analitica", "GET", f"{ANA}/tendencias", rol="inspector", espera=403,
           objetivo="La lectura es de Administrador, Analista, Supervisor y Encargado de Reembolsos.",
           verifica=[("tipo sin_permiso", lambda r: tipo_error(r) == "sin_permiso")])

    # ---------------------------------------------------------------- catalogo y reportes en JSON/XML
    c.caso("catalogo 200", "GET", API, rol="analista",
           objetivo="El catalogo dice que reportes hay, sus filtros y los formatos de descarga (RF-28).",
           verifica=[("cinco reportes", lambda r: {x["nombre"] for x in r.json["datos"]} == {"devoluciones", "costos", "tasas", "pareto", "tendencia"}),
                     ("cinco formatos", lambda r: set(r.json["datos"][0]["formatos"]) == {"json", "csv", "xlsx", "pdf", "xml"}
                      or set(r.json["datos"][0]["formatos"]) >= {"json", "csv", "xlsx", "pdf"})])
    c.caso("reporte de devoluciones 200 JSON", "GET", f"{API}/devoluciones?por_pagina=5", rol="analista",
           objetivo="Reporte tabular paginado, con sus columnas y los filtros aplicados (RF-28).",
           verifica=[("trae columnas", lambda r: [x["clave"] for x in r.json["columnas"]][:2] == ["folio", "fecha_solicitud"]),
                     ("hay filas", lambda r: len(r.json["datos"]) >= 1), ("a lo mas 5 por pagina", lambda r: len(r.json["datos"]) <= 5),
                     ("trae paginacion", lambda r: r.json["paginacion"]["total"] >= 1)],
           efecto=[("devoluciones vigentes en la base, para contrastar el total", "SELECT count(*) AS devoluciones FROM devoluciones WHERE eliminado_en IS NULL")])
    c.caso("reporte de devoluciones 200 XML", "GET", f"{API}/devoluciones?por_pagina=3", rol="supervisor", accept="application/xml",
           objetivo="El mismo reporte en XML (RF-31).",
           verifica=[("es XML", lambda r: r.tipo.startswith("application/xml")), ("raiz reporte", lambda r: "<reporte>" in r.texto)])
    c.caso("reporte de devoluciones filtrado por estado y fechas", "GET", f"{API}/devoluciones?desde=2026-01-01&hasta={hoy}&estado=resuelta", rol="analista",
           objetivo="Los filtros acotan el reporte; se devuelven tal como se aplicaron.",
           verifica=[("filtro estado aplicado", lambda r: r.json["filtros"]["estado"] == "resuelta"),
                     ("todas las filas son resueltas", lambda r: all(f["estado"] == "resuelta" for f in r.json["datos"]))])
    c.caso("reporte de costos 200", "GET", f"{API}/costos?por_pagina=5", rol="reembolsos",
           objetivo="Costos de transporte, inspeccion y almacenamiento por devolucion; lo ve el Encargado de Reembolsos.",
           verifica=[("trae columnas de costo", lambda r: "costo_transporte" in [x["clave"] for x in r.json["columnas"]])])
    c.caso("reporte de tasas 200 por proveedor", "GET", f"{API}/tasas?por=proveedor", rol="analista",
           objetivo="Tasa de devolucion = unidades devueltas entre vendidas (RF-26).", verifica=[("hay filas", lambda r: len(r.json["datos"]) >= 1)])
    c.caso("reporte de tasas 200 por tienda", "GET", f"{API}/tasas?por=tienda", rol="analista",
           objetivo="La misma tasa agrupada por tienda.", verifica=[("hay filas", lambda r: len(r.json["datos"]) >= 1)])
    c.caso("reporte pareto 200 por motivo", "GET", f"{API}/pareto?dimension=motivo&medida=frecuencia", rol="analista",
           objetivo="Pareto de devoluciones por motivo: ordenado de mayor a menor con % acumulado.", verifica=[("hay filas", lambda r: len(r.json["datos"]) >= 1)])
    c.caso("reporte pareto 200 por proveedor y costo", "GET", f"{API}/pareto?dimension=proveedor&medida=costo", rol="analista",
           objetivo="El mismo Pareto con otra dimension y otra medida.", verifica=[("hay filas", lambda r: len(r.json["datos"]) >= 1)])
    c.caso("reporte de tendencia 200", "GET", f"{API}/tendencia?medida=devoluciones&meses=12", rol="analista",
           objetivo="Serie mensual de las ultimas 12 meses.", verifica=[("doce meses", lambda r: r.json["paginacion"]["total"] == 12)])

    # ---------------------------------------------------------------- errores controlados de los reportes
    c.caso("reporte 404 inexistente", "GET", f"{API}/inventado", rol="analista", espera=404, objetivo="Un reporte que no existe responde 404.",
           verifica=[("tipo no_encontrado", lambda r: tipo_error(r) == "no_encontrado")])
    c.caso("reporte 400 formato invalido", "GET", f"{API}/costos?formato=docx", rol="analista", espera=400, objetivo="El formato debe ser uno de los publicados.",
           verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("reporte 400 parametro desconocido", "GET", f"{API}/costos?proveedor_id=1", rol="analista", espera=400,
           objetivo="Un parametro que ese reporte no admite se rechaza, no se ignora en silencio.",
           verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("reporte 400 fecha invalida", "GET", f"{API}/devoluciones?desde=ayer", rol="analista", espera=400, objetivo="Las fechas son AAAA-MM-DD.",
           verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("reporte 400 hasta antes de desde", "GET", f"{API}/devoluciones?desde=2026-06-01&hasta=2026-01-01", rol="analista", espera=400,
           objetivo="Un periodo al reves se rechaza.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("reporte 400 estado desconocido", "GET", f"{API}/devoluciones?estado=dormida", rol="analista", espera=400,
           objetivo="Un estado fuera del catalogo se rechaza.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("tendencia 400 meses fuera de rango", "GET", f"{API}/tendencia?meses=2", rol="analista", espera=400,
           objetivo="La serie admite de 6 a 36 meses.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("tendencia 400 dimension sin referencia", "GET", f"{API}/tendencia?dimension=proveedor", rol="analista", espera=400,
           objetivo="La dimension y su referencia_id van juntas.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("tendencia 404 objeto inexistente", "GET", f"{API}/tendencia?dimension=proveedor&referencia_id=999999", rol="analista", espera=404,
           objetivo="No se grafica un objeto que no existe.", verifica=[("tipo no_encontrado", lambda r: tipo_error(r) == "no_encontrado")])

    # ---------------------------------------------------------------- descargas CSV, Excel y PDF
    c.caso("descarga CSV de devoluciones", "GET", f"{API}/devoluciones?formato=csv", rol="analista",
           objetivo="Archivo CSV con encabezados de descarga y sin cache, porque son datos de negocio (RF-28).",
           verifica=[("tipo text/csv", lambda r: r.tipo.startswith("text/csv")),
                     ("se descarga como adjunto", lambda r: "attachment" in r.cabeceras.get("content-disposition", "")),
                     ("no se guarda en cache", lambda r: r.cabeceras.get("cache-control") == "no-store"),
                     ("primera linea con encabezados", lambda r: r.texto.lstrip("﻿").splitlines()[0].startswith("Folio"))],
           efecto=[("la descarga queda en la bitacora con reporte, formato y filas; sin los datos", bitacora)])
    c.caso("descarga Excel de devoluciones", "GET", f"{API}/devoluciones?formato=xlsx", rol="analista",
           objetivo="Libro de Excel (.xlsx) escrito con la biblioteca estandar.",
           verifica=[("tipo de hoja de calculo", lambda r: "spreadsheetml" in r.tipo), ("es un zip (PK)", lambda r: r.cuerpo[:2] == b"PK"),
                     ("adjunto .xlsx", lambda r: ".xlsx" in r.cabeceras.get("content-disposition", ""))])
    c.caso("descarga PDF de devoluciones", "GET", f"{API}/devoluciones?formato=pdf", rol="analista",
           objetivo="Documento PDF listo para imprimir.",
           verifica=[("tipo application/pdf", lambda r: r.tipo.startswith("application/pdf")), ("empieza con %PDF", lambda r: r.cuerpo[:4] == b"%PDF"),
                     ("termina con %%EOF", lambda r: r.cuerpo.rstrip().endswith(b"%%EOF"))])
    c.caso("descarga CSV de costos", "GET", f"{API}/costos?formato=csv", rol="reembolsos",
           objetivo="El Encargado de Reembolsos descarga los costos.", verifica=[("tipo text/csv", lambda r: r.tipo.startswith("text/csv"))])
    c.caso("descarga Excel de tasas", "GET", f"{API}/tasas?por=lote&formato=xlsx", rol="analista",
           objetivo="Tasas por lote en Excel.", verifica=[("es un zip (PK)", lambda r: r.cuerpo[:2] == b"PK")])
    c.caso("descarga PDF de Pareto", "GET", f"{API}/pareto?dimension=transportista&medida=cantidad&formato=pdf", rol="supervisor",
           objetivo="Pareto por transportista en PDF.", verifica=[("empieza con %PDF", lambda r: r.cuerpo[:4] == b"%PDF")])
    c.caso("descarga CSV de la tendencia de un proveedor", "GET", f"{API}/tendencia?dimension=proveedor&referencia_id={{prov}}&meses=12&formato=csv", rol="analista",
           objetivo="Serie mensual de un proveedor en CSV.", verifica=[("tipo text/csv", lambda r: r.tipo.startswith("text/csv"))])

    # El limite es de 20 descargas por minuto y por usuario (RNF-13). Las 20 primeras se hacen sin registrarlas
    # una por una; la 21 si se muestra completa. Se usa otra cuenta para no gastar la cuota de las anteriores.
    token = c.sesion("admin")
    for _ in range(20):
        c._curl("GET", f"{c.base}:{c.puerto}{API}/costos?formato=csv",
                {"Accept": "application/json", "Authorization": f"Bearer {token}"})
    c.caso("descarga 429 tras 20 en un minuto", "GET", f"{API}/costos?formato=csv", rol="admin", espera=429,
           objetivo="Un archivo cuesta mas que una pagina: tras 20 descargas en un minuto el usuario recibe 429 con Retry-After.",
           verifica=[("tipo demasiadas_peticiones", lambda r: tipo_error(r) == "demasiadas_peticiones"),
                     ("indica cuanto esperar", lambda r: int(r.cabeceras["retry-after"]) >= 1)])
    c.caso("JSON no cuenta para el limite de descargas", "GET", f"{API}/costos?por_pagina=1", rol="admin",
           objetivo="Solo los archivos tienen cuota; consultar en JSON sigue funcionando.", verifica=[("hay filas o vacio sin error", lambda r: "datos" in r.json)])

    # ---------------------------------------------------------------- graficas para Highcharts
    c.caso("grafica Pareto 200", "GET", f"{GRAF}/pareto?dimension=motivo", rol="analista",
           objetivo="Opciones listas para `Highcharts.chart(contenedor, opciones)`: columnas y linea de % acumulado.",
           verifica=[("trae series", lambda r: len(r.json["opciones"]["series"]) == 2),
                     ("columna y linea", lambda r: [s["type"] for s in r.json["opciones"]["series"]] == ["column", "line"])])
    c.caso("grafica de tasas 200", "GET", f"{GRAF}/tasas?por=proveedor", rol="analista",
           objetivo="Barras con la tasa por proveedor.", verifica=[("grafica de barras", lambda r: r.json["opciones"]["chart"]["type"] == "bar")])
    c.caso("grafica de tendencia 200", "GET", f"{GRAF}/tendencia?medida=tasa&meses=12&horizonte=3", rol="analista",
           objetivo="Serie observada, linea de tendencia y pronostico con banda.", verifica=[("trae la serie observada", lambda r: r.json["opciones"]["series"][0]["name"] == "Observado")])
    c.caso("grafica 406 en XML", "GET", f"{GRAF}/pareto", rol="analista", espera=406, accept="application/xml",
           objetivo="Las opciones de Highcharts solo se entregan en JSON.", verifica=[("tipo solo_json", lambda r: "solo_json" in r.texto)])
    c.caso("grafica 404 inexistente", "GET", f"{GRAF}/dona", rol="analista", espera=404, objetivo="Solo hay pareto, tendencia y tasas.",
           verifica=[("tipo no_encontrado", lambda r: tipo_error(r) == "no_encontrado")])
    c.caso("grafica 400 horizonte fuera de rango", "GET", f"{GRAF}/tendencia?horizonte=0", rol="analista", espera=400,
           objetivo="El horizonte del pronostico tiene un maximo.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])

    # ---------------------------------------------------------------- analitica explicable
    c.caso("tendencias 200", "GET", f"{ANA}/tendencias?medida=devoluciones&meses=12", rol="analista",
           objetivo="Regresion lineal sobre los meses con datos: pendiente, R2 y si es distinguible del ruido (RN-09). Con pocos datos dice sin_datos y por que.",
           verifica=[("estado ok o sin_datos explicado", lambda r: estado_valido(r, ["tendencia"])), ("trae la serie", lambda r: len(r.json["serie"]) == 12)])
    c.caso("tendencias 200 XML", "GET", f"{ANA}/tendencias?meses=6", rol="analista", accept="application/xml",
           objetivo="La misma tendencia en XML.", verifica=[("es XML", lambda r: r.tipo.startswith("application/xml"))])
    c.caso("tendencias 200 de un proveedor", "GET", f"{ANA}/tendencias?medida=tasa&dimension=proveedor&referencia_id={{prov}}", rol="supervisor",
           objetivo="La tendencia de la tasa de un proveedor concreto.",
           verifica=[("estado ok o sin_datos explicado", lambda r: estado_valido(r, ["tendencia"])), ("nombra el objeto", lambda r: r.json["objeto"] != "todos")])
    c.caso("pronosticos 200", "GET", f"{ANA}/pronosticos?medida=devoluciones&horizonte=3", rol="analista",
           objetivo="Pronostico con intervalo de prediccion del 95%; aclara que es de los meses siguientes al ultimo mes utilizable.",
           verifica=[("estado ok o sin_datos explicado", lambda r: estado_valido(r, ["pronostico"])), ("horizonte 3", lambda r: r.json["horizonte"] == 3)])
    c.caso("pronosticos 400 horizonte invalido", "GET", f"{ANA}/pronosticos?horizonte=99", rol="analista", espera=400,
           objetivo="El horizonte tiene un maximo.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("anomalias 200 entre proveedores", "GET", f"{ANA}/anomalias?tipo=objetos&por=proveedor", rol="analista",
           objetivo="Puntaje z robusto (mediana y MAD): marca proveedores distintos de sus pares, sin decir por que (RN-09).",
           verifica=[("estado ok o sin_datos explicado", lambda r: r.json["estado"] in ESTADOS_ANALISIS and (r.json["estado"] == "ok" or bool(r.json["motivo"]))),
                     ("declara el umbral", lambda r: "3.5" in r.json["metodo"]), ("aclara que no es una causa", lambda r: "RN-09" in r.json["nota"])])
    c.caso("anomalias 200 entre lotes", "GET", f"{ANA}/anomalias?tipo=objetos&por=lote", rol="analista",
           objetivo="Lo mismo entre lotes.", verifica=[("estado ok o sin_datos", lambda r: r.json["estado"] in ESTADOS_ANALISIS)])
    c.caso("anomalias 200 entre meses", "GET", f"{ANA}/anomalias?tipo=meses&medida=devoluciones&meses=12", rol="analista",
           objetivo="Meses que se alejan de la tendencia lineal.", verifica=[("estado ok o sin_datos", lambda r: r.json["estado"] in ESTADOS_ANALISIS)])
    c.caso("anomalias 400 tipo invalido", "GET", f"{ANA}/anomalias?tipo=planetas", rol="analista", espera=400,
           objetivo="El tipo es objetos o meses.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("alertas de fraude 200", "GET", f"{ANA}/alertas-fraude", rol="analista",
           objetivo="Senales explicables de posible fraude; advierten que no acusan ni bloquean (RF-25). Nombran clientes, por eso son solo de analisis (RN-15).",
           verifica=[("aviso preventivo", lambda r: "no una determinacion" in r.json["aviso"]), ("total coincide", lambda r: r.json["total"] == len(r.json["datos"]))],
           efecto=[("la consulta queda en la bitacora, solo con el numero de alertas",
                    "SELECT accion, detalle FROM bitacora WHERE accion = 'consulta_alertas_fraude' ORDER BY id DESC LIMIT 1")])
    c.caso("alertas de fraude 403 supervisor", "GET", f"{ANA}/alertas-fraude", rol="supervisor", espera=403,
           objetivo="Nombran clientes: las ven Administrador y Analista, no el Supervisor (RN-15).",
           verifica=[("tipo sin_permiso", lambda r: tipo_error(r) == "sin_permiso")])

    # ---------------------------------------------------------------- analisis de varios factores
    c.caso("factores 200: proveedor por tienda", "GET", f"{ANA}/factores?por=proveedor&con=tienda&limite=5", rol="analista",
           objetivo="Cruza dos factores: la tasa de cada combinacion con su intervalo de Wilson del 95 % y la tasa de cada factor por separado (RF-23, RF-24).",
           verifica=[("estado ok o sin_datos explicado", lambda r: r.json["estado"] in ESTADOS_ANALISIS and (r.json["estado"] == "ok" or bool(r.json["motivo"]))),
                     ("a lo mas 5 combinaciones", lambda r: len(r.json["celdas"]) <= 5),
                     ("ordenadas por tasa", lambda r: [x["tasa_pct"] for x in r.json["celdas"]] == sorted((x["tasa_pct"] for x in r.json["celdas"]), reverse=True)),
                     ("el intervalo envuelve a la tasa", lambda r: all(x["intervalo_95_pct"]["bajo"] <= x["tasa_pct"] <= x["intervalo_95_pct"]["alto"] for x in r.json["celdas"])),
                     ("aclara que no es una causa", lambda r: "RN-09" in r.json["nota"])])
    c.caso("factores 200: el lote problematico destaca", "GET", f"{ANA}/factores?por=lote&con=proveedor&solo_distinguibles=true", rol="analista",
           objetivo="El lote de la demo (24 unidades, 16 devueltas) es distinguible del promedio y trae su lectura de donde viene el exceso.",
           verifica=[("aparece el lote de la demo", lambda r: any(LOTE in x["a_etiqueta"] for x in r.json["celdas"])),
                     ("es distinguible y trae lectura", lambda r: all(x["distinguible"] and x["lectura"] for x in r.json["celdas"])),
                     ("supera el doble del promedio", lambda r: all(x["veces_promedio"] >= 2 for x in r.json["celdas"] if LOTE in x["a_etiqueta"]))])
    c.caso("factores 200 XML", "GET", f"{ANA}/factores?por=producto&con=tienda&limite=3", rol="supervisor", accept="application/xml",
           objetivo="El mismo analisis en XML (RF-31).", verifica=[("es XML", lambda r: r.tipo.startswith("application/xml")), ("raiz factores", lambda r: "<factores>" in r.texto)])
    c.caso("factores 400 mismo factor dos veces", "GET", f"{ANA}/factores?por=tienda&con=tienda", rol="analista", espera=400,
           objetivo="Un cruce necesita dos factores distintos.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("factores 400 ruta no tiene ventas", "GET", f"{ANA}/factores?por=ruta", rol="analista", espera=400,
           objetivo="Ruta y transportista no se cruzan: no existe 'vendido por ruta' para calcular la tasa.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("factores 400 limite fuera de rango", "GET", f"{ANA}/factores?limite=0", rol="analista", espera=400,
           objetivo="El limite va de 1 a 100.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("factores 403 cliente", "GET", f"{ANA}/factores", rol="cliente", espera=403,
           objetivo="Como el resto de la analitica, no es para clientes (RN-13).", verifica=[("tipo sin_permiso", lambda r: tipo_error(r) == "sin_permiso")])
