from django.db import models
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from .models import Individuo, Treinamento
import uuid


class DispositivoIoT(models.Model):
    """
    Modelo para gerenciar dispositivos IoT cadastrados no sistema
    """
    TIPO_DISPOSITIVO_CHOICES = [
        ('heartrate', 'Monitor de Frequência Cardíaca'),
        ('steps', 'Contador de Passos'),
        ('weight', 'Balança Inteligente'),
        ('reps', 'Contador de Repetições'),
        ('gps', 'Rastreador GPS'),
        ('temperature', 'Sensor de Temperatura'),
        ('generic', 'Genérico'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Ativo'),
        ('inactive', 'Inativo'),
        ('maintenance', 'Manutenção'),
        ('offline', 'Offline'),
    ]
    
    # Identificação
    device_id = models.CharField(
        max_length=100, 
        unique=True, 
        help_text="ID único do dispositivo (ex: ESP32_001)"
    )
    nome = models.CharField(max_length=200, help_text="Nome amigável do dispositivo")
    tipo = models.CharField(max_length=20, choices=TIPO_DISPOSITIVO_CHOICES)
    
    # Relacionamentos
    proprietario = models.ForeignKey(
        Individuo, 
        on_delete=models.CASCADE, 
        related_name='dispositivos_iot',
        null=True,
        blank=True,
        help_text="Dono do dispositivo (opcional para dispositivos compartilhados)"
    )
    
    # Status e configuração
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    ultimo_ping = models.DateTimeField(null=True, blank=True, help_text="Última vez que o dispositivo enviou dados")
    
    # Controle manual de status
    forcar_offline = models.BooleanField(
        default=False,
        help_text="Marque para forçar o dispositivo como offline manualmente"
    )
    
    # Metadados
    fabricante = models.CharField(max_length=100, blank=True)
    modelo = models.CharField(max_length=100, blank=True)
    firmware_version = models.CharField(max_length=50, blank=True)
    
    # Dados técnicos
    mac_address = models.CharField(max_length=17, blank=True, help_text="Endereço MAC do dispositivo")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    
    # Timestamps
    data_cadastro = models.DateTimeField(auto_now_add=True)
    ultima_atualizacao = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-ultimo_ping']
        verbose_name = "Dispositivo IoT"
        verbose_name_plural = "Dispositivos IoT"
    
    def __str__(self):
        return f"{self.nome} ({self.device_id})"
    
    def esta_online(self):
        """Verifica se o dispositivo está online (todos online por padrão, exceto se forçado offline)"""
        from datetime import timedelta
        
        # Se usuário forçou offline manualmente, retorna False
        if self.forcar_offline:
            return False
        
        # Por padrão, todos os dispositivos são considerados online
        # Mas ainda verificamos ping recente ou leituras para manter compatibilidade
        if self.ultimo_ping and timezone.now() - self.ultimo_ping < timedelta(minutes=30):
            return True
        
        if self.leituras.filter(timestamp__gte=timezone.now() - timedelta(hours=24)).exists():
            return True
            
        # Se não tem atividade recente mas não foi forçado offline, considera online
        return not self.forcar_offline


class LeituraIoT(models.Model):
    """
    Armazena as leituras brutas recebidas dos sensores IoT
    """
    # Relacionamentos
    dispositivo = models.ForeignKey(
        DispositivoIoT, 
        on_delete=models.CASCADE, 
        related_name='leituras'
    )
    individuo = models.ForeignKey(
        Individuo, 
        on_delete=models.CASCADE, 
        related_name='leituras_iot',
        null=True,
        blank=True
    )
    
    # Dados da leitura
    timestamp = models.DateTimeField(help_text="Timestamp da leitura do sensor")
    tipo_sensor = models.CharField(max_length=50, help_text="Tipo de sensor (heartrate, steps, etc)")
    valor = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        help_text="Valor da leitura"
    )
    unidade = models.CharField(max_length=20, help_text="Unidade de medida (bpm, steps, kg, etc)")
    
    # Metadados
    qualidade_sinal = models.CharField(
        max_length=20, 
        choices=[
            ('excellent', 'Excelente'),
            ('good', 'Bom'),
            ('fair', 'Razoável'),
            ('poor', 'Ruim'),
        ],
        default='good'
    )
    nivel_bateria = models.IntegerField(
        null=True, 
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Nível de bateria do dispositivo (%)"
    )
    
    # Dados adicionais em JSON
    metadata = models.JSONField(
        null=True, 
        blank=True,
        help_text="Dados adicionais do sensor (coordenadas GPS, etc)"
    )
    
    # Processamento
    processado = models.BooleanField(
        default=False,
        help_text="Indica se a leitura já foi processada e convertida em registro de treinamento"
    )
    registro_treinamento = models.ForeignKey(
        'RegistroTreinamento',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='leituras_origem'
    )
    
    # Timestamp de criação
    recebido_em = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = "Leitura IoT"
        verbose_name_plural = "Leituras IoT"
        indexes = [
            models.Index(fields=['-timestamp']),
            models.Index(fields=['dispositivo', '-timestamp']),
            models.Index(fields=['individuo', '-timestamp']),
        ]
    
    def __str__(self):
        return f"{self.tipo_sensor}: {self.valor}{self.unidade} - {self.dispositivo.nome} em {self.timestamp}"


