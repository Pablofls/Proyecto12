"""Reglas puras de disposicion e inventario recuperado."""

DESTINOS = {
    "reintegrar", "reparacion", "reacondicionamiento",
    "devolucion_proveedor", "reciclaje", "desecho", "donacion",
}


def validar_decision(destino, inspeccion):
    if destino not in DESTINOS:
        return "Destino no permitido."
    if inspeccion.get("estado_dictamen") == "evidencia_insuficiente":
        return "No puede decidirse la disposicion con evidencia insuficiente."
    if destino == "reintegrar" and not inspeccion.get("apto_para_inventario"):
        return "El dictamen tecnico impide reintegrar el producto."
    return None


def estado_inicial_inventario():
    return "cuarentena"
