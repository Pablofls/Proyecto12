"""Ejecutar dentro del contenedor: python -m pytest -v tests/"""
import pytest
from shared.respuestas import ErrorApi
from app import CATALOGOS, validar_datos


def test_catalogos_coinciden_con_monolito():
    assert set(CATALOGOS) == {"proveedores","productos","lotes","tiendas",
                              "rutas","transportistas","motivos"}


def test_producto_valido():
    datos=validar_datos("productos",{"sku":"AAA","nombre":"Pescado",
         "clasificacion_temperatura":"refrigerado","proveedor_id":"2"})
    assert datos["proveedor_id"]==2
    assert datos["clasificacion_temperatura"]=="refrigerado"


@pytest.mark.parametrize("datos",[
    {"sku":"A","nombre":"Pescado","clasificacion_temperatura":"templado","proveedor_id":1},
    {"sku":"A","nombre":"Pescado","clasificacion_temperatura":"refrigerado","proveedor_id":0},
    {"sku":"A","nombre":"Pescado","clasificacion_temperatura":"refrigerado","proveedor_id":True},
    {"sku":"A","nombre":"Pescado","clasificacion_temperatura":"refrigerado","proveedor_id":1,"activo":False},
])
def test_producto_invalido(datos):
    with pytest.raises(ErrorApi) as err:
        validar_datos("productos",datos)
    assert err.value.codigo==400


def test_lote_fecha_valida():
    datos=validar_datos("lotes",{"producto_id":1,"proveedor_id":1,
         "numero_lote":"L-001","fecha_caducidad":"2027-01-01"})
    assert datos["fecha_caducidad"]=="2027-01-01"


def test_lote_fecha_invalida():
    with pytest.raises(ErrorApi):
        validar_datos("lotes",{"producto_id":1,"proveedor_id":1,
          "numero_lote":"L-001","fecha_caducidad":"2026-02-30"})

