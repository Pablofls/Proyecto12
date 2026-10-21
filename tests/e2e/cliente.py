"""Utilidades de la suite E2E: HTTP real, SQL, MongoDB y Redis.

No hay dobles: cada llamada sale por la red del compose hacia los contenedores.
Todo se configura con variables de entorno (mismos nombres que docker-compose).

Trazabilidad: RNF-28, RNF-16 (los logs nunca llevan tokens ni contrasenas),
RNF-23 (X-Correlation-ID).
"""
import json
import os
import re
import uuid
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET
from collections import namedtuple

import psycopg2
import psycopg2.extras

# Nombre de variable -> URL por defecto dentro de la red del compose.
SERVICIOS = {
    "auth": ("AUTH_URL", "http://auth:8000"),
    "devoluciones": ("DEVOLUCIONES_URL", "http://devoluciones:8000"),
    "logistica": ("LOGISTICA_URL", "http://logistica:8000"),
    "inspecciones": ("INSPECCIONES_URL", "http://inspecciones:8000"),
    "reembolsos": ("REEMBOLSOS_URL", "http://reembolsos-costos:8000"),
    "ventas": ("VENTAS_URL", "http://ventas-catalogos:8000"),
    "evidencias": ("EVIDENCIAS_URL", "http://evidencias:8000"),
    "analisis": ("ANALISIS_URL", "http://analisis-auditoria:8000"),
}

PREFIJO_API = {
    "auth": "/api/v1/auth",
    "devoluciones": "/api/v1/devoluciones",
    "logistica": "/api/v1/logistica",
    "inspecciones": "/api/v1/inspecciones",
    "reembolsos": "/api/v1/reembolsos-costos",
    "ventas": "/api/v1/ventas",
    "evidencias": "/api/v1/evidencias",
    "analisis": "/api/v1/analisis",
}

CLIENTE = "Cliente"
INSPECTOR = "Inspector"
ENCARGADO_CENTRO = "Encargado del Centro de Devoluciones"
COORDINADOR = "Coordinador de Logistica"
ANALISTA = "Analista de Devoluciones"
ENCARGADO_REEMBOLSOS = "Encargado de Reembolsos"
ADMINISTRADOR = "Administrador"

# Campos que jamas se imprimen (RNF-16).
_SECRETOS = {"password", "access_token", "refresh_token", "token"}

Respuesta = namedtuple("Respuesta", "status headers texto datos")


def url_base(servicio):
    variable, defecto = SERVICIOS[servicio]
    return os.environ.get(variable, defecto).rstrip("/")


def _recortar(valor, limite=300):
    texto = valor if isinstance(valor, str) else json.dumps(valor, default=str)
    return texto if len(texto) <= limite else texto[:limite] + "...(recortado)"


def _sin_secretos(valor):
    if isinstance(valor, dict):
        return {k: ("***" if k in _SECRETOS else _sin_secretos(v))
                for k, v in valor.items()}
    if isinstance(valor, list):
        return [_sin_secretos(v) for v in valor]
    return valor


def _decodificar(texto, tipo):
    if "json" in tipo:
        try:
            return json.loads(texto)
        except ValueError:
            return None
    if "xml" in tipo:
        try:
            return ET.fromstring(texto)
        except ET.ParseError:
            return None
    return None


def llamar(servicio, metodo, ruta, cuerpo=None, token=None, xml=None,
           accept="application/json", cabeceras=None, correlation_id=None,
           multipart=None, absoluta=False):
    """Peticion HTTP real. Devuelve Respuesta(status, headers, texto, datos).

    - cuerpo: dict que se envia como JSON (o `xml` ya serializado como XML).
    - multipart: (campo, nombre_archivo, contenido_bytes, campos_extra_dict).
    - Nunca lanza por un 4xx/5xx: las pruebas comparan el codigo.
    - Imprime metodo, URL, codigo y cuerpo recortado SIN secretos (evidencia).
    """
    url = ruta if absoluta else url_base(servicio) + ruta
    encabezados = {"Accept": accept}
    datos = None
    if multipart:
        campo, nombre, contenido, extra = multipart
        frontera = "e2e" + uuid.uuid4().hex
        partes = []
        for k, v in (extra or {}).items():
            partes.append(f'--{frontera}\r\nContent-Disposition: form-data; '
                          f'name="{k}"\r\n\r\n{v}\r\n'.encode())
        partes.append(f'--{frontera}\r\nContent-Disposition: form-data; '
                      f'name="{campo}"; filename="{nombre}"\r\n'
                      'Content-Type: application/octet-stream\r\n\r\n'.encode()
                      + contenido + b"\r\n")
        partes.append(f"--{frontera}--\r\n".encode())
        datos = b"".join(partes)
        encabezados["Content-Type"] = f"multipart/form-data; boundary={frontera}"
    elif xml is not None:
        datos = xml.encode() if isinstance(xml, str) else xml
        encabezados["Content-Type"] = "application/xml"
    elif cuerpo is not None:
        datos = json.dumps(cuerpo).encode()
        encabezados["Content-Type"] = "application/json"
    if token:
        encabezados["Authorization"] = f"Bearer {token}"
    if correlation_id:
        encabezados["X-Correlation-ID"] = correlation_id
    encabezados.update(cabeceras or {})

    peticion = urllib.request.Request(url, data=datos, method=metodo,
                                      headers=encabezados)
    try:
        with urllib.request.urlopen(peticion, timeout=20) as resp:
            status, cabs, crudo = resp.status, resp.headers, resp.read()
    except urllib.error.HTTPError as exc:
        status, cabs, crudo = exc.code, exc.headers, exc.read()

    tipo = (cabs.get("Content-Type") or "").lower()
    texto = crudo.decode("utf-8", "replace") if "octet" not in tipo and \
        "image" not in tipo and "pdf" not in tipo else f"<{len(crudo)} bytes>"
    parseado = _decodificar(texto, tipo)
    if isinstance(parseado, (dict, list)):
        mostrado = _sin_secretos(parseado)
    else:  # XML o texto: se tachan los mismos campos por patron
        mostrado = re.sub(r"<(%s)>[^<]*</\1>" % "|".join(_SECRETOS), r"<\1>***</\1>", texto)
    print(f"[E2E] {metodo} {ruta.split('?')[0] if absoluta else ruta} "
          f"-> {status} {_recortar(mostrado)}")
    return Respuesta(status, cabs, texto, parseado)


