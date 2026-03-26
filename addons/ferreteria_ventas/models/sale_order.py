from odoo import models, fields, api


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    tipo_venta = fields.Selection([
        ('mostrador', 'Venta Mostrador'),
        ('cotizacion', 'Cotización'),
        ('credito', 'Venta a Crédito'),
        ('pedido', 'Pedido Especial'),
    ], string='Tipo de Venta', default='mostrador')
    ferreteria_notas = fields.Text(
        string='Notas de Venta',
        help='Instrucciones especiales o notas internas',
    )
    descuento_global = fields.Float(
        string='Descuento Global (%)',
        default=0.0,
        help='Descuento porcentual aplicado a toda la orden',
    )
    vendedor_id = fields.Many2one(
        related='user_id',
        string='Vendedor',
        readonly=True,
    )
    cliente_tipo = fields.Selection(
        related='partner_id.tipo_cliente',
        string='Tipo de Cliente',
        readonly=True,
    )

    @api.onchange('partner_id')
    def _onchange_partner_ferreteria(self):
        """Auto-configurar tipo de venta según el tipo de cliente."""
        if self.partner_id and self.partner_id.es_cliente_ferreteria:
            if self.partner_id.tipo_cliente == 'mayorista':
                self.tipo_venta = 'credito'
            elif self.partner_id.tipo_cliente in ('empresa', 'contratista'):
                self.tipo_venta = 'credito'

    @api.onchange('descuento_global')
    def _onchange_descuento_global(self):
        """Aplicar descuento global a todas las líneas."""
        if self.descuento_global:
            for line in self.order_line:
                line.discount = self.descuento_global

    def action_apply_descuento_global(self):
        """Botón para aplicar descuento global a las líneas existentes."""
        self.ensure_one()
        for line in self.order_line:
            line.discount = self.descuento_global
        return True


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    ferreteria_categoria_id = fields.Many2one(
        related='product_template_id.ferreteria_categoria_id',
        string='Categoría Ferretería',
        readonly=True,
        store=True,
    )
    ubicacion_producto = fields.Char(
        related='product_template_id.ubicacion_almacen',
        string='Ubicación',
        readonly=True,
    )
