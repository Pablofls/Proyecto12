"""Motor de evidencias con curl (apartado 5 del enunciado: request/response y efecto en las bases).

Ejecuta peticiones reales con `curl` contra los servicios y escribe un archivo Markdown
por servicio con, para cada caso: el comando `curl` para repetirlo, la respuesta completa,
las verificaciones y el efecto en PostgreSQL. Esta pensado para correr EN LA VM (los
servicios estan en 127.0.0.1) y solo usa la biblioteca estandar, igual que el resto del
repositorio (CLAUDE.md: no se agregan librerias sin acordarlo).

Reglas de honestidad, las mismas de docs/evidencias/README.md:
 - Nada se pega a mano: lo que sale en el archivo es lo que devolvio el servicio.
 - Un caso que no cumple lo esperado NO se oculta: queda marcado como falla con su
   respuesta real, y el programa termina con codigo distinto de cero.
 - Tokens y contrasenas se ocultan. La contrasena de demo se lee de PASSWORD_DEMO o del
   `.env` y nunca se imprime ni viaja en la linea de comandos de `curl` (va por stdin).

Trazabilidad: RNF-28, RF-31, RN-12, RNF-16.
"""
import json
import os
import re
import subprocess
import time
from datetime import datetime, timezone

CABECERAS_VISIBLES = ("content-type", "content-length", "x-correlation-id", "deprecation", "link",
                      "retry-after", "content-disposition", "cache-control", "x-content-type-options",
                      "location")
MAX_LINEAS_CUERPO = 70
TIPOS_BINARIOS = ("application/pdf", "application/vnd.openxmlformats", "application/octet-stream",
                  "image/")
MARCADOR_PASSWORD = "$PASSWORD_DEMO"
JWT = re.compile(r"eyJ[A-Za-z0-9_-]{8,}\.[A-Za-z0-9_-]{2,}\.[A-Za-z0-9_-]{2,}")

# Cuentas de demostracion del seed (scripts/seed_demo.py); los correos son publicos.
USUARIOS = {
    "admin": "pablo.admin@demo.mx", "analista": "josue.analista@demo.mx",
    "cliente": "ana.cliente@demo.mx", "supervisor": "jorge.supervisor@demo.mx",
    "inspector": "valentina.inspector@demo.mx", "reembolsos": "carla.reembolsos@demo.mx",
    "almacen": "marta.almacen@demo.mx",
}


class Respuesta:
    def __init__(self, estado, razon, cabeceras, cuerpo, ms):
        self.estado, self.razon, self.cabeceras, self.cuerpo, self.ms = estado, razon, cabeceras, cuerpo, ms

    @property
    def tipo(self):
        return self.cabeceras.get("content-type", "")

    @property
    def es_binario(self):
        return any(self.tipo.startswith(t) for t in TIPOS_BINARIOS)

    @property
    def texto(self):
        return self.cuerpo.decode("utf-8", errors="replace")

    @property
    def json(self):
        return json.loads(self.cuerpo)


def analizar_respuesta(crudo, ms):
    """Separa la salida de `curl -i` en estado, cabeceras y cuerpo (maneja 100-continue)."""
    while True:
        corte = crudo.find(b"\r\n\r\n")
        if corte < 0:
            raise ValueError("respuesta sin cabeceras")
        bloque, resto = crudo[:corte].decode("iso-8859-1"), crudo[corte + 4:]
        lineas = bloque.split("\r\n")
        partes = lineas[0].split(" ", 2)
        estado = int(partes[1])
        if estado == 100 and resto.startswith(b"HTTP/"):
            crudo = resto
            continue
        cabeceras = {}
        for linea in lineas[1:]:
            if ":" in linea:
                nombre, valor = linea.split(":", 1)
                cabeceras[nombre.strip().lower()] = valor.strip()
        return Respuesta(estado, partes[2] if len(partes) > 2 else "", cabeceras, resto, ms)


def comillas(texto):
    return "'" + texto.replace("'", "'\\''") + "'"


