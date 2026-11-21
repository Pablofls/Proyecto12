from reglas import estado_inicial_inventario, validar_decision


def test_evidencia_insuficiente_impide_cualquier_decision():
    assert validar_decision("reciclaje", {"estado_dictamen": "evidencia_insuficiente"})


def test_no_apto_no_se_reintegra():
    assert validar_decision("reintegrar", {"estado_dictamen": "concluido",
                                            "apto_para_inventario": False})


def test_apto_admite_reintegro_pero_inicia_en_cuarentena():
    assert validar_decision("reintegrar", {"estado_dictamen": "concluido",
                                            "apto_para_inventario": True}) is None
    assert estado_inicial_inventario() == "cuarentena"


def test_destino_fuera_de_catalogo_se_rechaza():
    assert validar_decision("venta_directa", {"estado_dictamen": "concluido",
                                               "apto_para_inventario": True})
