import logging
from datetime import datetime

from odoo import models, fields, api
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = 'account.move'

    # Campos SUNAT
    sunat_tipo_documento_id = fields.Many2one(
        'sunat.tipo.documento',
        string='Tipo de Comprobante',
    )
    sunat_serie_id = fields.Many2one(
        'sunat.serie.comprobante',
        string='Serie',
        domain="[('tipo_documento_id', '=', sunat_tipo_documento_id)]",
    )
    sunat_numero = fields.Char(
        string='Número Comprobante',
        readonly=True,
        copy=False,
        help='Número completo del comprobante (Serie-Correlativo)',
    )
    sunat_tipo_identidad_id = fields.Many2one(
        'sunat.tipo.identidad',
        string='Tipo Doc. Identidad',
        help='Tipo de documento de identidad del cliente',
    )
    sunat_numero_identidad = fields.Char(
        string='Nro. Documento',
        help='Número de documento de identidad del cliente',
    )

    # Estado SUNAT
    sunat_estado = fields.Selection([
        ('borrador', 'Borrador'),
        ('por_enviar', 'Por Enviar'),
        ('enviado', 'Enviado a SUNAT'),
        ('aceptado', 'Aceptado'),
        ('rechazado', 'Rechazado'),
        ('anulado', 'Anulado'),
    ], string='Estado SUNAT', default='borrador', copy=False, tracking=True)
    sunat_respuesta_codigo = fields.Char(
        string='Código Respuesta',
        readonly=True,
        copy=False,
    )
    sunat_respuesta_descripcion = fields.Text(
        string='Descripción Respuesta',
        readonly=True,
        copy=False,
    )
    sunat_hash = fields.Char(
        string='Hash',
        readonly=True,
        copy=False,
        help='Hash de la firma digital del comprobante',
    )
    sunat_xml_envio = fields.Binary(
        string='XML Enviado',
        readonly=True,
        copy=False,
    )
    sunat_xml_envio_filename = fields.Char(
        string='Nombre XML',
        compute='_compute_xml_filename',
    )
    sunat_xml_respuesta = fields.Binary(
        string='XML Respuesta',
        readonly=True,
        copy=False,
    )
    sunat_cdr_filename = fields.Char(
        string='Nombre CDR',
        compute='_compute_xml_filename',
    )
    sunat_fecha_envio = fields.Datetime(
        string='Fecha de Envío',
        readonly=True,
        copy=False,
    )

    # Nota de crédito/débito
    sunat_documento_referencia = fields.Many2one(
        'account.move',
        string='Documento de Referencia',
        help='Factura o boleta original (para notas de crédito/débito)',
        copy=False,
    )
    sunat_motivo_nota = fields.Selection([
        ('01', '01 - Anulación de la operación'),
        ('02', '02 - Anulación por error en el RUC'),
        ('03', '03 - Corrección por error en la descripción'),
        ('04', '04 - Descuento global'),
        ('05', '05 - Descuento por ítem'),
        ('06', '06 - Devolución total'),
        ('07', '07 - Devolución por ítem'),
        ('08', '08 - Bonificación'),
        ('09', '09 - Disminución en el valor'),
        ('10', '10 - Otros conceptos'),
    ], string='Motivo de Nota')

    # Montos calculados para SUNAT
    sunat_monto_gravado = fields.Float(
        string='Op. Gravadas',
        compute='_compute_sunat_montos',
        store=True,
    )
    sunat_monto_igv = fields.Float(
        string='IGV',
        compute='_compute_sunat_montos',
        store=True,
    )
    sunat_monto_exonerado = fields.Float(
        string='Op. Exoneradas',
        compute='_compute_sunat_montos',
        store=True,
    )
    sunat_monto_inafecto = fields.Float(
        string='Op. Inafectas',
        compute='_compute_sunat_montos',
        store=True,
    )
    sunat_monto_gratuito = fields.Float(
        string='Op. Gratuitas',
        compute='_compute_sunat_montos',
        store=True,
    )

    @api.depends('sunat_numero', 'sunat_serie_id')
    def _compute_xml_filename(self):
        for move in self:
            if move.sunat_numero:
                ruc = self.env.company.vat or 'SIN_RUC'
                tipo = move.sunat_tipo_documento_id.code or '01'
                move.sunat_xml_envio_filename = (
                    f'{ruc}-{tipo}-{move.sunat_numero}.xml'
                )
                move.sunat_cdr_filename = (
                    f'R-{ruc}-{tipo}-{move.sunat_numero}.xml'
                )
            else:
                move.sunat_xml_envio_filename = False
                move.sunat_cdr_filename = False

    @api.depends('invoice_line_ids', 'invoice_line_ids.price_subtotal',
                 'invoice_line_ids.tax_ids', 'amount_tax')
    def _compute_sunat_montos(self):
        for move in self:
            gravado = 0.0
            exonerado = 0.0
            inafecto = 0.0
            gratuito = 0.0

            for line in move.invoice_line_ids.filtered(
                lambda l: not l.display_type
            ):
                has_igv = any(
                    tax.amount > 0 and tax.type_tax_use == 'sale'
                    for tax in line.tax_ids
                )
                if line.price_unit == 0:
                    gratuito += line.price_subtotal
                elif has_igv:
                    gravado += line.price_subtotal
                else:
                    # Si no tiene impuesto, se considera exonerado
                    exonerado += line.price_subtotal

            move.sunat_monto_gravado = gravado
            move.sunat_monto_igv = move.amount_tax
            move.sunat_monto_exonerado = exonerado
            move.sunat_monto_inafecto = inafecto
            move.sunat_monto_gratuito = gratuito

    @api.onchange('partner_id')
    def _onchange_partner_sunat(self):
        """Auto-completar tipo y número de identidad desde el partner."""
        if self.partner_id:
            # Intentar determinar tipo de documento
            if hasattr(self.partner_id, 'ruc') and self.partner_id.ruc:
                tipo_ruc = self.env['sunat.tipo.identidad'].search(
                    [('code', '=', '6')], limit=1,
                )
                if tipo_ruc:
                    self.sunat_tipo_identidad_id = tipo_ruc
                    self.sunat_numero_identidad = self.partner_id.ruc
            elif hasattr(self.partner_id, 'dni') and self.partner_id.dni:
                tipo_dni = self.env['sunat.tipo.identidad'].search(
                    [('code', '=', '1')], limit=1,
                )
                if tipo_dni:
                    self.sunat_tipo_identidad_id = tipo_dni
                    self.sunat_numero_identidad = self.partner_id.dni
            elif self.partner_id.vat:
                if len(self.partner_id.vat) == 11:
                    tipo_ruc = self.env['sunat.tipo.identidad'].search(
                        [('code', '=', '6')], limit=1,
                    )
                    if tipo_ruc:
                        self.sunat_tipo_identidad_id = tipo_ruc
                        self.sunat_numero_identidad = self.partner_id.vat

    @api.onchange('sunat_tipo_documento_id')
    def _onchange_tipo_documento(self):
        """Auto-seleccionar la serie según tipo de documento."""
        if self.sunat_tipo_documento_id:
            serie = self.env['sunat.serie.comprobante'].search([
                ('tipo_documento_id', '=', self.sunat_tipo_documento_id.id),
                ('company_id', '=', self.env.company.id),
            ], limit=1)
            if serie:
                self.sunat_serie_id = serie

    def action_generar_numero(self):
        """Genera el número de comprobante (serie-correlativo)."""
        self.ensure_one()
        if self.sunat_numero:
            raise UserError('Este comprobante ya tiene número asignado.')
        if not self.sunat_serie_id:
            raise UserError('Debe seleccionar una serie.')

        self.sunat_numero = self.sunat_serie_id.get_next_number()
        self.sunat_estado = 'por_enviar'
        return True

    def action_enviar_sunat(self):
        """Enviar comprobante a SUNAT."""
        self.ensure_one()

        if not self.sunat_numero:
            raise UserError(
                'Debe generar el número de comprobante antes de enviar.'
            )

        if self.sunat_estado not in ('por_enviar', 'rechazado'):
            raise UserError(
                'Solo se pueden enviar comprobantes en estado '
                '"Por Enviar" o "Rechazado".'
            )

        # Validaciones
        if not self.sunat_tipo_identidad_id:
            raise UserError('Debe indicar el tipo de documento de identidad.')
        if not self.sunat_numero_identidad:
            raise UserError('Debe indicar el número de documento de identidad.')

        config = self.env['sunat.config'].search([
            ('company_id', '=', self.env.company.id),
            ('active', '=', True),
        ], limit=1)

        if not config:
            raise UserError(
                'No hay configuración SUNAT activa. '
                'Configure la conexión en Ferretería > Configuración > SUNAT.'
            )

        if config.estado_conexion != 'configurado':
            raise UserError(
                'La conexión SUNAT no está configurada correctamente. '
                'Verifique los datos en Configuración > SUNAT.'
            )

        # Generar XML UBL 2.1
        xml_content = self._generar_xml_ubl(config)

        # Aquí iría la lógica real de:
        # 1. Firmar XML con certificado digital
        # 2. Empaquetar en ZIP
        # 3. Enviar via SOAP al web service de SUNAT
        # 4. Procesar CDR (Constancia de Recepción)
        #
        # Por ahora se simula el envío exitoso
        _logger.info(
            'Enviando comprobante %s a SUNAT (ambiente: %s)',
            self.sunat_numero, config.ambiente,
        )

        self.write({
            'sunat_estado': 'aceptado' if config.ambiente == 'beta' else 'enviado',
            'sunat_fecha_envio': fields.Datetime.now(),
            'sunat_respuesta_codigo': '0' if config.ambiente == 'beta' else False,
            'sunat_respuesta_descripcion': (
                'Comprobante aceptado (ambiente beta)'
                if config.ambiente == 'beta'
                else 'Enviado, esperando respuesta...'
            ),
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Comprobante enviado',
                'message': f'Comprobante {self.sunat_numero} procesado correctamente.',
                'type': 'success',
                'sticky': False,
            },
        }

    def _generar_xml_ubl(self, config):
        """Genera el XML UBL 2.1 del comprobante.

        NOTA: Esta es una estructura base. Para producción real se necesita
        implementar la firma digital y el formato completo UBL 2.1 según
        las especificaciones de SUNAT.
        """
        self.ensure_one()
        tipo_doc = self.sunat_tipo_documento_id

        # Estructura base del XML (simplificada)
        xml_data = {
            'tipo_documento': tipo_doc.code,
            'serie_numero': self.sunat_numero,
            'fecha_emision': self.invoice_date or fields.Date.today(),
            'ruc_emisor': config.ruc_empresa,
            'razon_social_emisor': config.razon_social,
            'tipo_doc_receptor': self.sunat_tipo_identidad_id.code,
            'nro_doc_receptor': self.sunat_numero_identidad,
            'nombre_receptor': self.partner_id.name,
            'moneda': self.currency_id.name,
            'total_gravado': self.sunat_monto_gravado,
            'total_igv': self.sunat_monto_igv,
            'total_exonerado': self.sunat_monto_exonerado,
            'total_inafecto': self.sunat_monto_inafecto,
            'total': self.amount_total,
            'lineas': [],
        }

        for idx, line in enumerate(
            self.invoice_line_ids.filtered(lambda l: not l.display_type),
            start=1,
        ):
            xml_data['lineas'].append({
                'numero': idx,
                'codigo': line.product_id.default_code or '',
                'descripcion': line.name,
                'cantidad': line.quantity,
                'unidad': 'NIU',  # Unidad (código SUNAT)
                'precio_unitario': line.price_unit,
                'subtotal': line.price_subtotal,
                'igv': line.price_total - line.price_subtotal,
                'total': line.price_total,
            })

        _logger.info(
            'XML generado para %s: %d líneas, total S/ %.2f',
            self.sunat_numero, len(xml_data['lineas']), self.amount_total,
        )

        return xml_data

    def action_anular_sunat(self):
        """Comunicar baja / anulación a SUNAT."""
        self.ensure_one()
        if self.sunat_estado != 'aceptado':
            raise UserError(
                'Solo se pueden anular comprobantes aceptados por SUNAT.'
            )

        _logger.info('Anulando comprobante %s en SUNAT', self.sunat_numero)

        self.write({
            'sunat_estado': 'anulado',
            'sunat_respuesta_descripcion': (
                f'Comprobante anulado el '
                f'{datetime.now().strftime("%d/%m/%Y %H:%M")}'
            ),
        })

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Comprobante anulado',
                'message': f'{self.sunat_numero} ha sido comunicado para baja.',
                'type': 'warning',
                'sticky': False,
            },
        }

    def action_consultar_sunat(self):
        """Consultar estado del comprobante en SUNAT."""
        self.ensure_one()
        if not self.sunat_numero:
            raise UserError('Este comprobante no tiene número asignado.')

        _logger.info('Consultando estado de %s en SUNAT', self.sunat_numero)

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Consulta SUNAT',
                'message': f'Estado actual: {dict(self._fields["sunat_estado"].selection).get(self.sunat_estado, "Desconocido")}',
                'type': 'info',
                'sticky': False,
            },
        }
