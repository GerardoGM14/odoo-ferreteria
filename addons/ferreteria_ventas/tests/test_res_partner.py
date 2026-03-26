from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestResPartnerFerreteria(TransactionCase):
    """Tests para la extensión de res.partner (clientes)"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env['res.partner']
        cls.cliente = cls.Partner.create({
            'name': 'Juan Pérez Test',
            'es_cliente_ferreteria': True,
            'tipo_cliente': 'mayorista',
            'ruc': '20123456789',
            'dni': '12345678',
            'limite_credito': 5000.0,
            'dias_credito': 30,
        })

    def test_create_cliente(self):
        """Test creación de cliente ferretería."""
        self.assertTrue(self.cliente.id)
        self.assertTrue(self.cliente.es_cliente_ferreteria)
        self.assertEqual(self.cliente.tipo_cliente, 'mayorista')
        self.assertEqual(self.cliente.ruc, '20123456789')
        self.assertEqual(self.cliente.limite_credito, 5000.0)

    def test_ruc_validation_length(self):
        """Test validación de longitud de RUC."""
        with self.assertRaises(ValidationError):
            self.Partner.create({
                'name': 'RUC Corto',
                'ruc': '123',
            })

    def test_ruc_validation_numeric(self):
        """Test validación de RUC solo números."""
        with self.assertRaises(ValidationError):
            self.Partner.create({
                'name': 'RUC Letras',
                'ruc': '2012345ABC',
            })

    def test_dni_validation_length(self):
        """Test validación de longitud de DNI."""
        with self.assertRaises(ValidationError):
            self.Partner.create({
                'name': 'DNI Corto',
                'dni': '123',
            })

    def test_dni_validation_numeric(self):
        """Test validación de DNI solo números."""
        with self.assertRaises(ValidationError):
            self.Partner.create({
                'name': 'DNI Letras',
                'dni': '1234ABCD',
            })

    def test_historial_compras_sin_ordenes(self):
        """Test historial de compras vacío."""
        self.cliente._compute_historial_compras()
        self.assertEqual(self.cliente.historial_compras_count, 0)
        self.assertEqual(self.cliente.total_comprado, 0.0)

    def test_tipo_cliente_selection(self):
        """Test todos los tipos de cliente."""
        for tipo in ['mostrador', 'mayorista', 'contratista', 'empresa']:
            partner = self.Partner.create({
                'name': f'Test {tipo}',
                'es_cliente_ferreteria': True,
                'tipo_cliente': tipo,
            })
            self.assertEqual(partner.tipo_cliente, tipo)
