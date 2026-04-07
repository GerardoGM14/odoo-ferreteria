{
    'name': 'Ferretería: Gestión Financiera',
    'version': '17.0.1.0.0',
    'summary': 'Caja diaria, cuentas por cobrar/pagar, reportes financieros',
    'description': """
        Módulo financiero para ferreterías.
        - Control de caja diaria (apertura, cierre, arqueo)
        - Movimientos de caja (ingresos, egresos, gastos)
        - Cuentas por cobrar y pagar
        - Conciliación bancaria
        - Reportes: ganancia diaria, flujo de caja, resumen financiero
        - Integración con ventas, compras y facturación
    """,
    'author': 'Trigra',
    'website': 'https://trigra.com.pe',
    'category': 'Accounting',
    'depends': [
        'ferreteria_inventario',
        'ferreteria_facturacion',
        'account',
    ],
    'data': [
        # Seguridad
        'security/finanzas_security.xml',
        'security/ir.model.access.csv',
        # Datos
        'data/finanzas_data.xml',
        # Vistas
        'views/caja_diaria_views.xml',
        'views/movimiento_caja_views.xml',
        'views/cuenta_cobrar_views.xml',
        'views/reporte_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
