import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class ProductTemplate(models.Model):
    _inherit = 'product.template'

    es_ferreteria = fields.Boolean(
        string='Producto de Ferretería',
        default=False,
    )
    ferreteria_categoria_id = fields.Many2one(
        'ferreteria.categoria',
        string='Categoría Ferretería',
        index=True,
        ondelete='set null',
    )
    stock_minimo = fields.Float(
        string='Stock Mínimo',
        default=0.0,
        help='Cantidad mínima antes de generar alerta',
    )
    ubicacion_almacen = fields.Char(
        string='Ubicación en Almacén',
        help='Zona, pasillo o estante donde se encuentra el producto',
    )
    marca = fields.Char(string='Marca')
    unidad_ferreteria = fields.Selection([
        ('unidad', 'Unidad'),
        ('metro', 'Metro'),
        ('kilo', 'Kilo'),
        ('litro', 'Litro'),
        ('rollo', 'Rollo'),
        ('caja', 'Caja'),
        ('bolsa', 'Bolsa'),
        ('par', 'Par'),
    ], string='Unidad Ferretería', default='unidad')

    stock_bajo_minimo = fields.Boolean(
        string='Stock Bajo Mínimo',
        compute='_compute_stock_bajo_minimo',
        search='_search_stock_bajo_minimo',
        store=False,
    )

    @api.depends('qty_available', 'stock_minimo', 'es_ferreteria')
    def _compute_stock_bajo_minimo(self):
        for product in self:
            product.stock_bajo_minimo = (
                product.es_ferreteria
                and product.stock_minimo > 0
                and product.qty_available <= product.stock_minimo
            )

    def _search_stock_bajo_minimo(self, operator, value):
        products = self.search([
            ('es_ferreteria', '=', True),
            ('stock_minimo', '>', 0),
        ])
        below = products.filtered(lambda p: p.qty_available <= p.stock_minimo)
        if (operator == '=' and value) or (operator == '!=' and not value):
            return [('id', 'in', below.ids)]
        return [('id', 'not in', below.ids)]

    def _cron_check_stock_minimo(self):
        """Cron job para verificar productos con stock bajo mínimo."""
        products = self.search([
            ('es_ferreteria', '=', True),
            ('stock_minimo', '>', 0),
        ])
        below = products.filtered(lambda p: p.qty_available <= p.stock_minimo)
        if below:
            product_list = ', '.join(below.mapped('name'))
            _logger.warning(
                'Alerta de Stock Mínimo - Productos con stock bajo: %s',
                product_list,
            )
            # Crear actividad para el grupo administrador
            manager_group = self.env.ref(
                'ferreteria_inventario.group_ferreteria_manager',
                raise_if_not_found=False,
            )
            if manager_group and manager_group.users:
                for product in below:
                    product.activity_schedule(
                        'mail.mail_activity_data_warning',
                        user_id=manager_group.users[0].id,
                        note=f'El producto "{product.name}" tiene stock '
                             f'({product.qty_available}) por debajo del '
                             f'mínimo ({product.stock_minimo}).',
                        summary='Alerta: Stock Bajo Mínimo',
                    )
