from odoo import models, fields, api


class FerreteriaBienvenida(models.TransientModel):
    """Pantalla de bienvenida del modulo Ferreteria.

    Es transient (se autoborra) porque no necesita persistir nada:
    cada vez que el usuario abre el menu Ferreteria, se crea un
    registro en blanco que sirve de "lienzo" para mostrar las
    estadisticas y los pasos de onboarding.
    """
    _name = 'ferreteria.bienvenida'
    _description = 'Bienvenida Ferreteria'

    # Estadisticas vivas que mostramos en el dashboard
    productos_count = fields.Integer(
        string='Productos creados',
        compute='_compute_stats',
    )
    categorias_count = fields.Integer(
        string='Categorias creadas',
        compute='_compute_stats',
    )
    productos_bajo_stock = fields.Integer(
        string='Productos bajo stock minimo',
        compute='_compute_stats',
    )
    cajas_abiertas = fields.Integer(
        string='Cajas abiertas hoy',
        compute='_compute_stats',
    )

    def _compute_stats(self):
        Product = self.env['product.template']
        Categoria = self.env['ferreteria.categoria']
        for rec in self:
            rec.productos_count = Product.search_count([
                ('es_ferreteria', '=', True),
            ])
            rec.categorias_count = Categoria.search_count([])
            rec.productos_bajo_stock = Product.search_count([
                ('es_ferreteria', '=', True),
                ('stock_bajo_minimo', '=', True),
            ])
            # ferreteria.caja.diaria es de finanzas, puede no estar instalado
            CajaDiaria = self.env.get('ferreteria.caja.diaria')
            if CajaDiaria is not None:
                rec.cajas_abiertas = CajaDiaria.search_count([
                    ('state', '=', 'abierta'),
                ])
            else:
                rec.cajas_abiertas = 0

    @api.model
    def action_abrir_bienvenida(self):
        """Crea un registro transient en blanco y lo abre en form view."""
        record = self.create({})
        return {
            'type': 'ir.actions.act_window',
            'name': 'Bienvenido a Ferreteria',
            'res_model': self._name,
            'res_id': record.id,
            'view_mode': 'form',
            'view_id': self.env.ref(
                'ferreteria_inventario.view_ferreteria_bienvenida_form'
            ).id,
            'target': 'inline',
        }

    # ----- Acciones de los botones del dashboard -----

    def action_ir_categorias(self):
        return self.env.ref(
            'ferreteria_inventario.action_ferreteria_categoria'
        ).read()[0]

    def action_ir_productos(self):
        return self.env.ref(
            'ferreteria_inventario.action_ferreteria_productos'
        ).read()[0]

    def action_ir_stock(self):
        return self.env.ref('stock.dashboard_open_quants').read()[0]

    def action_ir_alertas(self):
        return self.env.ref(
            'ferreteria_inventario.action_stock_alert'
        ).read()[0]
