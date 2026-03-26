from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError
from datetime import date, timedelta


class TestCuentaCobrar(TransactionCase):
    """Tests para el modelo de cuentas por cobrar"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.CuentaCobrar = cls.env['ferreteria.cuenta.cobrar']
        cls.PagoCuenta = cls.env['ferreteria.pago.cuenta']
        cls.Partner = cls.env['res.partner']

        cls.cliente = cls.Partner.create({
            'name': 'Deudor Test',
        })

        cls.cuenta = cls.CuentaCobrar.create({
            'partner_id': cls.cliente.id,
            'monto_total': 1000.0,
            'fecha_vencimiento': date.today() + timedelta(days=30),
        })

    def test_create_cuenta(self):
        """Test creación de cuenta por cobrar."""
        self.assertTrue(self.cuenta.id)
        self.assertEqual(self.cuenta.state, 'pendiente')
        self.assertEqual(self.cuenta.monto_total, 1000.0)
        self.assertEqual(self.cuenta.monto_pendiente, 1000.0)
        self.assertNotEqual(self.cuenta.name, 'Nuevo')

    def test_pago_parcial(self):
        """Test pago parcial actualiza estado."""
        self.PagoCuenta.create({
            'cuenta_cobrar_id': self.cuenta.id,
            'monto': 400.0,
            'metodo_pago': 'efectivo',
        })
        self.assertEqual(self.cuenta.monto_pagado, 400.0)
        self.assertEqual(self.cuenta.monto_pendiente, 600.0)
        self.assertEqual(self.cuenta.state, 'parcial')

    def test_pago_completo(self):
        """Test pago total cierra la cuenta."""
        self.PagoCuenta.create({
            'cuenta_cobrar_id': self.cuenta.id,
            'monto': 1000.0,
            'metodo_pago': 'transferencia',
        })
        self.assertEqual(self.cuenta.monto_pagado, 1000.0)
        self.assertEqual(self.cuenta.monto_pendiente, 0.0)
        self.assertEqual(self.cuenta.state, 'pagada')

    def test_pago_monto_cero_error(self):
        """Test que pago con monto 0 genera error."""
        with self.assertRaises(ValidationError):
            self.PagoCuenta.create({
                'cuenta_cobrar_id': self.cuenta.id,
                'monto': 0.0,
                'metodo_pago': 'efectivo',
            })

    def test_dias_mora_no_vencida(self):
        """Test que cuenta no vencida tiene 0 días mora."""
        self.cuenta._compute_dias_mora()
        self.assertEqual(self.cuenta.dias_mora, 0)

    def test_dias_mora_vencida(self):
        """Test cálculo de días de mora."""
        cuenta_vencida = self.CuentaCobrar.create({
            'partner_id': self.cliente.id,
            'monto_total': 500.0,
            'fecha_vencimiento': date.today() - timedelta(days=10),
        })
        cuenta_vencida._compute_dias_mora()
        self.assertEqual(cuenta_vencida.dias_mora, 10)

    def test_cancelar_cuenta(self):
        """Test cancelación de cuenta."""
        self.cuenta.action_cancelar()
        self.assertEqual(self.cuenta.state, 'cancelada')

    def test_marcar_vencidas_cron(self):
        """Test cron de marcar cuentas vencidas."""
        cuenta_vieja = self.CuentaCobrar.create({
            'partner_id': self.cliente.id,
            'monto_total': 200.0,
            'fecha_vencimiento': date.today() - timedelta(days=5),
        })
        self.CuentaCobrar.action_marcar_vencidas()
        cuenta_vieja.invalidate_recordset()
        self.assertEqual(cuenta_vieja.state, 'vencida')

    def test_multiples_pagos(self):
        """Test múltiples pagos parciales."""
        self.PagoCuenta.create({
            'cuenta_cobrar_id': self.cuenta.id,
            'monto': 200.0,
            'metodo_pago': 'efectivo',
        })
        self.PagoCuenta.create({
            'cuenta_cobrar_id': self.cuenta.id,
            'monto': 300.0,
            'metodo_pago': 'yape_plin',
        })
        self.assertEqual(self.cuenta.monto_pagado, 500.0)
        self.assertEqual(self.cuenta.monto_pendiente, 500.0)
        self.assertEqual(self.cuenta.state, 'parcial')
