from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    es_proveedor_ferreteria = fields.Boolean(
        string='Proveedor Ferretería',
        default=False,
    )
    tipo_proveedor = fields.Selection([
        ('fabricante', 'Fabricante'),
        ('distribuidor', 'Distribuidor'),
        ('importador', 'Importador'),
        ('local', 'Proveedor Local'),
    ], string='Tipo de Proveedor')
    ruc_proveedor = fields.Char(
        string='RUC',
        size=11,
        help='RUC del proveedor (11 dígitos)',
    )
    categorias_proveedor_ids = fields.Many2many(
        'ferreteria.categoria',
        'partner_ferreteria_categoria_rel',
        'partner_id',
        'categoria_id',
        string='Categorías que Provee',
        help='Categorías de productos que este proveedor suministra',
    )
    dias_entrega = fields.Integer(
        string='Días de Entrega',
        default=0,
        help='Tiempo promedio de entrega en días',
    )
    condicion_pago_compra = fields.Selection([
        ('contado', 'Contado'),
        ('credito_15', 'Crédito 15 días'),
        ('credito_30', 'Crédito 30 días'),
        ('credito_60', 'Crédito 60 días'),
        ('credito_90', 'Crédito 90 días'),
    ], string='Condición de Pago', default='contado')
    contacto_ventas = fields.Char(
        string='Contacto de Ventas',
        help='Nombre del vendedor o ejecutivo de cuenta',
    )
    telefono_ventas = fields.Char(
        string='Teléfono Ventas',
    )
    cuenta_bancaria_proveedor = fields.Char(
        string='Cuenta Bancaria',
        help='Número de cuenta para transferencias',
    )
    banco_proveedor = fields.Char(
        string='Banco',
    )
    notas_proveedor = fields.Text(
        string='Notas del Proveedor',
        help='Acuerdos, condiciones especiales, etc.',
    )
    calificacion_proveedor = fields.Selection([
        ('1', 'Malo'),
        ('2', 'Regular'),
        ('3', 'Bueno'),
        ('4', 'Muy Bueno'),
        ('5', 'Excelente'),
    ], string='Calificación', default='3')
    total_compras_count = fields.Integer(
        string='Total Compras',
        compute='_compute_total_compras',
    )
    total_comprado_proveedor = fields.Float(
        string='Total Comprado (S/)',
        compute='_compute_total_compras',
    )

    @api.depends('purchase_order_count')
    def _compute_total_compras(self):
        PurchaseOrder = self.env['purchase.order']
        for partner in self:
            orders = PurchaseOrder.search([
                ('partner_id', '=', partner.id),
                ('state', 'in', ('purchase', 'done')),
            ])
            partner.total_compras_count = len(orders)
            partner.total_comprado_proveedor = sum(orders.mapped('amount_total'))

    @api.constrains('ruc_proveedor')
    def _check_ruc_proveedor(self):
        for partner in self:
            if partner.ruc_proveedor and len(partner.ruc_proveedor) != 11:
                raise models.ValidationError(
                    'El RUC debe tener exactamente 11 dígitos.'
                )
            if partner.ruc_proveedor and not partner.ruc_proveedor.isdigit():
                raise models.ValidationError(
                    'El RUC solo debe contener números.'
                )
