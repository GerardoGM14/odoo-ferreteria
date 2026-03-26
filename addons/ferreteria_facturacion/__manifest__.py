{
    'name': 'Ferretería: Facturación Electrónica SUNAT',
    'version': '17.0.1.0.0',
    'summary': 'Facturación electrónica para SUNAT - Perú',
    'description': """
        Módulo de facturación electrónica para ferreterías en Perú.
        - Emisión de Facturas Electrónicas (01)
        - Emisión de Boletas de Venta (03)
        - Notas de Crédito (07) y Débito (08)
        - Series y correlativos por tipo de documento
        - Configuración de conexión SUNAT (Beta/Producción)
        - Registro de estados de envío a SUNAT
        - Generación de XML según estándar UBL 2.1
        - Consulta de validez de comprobantes
        - Tipos de documento de identidad (RUC, DNI, CE, etc.)
        - IGV, ISC y otros tributos peruanos
    """,
    'author': 'Soporte',
    'website': 'https://www.example.com',
    'category': 'Accounting',
    'depends': [
        'ferreteria_inventario',
        'account',
    ],
    'data': [
        # Seguridad
        'security/facturacion_security.xml',
        'security/ir.model.access.csv',
        # Datos
        'data/tipo_documento_data.xml',
        'data/tipo_identidad_data.xml',
        'data/serie_data.xml',
        # Vistas
        'views/sunat_config_views.xml',
        'views/serie_comprobante_views.xml',
        'views/account_move_views.xml',
        'views/menu_views.xml',
    ],
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
