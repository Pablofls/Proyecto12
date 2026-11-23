"""Cliente HTTP del sistema web para los microservicios.

Los JWT permanecen en la sesion server-side de Flask (Redis), nunca en
localStorage ni en una cookie legible por JavaScript. Cada llamada propaga el
correlation id y renueva una sola vez el access token cuando expira.
"""
import json
import urllib.error
import urllib.parse
import urllib.request

from flask import current_app, session


class ErrorServicio(Exception):
    def __init__(self, codigo, mensaje, tipo="error_servicio", detalles=None,
                 correlation_id=None):
        super().__init__(mensaje)
        self.codigo = codigo
        self.mensaje = mensaje
        self.tipo = tipo
        self.detalles = detalles
        self.correlation_id = correlation_id


def habilitados():
    return bool(current_app.config.get("USE_MICROSERVICES"))


def _url(servicio, ruta, parametros=None):
    base = current_app.config["SERVICE_URLS"][servicio].rstrip("/")
    url = base + "/" + ruta.lstrip("/")
    if parametros:
        valores = {k: v for k, v in parametros.items() if v not in (None, "")}
        if valores:
            url += "?" + urllib.parse.urlencode(valores, doseq=True)
    return url


def _leer_error(exc):
    try:
        cuerpo = json.loads(exc.read().decode("utf-8"))
        error = cuerpo.get("error", cuerpo)
    except (ValueError, UnicodeDecodeError):
        error = {}
    return ErrorServicio(
        exc.code,
        error.get("mensaje") or f"El servicio respondio HTTP {exc.code}.",
        error.get("tipo", "error_http"),
        error.get("detalles"),
        error.get("correlation_id"),
    )


def _refrescar():
    refresh = session.get("refresh_token")
    if not refresh:
        return False
    try:
        datos = solicitar(
            "auth", "POST", "/api/v1/auth/refresh",
            datos={"refresh_token": refresh}, autenticado=False,
            reintentar=False,
        )
    except ErrorServicio:
        session.clear()
        return False
    session["access_token"] = datos["access_token"]
    session.modified = True
    return True


def solicitar(servicio, metodo, ruta, *, datos=None, parametros=None,
              autenticado=True, reintentar=True, encabezados_extra=None):
    """Ejecuta una llamada JSON y devuelve el cuerpo decodificado."""
    from app.security import correlation_id, ip_cliente

    cuerpo = None
    encabezados = {
        "Accept": "application/json",
        "X-Correlation-ID": correlation_id(),
        # Sin esto los servicios ven la IP del contenedor `app` para todos los
        # usuarios: el limite de login por IP (RNF-13) contaria a toda la web como
        # uno solo y intentos_acceso guardaria siempre la misma IP.
        "X-Forwarded-For": ip_cliente(),
    }
    if datos is not None:
        cuerpo = json.dumps(datos).encode("utf-8")
        encabezados["Content-Type"] = "application/json"
    if autenticado:
        token = session.get("access_token")
        if not token:
            raise ErrorServicio(401, "La sesion distribuida no tiene un token vigente.",
                                "token_ausente")
        encabezados["Authorization"] = f"Bearer {token}"
    encabezados.update(encabezados_extra or {})

    peticion = urllib.request.Request(
        _url(servicio, ruta, parametros), data=cuerpo,
        headers=encabezados, method=metodo.upper(),
    )
    try:
        with urllib.request.urlopen(
            peticion, timeout=current_app.config["MICROSERVICE_TIMEOUT"]
        ) as respuesta:
            contenido = respuesta.read()
            return json.loads(contenido.decode("utf-8")) if contenido else {}
    except urllib.error.HTTPError as exc:
        if autenticado and exc.code == 401 and reintentar and _refrescar():
            return solicitar(
                servicio, metodo, ruta, datos=datos, parametros=parametros,
                autenticado=True, reintentar=False,
                encabezados_extra=encabezados_extra,
            )
        raise _leer_error(exc) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ErrorServicio(
            503,
            f"El microservicio {servicio} no esta disponible temporalmente.",
            "servicio_no_disponible",
        ) from exc


def descargar(servicio, ruta, *, reintentar=True):
    """Descarga un archivo binario con el JWT de la sesion.

    Devuelve (bytes, content_type). Sirve para que el navegador vea las fotos
    de evidencia sin tener nunca el token ni la URL interna del servicio (RNF-15).
    """
    from app.security import correlation_id

    token = session.get("access_token")
    if not token:
        raise ErrorServicio(401, "La sesion distribuida no tiene un token vigente.",
                            "token_ausente")
    peticion = urllib.request.Request(
        _url(servicio, ruta),
        headers={"Authorization": f"Bearer {token}",
                 "X-Correlation-ID": correlation_id()},
        method="GET",
    )
    try:
        with urllib.request.urlopen(
            peticion, timeout=current_app.config["MICROSERVICE_TIMEOUT"]
        ) as respuesta:
            return respuesta.read(), respuesta.headers.get_content_type()
    except urllib.error.HTTPError as exc:
        if exc.code == 401 and reintentar and _refrescar():
            return descargar(servicio, ruta, reintentar=False)
        raise _leer_error(exc) from exc
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        raise ErrorServicio(
            503,
            f"El microservicio {servicio} no esta disponible temporalmente.",
            "servicio_no_disponible",
        ) from exc
