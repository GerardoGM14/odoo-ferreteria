from odoo import models, fields, api


class ResUsers(models.Model):
    _inherit = 'res.users'

    perfil_ferreteria_id = fields.Many2one(
        'ferreteria.perfil.usuario',
        string='Perfil Ferretería',
        help='Perfil predefinido para la ferretería',
    )
    area_trabajo = fields.Selection([
        ('ventas', 'Ventas'),
        ('almacen', 'Almacén'),
        ('caja', 'Caja'),
        ('compras', 'Compras'),
        ('gerencia', 'Gerencia'),
        ('administracion', 'Administración'),
    ], string='Área de Trabajo')
    turno = fields.Selection([
        ('manana', 'Mañana'),
        ('tarde', 'Tarde'),
        ('completo', 'Tiempo Completo'),
    ], string='Turno', default='completo')
    telefono_usuario = fields.Char(string='Teléfono')
    notas_usuario = fields.Text(
        string='Notas',
        help='Notas internas sobre el usuario',
    )

    @api.onchange('perfil_ferreteria_id')
    def _onchange_perfil_ferreteria(self):
        """Aplicar grupos del perfil al cambiar."""
        if self.perfil_ferreteria_id:
            self.groups_id = [
                (4, group.id)
                for group in self.perfil_ferreteria_id.group_ids
            ]
