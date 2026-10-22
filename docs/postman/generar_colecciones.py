"""Genera las 8 colecciones Postman v2.1, el environment de la VM, docs/EVIDENCIAS.md
y el checklist de capturas a partir de UNA sola especificacion (especificaciones.py).

    python3 docs/postman/generar_colecciones.py

Por que un solo generador: Postman, EVIDENCIAS.md y el checklist comparten los
mismos identificadores de captura; si se escribieran a mano divergirian
(RF-31, RNF-05). Solo usa libreria estandar: la VM y las laptops no necesitan
instalar nada para regenerar.

Nada de lo que se genera contiene credenciales: password_demo y los tokens
quedan vacios y se llenan al correr contra la VM (docs/evidencias/README.md).
"""
import base64
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(os.path.dirname(AQUI))
sys.path.insert(0, AQUI)

# clave (carpeta en services/), titulo, puerto, variable de URL, prefijo de la API.
SERVICIOS = [
    ("auth", "Autenticacion", 8001, "auth_url", "/api/v1/auth"),
    ("devoluciones", "Devoluciones", 8002, "devoluciones_url", "/api/v1/devoluciones"),
    ("logistica", "Logistica inversa", 8003, "logistica_url", "/api/v1/logistica"),
    ("inspecciones", "Inspecciones y disposicion", 8004, "inspecciones_url", "/api/v1/inspecciones"),
    ("reembolsos_costos", "Reembolsos y costos", 8005, "reembolsos_url", "/api/v1/reembolsos-costos"),
    ("ventas_catalogos", "Ventas y catalogos", 8006, "ventas_url", "/api/v1/ventas"),
    ("evidencias", "Evidencias", 8007, "evidencias_url", "/api/v1/evidencias"),
    ("analisis_auditoria", "Analisis y auditoria", 8008, "analisis_url", "/api/v1/analisis"),
]
INFO = {s[0]: s for s in SERVICIOS}

# rol -> correo del seed (scripts/seed_demo.py). Las contrasenas NO van aqui.
ROLES = {
    "cliente": ("miguel.cliente@demo.mx", "Cliente (dueno de la compra)"),
    "otro": ("ana.cliente@demo.mx", "Cliente distinto al dueno"),
    "inspector": ("valentina.inspector@demo.mx", "Inspector"),
    "centro": ("roberto.centro@demo.mx", "Encargado del Centro de Devoluciones"),
    "coordinador": ("david.logistica@demo.mx", "Coordinador de Logistica"),
    "analista": ("josue.analista@demo.mx", "Analista de Devoluciones"),
    "reembolsos": ("carla.reembolsos@demo.mx", "Encargado de Reembolsos"),
    "admin": ("pablo.admin@demo.mx", "Administrador"),
}
ROL_TEXTO = {k: v[1] for k, v in ROLES.items()}
ROL_TEXTO["falso"] = "Token invalido (cadena sin firma)"

PUBLICAS = ("/api/", "/health", "/contratos", "/docs")
SENTINELA = re.compile(r'"@id:([a-z_]+)"')

CORRIDA = {"n": 0}          # numero de captura, global y estable
TODOS = []                  # metadatos de cada caso, para EVIDENCIAS y checklist


def h(clave, valor):
    return {"key": clave, "value": valor}


def jb(datos):
    """JSON de cuerpo. "@id:var" se vuelve {{var}} sin comillas: los ids viajan
    como numero y Postman los sustituye antes de enviar."""
    return SENTINELA.sub(lambda m: "{{" + m.group(1) + "}}",
                         json.dumps(datos, indent=2, ensure_ascii=False))


def xb(raiz, **campos):
    cuerpo = "".join(f"  <{k}>{v}</{k}>\n" for k, v in campos.items())
    return f"<{raiz}>\n{cuerpo}</{raiz}>"


