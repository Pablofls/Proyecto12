"""Pruebas del motor de evidencias. Usan `curl` de verdad contra un servidor falso en este proceso;
no tocan la VM ni las bases.

    python3 -m pytest scripts/evidencias/test_motor.py

Trazabilidad: RNF-28, RNF-16.
"""
import json
import os
import subprocess
import sys
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import motor  # noqa: E402

JWT_FALSO = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxIn0.firma12345678"
PASSWORD = "clave-demo-que-no-debe-salir"


class Falso(BaseHTTPRequestHandler):
    visto = []

    def log_message(self, *a):
        pass

    def _responder(self, estado, tipo, cuerpo, extra=None):
        self.send_response(estado)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(cuerpo)))
        self.send_header("X-Correlation-ID", "abc123")
        for k, v in (extra or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(cuerpo)

    def _leer(self):
        n = int(self.headers.get("Content-Length") or 0)
        return self.rfile.read(n)

    def do_POST(self):
        cuerpo = self._leer()
        Falso.visto.append((self.path, self.headers.get("Authorization"), self.headers.get("Content-Type"), cuerpo))
        if self.path == "/api/v1/auth/login":
            return self._responder(200, "application/json", json.dumps({"access_token": JWT_FALSO}).encode())
        if self.path == "/xml":
            return self._responder(201, "application/xml", b"<respuesta><id>7</id></respuesta>")
        return self._responder(200, "application/json", json.dumps({"eco": cuerpo.decode()}).encode())

    def do_GET(self):
        Falso.visto.append((self.path, self.headers.get("Authorization"), None, b""))
        if self.path == "/ok":
            cuerpo = {"id": 41, "token_visible": JWT_FALSO, "autorizacion": self.headers.get("Authorization")}
            return self._responder(200, "application/json", json.dumps(cuerpo).encode(), {"Deprecation": "true"})
        if self.path == "/pdf":
            return self._responder(200, "application/pdf", b"%PDF-1.4\n" + b"x" * 500)
        if self.path == "/larga":
            return self._responder(200, "application/json", json.dumps(list(range(300))).encode())
        return self._responder(404, "application/json", b'{"error": {"tipo": "no_encontrado"}}')


@pytest.fixture(scope="module")
def puerto():
    servidor = ThreadingHTTPServer(("127.0.0.1", 0), Falso)
    hilo = threading.Thread(target=servidor.serve_forever, daemon=True)
    hilo.start()
    yield servidor.server_address[1]
    servidor.shutdown()


@pytest.fixture
def corrida(puerto):
    Falso.visto.clear()
    return motor.Corrida("servicio-x", "SX", "Servicio X", puerto, puerto_auth=puerto, password=PASSWORD,
                         ejecutar_sql=lambda sql: f"resultado de: {sql}")


# --------------------------------------------------------------------------- analisis de la respuesta
def test_analizar_respuesta_separa_estado_cabeceras_y_cuerpo():
    r = motor.analizar_respuesta(b"HTTP/1.1 201 Created\r\nContent-Type: application/json\r\nX-A: b\r\n\r\n{\"a\":1}", 12)
    assert (r.estado, r.razon, r.cabeceras["x-a"], r.json, r.ms) == (201, "Created", "b", {"a": 1}, 12)


def test_analizar_respuesta_ignora_el_100_continue():
    crudo = b"HTTP/1.1 100 Continue\r\n\r\nHTTP/1.1 200 OK\r\nContent-Type: text/plain\r\n\r\nhola"
    r = motor.analizar_respuesta(crudo, 1)
    assert (r.estado, r.texto) == (200, "hola")


def test_analizar_respuesta_sin_cabeceras_falla():
    with pytest.raises(ValueError):
        motor.analizar_respuesta(b"basura", 1)


# --------------------------------------------------------------------------- secretos
def test_el_token_y_la_contrasena_nunca_salen_en_el_markdown(corrida):
    corrida.caso("ok", "GET", "/ok", objetivo="o", rol="admin")
    md = corrida.markdown()
    assert JWT_FALSO not in md and PASSWORD not in md
    assert "***oculto***" in md                       # el token conocido que el servicio devolvio en el cuerpo
    assert "Authorization: Bearer $TOKEN_ADMIN" in md
    assert "Bearer $TOKEN_ADMIN" in md.split("Respuesta")[0]   # y en el comando que se puede copiar


def test_un_jwt_desconocido_tambien_se_oculta_por_su_forma(corrida):
    """Por ejemplo el token de operacion de auth: el motor no lo conoce de antemano, pero se reconoce."""
    ajeno = "eyJhbGciOiJIUzI1NiJ9.eyJhIjoxfQ.abcdefghij12"
    assert corrida.ocultar(f"token_operacion={ajeno}") == "token_operacion=***jwt***"
    assert corrida.ocultar("sin secretos aqui") == "sin secretos aqui"


def test_el_servidor_si_recibio_el_token_real(corrida):
    corrida.caso("ok", "GET", "/ok", objetivo="o", rol="admin")
    assert ("/ok", f"Bearer {JWT_FALSO}", None, b"") in Falso.visto


def test_la_contrasena_viaja_por_stdin_y_no_por_argumentos(corrida, monkeypatch):
    argumentos = []
    original = subprocess.run

    def espia(argv, *a, **k):
        argumentos.append(list(argv))
        return original(argv, *a, **k)
    monkeypatch.setattr(motor.subprocess, "run", espia)
    corrida.sesion("admin")
    assert argumentos and not any(PASSWORD in parte for argv in argumentos for parte in argv)
    assert any(PASSWORD.encode() in cuerpo for ruta, _, _, cuerpo in Falso.visto if ruta.endswith("/login"))


def test_la_sesion_se_reutiliza_en_toda_la_corrida(corrida):
    corrida.caso("a", "GET", "/ok", objetivo="o", rol="admin")
    corrida.caso("b", "GET", "/ok", objetivo="o", rol="admin")
    assert sum(1 for ruta, *_ in Falso.visto if ruta.endswith("/login")) == 1


def test_sin_rol_no_manda_authorization(corrida):
    corrida.caso("anonimo", "GET", "/ok", objetivo="o")
    assert Falso.visto[-1][1] is None
    assert "Authorization" not in corrida.casos[0]["cabeceras"]


# --------------------------------------------------------------------------- resultados
def test_un_caso_que_no_cumple_lo_esperado_queda_como_falla_y_se_ve(corrida):
    corrida.caso("pido 201 y llega 200", "GET", "/ok", objetivo="o", espera=201)
    c = corrida.casos[0]
    assert c["ok"] is False and c["resp"].estado == 200
    md = corrida.markdown()
    assert "**FALLA**" in md and "HTTP 201" in md


def test_las_verificaciones_se_evaluan_y_una_excepcion_cuenta_como_falla(corrida):
    corrida.caso("v", "GET", "/ok", objetivo="o", verifica=[
        ("trae id 41", lambda r: r.json["id"] == 41),
        ("trae algo inexistente", lambda r: r.json["no_existe"] == 1)])
    assert [ok for _, ok in corrida.casos[0]["verificaciones"]] == [True, True, False]
    assert corrida.casos[0]["ok"] is False


def test_guarda_encadena_un_valor_al_siguiente_caso(corrida):
    corrida.caso("crea", "GET", "/ok", objetivo="o", guarda={"nuevo_id": lambda r: r.json["id"]})
    corrida.caso("usa", "GET", "/ok?id={nuevo_id}", objetivo="o")
    assert corrida.casos[1]["ruta"] == "/ok?id=41"
    assert Falso.visto[-1][0] == "/ok?id=41"


def test_un_estado_404_es_un_caso_valido_si_se_esperaba(corrida):
    corrida.caso("no existe", "GET", "/nada", objetivo="o", espera=404,
                 verifica=[("tipo no_encontrado", lambda r: r.json["error"]["tipo"] == "no_encontrado")])
    assert corrida.casos[0]["ok"] is True


# --------------------------------------------------------------------------- cuerpos
def test_json_se_envia_compacto_y_se_muestra_en_el_comando(corrida):
    corrida.caso("json", "POST", "/echo", objetivo="o", rol="admin", json_cuerpo={"nombre": "Ñandú", "n": 1})
    ruta, auth, tipo, cuerpo = Falso.visto[-1]
    assert tipo == "application/json" and json.loads(cuerpo) == {"nombre": "Ñandú", "n": 1}
    assert '-d \'{"nombre":"Ñandú","n":1}\'' in corrida.markdown()


def test_xml_cambia_el_content_type_y_se_muestra_la_respuesta_xml(corrida):
    corrida.caso("xml", "POST", "/xml", objetivo="o", espera=201, xml="<a><b>1</b></a>", accept="application/xml")
    assert Falso.visto[-1][2] == "application/xml"
    md = corrida.markdown()
    assert "```xml" in md and "<respuesta><id>7</id></respuesta>" in md and "-H \"Accept: application/xml\"" in md


def test_una_comilla_simple_en_el_cuerpo_no_rompe_el_comando_copiable(corrida):
    corrida.caso("comilla", "POST", "/echo", objetivo="o", json_cuerpo={"t": "it's"})
    assert "it'\\''s" in corrida.markdown()


def test_un_binario_no_se_vuelca_solo_se_describe(corrida):
    corrida.caso("pdf", "GET", "/pdf", objetivo="o")
    md = corrida.markdown()
    assert "contenido binario de 509 bytes" in md and "xxxxxxxx" not in md
    assert "Content-Type: application/pdf" in md


def test_un_cuerpo_muy_largo_se_recorta_y_lo_dice(corrida):
    corrida.caso("larga", "GET", "/larga", objetivo="o")
    md = corrida.markdown()
    assert "recortado" in md and md.count("\n") < 600


def test_las_cabeceras_utiles_aparecen_con_su_nombre_canonico(corrida):
    corrida.caso("c", "GET", "/ok", objetivo="o")
    md = corrida.markdown()
    assert "X-Correlation-ID: abc123" in md and "Deprecation: true" in md and "Content-Type: application/json" in md


# --------------------------------------------------------------------------- base de datos
def test_el_efecto_en_la_base_usa_el_contexto_y_se_muestra(corrida):
    corrida.ctx["dev"] = 9
    corrida.caso("e", "GET", "/ok", objetivo="o", efecto=("la fila existe", "SELECT 1 FROM t WHERE id = {dev}"))
    _, consulta, salida = corrida.casos[0]["efectos"][0]
    assert consulta == "SELECT 1 FROM t WHERE id = 9" and salida == "resultado de: SELECT 1 FROM t WHERE id = 9"
    assert "Efecto en PostgreSQL - la fila existe" in corrida.markdown()


def test_si_la_consulta_falla_el_caso_falla_y_el_error_se_ve(puerto):
    def mala(sql):
        raise RuntimeError("tabla inexistente")
    c = motor.Corrida("s", "S", "S", puerto, puerto_auth=puerto, password=PASSWORD, ejecutar_sql=mala)
    c.caso("e", "GET", "/ok", objetivo="o", efecto=("x", "SELECT 1"))
    assert c.casos[0]["ok"] is False
    assert "ERROR: tabla inexistente" in c.markdown()


def test_la_limpieza_ejecuta_las_sentencias_con_el_contexto(puerto):
    ejecutadas = []
    c = motor.Corrida("s", "S", "S", puerto, puerto_auth=puerto, password=PASSWORD, ejecutar_sql=ejecutadas.append)
    c.ctx["id"] = 5
    c.limpieza += ["DELETE FROM a WHERE id = {id}", "DELETE FROM b"]
    c.limpiar()
    assert ejecutadas == ["DELETE FROM a WHERE id = 5", "DELETE FROM b"]
    assert "La bitacora no se toca" in c.markdown()


# --------------------------------------------------------------------------- documento
def test_ids_consecutivos_con_la_sigla_y_resumen_con_enlaces(corrida):
    for i in range(3):
        corrida.caso(f"caso {i}", "GET", "/ok", objetivo="o")
    assert [c["id"] for c in corrida.casos] == ["P4-SX-01", "P4-SX-02", "P4-SX-03"]
    md = corrida.markdown(commit="abcdef1234567")
    assert "[P4-SX-02](#p4-sx-02)" in md and "commit `abcdef1`" in md
    assert "Casos: **3**, correctos: **3**, con falla: **0**" in md


def test_la_preparacion_lista_solo_los_roles_usados_con_su_correo_de_demo(corrida):
    corrida.caso("a", "GET", "/ok", objetivo="o", rol="analista")
    md = corrida.markdown()
    assert "export TOKEN_ANALISTA=$(login josue.analista@demo.mx)" in md and "TOKEN_ADMIN" not in md
    assert "export VM_HOST=" in md and PASSWORD not in md


def test_escribir_devuelve_el_numero_de_fallas_y_crea_el_archivo(corrida, tmp_path):
    corrida.caso("ok", "GET", "/ok", objetivo="o")
    corrida.caso("mal", "GET", "/ok", objetivo="o", espera=500)
    destino = tmp_path / "salida.md"
    assert corrida.escribir(str(destino), "deadbeef") == 1
    assert destino.read_text(encoding="utf-8").startswith("# Evidencia con curl - `servicio-x`")


def test_valor_devuelve_el_primer_dato_sin_el_encabezado(puerto):
    c = motor.Corrida("s", "S", "S", puerto, puerto_auth=puerto, password=PASSWORD,
                      ejecutar_sql=lambda sql: "id\n41\n42")
    assert c.valor("SELECT id FROM t") == "41"


def test_valor_es_none_si_no_hay_filas(puerto):
    c = motor.Corrida("s", "S", "S", puerto, puerto_auth=puerto, password=PASSWORD, ejecutar_sql=lambda sql: "id")
    assert c.valor("SELECT id FROM t WHERE false") is None


def test_una_corrida_interrumpida_lo_dice_en_el_documento(corrida):
    corrida.caso("ok", "GET", "/ok", objetivo="o")
    md = corrida.markdown(interrupcion="KeyError: 'sub_id'")
    assert "CORRIDA INTERRUMPIDA** tras el caso 1" in md and "KeyError: 'sub_id'" in md
    assert "CORRIDA INTERRUMPIDA" not in corrida.markdown()


def test_valor_completa_las_variables_del_contexto_como_caso(puerto):
    """Regresion: valor() mandaba '{dev_id}' sin sustituir y PostgreSQL respondia error de sintaxis."""
    recibidas = []
    c = motor.Corrida("s", "S", "S", puerto, puerto_auth=puerto, password=PASSWORD,
                      ejecutar_sql=lambda sql: recibidas.append(sql) or "x\n7")
    c.ctx["dev_id"] = 41
    assert c.valor("SELECT estado FROM devoluciones WHERE id = {dev_id}") == "7"
    assert recibidas == ["SELECT estado FROM devoluciones WHERE id = 41"]


def test_la_cabecera_cita_el_comando_que_se_escribe_no_el_nombre_del_servicio(corrida):
    corrida.nombre_cli = "proveedores"
    corrida.caso("ok", "GET", "/ok", objetivo="o")
    md = corrida.markdown()
    assert "scripts/evidencias/ejecutar.py proveedores`" in md and "ejecutar.py servicio-x" not in md


def test_el_marcador_de_contrasena_viaja_real_pero_se_muestra_como_marcador(corrida):
    """Reconfirmar la contrasena (cierre de investigaciones): el cuerpo lleva $PASSWORD_DEMO."""
    corrida.caso("reconfirma", "POST", "/eco", objetivo="o", rol="admin",
                 json_cuerpo={"operacion": "cerrar_investigacion", "password": "$PASSWORD_DEMO"})
    enviado = json.loads(Falso.visto[-1][3])
    assert enviado["password"] == PASSWORD                      # el servicio recibio la contrasena real
    md = corrida.markdown()
    assert PASSWORD not in md
    assert '"password":"$PASSWORD_DEMO"' in md.split("Respuesta")[0]   # el lector ve el marcador en el comando


def test_un_secreto_generado_en_la_corrida_se_oculta_en_el_comando_y_en_la_respuesta(corrida):
    permiso = "permiso-opaco-que-no-parece-jwt"
    corrida.esconder(permiso)
    corrida.caso("usa permiso", "POST", "/eco", objetivo="o", rol="admin", json_cuerpo={"a": 1},
                 cabeceras_extra={"X-Autorizacion-Operacion": permiso})
    md = corrida.markdown()
    assert permiso not in md and 'X-Autorizacion-Operacion: ***oculto***' in md
