from odoo import models, fields, api


class FerreteriaCategoria(models.Model):
    _name = 'ferreteria.categoria'
    _description = 'Categoría de Ferretería'
    _parent_name = 'parent_id'
    _parent_store = True
    _order = 'sequence, name'

    name = fields.Char(string='Nombre', required=True)
    code = fields.Char(string='Código', size=5)
    description = fields.Text(string='Descripción')
    parent_id = fields.Many2one(
        'ferreteria.categoria',
        string='Categoría Padre',
        index=True,
        ondelete='cascade',
    )
    parent_path = fields.Char(index=True, unaccent=False)
    child_ids = fields.One2many(
        'ferreteria.categoria',
        'parent_id',
        string='Subcategorías',
    )
    active = fields.Boolean(default=True)
    icon = fields.Char(
        string='Icono',
        help='Clase Font Awesome (ej: fa fa-wrench)',
    )
    sequence = fields.Integer(default=10)
    product_count = fields.Integer(
        string='Nro. Productos',
        compute='_compute_product_count',
    )

    @api.depends('name')
    def _compute_product_count(self):
        for cat in self:
            cat.product_count = self.env['product.template'].search_count([
                ('ferreteria_categoria_id', '=', cat.id),
            ])

    @api.constrains('parent_id')
    def _check_parent_recursion(self):
        if not self._check_recursion():
            raise models.ValidationError(
                'No se puede crear una categoría recursiva.'
            )

    def name_get(self):
        result = []
        for record in self:
            if record.parent_id:
                name = f'{record.parent_id.name} / {record.name}'
            else:
                name = record.name
            result.append((record.id, name))
        return result