def espera(codigo, tipo=None, xml=False):
    lineas = [f'pm.test("HTTP {codigo}", () => pm.response.to.have.status({codigo}));']
    if tipo:
        leer = ("xml2Json(pm.response.text()).error.tipo" if xml
                else "pm.response.json().error.tipo")
        lineas.append(f'pm.test("error.tipo = {tipo}", () => pm.expect({leer}).to.eql("{tipo}"));')
    lineas.append('pm.test("Trae X-Correlation-ID", () => '
                  'pm.response.to.have.header("X-Correlation-ID"));')
    return lineas


def slug(texto):
    return re.sub(r"[^a-z0-9]+", "_", texto.lower()).strip("_")


def endpoint_de(ruta):
    """/x/123?a=1 -> /x/{id}: agrupa los casos por endpoint de openapi.yaml."""
    ruta = ruta.split("?")[0]
    ruta = re.sub(r"\{\{[a-z_]+\}\}", "{id}", ruta)
    ruta = re.sub(r"/\d+(?=/|$)", "/{id}", ruta)
    # Los siete catalogos comparten endpoint en openapi.yaml: /catalogos/{nombre}.
    return re.sub(r"^/api/v1/catalogos/[a-z]+", "/api/v1/catalogos/{nombre}", ruta)


class Coleccion:
    def __init__(self, clave):
        self.clave = clave
        _, self.titulo, self.puerto, self.var_url, self.prefijo = INFO[clave]
        self.carpetas = []

    # ------------------------------------------------------------------ #
    def carpeta(self, nombre):
        self.carpetas.append({"name": nombre, "item": []})

    def _url(self, ruta, url):
        if url:
            return url
        if ruta.startswith(PUBLICAS):
            return "{{" + self.var_url + "}}" + ruta
        return "{{" + self.var_url + "}}" + self.prefijo + ruta

    def caso(self, nombre, metodo, ruta, desc, *, rol=None, fmt="json", accept=None,
             body=None, contenido=None, formdata=None, codigo=200, tipo=None,
             tests=(), previo=(), guarda=None, url=None, ev=True, ep=None, solo_tests=False,
             obj=None, explica=None, pg=None, mongo=None, redis=None):
        """Agrega una peticion con sus verificaciones.

        rol    -> usuario del seed cuyo token viaja como Bearer ('falso' = token
                  invalido; None = sin Authorization).
        fmt    -> 'json' o 'xml': formato del cuerpo Y de la respuesta (Accept).
        accept -> sobreescribe el Accept (p. ej. GET con respuesta XML).
        solo_tests -> no agrega las verificaciones comunes (casos que se repiten
                  hasta provocar un bloqueo o un limite).
        ev     -> False para pasos de preparacion que no son evidencia.
        pg/mongo/redis -> que debe verse en cada base tras el caso (EVIDENCIAS.md).
        """
        xml = (accept or fmt) == "xml"
        encabezados = []
        if rol:
            encabezados.append(h("Authorization", "Bearer {{token_" + rol + "}}"))
        if formdata is None and (body is not None or contenido):
            encabezados.append(h("Content-Type", contenido or (
                "application/xml" if fmt == "xml" else "application/json")))
        encabezados.append(h("Accept", "application/xml" if xml else "application/json"))

        peticion = {"method": metodo, "header": encabezados,
                    "url": self._url(ruta, url), "description": desc}
        texto_body = None
        if formdata is not None:
            peticion["body"] = {"mode": "formdata", "formdata": formdata}
            texto_body = "multipart/form-data: " + ", ".join(
                f"{f['key']}={'(archivo ' + f['src'] + ')' if f['type'] == 'file' else f['value']}"
                for f in formdata)
        elif body is not None:
            texto_body = body if isinstance(body, str) else jb(body)
            peticion["body"] = {"mode": "raw", "raw": texto_body, "options": {
                "raw": {"language": "xml" if fmt == "xml" else "json"}}}

        guardado = [f'pm.environment.set("{k}", {v});' for k, v in (guarda or {}).items()]
        item = {"name": nombre, "request": peticion, "event": []}
        if previo:
            item["event"].append({"listen": "prerequest", "script": {
                "type": "text/javascript", "exec": list(previo)}})
        item["event"].append({"listen": "test", "script": {
            "type": "text/javascript",
            "exec": (list(tests) if solo_tests
                     else espera(codigo, tipo, xml) + list(tests) + guardado)}})
        self.carpetas[-1]["item"].append(item)

        if ev:
            CORRIDA["n"] += 1
            ep = ep or endpoint_de(self._url(ruta, url).split("}}", 1)[1])
            TODOS.append({
                "n": CORRIDA["n"], "servicio": self.clave, "carpeta": self.carpetas[-1]["name"],
                "nombre": nombre, "metodo": metodo, "ruta": self._url(ruta, url), "ep": ep,
                "desc": desc, "rol": rol, "fmt": "xml" if xml else "json",
                "encabezados": encabezados, "body": texto_body, "codigo": codigo,
                "tipo": tipo, "obj": obj, "explica": explica, "pg": pg,
                "mongo": mongo, "redis": redis,
                "id": "%03d_%s_%s_%s_%d%s" % (
                    CORRIDA["n"], self.clave, metodo.lower(),
                    slug(ep.replace("/api/v1/" + self.prefijo.rsplit("/", 1)[-1], "")
                         .replace("/api/v1/", "")) or "raiz", codigo,
                    "_xml" if xml else ""),
            })

    def login(self, rol):
        """Preparacion: cada coleccion inicia sesion con sus propios roles, asi
        puede correrse sola. No es evidencia (la evidencia de login es la de auth)."""
        email = "{{email_" + rol + "}}"
        self.caso(f"login {rol} (preparacion)", "POST", "/api/v1/auth/login",
                  f"Obtiene el JWT de {ROL_TEXTO[rol]} y lo guarda en token_{rol}.",
                  url="{{auth_url}}/api/v1/auth/login",
                  body={"email": email, "password": "{{password_demo}}"}, ev=False,
                  guarda={f"token_{rol}": "pm.response.json().access_token"})

    def salud(self, dependencias=("postgresql", "redis")):
        comprobar = [f'pm.test("{d} ok", () => pm.expect(pm.response.json().dependencias.{d}.ok).to.be.true);'
                     for d in dependencias]
        self.caso("health 200 (preparacion)", "GET", "/health",
                  "RNF-22: el servicio y sus dependencias responden antes de empezar.",
                  tests=comprobar, ev=False)

    def a_json(self):
        return {
            "info": {
                "name": f"{self.titulo} ({self.clave}) - v1",
                "description": (
                    f"Evidencias request/response del servicio {self.clave} (puerto {self.puerto}). "
                    "Requiere el environment vm.postman_environment.json con vm_host, "
                    "password_demo y, si aplica, los ids de las colecciones previas. "
                    "Orden de corrida y capturas: docs/evidencias/README.md."),
                "schema": "https://schema.getpostman.com/json/collection/v2.1.0/collection.json",
            },
            "item": self.carpetas,
        }


