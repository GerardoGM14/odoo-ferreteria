from odoo.tests.common import TransactionCase


class TestProductTemplateFerreteria(TransactionCase):
    """Tests para la extensión de product.template"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.ProductTemplate = cls.env['product.template']
        cls.Categoria = cls.env['ferreteria.categoria']

        cls.categoria = cls.Categoria.create({
            'name': 'Test Electricidad',
            'code': 'TEL',
        })

        cls.product = cls.ProductTemplate.create({
            'name': 'Cable Eléctrico 2.5mm Test',
            'type': 'product',
            'es_ferreteria': True,
            'ferreteria_categoria_id': cls.categoria.id,
            'marca': 'INDECO',
            'unidad_ferreteria': 'metro',
            'stock_minimo': 100.0,
            'ubicacion_almacen': 'A-01-03',
            'list_price': 5.50,
        })

    def test_create_product_ferreteria(self):
        """Test creación de producto con campos de ferretería."""
        self.assertTrue(self.product.id)
        self.assertTrue(self.product.es_ferreteria)
        self.assertEqual(self.product.marca, 'INDECO')
        self.assertEqual(self.product.unidad_ferreteria, 'metro')
        self.assertEqual(self.product.stock_minimo, 100.0)
        self.assertEqual(self.product.ubicacion_almacen, 'A-01-03')

    def test_ferreteria_categoria_relation(self):
        """Test relación con categoría ferretería."""
        self.assertEqual(
            self.product.ferreteria_categoria_id.id,
            self.categoria.id,
        )
        self.assertEqual(
            self.product.ferreteria_categoria_id.name,
            'Test Electricidad',
        )

    def test_stock_bajo_minimo_sin_stock(self):
        """Test que el campo stock_bajo_minimo funciona sin stock."""
        # Producto nuevo sin stock, con stock_minimo > 0
        self.product._compute_stock_bajo_minimo()
        # qty_available = 0, stock_minimo = 100 → bajo mínimo
        self.assertTrue(self.product.stock_bajo_minimo)

    def test_stock_bajo_minimo_no_ferreteria(self):
        """Test que productos no-ferretería no generan alerta."""
        product_normal = self.ProductTemplate.create({
            'name': 'Producto Normal',
            'es_ferreteria': False,
            'stock_minimo': 10.0,
        })
        product_normal._compute_stock_bajo_minimo()
        self.assertFalse(product_normal.stock_bajo_minimo)

    def test_stock_bajo_minimo_sin_minimo(self):
        """Test que sin stock_minimo no hay alerta."""
        product_sin_min = self.ProductTemplate.create({
            'name': 'Sin Mínimo Test',
            'es_ferreteria': True,
            'stock_minimo': 0.0,
        })
        product_sin_min._compute_stock_bajo_minimo()
        self.assertFalse(product_sin_min.stock_bajo_minimo)

    def test_search_stock_bajo_minimo(self):
        """Test búsqueda de productos bajo mínimo."""
        results = self.ProductTemplate.search([
            ('stock_bajo_minimo', '=', True),
        ])
        self.assertIn(self.product.id, results.ids)

    def test_unidad_ferreteria_selection(self):
        """Test todos los valores de unidad_ferreteria."""
        valid_units = [
            'unidad', 'metro', 'kilo', 'litro',
            'rollo', 'caja', 'bolsa', 'par',
        ]
        for unit in valid_units:
            product = self.ProductTemplate.create({
                'name': f'Test {unit}',
                'es_ferreteria': True,
                'unidad_ferreteria': unit,
            })
            self.assertEqual(product.unidad_ferreteria, unit)

    def test_cron_check_stock_minimo(self):
        """Test que el cron de alertas no falla."""
        # Solo verificar que no lanza excepción
        self.ProductTemplate._cron_check_stock_minimo()

    def test_pricelists_loaded(self):
        """Test que las 4 listas de precios se cargaron."""
        for ref in [
            'ferreteria_inventario.pricelist_mayoreo1',
            'ferreteria_inventario.pricelist_mayoreo2',
            'ferreteria_inventario.pricelist_mayoreo3',
            'ferreteria_inventario.pricelist_mayoreo4',
        ]:
            pl = self.env.ref(ref, raise_if_not_found=False)
            self.assertTrue(pl, f'Lista de precios {ref} debe existir')
