"""Notificaciones internas por rol (RF-29, UC-25, RN-13).

Una sola funcion, notificar_evento, decide a quien avisar en cada paso del
flujo de una devolucion. Los blueprints la llaman en la misma peticion que
cambia el estado, asi que la notificacion y el cambio se confirman o se
revierten juntos (db.cerrar_conn hace un unico commit).

Los tipos y textos de autorizacion, rechazo, solicitud_informacion y
reembolso_* son los mismos que inserta el microservicio de devoluciones y el
de reembolsos, para que la bandeja se vea igual con o sin API distribuida.

Trazabilidad: RF-29, UC-25, RN-13, RN-12
"""
from flask import url_for

from app.db import consultar, ejecutar
from app.security import (
    ANALISTA, COORDINADOR, ENCARGADO_CENTRO, ENCARGADO_REEMBOLSOS,
    INSPECTOR, registrar_bitacora, usuario_actual,
)

# Marca para "el cliente dueno de la devolucion", que no es un rol fijo.
CLIENTE_DEL_CASO = "__cliente_del_caso__"

# evento -> lista de avisos (destinatario, tipo, mensaje, endpoint destino).
# Los endpoints reciben devolucion_id; el texto usa {folio} y datos del evento.
EVENTOS = {
    "solicitud_nueva": [
        (ANALISTA, "solicitud_nueva",
         "Nueva solicitud {folio} pendiente de revision", "devoluciones.detalle"),
    ],
    "evidencia_nueva": [
        (ANALISTA, "evidencia_nueva",
         "Nueva evidencia en {folio}", "devoluciones.detalle"),
    ],
    "autorizacion": [
        (CLIENTE_DEL_CASO, "autorizacion",
         "Tu devolucion {folio} fue autorizada. Pronto programaremos la recoleccion.",
         "devoluciones.detalle"),
        (COORDINADOR, "autorizacion_logistica",
         "Autorizada {folio}: programa la recoleccion", "logistica.programar"),
    ],
    "rechazo": [
        (CLIENTE_DEL_CASO, "rechazo",
         "Tu devolucion {folio} fue rechazada: {nota}", "devoluciones.detalle"),
    ],
    "solicitud_informacion": [
        (CLIENTE_DEL_CASO, "solicitud_informacion",
         "Necesitamos mas informacion sobre tu devolucion {folio}. {nota}",
         "devoluciones.detalle"),
    ],
    "recoleccion_programada": [
        (CLIENTE_DEL_CASO, "recoleccion_programada",
         "Recoleccion de {folio} programada para {fecha} en {lugar}",
         "devoluciones.detalle"),
    ],
    "recoleccion_en_transito": [
        (CLIENTE_DEL_CASO, "recoleccion_en_transito",
         "Tu producto de {folio} va en camino", "devoluciones.detalle"),
        (ENCARGADO_CENTRO, "recoleccion_en_transito",
         "Producto de {folio} en camino al centro", "devoluciones.detalle"),
    ],
    "recoleccion_completada": [
        (CLIENTE_DEL_CASO, "recoleccion_completada",
         "La recoleccion de {folio} se completo", "devoluciones.detalle"),
        (ENCARGADO_CENTRO, "recoleccion_completada",
         "Recoleccion completada de {folio}: confirma la recepcion", "devoluciones.detalle"),
    ],
    "recepcion_confirmada": [
        (INSPECTOR, "recepcion_confirmada",
         "Recibido {folio}: pendiente de inspeccion", "inspecciones.registrar"),
        (CLIENTE_DEL_CASO, "recepcion_confirmada",
         "Recibimos tu producto de {folio}; sigue la inspeccion", "devoluciones.detalle"),
    ],
    "inspeccion_registrada": [
        (ANALISTA, "inspeccion_registrada",
         "Inspeccion lista en {folio}: define el destino", "inspecciones.disposicion"),
    ],
    "disposicion_definida": [
        (ENCARGADO_REEMBOLSOS, "disposicion_definida",
         "Disposicion definida en {folio}: evalua el reembolso", "reembolsos.registrar"),
    ],
    "disposicion_inventario": [
        (ENCARGADO_CENTRO, "disposicion_inventario",
         "{folio} regresa a inventario: genera la etiqueta", "inspecciones.inventario"),
    ],
    "reembolso_aprobado": [
        (CLIENTE_DEL_CASO, "reembolso_aprobado",
         "El reembolso de {folio} fue aprobado.", "devoluciones.detalle"),
        (ANALISTA, "reembolso_aprobado",
         "Reembolso aprobado en {folio} por ${monto}", "devoluciones.detalle"),
    ],
    "reembolso_rechazado": [
        (CLIENTE_DEL_CASO, "reembolso_rechazado",
         "El reembolso de {folio} fue rechazado.", "devoluciones.detalle"),
        (ANALISTA, "reembolso_rechazado",
         "Reembolso rechazado en {folio}", "devoluciones.detalle"),
    ],
    "caso_cerrado": [
        (CLIENTE_DEL_CASO, "caso_cerrado",
         "Tu devolucion {folio} fue cerrada", "devoluciones.detalle"),
    ],
}