# --------------------------------------------------------------------------- #
# Verificacion contra openapi.yaml (sin PyYAML: regex sobre el texto)
# --------------------------------------------------------------------------- #
METODOS = ("get", "post", "put", "patch", "delete")


def leer_openapi(clave):
    """-> {(metodo, ruta con {}): {'summary':..., 'params': [...]}}"""
    with open(os.path.join(RAIZ, "services", clave, "openapi.yaml"), encoding="utf-8") as f:
        texto = f.read()
    cabeza = list(re.finditer(r"^  (/[^\s:]*):", texto, re.M))
    salida = {}
    for i, m in enumerate(cabeza):
        fin = cabeza[i + 1].start() if i + 1 < len(cabeza) else len(texto)
        bloque = texto[m.end():fin]
        marcas = list(re.finditer(r"(?:^|[\s{,])(get|post|put|patch|delete):", bloque))
        for j, mm in enumerate(marcas):
            tramo = bloque[mm.end():marcas[j + 1].start() if j + 1 < len(marcas) else len(bloque)]
            resumen = re.search(r"summary:\s*(.+?)(?=,\s*[A-Za-z_]+:|\}|\n|$)", tramo)
            # Parametros del metodo mas los del nivel de la ruta (antes del primer metodo).
            params = (re.findall(r"name:\s*(\w+)[,\s]+in:\s*(path|query)", tramo)
                      + re.findall(r"name:\s*(\w+)[,\s]+in:\s*(path|query)", bloque[:marcas[0].start()]))
            salida[(mm.group(1), re.sub(r"\{[^}]*\}", "{}", m.group(1)))] = {
                "ruta": m.group(1),
                "summary": resumen.group(1).strip().strip("'\"") if resumen else "",
                "params": sorted(set(params))}
    return salida