class ConfiguracaoDispositivo(models.Model):
    """
    Configurações específicas por dispositivo
    """
    dispositivo = models.OneToOneField(
        DispositivoIoT,
        on_delete=models.CASCADE,
        related_name='configuracao'
    )
    
    # Frequência de envio
    intervalo_leitura = models.IntegerField(
        default=60,
        validators=[MinValueValidator(1), MaxValueValidator(3600)],
        help_text="Intervalo entre leituras em segundos"
    )
    
    # Limites e alertas
    valor_minimo_alerta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Valor mínimo para gerar alerta"
    )
    valor_maximo_alerta = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Valor máximo para gerar alerta"
    )
    
    # Mapeamento automático
    criar_registro_automatico = models.BooleanField(
        default=True,
        help_text="Criar automaticamente registros de treinamento"
    )
    treinamento_padrao = models.ForeignKey(
        Treinamento,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Tipo de treinamento padrão para este dispositivo"
    )
    
    # Calibração
    fator_calibracao = models.DecimalField(
        max_digits=5,
        decimal_places=3,
        default=1.000,
        help_text="Fator de calibração para ajustar leituras"
    )
    offset_calibracao = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0.00,
        help_text="Offset para ajustar leituras"
    )
    
    # Configurações adicionais em JSON
    configuracoes_extras = models.JSONField(
        null=True,
        blank=True,
        help_text="Configurações específicas do dispositivo"
    )
    
    # Timestamps
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Configuração de Dispositivo"
        verbose_name_plural = "Configurações de Dispositivos"
    
    def __str__(self):
        return f"Config: {self.dispositivo.nome}"


class AlertaIoT(models.Model):
    """
    Alertas gerados por leituras fora do padrão
    """
    TIPO_ALERTA_CHOICES = [
        ('low_value', 'Valor Baixo'),
        ('high_value', 'Valor Alto'),
        ('offline', 'Dispositivo Offline'),
        ('low_battery', 'Bateria Baixa'),
        ('error', 'Erro no Sensor'),
    ]
    
    SEVERIDADE_CHOICES = [
        ('info', 'Informação'),
        ('warning', 'Aviso'),
        ('critical', 'Crítico'),
    ]
    
    dispositivo = models.ForeignKey(
        DispositivoIoT,
        on_delete=models.CASCADE,
        related_name='alertas'
    )
    individuo = models.ForeignKey(
        Individuo,
        on_delete=models.CASCADE,
        related_name='alertas_iot',
        null=True,
        blank=True
    )
    leitura = models.ForeignKey(
        LeituraIoT,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='alertas'
    )
    
    tipo = models.CharField(max_length=20, choices=TIPO_ALERTA_CHOICES)
    severidade = models.CharField(max_length=20, choices=SEVERIDADE_CHOICES, default='warning')
    mensagem = models.TextField(help_text="Descrição do alerta")
    
    visualizado = models.BooleanField(default=False)
    resolvido = models.BooleanField(default=False)
    
    criado_em = models.DateTimeField(auto_now_add=True)
    visualizado_em = models.DateTimeField(null=True, blank=True)
    resolvido_em = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-criado_em']
        verbose_name = "Alerta IoT"
        verbose_name_plural = "Alertas IoT"
    
    def __str__(self):
        return f"{self.get_severidade_display()}: {self.mensagem[:50]}"
