{
    'name': 'Ferretería: Gestión de Compras',
    'version': '17.0.1.0.0',
    'summary': 'Compras, proveedores y control de abastecimiento para ferretería',
    'description': """
        Módulo de compras para ferreterías.
        - Gestión de proveedores con datos específicos
        - Solicitudes de cotización a proveedores
        - Órdenes de compra con actualización automática de stock
        - Control de precios de compra y comparación
        - Registro de proveedores por categoría de producto
        - Control de tiempos de entrega
    """,
    'author': 'Soporte',
    'website': 'https://www.example.com',
    'category': 'Purchase',
    'depends': [
        'ferreteria_inventario',
        'purchase',
    ],
    'data': [
        # Seguridad
        'security/compras_security.xml',
        'security/ir.model.access.csv',
        # Datos
        'data/compras_data.xml',
        # Vistas
        'views/res_partner_views.xml',
        'views/purchase_order_views.xml',
        'views/product_supplierinfo_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
