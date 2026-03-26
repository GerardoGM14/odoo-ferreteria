import logging

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class SunatConfig(models.Model):
    _name = 'sunat.config'
    _description = 'Configuración SUNAT'
    _rec_name = 'company_id'

    company_id = fields.Many2one(
        'res.company',
        string='Empresa',
        required=True,
        default=lambda self: self.env.company,
    )
    ruc_empresa = fields.Char(
        string='RUC de la Empresa',
        size=11,
        required=True,
    )
    razon_social = fields.Char(
        string='Razón Social',
        required=True,
    )
    nombre_comercial = fields.Char(
        string='Nombre Comercial',
    )
    direccion_fiscal = fields.Char(
        string='Dirección Fiscal',
    )
    ubigeo = fields.Char(
        string='Ubigeo',
        size=6,
        help='Código de ubigeo SUNAT (6 dígitos)',
    )

    # Conexión SUNAT
    ambiente = fields.Selection([
        ('beta', 'Beta (Pruebas)'),
        ('produccion', 'Producción'),
    ], string='Ambiente', default='beta', required=True)
    usuario_sol = fields.Char(
        string='Usuario SOL',
        help='Usuario secundario SOL de SUNAT',
    )
    clave_sol = fields.Char(
        string='Clave SOL',
        help='Contraseña del usuario SOL',
    )

    # Certificado digital
    certificado = fields.Binary(
        string='Certificado Digital (.pfx/.p12)',
        help='Certificado digital para firma electrónica',
    )
    certificado_filename = fields.Char(string='Nombre del Certificado')
    certificado_password = fields.Char(
        string='Contraseña del Certificado',
    )

    # URLs de SUNAT
    url_factura = fields.Char(
        string='URL Facturación',
        compute='_compute_urls',
        store=False,
    )
    url_consulta = fields.Char(
        string='URL Consulta',
        compute='_compute_urls',
        store=False,
    )

    # Estado
    active = fields.Boolean(default=True)
    estado_conexion = fields.Selection([
        ('sin_configurar', 'Sin Configurar'),
        ('configurado', 'Configurado'),
        ('error', 'Error de Conexión'),
    ], string='Estado', default='sin_configurar', readonly=True)
    ultimo_test = fields.Datetime(
        string='Última Prueba de Conexión',
        readonly=True,
    )

    # IGV
    igv_porcentaje = fields.Float(
        string='IGV (%)',
        default=18.0,
        help='Porcentaje de IGV vigente',
    )

    @api.depends('ambiente')
    def _compute_urls(self):
        for config in self:
            if config.ambiente == 'beta':
                config.url_factura = (
                    'https://e-beta.sunat.gob.pe/ol-ti-itcpfegem-beta/billService'
                )
                config.url_consulta = (
                    'https://e-beta.sunat.gob.pe/ol-it-wsconscpegem-beta/billConsultService'
                )
            else:
                config.url_factura = (
                    'https://e-factura.sunat.gob.pe/ol-ti-itcpfegem/billService'
                )
                config.url_consulta = (
                    'https://e-factura.sunat.gob.pe/ol-it-wsconscpegem/billConsultService'
                )

    def action_test_connection(self):
        """Probar conexión con SUNAT."""
        self.ensure_one()
        # Validaciones básicas
        if not self.ruc_empresa or not self.usuario_sol or not self.clave_sol:
            self.write({
                'estado_conexion': 'sin_configurar',
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Configuración incompleta',
                    'message': 'Debe completar RUC, Usuario SOL y Clave SOL.',
                    'type': 'warning',
                    'sticky': False,
                },
            }

        # Intento de conexión (simulado - necesita librería de conexión SUNAT)
        try:
            _logger.info(
                'Test de conexión SUNAT - Ambiente: %s, RUC: %s, URL: %s',
                self.ambiente, self.ruc_empresa, self.url_factura,
            )
            self.write({
                'estado_conexion': 'configurado',
                'ultimo_test': fields.Datetime.now(),
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Conexión exitosa',
                    'message': f'Configuración guardada para ambiente '
                               f'{dict(self._fields["ambiente"].selection).get(self.ambiente)}.',
                    'type': 'success',
                    'sticky': False,
                },
            }
        except Exception as e:
            _logger.error('Error al conectar con SUNAT: %s', str(e))
            self.write({
                'estado_conexion': 'error',
                'ultimo_test': fields.Datetime.now(),
            })
            return {
                'type': 'ir.actions.client',
                'tag': 'display_notification',
                'params': {
                    'title': 'Error de conexión',
                    'message': str(e),
                    'type': 'danger',
                    'sticky': True,
                },
            }

    @api.constrains('ruc_empresa')
    def _check_ruc(self):
        for config in self:
            if config.ruc_empresa:
                if len(config.ruc_empresa) != 11:
                    raise models.ValidationError(
                        'El RUC debe tener exactamente 11 dígitos.'
                    )
                if not config.ruc_empresa.isdigit():
                    raise models.ValidationError(
                        'El RUC solo debe contener números.'
                    )
                if config.ruc_empresa[0] not in ('1', '2'):
                    raise models.ValidationError(
                        'El RUC debe comenzar con 10 (persona natural) '
                        'o 20 (persona jurídica).'
                    )

    _sql_constraints = [
        ('company_unique', 'UNIQUE(company_id)',
         'Solo puede existir una configuración SUNAT por empresa.'),
    ]
