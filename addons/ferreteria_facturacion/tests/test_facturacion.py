from odoo.tests.common import TransactionCase
from odoo.exceptions import UserError, ValidationError


class TestFacturacion(TransactionCase):
    """Tests para el módulo de facturación electrónica SUNAT"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.TipoDoc = cls.env['sunat.tipo.documento']
        cls.TipoId = cls.env['sunat.tipo.identidad']
        cls.SunatConfig = cls.env['sunat.config']
        cls.Serie = cls.env['sunat.serie.comprobante']
        cls.AccountMove = cls.env['account.move']

    def test_tipos_documento_loaded(self):
        """Test que los tipos de documento se cargaron."""
        factura = self.env.ref(
            'ferreteria_facturacion.tipo_doc_factura',
            raise_if_not_found=False,
        )
        self.assertTrue(factura)
        self.assertEqual(factura.code, '01')
        self.assertEqual(factura.name, 'Factura Electrónica')

        boleta = self.env.ref(
            'ferreteria_facturacion.tipo_doc_boleta',
            raise_if_not_found=False,
        )
        self.assertTrue(boleta)
        self.assertEqual(boleta.code, '03')

    def test_tipos_identidad_loaded(self):
        """Test que los tipos de identidad se cargaron."""
        ruc = self.TipoId.search([('code', '=', '6')], limit=1)
        self.assertTrue(ruc)
        self.assertIn('RUC', ruc.name)

        dni = self.TipoId.search([('code', '=', '1')], limit=1)
        self.assertTrue(dni)
        self.assertIn('DNI', dni.name)

    def test_series_loaded(self):
        """Test que las series se cargaron."""
        serie_f001 = self.env.ref(
            'ferreteria_facturacion.serie_factura_f001',
            raise_if_not_found=False,
        )
        self.assertTrue(serie_f001)
        self.assertEqual(serie_f001.name, 'F001')

    def test_serie_get_next_number(self):
        """Test generación de correlativo."""
        serie = self.Serie.create({
            'name': 'T001',
            'tipo_documento_id': self.env.ref(
                'ferreteria_facturacion.tipo_doc_factura',
            ).id,
        })
        num1 = serie.get_next_number()
        self.assertEqual(num1, 'T001-00000001')
        num2 = serie.get_next_number()
        self.assertEqual(num2, 'T001-00000002')
        self.assertEqual(serie.correlativo_actual, 2)

    def test_serie_proximo_numero(self):
        """Test campo computado próximo número."""
        serie = self.Serie.create({
            'name': 'T002',
            'tipo_documento_id': self.env.ref(
                'ferreteria_facturacion.tipo_doc_factura',
            ).id,
            'correlativo_actual': 99,
        })
        self.assertEqual(serie.proximo_numero, 'T002-00000100')

    def test_sunat_config_create(self):
        """Test creación de configuración SUNAT."""
        config = self.SunatConfig.create({
            'ruc_empresa': '20123456789',
            'razon_social': 'Ferretería Test SAC',
            'ambiente': 'beta',
            'usuario_sol': 'MODDATOS',
            'clave_sol': 'moddatos',
        })
        self.assertTrue(config.id)
        self.assertEqual(config.ambiente, 'beta')
        self.assertEqual(config.estado_conexion, 'sin_configurar')
        self.assertIn('beta', config.url_factura)

    def test_sunat_config_ruc_validation(self):
        """Test validación de RUC en configuración."""
        with self.assertRaises(ValidationError):
            self.SunatConfig.create({
                'ruc_empresa': '123',
                'razon_social': 'Test',
            })

    def test_sunat_config_ruc_prefix(self):
        """Test que RUC debe empezar con 10 o 20."""
        with self.assertRaises(ValidationError):
            self.SunatConfig.create({
                'ruc_empresa': '30123456789',
                'razon_social': 'Test',
            })

    def test_sunat_config_urls_produccion(self):
        """Test URLs de producción."""
        config = self.SunatConfig.create({
            'ruc_empresa': '20123456789',
            'razon_social': 'Test',
            'ambiente': 'produccion',
        })
        self.assertIn('e-factura', config.url_factura)
        self.assertNotIn('beta', config.url_factura)

    def test_account_move_sunat_fields(self):
        """Test que los campos SUNAT existen en account.move."""
        expected_fields = [
            'sunat_tipo_documento_id', 'sunat_serie_id',
            'sunat_numero', 'sunat_estado',
            'sunat_tipo_identidad_id', 'sunat_numero_identidad',
            'sunat_monto_gravado', 'sunat_monto_igv',
        ]
        for field_name in expected_fields:
            self.assertIn(
                field_name,
                self.AccountMove._fields,
                f'Campo {field_name} debe existir en account.move',
            )

    def test_sunat_estado_default(self):
        """Test estado SUNAT por defecto."""
        field = self.AccountMove._fields['sunat_estado']
        self.assertEqual(field.default, 'borrador')

    def test_generar_numero_sin_serie_error(self):
        """Test que generar número sin serie da error."""
        partner = self.env['res.partner'].create({'name': 'Test'})
        move = self.AccountMove.create({
            'move_type': 'out_invoice',
            'partner_id': partner.id,
        })
        with self.assertRaises(UserError):
            move.action_generar_numero()
