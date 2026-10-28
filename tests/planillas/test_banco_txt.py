import sys
import unittest
from decimal import Decimal

sys.path.insert(0, '/app')

from cafae.documentos.banco_txt import formatear_linea_banco, generar_txt_banco


class TestBancoTxt(unittest.TestCase):
    def test_ejemplo_especificado_por_usuario(self):
        # Caso 1: 041, cuenta 4095653458, monto 3512.81 -> 0414095653458000000000351281
        linea1 = formatear_linea_banco('4095653458', 3512.81, '041')
        self.assertEqual(linea1, '0414095653458000000000351281')
        self.assertEqual(len(linea1), 28)

        # Caso 2: 041, cuenta 4093353456, monto 912.00 -> 0414093353456000000000091200
        linea2 = formatear_linea_banco('4093353456', 912.00, '041')
        self.assertEqual(linea2, '0414093353456000000000091200')
        self.assertEqual(len(linea2), 28)

    def test_tipo_transaccion_no_remunerativo(self):
        linea = formatear_linea_banco('4095653458', 1200.50, '341')
        self.assertTrue(linea.startswith('341'))
        self.assertEqual(len(linea), 28)
        self.assertEqual(linea, '3414095653458000000000120050')

    def test_cuenta_con_guiones_o_menos_de_10_digitos(self):
        # Cuenta ingresada con guiones o espacios
        linea = formatear_linea_banco('4-095-653458', 500.00, '041')
        self.assertEqual(linea, '0414095653458000000000050000')
        self.assertEqual(len(linea), 28)

        # Cuenta de 8 dígitos se completa con ceros a la izquierda a 10 dígitos
        linea_corta = formatear_linea_banco('95653458', 500.00, '041')
        self.assertEqual(linea_corta[3:13], '0095653458')
        self.assertEqual(len(linea_corta), 28)

    def test_generar_txt_banco_multiple_filas(self):
        filas = [
            {'dni': '12345678', 'apellidos': 'PEREZ', 'nombres': 'JUAN', 'cuenta_multired': '4095653458', 'neto': Decimal('3512.81')},
            {'dni': '87654321', 'apellidos': 'GOMEZ', 'nombres': 'ANA', 'cuenta_multired': '4093353456', 'neto': Decimal('912.00')},
            {'dni': '11223344', 'apellidos': 'SIN CTA', 'nombres': 'PEDRO', 'cuenta_multired': '', 'neto': Decimal('1000.00')},
            {'dni': '55667788', 'apellidos': 'NETO CERO', 'nombres': 'LUIS', 'cuenta_multired': '4091112223', 'neto': Decimal('0.00')}
        ]
        
        txt_bytes, resumen = generar_txt_banco(filas, '041')
        contenido = txt_bytes.decode('ascii')
        lineas = contenido.strip().split('\r\n')
        
        self.assertEqual(len(lineas), 2)
        self.assertEqual(lineas[0], '0414095653458000000000351281')
        self.assertEqual(lineas[1], '0414093353456000000000091200')
        self.assertEqual(resumen['total_registros'], 2)
        self.assertEqual(resumen['monto_total'], 4424.81)
        self.assertEqual(len(resumen['excluidos_sin_cuenta']), 1)
        self.assertEqual(len(resumen['excluidos_monto_cero']), 1)


if __name__ == '__main__':
    unittest.main()
