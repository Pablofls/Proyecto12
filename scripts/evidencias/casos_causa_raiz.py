"""Casos de evidencia de causa-raiz (8011): RF-23, RF-24, RF-30, RN-09, RN-11, RN-12, RN-13, RNF-09.

Recorre los nueve pasos que pidio el profe con un lote real de la demo: alerta -> investigacion ->
evidencia -> hipotesis -> verificacion -> conclusion -> CAPA -> medicion -> cierre por un supervisor
que reconfirma su contrasena (auth 8001). Una segunda investigacion, manual y en XML, cubre la
conclusion inconclusa, la reapertura y el cierre independiente.

Datos que toca: investigaciones con titulo "Evidencia P4..." (y sus hipotesis, evidencias, acciones,
mediciones y linea de tiempo) y la alerta del lote de la demo, que se descarta y se restablece para poder
continuar el flujo. Todo se revierte al final; la bitacora se conserva (es de solo agregar).
"""
import re
from datetime import date, timedelta

SERVICIO = "causa-raiz"
SIGLA = "CR"
TITULO = "Causa raiz y acciones correctivas (CAPA)"
PUERTO = 8011
ARCHIVO = "causa_raiz"

API = "/api/v1/causa-raiz"
AUTH = "/api/v1/auth"
LOTE = "L-2026-PROB-01"
MARCA = "Evidencia P4"
DEVOLUCION_N = ("SELECT d.id FROM devoluciones d JOIN venta_detalle vd ON vd.id = d.venta_detalle_id "
                "JOIN lotes l ON l.id = vd.lote_id WHERE l.numero_lote = '" + LOTE + "' "
                "AND d.eliminado_en IS NULL ORDER BY d.id OFFSET %d LIMIT 1")
VEREDICTOS = ("efectiva", "no_efectiva", "sin_datos")


def tipo_error(r):
    return r.json["error"]["tipo"]


def id_xml(r):
    return int(re.search(r"<id>(\d+)</id>", r.texto).group(1))


def usuario(email):
    return f"SELECT id FROM usuarios WHERE email = '{email}'"


