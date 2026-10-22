"""Casos de prueba de los 8 servicios (una funcion por servicio).

Cada codigo de estado, error.tipo y rol sale de services/<x>/app.py; si un
servicio cambia, se corrige aqui y se regenera (generar_colecciones.py). Los
textos pg / mongo / redis dicen que debe verse en cada base tras el caso: son
las consultas que se capturan en la VM (docs/evidencias/README.md).

Orden recomendado de corrida (reproduce el proceso completo de devolucion):
auth, ventas_catalogos, devoluciones, logistica, inspecciones, evidencias,
reembolsos_costos, analisis_auditoria.
"""
from generar_colecciones import jb, xb

BIT = ("`SELECT accion, entidad, entidad_id, detalle FROM bitacora "
       "ORDER BY id DESC LIMIT 3;` (RF-30).")
EVT = "`db.eventos.find({{servicio:'{s}'}}).sort({{fecha:-1}}).limit(2)` (RNF-23)."


def tj(nombre, cond):
    """Verificacion sobre la respuesta JSON (J es el cuerpo ya interpretado)."""
    return (f'pm.test("{nombre}", () => {{ const J = pm.response.json(); '
            f'pm.expect({cond}).to.be.true; }});')


def tx(nombre, cond):
    """Verificacion sobre la respuesta XML (X es el cuerpo convertido a objeto)."""
    return (f'pm.test("{nombre}", () => {{ const X = xml2Json(pm.response.text()); '
            f'pm.expect({cond}).to.be.true; }});')


def salud(c, dependencias=("postgresql", "redis")):
    c.caso("health 200", "GET", "/health",
           "RNF-22, RF-32: el servicio responde y reporta el estado de sus dependencias.",
           tests=[tj(f"{d} ok", f"J.dependencias.{d}.ok === true") for d in dependencias],
           pg="`SELECT 1;` desde el contenedor; el servicio hace la misma comprobacion.",
           redis="`redis-cli PING` responde PONG.",
           mongo="`mongosh --eval \"db.runCommand({ping:1})\"`" if "mongodb" in dependencias else None)


# =========================================================================== #
# auth (8001)
# =========================================================================== #
def auth(c):
    c.carpeta("00 Salud y contratos")
    salud(c)
    c.caso("health 200 XML", "GET", "/health", "Mismo health en XML (Accept: application/xml).",
           accept="xml", tests=[tx("estado ok", 'X.respuesta.estado === "ok"')])
    c.caso("contrato login.xsd 200", "GET", "/contratos/login.xsd",
           "Los contratos XSD se publican en el propio servicio.",
           tests=['pm.test("es un esquema XSD", () => pm.expect(pm.response.text()).to.include("xs:schema"));'],
           ev=False)

    c.carpeta("01 Login")
    login = {"email": "{{email_analista}}", "password": "{{password_demo}}"}
    c.caso("login 200 exitoso", "POST", "/login",
           "RF-01, HU-01: el analista inicia sesion y recibe access_token y refresh_token (JWT).",
           body=login, rol=None,
           tests=[tj("emite el par de tokens", 'J.token_type === "Bearer" && !!J.access_token && !!J.refresh_token && J.expires_in > 0'),
                  tj("el rol viaja en la respuesta", 'J.usuario.rol === "Analista de Devoluciones"')],
           guarda={"token_analista": "pm.response.json().access_token",
                   "refresh_token": "pm.response.json().refresh_token",
                   "analista_id": "pm.response.json().usuario.id"},
           explica="Valida correo y contrasena, abre la sesion en Redis y firma access (corto) y refresh (8 h) con HS256.",
           pg="`SELECT email, exitoso, ip_origen, fecha FROM intentos_acceso ORDER BY id DESC LIMIT 3;` y bitacora `login_api`: " + BIT,
           redis="`redis-cli --scan --pattern 'devoluciones:sesion_api:*'`; `HGETALL` de la clave (usuario_id, rol, ip) y `TTL` (cerca de 28800 s); "
                 "`SMEMBERS devoluciones:sesiones_usuario:<id>`; `GET devoluciones:limite:<ip>:login` (contador de la ventana de 60 s).")
    c.caso("login 200 XML (admin)", "POST", "/login",
           "El mismo login con cuerpo y respuesta XML validados contra login.xsd.",
           fmt="xml", body=xb("login", email="{{email_admin}}", password="{{password_demo}}"),
           guarda={"token_admin": "xml2Json(pm.response.text()).respuesta.access_token"},
           tests=[tx("trae access_token", "!!X.respuesta.access_token")])
    c.caso("login 400 datos invalidos", "POST", "/login", "Validacion: correo mal formado y contrasena vacia.",
           body={"email": "no-es-correo", "password": ""}, codigo=400, tipo="validacion")
    c.caso("login 401 credenciales invalidas", "POST", "/login",
           "RNF-16: el mensaje es generico, no revela si el correo existe. Se usa un correo inexistente para no bloquear usuarios reales.",
           body={"email": "nadie@demo.mx", "password": "incorrecta"}, codigo=401, tipo="credenciales_invalidas",
           pg="`SELECT email, exitoso FROM intentos_acceso ORDER BY id DESC LIMIT 1;` (exitoso = f).",
           redis="`GET devoluciones:intentos:nadie@demo.mx` -> 1 y su `TTL` (900 s).")
    c.caso("login 415 formato no soportado", "POST", "/login", "Content-Type distinto de JSON/XML.",
           contenido="text/plain", body="email=x", codigo=415, tipo="formato_no_soportado")
    c.caso("login 400 XML mal formado", "POST", "/login", "XML que no esta bien formado.",
           fmt="xml", body="<login><email>x</login>", codigo=400, tipo="xml_invalido")
    c.caso("login 400 XML no cumple XSD", "POST", "/login", "XML bien formado al que le falta password (login.xsd).",
           fmt="xml", body=xb("login", email="{{email_analista}}"), codigo=400, tipo="xml_no_cumple_xsd")

    c.carpeta("02 Sesion")
    c.caso("sesion 200 exitoso", "GET", "/sesion", "Datos de la sesion vigente y segundos que le quedan.",
           rol="analista", tests=[tj("trae sesion_id y usuario", "!!J.sesion_id && !!J.usuario.id")],
           redis="`TTL devoluciones:sesion_api:<sesion_id>` coincide con `sesion_expira_en_seg`.")
    c.caso("sesion 200 XML", "GET", "/sesion", "Respuesta en XML.", rol="analista", accept="xml",
           tests=[tx("trae sesion_id", "!!X.respuesta.sesion_id")])
    c.caso("sesion 401 sin token", "GET", "/sesion", "Endpoint protegido sin Authorization.",
           codigo=401, tipo="no_autenticado")
    c.caso("sesion 401 token invalido", "GET", "/sesion", "RNF-07: un JWT sin firma valida se rechaza.",
           rol="falso", codigo=401, tipo="token_invalido")

    c.carpeta("03 Refresh")
    c.caso("refresh 200 exitoso", "POST", "/refresh", "Cambia el refresh_token por un access_token nuevo.",
           body={"refresh_token": "{{refresh_token}}"},
           tests=[tj("access nuevo", "!!J.access_token")],
           guarda={"token_analista": "pm.response.json().access_token"},
           redis="`GET devoluciones:limite:<ip>:refresh` (maximo 30 por minuto).")
    c.caso("refresh 401 con access token", "POST", "/refresh", "Un access token no sirve como refresh (claim typ).",
           body={"refresh_token": "{{token_analista}}"}, codigo=401, tipo="token_invalido")
    c.caso("refresh 400 sin refresh_token", "POST", "/refresh", "Falta el campo obligatorio.",
           body={}, codigo=400, tipo="validacion")

    c.carpeta("04 Administracion de sesiones")
    c.caso("cerrar sesiones 403 rol sin permiso", "DELETE", "/usuarios/{{analista_id}}/sesiones",
           "RNF-09: solo el Administrador cierra sesiones ajenas.", rol="analista", codigo=403, tipo="sin_permiso")
    c.caso("cerrar sesiones 404 usuario inexistente", "DELETE", "/usuarios/999999/sesiones",
           "Usuario que no existe.", rol="admin", codigo=404, tipo="no_encontrado")

    c.carpeta("05 Revocacion")
    c.caso("logout 200 exitoso", "POST", "/logout", "RNF-08: revoca el token y cierra la sesion.",
           rol="analista", body={},
           explica="Agrega el jti del access token a la lista negra con TTL igual a su vida restante y borra la sesion.",
           redis="`GET devoluciones:jwt_revocado:<jti>` -> \"1\" con `TTL` > 0; la clave `devoluciones:sesion_api:<sid>` ya no existe (`EXISTS` -> 0).",
           pg="Bitacora `logout_api`: " + BIT)
    c.caso("sesion 401 token revocado", "GET", "/sesion", "El mismo token ya no sirve tras el logout.",
           rol="analista", codigo=401, tipo="token_revocado")
    c.caso("refresh 401 sesion inactiva", "POST", "/refresh", "El refresh de una sesion cerrada tampoco sirve.",
           body={"refresh_token": "{{refresh_token}}"}, codigo=401, tipo="sesion_inactiva")
    c.caso("login 200 nueva sesion", "POST", "/login", "Nueva sesion del analista para la prueba siguiente.",
           body=login, ev=False,
           guarda={"token_analista": "pm.response.json().access_token",
                   "analista_id": "pm.response.json().usuario.id"})
    c.caso("cerrar sesiones 200 admin", "DELETE", "/usuarios/{{analista_id}}/sesiones",
           "RNF-08: el administrador cierra todas las sesiones de un usuario sin esperar a que expiren.",
           rol="admin", tests=[tj("cerro al menos una", "J.sesiones_cerradas >= 1")],
           redis="`SMEMBERS devoluciones:sesiones_usuario:<id>` queda vacio y `EXISTS devoluciones:sesion_api:<sid>` -> 0.",
           pg="Bitacora `revocar_sesiones`: " + BIT)
    c.caso("sesion 401 sesion inactiva", "GET", "/sesion", "El token sigue firmado pero su sesion ya no existe en Redis.",
           rol="analista", codigo=401, tipo="sesion_inactiva")

    c.carpeta("06 Casos limite (correr aparte, bloquea una cuenta 15 min)")
    def repetir(variable, objetivo):
        """Repite la misma peticion con setNextRequest hasta ver el codigo buscado."""
        return [f'const n = Number(pm.environment.get("{variable}") || 0) + 1;',
                f'pm.environment.set("{variable}", n);',
                f'if (pm.response.code === {objetivo} || n >= 12) {{',
                f'  pm.test("HTTP {objetivo} tras " + n + " intentos", () => pm.response.to.have.status({objetivo}));',
                f'  pm.environment.set("{variable}", 0);',
                '} else {',
                '  postman.setNextRequest(pm.info.requestName);',
                '}']
    c.caso("login 423 cuenta bloqueada", "POST", "/login",
           "RNF-12: tras 5 intentos fallidos la cuenta se bloquea 15 min; la peticion se repite sola hasta recibir 423. "
           "Usa email_bloqueo (Sofia) para no bloquear a los usuarios de las demas colecciones. Para desbloquear antes: "
           "`redis-cli DEL devoluciones:bloqueo:<correo> devoluciones:intentos:<correo>` y "
           "`UPDATE usuarios SET bloqueado_hasta = NULL WHERE email = '<correo>';`.",
           body={"email": "{{email_bloqueo}}", "password": "contrasena-incorrecta"}, codigo=423, tipo="cuenta_bloqueada",
           solo_tests=True, tests=repetir("intentos_bloqueo", 423),
           pg="`SELECT email, bloqueado_hasta FROM usuarios WHERE email = '<correo>';` y bitacora `cuenta_bloqueada`: " + BIT,
           redis="`GET devoluciones:intentos:<correo>` (contador) y `GET`/`TTL devoluciones:bloqueo:<correo>` (900 s).")
    c.caso("login 429 rate limit", "POST", "/login",
           "RNF-13: mas de 10 logins por minuto desde la misma IP; se repite sola hasta recibir 429 y se revisa Retry-After.",
           body={"email": "nadie@demo.mx", "password": "x"}, codigo=429, tipo="demasiadas_peticiones",
           solo_tests=True, tests=repetir("intentos_limite", 429),
           redis="`GET devoluciones:limite:<ip>:login` > 10 y `TTL` <= 60.")


