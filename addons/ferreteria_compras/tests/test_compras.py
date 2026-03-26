from odoo.tests.common import TransactionCase
from odoo.exceptions import ValidationError


class TestComprasFerreteria(TransactionCase):
    """Tests para el módulo de compras"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env['res.partner']
        cls.PurchaseOrder = cls.env['purchase.order']
        cls.Product = cls.env['product.product']

        cls.proveedor = cls.Partner.create({
            'name': 'Proveedor Test SAC',
            'es_proveedor_ferreteria': True,
            'tipo_proveedor': 'distribuidor',
            'ruc_proveedor': '20987654321',
            'dias_entrega': 5,
            'condicion_pago_compra': 'credito_30',
            'calificacion_proveedor': '4',
        })

        cls.producto = cls.Product.create({
            'name': 'Cemento Test',
            'type': 'product',
            'es_ferreteria': True,
        })

    def test_create_proveedor(self):
        """Test creación de proveedor ferretería."""
        self.assertTrue(self.proveedor.id)
        self.assertTrue(self.proveedor.es_proveedor_ferreteria)
        self.assertEqual(self.proveedor.tipo_proveedor, 'distribuidor')
        self.assertEqual(self.proveedor.dias_entrega, 5)

    def test_ruc_proveedor_validation(self):
        """Test validación de RUC de proveedor."""
        with self.assertRaises(ValidationError):
            self.Partner.create({
                'name': 'RUC Malo',
                'ruc_proveedor': '123',
            })

    def test_calificacion_proveedor(self):
        """Test calificación del proveedor."""
        self.assertEqual(self.proveedor.calificacion_proveedor, '4')

    def test_create_purchase_order(self):
        """Test creación de orden de compra."""
        po = self.PurchaseOrder.create({
            'partner_id': self.proveedor.id,
            'tipo_compra': 'reposicion',
            'order_line': [(0, 0, {
                'product_id': self.producto.id,
                'name': 'Cemento Test',
                'product_qty': 50,
                'price_unit': 25.0,
                'product_uom': self.producto.uom_id.id,
                'date_planned': '2026-04-01',
            })],
        })
        self.assertTrue(po.id)
        self.assertEqual(po.tipo_compra, 'reposicion')
        self.assertEqual(len(po.order_line), 1)

    def test_tipo_compra_selection(self):
        """Test tipos de compra."""
        for tipo in ['reposicion', 'pedido_cliente', 'nueva_linea', 'urgente']:
            po = self.PurchaseOrder.create({
                'partner_id': self.proveedor.id,
                'tipo_compra': tipo,
            })
            self.assertEqual(po.tipo_compra, tipo)

    def test_recibido_computed(self):
        """Test campo recibido computado."""
        po = self.PurchaseOrder.create({
            'partner_id': self.proveedor.id,
        })
        po._compute_recibido()
        self.assertFalse(po.recibido)

    def test_total_compras_proveedor(self):
        """Test cálculo de total de compras."""
        self.proveedor._compute_total_compras()
        self.assertEqual(self.proveedor.total_compras_count, 0)

    def test_categorias_proveedor(self):
        """Test asignación de categorías a proveedor."""
        cat = self.env.ref(
            'ferreteria_inventario.cat_herramientas',
            raise_if_not_found=False,
        )
        if cat:
            self.proveedor.write({
                'categorias_proveedor_ids': [(4, cat.id)],
            })
            self.assertIn(cat.id, self.proveedor.categorias_proveedor_ids.ids)