def verificar(colecciones):
    avisos = []
    for clave, col in colecciones.items():
        oa = leer_openapi(clave)
        mios = {(c["metodo"].lower(), re.sub(r"\{[^}]*\}", "{}", c["ep"]))
                for c in TODOS if c["servicio"] == clave}
        mios.add(("get", "/health"))
        for (m, r), dato in oa.items():
            if (m, r) not in mios and r not in ("/docs", "/openapi.json"):
                avisos.append(f"{clave}: openapi tiene {m.upper()} {dato['ruta']} sin caso")
        for m, r in sorted(mios - set(oa)):
            avisos.append(f"{clave}: hay caso {m.upper()} {r} que openapi.yaml no declara")
    return avisos


# --------------------------------------------------------------------------- #
# Salidas
# --------------------------------------------------------------------------- #
def escribir_json(ruta, datos):
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(datos, f, ensure_ascii=False, indent=2)
        f.write("\n")


def environment():
    valores = [("vm_host", "IP-DE-LA-VM", "default")]
    valores += [(s[3], "http://{{vm_host}}:%d" % s[2], "default") for s in SERVICIOS]
    valores += [(f"email_{r}", ROLES[r][0], "default") for r in ROLES]
    valores += [("email_bloqueo", "sofia.cliente@demo.mx", "default"),
               ("password_demo", "", "secret")]
    valores += [(f"token_{r}", "", "secret") for r in ROLES]
    valores += [("token_falso", "esto-no-es-un-token", "default"),
                # Lineas de venta del seed: 72 es de Miguel (3 unidades), 85 de Ana.
                ("venta_detalle_id", "72", "default"), ("venta_detalle_ajena", "85", "default"),
                ("motivo_id", "1", "default")]
    for v in ("devolucion_id", "devolucion_xml_id", "devolucion_ev_id", "folio", "venta_id",
              "recoleccion_id", "ruta_id", "transportista_id", "disposicion_id",
              "evidencia_id", "evidencia_xml_id", "evidencia_archivo_id", "url_enlace",
              "catalogo_registro_id", "catalogo_xml_id", "analista_id", "refresh_token",
              "fecha_futura", "url_enlace_consulta", "intentos_bloqueo", "intentos_limite"):
        valores.append((v, "", "default"))
    return {"name": "VM Proyecto12 (GCP)", "_postman_variable_scope": "environment",
            "values": [{"key": k, "value": v, "type": t, "enabled": True}
                       for k, v, t in valores]}


def celda(texto):
    return (texto or "").replace("|", "\\|").replace("\n", " ")


def bloque(codigo, lenguaje=""):
    return f"```{lenguaje}\n{codigo}\n```"


