from odoo import models, fields, api
from odoo.exceptions import UserError


class CajaDiaria(models.Model):
    _name = 'ferreteria.caja.diaria'
    _description = 'Caja Diaria'
    _order = 'fecha desc, id desc'
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char(
        string='Referencia',
        required=True,
        readonly=True,
        default='Nuevo',
        copy=False,
    )
    fecha = fields.Date(
        string='Fecha',
        required=True,
        default=fields.Date.today,
        tracking=True,
    )
    responsable_id = fields.Many2one(
        'res.users',
        string='Responsable',
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        required=True,
        default=lambda self: self.env.company,
    )
    state = fields.Selection([
        ('borrador', 'Borrador'),
        ('abierta', 'Abierta'),
        ('cerrada', 'Cerrada'),
        ('arqueada', 'Arqueada'),
    ], string='Estado', default='borrador', tracking=True)

    # Montos
    monto_apertura = fields.Float(
        string='Monto de Apertura',
        required=True,
        tracking=True,
        help='Efectivo inicial en caja al abrir',
    )
    total_ingresos = fields.Float(
        string='Total Ingresos',
        compute='_compute_totales',
        store=True,
    )
    total_egresos = fields.Float(
        string='Total Egresos',
        compute='_compute_totales',
        store=True,
    )
    total_ventas_efectivo = fields.Float(
        string='Ventas en Efectivo',
        compute='_compute_totales',
        store=True,
    )
    total_ventas_tarjeta = fields.Float(
        string='Ventas con Tarjeta',
        compute='_compute_totales',
        store=True,
    )
    total_ventas_transferencia = fields.Float(
        string='Ventas Transferencia',
        compute='_compute_totales',
        store=True,
    )
    saldo_esperado = fields.Float(
        string='Saldo Esperado',
        compute='_compute_totales',
        store=True,
    )
    monto_cierre = fields.Float(
        string='Monto de Cierre (Conteo Real)',
        help='Monto real contado al cerrar la caja',
    )
    diferencia = fields.Float(
        string='Diferencia',
        compute='_compute_diferencia',
        store=True,
    )
    notas = fields.Text(string='Observaciones')
    hora_apertura = fields.Datetime(
        string='Hora de Apertura',
        readonly=True,
    )
    hora_cierre = fields.Datetime(
        string='Hora de Cierre',
        readonly=True,
    )

    # Relaciones
    movimiento_ids = fields.One2many(
        'ferreteria.movimiento.caja',
        'caja_diaria_id',
        string='Movimientos',
    )
    movimiento_count = fields.Integer(
        string='Nro. Movimientos',
        compute='_compute_totales',
        store=True,
    )

    @api.depends(
        'movimiento_ids',
        'movimiento_ids.monto',
        'movimiento_ids.tipo',
        'movimiento_ids.metodo_pago',
        'monto_apertura',
    )
    def _compute_totales(self):
        for caja in self:
            movimientos = caja.movimiento_ids
            ingresos = movimientos.filtered(lambda m: m.tipo == 'ingreso')
            egresos = movimientos.filtered(lambda m: m.tipo == 'egreso')

            caja.total_ingresos = sum(ingresos.mapped('monto'))
            caja.total_egresos = sum(egresos.mapped('monto'))

            caja.total_ventas_efectivo = sum(
                ingresos.filtered(lambda m: m.metodo_pago == 'efectivo').mapped('monto')
            )
            caja.total_ventas_tarjeta = sum(
                ingresos.filtered(lambda m: m.metodo_pago == 'tarjeta').mapped('monto')
            )
            caja.total_ventas_transferencia = sum(
                ingresos.filtered(lambda m: m.metodo_pago == 'transferencia').mapped('monto')
            )

            caja.saldo_esperado = (
                caja.monto_apertura + caja.total_ingresos - caja.total_egresos
            )
            caja.movimiento_count = len(movimientos)

    @api.depends('saldo_esperado', 'monto_cierre')
    def _compute_diferencia(self):
        for caja in self:
            caja.diferencia = caja.monto_cierre - caja.saldo_esperado

    @api.model_create_multi
    def create(self, vals_list):
        for vals in vals_list:
            if vals.get('name', 'Nuevo') == 'Nuevo':
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'ferreteria.caja.diaria'
                ) or 'Nuevo'
        return super().create(vals_list)

    def action_abrir_caja(self):
        """Abrir la caja del día."""
        self.ensure_one()
        # Verificar que no haya otra caja abierta para el mismo responsable
        caja_abierta = self.search([
            ('responsable_id', '=', self.responsable_id.id),
            ('state', '=', 'abierta'),
            ('id', '!=', self.id),
        ], limit=1)
        if caja_abierta:
            raise UserError(
                f'Ya existe una caja abierta ({caja_abierta.name}) '
                f'para {self.responsable_id.name}. Ciérrela primero.'
            )

        self.write({
            'state': 'abierta',
            'hora_apertura': fields.Datetime.now(),
        })

    def action_cerrar_caja(self):
        """Cerrar la caja (requiere conteo)."""
        self.ensure_one()
        if self.state != 'abierta':
            raise UserError('Solo se puede cerrar una caja abierta.')

        self.write({
            'state': 'cerrada',
            'hora_cierre': fields.Datetime.now(),
        })

    def action_arquear_caja(self):
        """Marcar como arqueada (revisada por supervisor)."""
        self.ensure_one()
        if self.state != 'cerrada':
            raise UserError('Solo se puede arquear una caja cerrada.')
        if self.monto_cierre <= 0:
            raise UserError(
                'Debe ingresar el monto de cierre (conteo real) antes de arquear.'
            )
        self.write({'state': 'arqueada'})

    def action_reabrir_caja(self):
        """Reabrir caja cerrada (solo supervisor)."""
        self.ensure_one()
        if self.state not in ('cerrada', 'arqueada'):
            raise UserError('Solo se puede reabrir una caja cerrada o arqueada.')
        self.write({
            'state': 'abierta',
            'hora_cierre': False,
        })

    def action_ver_movimientos(self):
        """Acción para ver movimientos de esta caja."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Movimientos - {self.name}',
            'res_model': 'ferreteria.movimiento.caja',
            'view_mode': 'tree,form',
            'domain': [('caja_diaria_id', '=', self.id)],
            'context': {'default_caja_diaria_id': self.id},
        }

    _sql_constraints = [
        ('fecha_responsable_unique',
         'UNIQUE(fecha, responsable_id, company_id)',
         'Solo puede existir una caja por día por responsable.'),
    ]