def error_tipo(resp):
    """Valor `error.tipo` de una respuesta de error en JSON."""
    return ((resp.datos or {}).get("error") or {}).get("tipo")


# --------------------------------------------------------------------------- #
# Bases de datos (solo desde la red del compose; nunca en la laptop)
# --------------------------------------------------------------------------- #
def sql(sentencia, params=(), uno=False):
    conn = psycopg2.connect(
        host=os.environ.get("POSTGRES_HOST", "postgres"),
        port=os.environ.get("POSTGRES_PORT", "5432"),
        dbname=os.environ.get("POSTGRES_DB", "devoluciones"),
        user=os.environ.get("POSTGRES_USER", "devoluciones_app"),
        password=os.environ.get("POSTGRES_PASSWORD", ""),
        cursor_factory=psycopg2.extras.RealDictCursor)
    try:
        with conn, conn.cursor() as cur:
            cur.execute(sentencia, params)
            if cur.description is None:
                return None
            return cur.fetchone() if uno else cur.fetchall()
    finally:
        conn.close()


def mongo_db():
    from shared import mongo
    return mongo.get_mongo()


def redis_cli():
    from shared.infra import get_redis
    return get_redis()


def liberar_limite_login():
    """Borra los contadores de rate limit de login para que repetir la suite
    no choque con el limite por minuto (RNF-13). Solo claves de prueba."""
    r = redis_cli()
    for clave in r.scan_iter("devoluciones:limite:*:login"):
        r.delete(clave)


def email_de_rol(rol, excluir=()):
    """Correo de un usuario activo del rol, tomado de la base (seed_demo)."""
    fila = sql("""SELECT u.email FROM usuarios u JOIN roles r ON r.id = u.rol_id
                   WHERE r.nombre = %s AND u.estado = 'activo'
                     AND u.eliminado_en IS NULL AND u.email <> ALL(%s)
                   ORDER BY u.id LIMIT 1""", (rol, list(excluir)), uno=True)
    return fila["email"] if fila else None


def iniciar_sesion(email):
    """Login real contra auth. La contrasena viene de PASSWORD_DEMO (.env)."""
    resp = llamar("auth", "POST", PREFIJO_API["auth"] + "/login",
                  {"email": email, "password": os.environ["PASSWORD_DEMO"]})
    assert resp.status == 200, f"login de {email}: {resp.status}"
    return resp.datos["access_token"]


def cerrar_sesion(token):
    llamar("auth", "POST", PREFIJO_API["auth"] + "/logout", token=token)


# --------------------------------------------------------------------------- #
# Limpieza de lo creado por la suite
# --------------------------------------------------------------------------- #
def borrar_devoluciones(ids):
    """Borra, de hijos a padre, todo lo que cuelga de las devoluciones de la
    suite. Es mejor esfuerzo: si el rol de la app no puede borrar alguna tabla
    se avisa y se sigue (la bitacora se conserva a proposito, RN-12)."""
    if not ids:
        return
    ids = tuple(ids)
    pasos = [
        "DELETE FROM notificaciones WHERE devolucion_id IN %s",
        "DELETE FROM evidencias WHERE devolucion_id IN %s",
        "DELETE FROM inventario_recuperado WHERE disposicion_id IN "
        "(SELECT id FROM disposiciones WHERE devolucion_id IN %s)",
        "DELETE FROM disposiciones WHERE devolucion_id IN %s",
        "DELETE FROM inspecciones_ref WHERE devolucion_id IN %s",
        "DELETE FROM recepciones WHERE devolucion_id IN %s",
        "DELETE FROM recolecciones WHERE devolucion_id IN %s",
        "DELETE FROM costos WHERE devolucion_id IN %s",
        "DELETE FROM reembolsos WHERE devolucion_id IN %s",
        "DELETE FROM devoluciones WHERE id IN %s",
    ]
    for paso in pasos:
        try:
            sql(paso, (ids,))
        except Exception as exc:  # noqa: BLE001 - limpieza, no prueba
            print(f"[E2E][limpieza] no se pudo: {paso.split(' WHERE')[0]} "
                  f"({type(exc).__name__})")
    lista = list(ids)
    try:
        db = mongo_db()
        db.eventos.delete_many({"datos.devolucion_id": {"$in": lista}})
        db.inspecciones.delete_many({"devolucion_id": {"$in": lista}})
        db.evidencias_metadatos.delete_many({"devolucion_id": {"$in": lista}})
        db.resultados_analisis.delete_many(
            {"tipo_analisis": "snapshot_devolucion",
             "devolucion_id": {"$in": lista}})
    except Exception as exc:  # noqa: BLE001
        print(f"[E2E][limpieza] MongoDB no se pudo limpiar ({type(exc).__name__})")
