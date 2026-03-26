from odoo.tests.common import TransactionCase


class TestSaleOrderFerreteria(TransactionCase):
    """Tests para la extensión de sale.order"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.SaleOrder = cls.env['sale.order']
        cls.Partner = cls.env['res.partner']
        cls.Product = cls.env['product.product']

        cls.cliente = cls.Partner.create({
            'name': 'Cliente Venta Test',
            'es_cliente_ferreteria': True,
            'tipo_cliente': 'mostrador',
        })

        cls.producto = cls.Product.create({
            'name': 'Tornillo Test',
            'type': 'consu',
            'list_price': 0.50,
            'es_ferreteria': True,
        })

    def test_create_sale_order(self):
        """Test creación de orden de venta con campos ferretería."""
        order = self.SaleOrder.create({
            'partner_id': self.cliente.id,
            'tipo_venta': 'mostrador',
            'order_line': [(0, 0, {
                'product_id': self.producto.id,
                'product_uom_qty': 100,
                'price_unit': 0.50,
            })],
        })
        self.assertTrue(order.id)
        self.assertEqual(order.tipo_venta, 'mostrador')
        self.assertEqual(len(order.order_line), 1)
        self.assertEqual(order.amount_total, 50.0)

    def test_tipo_venta_selection(self):
        """Test todos los tipos de venta."""
        for tipo in ['mostrador', 'cotizacion', 'credito', 'pedido']:
            order = self.SaleOrder.create({
                'partner_id': self.cliente.id,
                'tipo_venta': tipo,
            })
            self.assertEqual(order.tipo_venta, tipo)

    def test_descuento_global(self):
        """Test aplicación de descuento global."""
        order = self.SaleOrder.create({
            'partner_id': self.cliente.id,
            'tipo_venta': 'mostrador',
            'descuento_global': 10.0,
            'order_line': [(0, 0, {
                'product_id': self.producto.id,
                'product_uom_qty': 10,
                'price_unit': 10.0,
            })],
        })
        order.action_apply_descuento_global()
        self.assertEqual(order.order_line[0].discount, 10.0)

    def test_cliente_tipo_related(self):
        """Test campo relacionado tipo de cliente."""
        order = self.SaleOrder.create({
            'partner_id': self.cliente.id,
        })
        self.assertEqual(order.cliente_tipo, 'mostrador')
