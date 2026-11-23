from reglas import evaluar


def test_producto_danado_no_es_recuperable():
    assert not evaluar({"danos": True}, "no_refrigerado")["apto_para_inventario"]


def test_empaque_alterado_no_es_recuperable():
    assert "empaque o sello alterado" in evaluar(
        {"empaque_alterado": True}, "no_refrigerado")["motivos"]


def test_cadena_frio_fuera_de_tiempo():
    resultado = evaluar({"minutos_fuera_refrigeracion": 31,
                         "temperatura_recepcion": 9}, "refrigerado")
    assert not resultado["apto_para_inventario"]
    assert len(resultado["motivos"]) == 2


def test_evidencia_insuficiente_bloquea_dictamen():
    resultado = evaluar({"evidencia_suficiente": False}, "no_refrigerado")
    assert resultado["estado"] == "evidencia_insuficiente"
    assert resultado["recomendacion"] == "investigar"


def test_producto_recuperable_solo_recomienda_reintegrar():
    resultado = evaluar({"evidencia_suficiente": True}, "no_refrigerado")
    assert resultado["apto_para_inventario"]
    assert resultado["recomendacion"] == "reintegrar"
