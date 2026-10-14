import unittest
from decimal import Decimal
from app.domain.calculo import calcular_comissao

class TestERPComissoes(unittest.TestCase):
    def test_calculo_50_porcento(self):
        self.assertEqual(calcular_comissao("1250.00", "0.50"), Decimal("625.00"))
        self.assertEqual(calcular_comissao("850.50", "0.50"), Decimal("425.25"))

    def test_arredondamento_comercial(self):
        # 333.33 * 0.5 = 166.665 -> 166.67
        self.assertEqual(calcular_comissao("333.33", "0.50"), Decimal("166.67"))
        # 450.75 * 0.5 = 225.375 -> 225.38
        self.assertEqual(calcular_comissao("450.75", "0.50"), Decimal("225.38"))
        # 12300.99 * 0.5 = 6150.495 -> 6150.50
        self.assertEqual(calcular_comissao("12300.99", "0.50"), Decimal("6150.50"))

    def test_bloqueio_negativo(self):
        with self.assertRaises(ValueError):
            calcular_comissao("-100.00", "0.50")

if __name__ == '__main__':
    unittest.main()
