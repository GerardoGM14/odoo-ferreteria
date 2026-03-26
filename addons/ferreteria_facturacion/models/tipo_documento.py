from odoo import models, fields


class TipoDocumentoSunat(models.Model):
    _name = 'sunat.tipo.documento'
    _description = 'Tipo de Documento SUNAT'
    _order = 'code'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código SUNAT', required=True, size=2)
    active = fields.Boolean(default=True)
    genera_xml = fields.Boolean(
        string='Genera XML',
        default=True,
        help='Indica si este tipo de documento genera XML para SUNAT',
    )
    prefix = fields.Char(
        string='Prefijo Serie',
        help='Prefijo de serie (F para factura, B para boleta, etc.)',
    )
    nota_credito = fields.Boolean(
        string='Es Nota de Crédito',
        default=False,
    )
    nota_debito = fields.Boolean(
        string='Es Nota de Débito',
        default=False,
    )

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'El código SUNAT debe ser único.'),
    ]
