"""Reglas puras del dictamen tecnico. No decide la disposicion comercial."""

LIMITE_MINUTOS_FRIO = 30
TEMPERATURA_MAXIMA_C = 8.0


def evaluar(datos, clasificacion_temperatura):
    """Devuelve el dictamen reproducible para los cinco casos de la rubrica."""
    motivos = []
    evidencia_suficiente = bool(datos.get("evidencia_suficiente", True))
    refrigerado = clasificacion_temperatura == "refrigerado"

    if not evidencia_suficiente:
        return {
            "estado": "evidencia_insuficiente",
            "apto_para_inventario": False,
            "recomendacion": "investigar",
            "motivos": ["evidencia insuficiente para emitir un dictamen"],
        }
    if datos.get("danos"):
        motivos.append("danos fisicos visibles")
    if datos.get("empaque_alterado"):
        motivos.append("empaque o sello alterado")
    if datos.get("faltantes"):
        motivos.append("contenido incompleto")
    if datos.get("caducidad_vencida"):
        motivos.append("caducidad vencida")
    if datos.get("condicion_transporte") == "inadecuada":
        motivos.append("condiciones de transporte inadecuadas")

    if refrigerado:
        if datos.get("cadena_frio_rota"):
            motivos.append("cadena de frio rota")
        minutos = datos.get("minutos_fuera_refrigeracion")
        if minutos is not None and minutos > LIMITE_MINUTOS_FRIO:
            motivos.append("tiempo fuera de temperatura excedido")
        temperatura = datos.get("temperatura_recepcion")
        if temperatura is not None and temperatura > TEMPERATURA_MAXIMA_C:
            motivos.append("temperatura de recepcion fuera de rango")

    apto = not motivos
    return {
        "estado": "concluido",
        "apto_para_inventario": apto,
        "recomendacion": "reintegrar" if apto else "investigar",
        "motivos": motivos,
    }
