from . import models


def post_init_hook(env):
    """Al instalar ferreteria_pos, migrar las categorias y productos
    existentes para que se reflejen en el POS automaticamente.

    1. Sincroniza todas las ferreteria.categoria existentes con
       pos.category (crea las espejos).
    2. Marca todos los productos es_ferreteria=True como disponibles
       en POS y les asigna la pos_categ_ids correspondiente.
    """
    env['ferreteria.categoria']._sync_existing_categories_to_pos()
    env['product.template']._sync_existing_products_to_pos()
