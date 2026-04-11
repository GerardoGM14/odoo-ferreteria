from odoo import models, api


class ProductTemplate(models.Model):
    """Extiende product.template para que los productos de ferreteria
    aparezcan automaticamente en el POS, agrupados por la categoria
    POS espejo de su ferreteria.categoria.
    """
    _inherit = 'product.template'

    def _sync_pos_category_from_ferreteria(self):
        """Para cada producto del recordset, asigna como pos_categ_ids
        la pos.category espejo de su ferreteria_categoria_id.
        Tambien marca el producto como disponible en POS.
        """
        for product in self:
            if not product.es_ferreteria:
                continue
            # Marcar como disponible en POS por defecto
            vals = {'available_in_pos': True}
            # Si tiene categoria de ferreteria con espejo POS, asignarla
            if product.ferreteria_categoria_id and \
                    product.ferreteria_categoria_id.pos_category_id:
                pos_cat = product.ferreteria_categoria_id.pos_category_id
                # pos_categ_ids es Many2many, lo seteamos con [(6, 0, [ids])]
                vals['pos_categ_ids'] = [(6, 0, [pos_cat.id])]
            product.write(vals)

    @api.model_create_multi
    def create(self, vals_list):
        """Al crear productos, sincroniza la categoria POS si es de ferreteria."""
        records = super().create(vals_list)
        records.filtered('es_ferreteria')._sync_pos_category_from_ferreteria()
        return records

    def write(self, vals):
        """Al editar un producto, si cambia su ferreteria_categoria_id o
        es_ferreteria, resincroniza con POS.
        """
        res = super().write(vals)
        sync_triggers = {'ferreteria_categoria_id', 'es_ferreteria'}
        if sync_triggers & set(vals.keys()):
            self.filtered('es_ferreteria')._sync_pos_category_from_ferreteria()
        return res

    @api.model
    def _sync_existing_products_to_pos(self):
        """Migracion: para todos los productos es_ferreteria=True ya
        existentes, los marca como disponibles en POS y les asigna su
        pos_categ_ids. Se llama una sola vez desde el post_init_hook.
        """
        products = self.search([('es_ferreteria', '=', True)])
        products._sync_pos_category_from_ferreteria()
