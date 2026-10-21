import unittest
from app import ErrorApi, _bool_estricto, evaluar_aptitud

class PruebaAptitud(unittest.TestCase):
    def test_seco_sano_es_apto(self): self.assertEqual(evaluar_aptitud(False,False,False,False,None),(True,[]))
    def test_dano_impide_inventario(self): self.assertFalse(evaluar_aptitud(False,True,False,False,None)[0])
    def test_cadena_frio_impide_inventario(self): self.assertFalse(evaluar_aptitud(True,False,False,True,5)[0])
    def test_tiempo_fuera_impide_inventario(self): self.assertFalse(evaluar_aptitud(True,False,False,False,31)[0])
    def test_booleano_ambiguo_se_rechaza(self):
        with self.assertRaises(ErrorApi): _bool_estricto("quizas","danos")

if __name__=="__main__": unittest.main()
