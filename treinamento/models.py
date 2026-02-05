from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator, RegexValidator
from django.utils import timezone
from decimal import Decimal
from datetime import timedelta
import re
import random
import string

class Individuo(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    nome_completo = models.CharField(
        max_length=255,
        validators=[
            RegexValidator(
                regex=r'^[A-Za-zÀ-ÿ\s]+$',
                message='O nome deve conter apenas letras e espaços'
            )
        ]
    )

    data_nascimento = models.DateField(null=True, blank=True)
    peso = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Peso em kg")
    SEXO_CHOICES = [
        ("masculino", "Masculino"),
        ("feminino", "Feminino"),
        ("outro", "Outro"),
    ]
    sexo = models.CharField(max_length=10, choices=SEXO_CHOICES, null=True, blank=True)
    observacoes = models.TextField(blank=True, max_length=500, help_text="Observações/restrições")
    ativo = models.BooleanField(default=True)
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True)

    def __str__(self):
        return self.nome_completo

class Treinamento(models.Model):
    UNIDADES_CHOICES = [
        ('min', 'Minutos'),
        ('km', 'Quilômetros'),
        ('kg', 'Quilogramas'),
        ('rep', 'Repetições'),
        ('out', 'Outro'),
    ]
    nome = models.CharField(
        max_length=100, 
        unique=True,
        validators=[
            RegexValidator(
                regex=r'^[A-Za-zÀ-ÿ0-9\s\-\.]+$',
                message='O nome do treinamento deve conter apenas letras, números, espaços, hífens e pontos'
            )
        ]
    )
    unidade_medida = models.CharField(max_length=5, choices=UNIDADES_CHOICES)
    descricao = models.TextField(blank=True)

    def __str__(self):
        return f"{self.nome} ({self.unidade_medida})"

class RegistroTreinamento(models.Model):
    ESPORTE_CHOICES = [
        ('corrida', 'Corrida'),
        ('ciclismo', 'Ciclismo'),
        ('caminhada', 'Caminhada'),
        ('natacao', 'Natação'),
        ('musculacao', 'Musculação'),
        ('outro', 'Outro'),
    ]

    individuo = models.ForeignKey(Individuo, on_delete=models.CASCADE, related_name='registros')
    treinamento = models.ForeignKey(Treinamento, on_delete=models.CASCADE)
    data = models.DateField()
    valor_alcançado = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        validators=[
            MinValueValidator(Decimal('0.00')),
            MaxValueValidator(Decimal('999999.99'))
        ]
    )
    # Novos campos estilo Strava
    esporte = models.CharField(max_length=20, choices=ESPORTE_CHOICES, default='outro')
    esforco_percebido = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True, blank=True,
        help_text="Escala de 1 a 10"
    )
    percurso_gps = models.JSONField(null=True, blank=True, help_text="Dados de GPS em formato GeoJSON ou lista de coordenadas")
    duracao = models.DurationField(null=True, blank=True)
    
    # Campos IoT
    FONTE_DADOS_CHOICES = [
        ('manual', 'Entrada Manual'),
        ('iot', 'Dispositivo IoT'),
        ('api', 'API Externa'),
    ]
    fonte_dados = models.CharField(
        max_length=10, 
        choices=FONTE_DADOS_CHOICES, 
        default='manual',
        help_text="Origem dos dados"
    )
    # Relacionamento com dispositivo IoT (lazy import para evitar circular import)
    # dispositivo_iot definido via related_name em iot_models.py
    confiabilidade = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=100.00,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Score de confiabilidade dos dados (0-100%)"
    )
    
    observacoes = models.TextField(blank=True, max_length=500)

    class Meta:
        ordering = ['-data']

    def __str__(self):
        return f"{self.get_esporte_display()} por {self.individuo.nome_completo} em {self.data}"

    def clean(self):
        from django.core.exceptions import ValidationError
        # Validação personalizada (permite até 30 dias no futuro para agendamentos)
        from datetime import timedelta
        max_data_futura = timezone.now().date() + timedelta(days=30)
        if self.data and self.data > max_data_futura:
            raise ValidationError('A data do registro não pode ser mais de 30 dias no futuro.')

class PesoHistorico(models.Model):
    """
    Modelo para armazenar histórico de peso do usuário
    """
    individuo = models.ForeignKey(Individuo, on_delete=models.CASCADE, related_name='historico_pesos')
    peso = models.DecimalField(max_digits=5, decimal_places=2, help_text="Peso em kg")
    data_registro = models.DateField(default=timezone.now, help_text="Data do registro de peso")
    observacoes = models.TextField(blank=True, max_length=500, help_text="Observações sobre a medição")

    class Meta:
        ordering = ['-data_registro']
        unique_together = ('individuo', 'data_registro')

    def __str__(self):
        return f"Peso {self.peso}kg para {self.individuo.nome_completo} em {self.data_registro}"

class Kudos(models.Model):
    registro = models.ForeignKey(RegistroTreinamento, on_delete=models.CASCADE, related_name='kudos')
    individuo = models.ForeignKey(Individuo, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('registro', 'individuo')

class Comentario(models.Model):
    registro = models.ForeignKey(RegistroTreinamento, on_delete=models.CASCADE, related_name='comentarios')
    individuo = models.ForeignKey(Individuo, on_delete=models.CASCADE)
    texto = models.TextField(max_length=300)
    created_at = models.DateTimeField(auto_now_add=True)

class Seguidor(models.Model):
    seguidor = models.ForeignKey(Individuo, on_delete=models.CASCADE, related_name='seguindo')
    seguido = models.ForeignKey(Individuo, on_delete=models.CASCADE, related_name='seguidores')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('seguidor', 'seguido')

class LetterCaptcha(models.Model):
    """Modelo para armazenar captchas de letras"""
    session_key = models.CharField(max_length=255, unique=True)
    letters = models.CharField(max_length=10)  # Letras do captcha
    created_at = models.DateTimeField(auto_now_add=True)
    is_solved = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Letter captcha for session {self.session_key}"
    
    @classmethod
    def generate_captcha(cls, session_key):
        """Gera um novo captcha com letras"""
        # Remove captchas muito antigos (por exemplo, mais de 10 minutos)
        expiration_threshold = timezone.now() - timedelta(minutes=10)
        cls.objects.filter(created_at__lt=expiration_threshold).delete()

        # Gera 6 letras aleatórias (evitando letras confusas como I, L, O, 0, 1)
        available_letters = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
        letters = ''.join(random.choice(available_letters) for _ in range(6))
        
        # Remove captchas antigos
        cls.objects.filter(session_key=session_key, is_solved=False).delete()
        
        return cls.objects.create(
            session_key=session_key,
            letters=letters
        )
    
    def verify_solution(self, user_input):
        """Verifica se a solução do usuário está correta"""
        # Verifica expiração (mesmo limite usado em generate_captcha)
        if timezone.now() - self.created_at > timedelta(minutes=10):
            return False
        return user_input.upper() == self.letters