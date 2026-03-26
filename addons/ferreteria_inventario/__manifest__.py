{
    'name': 'Ferretería: Gestión de Inventario',
    'version': '17.0.2.0.0',
    'summary': 'Gestión de productos, categorías, kardex y alertas para ferretería',
    'description': """
        Módulo completo de inventario para ferreterías.
        - Extensión de productos con campos específicos de ferretería
        - Categorías dinámicas con jerarquía
        - Kardex de inventario en tiempo real
        - Alertas de stock mínimo
        - 3 listas de precios (Mayorista, Normal, Menudeo)
        - Roles de seguridad (Vendedor / Administrador)
    """,
    'author': 'Soporte',
    'website': 'https://www.example.com',
    'category': 'Inventory',
    'depends': ['base', 'stock', 'product', 'sale_management'],
    'data': [
        # Seguridad (grupos primero)
        'security/ferreteria_security.xml',
        'security/ir.model.access.csv',
        # Datos por defecto
        'data/ferreteria_categoria_data.xml',
        'data/product_pricelist_data.xml',
        'data/ferreteria_cron_data.xml',
        # Vistas
        'views/ferreteria_categoria_views.xml',
        'views/product_template_views.xml',
        'views/ferreteria_kardex_views.xml',
        'views/stock_alert_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': True,
    'license': 'LGPL-3',
}
