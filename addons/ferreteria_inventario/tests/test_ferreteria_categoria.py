from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestFerreteriaCategoria(TransactionCase):
    """Tests para el modelo ferreteria.categoria"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Categoria = cls.env['ferreteria.categoria']
        cls.cat_parent = cls.Categoria.create({
            'name': 'Herramientas Test',
            'code': 'HRT',
            'icon': 'fa fa-wrench',
            'sequence': 1,
        })

    def test_create_categoria(self):
        """Test creación básica de categoría."""
        self.assertTrue(self.cat_parent.id)
        self.assertEqual(self.cat_parent.name, 'Herramientas Test')
        self.assertEqual(self.cat_parent.code, 'HRT')
        self.assertTrue(self.cat_parent.active)

    def test_create_subcategoria(self):
        """Test creación de subcategoría con jerarquía."""
        sub = self.Categoria.create({
            'name': 'Herramientas Manuales',
            'code': 'HRM',
            'parent_id': self.cat_parent.id,
        })
        self.assertEqual(sub.parent_id.id, self.cat_parent.id)
        self.assertIn(sub.id, self.cat_parent.child_ids.ids)

    def test_recursion_check(self):
        """Test que no se permite recursión en categorías."""
        sub = self.Categoria.create({
            'name': 'Sub Test',
            'parent_id': self.cat_parent.id,
        })
        with self.assertRaises(ValidationError):
            self.cat_parent.write({'parent_id': sub.id})

    def test_product_count(self):
        """Test conteo de productos por categoría."""
        self.assertEqual(self.cat_parent.product_count, 0)
        self.env['product.template'].create({
            'name': 'Martillo Test',
            'es_ferreteria': True,
            'ferreteria_categoria_id': self.cat_parent.id,
        })
        self.cat_parent._compute_product_count()
        self.assertEqual(self.cat_parent.product_count, 1)

    def test_name_get_with_parent(self):
        """Test que name_get muestra jerarquía."""
        sub = self.Categoria.create({
            'name': 'Eléctricas',
            'parent_id': self.cat_parent.id,
        })
        display_name = dict(sub.name_get())[sub.id]
        self.assertIn('/', display_name)
        self.assertIn('Herramientas Test', display_name)

    def test_default_data_loaded(self):
        """Test que los datos por defecto se cargaron."""
        cat_her = self.env.ref(
            'ferreteria_inventario.cat_herramientas',
            raise_if_not_found=False,
        )
        self.assertTrue(cat_her, 'La categoría Herramientas debe existir')
        cat_ele = self.env.ref(
            'ferreteria_inventario.cat_electricidad',
            raise_if_not_found=False,
        )
        self.assertTrue(cat_ele, 'La categoría Electricidad debe existir')
