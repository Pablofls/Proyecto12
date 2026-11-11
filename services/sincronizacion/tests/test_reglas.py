"""Pruebas unitarias de las reglas de sincronizacion (sin base de datos)."""
import unittest
import uuid
from datetime import datetime, timedelta, timezone

import reglas

AHORA = datetime(2026, 11, 10, 18, 0, tzinfo=timezone.utc)


class PruebaIdYHuella(unittest.TestCase):
    def test_uuid_valido_en_forma_canonica(self):
        valor = str(uuid.uuid4())
        self.assertEqual(reglas.id_operacion_valido(valor.upper()), valor)

    def test_uuid_invalido(self):
        for valor in (None, "", "123", "no-es-uuid", 5):
            self.assertIsNone(reglas.id_operacion_valido(valor))

    def test_misma_operacion_en_json_y_xml_da_la_misma_huella(self):
        json_op = {"tipo": "recepcion", "capturado_en": "2026-11-10T10:00:00-06:00",
                   "datos": {"devolucion_id": 5, "coincide_expediente": True}}
        xml_op = {"tipo": "recepcion", "capturado_en": "2026-11-10T10:00:00-06:00",
                  "datos": {"devolucion_id": "5", "coincide_expediente": "true"}}
        self.assertEqual(reglas.huella(json_op), reglas.huella(xml_op))

    def test_huella_cambia_si_cambian_los_datos(self):
        a = {"tipo": "recepcion", "capturado_en": "x", "datos": {"devolucion_id": 5}}
        b = {"tipo": "recepcion", "capturado_en": "x", "datos": {"devolucion_id": 6}}
        self.assertNotEqual(reglas.huella(a), reglas.huella(b))

    def test_huella_no_depende_del_id(self):
        a = {"id_operacion": "1", "tipo": "t", "capturado_en": "x", "datos": {}}
        b = dict(a, id_operacion="2")
        self.assertEqual(reglas.huella(a), reglas.huella(b))


class PruebaCaptura(unittest.TestCase):
    def test_fecha_sin_zona_horaria_no_se_acepta(self):
        self.assertIsNone(reglas.leer_fecha_captura("2026-11-10T10:00:00"))
        self.assertIsNotNone(reglas.leer_fecha_captura("2026-11-10T10:00:00Z"))

    def test_captura_reciente_es_valida(self):
        self.assertIsNone(reglas.problema_de_captura(AHORA - timedelta(hours=3), AHORA))

    def test_captura_en_el_futuro(self):
        self.assertIn("futuro", reglas.problema_de_captura(AHORA + timedelta(hours=1), AHORA))

    def test_tolerancia_de_reloj(self):
        self.assertIsNone(reglas.problema_de_captura(AHORA + timedelta(minutes=4), AHORA))

    def test_captura_demasiado_vieja(self):
        vieja = AHORA - timedelta(days=reglas.MAX_DIAS_OFFLINE, minutes=1)
        self.assertIn("dias", reglas.problema_de_captura(vieja, AHORA))

    def test_captura_ilegible(self):
        self.assertIsNotNone(reglas.problema_de_captura(None, AHORA))


class PruebaReglasDeCampo(unittest.TestCase):
    def test_transiciones(self):
        self.assertTrue(reglas.transicion_permitida("asignada", "en_transito"))
        self.assertTrue(reglas.transicion_permitida("en_transito", "completada"))
        self.assertFalse(reglas.transicion_permitida("asignada", "completada"))
        self.assertFalse(reglas.transicion_permitida("completada", "fallida"))

    def test_ubicacion(self):
        self.assertIsNone(reglas.ubicacion_valida(None))
        self.assertEqual(reglas.ubicacion_valida({"latitud": "25.65", "longitud": "-100.4"}),
                         {"latitud": 25.65, "longitud": -100.4})
        with self.assertRaises(ValueError):
            reglas.ubicacion_valida({"latitud": 95, "longitud": 0})
        with self.assertRaises(ValueError):
            reglas.ubicacion_valida("25,-100")

    def test_conflicto_solo_con_409(self):
        self.assertEqual(reglas.estado_por_codigo(409), "conflicto")
        for codigo in (400, 403, 404, 413, 415):
            self.assertEqual(reglas.estado_por_codigo(codigo), "rechazada")

    def test_operaciones_criticas_nunca_son_offline(self):
        self.assertFalse(set(reglas.SOLO_EN_LINEA) & set(reglas.TIPOS_OFFLINE))

    def test_roles_sin_repetir(self):
        roles = reglas.roles_que_sincronizan()
        self.assertEqual(len(roles), len(set(roles)))
        self.assertNotIn("Cliente", roles)


if __name__ == "__main__":
    unittest.main()
