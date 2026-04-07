{
    'name': 'Ferretería: Gestión de Ventas',
    'version': '17.0.1.0.0',
    'summary': 'Ventas, cotizaciones, clientes y POS para ferretería',
    'description': """
        Módulo de ventas para ferreterías.
        - Importación masiva de productos desde Excel
        - Cotizaciones y órdenes de venta adaptadas
        - Gestión de clientes con historial de compras
        - Control de 4 listas de precios por volumen
        - Descuentos autorizados por grupo
        - Integración con inventario de ferretería
    """,
    'author': 'Trigra',
    'website': 'https://trigra.com.pe',
    'category': 'Sales',
    'depends': [
        'ferreteria_inventario',
        'sale_management',
        'contacts',
    ],
    'data': [
        # Seguridad
        'security/ventas_security.xml',
        'security/ir.model.access.csv',
        # Datos
        'data/descuento_data.xml',
        # Vistas
        'views/res_partner_views.xml',
        'views/sale_order_views.xml',
        # Wizards (deben cargarse antes que el menú que los referencia)
        'wizard/import_productos_wizard_views.xml',
        'views/menu_views.xml',
    ],
    'external_dependencies': {
        'python': ['openpyxl'],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
