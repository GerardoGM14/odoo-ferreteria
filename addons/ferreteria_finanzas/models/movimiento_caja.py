from odoo import models, fields, api
from odoo.exceptions import UserError


class MovimientoCaja(models.Model):
    _name = 'ferreteria.movimiento.caja'
    _description = 'Movimiento de Caja'
    _order = 'fecha desc, id desc'

    name = fields.Char(
        string='Referencia',
        required=True,
        readonly=True,
        default='Nuevo',
        copy=False,
    )
    caja_diaria_id = fields.Many2one(
        'ferreteria.caja.diaria',
        string='Caja Diaria',
        required=True,
        ondelete='cascade',
    )
    fecha = fields.Datetime(
        string='Fecha/Hora',
        required=True,
        default=fields.Datetime.now,
    )
    tipo = fields.Selection([
        ('ingreso', 'Ingreso'),
        ('egreso', 'Egreso'),
    ], string='Tipo', required=True)
    categoria = fields.Selection([
        ('venta', 'Venta'),
        ('cobro', 'Cobro de Cuenta'),
        ('adelanto', 'Adelanto de Cliente'),
        ('devolucion_cliente', 'Devolución a Cliente'),
        ('pago_proveedor', 'Pago a Proveedor'),
        ('gasto_operativo', 'Gasto Operativo'),
        ('gasto_personal', 'Gasto de Personal'),
        ('retiro', 'Retiro de Efectivo'),
        ('deposito', 'Depósito Bancario'),
        ('otros', 'Otros'),
    ], string='Categoría', required=True)
    metodo_pago = fields.Selection([
        ('efectivo', 'Efectivo'),
        ('tarjeta', 'Tarjeta'),
        ('transferencia', 'Transferencia'),
        ('yape_plin', 'Yape/Plin'),
        ('cheque', 'Cheque'),
    ], string='Método de Pago', required=True, default='efectivo')
    monto = fields.Float(
        string='Monto (S/)',
        required=True,
    )
    descripcion = fields.Char(
        string='Descripción',
        required=True,
    )
    partner_id = fields.Many2one(
        'res.partner',
        string='Cliente/Proveedor',
    )
    sale_order_id = fields.Many2one(
        'sale.order',
        string='Orden de Venta',
    )
    invoice_id = fields.Many2one(
        'account.move',
        string='Factura/Boleta',
    )
    usuario_id = fields.Many2one(
        'res.users',
        string='Registrado por',
        default=lambda self: self.env.user,
        readonly=True,
    )
    comprobante_ref = fields.Char(
        string='Nro. Comprobante',
        help='Número de factura, boleta, recibo u otro comprobante',
    )
    notas = fields.Text(string='Notas')

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'ferreteria.movimiento.caja'
                ) or 'Nuevo'
        records = super().create(vals_list)
        # Verificar que la caja esté abierta
        for record in records:
            if record.caja_diaria_id.state != 'abierta':
                raise UserError(
                    'Solo se pueden registrar movimientos en una caja abierta.'
                )
        return records

    @api.constrains('monto')
    def _check_monto(self):
        for mov in self:
            if mov.monto <= 0:
                raise models.ValidationError(
                    'El monto debe ser mayor a cero.'
                )

    @api.onchange('tipo')
    def _onchange_tipo(self):
        """Sugerir categorías según tipo."""
        if self.tipo == 'ingreso':
            self.categoria = 'venta'
        elif self.tipo == 'egreso':
            self.categoria = 'gasto_operativo'