# Endpoints que no reciben devolucion_id como parametro.
_ENDPOINTS_SIN_ID = {"inspecciones.inventario"}


def _usuarios_del_rol(rol):
    return consultar(
        """
        SELECT u.id
          FROM usuarios u JOIN roles r ON r.id = u.rol_id
         WHERE r.nombre = %s AND u.estado = 'activo' AND u.eliminado_en IS NULL
        """,
        (rol,),
    )


def _ruta(endpoint, devolucion_id):
    if endpoint in _ENDPOINTS_SIN_ID:
        return url_for(endpoint)
    return url_for(endpoint, devolucion_id=devolucion_id)


def notificar_usuario(usuario_id, devolucion_id, tipo, mensaje, url=None):
    """Inserta una notificacion para un usuario. El mensaje nunca lleva datos
    sensibles (RNF-16): solo folios y textos de estado."""
    ejecutar(
        """
        INSERT INTO notificaciones (usuario_id, devolucion_id, tipo, mensaje, url)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (usuario_id, devolucion_id, tipo, mensaje[:500], url),
    )


def notificar_evento(evento, expediente, omitir_cliente=False, **datos):
    """Avisa a quien debe actuar despues de `evento`.

    `expediente` necesita id, folio_devolucion y cliente_id. Con
    omitir_cliente=True se salta al cliente del caso (lo usa la rama con API
    distribuida, donde el microservicio ya lo notifico). Quien ejecuta la
    accion no se notifica a si mismo. Si un rol no tiene usuarios activos se
    omite y queda en bitacora, sin romper el flujo.
    """
    actor = usuario_actual()
    actor_id = actor["id"] if actor else None
    devolucion_id = expediente["id"]
    textos = {"folio": expediente["folio_devolucion"], "nota": "", "fecha": "",
              "lugar": "", "monto": ""}
    textos.update({k: ("" if v is None else v) for k, v in datos.items()})

    enviados = 0
    for destinatario, tipo, plantilla, endpoint in EVENTOS[evento]:
        if destinatario == CLIENTE_DEL_CASO:
            if omitir_cliente:
                continue
            ids = [expediente["cliente_id"]]
        else:
            ids = [fila["id"] for fila in _usuarios_del_rol(destinatario)]
            if not ids:
                registrar_bitacora(
                    "notificacion_omitida", "devoluciones", devolucion_id,
                    f"Sin usuarios activos con el rol '{destinatario}' para el evento {evento}",
                )
                continue
        mensaje = plantilla.format(**textos).strip()
        ruta = _ruta(endpoint, devolucion_id)
        for usuario_id in ids:
            if usuario_id == actor_id:
                continue
            notificar_usuario(usuario_id, devolucion_id, tipo, mensaje, ruta)
            enviados += 1
    return enviados

