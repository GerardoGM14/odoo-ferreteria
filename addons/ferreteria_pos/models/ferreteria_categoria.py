from odoo import models, fields, api


class FerreteriaCategoria(models.Model):
    """Extiende ferreteria.categoria para sincronizar automaticamente
    con pos.category, de modo que las categorias que el usuario crea
    en el modulo Ferreteria aparezcan tambien en el grid del POS sin
    trabajo manual.

    La sincronizacion es UNIDIRECCIONAL: cambios en ferreteria.categoria
    se propagan a pos.category, pero no al reves. Esto evita ciclos
    cuando el usuario edita una pos.category directamente.
    """
    _inherit = 'ferreteria.categoria'

    pos_category_id = fields.Many2one(
        'pos.category',
        string='Categoría POS espejo',
        readonly=True,
        copy=False,
        ondelete='set null',
        help='Categoría del punto de venta sincronizada automáticamente '
             'con esta categoría de ferretería. No editar manualmente.',
    )

    def _sync_pos_category_vals(self):
        """Construye el dict de valores para crear/actualizar la
        pos.category espejo a partir de los datos de esta ferreteria.categoria.
        """
        self.ensure_one()
        vals = {
            'name': self.name,
            'sequence': self.sequence,
        }
        # Imagen: pos.category usa image_128 (mismo nombre que nuestra categoria)
        if self.image_1920:
            vals['image_128'] = self.image_1920
        # Jerarquia: si esta categoria tiene padre y el padre ya tiene
        # su pos.category espejo, propagamos el parent_id
        if self.parent_id and self.parent_id.pos_category_id:
            vals['parent_id'] = self.parent_id.pos_category_id.id
        return vals

    def _sync_to_pos_category(self):
        """Crea o actualiza la pos.category espejo de cada ferreteria.categoria
        del recordset. Tambien resincroniza los productos que pertenecen a
        esta categoria para que su pos_categ_ids quede actualizado.
        """
        PosCategory = self.env['pos.category']
        for cat in self:
            vals = cat._sync_pos_category_vals()
            if cat.pos_category_id:
                cat.pos_category_id.write(vals)
            else:
                pos_cat = PosCategory.create(vals)
                # Usamos sudo + skip del recompute para no disparar
                # otra vez la propia sincronizacion en el write de cat
                cat.with_context(skip_pos_sync=True).write({
                    'pos_category_id': pos_cat.id,
                })
            # Asegurar que los productos asociados queden con la
            # pos_categ_ids correcta
            products = self.env['product.template'].search([
                ('ferreteria_categoria_id', '=', cat.id),
            ])
            if products:
                products._sync_pos_category_from_ferreteria()

    @api.model_create_multi
    def create(self, vals_list):
        """Al crear una ferreteria.categoria, crea su pos.category espejo."""
        records = super().create(vals_list)
        records._sync_to_pos_category()
        return records

    def write(self, vals):
        """Al editar una ferreteria.categoria, actualiza su pos.category espejo.
        Solo si los campos relevantes cambian, para no hacer escrituras
        inutiles.
        """
        res = super().write(vals)
        # Si esta llamada viene del propio sync (skip_pos_sync=True), no
        # reentramos para evitar bucles infinitos
        if self.env.context.get('skip_pos_sync'):
            return res
        sync_fields = {'name', 'sequence', 'image_1920', 'parent_id'}
        if sync_fields & set(vals.keys()):
            self._sync_to_pos_category()
        return res

    @api.model
    def _sync_existing_categories_to_pos(self):
        """Migracion: sincroniza todas las categorias existentes que aun
        no tienen pos.category espejo. Se llama una sola vez desde el
        post_init_hook del modulo ferreteria_pos.
        """
        # Primero las categorias raiz, luego las hijas, para que el
        # parent_id se propague correctamente
        roots = self.search([
            ('parent_id', '=', False),
            ('pos_category_id', '=', False),
        ])
        roots._sync_to_pos_category()
        children = self.search([
            ('parent_id', '!=', False),
            ('pos_category_id', '=', False),
        ])
        children._sync_to_pos_category()
