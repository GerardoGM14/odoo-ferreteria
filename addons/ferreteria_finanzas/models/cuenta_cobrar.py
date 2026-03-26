from odoo import models, fields, api


class CuentaCobrar(models.Model):
    _name = 'ferreteria.cuenta.cobrar'
    _description = 'Cuenta por Cobrar'
    _order = 'fecha_vencimiento asc'
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Referencia',
        required=True,
        readonly=True,
        default='Nuevo',
        copy=False,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente',
        required=True,
        tracking=True,
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Orden de Venta',
    )
    invoice_id = fields.Many2one(
        'account.move',
        string='Factura',
    )
    fecha_emision = fields.Date(
        string='Fecha Emisión',
        required=True,
        default=fields.Date.today,
    )
    fecha_vencimiento = fields.Date(
        string='Fecha Vencimiento',
        required=True,
        tracking=True,
    )
    monto_total = fields.Float(
        string='Monto Total',
        required=True,
        tracking=True,
    )
    monto_pagado = fields.Float(
        string='Monto Pagado',
        compute='_compute_monto_pagado',
        store=True,
    )
    monto_pendiente = fields.Float(
        string='Saldo Pendiente',
        compute='_compute_monto_pagado',
        store=True,
    )
    state = fields.Selection([
        ('pendiente', 'Pendiente'),
        ('parcial', 'Pago Parcial'),
        ('pagada', 'Pagada'),
        ('vencida', 'Vencida'),
        ('cancelada', 'Cancelada'),
    ], string='Estado', default='pendiente', tracking=True)
    dias_mora = fields.Integer(
        string='Días de Mora',
        compute='_compute_dias_mora',
    )
    pago_ids = fields.One2many(
        'ferreteria.pago.cuenta',
        'cuenta_cobrar_id',
        string='Pagos',
    )
    notas = fields.Text(string='Notas')
    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        default=lambda self: self.env.company,
    )

    @api.depends('pago_ids', 'pago_ids.monto', 'monto_total')
    def _compute_monto_pagado(self):
        for cuenta in self:
            pagado = sum(cuenta.pago_ids.mapped('monto'))
            cuenta.monto_pagado = pagado
            cuenta.monto_pendiente = cuenta.monto_total - pagado

    @api.depends('fecha_vencimiento', 'state')
    def _compute_dias_mora(self):
        today = fields.Date.today()
        for cuenta in self:
            if (
                cuenta.fecha_vencimiento
                and cuenta.state in ('pendiente', 'parcial')
                and today > cuenta.fecha_vencimiento
            ):
                cuenta.dias_mora = (today - cuenta.fecha_vencimiento).days
            else:
                cuenta.dias_mora = 0

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'ferreteria.cuenta.cobrar'
                ) or 'Nuevo'
        return super().create(vals_list)

    def action_marcar_vencidas(self):
        """Cron: marcar cuentas vencidas."""
        today = fields.Date.today()
        cuentas = self.search([
            ('state', 'in', ('pendiente', 'parcial')),
            ('fecha_vencimiento', '<', today),
        ])
        cuentas.write({'state': 'vencida'})

    def action_cancelar(self):
        """Cancelar cuenta."""
        self.ensure_one()
        self.write({'state': 'cancelada'})


class PagoCuenta(models.Model):
    _name = 'ferreteria.pago.cuenta'
    _description = 'Pago de Cuenta por Cobrar'
    _order = 'fecha desc'

    cuenta_cobrar_id = fields.Many2one(
        'ferreteria.cuenta.cobrar',
        string='Cuenta por Cobrar',
        required=True,
        ondelete='cascade',
    )
    fecha = fields.Date(
        string='Fecha de Pago',
        required=True,
        default=fields.Date.today,
    )
    monto = fields.Float(
        string='Monto Pagado',
        required=True,
    )
    metodo_pago = fields.Selection([
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia'),
        ('yape_plin', 'Yape/Plin'),
        ('cheque', 'Cheque'),
    ], string='Método de Pago', required=True, default='efectivo')
    referencia = fields.Char(
        string='Referencia de Pago',
        help='Número de operación, voucher, etc.',
    )
    notas = fields.Text(string='Notas')
    usuario_id = fields.Many2one(
        'res.users',
        string='Registrado por',
        default=lambda self: self.env.user,
        readonly=True,
    )

    @api.constrains('monto')
    def _check_monto(self):
        for pago in self:
            if pago.monto <= 0:
                raise models.ValidationError('El monto debe ser mayor a cero.')

    @api.model_create_multi
    def create(self, vals_list):
        records = super().create(vals_list)
        # Actualizar estado de la cuenta
        for record in records:
            cuenta = record.cuenta_cobrar_id
            if cuenta.monto_pendiente <= 0:
                cuenta.write({'state': 'pagada'})
            elif cuenta.monto_pagado > 0:
                cuenta.write({'state': 'parcial'})
        return records
