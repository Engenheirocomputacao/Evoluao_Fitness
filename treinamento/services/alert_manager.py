"""
Serviço de gerenciamento de alertas IoT
Responsável por criar e gerenciar alertas baseados em leituras de sensores
"""
from django.utils import timezone
from ..iot_models import AlertaIoT, DispositivoIoT, LeituraIoT, ConfiguracaoDispositivo
import logging

logger = logging.getLogger(__name__)


class AlertManager:
    """
    Gerencia alertas de dispositivos IoT
    """
    
    @classmethod
    def check_reading_alerts(cls, leitura, dispositivo):
        """
        Verifica se a leitura está fora dos limites configurados e cria alertas
        
        Args:
            leitura: Instância de LeituraIoT
            dispositivo: Instância de DispositivoIoT
            
        Returns:
            AlertaIoT ou None: Alerta criado, se houver
        """
        try:
            config = dispositivo.configuracao
        except ConfiguracaoDispositivo.DoesNotExist:
            # Sem configuração, sem alertas
            return None
        
        # Verifica limites
        valor = leitura.valor
        alerta = None
        
        if config.valor_minimo_alerta is not None and valor < config.valor_minimo_alerta:
            alerta = cls._create_alert(
                dispositivo=dispositivo,
                individuo=leitura.individuo,
                leitura=leitura,
                tipo='low_value',
                severidade='warning',
                mensagem=f"Valor baixo detectado: {valor} {leitura.unidade} (mínimo: {config.valor_minimo_alerta})"
            )
            
        elif config.valor_maximo_alerta is not None and valor > config.valor_maximo_alerta:
            # Determina severidade baseado no quanto excedeu
            excesso_percentual = ((valor - config.valor_maximo_alerta) / config.valor_maximo_alerta) * 100
            
            if excesso_percentual > 30:
                severidade = 'critical'
            elif excesso_percentual > 15:
                severidade = 'warning'
            else:
                severidade = 'info'
            
            alerta = cls._create_alert(
                dispositivo=dispositivo,
                individuo=leitura.individuo,
                leitura=leitura,
                tipo='high_value',
                severidade=severidade,
                mensagem=f"Valor alto detectado: {valor} {leitura.unidade} (máximo: {config.valor_maximo_alerta})"
            )
        
        return alerta
    
    @classmethod
    def create_low_battery_alert(cls, dispositivo, nivel_bateria, individuo):
        """
        Cria alerta de bateria baixa
        
        Args:
            dispositivo: Instância de DispositivoIoT
            nivel_bateria: Nível de bateria em %
            individuo: Instância de Individuo
            
        Returns:
            AlertaIoT: Alerta criado
        """
        # Não cria alertas duplicados
        alerta_existente = AlertaIoT.objects.filter(
            dispositivo=dispositivo,
            tipo='low_battery',
            resolvido=False
        ).first()
        
        if alerta_existente:
            return alerta_existente
        
        severidade = 'critical' if nivel_bateria < 10 else 'warning'
        
        return cls._create_alert(
            dispositivo=dispositivo,
            individuo=individuo,
            tipo='low_battery',
            severidade=severidade,
            mensagem=f"Bateria baixa: {nivel_bateria}% - Recarregue o dispositivo '{dispositivo.nome}'"
        )
    
    @classmethod
    def create_offline_alert(cls, dispositivo, individuo):
        """
        Cria alerta de dispositivo offline
        
        Args:
            dispositivo: Instância de DispositivoIoT
            individuo: Instância de Individuo
            
        Returns:
            AlertaIoT: Alerta criado
        """
        # Não cria alertas duplicados
        alerta_existente = AlertaIoT.objects.filter(
            dispositivo=dispositivo,
            tipo='offline',
            resolvido=False
        ).first()
        
        if alerta_existente:
            return alerta_existente
        
        tempo_offline = "mais de 5 minutos"
        if dispositivo.ultimo_ping:
            delta = timezone.now() - dispositivo.ultimo_ping
            if delta.days > 0:
                tempo_offline = f"{delta.days} dia(s)"
            elif delta.seconds > 3600:
                tempo_offline = f"{delta.seconds // 3600} hora(s)"
            elif delta.seconds > 60:
                tempo_offline = f"{delta.seconds // 60} minuto(s)"
        
        return cls._create_alert(
            dispositivo=dispositivo,
            individuo=individuo,
            tipo='offline',
            severidade='warning',
            mensagem=f"Dispositivo '{dispositivo.nome}' está offline há {tempo_offline}"
        )
    
    @classmethod
    def create_error_alert(cls, dispositivo, individuo, error_message):
        """
        Cria alerta de erro no sensor
        
        Args:
            dispositivo: Instância de DispositivoIoT
            individuo: Instância de Individuo
            error_message: Mensagem de erro
            
        Returns:
            AlertaIoT: Alerta criado
        """
        return cls._create_alert(
            dispositivo=dispositivo,
            individuo=individuo,
            tipo='error',
            severidade='critical',
            mensagem=f"Erro no dispositivo '{dispositivo.nome}': {error_message}"
        )
    
    @classmethod
    def _create_alert(cls, dispositivo, individuo, tipo, severidade, mensagem, leitura=None):
        """
        Cria um alerta
        
        Args:
            dispositivo: Instância de DispositivoIoT
            individuo: Instância de Individuo
            tipo: Tipo do alerta
            severidade: Severidade do alerta
            mensagem: Mensagem do alerta
            leitura: Leitura relacionada (opcional)
            
        Returns:
            AlertaIoT: Alerta criado
        """
        alerta = AlertaIoT.objects.create(
            dispositivo=dispositivo,
            individuo=individuo,
            leitura=leitura,
            tipo=tipo,
            severidade=severidade,
            mensagem=mensagem
        )
        
        logger.info(f"Alerta criado: {alerta}")
        
        # TODO: Enviar notificação (email, push, etc)
        # cls._send_notification(alerta)
        
        return alerta
    
    @classmethod
    def mark_as_viewed(cls, alerta_id):
        """
        Marca alerta como visualizado
        """
        try:
            alerta = AlertaIoT.objects.get(id=alerta_id)
            if not alerta.visualizado:
                alerta.visualizado = True
                alerta.visualizado_em = timezone.now()
                alerta.save(update_fields=['visualizado', 'visualizado_em'])
                return True
        except AlertaIoT.DoesNotExist:
            logger.error(f"Alerta {alerta_id} não encontrado")
        return False
    
    @classmethod
    def mark_as_resolved(cls, alerta_id):
        """
        Marca alerta como resolvido
        """
        try:
            alerta = AlertaIoT.objects.get(id=alerta_id)
            if not alerta.resolvido:
                alerta.resolvido = True
                alerta.resolvido_em = timezone.now()
                if not alerta.visualizado:
                    alerta.visualizado = True
                    alerta.visualizado_em = timezone.now()
                alerta.save(update_fields=['resolvido', 'resolvido_em', 'visualizado', 'visualizado_em'])
                return True
        except AlertaIoT.DoesNotExist:
            logger.error(f"Alerta {alerta_id} não encontrado")
        return False
    
    @classmethod
    def check_offline_devices(cls):
        """
        Verifica dispositivos offline e cria alertas
        Deve ser executado periodicamente (ex: celery task)
        
        Returns:
            int: Número de alertas criados
        """
        from datetime import timedelta
        
        # Dispositivos ativos que não enviaram dados há mais de 5 minutos
        threshold = timezone.now() - timedelta(minutes=5)
        
        dispositivos_offline = DispositivoIoT.objects.filter(
            status='active',
            ultimo_ping__lt=threshold
        ).exclude(
            # Exclui dispositivos que já têm alerta de offline não resolvido
            alertas__tipo='offline',
            alertas__resolvido=False
        )
        
        alertas_criados = 0
        for dispositivo in dispositivos_offline:
            if dispositivo.proprietario:
                cls.create_offline_alert(dispositivo, dispositivo.proprietario)
                alertas_criados += 1
        
        logger.info(f"Verificação de dispositivos offline: {alertas_criados} alerta(s) criado(s)")
        return alertas_criados
    
    @classmethod
    def resolve_offline_alerts_for_device(cls, dispositivo):
        """
        Resolve alertas de offline quando dispositivo volta a ficar online
        
        Args:
            dispositivo: Instância de DispositivoIoT
        """
        alertas = AlertaIoT.objects.filter(
            dispositivo=dispositivo,
            tipo='offline',
            resolvido=False
        )
        
        for alerta in alertas:
            alerta.resolvido = True
            alerta.resolvido_em = timezone.now()
            alerta.save(update_fields=['resolvido', 'resolvido_em'])
        
        if alertas.exists():
            logger.info(f"Resolvidos {alertas.count()} alerta(s) de offline para {dispositivo.device_id}")
    
    @classmethod
    def get_active_alerts_for_user(cls, individuo, limit=10):
        """
        Retorna alertas ativos para um usuário
        
        Args:
            individuo: Instância de Individuo
            limit: Número máximo de alertas
            
        Returns:
            QuerySet: Alertas não resolvidos
        """
        return AlertaIoT.objects.filter(
            individuo=individuo,
            resolvido=False
        ).order_by('-criado_em')[:limit]
    
    @classmethod
    def get_critical_alerts_count(cls, individuo):
        """
        Retorna contagem de alertas críticos não resolvidos
        """
        return AlertaIoT.objects.filter(
            individuo=individuo,
            severidade='critical',
            resolvido=False
        ).count()
