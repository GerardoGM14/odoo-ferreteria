from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError


class TestCajaDiaria(TransactionCase):
    """Tests para el modelo de caja diaria"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.CajaDiaria = cls.env['ferreteria.caja.diaria']
        cls.MovimientoCaja = cls.env['ferreteria.movimiento.caja']

        cls.caja = cls.CajaDiaria.create({
            'monto_apertura': 500.0,
        })

    def test_create_caja(self):
        """Test creación de caja diaria."""
        self.assertTrue(self.caja.id)
        self.assertEqual(self.caja.state, 'borrador')
        self.assertEqual(self.caja.monto_apertura, 500.0)
        self.assertNotEqual(self.caja.name, 'Nuevo')

    def test_abrir_caja(self):
        """Test apertura de caja."""
        self.caja.action_abrir_caja()
        self.assertEqual(self.caja.state, 'abierta')
        self.assertTrue(self.caja.hora_apertura)

    def test_no_abrir_dos_cajas(self):
        """Test que no se pueden abrir dos cajas para el mismo usuario."""
        self.caja.action_abrir_caja()
        caja2 = self.CajaDiaria.create({
            'monto_apertura': 300.0,
            'fecha': '2026-03-27',
        })
        with self.assertRaises(UserError):
            caja2.action_abrir_caja()

    def test_cerrar_caja(self):
        """Test cierre de caja."""
        self.caja.action_abrir_caja()
        self.caja.action_cerrar_caja()
        self.assertEqual(self.caja.state, 'cerrada')
        self.assertTrue(self.caja.hora_cierre)

    def test_cerrar_caja_no_abierta_error(self):
        """Test que no se puede cerrar una caja no abierta."""
        with self.assertRaises(UserError):
            self.caja.action_cerrar_caja()

    def test_arquear_caja(self):
        """Test arqueo de caja."""
        self.caja.action_abrir_caja()
        self.caja.action_cerrar_caja()
        self.caja.write({'monto_cierre': 500.0})
        self.caja.action_arquear_caja()
        self.assertEqual(self.caja.state, 'arqueada')

    def test_arquear_sin_monto_error(self):
        """Test que arquear sin monto de cierre da error."""
        self.caja.action_abrir_caja()
        self.caja.action_cerrar_caja()
        with self.assertRaises(UserError):
            self.caja.action_arquear_caja()

    def test_movimientos_ingresos(self):
        """Test registro de ingresos en caja."""
        self.caja.action_abrir_caja()
        self.MovimientoCaja.create({
            'caja_diaria_id': self.caja.id,
            'tipo': 'ingreso',
            'categoria': 'venta',
            'metodo_pago': 'efectivo',
            'monto': 150.0,
            'descripcion': 'Venta Test 1',
        })
        self.MovimientoCaja.create({
            'caja_diaria_id': self.caja.id,
            'tipo': 'ingreso',
            'categoria': 'venta',
            'metodo_pago': 'tarjeta',
            'monto': 200.0,
            'descripcion': 'Venta Test 2',
        })
        self.assertEqual(self.caja.total_ingresos, 350.0)
        self.assertEqual(self.caja.total_ventas_efectivo, 150.0)
        self.assertEqual(self.caja.total_ventas_tarjeta, 200.0)
        self.assertEqual(self.caja.movimiento_count, 2)

    def test_saldo_esperado(self):
        """Test cálculo del saldo esperado."""
        self.caja.action_abrir_caja()
        self.MovimientoCaja.create({
            'caja_diaria_id': self.caja.id,
            'tipo': 'ingreso',
            'categoria': 'venta',
            'metodo_pago': 'efectivo',
            'monto': 300.0,
            'descripcion': 'Ingreso',
        })
        self.MovimientoCaja.create({
            'caja_diaria_id': self.caja.id,
            'tipo': 'egreso',
            'categoria': 'gasto_operativo',
            'metodo_pago': 'efectivo',
            'monto': 50.0,
            'descripcion': 'Gasto',
        })
        # 500 (apertura) + 300 (ingreso) - 50 (egreso) = 750
        self.assertEqual(self.caja.saldo_esperado, 750.0)

    def test_diferencia_cierre(self):
        """Test cálculo de diferencia al cierre."""
        self.caja.action_abrir_caja()
        self.caja.write({'monto_cierre': 480.0})
        # Saldo esperado = 500 (apertura), cierre = 480 → diferencia = -20
        self.assertEqual(self.caja.diferencia, -20.0)

    def test_movimiento_en_caja_cerrada_error(self):
        """Test que no se permite movimiento en caja cerrada."""
        # Caja en borrador (no abierta)
        with self.assertRaises(UserError):
            self.MovimientoCaja.create({
                'caja_diaria_id': self.caja.id,
                'tipo': 'ingreso',
                'categoria': 'venta',
                'metodo_pago': 'efectivo',
                'monto': 100.0,
                'descripcion': 'No debe funcionar',
            })

    def test_reabrir_caja(self):
        """Test reapertura de caja cerrada."""
        self.caja.action_abrir_caja()
        self.caja.action_cerrar_caja()
        self.caja.action_reabrir_caja()
        self.assertEqual(self.caja.state, 'abierta')
        self.assertFalse(self.caja.hora_cierre)