# =========================================================================== #
# devoluciones (8002)
# =========================================================================== #
NUEVA = {"venta_detalle_id": "@id:venta_detalle_id", "motivo_id": "@id:motivo_id",
         "descripcion_problema": "El empaque llego roto y el producto derramado.",
         "cantidad_devuelta": 1}


def devoluciones(c):
    c.carpeta("00 Preparacion (tokens)")
    salud(c, ("postgresql", "redis", "mongodb"))
    for r in ("cliente", "otro", "analista"):
        c.login(r)

    c.carpeta("01 Registro (POST)")
    c.caso("registrar 409 cantidad excedida", "POST", "", "Regla de negocio RN-01: no se devuelve mas de lo comprado. "
           "Va primero: si la linea ya no tuviera unidades la respuesta seria sin_disponible.",
           rol="cliente", body={**NUEVA, "cantidad_devuelta": 999}, codigo=409, tipo="cantidad_excedida")
    c.caso("registrar 201 exitoso", "POST", "", "RF-07, RN-01: el cliente registra una devolucion sobre su compra.",
           rol="cliente", body=NUEVA, codigo=201,
           tests=[tj("estado solicitada", 'J.estado === "solicitada"'),
                  'pm.test("Location al expediente", () => pm.expect(pm.response.headers.get("Location")).to.include("/api/v1/devoluciones/"));'],
           guarda={"devolucion_id": "pm.response.json().id", "folio": "pm.response.json().folio_devolucion"},
           explica="Valida la compra (es del cliente, hay unidades), inserta la devolucion en estado `solicitada`, "
                   "escribe bitacora y publica el evento `devolucion_registrada`. Limite: 20 por minuto por usuario.",
           pg="`SELECT id, folio_devolucion, estado, cantidad_devuelta FROM devoluciones ORDER BY id DESC LIMIT 1;` y " + BIT,
           mongo=EVT.format(s="devoluciones") + " Debe verse `tipo: 'devolucion_registrada'`.",
           redis="`GET devoluciones:limite:usuario<id>:crear_devolucion` (contador, `TTL` <= 60).")
    c.caso("registrar 201 XML", "POST", "", "Contrato XML: cuerpo validado contra devolucion_nueva.xsd y respuesta en XML.",
           rol="cliente", fmt="xml", codigo=201,
           body=xb("devolucion", venta_detalle_id="{{venta_detalle_id}}", motivo_id="{{motivo_id}}",
                   descripcion_problema="Caja golpeada, el producto llego aplastado."),
           guarda={"devolucion_xml_id": "xml2Json(pm.response.text()).respuesta.id"})
    c.caso("registrar 400 datos invalidos", "POST", "", "Validacion: id no numerico, motivo ausente y descripcion corta.",
           rol="cliente", body={"venta_detalle_id": "abc", "descripcion_problema": "roto"}, codigo=400, tipo="validacion")
    c.caso("registrar 400 XML no cumple XSD", "POST", "", "XML bien formado al que le faltan campos del contrato.",
           rol="cliente", fmt="xml", body=xb("devolucion", motivo_id="{{motivo_id}}"), codigo=400, tipo="xml_no_cumple_xsd")
    c.caso("registrar 401 sin token", "POST", "", "Endpoint protegido sin Authorization.",
           body=NUEVA, codigo=401, tipo="no_autenticado")
    c.caso("registrar 403 compra de otro cliente", "POST", "", "Autorizacion por recurso: no se devuelve una compra ajena.",
           rol="cliente", body={**NUEVA, "venta_detalle_id": "@id:venta_detalle_ajena"}, codigo=403, tipo="sin_permiso",
           pg="Bitacora `acceso_denegado`: " + BIT)
    c.caso("registrar 404 linea inexistente", "POST", "", "La linea de venta no existe.",
           rol="cliente", body={**NUEVA, "venta_detalle_id": 999999}, codigo=404, tipo="no_encontrado")

    c.carpeta("02 Consulta (GET)")
    c.caso("listar 200 cliente paginado", "GET", "?pagina=1&por_pagina=5", "RF-11: el cliente solo ve sus devoluciones.",
           rol="cliente", tests=[tj("trae paginacion", "J.paginacion.por_pagina === 5")])
    c.caso("listar 200 analista filtro XML", "GET", "?estado=solicitada&por_pagina=5", "Filtro por estado y respuesta en XML.",
           rol="analista", accept="xml")
    c.caso("listar 400 estado invalido", "GET", "?estado=perdida", "Parametro de consulta invalido.",
           rol="analista", codigo=400, tipo="validacion")
    c.caso("listar 401 sin token", "GET", "", "Endpoint protegido sin Authorization.", codigo=401, tipo="no_autenticado")
    c.caso("listar 401 token invalido", "GET", "", "JWT sin firma valida.", rol="falso", codigo=401, tipo="token_invalido")
    c.caso("detalle 200 exitoso", "GET", "/{{devolucion_id}}", "Expediente con historial (bitacora) y eventos (MongoDB).",
           rol="cliente", tests=[tj("trae eventos de MongoDB", "J.eventos.length > 0")],
           mongo=EVT.format(s="devoluciones"))
    c.caso("detalle 403 otro cliente", "GET", "/{{devolucion_id}}", "Un cliente no ve la devolucion de otro.",
           rol="otro", codigo=403, tipo="sin_permiso")
    c.caso("detalle 404 inexistente", "GET", "/999999", "Registro inexistente.", rol="analista", codigo=404, tipo="no_encontrado")

    c.carpeta("03 Revision (PATCH y PUT)")
    c.caso("resolver 403 cliente sin permiso", "PATCH", "/{{devolucion_id}}/resolucion",
           "RNF-09: solo el Analista de Devoluciones resuelve.", rol="cliente", body={"decision": "autorizar"},
           codigo=403, tipo="sin_permiso")
    c.caso("resolver 400 rechazo sin justificacion", "PATCH", "/{{devolucion_id}}/resolucion",
           "Rechazar exige justificacion (RN-12).", rol="analista", body={"decision": "rechazar"}, codigo=400, tipo="validacion")
    c.caso("resolver 200 pedir informacion", "PATCH", "/{{devolucion_id}}/resolucion",
           "RF-10: pasa a en_revision y notifica al cliente (RF-29).", rol="analista",
           body={"decision": "informacion", "justificacion": "Describe el estado del sello."},
           tests=[tj("en_revision", 'J.estado === "en_revision"')],
           pg="`SELECT estado FROM devoluciones WHERE id = <id>;` y `SELECT tipo, mensaje, url FROM notificaciones ORDER BY id DESC LIMIT 2;`",
           mongo=EVT.format(s="devoluciones"))
    c.caso("corregir 200 PUT", "PUT", "/{{devolucion_id}}", "El cliente responde corrigiendo su solicitud.",
           rol="cliente", codigo=200,
           body='{\n  "motivo_id": {{motivo_id}},\n  "descripcion_problema": "El sello venia abierto desde la tienda.",\n  "cantidad_devuelta": 1\n}')
    c.caso("cancelar 409 ya revisada", "DELETE", "/{{devolucion_id}}", "Regla de negocio: no se cancela lo que un analista ya reviso.",
           rol="cliente", codigo=409, tipo="estado_no_permite")
    c.caso("resolver 200 autorizar XML", "PATCH", "/{{devolucion_id}}/resolucion",
           "Autorizacion con cuerpo y respuesta XML (resolucion.xsd). Deja la devolucion lista para logistica.",
           rol="analista", fmt="xml", body=xb("resolucion", decision="autorizar", justificacion="Evidencia suficiente."),
           tests=[tx("autorizada", 'X.respuesta.estado === "autorizada"')],
           pg="`SELECT estado FROM devoluciones WHERE id = <id>;` -> autorizada; notificacion al Coordinador de Logistica: "
              "`SELECT tipo, url FROM notificaciones WHERE tipo = 'autorizacion_logistica' ORDER BY id DESC LIMIT 1;`")
    c.caso("resolver 409 ya resuelta", "PATCH", "/{{devolucion_id}}/resolucion",
           "Regla de negocio: solo se resuelve lo que sigue en revision.", rol="analista",
           body={"decision": "rechazar", "justificacion": "Intento tardio."}, codigo=409, tipo="estado_no_permite")
    c.caso("detalle 200 historial completo", "GET", "/{{devolucion_id}}", "Historial con alta, solicitud de informacion, correccion y autorizacion.",
           rol="analista")

    c.carpeta("04 Cancelacion (DELETE)")
    c.caso("cancelar 200 exitoso", "DELETE", "/{{devolucion_xml_id}}", "RNF-30: eliminacion logica de una devolucion sin revisar.",
           rol="cliente",
           pg="`SELECT id, estado, eliminado_en FROM devoluciones WHERE id = <id>;` (eliminado_en con fecha; la fila no se borra).",
           mongo=EVT.format(s="devoluciones") + " Debe verse `devolucion_cancelada`.")
    c.caso("detalle 404 cancelada", "GET", "/{{devolucion_xml_id}}", "La devolucion cancelada ya no se expone por la API.",
           rol="cliente", codigo=404, tipo="no_encontrado")


