"""Validacion de entradas del servicio de devoluciones.

Funciones puras (sin base de datos) para poder probarlas de forma unitaria.
Las reglas que dependen de datos guardados (dueno de la venta, cantidad
disponible, estado actual) viven en app.py.

Trazabilidad: RF-07, RF-10, RN-01.
"""
# Estados del expediente: mismos valores que el CHECK de devoluciones.estado.
ESTADOS = ("solicitada", "en_revision", "autorizada", "rechazada",
           "en_recoleccion", "recibida", "en_inspeccion", "resuelta", "cerrada")
# Estados desde los que el analista todavia puede resolver (RF-10).
ESTADOS_REVISABLES = ("solicitada", "en_revision")
DECISIONES = ("autorizar", "rechazar", "informacion")

MIN_DESCRIPCION = 10
MAX_DESCRIPCION = 2000
MAX_JUSTIFICACION = 500


def _entero_positivo(datos, campo, errores, obligatorio=True, defecto=None):
    valor = datos.get(campo)
    if valor in (None, ""):
        if obligatorio:
            errores.append({"campo": campo, "problema": "es obligatorio"})
        return defecto
    # bool es subclase de int en Python: true no debe valer 1.
    if isinstance(valor, bool):
        valor = None
    try:
        numero = int(str(valor).strip())
    except (TypeError, ValueError):
        numero = None
    if numero is None or numero < 1:
        errores.append({"campo": campo, "problema": "debe ser un entero mayor que 0"})
        return defecto
    return numero


def _descripcion(datos, errores):
    texto = str(datos.get("descripcion_problema") or "").strip()
    if len(texto) < MIN_DESCRIPCION:
        errores.append({"campo": "descripcion_problema",
                        "problema": f"minimo {MIN_DESCRIPCION} caracteres"})
    elif len(texto) > MAX_DESCRIPCION:
        errores.append({"campo": "descripcion_problema",
                        "problema": f"maximo {MAX_DESCRIPCION} caracteres"})
    return texto


def validar_nueva(datos):
    """Cuerpo de POST /devoluciones. Devuelve (valores, errores)."""
    errores = []
    valores = {
        "venta_detalle_id": _entero_positivo(datos, "venta_detalle_id", errores),
        "motivo_id": _entero_positivo(datos, "motivo_id", errores),
        "descripcion_problema": _descripcion(datos, errores),
        "cantidad_devuelta": _entero_positivo(datos, "cantidad_devuelta", errores,
                                              obligatorio=False, defecto=1),
    }
    return valores, errores


def validar_edicion(datos):
    """Cuerpo de PUT /devoluciones/{id}: reemplaza los datos editables, por eso
    todos son obligatorios."""
    errores = []
    valores = {
        "motivo_id": _entero_positivo(datos, "motivo_id", errores),
        "descripcion_problema": _descripcion(datos, errores),
        "cantidad_devuelta": _entero_positivo(datos, "cantidad_devuelta", errores),
    }
    return valores, errores


def validar_resolucion(datos):
    """Cuerpo de PATCH /devoluciones/{id}/resolucion (RF-10)."""
    errores = []
    decision = str(datos.get("decision") or "").strip().lower()
    justificacion = str(datos.get("justificacion") or "").strip()
    if decision not in DECISIONES:
        errores.append({"campo": "decision",
                        "problema": "debe ser autorizar, rechazar o informacion"})
    # Rechazar sin explicar deja al cliente sin saber que corregir (RN-12).
    if decision == "rechazar" and not justificacion:
        errores.append({"campo": "justificacion",
                        "problema": "es obligatoria para rechazar"})
    if len(justificacion) > MAX_JUSTIFICACION:
        errores.append({"campo": "justificacion",
                        "problema": f"maximo {MAX_JUSTIFICACION} caracteres"})
    return {"decision": decision, "justificacion": justificacion}, errores


def validar_estado(texto):
    """Filtro ?estado= del listado. Vacio significa sin filtro."""
    estado = (texto or "").strip()
    if estado and estado not in ESTADOS:
        return None, [{"campo": "estado",
                       "problema": "valor desconocido; validos: " + ", ".join(ESTADOS)}]
    return estado, []
