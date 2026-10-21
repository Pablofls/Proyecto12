"""Dobles de la capa de datos para probar vistas sin PostgreSQL ni Redis.

Las bases de datos viven solo en la VM (CLAUDE.md): aqui se reemplazan
consultar/ejecutar y la sesion de Flask-Session por versiones en memoria.
"""
import importlib
import unittest
from unittest.mock import patch

# Modulos que importan consultar/ejecutar por nombre y por eso hay que parchear.
MODULOS_CON_BD = (
    "app.security",
    "app.notificaciones",
    "app.blueprints.notificaciones",
    "app.blueprints.panel",
    "app.blueprints.devoluciones",
    "app.blueprints.reembolsos",
    "app.blueprints.reportes",
)


class BaseFalsa:
    """Responde consultas segun un fragmento del SQL y registra lo ejecutado."""

    def __init__(self):
        self.reglas = []
        self.consultas = []
        self.ejecutadas = []

    def cuando(self, fragmento, resultado):
        """`resultado` es una lista de filas, un dict (con uno=True) o una funcion
        (sql, params) -> una de las anteriores."""
        self.reglas.append((fragmento, resultado))

    def consultar(self, sql, params=None, uno=False):
        self.consultas.append((sql, params))
        for fragmento, resultado in self.reglas:
            if fragmento in sql:
                if callable(resultado):
                    resultado = resultado(sql, params)
                if uno:
                    if isinstance(resultado, list):
                        return resultado[0] if resultado else None
                    return resultado
                return resultado if isinstance(resultado, list) else [resultado]
        return None if uno else []

    def ejecutar(self, sql, params=None, devolver=False):
        self.ejecutadas.append((sql, params))
        return None

    def insertadas(self, tabla):
        return [p for s, p in self.ejecutadas if f"INSERT INTO {tabla}" in s]

    def actualizadas(self, tabla):
        return [(s, p) for s, p in self.ejecutadas if f"UPDATE {tabla}" in s]


class PruebaWeb(unittest.TestCase):
    """App real (create_app) con BD falsa y sesion de cookie en lugar de Redis."""

    def setUp(self):
        self.bd = BaseFalsa()
        parches = [patch("app.Session")]
        for nombre in MODULOS_CON_BD:
            modulo = importlib.import_module(nombre)
            for funcion in ("consultar", "ejecutar"):
                if hasattr(modulo, funcion):
                    parches.append(patch.object(modulo, funcion, getattr(self.bd, funcion)))
        for parche in parches:
            parche.start()
            self.addCleanup(parche.stop)

        from app import create_app
        self.app = create_app()
        self.app.config.update(TESTING=True, SECRET_KEY="prueba", USE_MICROSERVICES=False)

    def cliente_como(self, rol, usuario_id=1, nombre="Prueba"):
        cliente = self.app.test_client()
        with cliente.session_transaction() as sesion:
            sesion["usuario"] = {"id": usuario_id, "nombre": nombre,
                                 "email": "prueba@example.com", "rol": rol}
        return cliente