# =========================================================================== #
# ventas_catalogos (8006)
# =========================================================================== #
def ventas_catalogos(c):
    V, K = "/api/v1/ventas", "/api/v1/catalogos"
    c.carpeta("00 Preparacion (tokens)")
    salud(c)
    for r in ("cliente", "otro", "analista", "admin"):
        c.login(r)

    c.carpeta("01 Ventas")
    c.caso("ventas 200 cliente paginado", "GET", V + "?pagina=1&por_pagina=5",
           "Un cliente solo ve sus compras. Guarda venta_id para el detalle.", rol="cliente",
           tests=[tj("trae paginacion", "J.paginacion.por_pagina === 5 && J.datos.length > 0")],
           guarda={"venta_id": "pm.response.json().datos[0].id"},
           pg="`SELECT v.id, v.folio_venta, v.cliente_id FROM ventas v WHERE v.cliente_id = <id> ORDER BY v.fecha_venta DESC LIMIT 5;`")
    c.caso("ventas 200 analista XML", "GET", V + "?pagina=1&por_pagina=5", "Un rol interno ve todas las ventas; respuesta XML.",
           rol="analista", accept="xml")
    c.caso("ventas 400 paginacion invalida", "GET", V + "?por_pagina=0", "por_pagina fuera de rango (1 a 100).",
           rol="cliente", codigo=400, tipo="validacion")
    c.caso("ventas 401 sin token", "GET", V, "Endpoint protegido sin Authorization.", codigo=401, tipo="no_autenticado")
    c.caso("ventas 401 token invalido", "GET", V, "JWT sin firma valida.", rol="falso", codigo=401, tipo="token_invalido")
    c.caso("venta 200 detalle", "GET", V + "/{{venta_id}}", "Lineas de la venta con unidades ya devueltas y disponibles.",
           rol="cliente", tests=[tj("trae lineas", "J.lineas.length > 0 && J.lineas[0].disponible !== undefined")],
           pg="`SELECT vd.id, vd.cantidad, vd.precio_unitario FROM venta_detalle vd WHERE vd.venta_id = <venta_id>;`")
    c.caso("venta 200 detalle XML", "GET", V + "/{{venta_id}}", "Mismo detalle en XML.", rol="cliente", accept="xml")
    c.caso("venta 403 de otro cliente", "GET", V + "/{{venta_id}}", "La venta no pertenece al cliente que consulta.",
           rol="otro", codigo=403, tipo="sin_permiso")
    c.caso("venta 404 inexistente", "GET", V + "/999999", "Venta inexistente.", rol="analista", codigo=404, tipo="no_encontrado")

    c.carpeta("02 Catalogos (lectura)")
    c.caso("catalogos 200 lista", "GET", K, "Nombres de los siete catalogos.", rol="admin",
           tests=[tj("siete catalogos", "J.catalogos.length === 7")])
    c.caso("catalogos 403 cliente", "GET", K, "Solo Administrador y Analista listan catalogos.", rol="cliente", codigo=403, tipo="sin_permiso")
    c.caso("catalogo motivos 200 cliente", "GET", K + "/motivos?pagina=1&por_pagina=5",
           "El cliente solo lee motivos (para solicitar devoluciones). Guarda un id para el detalle.", rol="cliente",
           tests=[tj("trae datos", "J.datos.length > 0")],
           guarda={"catalogo_registro_id": "pm.response.json().datos[0].id"},
           pg="`SELECT id, nombre, activo FROM motivos ORDER BY id DESC LIMIT 5;`")
    c.caso("catalogo motivos 200 XML con inactivos", "GET", K + "/motivos?solo_activos=false", "Un rol interno puede ver inactivos; XML.",
           rol="analista", accept="xml")
    c.caso("catalogo productos 403 cliente", "GET", K + "/productos", "El cliente no consulta otros catalogos.",
           rol="cliente", codigo=403, tipo="sin_permiso")
    c.caso("catalogo inexistente 404", "GET", K + "/inexistente", "El nombre no esta en la lista blanca de catalogos.",
           rol="admin", codigo=404, tipo="no_encontrado")
    c.caso("catalogo rutas 200", "GET", K + "/rutas?por_pagina=1", "Guarda ruta_id para la coleccion de logistica.", rol="analista",
           guarda={"ruta_id": "pm.response.json().datos[0].id"})
    c.caso("catalogo transportistas 200", "GET", K + "/transportistas?por_pagina=1", "Guarda transportista_id para logistica.",
           rol="analista", guarda={"transportista_id": "pm.response.json().datos[0].id"})
    c.caso("registro 200 detalle", "GET", K + "/motivos/{{catalogo_registro_id}}", "Un registro del catalogo.", rol="cliente",
           ep=K + "/{nombre}/{registro_id}")
    c.caso("registro 404 inexistente", "GET", K + "/motivos/999999", "Registro inexistente.", rol="cliente",
           codigo=404, tipo="no_encontrado", ep=K + "/{nombre}/{registro_id}")

    c.carpeta("03 Catalogos (escritura, Administrador)")
    nuevo = {"nombre": "Motivo Postman {{$timestamp}}", "descripcion": "Alta de prueba desde Postman"}
    c.caso("alta 201 JSON", "POST", K + "/motivos", "Alta de un motivo de prueba.", rol="admin", body=nuevo, codigo=201,
           guarda={"catalogo_registro_id": "pm.response.json().id"}, ep=K + "/{nombre}",
           tests=['pm.test("Location", () => pm.expect(pm.response.headers.get("Location")).to.include("/api/v1/catalogos/motivos/"));'],
           explica="Valida contra la lista blanca de campos del catalogo y inserta con SQL parametrizado (RNF-11).",
           pg="`SELECT id, nombre, activo FROM motivos ORDER BY id DESC LIMIT 2;` y " + BIT)
    c.caso("alta 201 XML", "POST", K + "/motivos", "Alta con cuerpo XML (catalogo.xsd).", rol="admin", fmt="xml", codigo=201,
           body=xb("catalogo", nombre="Motivo XML {{$timestamp}}", descripcion="Alta de prueba XML"),
           guarda={"catalogo_xml_id": "xml2Json(pm.response.text()).registro.id"}, ep=K + "/{nombre}")
    c.caso("alta 400 sin nombre", "POST", K + "/motivos", "Campo obligatorio vacio.", rol="admin",
           body={"nombre": ""}, codigo=400, tipo="validacion", ep=K + "/{nombre}")
    c.caso("alta 401 sin token", "POST", K + "/motivos", "Endpoint protegido sin Authorization.", body=nuevo,
           codigo=401, tipo="no_autenticado", ep=K + "/{nombre}")
    c.caso("alta 403 analista", "POST", K + "/motivos", "Solo el Administrador da de alta.", rol="analista", body=nuevo,
           codigo=403, tipo="sin_permiso", ep=K + "/{nombre}")
    c.caso("alta 404 catalogo inexistente", "POST", K + "/inexistente", "Catalogo fuera de la lista blanca.", rol="admin",
           body=nuevo, codigo=404, tipo="no_encontrado", ep=K + "/{nombre}")
    c.caso("alta 409 referencia inactiva", "POST", K + "/productos",
           "El producto apunta a un proveedor que no existe o esta inactivo.", rol="admin", codigo=409, tipo="referencia_inactiva",
           body={"sku": "PM-{{$timestamp}}", "nombre": "Producto Postman", "clasificacion_temperatura": "refrigerado",
                 "proveedor_id": 999999}, ep=K + "/{nombre}")
    c.caso("edicion 200 PUT", "PUT", K + "/motivos/{{catalogo_registro_id}}", "Reemplaza los campos del registro.", rol="admin",
           body={"nombre": "Motivo editado {{$timestamp}}", "descripcion": "Editado desde Postman"},
           tests=[tj("actualizado", "J.actualizado === true")], ep=K + "/{nombre}/{registro_id}",
           pg="`SELECT id, nombre FROM motivos WHERE id = <id>;` (nombre nuevo).")
    c.caso("edicion 400 tipo invalido", "PUT", K + "/motivos/{{catalogo_registro_id}}", "El nombre debe ser texto.", rol="admin",
           body={"nombre": 123}, codigo=400, tipo="validacion", ep=K + "/{nombre}/{registro_id}")
    c.caso("edicion 404 inexistente", "PUT", K + "/motivos/999999", "Registro inexistente.", rol="admin",
           body={"nombre": "Motivo fantasma"}, codigo=404, tipo="no_encontrado", ep=K + "/{nombre}/{registro_id}")
    c.caso("estado 200 desactivar", "PATCH", K + "/motivos/{{catalogo_registro_id}}/estado", "Activa o desactiva un registro.",
           rol="admin", body={"activo": False}, tests=[tj("inactivo", "J.activo === false")],
           pg="`SELECT id, activo FROM motivos WHERE id = <id>;` -> f.")
    c.caso("estado 400 booleano invalido", "PATCH", K + "/motivos/{{catalogo_registro_id}}/estado", "activo debe ser booleano.",
           rol="admin", body={"activo": "quizas"}, codigo=400, tipo="validacion")
    c.caso("estado 404 inexistente", "PATCH", K + "/motivos/999999/estado", "Registro inexistente.", rol="admin",
           body={"activo": True}, codigo=404, tipo="no_encontrado")
    c.caso("baja 200 desactivar", "DELETE", K + "/motivos/{{catalogo_xml_id}}", "Baja logica del registro creado en XML.",
           rol="admin", ep=K + "/{nombre}/{registro_id}",
           pg="`SELECT id, activo FROM motivos WHERE id = <id>;` -> f (la fila sigue existiendo).")
    c.caso("baja 404 inexistente", "DELETE", K + "/motivos/999999", "Registro inexistente.", rol="admin",
           codigo=404, tipo="no_encontrado", ep=K + "/{nombre}/{registro_id}")


