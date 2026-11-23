"""Casos de evidencia de auditoria (8008): RF-30, RN-12, RN-13, RNF-16, RNF-23, RF-25.

El servicio de auditoria es de solo lectura: no hay datos que limpiar. Tambien se documentan las rutas
de /api/v1/analisis tras retirar el analisis (docs/MIGRACION_ANALISIS_8008.md): responden 410
servicio_movido, aun sin token, y nombran a su sucesor (clasificacion-motivos 8010, reportes-analitica 8018 y la
propia auditoria). Con el analisis habilitado estas mismas rutas responden 200 con las cabeceras Deprecation y Link.
"""
SERVICIO = "analisis-auditoria"
SIGLA = "AUD"
TITULO = "Auditoria (bitacora y traza) y rutas de analisis obsoletas"
PUERTO = 8008
ARCHIVO = "auditoria"

API = "/api/v1/auditoria"
OBS = "/api/v1/analisis"


def tipo_error(r):
    return r.json["error"]["tipo"]


def ejecutar(c):
    c.ctx["cid"] = c.valor("SELECT correlation_id FROM bitacora WHERE correlation_id IS NOT NULL ORDER BY id DESC LIMIT 1")
    c.ctx["uid"] = int(c.valor("SELECT usuario_id FROM bitacora WHERE usuario_id IS NOT NULL ORDER BY id DESC LIMIT 1"))

    # ---------------------------------------------------------------- salud, contratos y Swagger
    c.caso("salud 200 con las tres dependencias", "GET", "/health", objetivo="El servicio informa PostgreSQL, Redis y MongoDB, y que el analisis esta retirado (RF-32).",
           verifica=[("estado ok", lambda r: r.json["estado"] == "ok"), ("MongoDB ok", lambda r: r.json["dependencias"]["mongodb"]["ok"] is True),
                     ("analisis retirado", lambda r: r.json["analisis"] == "retirado")])
    c.caso("Swagger: documentacion de la API", "GET", "/docs", accept="text/html", objetivo="La API publica su documentacion Swagger.",
           verifica=[("HTML de Swagger UI", lambda r: "swagger" in r.texto.lower())])
    c.caso("Swagger: especificacion OpenAPI", "GET", "/openapi.json", objetivo="La especificacion incluye la auditoria.",
           verifica=[("incluye la bitacora", lambda r: API in r.json["paths"]), ("incluye el estado", lambda r: f"{API}/estado" in r.json["paths"])])

    # ---------------------------------------------------------------- autenticacion y permisos
    c.caso("sin token: 401", "GET", API, espera=401, objetivo="La auditoria exige JWT (RNF-09).", verifica=[("tipo no_autenticado", lambda r: tipo_error(r) == "no_autenticado")])
    c.caso("token invalido: 401", "GET", API, espera=401, token="no.es.un.jwt", objetivo="Un token alterado se rechaza.", verifica=[("tipo token_invalido", lambda r: tipo_error(r) == "token_invalido")])
    c.caso("cliente: 403", "GET", API, rol="cliente", espera=403, objetivo="La bitacora no la lee un cliente (RN-13).", verifica=[("tipo sin_permiso", lambda r: tipo_error(r) == "sin_permiso")])
    c.caso("supervisor: 403", "GET", f"{API}/estado", rol="supervisor", espera=403,
           objetivo="Auditar es de Administrador y Analista; la separacion de funciones evita que quien opera revise su propio rastro (RN-12).",
           verifica=[("tipo sin_permiso", lambda r: tipo_error(r) == "sin_permiso")])

    # ---------------------------------------------------------------- bitacora
    c.caso("bitacora 200: lo mas reciente primero", "GET", f"{API}?por_pagina=10", rol="admin",
           objetivo="La bitacora registra quien hizo que y cuando (RF-30), ordenada de lo mas reciente a lo mas antiguo.",
           verifica=[("hay registros", lambda r: len(r.json["datos"]) >= 1), ("trae usuario, accion y fecha", lambda r: all(k in r.json["datos"][0] for k in ("usuario", "accion", "fecha"))),
                     ("orden descendente por id", lambda r: [f["id"] for f in r.json["datos"]] == sorted((f["id"] for f in r.json["datos"]), reverse=True)),
                     ("sin tokens ni hashes", lambda r: "eyJ" not in r.texto and "password_hash" not in r.texto.lower())],
           efecto=[("registros de la bitacora, para contrastar el total", "SELECT count(*) AS registros FROM bitacora")])
    c.caso("bitacora 200 XML", "GET", f"{API}?por_pagina=3", rol="analista", accept="application/xml", objetivo="La bitacora responde XML (RF-31).",
           verifica=[("es XML", lambda r: r.tipo.startswith("application/xml")), ("raiz bitacora", lambda r: "<bitacora>" in r.texto)])
    c.caso("bitacora 200 por correlation id", "GET", f"{API}?correlation_id={{cid}}", rol="admin",
           objetivo="Todo lo que dejo una misma peticion, de punta a punta, se sigue con su correlation id.",
           verifica=[("todas con ese id", lambda r: len(r.json["datos"]) >= 1 and all(f["correlation_id"] == c.ctx["cid"] for f in r.json["datos"]))])
    c.caso("bitacora 200 por usuario", "GET", f"{API}?usuario_id={{uid}}&por_pagina=20", rol="admin",
           objetivo="Lo que hizo una persona.", verifica=[("hay registros", lambda r: r.json["paginacion"]["total"] >= 1)])
    c.caso("bitacora 200 por entidad y accion", "GET", f"{API}?entidad=usuarios&accion=autorizacion_operacion", rol="analista",
           objetivo="Filtros por entidad y accion; las reconfirmaciones de contrasena quedan asentadas.",
           verifica=[("todas coinciden", lambda r: all(f["entidad"] == "usuarios" and f["accion"] == "autorizacion_operacion" for f in r.json["datos"]))])
    c.caso("bitacora 200 por periodo", "GET", f"{API}?desde=2026-01-01&hasta=2026-12-31&por_pagina=5", rol="admin",
           objetivo="El periodo incluye todo el dia final.", verifica=[("hay registros", lambda r: len(r.json["datos"]) >= 1)])
    c.caso("bitacora 200 con intento de inyeccion SQL", "GET", f"{API}?accion=x%27%20OR%20%271%27%3D%271", rol="admin",
           objetivo="Un filtro con SQL se trata como texto (parametros ligados, RNF-11): no devuelve toda la bitacora.",
           verifica=[("sin resultados", lambda r: r.json["paginacion"]["total"] == 0)])
    c.caso("bitacora 400 fecha invalida", "GET", f"{API}?desde=ayer", rol="admin", espera=400, objetivo="Las fechas son AAAA-MM-DD.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("bitacora 400 hasta antes de desde", "GET", f"{API}?desde=2026-06-01&hasta=2026-01-01", rol="admin", espera=400, objetivo="Un periodo al reves se rechaza.",
           verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("bitacora 400 usuario no numerico", "GET", f"{API}?usuario_id=abc", rol="admin", espera=400, objetivo="El filtro numerico se valida.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("bitacora 400 filtro demasiado largo", "GET", f"{API}?accion={'a' * 101}", rol="admin", espera=400, objetivo="Un filtro de texto tiene un maximo de 100 caracteres.",
           verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])

    # ---------------------------------------------------------------- solo lectura y proteccion
    c.caso("la bitacora no se escribe por la API: POST", "POST", API, rol="admin", espera=405, json_cuerpo={"accion": "falsa", "entidad": "x"},
           objetivo="La auditoria solo se consulta: no existe una ruta para agregar o alterar registros (RN-12). Los demas servicios escriben directo en la base.",
           verifica=[("metodo no permitido", lambda r: r.estado == 405)])
    c.caso("la bitacora no se escribe por la API: PATCH", "PATCH", f"{API}/1", rol="admin", espera=404, json_cuerpo={"detalle": "alterado"},
           objetivo="Tampoco hay ruta para modificar un registro.", verifica=[("la ruta no existe", lambda r: r.estado in (404, 405))])
    c.caso("estado 200: la base protege la bitacora", "GET", f"{API}/estado", rol="analista",
           objetivo="Informa si la base rechaza UPDATE, DELETE y TRUNCATE (migracion 045) y avisa hasta donde llega esa proteccion.",
           verifica=[("proteccion completa", lambda r: r.json["proteccion"]["completa"] is True), ("hay registros", lambda r: r.json["registros"] >= 1),
                     ("no promete mas de lo que hace", lambda r: "no sustituye el control de acceso" in r.json["aviso"])],
           efecto=[("los triggers que la protegen", "SELECT tgname FROM pg_trigger WHERE tgrelid = 'bitacora'::regclass AND NOT tgisinternal ORDER BY 1")])

    # ---------------------------------------------------------------- traza de eventos (MongoDB)
    c.caso("eventos 200 de MongoDB", "GET", f"{API}/eventos?por_pagina=5", rol="admin",
           objetivo="Traza de eventos entre servicios. Nunca incluye el campo `datos` (puede traer cuerpos de peticiones, RNF-16).",
           verifica=[("trae paginacion", lambda r: "paginacion" in r.json), ("ningun evento trae `datos`", lambda r: all("datos" not in e for e in r.json["datos"]))])
    c.caso("eventos 200 por servicio", "GET", f"{API}/eventos?servicio=auth", rol="analista", objetivo="Filtra los eventos por servicio.",
           verifica=[("todos del servicio", lambda r: all(e.get("servicio") == "auth" for e in r.json["datos"]))])
    c.caso("eventos 200 XML", "GET", f"{API}/eventos?por_pagina=2", rol="analista", accept="application/xml", objetivo="La traza responde XML (RF-31).",
           verifica=[("es XML", lambda r: r.tipo.startswith("application/xml"))])
    c.caso("eventos 400 filtro demasiado largo", "GET", f"{API}/eventos?servicio={'s' * 61}", rol="admin", espera=400, objetivo="Un filtro de texto tiene un maximo.",
           verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])

    # ---------------------------------------------------------------- rutas de analisis retiradas (corte)
    def retirada(sucesor):
        return [("410 servicio_movido", lambda r: tipo_error(r) == "servicio_movido"),
                ("nombra al sucesor", lambda r: sucesor in " ".join(r.json["error"]["detalles"].values())),
                ("lleva Deprecation: true", lambda r: r.cabeceras.get("deprecation") == "true")]

    c.caso("retirada: clasificar motivo", "POST", f"{OBS}/clasificar-motivo", espera=410, json_cuerpo={"descripcion": "El producto llego con el empaque roto"},
           objetivo="La clasificacion de motivos vive ahora en clasificacion-motivos (8010). Esta ruta responde 410 aun sin token y dice donde.",
           verifica=retirada("clasificacion-motivos"))
    c.caso("retirada: alertas de fraude", "GET", f"{OBS}/alertas-fraude", rol="analista", espera=410,
           objetivo="Las alertas de fraude viven en reportes-analitica (8018). Ni un Analista con token las obtiene aqui.", verifica=retirada("reportes-analitica"))
    c.caso("retirada: Pareto", "GET", f"{OBS}/pareto?dimension=motivo", rol="analista", espera=410,
           objetivo="El Pareto vive en reportes-analitica (8018), calculado directo en PostgreSQL.", verifica=retirada("/api/v1/reportes/pareto"))
    c.caso("retirada: sincronizar", "POST", f"{OBS}/sincronizar", rol="analista", espera=410, json_cuerpo={},
           objetivo="Sincronizar ya no hace falta: 8018 calcula directo en PostgreSQL y siempre esta al dia. No escribe nada.", verifica=[("410 servicio_movido", lambda r: tipo_error(r) == "servicio_movido")])
    c.caso("retirada: resumen", "GET", f"{OBS}/resumen", rol="analista", espera=410,
           objetivo="El resumen solo contaba snapshots y no tiene sucesor.", verifica=[("410 servicio_movido", lambda r: tipo_error(r) == "servicio_movido")])
    c.caso("retirada: alias de eventos", "GET", f"{OBS}/eventos?por_pagina=2", rol="admin", espera=410,
           objetivo="La traza por correlation id es auditoria: el sucesor es /api/v1/auditoria/eventos, que sigue en 200 (ver arriba).", verifica=retirada("/api/v1/auditoria/eventos"))
    c.caso("la auditoria sigue en pie tras el corte", "GET", f"{API}/estado", rol="analista",
           objetivo="Retirar el analisis no toca la auditoria: la separacion que pidio el profe.", verifica=[("proteccion completa", lambda r: r.json["proteccion"]["completa"] is True)])