class Corrida:
    """Una corrida = un servicio. `sigla` da los ids de los casos (P4-<SIGLA>-NN)."""

    def __init__(self, servicio, sigla, titulo, puerto, base="http://127.0.0.1", host_mostrado="$VM_HOST",
                 ejecutar_sql=None, puerto_auth=8001, password=None, via_proxy=False):
        self.servicio, self.sigla, self.titulo, self.puerto = servicio, sigla, titulo, puerto
        self.base, self.host_mostrado, self.puerto_auth = base, host_mostrado, puerto_auth
        # Con el reverse proxy los puertos 8001-8021 ya no se publican: todo entra
        # por Nginx en el puerto 80 y las rutas /api/v1 se conservan (RNF-28).
        self.via_proxy = via_proxy
        self.tokens, self.ctx, self.casos, self.limpieza = {}, {}, [], []
        self._ejecutar_sql = ejecutar_sql or self._psql
        self._password = password
        self._n = 0
        self._ocultos = set()
        self.nombre_cli = servicio   # lo que se escribe tras ejecutar.py; ejecutar.py lo ajusta

    # ------------------------------------------------------------------ infraestructura
    def _psql(self, sql):
        """PostgreSQL del compose, como indica docs/SETUP.md (el psql nativo de la VM no es el del proyecto)."""
        r = subprocess.run(["docker", "compose", "exec", "-T", "postgres", "psql", "-U", "devoluciones_app",
                            "-d", "devoluciones", "-X", "-A", "-F", " | ", "-P", "footer=off", "-v", "ON_ERROR_STOP=1"],
                           input=sql, capture_output=True, text=True, timeout=60)
        if r.returncode != 0:
            raise RuntimeError(f"psql fallo: {r.stderr.strip()[:300]}")
        return r.stdout.strip()

    def sql(self, sql):
        return self._ejecutar_sql(sql)

    def valor(self, sql):
        """Primer dato de una consulta (la salida de psql trae el encabezado en la primera linea); None si no hay filas."""
        lineas = self.sql(sql.format(**self.ctx)).splitlines()   # igual que caso(): {variable} sale del contexto
        return lineas[1].strip() if len(lineas) > 1 else None

    def password(self):
        if self._password is None:
            self._password = os.environ.get("PASSWORD_DEMO", "").strip()
            if not self._password and os.path.exists(".env"):
                for linea in open(".env", encoding="utf-8"):
                    if linea.startswith("PASSWORD_DEMO="):
                        self._password = linea.split("=", 1)[1].strip().strip("\"'")
            if not self._password:
                raise SystemExit("Falta PASSWORD_DEMO (variable de entorno o .env).")
        return self._password

    def _curl(self, metodo, url, cabeceras, cuerpo=None):
        argv = ["curl", "-sS", "-i", "--max-time", "30", "-X", metodo, url]
        for nombre, valor in cabeceras.items():
            argv += ["-H", f"{nombre}: {valor}"]
        if cuerpo is not None:
            argv += ["--data-binary", "@-"]   # por stdin: la contrasena no queda en la lista de procesos
        inicio = time.perf_counter()
        r = subprocess.run(argv, input=cuerpo, capture_output=True, timeout=45)
        ms = round((time.perf_counter() - inicio) * 1000)
        if r.returncode != 0:
            raise RuntimeError(f"curl fallo ({r.returncode}): {r.stderr.decode()[:200]}")
        return analizar_respuesta(r.stdout, ms)

    def _con_contrasena(self, cuerpo):
        """Un cuerpo puede llevar el marcador $PASSWORD_DEMO (ej. reconfirmar contrasena): se envia la real, se muestra el marcador."""
        if MARCADOR_PASSWORD not in cuerpo:
            return cuerpo
        real = self.password()
        self._ocultos.add(real)
        return cuerpo.replace(MARCADOR_PASSWORD, json.dumps(real)[1:-1])

    def esconder(self, valor):
        """Registra un secreto generado en la corrida (ej. permiso de operacion) para que nunca salga en el archivo."""
        self._ocultos.add(valor)

    def ocultar(self, texto):
        for secreto in self._ocultos:
            texto = texto.replace(secreto, "***oculto***")
        return JWT.sub("***jwt***", texto)

    # ------------------------------------------------------------------ sesiones
    def sesion(self, rol):
        """Inicia sesion con la cuenta de demo del rol; el token se reutiliza en toda la corrida."""
        if rol in self.tokens:
            return self.tokens[rol]
        cuerpo = json.dumps({"email": USUARIOS[rol], "password": self.password()}).encode()
        self._ocultos.add(self.password())
        r = self._curl("POST", f"{self.origen(self.puerto_auth)}/api/v1/auth/login",
                       {"Content-Type": "application/json"}, cuerpo)
        if r.estado != 200:
            raise SystemExit(f"No se pudo iniciar sesion como {rol}: HTTP {r.estado} (el login admite 10 por minuto).")
        token = r.json["access_token"]
        self.tokens[rol] = token
        self._ocultos.add(token)
        return token

    # ------------------------------------------------------------------ casos
    def origen(self, puerto):
        return self.base if self.via_proxy else f"{self.base}:{puerto}"

    def caso(self, titulo, metodo, ruta, *, objetivo, rol=None, json_cuerpo=None, xml=None, accept="application/json",
             espera=200, verifica=(), guarda=None, efecto=None, cabeceras_extra=None, token=None, puerto=None):
        """Ejecuta un caso y lo registra.

        rol: cuenta de demo que inicia sesion; None = sin Authorization; `token` fuerza uno literal (para probar tokens malos).
        verifica: lista de (descripcion, funcion(respuesta) -> bool).
        guarda: {"variable": funcion(respuesta)} para encadenar casos (ids creados, etc.).
        efecto: (descripcion, sql) o lista de ellos; el sql puede usar {variable} del contexto.
        """
        self._n += 1
        id_caso = f"P4-{self.sigla}-{self._n:02d}"
        puerto = puerto or self.puerto
        cabeceras, mostradas = {"Accept": accept}, {"Accept": accept}
        cuerpo, cuerpo_mostrado = None, None
        if json_cuerpo is not None:
            cuerpo_mostrado = json.dumps(json_cuerpo, ensure_ascii=False, separators=(",", ":"))
            cabeceras["Content-Type"] = mostradas["Content-Type"] = "application/json"
            cuerpo = self._con_contrasena(cuerpo_mostrado).encode()
        elif xml is not None:
            cuerpo_mostrado = xml
            cabeceras["Content-Type"] = mostradas["Content-Type"] = "application/xml"
            cuerpo = xml.encode()
        if rol:
            cabeceras["Authorization"] = f"Bearer {self.sesion(rol)}"
            mostradas["Authorization"] = f"Bearer $TOKEN_{rol.upper()}"
        elif token is not None:
            cabeceras["Authorization"] = f"Bearer {token}"
            mostradas["Authorization"] = f"Bearer {token}"
        for nombre, valor in (cabeceras_extra or {}).items():
            cabeceras[nombre] = mostradas[nombre] = valor
        ruta = ruta.format(**self.ctx)
        resp = self._curl(metodo, f"{self.origen(puerto)}{ruta}", cabeceras, cuerpo)

        registro = {
            "id": id_caso, "titulo": titulo, "objetivo": objetivo, "metodo": metodo, "ruta": ruta, "puerto": puerto,
            "cabeceras": mostradas, "cuerpo": cuerpo_mostrado, "esperado": espera, "resp": resp,
            "rol": rol, "verificaciones": [(f"HTTP {espera}", resp.estado == espera)], "efectos": [],
        }
        for texto, funcion in verifica:
            try:
                ok = bool(funcion(resp))
            except Exception:
                ok = False
            registro["verificaciones"].append((texto, ok))
        if guarda:
            for nombre, funcion in guarda.items():
                try:
                    self.ctx[nombre] = funcion(resp)
                except Exception:
                    registro["verificaciones"].append((f"no se pudo guardar {nombre}", False))
        for descripcion, consulta in ([efecto] if isinstance(efecto, tuple) else (efecto or [])):
            consulta = consulta.format(**self.ctx)
            try:
                salida = self.sql(consulta)
            except Exception as exc:  # el efecto es parte de la evidencia: si falla, se ve
                salida = f"ERROR: {exc}"
                registro["verificaciones"].append((f"efecto en la base: {descripcion}", False))
            registro["efectos"].append((descripcion, consulta, salida))
        registro["ok"] = all(ok for _, ok in registro["verificaciones"])
        self.casos.append(registro)
        return resp

    # ------------------------------------------------------------------ salida
    def comando(self, c):
        """El curl que el lector puede copiar: mismo metodo, cabeceras y cuerpo que se ejecutaron."""
        url = (f"http://{self.host_mostrado}{c['ruta']}" if self.via_proxy
               else f"http://{self.host_mostrado}:{c['puerto']}{c['ruta']}")
        partes = [f'curl -sS -i -X {c["metodo"]} "{url}"']
        for nombre, valor in c["cabeceras"].items():
            partes.append(f'-H "{nombre}: {valor}"')
        if c["cuerpo"] is not None:
            partes.append(f"-d {comillas(c['cuerpo'])}")
        return self.ocultar(" \\\n  ".join(partes))

    def _cuerpo_legible(self, r):
        if r.es_binario:
            return f"(contenido binario de {len(r.cuerpo)} bytes; empieza con {r.cuerpo[:8]!r})", "text"
        texto = r.texto
        if "json" in r.tipo:
            try:
                texto = json.dumps(r.json, indent=2, ensure_ascii=False)
            except ValueError:
                pass
            lenguaje = "json"
        else:
            lenguaje = "xml" if "xml" in r.tipo else "text"
        lineas = texto.split("\n")
        if len(lineas) > MAX_LINEAS_CUERPO:
            lineas = lineas[:MAX_LINEAS_CUERPO] + [f"... (recortado: {len(lineas) - MAX_LINEAS_CUERPO} lineas mas)"]
        return self.ocultar("\n".join(lineas)), lenguaje

    def markdown(self, commit="", ahora=None, interrupcion=None):
        ahora = ahora or datetime.now(timezone.utc)
        fallas = [c for c in self.casos if not c["ok"]]
        sal = [f"# Evidencia con curl - `{self.servicio}`", "",
               f"Ejecutada en la VM el {ahora:%Y-%m-%d %H:%M} UTC con `scripts/evidencias/ejecutar.py {self.nombre_cli}`"
               + (f" (commit `{commit[:7]}`)." if commit else "."),
               f"Casos: **{len(self.casos)}**, correctos: **{len(self.casos) - len(fallas)}**, con falla: **{len(fallas)}**. "
               "Los tokens y la contrasena de demo estan ocultos; la IP de la VM se muestra como `$VM_HOST`.", "",
               "Cada respuesta es la que devolvio el servicio: nada se pego a mano. Un caso que no cumple lo esperado "
               "queda marcado como falla, no se omite.", ""]
        if interrupcion:
            sal += [f"> **CORRIDA INTERRUMPIDA** tras el caso {len(self.casos)}: `{interrupcion}`. "
                    "Los casos siguientes no se ejecutaron.", ""]
        sal += [
               "## Preparacion", "",
               "```bash", "export VM_HOST=<IP-DE-LA-VM>      # o 127.0.0.1 si corres los comandos dentro de la VM",
               "export PASSWORD_DEMO=...                 # la de las cuentas de demo; no se versiona",
               "login() { curl -s -X POST \"http://$VM_HOST:8001/api/v1/auth/login\" -H 'Content-Type: application/json' \\",
               "  -d \"{\\\"email\\\":\\\"$1\\\",\\\"password\\\":\\\"$PASSWORD_DEMO\\\"}\" | jq -r .access_token; }"]
        for rol in sorted(self.tokens):
            sal.append(f"export TOKEN_{rol.upper()}=$(login {USUARIOS[rol]})")
        sal += ["```", "", "El login admite 10 intentos por minuto por IP (RNF-13); el token dura 15 minutos.", "",
                "## Resumen", "", "| Caso | Resultado | HTTP | Descripcion |", "|---|---|---|---|"]
        for c in self.casos:
            sal.append(f"| [{c['id']}](#{c['id'].lower()}) | {'correcto' if c['ok'] else '**FALLA**'} | "
                       f"{c['resp'].estado} | {c['titulo']} |")
        sal.append("")
        for c in self.casos:
            r = c["resp"]
            cuerpo, lenguaje = self._cuerpo_legible(r)
            sal += [f"## {c['id']}", "", f"**{c['titulo']}**", "", f"Objetivo: {c['objetivo']}", "",
                    "Comando:", "", "```bash", self.comando(c), "```", "",
                    f"Respuesta - **{r.estado} {r.razon}** ({r.ms} ms, {len(r.cuerpo)} bytes):", "", "```http"]
            for nombre in CABECERAS_VISIBLES:
                if nombre in r.cabeceras:
                    sal.append(f"{'-'.join(p.capitalize() if p != 'id' else 'ID' for p in nombre.split('-'))}: "
                               f"{self.ocultar(r.cabeceras[nombre])}")
            sal += ["```", "", f"```{lenguaje}", cuerpo, "```", "", "Verificaciones:", ""]
            sal += [f"- {'ok' if ok else '**FALLA**'}: {texto}" for texto, ok in c["verificaciones"]]
            for descripcion, consulta, salida in c["efectos"]:
                sal += ["", f"Efecto en PostgreSQL - {descripcion}:", "", "```sql", consulta.strip(), "```", "",
                        "```text", self.ocultar(salida) or "(sin filas)", "```"]
            sal.append("")
        if self.limpieza:
            sal += ["## Limpieza", "",
                    "Al terminar se borraron los datos que creo esta corrida, para no dejar basura en la base de "
                    "demostracion. **La bitacora no se toca**: es de solo agregar (migracion 045).", ""]
        return "\n".join(sal) + "\n"

    def limpiar(self):
        for sql in self.limpieza:
            self.sql(sql.format(**self.ctx))

    def escribir(self, ruta, commit="", interrupcion=None):
        with open(ruta, "w", encoding="utf-8") as f:
            f.write(self.markdown(commit, interrupcion=interrupcion))
        return sum(1 for c in self.casos if not c["ok"])
