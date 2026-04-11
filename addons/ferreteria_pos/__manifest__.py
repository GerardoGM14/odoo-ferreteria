{
    'name': 'Ferretería: Integración Punto de Venta',
    'version': '17.0.1.0.0',
    'summary': 'Puente entre los módulos custom de ferretería y el POS de Odoo',
    'description': """
        Módulo puente que integra el Punto de Venta (POS) de Odoo con el
        resto de módulos custom de la ferretería.

        - Sincroniza automáticamente las categorías de ferretería
          (ferreteria.categoria) con las categorías del POS (pos.category)
        - Asigna automáticamente los productos de ferretería a su
          categoría POS correspondiente cuando se crean o editan
        - Configura el POS para usar por defecto la "Lista de Precios
          Ferretería" con sus reglas de volumen
        - Oculta el menú de Caja Diaria de ferreteria_finanzas para
          evitar duplicidad con la sesión de caja del POS
    """,
    'author': 'Trigra',
    'website': 'https://trigra.com.pe',
    'category': 'Point of Sale',
    'depends': [
        'ferreteria_inventario',
        'ferreteria_finanzas',
        'point_of_sale',
    ],
    'data': [
        'data/pos_config_data.xml',
        'views/ferreteria_categoria_views.xml',
        'views/ferreteria_finanzas_menu_hide.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
    'post_init_hook': 'post_init_hook',
}
