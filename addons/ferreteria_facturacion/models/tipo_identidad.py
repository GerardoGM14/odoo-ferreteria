from odoo import models, fields


class TipoIdentidadSunat(models.Model):
    _name = 'sunat.tipo.identidad'
    _description = 'Tipo de Documento de Identidad SUNAT'
    _order = 'code'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código SUNAT', required=True, size=1)
    longitud = fields.Integer(
        string='Longitud',
        help='Cantidad de dígitos del documento (0 = variable)',
    )
    active = fields.Boolean(default=True)

    _sql_constraints = [
        ('code_unique', 'UNIQUE(code)', 'El código de identidad SUNAT debe ser único.'),
    ]
