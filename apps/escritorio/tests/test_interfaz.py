import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
sys.path.insert(0, str(Path(__file__).parents[1]))

from cliente_xml import ClienteXml
from main import (ADMIN, ANALISTA, CENTRO, INSPECTOR, REEMBOLSOS, SUPERVISOR,
                  Ventana, crear_aplicacion, filas_respuesta, valor_celda,
                  valor_tabla)


class ClienteFalso(ClienteXml):
    def __init__(self, rol):
        self.usuario = {"id": "1", "nombre": "Usuario de prueba", "rol": rol}
        self.access_token = "token"
        self.refresh_token = "refresh"

    def solicitar(self, *args, **kwargs):
        return {"datos": []}


def etiquetas(rol):
    app = crear_aplicacion([])
    ventana = Ventana(ClienteFalso(rol))
    resultado = [ventana.tabs.tabText(i) for i in range(ventana.tabs.count())]
    ventana.close()
    return resultado


def test_menu_del_inspector_no_expone_decisiones_comerciales():
    tabs = etiquetas(INSPECTOR)
    assert "Inspección" in tabs
    assert "Disposición" not in tabs
    assert "Reembolso" not in tabs


def test_menu_del_analista_separa_dictamen_de_disposicion():
    tabs = etiquetas(ANALISTA)
    assert "Disposición" in tabs
    assert "Inspección" not in tabs
    assert "Auditoría" in tabs


def test_menu_de_roberto_controla_inventario_sin_aprobar_reembolsos():
    tabs = etiquetas(CENTRO)
    assert tabs == ["Panel", "Inventario", "Existencias", "Evidencias"]


def test_menu_de_reembolsos_limita_el_alcance_economico():
    tabs = etiquetas(REEMBOLSOS)
    assert "Reembolso" in tabs
    assert "Inventario" not in tabs
    assert "Disposición" not in tabs


def test_supervisor_puede_decidir_y_controlar_inventario():
    tabs = etiquetas(SUPERVISOR)
    assert "Disposición" in tabs and "Inventario" in tabs


def test_administrador_solo_consulta_auditoria_e_investigaciones():
    assert etiquetas(ADMIN) == ["Auditoría", "Investigaciones"]


def test_normalizacion_de_lista_xml_unica_y_multiple():
    assert filas_respuesta({"datos": {"item": {"id": "1"}}}) == [{"id": "1"}]
    assert filas_respuesta({"datos": [{"id": "1"}, {"id": "2"}]})[1]["id"] == "2"
    assert filas_respuesta({"datos": ""}) == []


def test_formato_amigable_para_booleanos_y_vacios():
    assert valor_tabla("true") == "Sí"
    assert valor_tabla("false") == "No"
    assert valor_tabla("") == "—"
    assert valor_celda("horas_pendiente", "1.1055") == "1.1 h"
    assert valor_celda("clasificacion_temperatura", "no_refrigerado") == "No refrigerado"
    fecha = valor_celda("fecha_solicitud", "2026-11-21T20:00:04+00:00")
    assert "T20" not in fecha and fecha.endswith("UTC")


def test_cierre_local_elimina_todos_los_secretos():
    cliente = ClienteFalso(CENTRO)
    cliente.http = type("Http", (), {"cookies": type("Cookies", (), {"clear": lambda self: None})()})()
    cliente.cerrar_sesion_local()
    assert cliente.access_token is None
    assert cliente.refresh_token is None
    assert cliente.usuario is None
