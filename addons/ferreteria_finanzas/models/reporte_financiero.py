from odoo import models, fields, tools


class ReporteVentasDiarias(models.Model):
    _name = 'ferreteria.reporte.ventas.diarias'
    _description = 'Reporte de Ventas Diarias'
    _auto = False
    _order = 'fecha desc'

    fecha = fields.Date(string='Fecha', readonly=True)
    total_ventas = fields.Float(string='Total Ventas (S/)', readonly=True)
    cantidad_ordenes = fields.Integer(string='Nro. Órdenes', readonly=True)
    ticket_promedio = fields.Float(string='Ticket Promedio', readonly=True)
    vendedor_id = fields.Many2one('res.users', string='Vendedor', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    MIN(so.id) AS id,
                    so.date_order::date AS fecha,
                    SUM(so.amount_total) AS total_ventas,
                    COUNT(so.id) AS cantidad_ordenes,
                    CASE
                        WHEN COUNT(so.id) > 0
                        THEN SUM(so.amount_total) / COUNT(so.id)
                        ELSE 0
                    END AS ticket_promedio,
                    so.user_id AS vendedor_id
                FROM sale_order so
                WHERE so.state IN ('sale', 'done')
                GROUP BY so.date_order::date, so.user_id
            )
        """ % self._table)


class ReporteFlujoCaja(models.Model):
    _name = 'ferreteria.reporte.flujo.caja'
    _description = 'Reporte de Flujo de Caja'
    _auto = False
    _order = 'fecha desc'

    fecha = fields.Date(string='Fecha', readonly=True)
    total_ingresos = fields.Float(string='Ingresos', readonly=True)
    total_egresos = fields.Float(string='Egresos', readonly=True)
    flujo_neto = fields.Float(string='Flujo Neto', readonly=True)
    categoria = fields.Char(string='Categoría', readonly=True)
    metodo_pago = fields.Char(string='Método de Pago', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    mc.id AS id,
                    mc.fecha::date AS fecha,
                    CASE WHEN mc.tipo = 'ingreso' THEN mc.monto ELSE 0 END
                        AS total_ingresos,
                    CASE WHEN mc.tipo = 'egreso' THEN mc.monto ELSE 0 END
                        AS total_egresos,
                    CASE
                        WHEN mc.tipo = 'ingreso' THEN mc.monto
                        ELSE -mc.monto
                    END AS flujo_neto,
                    mc.categoria AS categoria,
                    mc.metodo_pago AS metodo_pago
                FROM ferreteria_movimiento_caja mc
            )
        """ % self._table)


class ReporteCuentasCobrar(models.Model):
    _name = 'ferreteria.reporte.cuentas.cobrar'
    _description = 'Reporte de Cuentas por Cobrar'
    _auto = False
    _order = 'dias_mora desc'

    partner_id = fields.Many2one('res.partner', string='Cliente', readonly=True)
    total_deuda = fields.Float(string='Total Deuda', readonly=True)
    total_pagado = fields.Float(string='Total Pagado', readonly=True)
    saldo_pendiente = fields.Float(string='Saldo Pendiente', readonly=True)
    cantidad_cuentas = fields.Integer(string='Nro. Cuentas', readonly=True)
    dias_mora = fields.Integer(string='Mayor Días Mora', readonly=True)

    def init(self):
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    MIN(cc.id) AS id,
                    cc.partner_id AS partner_id,
                    SUM(cc.monto_total) AS total_deuda,
                    SUM(cc.monto_pagado) AS total_pagado,
                    SUM(cc.monto_pendiente) AS saldo_pendiente,
                    COUNT(cc.id) AS cantidad_cuentas,
                    MAX(
                        CASE
                            WHEN cc.state IN ('pendiente', 'parcial', 'vencida')
                                 AND cc.fecha_vencimiento < CURRENT_DATE
                            THEN CURRENT_DATE - cc.fecha_vencimiento
                            ELSE 0
                        END
                    ) AS dias_mora
                FROM ferreteria_cuenta_cobrar cc
                WHERE cc.state != 'cancelada'
                GROUP BY cc.partner_id
            )
        """ % self._table)