# =========================================================================== #
# logistica (8003)
# =========================================================================== #
def logistica(c):
    c.carpeta("00 Preparacion (requiere devolucion_id autorizada: coleccion devoluciones)")
    salud(c)
    for r in ("coordinador", "centro", "cliente"):
        c.login(r)
    c.caso("ruta y transportista para asignar", "GET", "/api/v1/catalogos/rutas?por_pagina=1",
           "Toma una ruta activa del catalogo (ventas_catalogos).", rol="coordinador",
           url="{{ventas_url}}/api/v1/catalogos/rutas?por_pagina=1", ev=False,
           guarda={"ruta_id": "pm.response.json().datos[0].id"})
    c.caso("transportista para asignar", "GET", "/api/v1/catalogos/transportistas?por_pagina=1",
           "Toma un transportista activo del catalogo.", rol="coordinador",
           url="{{ventas_url}}/api/v1/catalogos/transportistas?por_pagina=1", ev=False,
           guarda={"transportista_id": "pm.response.json().datos[0].id"})

    c.carpeta("01 Programar recoleccion (POST)")
    futura = ['pm.environment.set("fecha_futura", new Date(Date.now() + 7 * 86400000).toISOString().slice(0, 10));']
    prog = {"devolucion_id": "@id:devolucion_id", "fecha_programada": "{{fecha_futura}}", "lugar": "Domicilio del cliente"}
    c.caso("programar 401 sin token", "POST", "/recolecciones", "Endpoint protegido sin Authorization.", previo=futura,
           body=prog, codigo=401, tipo="no_autenticado")
    c.caso("programar 401 token invalido", "POST", "/recolecciones", "JWT sin firma valida.", rol="falso", previo=futura,
           body=prog, codigo=401, tipo="token_invalido")
    c.caso("programar 403 centro sin permiso", "POST", "/recolecciones", "Solo el Coordinador de Logistica programa.",
           rol="centro", previo=futura, body=prog, codigo=403, tipo="sin_permiso")
    c.caso("programar 400 devolucion_id invalido", "POST", "/recolecciones", "devolucion_id debe ser entero positivo.",
           rol="coordinador", previo=futura, body={**prog, "devolucion_id": "abc"}, codigo=400, tipo="validacion")
    c.caso("programar 404 devolucion inexistente", "POST", "/recolecciones", "La devolucion no existe.", rol="coordinador",
           previo=futura, body={**prog, "devolucion_id": 999999}, codigo=404, tipo="no_encontrado")
    c.caso("programar 400 fecha en el pasado", "POST", "/recolecciones", "fecha_programada no puede ser anterior a hoy (RF-12).",
           rol="coordinador", body={**prog, "fecha_programada": "2020-01-01"}, codigo=400, tipo="validacion")
    c.caso("programar 400 XML no cumple XSD", "POST", "/recolecciones", "Falta fecha_programada (recoleccion.xsd).",
           rol="coordinador", fmt="xml", body=xb("recoleccion", devolucion_id="{{devolucion_id}}", lugar="Domicilio"),
           codigo=400, tipo="xml_no_cumple_xsd")
    c.caso("programar 201 exitoso", "POST", "/recolecciones", "RF-12: programa la recoleccion de una devolucion autorizada.",
           rol="coordinador", previo=futura, body=prog, codigo=201,
           tests=[tj("estado programada", 'J.estado === "programada"')],
           guarda={"recoleccion_id": "pm.response.json().id"},
           explica="Bloquea la fila de la devolucion (FOR UPDATE), exige estado `autorizada`, inserta la recoleccion y "
                   "pasa la devolucion a `en_recoleccion`.",
           pg="`SELECT id, devolucion_id, estado, fecha_programada, lugar FROM recolecciones ORDER BY id DESC LIMIT 1;` y "
              "`SELECT estado FROM devoluciones WHERE id = <devolucion_id>;` -> en_recoleccion. " + BIT)
    c.caso("programar 409 ya programada", "POST", "/recolecciones", "La devolucion ya no esta autorizada: no se programa dos veces.",
           rol="coordinador", previo=futura, body=prog, codigo=409, tipo="estado_no_permite")

    c.carpeta("02 Consulta (GET)")
    c.caso("listar 200 coordinador", "GET", "/recolecciones", "Recolecciones con folio, ruta y transportista.", rol="coordinador",
           tests=[tj("trae datos", "Array.isArray(J.datos) && J.datos.length > 0")],
           pg="`SELECT r.id, d.folio_devolucion, r.estado FROM recolecciones r JOIN devoluciones d ON d.id = r.devolucion_id ORDER BY r.id DESC LIMIT 5;`")
    c.caso("listar 200 centro XML con filtro", "GET", "/recolecciones?estado=programada", "El Encargado del Centro tambien consulta; XML.",
           rol="centro", accept="xml")
    c.caso("listar 400 estado invalido", "GET", "/recolecciones?estado=volando", "Estado de recoleccion fuera del catalogo.",
           rol="coordinador", codigo=400, tipo="validacion")
    c.caso("listar 403 cliente", "GET", "/recolecciones", "El cliente no consulta recolecciones.", rol="cliente",
           codigo=403, tipo="sin_permiso")
    c.caso("listar 401 sin token", "GET", "/recolecciones", "Endpoint protegido sin Authorization.", codigo=401, tipo="no_autenticado")

    c.carpeta("03 Asignar ruta y transportista (PATCH)")
    asig = {"ruta_id": "@id:ruta_id", "transportista_id": "@id:transportista_id"}
    c.caso("asignar 403 centro sin permiso", "PATCH", "/recolecciones/{{recoleccion_id}}/asignacion", "Solo el Coordinador asigna.",
           rol="centro", body=asig, codigo=403, tipo="sin_permiso")
    c.caso("asignar 400 ruta invalida", "PATCH", "/recolecciones/{{recoleccion_id}}/asignacion", "ruta_id debe ser entero positivo.",
           rol="coordinador", body={**asig, "ruta_id": 0}, codigo=400, tipo="validacion")
    c.caso("asignar 400 ruta inexistente", "PATCH", "/recolecciones/{{recoleccion_id}}/asignacion", "La ruta no existe o esta inactiva.",
           rol="coordinador", body={**asig, "ruta_id": 999999}, codigo=400, tipo="validacion")
    c.caso("asignar 404 recoleccion inexistente", "PATCH", "/recolecciones/999999/asignacion", "La recoleccion no existe.",
           rol="coordinador", body=asig, codigo=404, tipo="no_encontrado")
    c.caso("asignar 200 XML", "PATCH", "/recolecciones/{{recoleccion_id}}/asignacion", "RF-13: asigna ruta y transportista (asignacion.xsd).",
           rol="coordinador", fmt="xml", body=xb("asignacion", ruta_id="{{ruta_id}}", transportista_id="{{transportista_id}}"),
           tests=[tx("asignada", 'X.respuesta.estado === "asignada"')],
           pg="`SELECT id, estado, ruta_id, transportista_id FROM recolecciones WHERE id = <id>;` " + BIT)

    c.carpeta("04 Estado de la recoleccion (PATCH)")
    c.caso("estado 409 transicion invalida", "PATCH", "/recolecciones/{{recoleccion_id}}/estado",
           "De asignada solo se pasa a en_transito o fallida.", rol="coordinador", body={"estado": "completada"},
           codigo=409, tipo="transicion_invalida")
    c.caso("estado 404 inexistente", "PATCH", "/recolecciones/999999/estado", "La recoleccion no existe.", rol="coordinador",
           body={"estado": "en_transito"}, codigo=404, tipo="no_encontrado")
    c.caso("estado 200 en_transito", "PATCH", "/recolecciones/{{recoleccion_id}}/estado", "RF-14: el producto va en camino.",
           rol="coordinador", body={"estado": "en_transito"}, tests=[tj("en_transito", 'J.estado === "en_transito"')],
           pg="`SELECT id, estado FROM recolecciones WHERE id = <id>;` " + BIT)
    c.caso("asignar 409 ya inicio", "PATCH", "/recolecciones/{{recoleccion_id}}/asignacion", "Una recoleccion en transito ya no se reasigna.",
           rol="coordinador", body=asig, codigo=409, tipo="estado_no_permite")
    c.caso("estado 200 completada XML", "PATCH", "/recolecciones/{{recoleccion_id}}/estado", "La recoleccion termina; XML (estado_recoleccion.xsd).",
           rol="coordinador", fmt="xml", body=xb("estado_recoleccion", estado="completada"),
           tests=[tx("completada", 'X.respuesta.estado === "completada"')])

    c.carpeta("05 Recepcion en el centro (POST)")
    rec = {"devolucion_id": "@id:devolucion_id", "coincide_expediente": True}
    c.caso("recepcion 403 coordinador", "POST", "/recepciones", "Solo el Encargado del Centro recibe.", rol="coordinador",
           body=rec, codigo=403, tipo="sin_permiso")
    c.caso("recepcion 400 devolucion invalida", "POST", "/recepciones", "devolucion_id debe ser entero positivo.", rol="centro",
           body={**rec, "devolucion_id": 0}, codigo=400, tipo="validacion")
    c.caso("recepcion 404 inexistente", "POST", "/recepciones", "La devolucion no existe.", rol="centro",
           body={**rec, "devolucion_id": 999999}, codigo=404, tipo="no_encontrado")
    c.caso("recepcion 400 booleano invalido", "POST", "/recepciones", "coincide_expediente debe ser booleano.", rol="centro",
           body={**rec, "coincide_expediente": "quizas"}, codigo=400, tipo="validacion")
    c.caso("recepcion 201 exitoso", "POST", "/recepciones", "RF-15: el centro confirma que recibio el producto.", rol="centro",
           body=rec, codigo=201,
           explica="Exige recoleccion `completada`, inserta la recepcion y pasa la devolucion a `recibida`.",
           pg="`SELECT id, devolucion_id, coincide_expediente, fecha_recepcion FROM recepciones ORDER BY id DESC LIMIT 1;` y "
              "`SELECT estado FROM devoluciones WHERE id = <devolucion_id>;` -> recibida. " + BIT)
    c.caso("recepcion 409 duplicada", "POST", "/recepciones", "La devolucion ya fue recibida.", rol="centro", body=rec,
           codigo=409, tipo="recepcion_duplicada")


