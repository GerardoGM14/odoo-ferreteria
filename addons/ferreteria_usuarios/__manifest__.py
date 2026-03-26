{
    'name': 'Ferretería: Usuarios y Seguridad',
    'version': '17.0.1.0.0',
    'summary': 'Perfiles de usuario, roles por área y control de acceso',
    'description': """
        Módulo de gestión de usuarios y seguridad para ferreterías.
        - Perfiles predefinidos por área (ventas, almacén, caja, gerencia)
        - Restricciones por módulo y funcionalidad
        - Dashboard de actividad por usuario
        - Control de sesiones activas
        - Configuración simplificada de permisos
    """,
    'author': 'Soporte',
    'website': 'https://www.example.com',
    'category': 'Administration',
    'depends': [
        'ferreteria_inventario',
        'ferreteria_ventas',
        'ferreteria_compras',
        'ferreteria_facturacion',
        'ferreteria_finanzas',
    ],
    'data': [
        # Seguridad
        'security/perfiles_security.xml',
        'security/ir.model.access.csv',
        # Datos
        'data/perfiles_data.xml',
        # Vistas
        'views/perfil_usuario_views.xml',
        'views/res_users_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
