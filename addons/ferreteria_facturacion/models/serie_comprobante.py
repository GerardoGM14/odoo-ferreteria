from odoo import models, fields, api


class SerieComprobante(models.Model):
    _name = 'sunat.serie.comprobante'
    _description = 'Serie de Comprobante SUNAT'
    _order = 'tipo_documento_id, name'

    name = fields.Char(
        string='Serie',
        required=True,
        size=4,
        help='Serie del comprobante (ej: F001, B001, FC01, BC01)',
    )
    tipo_documento_id = fields.Many2one(
        'sunat.tipo.documento',
        string='Tipo de Documento',
        required=True,
    )
    correlativo_actual = fields.Integer(
        string='Último Correlativo',
        default=0,
        help='Último número correlativo utilizado',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        required=True,
        default=lambda self: self.env.company,
    )
    active = fields.Boolean(default=True)
    punto_emision = fields.Char(
        string='Punto de Emisión',
        help='Identificación del punto de emisión (ej: Caja 1, Mostrador)',
    )

    # Campo calculado: próximo número
    proximo_numero = fields.Char(
        string='Próximo Número',
        compute='_compute_proximo_numero',
    )

    @api.depends('name', 'correlativo_actual')
    def _compute_proximo_numero(self):
        for serie in self:
            next_num = serie.correlativo_actual + 1
            serie.proximo_numero = f'{serie.name}-{next_num:08d}'

    def get_next_number(self):
        """Obtiene y reserva el siguiente correlativo."""
        self.ensure_one()
        self.correlativo_actual += 1
        return f'{self.name}-{self.correlativo_actual:08d}'

    _sql_constraints = [
        ('serie_tipo_company_unique',
         'UNIQUE(name, tipo_documento_id, company_id)',
         'La serie debe ser única por tipo de documento y empresa.'),
    ]