def ejecutar(c):
    hoy = date.today()
    compromiso = (hoy + timedelta(days=30)).isoformat()
    c.ctx.update(alerta=0, alerta_max=int(c.valor("SELECT COALESCE(MAX(id), 0) FROM alertas_patron")))
    c.ctx["lote"] = int(c.valor(f"SELECT id FROM lotes WHERE numero_lote = '{LOTE}'"))
    c.ctx["prov"] = int(c.valor(f"SELECT proveedor_id FROM lotes WHERE numero_lote = '{LOTE}'"))
    c.ctx["dev1"] = int(c.valor(DEVOLUCION_N % 0))
    c.ctx["dev_ajena"] = int(c.valor("SELECT d.id FROM devoluciones d JOIN venta_detalle vd ON vd.id = d.venta_detalle_id "
                                     "WHERE vd.lote_id <> {lote} AND d.eliminado_en IS NULL ORDER BY d.id LIMIT 1"))
    c.ctx["insp"] = int(c.valor(usuario("valentina.inspector@demo.mx")))
    c.ctx["carla"] = int(c.valor(usuario("carla.reembolsos@demo.mx")))
    c.ctx["cliente"] = int(c.valor(usuario("ana.cliente@demo.mx")))
    # Orden: lo que cuelga de las investigaciones primero; luego ellas; al final la alerta vuelve a su estado.
    de_la_corrida = f"(SELECT id FROM investigaciones WHERE titulo LIKE '{MARCA}%')"
    c.limpieza += [
        f"DELETE FROM mediciones_eficacia WHERE accion_id IN (SELECT id FROM acciones_capa WHERE investigacion_id IN {de_la_corrida})",
        f"DELETE FROM acciones_capa WHERE investigacion_id IN {de_la_corrida}",
        f"DELETE FROM evidencias_investigacion WHERE investigacion_id IN {de_la_corrida}",
        # Un porque no puede quedar sin padre (check) ni borrarse antes que su continuacion (RESTRICT): del nivel 5 al 2.
        *[f"DELETE FROM hipotesis WHERE investigacion_id IN {de_la_corrida} AND tipo = 'cinco_porques' AND nivel = {n}"
          for n in (5, 4, 3, 2)],
        f"DELETE FROM hipotesis WHERE investigacion_id IN {de_la_corrida}",
        f"DELETE FROM seguimiento_investigacion WHERE investigacion_id IN {de_la_corrida}",
        f"DELETE FROM investigaciones WHERE titulo LIKE '{MARCA}%'",
        "UPDATE alertas_patron SET estado = 'abierta', comentario = NULL, resuelta_por = NULL WHERE id = {alerta}",
        "DELETE FROM alertas_patron WHERE id > {alerta_max} AND id NOT IN "
        "(SELECT alerta_id FROM investigaciones WHERE alerta_id IS NOT NULL)",
    ]

    # ---------------------------------------------------------------- salud, contratos y Swagger
    c.caso("salud 200 JSON", "GET", "/health", objetivo="El servicio informa su estado y el de PostgreSQL y Redis (RF-32).",
           verifica=[("estado ok", lambda r: r.json["estado"] == "ok"),
                     ("PostgreSQL ok", lambda r: r.json["dependencias"]["postgresql"]["ok"] is True),
                     ("Redis ok", lambda r: r.json["dependencias"]["redis"]["ok"] is True)])
    c.caso("salud 200 XML", "GET", "/health", accept="application/xml", objetivo="El mismo endpoint responde XML (RF-31).",
           verifica=[("es XML", lambda r: r.tipo.startswith("application/xml")), ("estado ok", lambda r: "<estado>ok</estado>" in r.texto)])
    c.caso("Swagger: documentacion de la API", "GET", "/docs", accept="text/html", objetivo="La API publica su documentacion Swagger.",
           verifica=[("HTML de Swagger UI", lambda r: "swagger" in r.texto.lower())])
    c.caso("Swagger: especificacion OpenAPI", "GET", "/openapi.json", objetivo="La especificacion lista el flujo completo de la investigacion.",
           verifica=[("incluye el cierre", lambda r: f"{API}/investigaciones/{{id}}/cierre" in r.json["paths"]),
                     ("incluye la medicion", lambda r: f"{API}/acciones/{{id}}/mediciones" in r.json["paths"])])
    c.caso("contrato XSD publicado", "GET", "/contratos/investigacion.xsd", accept="application/xml",
           objetivo="El contrato XML de la investigacion se publica para que los clientes lo validen (RF-31).",
           verifica=[("es un esquema XSD", lambda r: "xs:schema" in r.texto and 'name="dimension"' in r.texto)])

    # ---------------------------------------------------------------- autenticacion y permisos
    c.caso("sin token: 401", "GET", f"{API}/alertas", espera=401, objetivo="Un endpoint protegido exige JWT (RNF-09).",
           verifica=[("tipo no_autenticado", lambda r: tipo_error(r) == "no_autenticado")])
    c.caso("token invalido: 401", "GET", f"{API}/alertas", espera=401, token="no.es.un.jwt", objetivo="Un token alterado se rechaza (RNF-09).",
           verifica=[("tipo token_invalido", lambda r: tipo_error(r) == "token_invalido")])
    c.caso("cliente: 403 en alertas", "GET", f"{API}/alertas", rol="cliente", espera=403,
           objetivo="Las alertas y las investigaciones son de Administrador, Analista y Supervisor (RN-13).",
           verifica=[("tipo sin_permiso", lambda r: tipo_error(r) == "sin_permiso")])
    c.caso("inspector: 403 en investigaciones", "GET", f"{API}/investigaciones", rol="inspector", espera=403,
           objetivo="El Inspector ve solo las acciones que se le asignan, no las investigaciones.",
           verifica=[("tipo sin_permiso", lambda r: tipo_error(r) == "sin_permiso")])

    # ---------------------------------------------------------------- pasos 1 y 2: patron y alerta
    c.caso("detectar patrones 200", "POST", f"{API}/alertas/detectar", rol="analista",
           objetivo="Paso 1: el sistema busca patrones raros (tasa >= 2x el promedio, 20 unidades, 3 casos). Repetirlo no duplica alertas.",
           verifica=[("cuenta alertas nuevas", lambda r: isinstance(r.json["alertas_nuevas"], int)),
                     ("declara el criterio", lambda r: r.json["criterio"]["unidades_minimas"] == 20),
                     ("aclara que no abre investigaciones", lambda r: "no abren investigaciones" in r.json["aviso"])],
           efecto=[("alertas abiertas por dimension", "SELECT dimension, count(*) AS abiertas FROM alertas_patron WHERE estado = 'abierta' GROUP BY dimension ORDER BY 1")])
    c.ctx["alerta"] = int(c.valor("SELECT id FROM alertas_patron WHERE dimension = 'lote' AND referencia_id = {lote} AND estado = 'abierta'"))
    c.caso("alertas 200: lote de la demo", "GET", f"{API}/alertas?estado=abierta&dimension=lote", rol="analista",
           objetivo="Paso 2: la alerta PROPONE investigar; ninguna investigacion se abre sola.",
           verifica=[("incluye la alerta del lote de la demo", lambda r: c.ctx["alerta"] in [a["id"] for a in r.json["datos"]]),
                     ("todas abiertas y de lotes", lambda r: all(a["estado"] == "abierta" and a["dimension"] == "lote" for a in r.json["datos"])),
                     ("cumple el criterio de alerta", lambda r: all(float(a["veces_promedio"]) >= 2 and a["casos"] >= 3 and a["unidades_vendidas"] >= 20 for a in r.json["datos"]))],
           efecto=[("ninguna investigacion existe aun sobre el lote",
                    "SELECT count(*) AS investigaciones_del_lote FROM investigaciones WHERE dimension = 'lote' AND referencia_id = {lote}")])
    c.caso("alertas 200 XML", "GET", f"{API}/alertas?por_pagina=2", rol="supervisor", accept="application/xml",
           objetivo="El listado de alertas responde XML (RF-31).",
           verifica=[("es XML", lambda r: r.tipo.startswith("application/xml")), ("raiz alertas", lambda r: "<alertas>" in r.texto)])
    c.caso("alertas 400 dimension desconocida", "GET", f"{API}/alertas?dimension=planeta", rol="analista", espera=400,
           objetivo="Un filtro fuera del catalogo se rechaza.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("descartar alerta 400 comentario corto", "POST", f"{API}/alertas/{{alerta}}/descartar", rol="analista", espera=400,
           json_cuerpo={"comentario": "no"}, objetivo="Descartar una alerta exige explicar por que (minimo 10 caracteres).",
           verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("descartar alerta 404", "POST", f"{API}/alertas/999999/descartar", rol="analista", espera=404,
           json_cuerpo={"comentario": "La alerta no existe en la base"}, objetivo="Una alerta inexistente responde 404.",
           verifica=[("tipo no_encontrado", lambda r: tipo_error(r) == "no_encontrado")])
    c.caso("descartar alerta 200", "POST", f"{API}/alertas/{{alerta}}/descartar", rol="analista",
           json_cuerpo={"comentario": "Prueba de evidencia: se descarta y luego se restablece para seguir el flujo"},
           objetivo="Una persona puede descartar una alerta con comentario; queda registrado quien.",
           verifica=[("queda descartada", lambda r: r.json["estado"] == "descartada")],
           efecto=[("estado y autor de la alerta", "SELECT id, estado, comentario, resuelta_por FROM alertas_patron WHERE id = {alerta}")])
    c.caso("descartar alerta 409 ya resuelta", "POST", f"{API}/alertas/{{alerta}}/descartar", rol="analista", espera=409,
           json_cuerpo={"comentario": "Segundo intento sobre la misma alerta"}, objetivo="Una alerta ya resuelta no se vuelve a resolver.",
           verifica=[("tipo alerta_resuelta", lambda r: tipo_error(r) == "alerta_resuelta")])
    c.caso("investigar alerta descartada: 409", "POST", f"{API}/alertas/{{alerta}}/investigar", rol="analista", espera=409,
           json_cuerpo={"titulo": f"{MARCA}: alerta descartada", "descripcion": "No debe abrirse desde una alerta descartada"},
           objetivo="Una alerta descartada ya no genera investigacion.",
           verifica=[("tipo alerta_resuelta", lambda r: tipo_error(r) == "alerta_resuelta")],
           efecto=[("paso preparatorio de la evidencia: la alerta vuelve a abierta para continuar el flujo",
                    "UPDATE alertas_patron SET estado = 'abierta', comentario = NULL, resuelta_por = NULL WHERE id = {alerta} RETURNING id, estado")])

    # ---------------------------------------------------------------- paso 3: abrir la investigacion
    c.caso("investigar alerta 400 campo no permitido", "POST", f"{API}/alertas/{{alerta}}/investigar", rol="analista", espera=400,
           json_cuerpo={"titulo": f"{MARCA}: lote", "descripcion": "El objeto lo define la alerta, no el cliente", "dimension": "proveedor"},
           objetivo="Desde una alerta el objeto ya viene dado; mandar otro se rechaza.",
           verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("investigar alerta 201", "POST", f"{API}/alertas/{{alerta}}/investigar", rol="analista", espera=201,
           json_cuerpo={"titulo": f"{MARCA}: leche del lote de la demo",
                        "descripcion": "Cuatro ventas del mismo lote concentran las devoluciones; se investiga la cadena de frio"},
           objetivo="Paso 3: una persona decide abrir la investigacion que la alerta propone. Queda con folio y linea base.",
           guarda={"inv_a": lambda r: r.json["id"]},
           verifica=[("nace abierta", lambda r: r.json["estado"] == "abierta"), ("folio INV-", lambda r: r.json["folio"].startswith("INV-")),
                     ("guarda la linea base", lambda r: r.json["linea_base"]["origen"] == "alerta"), ("trae Location", lambda r: "location" in r.cabeceras)],
           efecto=[("investigacion, alerta enlazada y primer evento de la linea de tiempo",
                    "SELECT i.folio, i.estado, i.dimension, i.alerta_id, a.estado AS estado_alerta, "
                    "(SELECT count(*) FROM seguimiento_investigacion s WHERE s.investigacion_id = i.id) AS eventos "
                    "FROM investigaciones i JOIN alertas_patron a ON a.id = i.alerta_id WHERE i.id = {inv_a}")])
    c.caso("investigar alerta 409 ya en investigacion", "POST", f"{API}/alertas/{{alerta}}/investigar", rol="analista", espera=409,
           json_cuerpo={"titulo": f"{MARCA}: duplicada", "descripcion": "La alerta ya tiene una investigacion en curso"},
           objetivo="Una alerta se investiga una sola vez.", verifica=[("tipo alerta_resuelta", lambda r: tipo_error(r) == "alerta_resuelta")])
    c.caso("investigacion manual 409 objeto ya investigado", "POST", f"{API}/investigaciones", rol="analista", espera=409,
           json_cuerpo={"dimension": "lote", "referencia_id": c.ctx["lote"], "titulo": f"{MARCA}: duplicada manual",
                        "descripcion": "Intento de abrir otra investigacion sobre el mismo lote"},
           objetivo="Un objeto no tiene dos investigaciones sin cerrar.", verifica=[("tipo investigacion_activa", lambda r: tipo_error(r) == "investigacion_activa")])
    c.caso("investigacion manual 400 dimension invalida", "POST", f"{API}/investigaciones", rol="analista", espera=400,
           json_cuerpo={"dimension": "planeta", "referencia_id": 1, "titulo": f"{MARCA}: invalida", "descripcion": "La dimension no existe en el catalogo"},
           objetivo="La dimension debe ser lote, proveedor, tienda o producto.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("investigacion manual 404 objeto inexistente", "POST", f"{API}/investigaciones", rol="analista", espera=404,
           json_cuerpo={"dimension": "lote", "referencia_id": 999999, "titulo": f"{MARCA}: lote fantasma", "descripcion": "El lote no existe en la base"},
           objetivo="No se investiga un objeto que no existe.", verifica=[("tipo no_encontrado", lambda r: tipo_error(r) == "no_encontrado")])
    c.caso("listado de investigaciones 200", "GET", f"{API}/investigaciones?estado=abierta&dimension=lote", rol="analista",
           objetivo="Listado filtrable con conteo de hipotesis, evidencias y acciones.",
           verifica=[("incluye la investigacion", lambda r: c.ctx["inv_a"] in [i["id"] for i in r.json["datos"]]),
                     ("trae conteos", lambda r: all(k in r.json["datos"][0] for k in ("hipotesis", "evidencias", "acciones")))])
    c.caso("listado de investigaciones 200 XML", "GET", f"{API}/investigaciones?por_pagina=2", rol="supervisor", accept="application/xml",
           objetivo="El listado responde XML (RF-31).", verifica=[("es XML", lambda r: r.tipo.startswith("application/xml"))])
    c.caso("listado de investigaciones 400 estado desconocido", "GET", f"{API}/investigaciones?estado=dormida", rol="analista", espera=400,
           objetivo="Un estado fuera del catalogo se rechaza.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("detalle de investigacion 404", "GET", f"{API}/investigaciones/999999", rol="analista", espera=404,
           objetivo="Una investigacion inexistente responde 404.", verifica=[("tipo no_encontrado", lambda r: tipo_error(r) == "no_encontrado")])

    # ---------------------------------------------------------------- paso 4: hipotesis (5 porques, Ishikawa)
    c.caso("hipotesis 400 tipo invalido", "POST", f"{API}/investigaciones/{{inv_a}}/hipotesis", rol="analista", espera=400,
           json_cuerpo={"tipo": "adivinanza", "descripcion": "Esto no es un tipo valido de hipotesis"},
           objetivo="El tipo es cinco_porques, ishikawa o libre.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("hipotesis 201: primer porque", "POST", f"{API}/investigaciones/{{inv_a}}/hipotesis", rol="analista", espera=201,
           json_cuerpo={"tipo": "cinco_porques", "descripcion": "Las devoluciones se concentran en el lote porque la leche llego tibia"},
           objetivo="Paso 4: el primer porque es el nivel 1; el nivel lo calcula el servicio.",
           guarda={"h1": lambda r: r.json["id"]}, verifica=[("nivel 1", lambda r: r.json["nivel"] == 1)])
    c.caso("hipotesis 201: segundo porque", "POST", f"{API}/investigaciones/{{inv_a}}/hipotesis", rol="analista", espera=201,
           json_cuerpo={"tipo": "cinco_porques", "padre_id": c.ctx["h1"], "descripcion": "Llego tibia porque el camion no mantuvo la cadena de frio"},
           objetivo="Un porque con padre es el nivel siguiente.",
           guarda={"h2": lambda r: r.json["id"]}, verifica=[("nivel 2", lambda r: r.json["nivel"] == 2)])
    c.caso("hipotesis 409 porque ya con continuacion", "POST", f"{API}/investigaciones/{{inv_a}}/hipotesis", rol="analista", espera=409,
           json_cuerpo={"tipo": "cinco_porques", "padre_id": c.ctx["h1"], "descripcion": "Otro porque para el mismo padre, sin ramificar"},
           objetivo="La cadena no se ramifica: cada porque tiene una sola continuacion.",
           verifica=[("tipo porque_con_continuacion", lambda r: tipo_error(r) == "porque_con_continuacion")])
    c.caso("hipotesis 409 porque padre inexistente", "POST", f"{API}/investigaciones/{{inv_a}}/hipotesis", rol="analista", espera=409,
           json_cuerpo={"tipo": "cinco_porques", "padre_id": 999999, "descripcion": "Continuacion de un porque que no existe"},
           objetivo="El porque anterior debe existir en esta investigacion.", verifica=[("tipo padre_invalido", lambda r: tipo_error(r) == "padre_invalido")])
    c.caso("hipotesis 400 Ishikawa sin categoria", "POST", f"{API}/investigaciones/{{inv_a}}/hipotesis", rol="analista", espera=400,
           json_cuerpo={"tipo": "ishikawa", "descripcion": "Falta decir a que rama del diagrama pertenece"},
           objetivo="Una hipotesis Ishikawa indica su categoria (6M).", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("hipotesis 201: Ishikawa", "POST", f"{API}/investigaciones/{{inv_a}}/hipotesis", rol="analista", espera=201,
           json_cuerpo={"tipo": "ishikawa", "categoria_ishikawa": "metodo", "descripcion": "El metodo de carga no respeta el tiempo maximo fuera de refrigeracion"},
           objetivo="Hipotesis en una rama del diagrama de Ishikawa.", guarda={"h3": lambda r: r.json["id"]},
           verifica=[("sin nivel de porque", lambda r: r.json["nivel"] is None)])
    c.caso("hipotesis 201 XML: libre", "POST", f"{API}/investigaciones/{{inv_a}}/hipotesis", rol="analista", espera=201, accept="application/xml",
           xml="<hipotesis><tipo>libre</tipo><descripcion>Un lote de empaque defectuoso podria explicar las bolsas danadas</descripcion></hipotesis>",
           objetivo="La misma alta en XML, validada contra su XSD (RF-31).", guarda={"h4": id_xml},
           verifica=[("es XML", lambda r: r.tipo.startswith("application/xml"))])

    # ---------------------------------------------------------------- evidencia
    c.caso("evidencia 400 devolucion sin devolucion_id", "POST", f"{API}/investigaciones/{{inv_a}}/evidencias", rol="analista", espera=400,
           json_cuerpo={"tipo": "devolucion", "descripcion": "Falta indicar cual devolucion respalda"},
           objetivo="Una evidencia de tipo devolucion o inspeccion apunta a una devolucion.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("evidencia 409 devolucion de otro lote", "POST", f"{API}/investigaciones/{{inv_a}}/evidencias", rol="analista", espera=409,
           json_cuerpo={"tipo": "devolucion", "descripcion": "Devolucion que no es de este lote", "devolucion_id": c.ctx["dev_ajena"]},
           objetivo="La evidencia debe pertenecer al objeto que se investiga.", verifica=[("tipo devolucion_ajena", lambda r: tipo_error(r) == "devolucion_ajena")])
    c.caso("evidencia 409 hipotesis ajena", "POST", f"{API}/investigaciones/{{inv_a}}/evidencias", rol="analista", espera=409,
           json_cuerpo={"tipo": "nota", "descripcion": "Apunta a una hipotesis que no es de esta investigacion", "hipotesis_id": 999999},
           objetivo="Una evidencia solo se liga a hipotesis de su investigacion.", verifica=[("tipo hipotesis_ajena", lambda r: tipo_error(r) == "hipotesis_ajena")])
    c.caso("evidencia 201: devolucion del lote", "POST", f"{API}/investigaciones/{{inv_a}}/evidencias", rol="analista", espera=201,
           json_cuerpo={"tipo": "devolucion", "descripcion": "Devolucion del lote reportada con producto tibio al recibirlo",
                        "devolucion_id": c.ctx["dev1"], "hipotesis_id": c.ctx["h1"]},
           objetivo="Evidencia ligada a una devolucion real del lote y a la primera hipotesis.", guarda={"ev1": lambda r: r.json["id"]},
           efecto=[("la evidencia guardada", "SELECT id, tipo, hipotesis_id, devolucion_id FROM evidencias_investigacion WHERE id = {ev1}")])
    c.caso("evidencia 201: nota", "POST", f"{API}/investigaciones/{{inv_a}}/evidencias", rol="analista", espera=201,
           json_cuerpo={"tipo": "nota", "descripcion": "El chofer confirma que la unidad estuvo detenida 40 minutos sin refrigeracion",
                        "referencia_externa": "bitacora-ruta-0412"},
           objetivo="Una nota de campo con referencia externa.", verifica=[("tipo nota", lambda r: r.json["tipo"] == "nota")])
    c.caso("detalle de investigacion 200", "GET", f"{API}/investigaciones/{{inv_a}}", rol="analista",
           objetivo="Una sola respuesta reune hipotesis, evidencias, acciones y linea de tiempo; recuerda que la conclusion es humana (RN-09).",
           verifica=[("4 hipotesis", lambda r: len(r.json["hipotesis"]) == 4), ("2 evidencias", lambda r: len(r.json["evidencias"]) == 2),
                     ("la evidencia trae el folio de la devolucion", lambda r: any(e["folio_devolucion"] for e in r.json["evidencias"])),
                     ("aviso de RN-09", lambda r: "RN-09" in r.json["aviso"])])

    # ---------------------------------------------------------------- paso 5: verificacion
    c.caso("concluir 409 sin pasar por verificacion", "POST", f"{API}/investigaciones/{{inv_a}}/conclusion", rol="analista", espera=409,
           json_cuerpo={"conclusion": "inconclusa", "justificacion": "Todavia no se verifico ninguna hipotesis"},
           objetivo="No se salta de abierta a concluida: el estado avanza paso a paso.", verifica=[("tipo transicion_invalida", lambda r: tipo_error(r) == "transicion_invalida")])
    c.caso("iniciar verificacion 200", "POST", f"{API}/investigaciones/{{inv_a}}/verificacion", rol="analista", json_cuerpo={},
           objetivo="Paso 5: pasa de juntar evidencia a verificar las hipotesis.", verifica=[("en_verificacion", lambda r: r.json["estado"] == "en_verificacion")])
    c.caso("iniciar verificacion 409 repetida", "POST", f"{API}/investigaciones/{{inv_a}}/verificacion", rol="analista", espera=409, json_cuerpo={},
           objetivo="No se puede iniciar dos veces.", verifica=[("tipo transicion_invalida", lambda r: tipo_error(r) == "transicion_invalida")])
    c.caso("concluir 409 sin hipotesis verificada", "POST", f"{API}/investigaciones/{{inv_a}}/conclusion", rol="analista", espera=409,
           json_cuerpo={"conclusion": "causa_confirmada", "causa_raiz": "El camion no mantuvo la cadena de frio",
                        "justificacion": "Hay evidencia pero ninguna hipotesis verificada"},
           objetivo="Confirmar una causa exige al menos una hipotesis verificada (RN-09).",
           verifica=[("tipo sin_hipotesis_verificada", lambda r: tipo_error(r) == "sin_hipotesis_verificada")])
    c.caso("verificar hipotesis 400 resultado invalido", "POST", f"{API}/investigaciones/{{inv_a}}/hipotesis/{{h1}}/verificacion", rol="analista", espera=400,
           json_cuerpo={"resultado": "quizas", "resultado_verificacion": "El resultado no es verificada ni descartada"},
           objetivo="El resultado es verificada o descartada.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("verificar hipotesis 404 inexistente", "POST", f"{API}/investigaciones/{{inv_a}}/hipotesis/999999/verificacion", rol="analista", espera=404,
           json_cuerpo={"resultado": "verificada", "resultado_verificacion": "La hipotesis no existe en esta investigacion"},
           objetivo="Solo se verifican hipotesis de la propia investigacion.", verifica=[("tipo no_encontrado", lambda r: tipo_error(r) == "no_encontrado")])
    c.caso("verificar hipotesis 200: verificada", "POST", f"{API}/investigaciones/{{inv_a}}/hipotesis/{{h1}}/verificacion", rol="analista",
           json_cuerpo={"resultado": "verificada", "resultado_verificacion": "El registro del termometro del camion confirma 14 C durante 40 minutos"},
           objetivo="La hipotesis se verifica con informacion adicional; queda quien y cuando.", verifica=[("verificada", lambda r: r.json["estado"] == "verificada")],
           efecto=[("estado de las hipotesis", "SELECT id, tipo, nivel, estado, verificada_por IS NOT NULL AS tiene_autor FROM hipotesis WHERE investigacion_id = {inv_a} ORDER BY id")])
    c.caso("verificar hipotesis 409 ya verificada", "POST", f"{API}/investigaciones/{{inv_a}}/hipotesis/{{h1}}/verificacion", rol="analista", espera=409,
           json_cuerpo={"resultado": "descartada", "resultado_verificacion": "Intento de cambiar una hipotesis ya verificada"},
           objetivo="Una hipotesis verificada no se reescribe.", verifica=[("tipo ya_verificada", lambda r: tipo_error(r) == "ya_verificada")])
    c.caso("verificar hipotesis 200: descartada", "POST", f"{API}/investigaciones/{{inv_a}}/hipotesis/{{h4}}/verificacion", rol="analista",
           json_cuerpo={"resultado": "descartada", "resultado_verificacion": "El empaque del lote cumple con la inspeccion de recepcion"},
           objetivo="Descartar tambien es un resultado valido y queda asentado.", verifica=[("descartada", lambda r: r.json["estado"] == "descartada")])

    # ---------------------------------------------------------------- paso 6: conclusion
    c.caso("concluir 400 causa confirmada sin causa", "POST", f"{API}/investigaciones/{{inv_a}}/conclusion", rol="analista", espera=400,
           json_cuerpo={"conclusion": "causa_confirmada", "justificacion": "Falta declarar cual es la causa raiz"},
           objetivo="Confirmar una causa exige describirla.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("concluir 400 inconclusa con causa", "POST", f"{API}/investigaciones/{{inv_a}}/conclusion", rol="analista", espera=400,
           json_cuerpo={"conclusion": "inconclusa", "causa_raiz": "No deberia declarar causa", "justificacion": "Una inconclusa no declara causa"},
           objetivo="Una investigacion inconclusa no inventa una causa (RN-09).", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("concluir 200 causa confirmada", "POST", f"{API}/investigaciones/{{inv_a}}/conclusion", rol="analista",
           json_cuerpo={"conclusion": "causa_confirmada", "causa_raiz": "El camion de reparto no mantuvo la cadena de frio durante una parada de 40 minutos",
                        "justificacion": "Hipotesis verificada con el termometro del camion y una devolucion del lote con producto tibio"},
           objetivo="Paso 6: causa confirmada, con evidencia y una hipotesis verificada. La decide una persona, no el sistema.",
           verifica=[("concluida", lambda r: r.json["estado"] == "concluida"), ("causa confirmada", lambda r: r.json["conclusion"] == "causa_confirmada")])
    c.caso("hipotesis 409 investigacion concluida", "POST", f"{API}/investigaciones/{{inv_a}}/hipotesis", rol="analista", espera=409,
           json_cuerpo={"tipo": "libre", "descripcion": "Ya no se agregan hipotesis tras concluir"},
           objetivo="Una investigacion concluida deja de editarse.", verifica=[("tipo investigacion_no_editable", lambda r: tipo_error(r) == "investigacion_no_editable")])

    # ---------------------------------------------------------------- paso 7: acciones CAPA
    c.caso("accion 409 responsable no interno", "POST", f"{API}/investigaciones/{{inv_a}}/acciones", rol="analista", espera=409,
           json_cuerpo={"tipo": "correctiva", "descripcion": "Responsable que es un cliente, no personal interno",
                        "responsable_id": c.ctx["cliente"], "fecha_compromiso": compromiso},
           objetivo="El responsable debe ser personal interno activo (RN-13).", verifica=[("tipo responsable_invalido", lambda r: tipo_error(r) == "responsable_invalido")])
    c.caso("accion 400 fecha pasada", "POST", f"{API}/investigaciones/{{inv_a}}/acciones", rol="analista", espera=400,
           json_cuerpo={"tipo": "correctiva", "descripcion": "La fecha compromiso no puede estar en el pasado",
                        "responsable_id": c.ctx["insp"], "fecha_compromiso": "2020-01-01"},
           objetivo="Toda accion tiene fecha compromiso futura.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("accion 201: correctiva", "POST", f"{API}/investigaciones/{{inv_a}}/acciones", rol="analista", espera=201,
           json_cuerpo={"tipo": "correctiva", "descripcion": "Exigir registro de temperatura en cada parada del camion de reparto",
                        "responsable_id": c.ctx["insp"], "fecha_compromiso": compromiso, "meta_reduccion_pct": "30"},
           objetivo="Paso 7: accion CAPA con responsable, fecha compromiso y meta medible. La investigacion pasa a en_accion.",
           guarda={"a1": lambda r: r.json["id"]},
           verifica=[("folio CAPA-", lambda r: r.json["folio"].startswith("CAPA-")), ("planificada", lambda r: r.json["estado"] == "planificada")],
           efecto=[("la investigacion avanza a en_accion", "SELECT folio, estado FROM investigaciones WHERE id = {inv_a}")])
    c.caso("accion 201: preventiva", "POST", f"{API}/investigaciones/{{inv_a}}/acciones", rol="supervisor", espera=201,
           json_cuerpo={"tipo": "preventiva", "descripcion": "Auditar trimestralmente los termometros de la flota",
                        "responsable_id": c.ctx["carla"], "fecha_compromiso": compromiso},
           objetivo="Una accion preventiva; sin meta, usa la predeterminada de 30%.", guarda={"a2": lambda r: r.json["id"]})
    c.caso("acciones 200: las ve un operador", "GET", f"{API}/acciones?investigacion_id={{inv_a}}", rol="analista",
           objetivo="Los operadores ven todas las acciones de una investigacion.",
           verifica=[("dos acciones", lambda r: r.json["paginacion"]["total"] == 2), ("traen responsable", lambda r: all(a["responsable"] for a in r.json["datos"]))])
    c.caso("acciones 200: cada responsable ve solo las suyas", "GET", f"{API}/acciones", rol="inspector",
           objetivo="El Inspector, responsable de una accion, ve solo la suya (RN-13).",
           verifica=[("solo acciones suyas", lambda r: r.json["paginacion"]["total"] >= 1 and all(a["responsable_id"] == c.ctx["insp"] for a in r.json["datos"]))])
    c.caso("acciones 200: vencidas", "GET", f"{API}/acciones?vencidas=true", rol="analista",
           objetivo="Filtra las acciones con fecha compromiso pasada y sin terminar.", verifica=[("todas marcadas vencidas", lambda r: all(a["vencida"] for a in r.json["datos"]))])
    c.caso("acciones 400 estado desconocido", "GET", f"{API}/acciones?estado=dormida", rol="analista", espera=400,
           objetivo="Un estado fuera del catalogo se rechaza.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("accion 200: detalle por su responsable", "GET", f"{API}/acciones/{{a1}}", rol="inspector",
           objetivo="El responsable consulta su accion con sus mediciones.", verifica=[("es la accion pedida", lambda r: r.json["id"] == c.ctx["a1"]), ("aun sin mediciones", lambda r: r.json["mediciones"] == [])])
    c.caso("accion 404 ajena: no revela que existe", "GET", f"{API}/acciones/{{a2}}", rol="inspector", espera=404,
           objetivo="Una accion de otra persona responde 404 y no 403, para no confirmar que existe (RN-13).",
           verifica=[("tipo no_encontrado", lambda r: tipo_error(r) == "no_encontrado")])

    # ---------------------------------------------------------------- paso 8: avance y medicion de eficacia
    c.caso("medir 409 accion no implementada", "POST", f"{API}/acciones/{{a1}}/mediciones", rol="analista", espera=409, json_cuerpo={},
           objetivo="Solo se mide una accion que ya se implemento.", verifica=[("tipo accion_no_implementada", lambda r: tipo_error(r) == "accion_no_implementada")])
    c.caso("cierre 409 con acciones sin medir", "POST", f"{API}/investigaciones/{{inv_a}}/cierre", rol="supervisor", espera=409,
           json_cuerpo={"comentario": "Intento de cerrar antes de medir la eficacia"},
           objetivo="No se cierra mientras haya acciones sin medir: el cierre no esconde si algo funciono.",
           verifica=[("tipo requiere_medicion", lambda r: tipo_error(r) == "requiere_medicion")])
    c.caso("accion 409 saltar a implementada", "POST", f"{API}/acciones/{{a1}}/estado", rol="inspector", espera=409,
           json_cuerpo={"estado": "implementada"}, objetivo="La accion avanza planificada, en curso, implementada; no se salta un paso.",
           verifica=[("tipo transicion_invalida", lambda r: tipo_error(r) == "transicion_invalida")])
    c.caso("accion 404 ajena no se mueve", "POST", f"{API}/acciones/{{a2}}/estado", rol="inspector", espera=404,
           json_cuerpo={"estado": "en_curso"}, objetivo="Quien no es responsable ni operador no puede mover la accion.",
           verifica=[("tipo no_encontrado", lambda r: tipo_error(r) == "no_encontrado")])
    c.caso("accion 200: en curso por su responsable", "POST", f"{API}/acciones/{{a1}}/estado", rol="inspector",
           json_cuerpo={"estado": "en_curso"}, objetivo="El responsable avanza su accion.", verifica=[("en_curso", lambda r: r.json["estado"] == "en_curso")])
    c.caso("accion 400 implementada en fecha futura", "POST", f"{API}/acciones/{{a1}}/estado", rol="inspector", espera=400,
           json_cuerpo={"estado": "implementada", "fecha_implementacion": (hoy + timedelta(days=5)).isoformat()},
           objetivo="No se declara implementada una accion con fecha futura.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("accion 200: implementada", "POST", f"{API}/acciones/{{a1}}/estado", rol="inspector",
           json_cuerpo={"estado": "implementada", "fecha_implementacion": (hoy - timedelta(days=45)).isoformat()},
           objetivo="Se implementa con su fecha real; de ella dependen los periodos de la medicion.",
           verifica=[("implementada", lambda r: r.json["estado"] == "implementada")])
    c.caso("accion 400 cancelar sin comentario", "POST", f"{API}/acciones/{{a2}}/estado", rol="analista", espera=400,
           json_cuerpo={"estado": "cancelada"}, objetivo="Cancelar una accion exige explicar por que.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("accion 200: cancelada con motivo", "POST", f"{API}/acciones/{{a2}}/estado", rol="analista",
           json_cuerpo={"estado": "cancelada", "comentario": "Se difiere a la siguiente auditoria anual"},
           objetivo="Una accion cancelada no cuenta para el cierre.", verifica=[("cancelada", lambda r: r.json["estado"] == "cancelada")])
    c.caso("medir 403 inspector", "POST", f"{API}/acciones/{{a1}}/mediciones", rol="inspector", espera=403, json_cuerpo={},
           objetivo="Medir es de Administrador, Analista y Supervisor.", verifica=[("tipo sin_permiso", lambda r: tipo_error(r) == "sin_permiso")])
    c.caso("medir 400 ventana invalida", "POST", f"{API}/acciones/{{a1}}/mediciones", rol="analista", espera=400,
           json_cuerpo={"ventana_antes_dias": 3}, objetivo="La ventana de comparacion es de 7 a 365 dias.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("medir 201: antes contra despues", "POST", f"{API}/acciones/{{a1}}/mediciones", rol="analista", espera=201,
           json_cuerpo={"ventana_antes_dias": 90},
           objetivo="Paso 8: tasa de lo vendido antes contra lo vendido despues, sin contar lo que aun puede devolverse. Con poca muestra el veredicto es sin_datos, nunca efectiva.",
           guarda={"med1": lambda r: r.json["id"]},
           verifica=[("veredicto conocido", lambda r: r.json["veredicto"] in VEREDICTOS),
                     ("sin_datos explica por que", lambda r: r.json["veredicto"] != "sin_datos" or bool(r.json["motivo_sin_datos"])),
                     ("aclara que no prueba causalidad", lambda r: "RN-09" in r.json["aviso"])],
           efecto=[("la medicion y el nuevo estado de la investigacion",
                    "SELECT m.veredicto, m.antes_vendidas, m.antes_devueltas, m.despues_vendidas, m.meta_reduccion_pct, i.estado "
                    "FROM mediciones_eficacia m JOIN acciones_capa a ON a.id = m.accion_id JOIN investigaciones i ON i.id = a.investigacion_id WHERE m.id = {med1}")])
    c.caso("accion 200: detalle con su medicion", "GET", f"{API}/acciones/{{a1}}", rol="inspector",
           objetivo="El responsable ve el resultado de la medicion de su accion.", verifica=[("una medicion", lambda r: len(r.json["mediciones"]) == 1)])

    # ---------------------------------------------------------------- paso 9: cierre con reconfirmacion de contrasena
    c.caso("cierre 403 analista", "POST", f"{API}/investigaciones/{{inv_a}}/cierre", rol="analista", espera=403,
           json_cuerpo={"comentario": "El analista no puede cerrar investigaciones"},
           objetivo="Cerrar es solo de un Supervisor (RN-13).", verifica=[("tipo sin_permiso", lambda r: tipo_error(r) == "sin_permiso")])
    c.caso("cierre 403 sin reconfirmar la contrasena", "POST", f"{API}/investigaciones/{{inv_a}}/cierre", rol="supervisor", espera=403,
           json_cuerpo={"comentario": "Cierre sin permiso de operacion critica"},
           objetivo="Aunque todo lo demas este en orden, cerrar exige reconfirmar la contrasena (operacion critica).",
           verifica=[("tipo autorizacion_operacion_requerida", lambda r: tipo_error(r) == "autorizacion_operacion_requerida")])
    c.caso("autorizar operacion 403 analista", "POST", f"{AUTH}/autorizar-operacion", rol="analista", espera=403, puerto=8001,
           json_cuerpo={"operacion": "cerrar_investigacion", "recurso_id": str(c.ctx["inv_a"]), "password": "$PASSWORD_DEMO"},
           objetivo="Solo un Supervisor puede autorizar el cierre de una investigacion.", verifica=[("tipo sin_permiso", lambda r: tipo_error(r) == "sin_permiso")])
    c.caso("autorizar operacion 401 contrasena incorrecta", "POST", f"{AUTH}/autorizar-operacion", rol="supervisor", espera=401, puerto=8001,
           json_cuerpo={"operacion": "cerrar_investigacion", "recurso_id": str(c.ctx["inv_a"]), "password": "contrasena-incorrecta-de-prueba"},
           objetivo="Una contrasena equivocada no emite permiso; el intento queda en la bitacora.",
           verifica=[("tipo credenciales_invalidas", lambda r: tipo_error(r) == "credenciales_invalidas")])

    def permiso(r):
        c.esconder(r.json["token_operacion"])
        return r.json["token_operacion"]

    c.caso("autorizar operacion 201 sobre otro registro", "POST", f"{AUTH}/autorizar-operacion", rol="supervisor", espera=201, puerto=8001,
           json_cuerpo={"operacion": "cerrar_investigacion", "recurso_id": "999999", "password": "$PASSWORD_DEMO"},
           objetivo="Un permiso se emite para UN registro; este es de otro, para probar que no sirve aqui.",
           guarda={"permiso_ajeno": permiso}, verifica=[("vigencia 5 minutos", lambda r: r.json["expires_in"] == 300)])
    c.caso("cierre 403 permiso de otro registro", "POST", f"{API}/investigaciones/{{inv_a}}/cierre", rol="supervisor", espera=403,
           json_cuerpo={"comentario": "Intento de cerrar con el permiso de otro registro"},
           cabeceras_extra={"X-Autorizacion-Operacion": c.ctx["permiso_ajeno"]},
           objetivo="El permiso vale para un solo registro.", verifica=[("tipo autorizacion_operacion_invalida", lambda r: tipo_error(r) == "autorizacion_operacion_invalida")])
    c.caso("autorizar operacion 201", "POST", f"{AUTH}/autorizar-operacion", rol="supervisor", espera=201, puerto=8001,
           json_cuerpo={"operacion": "cerrar_investigacion", "recurso_id": str(c.ctx["inv_a"]), "password": "$PASSWORD_DEMO"},
           objetivo="El supervisor reconfirma su contrasena y recibe un permiso de un solo uso para esta investigacion.",
           guarda={"permiso": permiso},
           efecto=[("la autorizacion queda en la bitacora, sin la contrasena",
                    "SELECT accion, entidad, detalle FROM bitacora WHERE accion = 'autorizacion_operacion' ORDER BY id DESC LIMIT 1")])
    c.caso("cierre 400 comentario corto", "POST", f"{API}/investigaciones/{{inv_a}}/cierre", rol="supervisor", espera=400,
           json_cuerpo={"comentario": "ok"}, cabeceras_extra={"X-Autorizacion-Operacion": c.ctx["permiso"]},
           objetivo="La validacion ocurre antes de consumir el permiso: un error de captura no lo gasta.", verifica=[("tipo validacion", lambda r: tipo_error(r) == "validacion")])
    c.caso("cierre 200 por un supervisor distinto del analista", "POST", f"{API}/investigaciones/{{inv_a}}/cierre", rol="supervisor",
           json_cuerpo={"comentario": "Medicion revisada; se cierra la investigacion con el veredicto que arrojo la medicion"},
           cabeceras_extra={"X-Autorizacion-Operacion": c.ctx["permiso"]},
           objetivo="Paso 9: lo cierra un supervisor distinto del analista, con permiso de un solo uso. El veredicto sale de las mediciones, no del cierre.",
           verifica=[("cerrada", lambda r: r.json["estado"] == "cerrada"), ("veredicto conocido", lambda r: r.json["veredicto_final"] in VEREDICTOS)],
           efecto=[("investigacion cerrada y quien la cerro", "SELECT folio, estado, veredicto_final, cerrada_por IS NOT NULL AS tiene_autor_del_cierre, "
                    "cerrada_por <> analista_id AS cierra_otra_persona FROM investigaciones WHERE id = {inv_a}"),
                   ("el cierre en la bitacora", "SELECT accion, entidad, detalle FROM bitacora WHERE accion = 'cierre_investigacion' ORDER BY id DESC LIMIT 1")])
    c.caso("cierre 409 ya cerrada", "POST", f"{API}/investigaciones/{{inv_a}}/cierre", rol="supervisor", espera=409,
           json_cuerpo={"comentario": "Segundo intento de cerrar la misma investigacion"},
           objetivo="Una investigacion cerrada no vuelve a abrirse ni a cerrarse.", verifica=[("tipo transicion_invalida", lambda r: tipo_error(r) == "transicion_invalida")])
    c.caso("detalle final: linea de tiempo completa", "GET", f"{API}/investigaciones/{{inv_a}}", rol="supervisor",
           objetivo="La linea de tiempo registra cada cambio de estado, en orden.",
           verifica=[("termina cerrada", lambda r: r.json["estado"] == "cerrada"),
                     ("6 eventos: uno por estado", lambda r: len(r.json["seguimiento"]) == 6),
                     ("pasa por todos los estados", lambda r: {"abierta", "en_verificacion", "concluida", "en_accion", "en_medicion", "cerrada"}
                      <= {e["estado_nuevo"] for e in r.json["seguimiento"]})])

    # ---------------------------------------------------------------- segunda investigacion: manual, XML, inconclusa
    c.caso("investigacion manual 201 XML", "POST", f"{API}/investigaciones", rol="supervisor", espera=201, accept="application/xml",
           xml=("<investigacion><dimension>proveedor</dimension><referencia_id>%d</referencia_id>"
                "<titulo>%s: proveedor del lote de la demo</titulo>"
                "<descripcion>Investigacion abierta a mano sobre el proveedor, enviada por XML</descripcion></investigacion>" % (c.ctx["prov"], MARCA)),
           objetivo="Una investigacion manual, sin alerta previa, por contrato XML (RF-31).", guarda={"inv_b": id_xml},
           verifica=[("trae folio", lambda r: "<folio>INV-" in r.texto)],
           efecto=[("nace sin alerta y a nombre de quien la abre", "SELECT folio, dimension, alerta_id, estado, linea_base->>'origen' AS origen FROM investigaciones WHERE id = {inv_b}")])
    c.caso("iniciar verificacion 409 sin hipotesis", "POST", f"{API}/investigaciones/{{inv_b}}/verificacion", rol="supervisor", espera=409, json_cuerpo={},
           objetivo="No se verifica sin haber escrito al menos una hipotesis.", verifica=[("tipo sin_hipotesis", lambda r: tipo_error(r) == "sin_hipotesis")])
    c.caso("hipotesis 201 en la segunda investigacion", "POST", f"{API}/investigaciones/{{inv_b}}/hipotesis", rol="supervisor", espera=201,
           json_cuerpo={"tipo": "libre", "descripcion": "El proveedor cambio de planta de envasado este trimestre"},
           objetivo="Hipotesis libre.", guarda={"hb": lambda r: r.json["id"]})
    c.caso("iniciar verificacion 200 en la segunda", "POST", f"{API}/investigaciones/{{inv_b}}/verificacion", rol="supervisor", json_cuerpo={},
           objetivo="Pasa a verificacion.", verifica=[("en_verificacion", lambda r: r.json["estado"] == "en_verificacion")])
    c.caso("verificar hipotesis 200: descartada en la segunda", "POST", f"{API}/investigaciones/{{inv_b}}/hipotesis/{{hb}}/verificacion", rol="supervisor",
           json_cuerpo={"resultado": "descartada", "resultado_verificacion": "El proveedor confirma que la planta de envasado no cambio"},
           objetivo="La unica hipotesis se descarta.", verifica=[("descartada", lambda r: r.json["estado"] == "descartada")])
    c.caso("concluir 409 confirmar sin evidencia", "POST", f"{API}/investigaciones/{{inv_b}}/conclusion", rol="supervisor", espera=409,
           json_cuerpo={"conclusion": "causa_confirmada", "causa_raiz": "Cambio de planta del proveedor", "justificacion": "Sin evidencia ni hipotesis verificada"},
           objetivo="Confirmar exige evidencia (RN-09); aqui no hay ninguna.", verifica=[("tipo sin_evidencia", lambda r: tipo_error(r) == "sin_evidencia")])
    c.caso("concluir 200 inconclusa", "POST", f"{API}/investigaciones/{{inv_b}}/conclusion", rol="supervisor",
           json_cuerpo={"conclusion": "inconclusa", "justificacion": "No se hallo evidencia suficiente para atribuir la causa al proveedor"},
           objetivo="El sistema acepta que no se encontro la causa: concluir inconclusa es valido y honesto (RN-09).",
           verifica=[("inconclusa", lambda r: r.json["conclusion"] == "inconclusa")])
    c.caso("accion 409 sin causa confirmada", "POST", f"{API}/investigaciones/{{inv_b}}/acciones", rol="supervisor", espera=409,
           json_cuerpo={"tipo": "correctiva", "descripcion": "No se corrige una causa que no se confirmo",
                        "responsable_id": c.ctx["insp"], "fecha_compromiso": compromiso},
           objetivo="Las acciones se crean cuando la causa esta confirmada.", verifica=[("tipo sin_causa_confirmada", lambda r: tipo_error(r) == "sin_causa_confirmada")])
    c.caso("cierre 409 el analista no cierra lo suyo", "POST", f"{API}/investigaciones/{{inv_b}}/cierre", rol="supervisor", espera=409,
           json_cuerpo={"comentario": "El mismo supervisor que la lleva intenta cerrarla"},
           objetivo="Quien lleva la investigacion no puede cerrarla: lo hace otro supervisor (separacion de funciones).",
           verifica=[("tipo cierre_independiente", lambda r: tipo_error(r) == "cierre_independiente")])
    c.caso("reabrir 200 una inconclusa", "POST", f"{API}/investigaciones/{{inv_b}}/reabrir", rol="analista",
           json_cuerpo={"comentario": "Llego informacion nueva del proveedor"},
           objetivo="Una inconclusa vuelve a verificacion si aparece mas informacion.", verifica=[("en_verificacion", lambda r: r.json["estado"] == "en_verificacion")],
           efecto=[("la conclusion se limpia y queda en la linea de tiempo",
                    "SELECT i.estado, i.conclusion, (SELECT count(*) FROM seguimiento_investigacion s WHERE s.investigacion_id = i.id) AS eventos FROM investigaciones i WHERE i.id = {inv_b}")])
    c.caso("reabrir 409 si no esta concluida inconclusa", "POST", f"{API}/investigaciones/{{inv_b}}/reabrir", rol="analista", espera=409,
           json_cuerpo={"comentario": "Ya esta reabierta, no hay nada que reabrir"},
           objetivo="Solo se reabre una investigacion concluida como inconclusa.", verifica=[("tipo no_reabrible", lambda r: tipo_error(r) == "no_reabrible")])