# =========================================================================== #
# inspecciones (8004)
# =========================================================================== #
def inspecciones(c):
    c.carpeta("00 Preparacion (requiere devolucion_id recibida: coleccion logistica)")
    salud(c, ("postgresql", "redis", "mongodb"))
    for r in ("inspector", "analista", "centro", "cliente"):
        c.login(r)

    c.carpeta("01 Registrar inspeccion (POST)")
    insp = {"devolucion_id": "@id:devolucion_id", "estado_empaque": "Empaque intacto, sello cerrado",
            "danos": False, "caducidad_vencida": False, "cadena_frio_rota": False,
            "minutos_fuera_refrigeracion": 10, "temperatura_recepcion": 4.5,
            "observaciones": "Inspeccion de prueba desde Postman"}
    c.caso("registrar 401 sin token", "POST", "", "Endpoint protegido sin Authorization.", body=insp, codigo=401, tipo="no_autenticado")
    c.caso("registrar 403 analista", "POST", "", "Solo el Inspector registra la inspeccion.", rol="analista", body=insp,
           codigo=403, tipo="sin_permiso")
    c.caso("registrar 400 devolucion_id invalido", "POST", "", "devolucion_id debe ser positivo.", rol="inspector",
           body={**insp, "devolucion_id": 0}, codigo=400, tipo="validacion")
    c.caso("registrar 404 devolucion inexistente", "POST", "", "La devolucion no existe.", rol="inspector",
           body={**insp, "devolucion_id": 999999}, codigo=404, tipo="no_encontrado")
    c.caso("registrar 400 XML no cumple XSD", "POST", "", "Faltan campos obligatorios (inspeccion.xsd).", rol="inspector",
           fmt="xml", body=xb("inspeccion", devolucion_id="{{devolucion_id}}"), codigo=400, tipo="xml_no_cumple_xsd")
    c.caso("registrar 400 empaque sin describir", "POST", "", "estado_empaque exige al menos 3 caracteres.", rol="inspector",
           body={**insp, "estado_empaque": "x"}, codigo=400, tipo="validacion")
    c.caso("registrar 400 booleano invalido", "POST", "", "danos debe ser booleano.", rol="inspector",
           body={**insp, "danos": "quizas"}, codigo=400, tipo="validacion")
    c.caso("registrar 201 exitoso", "POST", "", "RF-16, RF-17: inspeccion con detalle en MongoDB y referencia en PostgreSQL.",
           rol="inspector", body=insp, codigo=201,
           tests=[tj("aptitud calculada", "J.apto_para_inventario === true && !!J.mongo_doc_id")],
           explica="Inserta el documento en MongoDB (`inspecciones`), la referencia en `inspecciones_ref` y pasa la devolucion a "
                   "`en_inspeccion`. Aptitud: sin danos, sin caducidad vencida, cadena de frio integra y <= 30 min fuera de refrigeracion (RN-05, RN-06).",
           pg="`SELECT id, devolucion_id, resultado_general, mongo_doc_id, apto_para_inventario FROM inspecciones_ref ORDER BY id DESC LIMIT 1;` y "
              "`SELECT estado FROM devoluciones WHERE id = <devolucion_id>;` -> en_inspeccion. " + BIT,
           mongo="`db.inspecciones.find({devolucion_id: <id>}).pretty()` (condiciones, resultado.apto_para_inventario) y "
                 "`db.inspecciones.getIndexes()` (indice unico uq_inspeccion_devolucion).")
    c.caso("registrar 409 duplicada", "POST", "", "La devolucion ya tiene inspeccion.", rol="inspector", body=insp,
           codigo=409, tipo="inspeccion_duplicada")

    c.carpeta("02 Consulta (GET)")
    c.caso("detalle 200 inspector", "GET", "/{{devolucion_id}}", "Referencia (PostgreSQL) y detalle (MongoDB) de la inspeccion.",
           rol="inspector", tests=[tj("une las dos bases", "!!J.referencia && !!J.detalle")],
           mongo="`db.inspecciones.findOne({devolucion_id: <id>})` coincide con `detalle`.")
    c.caso("detalle 200 analista XML", "GET", "/{{devolucion_id}}", "Mismo expediente en XML.", rol="analista", accept="xml")
    c.caso("detalle 403 cliente", "GET", "/{{devolucion_id}}", "El cliente no consulta inspecciones.", rol="cliente",
           codigo=403, tipo="sin_permiso")
    c.caso("detalle 404 inexistente", "GET", "/999999", "No hay inspeccion para esa devolucion.", rol="inspector",
           codigo=404, tipo="no_encontrado")
    c.caso("detalle 401 token invalido", "GET", "/{{devolucion_id}}", "JWT sin firma valida.", rol="falso",
           codigo=401, tipo="token_invalido")

    c.carpeta("03 Actualizar detalle (PATCH)")
    c.caso("actualizar 400 sin cambios", "PATCH", "/{{devolucion_id}}", "No hay campos actualizables.", rol="inspector",
           body={}, codigo=400, tipo="validacion")
    c.caso("actualizar 403 analista", "PATCH", "/{{devolucion_id}}", "Solo el Inspector actualiza.", rol="analista",
           body={"observaciones": "x"}, codigo=403, tipo="sin_permiso")
    c.caso("actualizar 404 inexistente", "PATCH", "/999999", "No hay inspeccion para actualizar.", rol="inspector",
           body={"observaciones": "x"}, codigo=404, tipo="no_encontrado")
    c.caso("actualizar 200 XML", "PATCH", "/{{devolucion_id}}", "Actualiza observaciones en MongoDB; XML (inspeccion_actualizacion.xsd).",
           rol="inspector", fmt="xml",
           body=xb("inspeccion_actualizacion", observaciones="Observacion actualizada desde Postman"),
           mongo="`db.inspecciones.findOne({devolucion_id: <id>}, {observaciones: 1})` muestra el texto nuevo.",
           pg="Bitacora `inspeccion_actualizada`: " + BIT)

    c.carpeta("04 Disposicion (POST)")
    disp = {"destino": "inventario", "justificacion": "Producto apto, regresa a inventario."}
    c.caso("disposicion 403 inspector", "POST", "/{{devolucion_id}}/disposicion", "Solo el Analista decide el destino.",
           rol="inspector", body=disp, codigo=403, tipo="sin_permiso")
    c.caso("disposicion 400 destino invalido", "POST", "/{{devolucion_id}}/disposicion", "Destino fuera del catalogo de siete.",
           rol="analista", body={"destino": "tirar"}, codigo=400, tipo="validacion")
    c.caso("disposicion 404 inexistente", "POST", "/999999/disposicion", "La devolucion no existe.", rol="analista",
           body=disp, codigo=404, tipo="no_encontrado")
    c.caso("disposicion 201 XML", "POST", "/{{devolucion_id}}/disposicion", "RF-18: destino del producto (disposicion.xsd). Guarda disposicion_id.",
           rol="analista", fmt="xml", codigo=201,
           body=xb("disposicion", destino="inventario", justificacion="Producto apto, regresa a inventario."),
           guarda={"disposicion_id": "xml2Json(pm.response.text()).respuesta.id"},
           explica="Exige inspeccion previa (RN-07) y, para `inventario`, que el producto sea apto. Pasa la devolucion a `resuelta`.",
           pg="`SELECT id, devolucion_id, destino, justificacion FROM disposiciones ORDER BY id DESC LIMIT 1;` y "
              "`SELECT estado FROM devoluciones WHERE id = <devolucion_id>;` -> resuelta. " + BIT)
    c.caso("disposicion 409 duplicada", "POST", "/{{devolucion_id}}/disposicion", "Ya existe una disposicion para la devolucion.",
           rol="analista", body={"destino": "reciclaje"}, codigo=409, tipo="disposicion_duplicada")

    c.carpeta("05 Etiqueta de inventario (POST)")
    c.caso("etiqueta 403 inspector", "POST", "/inventario/{{disposicion_id}}/etiqueta", "Solo el Encargado del Centro etiqueta.",
           rol="inspector", body={}, codigo=403, tipo="sin_permiso")
    c.caso("etiqueta 404 inexistente", "POST", "/inventario/999999/etiqueta", "La disposicion no existe.", rol="centro",
           body={}, codigo=404, tipo="no_encontrado")
    c.caso("etiqueta 201 exitoso", "POST", "/inventario/{{disposicion_id}}/etiqueta", "RF-19: etiqueta el producto recuperable.",
           rol="centro", body={}, codigo=201,
           tests=[tj("etiqueta REC-", 'J.etiqueta_codigo.indexOf("REC-") === 0')],
           pg="`SELECT id, disposicion_id, producto_id, etiqueta_codigo FROM inventario_recuperado ORDER BY id DESC LIMIT 1;` " + BIT)


