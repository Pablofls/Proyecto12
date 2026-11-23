"""Seguridad de la API sin base de datos: todo exige JWT (RNF-09, RN-13)."""
import pytest

from app import create_app


@pytest.fixture(scope="module")
def cliente():
    return create_app().test_client()


RUTAS = [
    "/api/v1/reportes", "/api/v1/reportes/devoluciones", "/api/v1/reportes/costos",
    "/api/v1/reportes/tasas", "/api/v1/reportes/pareto", "/api/v1/reportes/tendencia",
    "/api/v1/graficas/pareto", "/api/v1/graficas/tendencia", "/api/v1/graficas/tasas",
    "/api/v1/analitica/tendencias", "/api/v1/analitica/pronosticos", "/api/v1/analitica/anomalias",
    "/api/v1/analitica/alertas-fraude",
]


@pytest.mark.parametrize("ruta", RUTAS)
def test_sin_token_401(cliente, ruta):
    assert cliente.get(ruta).status_code == 401


def test_las_rutas_del_servicio_son_exactamente_las_probadas(cliente):
    """Si alguien agrega un endpoint sin protegerlo, esta prueba lo senala."""
    reales = {str(r) for r in cliente.application.url_map.iter_rules() if str(r).startswith("/api/")}
    esperadas = {"/api/v1/reportes", "/api/v1/reportes/<nombre>", "/api/v1/graficas/<nombre>",
                 "/api/v1/analitica/tendencias", "/api/v1/analitica/pronosticos",
                 "/api/v1/analitica/anomalias", "/api/v1/analitica/factores",
                     "/api/v1/analitica/alertas-fraude"}
    assert reales == esperadas
