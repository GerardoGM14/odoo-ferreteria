from odoo import models, fields, api
from odoo.exceptions import UserError


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    tipo_compra = fields.Selection([
        ('reposicion', 'Reposición de Stock'),
        ('pedido_cliente', 'Pedido de Cliente'),
        ('nueva_linea', 'Nueva Línea de Productos'),
        ('urgente', 'Compra Urgente'),
    ], string='Tipo de Compra', default='reposicion')
    proveedor_tipo = fields.Selection(
        related='partner_id.tipo_proveedor',
        string='Tipo de Proveedor',
        readonly=True,
    )
    compras_notas = fields.Text(
        string='Notas de Compra',
        help='Instrucciones o notas internas de la compra',
    )
    fecha_entrega_esperada = fields.Date(
        string='Fecha Entrega Esperada',
        help='Fecha en la que se espera recibir la mercadería',
    )
    recibido = fields.Boolean(
        string='Mercadería Recibida',
        compute='_compute_recibido',
        store=True,
    )

    @api.depends('picking_ids', 'picking_ids.state')
    def _compute_recibido(self):
        for order in self:
            pickings = order.picking_ids
            if pickings:
                order.recibido = all(p.state == 'done' for p in pickings)
            else:
                order.recibido = False

    @api.onchange('partner_id')
    def _onchange_partner_compras_ferreteria(self):
        """Auto-completar datos según el proveedor."""
        if self.partner_id and self.partner_id.es_proveedor_ferreteria:
            if self.partner_id.dias_entrega:
                from datetime import timedelta
                self.fecha_entrega_esperada = (
                    fields.Date.today() + timedelta(days=self.partner_id.dias_entrega)
                )

    def action_crear_desde_alertas_stock(self):
        """Crear orden de compra desde productos con stock bajo mínimo."""
        self.ensure_one()
        ProductTemplate = self.env['product.template']
        products_below = ProductTemplate.search([
            ('es_ferreteria', '=', True),
            ('stock_minimo', '>', 0),
        ]).filtered(lambda p: p.qty_available <= p.stock_minimo)

        if not products_below:
            raise UserError('No hay productos con stock bajo mínimo.')

        lines = []
        for product in products_below:
            # Calcular cantidad a pedir: llevar al doble del stock mínimo
            qty_to_order = (product.stock_minimo * 2) - product.qty_available
            if qty_to_order <= 0:
                qty_to_order = product.stock_minimo

            # Buscar info del proveedor
            supplier_info = self.env['product.supplierinfo'].search([
                ('product_tmpl_id', '=', product.id),
                ('partner_id', '=', self.partner_id.id),
            ], limit=1)

            price = supplier_info.price if supplier_info else 0.0

            lines.append((0, 0, {
                'product_id': product.product_variant_id.id,
                'name': product.name,
                'product_qty': qty_to_order,
                'price_unit': price,
                'product_uom': product.uom_po_id.id or product.uom_id.id,
                'date_planned': self.fecha_entrega_esperada or fields.Date.today(),
            }))

        if lines:
            self.write({
                'order_line': lines,
                'tipo_compra': 'reposicion',
            })

        return True


class PurchaseOrderLine(models.Model):
    _inherit = 'purchase.order.line'

    ferreteria_categoria_id = fields.Many2one(
        related='product_id.product_tmpl_id.ferreteria_categoria_id',
        string='Categoría Ferretería',
        readonly=True,
        store=True,
    )
    stock_actual = fields.Float(
        related='product_id.qty_available',
        string='Stock Actual',
        readonly=True,
    )
    stock_minimo = fields.Float(
        related='product_id.product_tmpl_id.stock_minimo',
        string='Stock Mínimo',
        readonly=True,
    )
    diferencia_precio = fields.Float(
        string='Diferencia vs Último Precio',
        compute='_compute_diferencia_precio',
    )

    @api.depends('price_unit', 'product_id')
    def _compute_diferencia_precio(self):
        for line in self:
            if line.product_id:
                # Buscar último precio de compra
                last_line = self.search([
                    ('product_id', '=', line.product_id.id),
                    ('order_id.state', 'in', ('purchase', 'done')),
                    ('id', '!=', line.id),
                ], order='create_date desc', limit=1)
                if last_line:
                    line.diferencia_precio = line.price_unit - last_line.price_unit
                else:
                    line.diferencia_precio = 0.0
            else:
                line.diferencia_precio = 0.0
