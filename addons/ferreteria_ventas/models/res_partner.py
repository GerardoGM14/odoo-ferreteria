from odoo import models, fields, api


class ResPartner(models.Model):
    _inherit = 'res.partner'

    es_cliente_ferreteria = fields.Boolean(
        string='Cliente Ferretería',
        default=False,
    )
    tipo_cliente = fields.Selection([
        ('mostrador', 'Mostrador'),
        ('mayorista', 'Mayorista'),
        ('contratista', 'Contratista'),
        ('empresa', 'Empresa'),
    ], string='Tipo de Cliente', default='mostrador')
    ruc = fields.Char(
        string='RUC',
        size=11,
        help='Registro Único de Contribuyentes (11 dígitos)',
    )
    dni = fields.Char(
        string='DNI',
        size=8,
        help='Documento Nacional de Identidad (8 dígitos)',
    )
    limite_credito = fields.Float(
        string='Límite de Crédito',
        default=0.0,
        help='Monto máximo permitido para ventas a crédito (S/)',
    )
    dias_credito = fields.Integer(
        string='Días de Crédito',
        default=0,
        help='Cantidad de días de plazo para pago',
    )
    historial_compras_count = fields.Integer(
        string='Total Compras',
        compute='_compute_historial_compras',
    )
    total_comprado = fields.Float(
        string='Total Comprado (S/)',
        compute='_compute_historial_compras',
    )
    notas_ferreteria = fields.Text(
        string='Notas Internas',
        help='Notas sobre el cliente (preferencias, acuerdos, etc.)',
    )

    @api.depends('sale_order_ids', 'sale_order_ids.state', 'sale_order_ids.amount_total')
    def _compute_historial_compras(self):
        for partner in self:
            orders = partner.sale_order_ids.filtered(
                lambda o: o.state in ('sale', 'done')
            )
            partner.historial_compras_count = len(orders)
            partner.total_comprado = sum(orders.mapped('amount_total'))

    @api.constrains('ruc')
    def _check_ruc(self):
        for partner in self:
            if partner.ruc and len(partner.ruc) != 11:
                raise models.ValidationError(
                    'El RUC debe tener exactamente 11 dígitos.'
                )
            if partner.ruc and not partner.ruc.isdigit():
                raise models.ValidationError(
                    'El RUC solo debe contener números.'
                )

    @api.constrains('dni')
    def _check_dni(self):
        for partner in self:
            if partner.dni and len(partner.dni) != 8:
                raise models.ValidationError(
                    'El DNI debe tener exactamente 8 dígitos.'
                )
            if partner.dni and not partner.dni.isdigit():
                raise models.ValidationError(
                    'El DNI solo debe contener números.'
                )

    @api.onchange('tipo_cliente')
    def _onchange_tipo_cliente(self):
        """Asignar lista de precios por defecto según tipo de cliente."""
        if self.tipo_cliente == 'mayorista':
            pricelist = self.env.ref(
                'ferreteria_inventario.pricelist_mayoreo2',
                raise_if_not_found=False,
            )
            if pricelist:
                self.property_product_pricelist = pricelist
        elif self.tipo_cliente == 'empresa':
            pricelist = self.env.ref(
                'ferreteria_inventario.pricelist_mayoreo3',
                raise_if_not_found=False,
            )
            if pricelist:
                self.property_product_pricelist = pricelist
        elif self.tipo_cliente == 'contratista':
            pricelist = self.env.ref(
                'ferreteria_inventario.pricelist_mayoreo4',
                raise_if_not_found=False,
            )
            if pricelist:
                self.property_product_pricelist = pricelist
        else:
            # Mostrador = Mayoreo 1 (precio base)
            pricelist = self.env.ref(
                'ferreteria_inventario.pricelist_mayoreo1',
                raise_if_not_found=False,
            )
            if pricelist:
                self.property_product_pricelist = pricelist