# =========================================================================== #
# evidencias (8007)
# =========================================================================== #
def evidencias(c):
    E = "/api/v1/evidencias"
    c.carpeta("00 Preparacion (crea una devolucion propia para adjuntar)")
    salud(c, ("postgresql", "redis", "mongodb", "almacen_privado"))
    for r in ("cliente", "otro", "inspector", "analista"):
        c.login(r)
    c.caso("registrar devolucion para evidencias", "POST", "/api/v1/devoluciones", "Una devolucion en estado solicitada: "
           "el cliente solo adjunta durante la solicitud o la revision. Se cancela al final.", rol="cliente",
           url="{{devoluciones_url}}/api/v1/devoluciones", ev=False, body=NUEVA, codigo=201,
           guarda={"devolucion_ev_id": "pm.response.json().id"})

    c.carpeta("01 Alta (POST)")
    com = {"devolucion_id": "@id:devolucion_ev_id", "tipo": "comentario", "etapa": "solicitud",
           "comentario": "El sello del empaque llego roto."}
    c.caso("alta 201 comentario JSON", "POST", "", "RF-09: el cliente agrega un comentario a su devolucion.",
           rol="cliente", body=com, codigo=201, guarda={"evidencia_id": "pm.response.json().id"},
           tests=[tj("tipo comentario", 'J.tipo === "comentario" && !!J.metadatos_id')],
           explica="Inserta la fila en `evidencias` (PostgreSQL) y el documento de metadatos en MongoDB; si Mongo falla se hace rollback.",
           pg="`SELECT id, devolucion_id, tipo, etapa, comentario FROM evidencias ORDER BY id DESC LIMIT 1;` " + BIT,
           mongo="`db.evidencias_metadatos.find({evidencia_id: <id>}).pretty()` y `db.evidencias_metadatos.getIndexes()` (idx_devolucion).")
    c.caso("alta 201 comentario XML", "POST", "", "El mismo alta con XML (comentario.xsd).", rol="cliente", fmt="xml", codigo=201,
           body=xb("evidencia", devolucion_id="{{devolucion_ev_id}}", tipo="comentario", etapa="solicitud",
                   comentario="Segundo comentario en XML."),
           guarda={"evidencia_xml_id": "xml2Json(pm.response.text()).evidencia.id"})
    c.caso("alta 201 archivo PNG", "POST", "", "Sube una fotografia (multipart). Selecciona fixtures/evidencia_prueba.png en el campo archivo.",
           rol="cliente", codigo=201, guarda={"evidencia_archivo_id": "pm.response.json().id"},
           tests=[tj("es fotografia", 'J.tipo === "fotografia"')],
           formdata=[{"key": "devolucion_id", "value": "{{devolucion_ev_id}}", "type": "text"},
                     {"key": "etapa", "value": "solicitud", "type": "text"},
                     {"key": "archivo", "type": "file", "src": "fixtures/evidencia_prueba.png"}],
           explica="Valida el tipo real por los primeros bytes (no por la extension), guarda el archivo en el volumen privado con "
                   "nombre aleatorio y registra la referencia.",
           pg="`SELECT id, tipo, nombre_original, mime_type, tamano_bytes, bucket FROM evidencias ORDER BY id DESC LIMIT 1;`",
           mongo="`db.evidencias_metadatos.find({evidencia_id: <id>}).pretty()` (mime_type, tamano_bytes).")
    c.caso("alta 400 comentario vacio", "POST", "", "Un comentario sin texto.", rol="cliente",
           body={**com, "comentario": ""}, codigo=400, tipo="validacion")
    c.caso("alta 400 tipo no permitido en JSON", "POST", "", "JSON solo sirve para comentarios; los archivos van en multipart.",
           rol="cliente", body={**com, "tipo": "fotografia"}, codigo=400, tipo="validacion")
    c.caso("alta 400 etapa invalida", "POST", "", "Etapa fuera de solicitud/recoleccion/recepcion/inspeccion.", rol="cliente",
           body={**com, "etapa": "volando"}, codigo=400, tipo="validacion")
    c.caso("alta 400 multipart sin archivo", "POST", "", "Falta el campo archivo.", rol="cliente", codigo=400, tipo="validacion",
           formdata=[{"key": "devolucion_id", "value": "{{devolucion_ev_id}}", "type": "text"}])
    c.caso("alta 401 sin token", "POST", "", "Endpoint protegido sin Authorization.", body=com, codigo=401, tipo="no_autenticado")
    c.caso("alta 401 token invalido", "POST", "", "JWT sin firma valida.", rol="falso", body=com, codigo=401, tipo="token_invalido")
    c.caso("alta 403 analista", "POST", "", "Solo cliente e inspector adjuntan.", rol="analista", body=com, codigo=403, tipo="sin_permiso")
    c.caso("alta 403 otro cliente", "POST", "", "No se adjunta a la devolucion de otra persona.", rol="otro", body=com,
           codigo=403, tipo="sin_permiso")
    c.caso("alta 403 inspector sin inspeccion", "POST", "", "La inspeccion no esta asignada a este inspector.", rol="inspector",
           body={**com, "etapa": "inspeccion"}, codigo=403, tipo="sin_permiso")
    c.caso("alta 404 devolucion inexistente", "POST", "", "La devolucion no existe.", rol="cliente",
           body={**com, "devolucion_id": 999999}, codigo=404, tipo="no_encontrado")
    c.caso("alta 409 etapa no permitida al cliente", "POST", "", "El cliente solo adjunta en la etapa de solicitud.", rol="cliente",
           body={**com, "etapa": "recoleccion"}, codigo=409, tipo="estado_no_permite")
    c.caso("alta 415 archivo no soportado", "POST", "", "Un .txt no es JPG, PNG ni PDF reales. Selecciona fixtures/no_es_imagen.txt.",
           rol="cliente", codigo=415, tipo="formato_no_soportado",
           formdata=[{"key": "devolucion_id", "value": "{{devolucion_ev_id}}", "type": "text"},
                     {"key": "etapa", "value": "solicitud", "type": "text"},
                     {"key": "archivo", "type": "file", "src": "fixtures/no_es_imagen.txt"}])

    c.carpeta("02 Consulta (GET)")
    c.caso("listar 200 cliente", "GET", "?devolucion_id={{devolucion_ev_id}}&pagina=1&por_pagina=5", "Evidencias de la devolucion, paginadas.",
           rol="cliente", tests=[tj("trae las tres", "J.paginacion.total >= 3")])
    c.caso("listar 200 analista XML", "GET", "?devolucion_id={{devolucion_ev_id}}", "Un rol interno consulta; XML.", rol="analista", accept="xml")
    c.caso("listar 400 sin devolucion_id", "GET", "", "devolucion_id es obligatorio.", rol="cliente", codigo=400, tipo="validacion")
    c.caso("listar 403 otro cliente", "GET", "?devolucion_id={{devolucion_ev_id}}", "No se ven las evidencias de otro cliente.",
           rol="otro", codigo=403, tipo="sin_permiso")
    c.caso("listar 404 devolucion inexistente", "GET", "?devolucion_id=999999", "La devolucion no existe.", rol="analista",
           codigo=404, tipo="no_encontrado")
    c.caso("detalle 200 con metadatos", "GET", "/{{evidencia_id}}", "Detalle de la evidencia mas sus metadatos de MongoDB.", rol="cliente",
           tests=[tj("no expone bucket ni objeto", "J.bucket === undefined && J.objeto === undefined"),
                  tj("trae metadatos", "Array.isArray(J.metadatos)")],
           mongo="`db.evidencias_metadatos.find({evidencia_id: <id>})` coincide con `metadatos`.")
    c.caso("detalle 404 inexistente", "GET", "/999999", "Evidencia inexistente.", rol="cliente", codigo=404, tipo="no_encontrado")
    c.caso("detalle 403 otro cliente", "GET", "/{{evidencia_id}}", "Evidencia de otro cliente.", rol="otro", codigo=403, tipo="sin_permiso")
    c.caso("enlace 200 firmado", "GET", "/{{evidencia_archivo_id}}/enlace", "Enlace firmado que caduca en 900 s (15 min).", rol="cliente",
           tests=[tj("vigencia 900 s", "J.vigencia_segundos === 900")],
           guarda={"url_enlace": "pm.response.json().url_relativa"},
           explica="HMAC-SHA256 sobre `id:vencimiento` con el secreto JWT; el archivo nunca se sirve desde una ruta publica.")
    c.caso("enlace 409 comentario sin archivo", "GET", "/{{evidencia_id}}/enlace", "Un comentario no tiene archivo.", rol="cliente",
           codigo=409, tipo="sin_archivo")
    c.caso("archivo 200 con enlace firmado", "GET", "/{{evidencia_archivo_id}}/archivo?{{url_enlace_consulta}}",
           "Descarga con el enlace firmado, sin Bearer.",
           previo=['pm.environment.set("url_enlace_consulta", (pm.environment.get("url_enlace") || "").split("?")[1] || "");'],
           tests=['pm.test("es una imagen PNG", () => pm.expect(pm.response.headers.get("Content-Type")).to.include("image/png"));'],
           ep=E + "/{evidencia_id}/archivo")
    c.caso("archivo 200 con Bearer", "GET", "/{{evidencia_archivo_id}}/archivo", "Descarga autenticada por JWT (sin firma).", rol="cliente",
           tests=['pm.test("es una imagen PNG", () => pm.expect(pm.response.headers.get("Content-Type")).to.include("image/png"));'])
    c.caso("archivo 401 sin firma ni token", "GET", "/{{evidencia_archivo_id}}/archivo", "Sin firma valida ni Bearer no se entrega nada.",
           codigo=401, tipo="no_autenticado")
    c.caso("archivo 404 inexistente", "GET", "/999999/archivo", "Evidencia inexistente.", rol="cliente", codigo=404, tipo="no_encontrado")

    c.carpeta("03 Retiro (DELETE)")
    c.caso("retiro 403 analista", "DELETE", "/{{evidencia_xml_id}}", "Solo cliente e inspector retiran evidencias.", rol="analista",
           codigo=403, tipo="sin_permiso")
    c.caso("retiro 403 otro cliente", "DELETE", "/{{evidencia_xml_id}}", "Solo se retiran evidencias propias.", rol="otro",
           codigo=403, tipo="sin_permiso")
    c.caso("retiro 200 exitoso", "DELETE", "/{{evidencia_xml_id}}", "Retiro logico (RN-12): el archivo se conserva para auditoria.",
           rol="cliente", tests=[tj("eliminada", "J.eliminada === true")],
           pg="`SELECT id, eliminado_en FROM evidencias WHERE id = <id>;` (eliminado_en con fecha) y " + BIT)
    c.caso("retiro 404 ya retirada", "DELETE", "/{{evidencia_xml_id}}", "La evidencia retirada ya no se encuentra.", rol="cliente",
           codigo=404, tipo="no_encontrado")
    c.caso("retiro 404 inexistente", "DELETE", "/999999", "Evidencia inexistente.", rol="cliente", codigo=404, tipo="no_encontrado")

    c.carpeta("04 Inspector (requiere haber corrido la coleccion inspecciones)")
    c.caso("alta 201 inspector en etapa inspeccion", "POST", "", "El inspector asignado agrega un comentario a la inspeccion de devolucion_id.",
           rol="inspector", codigo=201,
           body={"devolucion_id": "@id:devolucion_id", "tipo": "comentario", "etapa": "inspeccion",
                 "comentario": "Verificacion visual del empaque."})

    c.carpeta("99 Limpieza")
    c.caso("cancelar devolucion de prueba", "DELETE", "/api/v1/devoluciones/{{devolucion_ev_id}}",
           "Libera las unidades de la linea de venta para la siguiente corrida.", rol="cliente",
           url="{{devoluciones_url}}/api/v1/devoluciones/{{devolucion_ev_id}}", ev=False)


