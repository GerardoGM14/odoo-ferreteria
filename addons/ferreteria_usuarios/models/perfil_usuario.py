from odoo import models, fields, api


class PerfilUsuario(models.Model):
    _name = 'ferreteria.perfil.usuario'
    _description = 'Perfil de Usuario Ferretería'
    _order = 'sequence, name'

    name = fields.Char(string='Nombre del Perfil', required=True)
    code = fields.Char(string='Código', size=10)
    description = fields.Text(string='Descripción')
    sequence = fields.Integer(default=10)
    active = fields.Boolean(default=True)
    color = fields.Integer(string='Color')

    # Grupos que incluye este perfil
    group_ids = fields.Many2many(
        'res.groups',
        'perfil_usuario_groups_rel',
        'perfil_id',
        'group_id',
        string='Grupos de Seguridad',
        help='Grupos que se asignarán automáticamente al usuario con este perfil',
    )

    # Usuarios asignados
    user_ids = fields.Many2many(
        'res.users',
        'perfil_usuario_users_rel',
        'perfil_id',
        'user_id',
        string='Usuarios Asignados',
    )
    user_count = fields.Integer(
        string='Nro. Usuarios',
        compute='_compute_user_count',
    )

    # Restricciones
    modulos_acceso = fields.Text(
        string='Módulos con Acceso',
        help='Descripción de los módulos a los que tiene acceso este perfil',
    )
    restricciones = fields.Text(
        string='Restricciones',
        help='Restricciones específicas de este perfil',
    )

    @api.depends('user_ids')
    def _compute_user_count(self):
        for perfil in self:
            perfil.user_count = len(perfil.user_ids)

    def action_apply_profile(self):
        """Aplicar los grupos de este perfil a todos los usuarios asignados."""
        self.ensure_one()
        for user in self.user_ids:
            # Agregar los grupos del perfil al usuario
            user.write({
                'groups_id': [(4, group.id) for group in self.group_ids],
            })
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Perfil aplicado',
                'message': f'Se aplicaron los permisos a {len(self.user_ids)} usuario(s).',
                'type': 'success',
                'sticky': False,
            },
        }

    def action_view_users(self):
        """Ver usuarios de este perfil."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'name': f'Usuarios - {self.name}',
            'res_model': 'res.users',
            'view_mode': 'tree,form',
            'domain': [('id', 'in', self.user_ids.ids)],
        }