def generar_evidencias(colecciones):
    L = ["# Evidencias request/response por servicio (apartado 5)", "",
         "<!-- Generado por docs/postman/generar_colecciones.py; no editar a mano. "
         "Para cambiar algo, edita docs/postman/especificaciones.py y regenera. -->", "",
         "Cada endpoint sigue la plantilla del apartado 5: URL y metodo, objetivo, parametros, "
         "headers, body, respuesta, codigo, explicacion, evidencia en PostgreSQL / MongoDB / "
         "Redis, error controlado y captura.", "",
         "**Que es real y que esta pendiente.** URL, metodo, headers, body y la explicacion salen "
         "del codigo del servicio y de su `openapi.yaml`. La **respuesta** y la **captura** solo "
         "existen despues de ejecutar en la VM: hasta entonces estan marcadas "
         "`<!-- CAPTURA PENDIENTE: id -->`. Ninguna respuesta de este archivo fue ejecutada. "
         "Como capturarlas: [docs/evidencias/README.md](evidencias/README.md); lista de "
         "archivos esperados: [docs/evidencias/CHECKLIST_CAPTURAS.md](evidencias/CHECKLIST_CAPTURAS.md).",
         "", "Las variables `{{...}}` son las del environment "
         "`docs/postman/vm.postman_environment.json`.", "", "## Indice", ""]
    for clave, titulo, puerto, _, _ in SERVICIOS:
        n = sum(1 for c in TODOS if c["servicio"] == clave)
        L.append(f"- [{titulo} (`{clave}`, puerto {puerto})](#{slug(clave)}) - {n} capturas")
    L.append("")
    for clave, titulo, puerto, var, prefijo in SERVICIOS:
        oa = leer_openapi(clave)
        L += [f"## {clave}", "", f"**{titulo}** - puerto {puerto} - coleccion "
              f"`docs/postman/{clave}.postman_collection.json` - Swagger en `/docs` del servicio.", ""]
        endpoints = []
        for c in TODOS:
            if c["servicio"] != clave:
                continue
            llave = (c["metodo"], c["ep"])
            if llave not in endpoints:
                endpoints.append(llave)
        for metodo, ep in endpoints:
            casos = [c for c in TODOS if c["servicio"] == clave and (c["metodo"], c["ep"]) == (metodo, ep)]
            ok = [c for c in casos if c["codigo"] < 300]
            err = [c for c in casos if c["codigo"] >= 300]
            ppal = ok[0] if ok else casos[0]
            dato = oa.get((metodo.lower(), re.sub(r"\{[^}]*\}", "{}", ep)), {})
            L += [f"### {metodo} {ep}", ""]
            if dato.get("summary"):
                L += [f"*openapi.yaml:* {dato['summary']}", ""]
            L += ["| Campo | Detalle |", "|---|---|",
                  f"| URL y metodo | `{metodo} {ppal['ruta']}` |",
                  f"| Objetivo | {celda(ppal['obj'] or ppal['desc'])} |",
                  "| Parametros | " + (celda(", ".join(f"`{n}` ({d})" for n, d in dato.get("params", []))) or "Ninguno") + " |",
                  "| Headers | " + celda("; ".join(f"`{x['key']}: {x['value']}`" for x in ppal["encabezados"])) + " |",
                  f"| Roles (caso exitoso) | {celda(', '.join(sorted({ROL_TEXTO[c['rol']] for c in (ok or casos) if c['rol'] and c['rol'] != 'falso'})) or 'Sin autenticacion')} |",
                  f"| Codigo HTTP esperado | {ppal['codigo']} |",
                  f"| Explicacion | {celda(ppal['explica'] or ppal['desc'])} |",
                  f"| Evidencia en PostgreSQL | {celda(ppal['pg'] or 'No aplica a este endpoint.')} |",
                  f"| Evidencia en MongoDB | {celda(ppal['mongo'] or 'No aplica a este endpoint.')} |",
                  f"| Evidencia en Redis | {celda(ppal['redis'] or 'No aplica a este endpoint.')} |", ""]
            if ppal["body"]:
                lenguaje = ("" if ppal["body"].startswith("multipart")
                            else "xml" if ppal["fmt"] == "xml" and ppal["metodo"] != "GET" and ppal["body"].lstrip().startswith("<")
                            else "json")
                L += ["**Body de ejemplo** (caso " + ppal["nombre"] + "):", "",
                      bloque(ppal["body"], lenguaje), ""]
            L += ["**Respuesta (caso exitoso):**" if ok else "**Respuesta:**", "",
                  f"<!-- CAPTURA PENDIENTE: {ppal['id']} -->", ""]
            L += ["**Casos de la coleccion** (cada uno con su captura):", "",
                  "| # | Caso | Formato | Rol | Codigo | error.tipo | Captura |", "|---|---|---|---|---|---|---|"]
            for c in ok + err:
                L.append(f"| {c['n']} | {celda(c['nombre'])} | {c['fmt'].upper()} | "
                         f"{celda(ROL_TEXTO.get(c['rol'], 'ninguno') if c['rol'] else 'ninguno')} | "
                         f"{c['codigo']} | {c['tipo'] or '-'} | `<!-- CAPTURA PENDIENTE: {c['id']} -->` |")
            L.append("")
            if err:
                L += ["**Errores controlados:**", ""]
                for c in err:
                    L.append(f"- **{c['codigo']} `{c['tipo']}`** - {c['nombre']}: {c['desc']}")
                L.append("")
    with open(os.path.join(RAIZ, "docs", "EVIDENCIAS.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


def generar_checklist():
    L = ["# Checklist de capturas", "",
         "<!-- Generado por docs/postman/generar_colecciones.py. Marca [x] al guardar el archivo. -->", "",
         "Guarda cada captura en `docs/evidencias/capturas/<id>.png` (la peticion y la respuesta "
         "visibles; **oculta o tacha el token Bearer**). Los ids son los mismos que los marcadores "
         "`CAPTURA PENDIENTE` de `docs/EVIDENCIAS.md`.", ""]
    for clave, *_ in SERVICIOS:
        L += [f"## {clave}", "", "| Listo | Archivo | Carpeta de la coleccion | Caso |", "|---|---|---|---|"]
        for c in TODOS:
            if c["servicio"] == clave:
                L.append(f"| [ ] | `{c['id']}.png` | {celda(c['carpeta'])} | {celda(c['nombre'])} |")
        L.append("")
    os.makedirs(os.path.join(RAIZ, "docs", "evidencias"), exist_ok=True)
    with open(os.path.join(RAIZ, "docs", "evidencias", "CHECKLIST_CAPTURAS.md"), "w", encoding="utf-8") as f:
        f.write("\n".join(L) + "\n")


# Archivos de prueba para las evidencias (multipart). PNG minimo valido de 1x1 y
# un texto plano para provocar el 415; no contienen nada sensible.
PNG_1X1 = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg==")


def escribir_fixtures():
    carpeta = os.path.join(AQUI, "fixtures")
    os.makedirs(carpeta, exist_ok=True)
    with open(os.path.join(carpeta, "evidencia_prueba.png"), "wb") as f:
        f.write(PNG_1X1)
    with open(os.path.join(carpeta, "no_es_imagen.txt"), "w", encoding="utf-8") as f:
        f.write("Archivo de texto: el servicio debe rechazarlo con 415.\n")


def main():
    import especificaciones
    colecciones = {}
    for clave, *_ in SERVICIOS:
        col = Coleccion(clave)
        getattr(especificaciones, clave)(col)
        colecciones[clave] = col
    for clave, col in colecciones.items():
        escribir_json(os.path.join(AQUI, f"{clave}.postman_collection.json"), col.a_json())
    escribir_json(os.path.join(AQUI, "vm.postman_environment.json"), environment())
    escribir_fixtures()
    generar_evidencias(colecciones)
    generar_checklist()
    avisos = verificar(colecciones)
    for clave, col in colecciones.items():
        n = sum(len(c["item"]) for c in col.carpetas)
        print(f"{clave:20s} {n:3d} peticiones, {sum(1 for c in TODOS if c['servicio'] == clave):3d} capturas")
    for a in avisos:
        print("AVISO:", a)
    print("Verificacion contra openapi.yaml:", "OK" if not avisos else f"{len(avisos)} aviso(s)")
    return 1 if avisos else 0


if __name__ == "__main__":
    sys.exit(main())
