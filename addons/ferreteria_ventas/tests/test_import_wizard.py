from odoo.tests.common import TransactionCase


class TestImportWizard(TransactionCase):
    """Tests para el wizard de importación de productos"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Wizard = cls.env['ferreteria.import.productos.wizard']

    def test_wizard_create(self):
        """Test creación del wizard."""
        wizard = self.Wizard.create({
            'update_existing': True,
            'import_mode': 'all',
        })
        self.assertTrue(wizard.id)
        self.assertEqual(wizard.state, 'draft')

    def test_parse_price_soles(self):
        """Test parseo de precios en formato soles."""
        wizard = self.Wizard.create({})
        self.assertEqual(wizard._parse_price('S/ 17,50'), 17.50)
        self.assertEqual(wizard._parse_price('S/ 1.250,00'), 1250.00)
        self.assertEqual(wizard._parse_price('S/ 0,59'), 0.59)

    def test_parse_price_dash(self):
        """Test parseo de precio vacío (guión)."""
        wizard = self.Wizard.create({})
        self.assertEqual(wizard._parse_price('-'), 0.0)
        self.assertEqual(wizard._parse_price(''), 0.0)
        self.assertEqual(wizard._parse_price(None), 0.0)

    def test_parse_price_numeric(self):
        """Test parseo de precio numérico directo."""
        wizard = self.Wizard.create({})
        self.assertEqual(wizard._parse_price(17.5), 17.5)
        self.assertEqual(wizard._parse_price(0.0), 0.0)

    def test_departamento_mapping(self):
        """Test mapeo de departamento a categoría."""
        wizard = self.Wizard.create({})

        cat = wizard._get_departamento_categoria('GASFITERIA')
        self.assertTrue(cat)

        cat = wizard._get_departamento_categoria('HERRAMIENTAS')
        self.assertTrue(cat)

        cat = wizard._get_departamento_categoria('ELECTRICIDAD')
        self.assertTrue(cat)

        cat = wizard._get_departamento_categoria('SIN DEFINIR')
        self.assertFalse(cat)

    def test_import_without_file_raises_error(self):
        """Test que importar sin archivo genera error."""
        wizard = self.Wizard.create({
            'import_mode': 'all',
        })
        from odoo.exceptions import UserError
        with self.assertRaises(UserError):
            wizard.action_import()
