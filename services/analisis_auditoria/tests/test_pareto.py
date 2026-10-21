"""Pruebas puras del formato Pareto y del pipeline enviado a MongoDB."""
import app


class ColeccionFalsa:
    def __init__(self, filas):
        self.filas=filas
        self.pipeline=None
    def aggregate(self, pipeline):
        self.pipeline=pipeline
        return self.filas


def test_pareto_motivo_frecuencia():
    c=ColeccionFalsa([{"_id":"Empaque roto","total":3,"casos":3},
                      {"_id":"Caducidad","total":1,"casos":1}])
    datos=app.calcular_pareto(c,"motivo","frecuencia")
    assert datos["total_general"]==4
    assert datos["categorias"][0]["porcentaje"]==75
    assert datos["categorias"][-1]["porcentaje_acumulado"]==100
    assert c.pipeline[0]["$match"]["vigente"] is True
    assert "$group" in c.pipeline[1]


def test_pareto_vacio_sin_division_por_cero():
    datos=app.calcular_pareto(ColeccionFalsa([]),"producto","costo")
    assert datos["total_general"]==0
    assert datos["categorias"]==[]


def test_clasificacion_explica_coincidencias():
    resultado=app.clasificar_descripcion("El producto llego caliente y descongelado")
    assert resultado[0]["motivo"]=="Cadena de frio rota"
    assert resultado[0]["puntaje"]>=2


def test_clasificacion_desconocida_no_inventa():
    assert app.clasificar_descripcion("situacion sin palabras conocidas")==[]

