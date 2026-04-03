"""
Tests for treinamento views.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from django.utils import timezone

from ..models import Individuo, Treinamento, RegistroTreinamento


class AuthViewsTest(TestCase):
    """Tests for authentication views."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.individuo = Individuo.objects.create(
            user=self.user,
            nome_completo='Test User'
        )
    
    def test_login_page_loads(self):
        """Test that login page loads correctly."""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
    
    def test_register_page_loads(self):
        """Test that register page loads correctly."""
        response = self.client.get(reverse('register_view'))
        self.assertEqual(response.status_code, 200)
    
    def test_logout_requires_post(self):
        """Test that logout requires POST request."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('logout'))
        # Should redirect or fail for non-POST
        self.assertIn(response.status_code, [302, 405])


class DashboardViewsTest(TestCase):
    """Tests for dashboard views."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.individuo = Individuo.objects.create(
            user=self.user,
            nome_completo='Test User'
        )
    
    def test_home_page_loads_unauthenticated(self):
        """Test that home page loads for unauthenticated users."""
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
    
    def test_home_page_loads_authenticated(self):
        """Test that home page loads for authenticated users."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
    
    def test_dashboard_requires_login(self):
        """Test that dashboard requires authentication."""
        response = self.client.get(reverse('dashboard_view'))
        # Should redirect to login
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)
    
    def test_dashboard_loads_authenticated(self):
        """Test that dashboard loads for authenticated users."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard_view'))
        self.assertEqual(response.status_code, 200)


class RegistrosViewsTest(TestCase):
    """Tests for registros views."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.individuo = Individuo.objects.create(
            user=self.user,
            nome_completo='Test User'
        )
        self.treinamento = Treinamento.objects.create(
            nome='Corrida',
            unidade_medida='km'
        )
    
    def test_treinamentos_requires_login(self):
        """Test that treinamentos page requires authentication."""
        response = self.client.get(reverse('treinamentos_view'))
        self.assertEqual(response.status_code, 302)
    
    def test_treinamentos_loads_authenticated(self):
        """Test that treinamentos page loads for authenticated users."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('treinamentos_view'))
        self.assertEqual(response.status_code, 200)
    
    def test_registros_requires_login(self):
        """Test that registros page requires authentication."""
        response = self.client.get(reverse('registros_view'))
        self.assertEqual(response.status_code, 302)
    
    def test_registros_loads_authenticated(self):
        """Test that registros page loads for authenticated users."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('registros_view'))
        self.assertEqual(response.status_code, 200)


class PerfilViewsTest(TestCase):
    """Tests for perfil views."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.individuo = Individuo.objects.create(
            user=self.user,
            nome_completo='Test User'
        )
    
    def test_perfil_requires_login(self):
        """Test that perfil page requires authentication."""
        response = self.client.get(reverse('perfil_view'))
        self.assertEqual(response.status_code, 302)
    
    def test_perfil_loads_authenticated(self):
        """Test that perfil page loads for authenticated users."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('perfil_view'))
        self.assertEqual(response.status_code, 200)
    
    def test_calendar_requires_login(self):
        """Test that calendar page requires authentication."""
        response = self.client.get(reverse('calendar_view'))
        self.assertEqual(response.status_code, 302)
    
    def test_calendar_loads_authenticated(self):
        """Test that calendar page loads for authenticated users."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('calendar_view'))
        self.assertEqual(response.status_code, 200)


class RelatoriosViewsTest(TestCase):
    """Tests for relatorios views."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        self.individuo = Individuo.objects.create(
            user=self.user,
            nome_completo='Test User'
        )
    
    def test_relatorios_requires_login(self):
        """Test that relatorios page requires authentication."""
        response = self.client.get(reverse('relatorios_view'))
        self.assertEqual(response.status_code, 302)
    
    def test_relatorios_loads_authenticated(self):
        """Test that relatorios page loads for authenticated users."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('relatorios_view'))
        self.assertEqual(response.status_code, 200)
    
    def test_ranking_requires_login(self):
        """Test that ranking page requires authentication."""
        response = self.client.get(reverse('ranking_view'))
        self.assertEqual(response.status_code, 302)
    
    def test_ranking_loads_authenticated(self):
        """Test that ranking page loads for authenticated users."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('ranking_view'))
        self.assertEqual(response.status_code, 200)

    def test_ranking_uses_individuo_avatar(self):
        """Test that ranking view uses the individuo.avatar URL instead of unrelated avatars."""
        from django.core.files.uploadedfile import SimpleUploadedFile

        # Usuário atual
        self.client.login(username='testuser', password='testpass123')

        # Outro usuário com avatar específico
        user2 = User.objects.create_user(username='maria', password='pass123')
        avatar_file = SimpleUploadedFile('maria.jpg', b'content', content_type='image/jpeg')
        individuo2 = Individuo.objects.create(user=user2, nome_completo='Maria Silva', avatar=avatar_file)

        # Cria um treinamento e registros suficientes para entrar no ranking
        treinamento = Treinamento.objects.create(nome='TreinoX', unidade_medida='min')
        now = timezone.now().date()
        RegistroTreinamento.objects.create(individuo=self.individuo, treinamento=treinamento, data=now, valor_alcançado=10)
        RegistroTreinamento.objects.create(individuo=self.individuo, treinamento=treinamento, data=now, valor_alcançado=20)
        RegistroTreinamento.objects.create(individuo=self.individuo, treinamento=treinamento, data=now, valor_alcançado=30)
        RegistroTreinamento.objects.create(individuo=self.individuo, treinamento=treinamento, data=now, valor_alcançado=40)
        RegistroTreinamento.objects.create(individuo=self.individuo, treinamento=treinamento, data=now, valor_alcançado=50)

        RegistroTreinamento.objects.create(individuo=individuo2, treinamento=treinamento, data=now, valor_alcançado=100)
        RegistroTreinamento.objects.create(individuo=individuo2, treinamento=treinamento, data=now, valor_alcançado=100)
        RegistroTreinamento.objects.create(individuo=individuo2, treinamento=treinamento, data=now, valor_alcançado=100)
        RegistroTreinamento.objects.create(individuo=individuo2, treinamento=treinamento, data=now, valor_alcançado=100)
        RegistroTreinamento.objects.create(individuo=individuo2, treinamento=treinamento, data=now, valor_alcançado=100)

        response = self.client.get(reverse('ranking_view'))
        self.assertEqual(response.status_code, 200)

        ranking_geral = response.context['ranking_geral']
        found = next((item for item in ranking_geral if item['individuo__nome_completo'] == 'Maria Silva'), None)
        self.assertIsNotNone(found)
        self.assertEqual(found['avatar'], individuo2.avatar.url)