# =========================================================================== #
# reembolsos_costos (8005)
# =========================================================================== #
def reembolsos_costos(c):
    c.carpeta("00 Preparacion (requiere devolucion_id autorizada o resuelta)")
    salud(c)
    for r in ("reembolsos", "coordinador", "centro", "analista", "cliente"):
        c.login(r)

    c.carpeta("01 Costos (POST)")
    costo = {"devolucion_id": "@id:devolucion_id", "etapa": "transporte", "monto": 150.5}
    c.caso("costo 401 sin token", "POST", "/costos", "Endpoint protegido sin Authorization.", body=costo, codigo=401, tipo="no_autenticado")
    c.caso("costo 403 cliente", "POST", "/costos", "El cliente no registra costos.", rol="cliente", body=costo, codigo=403, tipo="sin_permiso")
    c.caso("costo 403 etapa de otro rol", "POST", "/costos", "El coordinador solo registra costos de transporte.", rol="coordinador",
           body={**costo, "etapa": "reembolso"}, codigo=403, tipo="sin_permiso")
    c.caso("costo 400 monto negativo", "POST", "/costos", "monto debe ser decimal no negativo.", rol="coordinador",
           body={**costo, "monto": -5}, codigo=400, tipo="validacion")
    c.caso("costo 400 etapa invalida", "POST", "/costos", "Etapa fuera del catalogo.", rol="coordinador",
           body={**costo, "etapa": "viaje"}, codigo=400, tipo="validacion")
    c.caso("costo 400 devolucion_id invalido", "POST", "/costos", "devolucion_id debe ser entero.", rol="coordinador",
           body={**costo, "devolucion_id": "abc"}, codigo=400, tipo="validacion")
    c.caso("costo 400 XML no cumple XSD", "POST", "/costos", "Faltan etapa y monto (costo.xsd).", rol="coordinador", fmt="xml",
           body=xb("costo", devolucion_id="{{devolucion_id}}"), codigo=400, tipo="xml_no_cumple_xsd")
    c.caso("costo 404 devolucion inexistente", "POST", "/costos", "La devolucion no existe.", rol="coordinador",
           body={**costo, "devolucion_id": 999999}, codigo=404, tipo="no_encontrado")
    c.caso("costo 201 transporte JSON", "POST", "/costos", "RF-27: el coordinador registra el costo de transporte.", rol="coordinador",
           body=costo, codigo=201,
           explica="Cada rol solo registra las etapas de su area (RN-04): coordinador=transporte, centro=almacenamiento, "
                   "inspector=inspeccion, analista=reacondicionamiento/destruccion/otros, reembolsos=reembolso.",
           pg="`SELECT id, devolucion_id, etapa, monto, fecha FROM costos ORDER BY id DESC LIMIT 2;` " + BIT)
    c.caso("costo 201 almacenamiento XML", "POST", "/costos", "El encargado del centro registra almacenamiento; XML.", rol="centro",
           fmt="xml", body=xb("costo", devolucion_id="{{devolucion_id}}", etapa="almacenamiento", monto="45.00"), codigo=201)

    c.carpeta("02 Reembolsos (POST)")
    reem = {"devolucion_id": "@id:devolucion_id", "estado": "aprobado", "metodo": "transferencia", "monto": 1.0}
    c.caso("reembolso 403 analista", "POST", "/reembolsos", "Solo el Encargado de Reembolsos resuelve.", rol="analista",
           body=reem, codigo=403, tipo="sin_permiso")
    c.caso("reembolso 400 estado invalido", "POST", "/reembolsos", "estado debe ser aprobado o rechazado.", rol="reembolsos",
           body={**reem, "estado": "quizas"}, codigo=400, tipo="validacion")
    c.caso("reembolso 400 metodo invalido", "POST", "/reembolsos", "Un reembolso aprobado exige metodo valido.", rol="reembolsos",
           body={**reem, "metodo": "cheque"}, codigo=400, tipo="validacion")
    c.caso("reembolso 400 devolucion_id invalido", "POST", "/reembolsos", "devolucion_id debe ser entero positivo.", rol="reembolsos",
           body={**reem, "devolucion_id": 0}, codigo=400, tipo="validacion")
    c.caso("reembolso 404 devolucion inexistente", "POST", "/reembolsos", "La devolucion no existe.", rol="reembolsos",
           body={**reem, "devolucion_id": 999999}, codigo=404, tipo="no_encontrado")
    c.caso("reembolso 409 monto excedido", "POST", "/reembolsos", "RN-03: el reembolso no puede superar el valor devuelto.",
           rol="reembolsos", body={**reem, "monto": 9999999.99}, codigo=409, tipo="monto_excedido",
           tests=[tj("informa el maximo", "J.error.detalles.maximo > 0")])
    c.caso("reembolso 201 aprobado", "POST", "/reembolsos", "RF-20, RF-21: aprueba el reembolso con monto y metodo.", rol="reembolsos",
           body=reem, codigo=201, tests=[tj("aprobado", 'J.estado === "aprobado"')],
           explica="Toma un candado en Redis (SET NX EX 30) para que dos personas no resuelvan a la vez, valida el maximo con Decimal, "
                   "inserta el reembolso y el costo de etapa `reembolso`, cierra la devolucion si estaba `resuelta` y notifica al cliente.",
           pg="`SELECT id, devolucion_id, monto, metodo, estado FROM reembolsos ORDER BY id DESC LIMIT 1;`, "
              "`SELECT etapa, monto FROM costos WHERE devolucion_id = <id>;` y `SELECT estado, fecha_cierre FROM devoluciones WHERE id = <id>;` -> cerrada. " + BIT,
           redis="Durante la peticion existe `devoluciones:lock:reembolso:<id>` (TTL <= 30 s); al terminar ya no existe. "
                 "Para ver el 409 reembolso_en_proceso: `SET devoluciones:lock:reembolso:<id> x NX EX 30` y repetir el POST.")
    c.caso("reembolso 409 duplicado XML", "POST", "/reembolsos", "La devolucion ya tiene un reembolso valido; error en XML.", rol="reembolsos",
           fmt="xml", body=xb("reembolso", devolucion_id="{{devolucion_id}}", monto="1.00", metodo="transferencia", estado="aprobado"),
           codigo=409, tipo="reembolso_duplicado")

    c.carpeta("03 Consulta (GET)")
    c.caso("reembolsos 200 lista", "GET", "/reembolsos", "Ultimos 100 reembolsos.", rol="reembolsos",
           tests=[tj("trae datos", "Array.isArray(J.datos)")])
    c.caso("reembolsos 200 analista XML", "GET", "/reembolsos", "El analista tambien consulta; XML.", rol="analista", accept="xml")
    c.caso("reembolsos 403 cliente", "GET", "/reembolsos", "El cliente no lista reembolsos.", rol="cliente", codigo=403, tipo="sin_permiso")
    c.caso("reembolsos 401 token invalido", "GET", "/reembolsos", "JWT sin firma valida.", rol="falso", codigo=401, tipo="token_invalido")
    c.caso("costos 200 desglose", "GET", "/costos/{{devolucion_id}}", "RF-27: costo por etapa y total de la devolucion.", rol="reembolsos",
           tests=[tj("desglose y total", "J.desglose.length >= 1 && J.costo_total > 0")],
           pg="`SELECT etapa, SUM(monto) FROM costos WHERE devolucion_id = <id> GROUP BY etapa;` y `SELECT * FROM vista_costo_devolucion WHERE devolucion_id = <id>;`")
    c.caso("costos 200 analista XML", "GET", "/costos/{{devolucion_id}}", "Mismo desglose en XML.", rol="analista", accept="xml")
    c.caso("costos 403 centro", "GET", "/costos/{{devolucion_id}}", "El centro registra costos pero no consulta el total.", rol="centro",
           codigo=403, tipo="sin_permiso")
    c.caso("costos 404 devolucion inexistente", "GET", "/costos/999999", "La devolucion no existe.", rol="reembolsos",
           codigo=404, tipo="no_encontrado")


