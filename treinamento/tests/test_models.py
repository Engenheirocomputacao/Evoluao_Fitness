"""
Tests for treinamento models.
"""
from django.test import TestCase
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import date, timedelta
from decimal import Decimal

from ..models import Individuo, Treinamento, RegistroTreinamento, LetterCaptcha


class IndividuoModelTest(TestCase):
    """Tests for Individuo model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
    
    def test_individuo_creation(self):
        """Test that an Individuo can be created."""
        individuo = Individuo.objects.create(
            user=self.user,
            nome_completo='João Silva'
        )
        self.assertEqual(individuo.nome_completo, 'João Silva')
        self.assertTrue(individuo.ativo)
        self.assertIsNone(individuo.data_nascimento)
    
    def test_individuo_str(self):
        """Test string representation of Individuo."""
        individuo = Individuo.objects.create(
            user=self.user,
            nome_completo='Maria Santos'
        )
        self.assertEqual(str(individuo), 'Maria Santos')
    
    def test_individuo_with_birth_date(self):
        """Test Individuo with birth date."""
        individuo = Individuo.objects.create(
            user=self.user,
            nome_completo='Carlos Souza',
            data_nascimento=date(1990, 5, 15)
        )
        self.assertEqual(individuo.data_nascimento, date(1990, 5, 15))


class TreinamentoModelTest(TestCase):
    """Tests for Treinamento model."""
    
    def test_treinamento_creation(self):
        """Test that a Treinamento can be created."""
        treinamento = Treinamento.objects.create(
            nome='Corrida',
            unidade_medida='km',
            descricao='Corrida ao ar livre'
        )
        self.assertEqual(treinamento.nome, 'Corrida')
        self.assertEqual(treinamento.unidade_medida, 'km')
    
    def test_treinamento_str(self):
        """Test string representation of Treinamento."""
        treinamento = Treinamento.objects.create(
            nome='Musculação',
            unidade_medida='min'
        )
        self.assertEqual(str(treinamento), 'Musculação (min)')
    
    def test_treinamento_unique_nome(self):
        """Test that treinamento nome must be unique."""
        Treinamento.objects.create(
            nome='Natação',
            unidade_medida='min'
        )
        with self.assertRaises(Exception):
            Treinamento.objects.create(
                nome='Natação',
                unidade_medida='km'
            )
    
    def test_treinamento_unidade_choices(self):
        """Test valid unidade_medida choices."""
        valid_choices = ['min', 'km', 'kg', 'rep', 'out']
        for choice in valid_choices:
            treinamento = Treinamento.objects.create(
                nome=f'Treino {choice}',
                unidade_medida=choice
            )
            self.assertEqual(treinamento.unidade_medida, choice)


class RegistroTreinamentoModelTest(TestCase):
    """Tests for RegistroTreinamento model."""
    
    def setUp(self):
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
    
    def test_registro_creation(self):
        """Test that a RegistroTreinamento can be created."""
        registro = RegistroTreinamento.objects.create(
            individuo=self.individuo,
            treinamento=self.treinamento,
            data=date.today(),
            valor_alcançado=Decimal('5.50')
        )
        self.assertEqual(registro.valor_alcançado, Decimal('5.50'))
    
    def test_registro_str(self):
        """Test string representation of RegistroTreinamento."""
        registro = RegistroTreinamento.objects.create(
            individuo=self.individuo,
            treinamento=self.treinamento,
            data=date.today(),
            valor_alcançado=Decimal('10.00')
        )
        self.assertIn('Corrida', str(registro))
        self.assertIn('Test User', str(registro))
    
    def test_registro_unique_together(self):
        """Test that same individuo+treinamento+data is unique."""
        RegistroTreinamento.objects.create(
            individuo=self.individuo,
            treinamento=self.treinamento,
            data=date.today(),
            valor_alcançado=Decimal('5.00')
        )
        with self.assertRaises(Exception):
            RegistroTreinamento.objects.create(
                individuo=self.individuo,
                treinamento=self.treinamento,
                data=date.today(),
                valor_alcançado=Decimal('10.00')
            )
    
    def test_registro_ordering(self):
        """Test that registros are ordered by date descending."""
        yesterday = date.today() - timedelta(days=1)
        today = date.today()
        
        reg1 = RegistroTreinamento.objects.create(
            individuo=self.individuo,
            treinamento=self.treinamento,
            data=yesterday,
            valor_alcançado=Decimal('5.00')
        )
        
        treinamento2 = Treinamento.objects.create(
            nome='Natação',
            unidade_medida='min'
        )
        reg2 = RegistroTreinamento.objects.create(
            individuo=self.individuo,
            treinamento=treinamento2,
            data=today,
            valor_alcançado=Decimal('30.00')
        )
        
        registros = RegistroTreinamento.objects.filter(individuo=self.individuo)
        self.assertEqual(registros[0].data, today)
        self.assertEqual(registros[1].data, yesterday)

    def test_registro_with_observacoes(self):
        """Test registro with observations."""
        registro = RegistroTreinamento.objects.create(
            individuo=self.individuo,
            treinamento=self.treinamento,
            data=date.today(),
            valor_alcançado=Decimal('8.00'),
            observacoes='Treino leve'
        )
        self.assertEqual(registro.observacoes, 'Treino leve')


class LetterCaptchaModelTest(TestCase):
    """Tests for LetterCaptcha model."""
    
    def test_captcha_generation(self):
        """Test captcha generation."""
        captcha = LetterCaptcha.generate_captcha('test_session_123')
        self.assertEqual(len(captcha.letters), 6)
        self.assertEqual(captcha.session_key, 'test_session_123')
        self.assertFalse(captcha.is_solved)
    
    def test_captcha_verify_correct(self):
        """Test captcha verification with correct answer."""
        captcha = LetterCaptcha.generate_captcha('test_session_456')
        result = captcha.verify_solution(captcha.letters)
        self.assertTrue(result)
    
    def test_captcha_verify_wrong(self):
        """Test captcha verification with wrong answer."""
        captcha = LetterCaptcha.generate_captcha('test_session_789')
        result = captcha.verify_solution('WRONG')
        self.assertFalse(result)
    
    def test_captcha_case_insensitive(self):
        """Test that captcha is case insensitive."""
        captcha = LetterCaptcha.generate_captcha('test_session_abc')
        result = captcha.verify_solution(captcha.letters.lower())
        self.assertTrue(result)
