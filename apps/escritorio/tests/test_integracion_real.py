"""Pruebas de lectura de la app real contra servicios locales, siempre en XML."""
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parents[1]))
from cliente_xml import ClienteXml

pytestmark = pytest.mark.skipif(
    os.environ.get("INTEGRACION_ESCRITORIO") != "1",
    reason="Activa INTEGRACION_ESCRITORIO=1 con Docker Compose levantado",
)

PASSWORD = os.environ.get("PASSWORD_DEMO", "DemoRoberto2026!")


@pytest.mark.parametrize("correo,servicio,ruta", [
    ("valentina.inspector@demo.mx", "inspecciones", "/api/v1/inspecciones/pendientes"),
    ("josue.analista@demo.mx", "disposicion", "/api/v1/disposicion-inventario/pendientes"),
    ("roberto.centro@demo.mx", "disposicion", "/api/v1/disposicion-inventario/inventario"),
    ("carla.reembolsos@demo.mx", "reembolsos", "/api/v1/reembolsos-costos/reembolsos"),
    ("pablo.admin@demo.mx", "analisis", "/api/v1/auditoria"),
])
def test_cada_perfil_consulta_su_microservicio(correo, servicio, ruta):
    cliente = ClienteXml()
    sesion = cliente.login(correo, PASSWORD)
    assert sesion["usuario"]["rol"]
    respuesta = cliente.solicitar(servicio, "GET", ruta)
    assert isinstance(respuesta, dict)


def test_rol_incorrecto_es_rechazado_por_el_backend_no_solo_por_la_interfaz():
    cliente = ClienteXml(); cliente.login("roberto.centro@demo.mx", PASSWORD)
    with pytest.raises(Exception) as error:
        cliente.solicitar("reembolsos", "GET", "/api/v1/reembolsos-costos/reembolsos")
    assert getattr(error.value, "codigo", None) == 403