# =========================================================================== #
# analisis_auditoria (8008)
# =========================================================================== #
def analisis_auditoria(c):
    A, U = "/api/v1/analisis", "/api/v1/auditoria"
    c.carpeta("00 Preparacion (tokens)")
    salud(c, ("postgresql", "redis", "mongodb"))
    for r in ("cliente", "analista", "admin", "centro"):
        c.login(r)

    c.carpeta("01 Clasificar motivo (POST)")
    desc = {"descripcion": "El producto llego roto y el empaque aplastado por el golpe."}
    c.caso("clasificar 200 cliente", "POST", A + "/clasificar-motivo", "RF-24, RN-11: sugiere un motivo; el usuario siempre confirma.",
           rol="cliente", body=desc, tests=[tj("requiere confirmacion", "J.requiere_confirmacion === true")],
           explica="Ranking explicable por palabras clave; nunca decide la causa (RN-09, RN-11).",
           pg="`SELECT id, nombre FROM motivos WHERE activo;` (los motivos sugeridos salen de aqui).")
    c.caso("clasificar 200 analista XML", "POST", A + "/clasificar-motivo", "Mismo servicio con XML (clasificacion.xsd).", rol="analista",
           fmt="xml", body=xb("clasificacion", descripcion="La leche llego caliente, la temperatura estaba alta."))
    c.caso("clasificar 400 descripcion corta", "POST", A + "/clasificar-motivo", "La descripcion exige entre 10 y 2000 caracteres.",
           rol="cliente", body={"descripcion": "roto"}, codigo=400, tipo="validacion")
    c.caso("clasificar 401 sin token", "POST", A + "/clasificar-motivo", "Endpoint protegido sin Authorization.", body=desc,
           codigo=401, tipo="no_autenticado")
    c.caso("clasificar 403 centro", "POST", A + "/clasificar-motivo", "Rol sin permiso.", rol="centro", body=desc, codigo=403, tipo="sin_permiso")

    c.carpeta("02 Sincronizar y Pareto")
    c.caso("sincronizar 403 cliente", "POST", A + "/sincronizar", "Solo Administrador y Analista.", rol="cliente", body={},
           codigo=403, tipo="sin_permiso")
    c.caso("sincronizar 401 sin token", "POST", A + "/sincronizar", "Endpoint protegido sin Authorization.", body={}, codigo=401, tipo="no_autenticado")
    c.caso("sincronizar 200 exitoso", "POST", A + "/sincronizar", "RF-23: proyecta las devoluciones de PostgreSQL a MongoDB (snapshots).",
           rol="analista", body={}, tests=[tj("sincronizo casos", "J.casos_sincronizados >= 0 && J.version_cache > 0")],
           explica="No modifica PostgreSQL. Hace upsert por devolucion en `resultados_analisis`, marca no vigentes los desaparecidos y "
                   "sube la version del cache en Redis, lo que invalida el Pareto anterior.",
           pg="`SELECT count(*) FROM devoluciones WHERE eliminado_en IS NULL;` (debe coincidir con `casos_sincronizados`).",
           mongo="`db.resultados_analisis.countDocuments({tipo_analisis:'snapshot_devolucion', vigente:true})` y "
                 "`db.resultados_analisis.getIndexes()` (idx_snapshot_devolucion_unico, idx_tipo_fecha).",
           redis="`GET devoluciones:analisis:version` aumento en 1; `TTL` cerca de 86400 s.")
    c.caso("pareto 200 miss", "GET", A + "/pareto?dimension=motivo&medida=frecuencia", "RF-25, RNF-19: primer calculo tras sincronizar, "
           "con aggregate real en MongoDB.", rol="analista",
           tests=[tj("cache miss", 'J.cache === "miss" && Array.isArray(J.categorias)')],
           explica="Pipeline `$match` -> `$group` -> `$sort` sobre los snapshots vigentes; guarda el resultado en MongoDB y en Redis (10 min).",
           mongo="`db.resultados_analisis.aggregate([{$match:{tipo_analisis:'snapshot_devolucion',vigente:true}},{$group:{_id:'$motivo',total:{$sum:1}}},{$sort:{total:-1}}])` "
                 "y `db.resultados_analisis.find({tipo_analisis:'pareto'}).sort({fecha_calculo:-1}).limit(1)`.",
           redis="`KEYS devoluciones:cache:causas:*`, `GET` de la clave (JSON) y `TTL` <= 600.")
    c.caso("pareto 200 hit", "GET", A + "/pareto?dimension=motivo&medida=frecuencia", "Misma consulta: ahora sale del cache de Redis.",
           rol="analista", tests=[tj("cache hit", 'J.cache === "hit"')],
           redis="El `TTL` de la clave ya no es 600 (va bajando); no se creo una clave nueva.")
    c.caso("pareto 200 XML por proveedor y costo", "GET", A + "/pareto?dimension=proveedor&medida=costo", "Otra dimension y medida; XML.",
           rol="admin", accept="xml")
    c.caso("pareto 400 dimension desconocida", "GET", A + "/pareto?dimension=color", "Dimension fuera de la lista.", rol="analista",
           codigo=400, tipo="validacion")
    c.caso("pareto 400 fecha invalida", "GET", A + "/pareto?desde=ayer", "desde debe usar AAAA-MM-DD.", rol="analista", codigo=400, tipo="validacion")
    c.caso("pareto 400 rango invertido", "GET", A + "/pareto?desde=2026-12-31&hasta=2026-01-01", "hasta no puede ser menor que desde.",
           rol="analista", codigo=400, tipo="validacion")
    c.caso("pareto 403 cliente", "GET", A + "/pareto", "Solo Administrador y Analista.", rol="cliente", codigo=403, tipo="sin_permiso")
    c.caso("pareto 401 token invalido", "GET", A + "/pareto", "JWT sin firma valida.", rol="falso", codigo=401, tipo="token_invalido")

    c.carpeta("03 Resumen, alertas y eventos")
    c.caso("resumen 200", "GET", A + "/resumen", "Cuantos casos y reportes hay en MongoDB.", rol="analista",
           tests=[tj("trae contadores", "J.casos_sincronizados >= 0")])
    c.caso("resumen 403 cliente", "GET", A + "/resumen", "Rol sin permiso.", rol="cliente", codigo=403, tipo="sin_permiso")
    c.caso("alertas 200", "GET", A + "/alertas-fraude", "RF-25, RN-09: senales de revision humana; no acusan ni bloquean.", rol="analista",
           tests=[tj("aviso de no determinacion", "!!J.aviso")],
           pg="Misma agregacion sobre `devoluciones` y `reembolsos` de los ultimos 90 dias.")
    c.caso("alertas 200 XML", "GET", A + "/alertas-fraude", "Respuesta XML.", rol="admin", accept="xml")
    c.caso("alertas 403 cliente", "GET", A + "/alertas-fraude", "Rol sin permiso.", rol="cliente", codigo=403, tipo="sin_permiso")
    c.caso("eventos 200 paginado", "GET", A + "/eventos?pagina=1&por_pagina=5", "RNF-23: eventos publicados por los servicios.", rol="analista",
           tests=[tj("trae paginacion", "J.paginacion.por_pagina === 5")],
           mongo="`db.eventos.find({}, {datos: 0}).sort({fecha: -1}).limit(5)` y `db.eventos.getIndexes()` (idx_correlation, idx_fecha).")
    c.caso("eventos 200 XML", "GET", A + "/eventos?servicio=devoluciones", "Filtro por servicio; XML.", rol="admin", accept="xml")
    c.caso("eventos 400 correlation_id largo", "GET", A + "/eventos?correlation_id=" + "a" * 101, "El filtro no puede superar 100 caracteres.",
           rol="analista", codigo=400, tipo="validacion")
    c.caso("eventos 400 paginacion invalida", "GET", A + "/eventos?por_pagina=0", "por_pagina fuera de rango.", rol="analista",
           codigo=400, tipo="validacion")
    c.caso("eventos 403 cliente", "GET", A + "/eventos", "Rol sin permiso.", rol="cliente", codigo=403, tipo="sin_permiso")

    c.carpeta("04 Auditoria (bitacora)")
    c.caso("bitacora 200 paginada", "GET", U + "?pagina=1&por_pagina=5", "RF-30, RN-12: bitacora de operaciones.", rol="analista",
           tests=[tj("trae paginacion", "J.paginacion.por_pagina === 5")],
           pg="`SELECT id, accion, entidad, correlation_id, fecha FROM bitacora ORDER BY fecha DESC LIMIT 5;`")
    c.caso("bitacora 200 filtro XML", "GET", U + "?accion=alta_devolucion", "Filtro por accion; XML.", rol="admin", accept="xml")
    c.caso("bitacora 400 filtro largo", "GET", U + "?accion=" + "a" * 101, "El filtro no puede superar 100 caracteres.", rol="analista",
           codigo=400, tipo="validacion")
    c.caso("bitacora 403 cliente", "GET", U, "Rol sin permiso.", rol="cliente", codigo=403, tipo="sin_permiso")
    c.caso("bitacora 401 sin token", "GET", U, "Endpoint protegido sin Authorization.", codigo=401, tipo="no_autenticado")
