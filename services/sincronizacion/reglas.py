"""Reglas puras de la sincronizacion offline (dominio 20 del tercer parcial).

Sin base de datos ni Flask para poder probarlas con pruebas unitarias.
"""
import hashlib
import json
import uuid
from datetime import datetime, timedelta

from shared.seguridad import (COORDINADOR, ENCARGADO_CENTRO, OPERADOR_ALMACEN,
                              RECOLECTOR)

# Operaciones que SI se pueden capturar sin conexion. Quedan en el dispositivo
# como "pendientes" y solo cuentan como confirmadas cuando el servidor responde
# estado = "aceptada".
TIPOS_OFFLINE = {
    "estado_recoleccion": {
        "roles": (RECOLECTOR, COORDINADOR),
        "descripcion": "Avance de una recoleccion en campo (en_transito, completada, fallida).",
        "campos": ["recoleccion_id", "estado_esperado", "estado", "ubicacion (opcional)"],
    },
    "recepcion": {
        "roles": (OPERADOR_ALMACEN, ENCARGADO_CENTRO),
        "descripcion": "Recepcion del producto en el centro de devoluciones.",
        "campos": ["devolucion_id", "coincide_expediente (opcional)"],
    },
    "evidencia": {
        "roles": (RECOLECTOR, OPERADOR_ALMACEN, ENCARGADO_CENTRO),
        "descripcion": "Comentario o foto de la recoleccion o de la recepcion.",
        "campos": ["devolucion_id", "comentario y/o archivo {nombre, contenido_base64, sha256}"],
    },
}

# Operaciones que NUNCA se aceptan desde una cola offline: deciden dinero,
# autorizaciones o el destino final del producto, y deben comprobar permisos y
# estado vigentes en el servidor en el momento (retroalimentacion del profesor).
SOLO_EN_LINEA = (
    "autorizar_devolucion", "programar_recoleccion", "aprobar_reembolso",
    "aprobar_disposicion", "reincorporar_inventario", "cerrar_investigacion",
)

# La etapa de la evidencia la decide el rol, no el dispositivo.
ETAPA_POR_ROL = {
    RECOLECTOR: "recoleccion",
    OPERADOR_ALMACEN: "recepcion",
    ENCARGADO_CENTRO: "recepcion",
}

# Mismas transiciones que el servicio de logistica para el trabajo de campo.
TRANSICIONES_CAMPO = {
    "asignada": ("en_transito", "fallida"),
    "en_transito": ("completada", "fallida"),
}

MAX_OPERACIONES = 50          # por envio
MAX_DIAS_OFFLINE = 7          # una captura mas vieja ya no se acepta
TOLERANCIA_RELOJ = timedelta(minutes=5)  # reloj del celular adelantado
MAX_ARCHIVO = 5 * 1024 * 1024  # 5 MB por foto (el envio completo: 16 MB)


def roles_que_sincronizan():
    roles = []
    for definicion in TIPOS_OFFLINE.values():
        for rol in definicion["roles"]:
            if rol not in roles:
                roles.append(rol)
    return tuple(roles)


def id_operacion_valido(valor):
    """UUID generado por el dispositivo; se devuelve en forma canonica."""
    try:
        return str(uuid.UUID(str(valor).strip()))
    except (ValueError, AttributeError, TypeError):
        return None


def _canonico(valor):
    # JSON manda 5 y true; XML manda "5" y "true". Para que el reintento de la
    # misma operacion produzca la misma huella sin importar el formato, todo
    # valor simple se compara como texto.
    if isinstance(valor, dict):
        return {str(k): _canonico(v) for k, v in valor.items()}
    if isinstance(valor, (list, tuple)):
        return [_canonico(v) for v in valor]
    if isinstance(valor, bool):
        return "true" if valor else "false"
    if valor is None:
        return ""
    return str(valor).strip()


def huella(operacion):
    """SHA-256 del contenido de la operacion (sin el id)."""
    contenido = {
        "tipo": operacion.get("tipo"),
        "capturado_en": operacion.get("capturado_en"),
        "datos": operacion.get("datos"),
    }
    texto = json.dumps(_canonico(contenido), sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(texto.encode("utf-8")).hexdigest()


def leer_fecha_captura(texto):
    """ISO 8601 con zona horaria; None si no se puede leer."""
    try:
        fecha = datetime.fromisoformat(str(texto).strip().replace("Z", "+00:00"))
    except ValueError:
        return None
    if fecha.tzinfo is None:
        return None
    return fecha


def problema_de_captura(capturado, ahora):
    """Texto del problema con la fecha de captura, o None si es aceptable."""
    if capturado is None:
        return "capturado_en debe ser fecha ISO 8601 con zona horaria."
    if capturado > ahora + TOLERANCIA_RELOJ:
        return "capturado_en esta en el futuro: revisa el reloj del dispositivo."
    if capturado < ahora - timedelta(days=MAX_DIAS_OFFLINE):
        return f"La captura tiene mas de {MAX_DIAS_OFFLINE} dias sin sincronizar."
    return None


def transicion_permitida(actual, nuevo):
    return nuevo in TRANSICIONES_CAMPO.get(actual, ())


def ubicacion_valida(ubicacion):
    """GPS opcional: {"latitud": .., "longitud": ..}. Devuelve floats o None."""
    if ubicacion in (None, "", {}):
        return None
    if not isinstance(ubicacion, dict):
        raise ValueError("ubicacion debe tener latitud y longitud.")
    try:
        lat = float(ubicacion.get("latitud"))
        lon = float(ubicacion.get("longitud"))
    except (TypeError, ValueError):
        raise ValueError("latitud y longitud deben ser numeros.")
    if not (-90 <= lat <= 90 and -180 <= lon <= 180):
        raise ValueError("latitud o longitud fuera de rango.")
    return {"latitud": lat, "longitud": lon}


def estado_por_codigo(codigo):
    """Como queda guardada una operacion que el servidor no aplico.

    409 = el servidor cambio mientras el dispositivo estaba sin red: es un
    conflicto y el usuario decide que hacer. Lo demas (datos malos, sin permiso,
    registro inexistente) es un rechazo.
    """
    return "conflicto" if codigo == 409 else "rechazada"
