from odoo.tests.common import TransactionCase


class TestFerreteriaKardex(TransactionCase):
    """Tests para el modelo ferreteria.kardex (SQL View)"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Kardex = cls.env['ferreteria.kardex']

    def test_kardex_model_exists(self):
        """Test que el modelo Kardex existe y es accesible."""
        self.assertTrue(self.Kardex)

    def test_kardex_is_readonly(self):
        """Test que el Kardex es de solo lectura (SQL view)."""
        # _auto = False, no se pueden crear registros directamente
        self.assertFalse(self.Kardex._auto)

    def test_kardex_search_empty(self):
        """Test búsqueda en Kardex vacío (sin movimientos)."""
        records = self.Kardex.search([])
        # Puede tener o no registros, pero no debe fallar
        self.assertIsNotNone(records)

    def test_kardex_fields_exist(self):
        """Test que todos los campos del Kardex existen."""
        expected_fields = [
            'date', 'product_id', 'product_tmpl_id',
            'ferreteria_categoria_id', 'tipo_movimiento',
            'quantity', 'reference', 'location_id',
            'location_dest_id', 'picking_id',
        ]
        for field_name in expected_fields:
            self.assertIn(
                field_name,
                self.Kardex._fields,
                f'Campo {field_name} debe existir en ferreteria.kardex',
            )

    def test_kardex_tipo_movimiento_selection(self):
        """Test valores de selección de tipo_movimiento."""
        field = self.Kardex._fields['tipo_movimiento']
        selection_values = [s[0] for s in field.selection]
        self.assertIn('entrada', selection_values)
        self.assertIn('salida', selection_values)
