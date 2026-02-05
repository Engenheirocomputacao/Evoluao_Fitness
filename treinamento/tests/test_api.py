"""
Tests for treinamento API endpoints.
"""
from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from datetime import date
from decimal import Decimal
import json

from ..models import Individuo, Treinamento, RegistroTreinamento


class DashboardAPITest(TestCase):
    """Tests for dashboard API endpoint."""
    
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
        # Create some test data
        RegistroTreinamento.objects.create(
            individuo=self.individuo,
            treinamento=self.treinamento,
            data=date.today(),
            valor_alcançado=Decimal('5.50')
        )
    
    def test_dashboard_api_requires_login(self):
        """Test that dashboard API requires authentication."""
        response = self.client.get(reverse('dashboard_data_api'))
        self.assertEqual(response.status_code, 302)
    
    def test_dashboard_api_returns_json(self):
        """Test that dashboard API returns JSON."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard_data_api'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
    
    def test_dashboard_api_contains_stats(self):
        """Test that dashboard API contains stats."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard_data_api'))
        data = json.loads(response.content)
        
        self.assertIn('stats', data)
        self.assertIn('total_registros', data['stats'])
        self.assertIn('media_geral', data['stats'])
    
    def test_dashboard_api_with_period_filter(self):
        """Test dashboard API with period filter."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard_data_api') + '?period=30')
        self.assertEqual(response.status_code, 200)
    
    def test_dashboard_api_with_training_type_filter(self):
        """Test dashboard API with training type filter."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('dashboard_data_api') + '?training_type=Corrida')
        self.assertEqual(response.status_code, 200)


class CalendarAPITest(TestCase):
    """Tests for calendar API endpoint."""
    
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
            nome='Natação',
            unidade_medida='min'
        )
        RegistroTreinamento.objects.create(
            individuo=self.individuo,
            treinamento=self.treinamento,
            data=date.today(),
            valor_alcançado=Decimal('45.00')
        )
    
    def test_calendar_api_requires_login(self):
        """Test that calendar API requires authentication."""
        response = self.client.get(reverse('calendar_data_api'))
        self.assertEqual(response.status_code, 302)
    
    def test_calendar_api_returns_json(self):
        """Test that calendar API returns JSON."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('calendar_data_api'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/json')
    
    def test_calendar_api_contains_registros(self):
        """Test that calendar API contains registros."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('calendar_data_api'))
        data = json.loads(response.content)
        
        self.assertIn('month', data)
        self.assertIn('year', data)
        self.assertIn('registros', data)
    
    def test_calendar_api_with_month_filter(self):
        """Test calendar API with month filter."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('calendar_data_api') + '?month=12&year=2024')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertEqual(data['month'], 12)
        self.assertEqual(data['year'], 2024)
