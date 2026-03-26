from odoo import models, fields, tools


class FerreteriaKardex(models.Model):
    _name = 'ferreteria.kardex'
    _description = 'Kardex de Inventario'
    _auto = False
    _order = 'date desc, id desc'

    date = fields.Datetime(string='Fecha', readonly=True)
    product_id = fields.Many2one(
        'product.product',
        string='Producto',
        readonly=True,
    )
    product_tmpl_id = fields.Many2one(
        'product.template',
        string='Plantilla Producto',
        readonly=True,
    )
    ferreteria_categoria_id = fields.Many2one(
        'ferreteria.categoria',
        string='Categoría',
        readonly=True,
    )
    tipo_movimiento = fields.Selection([
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
    ], string='Tipo', readonly=True)
    quantity = fields.Float(string='Cantidad', readonly=True)
    reference = fields.Char(string='Referencia', readonly=True)
    location_id = fields.Many2one(
        'stock.location',
        string='Ubicación Origen',
        readonly=True,
    )
    location_dest_id = fields.Many2one(
        'stock.location',
        string='Ubicación Destino',
        readonly=True,
    )
    picking_id = fields.Many2one(
        'stock.picking',
        string='Transferencia',
        readonly=True,
    )

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    sml.id AS id,
                    sml.date AS date,
                    sml.product_id AS product_id,
                    pp.product_tmpl_id AS product_tmpl_id,
                    pt.ferreteria_categoria_id AS ferreteria_categoria_id,
                    CASE
                        WHEN sl_dest.usage = 'internal'
                             AND sl_src.usage != 'internal'
                            THEN 'entrada'
                        WHEN sl_src.usage = 'internal'
                             AND sl_dest.usage != 'internal'
                            THEN 'salida'
                        ELSE 'entrada'
                    END AS tipo_movimiento,
                    sml.quantity AS quantity,
                    sm.reference AS reference,
                    sml.location_id AS location_id,
                    sml.location_dest_id AS location_dest_id,
                    sm.picking_id AS picking_id
                FROM stock_move_line sml
                JOIN stock_move sm ON sm.id = sml.move_id
                JOIN product_product pp ON pp.id = sml.product_id
                JOIN product_template pt ON pt.id = pp.product_tmpl_id
                JOIN stock_location sl_src ON sl_src.id = sml.location_id
                JOIN stock_location sl_dest ON sl_dest.id = sml.location_dest_id
                WHERE sml.state = 'done'
                  AND pt.es_ferreteria = TRUE
                  AND (
                      (sl_dest.usage = 'internal' AND sl_src.usage != 'internal')
                      OR (sl_src.usage = 'internal' AND sl_dest.usage != 'internal')
                  )
            )
        """ % self._table)
