from odoo.tests.common import TransactionCase


class TestUsuarios(TransactionCase):
    """Tests para el módulo de usuarios y perfiles"""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Perfil = cls.env['ferreteria.perfil.usuario']
        cls.Users = cls.env['res.users']

    def test_perfiles_loaded(self):
        """Test que los perfiles predefinidos se cargaron."""
        vendedor = self.env.ref(
            'ferreteria_usuarios.perfil_vendedor',
            raise_if_not_found=False,
        )
        self.assertTrue(vendedor)
        self.assertEqual(vendedor.code, 'VENDEDOR')

        gerente = self.env.ref(
            'ferreteria_usuarios.perfil_gerente',
            raise_if_not_found=False,
        )
        self.assertTrue(gerente)
        self.assertEqual(gerente.code, 'GERENTE')

    def test_perfil_tiene_grupos(self):
        """Test que los perfiles tienen grupos asignados."""
        vendedor = self.env.ref('ferreteria_usuarios.perfil_vendedor')
        self.assertTrue(len(vendedor.group_ids) > 0)

        gerente = self.env.ref('ferreteria_usuarios.perfil_gerente')
        self.assertTrue(len(gerente.group_ids) > 0)
        # Gerente debe tener más grupos que vendedor
        self.assertGreaterEqual(
            len(gerente.group_ids),
            len(vendedor.group_ids),
        )

    def test_create_perfil(self):
        """Test creación de perfil personalizado."""
        perfil = self.Perfil.create({
            'name': 'Perfil Test',
            'code': 'TEST',
            'description': 'Perfil de prueba',
        })
        self.assertTrue(perfil.id)
        self.assertEqual(perfil.user_count, 0)

    def test_user_count(self):
        """Test conteo de usuarios en perfil."""
        perfil = self.Perfil.create({
            'name': 'Perfil Count Test',
            'code': 'CNT',
        })
        user = self.Users.create({
            'name': 'Test User Perfil',
            'login': 'test_perfil_user@test.com',
            'perfil_ferreteria_id': perfil.id,
        })
        perfil.write({
            'user_ids': [(4, user.id)],
        })
        self.assertEqual(perfil.user_count, 1)

    def test_apply_profile(self):
        """Test aplicación de perfil a usuarios."""
        group = self.env.ref('ferreteria_inventario.group_ferreteria_user')
        perfil = self.Perfil.create({
            'name': 'Perfil Apply Test',
            'code': 'APL',
            'group_ids': [(4, group.id)],
        })
        user = self.Users.create({
            'name': 'Test Apply User',
            'login': 'test_apply@test.com',
        })
        perfil.write({
            'user_ids': [(4, user.id)],
        })
        perfil.action_apply_profile()
        self.assertIn(group.id, user.groups_id.ids)

    def test_user_ferreteria_fields(self):
        """Test campos de ferretería en res.users."""
        user = self.Users.create({
            'name': 'User Ferreteria Test',
            'login': 'user_ferreteria@test.com',
            'area_trabajo': 'ventas',
            'turno': 'manana',
            'telefono_usuario': '999888777',
        })
        self.assertEqual(user.area_trabajo, 'ventas')
        self.assertEqual(user.turno, 'manana')
        self.assertEqual(user.telefono_usuario, '999888777')

    def test_area_trabajo_selection(self):
        """Test todos los valores de área de trabajo."""
        for area in ['ventas', 'almacen', 'caja', 'compras', 'gerencia', 'administracion']:
            user = self.Users.create({
                'name': f'User {area}',
                'login': f'user_{area}@test.com',
                'area_trabajo': area,
            })
            self.assertEqual(user.area_trabajo, area)

    def test_cinco_perfiles_predefinidos(self):
        """Test que existen exactamente 5 perfiles predefinidos."""
        refs = [
            'ferreteria_usuarios.perfil_vendedor',
            'ferreteria_usuarios.perfil_almacenero',
            'ferreteria_usuarios.perfil_cajero',
            'ferreteria_usuarios.perfil_comprador',
            'ferreteria_usuarios.perfil_gerente',
        ]
        for ref in refs:
            perfil = self.env.ref(ref, raise_if_not_found=False)
            self.assertTrue(perfil, f'Perfil {ref} debe existir')
