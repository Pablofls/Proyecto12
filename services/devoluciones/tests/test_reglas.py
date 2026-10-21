"""Pruebas unitarias de las validaciones (sin base de datos)."""
import unittest

import reglas

DESCRIPCION = "El empaque llego roto y el producto derramado."


class PruebaReglas(unittest.TestCase):
    def campos(self, errores):
        return {e["campo"] for e in errores}

    def test_nueva_valida_y_cantidad_por_defecto(self):
        valores, errores = reglas.validar_nueva(
            {"venta_detalle_id": 5, "motivo_id": "2", "descripcion_problema": DESCRIPCION})
        self.assertEqual(errores, [])
        self.assertEqual(valores["cantidad_devuelta"], 1)
        self.assertEqual(valores["motivo_id"], 2)  # llega como texto desde XML

    def test_nueva_sin_campos(self):
        _, errores = reglas.validar_nueva({})
        self.assertEqual(self.campos(errores),
                         {"venta_detalle_id", "motivo_id", "descripcion_problema"})

    def test_enteros_invalidos(self):
        _, errores = reglas.validar_nueva({"venta_detalle_id": 0, "motivo_id": "abc",
                                           "descripcion_problema": DESCRIPCION,
                                           "cantidad_devuelta": -2})
        self.assertEqual(self.campos(errores),
                         {"venta_detalle_id", "motivo_id", "cantidad_devuelta"})

    def test_booleano_no_cuenta_como_entero(self):
        _, errores = reglas.validar_nueva({"venta_detalle_id": True, "motivo_id": 1,
                                           "descripcion_problema": DESCRIPCION})
        self.assertEqual(self.campos(errores), {"venta_detalle_id"})

    def test_descripcion_corta_y_larga(self):
        _, corta = reglas.validar_nueva({"venta_detalle_id": 1, "motivo_id": 1,
                                         "descripcion_problema": "roto"})
        _, larga = reglas.validar_nueva({"venta_detalle_id": 1, "motivo_id": 1,
                                         "descripcion_problema": "x" * 2001})
        self.assertEqual(self.campos(corta), {"descripcion_problema"})
        self.assertEqual(self.campos(larga), {"descripcion_problema"})

    def test_edicion_exige_cantidad(self):
        _, errores = reglas.validar_edicion({"motivo_id": 1,
                                             "descripcion_problema": DESCRIPCION})
        self.assertEqual(self.campos(errores), {"cantidad_devuelta"})

    def test_resolucion_valida(self):
        valores, errores = reglas.validar_resolucion({"decision": "AUTORIZAR"})
        self.assertEqual(errores, [])
        self.assertEqual(valores["decision"], "autorizar")

    def test_rechazo_sin_justificacion(self):
        _, errores = reglas.validar_resolucion({"decision": "rechazar"})
        self.assertEqual(self.campos(errores), {"justificacion"})

    def test_decision_desconocida(self):
        _, errores = reglas.validar_resolucion({"decision": "aprobar"})
        self.assertEqual(self.campos(errores), {"decision"})

    def test_justificacion_demasiado_larga(self):
        _, errores = reglas.validar_resolucion({"decision": "autorizar",
                                                "justificacion": "x" * 501})
        self.assertEqual(self.campos(errores), {"justificacion"})

    def test_filtro_de_estado(self):
        self.assertEqual(reglas.validar_estado("autorizada"), ("autorizada", []))
        self.assertEqual(reglas.validar_estado(""), ("", []))
        estado, errores = reglas.validar_estado("perdida")
        self.assertIsNone(estado)
        self.assertEqual(self.campos(errores), {"estado"})


if __name__ == "__main__":
    unittest.main()
