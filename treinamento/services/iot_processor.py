"""
Serviço de processamento de dados IoT
Responsável por processar leituras de sensores IoT e convertê-las em registros de treinamento
"""
from decimal import Decimal
from django.utils import timezone
from django.db import transaction
from ..models import RegistroTreinamento, Treinamento
from ..iot_models import DispositivoIoT, LeituraIoT, ConfiguracaoDispositivo
import logging

logger = logging.getLogger(__name__)


class IoTDataProcessor:
    """
    Processa dados recebidos de dispositivos IoT
    """
    
    # Mapeamento de tipos de sensor para tipos de treinamento
    SENSOR_TO_TRAINING_MAP = {
        'heartrate': None,  # Frequência cardíaca não gera treinamento direto
        'steps': 'Caminhada',  # Passos -> Caminhada
        'weight': None,  # Peso vai para PesoHistorico
        'reps': 'Musculação',  # Repetições -> Musculação
        'gps': 'Corrida',  # GPS -> Corrida
        'distance': 'Corrida',  # Distância -> Corrida
        'duration': None,  # Duração é um atributo, não um treinamento
    }
    
    # Mapeamento de unidades de medida
    SENSOR_UNIT_MAP = {
        'heartrate': 'bpm',
        'steps': 'steps',
        'weight': 'kg',
        'reps': 'rep',
        'distance': 'km',
        'duration': 'min',
    }
    
    @classmethod
    def process_reading(cls, dispositivo, reading_data, individuo=None):
        """
        Processa uma leitura do dispositivo IoT
        
        Args:
            dispositivo: Instância de DispositivoIoT
            reading_data: Dict com dados da leitura {tipo, valor, timestamp, metadata, etc}
            individuo: Instância de Individuo (opcional, usa o proprietário do dispositivo se não fornecido)
            
        Returns:
            LeituraIoT: Instância da leitura criada
        """
        from .alert_manager import AlertManager
        
        # Usa o proprietário do dispositivo se não fornecido
        if individuo is None:
            individuo = dispositivo.proprietario
        
        if individuo is None:
            logger.error(f"Dispositivo {dispositivo.device_id} não tem proprietário definido")
            raise ValueError("Dispositivo sem proprietário definido")
        
        # Extrai dados da leitura
        tipo_sensor = reading_data.get('tipo', reading_data.get('tipo_sensor', 'generic'))
        valor_bruto = Decimal(str(reading_data.get('valor', 0)))
        timestamp = reading_data.get('timestamp', timezone.now())
        unidade = reading_data.get('unidade', cls.SENSOR_UNIT_MAP.get(tipo_sensor, 'unit'))
        qualidade_sinal = reading_data.get('qualidade_sinal', 'good')
        nivel_bateria = reading_data.get('nivel_bateria')
        metadata = reading_data.get('metadata', {})
        
        # Aplica calibração se configurado
        try:
            config = dispositivo.configuracao
            valor_calibrado = (valor_bruto * config.fator_calibracao) + config.offset_calibracao
        except ConfiguracaoDispositivo.DoesNotExist:
            valor_calibrado = valor_bruto
        
        # Calcula score de confiabilidade
        confiabilidade = cls._calcular_confiabilidade(qualidade_sinal, nivel_bateria, dispositivo)
        
        # Cria a leitura
        with transaction.atomic():
            leitura = LeituraIoT.objects.create(
                dispositivo=dispositivo,
                individuo=individuo,
                timestamp=timestamp,
                tipo_sensor=tipo_sensor,
                valor=valor_calibrado,
                unidade=unidade,
                qualidade_sinal=qualidade_sinal,
                nivel_bateria=nivel_bateria,
                metadata=metadata,
                processado=False
            )
            
            # Atualiza último ping do dispositivo
            dispositivo.ultimo_ping = timezone.now()
            dispositivo.save(update_fields=['ultimo_ping'])
            
            # Verifica alertas
            AlertManager.check_reading_alerts(leitura, dispositivo)
            
            # Verifica bateria baixa
            if nivel_bateria is not None and nivel_bateria < 20:
                AlertManager.create_low_battery_alert(dispositivo, nivel_bateria, individuo)
            
            # Cria registro de treinamento automaticamente se configurado
            try:
                config = dispositivo.configuracao
                if config.criar_registro_automatico:
                    registro = cls._criar_registro_treinamento(
                        leitura, 
                        dispositivo, 
                        individuo, 
                        config,
                        confiabilidade
                    )
                    if registro:
                        leitura.processado = True
                        leitura.registro_treinamento = registro
                        leitura.save(update_fields=['processado', 'registro_treinamento'])
            except ConfiguracaoDispositivo.DoesNotExist:
                pass
            
            logger.info(f"Leitura processada: {leitura}")
            return leitura
    
    @classmethod
    def _calcular_confiabilidade(cls, qualidade_sinal, nivel_bateria, dispositivo):
        """
        Calcula score de confiabilidade dos dados (0-100%)
        """
        score = Decimal('100.0')
        
        # Penaliza por qualidade de sinal
        qualidade_scores = {
            'excellent': 0,
            'good': 5,
            'fair': 15,
            'poor': 30,
        }
        score -= Decimal(str(qualidade_scores.get(qualidade_sinal, 10)))
        
        # Penaliza por bateria baixa
        if nivel_bateria is not None:
            if nivel_bateria < 10:
                score -= Decimal('20')
            elif nivel_bateria < 20:
                score -= Decimal('10')
        
        # Penaliza se dispositivo está em manutenção
        if dispositivo.status == 'maintenance':
            score -= Decimal('15')
        
        return max(Decimal('0'), min(Decimal('100'), score))
    
    @classmethod
    def _criar_registro_treinamento(cls, leitura, dispositivo, individuo, config, confiabilidade):
        """
        Cria registro de treinamento a partir da leitura IoT
        """
        tipo_sensor = leitura.tipo_sensor
        
        # Determina o tipo de treinamento
        if config.treinamento_padrao:
            treinamento = config.treinamento_padrao
        else:
            # Tenta mapear automaticamente
            nome_treinamento = cls.SENSOR_TO_TRAINING_MAP.get(tipo_sensor)
            if not nome_treinamento:
                logger.warning(f"Tipo de sensor {tipo_sensor} não mapeado para treinamento automático")
                return None
            
            try:
                treinamento = Treinamento.objects.get(nome=nome_treinamento)
            except Treinamento.DoesNotExist:
                logger.error(f"Treinamento '{nome_treinamento}' não encontrado")
                return None
        
        # Mapeia esporte baseado no tipo de sensor
        esporte_map = {
            'steps': 'caminhada',
            'distance': 'corrida',
            'gps': 'corrida',
            'reps': 'musculacao',
        }
        esporte = esporte_map.get(tipo_sensor, 'outro')
        
        # Extrai duração se disponível nos metadados
        duracao = None
        if leitura.metadata and 'duracao' in leitura.metadata:
            from datetime import timedelta
            duracao_segundos = leitura.metadata.get('duracao')
            if duracao_segundos:
                duracao = timedelta(seconds=duracao_segundos)
        
        # Extrai percurso GPS se disponível
        percurso_gps = None
        if leitura.metadata and 'gps_track' in leitura.metadata:
            percurso_gps = leitura.metadata.get('gps_track')
        
        # Cria o registro de treinamento
        registro = RegistroTreinamento.objects.create(
            individuo=individuo,
            treinamento=treinamento,
            data=leitura.timestamp.date(),
            valor_alcançado=leitura.valor,
            esporte=esporte,
            fonte_dados='iot',
            confiabilidade=confiabilidade,
            duracao=duracao,
            percurso_gps=percurso_gps,
            observacoes=f"Gerado automaticamente do dispositivo {dispositivo.nome} ({dispositivo.device_id})"
        )
        
        logger.info(f"Registro de treinamento criado automaticamente: {registro}")
        return registro
    
    @classmethod
    def process_batch_readings(cls, dispositivo, readings_list, individuo=None):
        """
        Processa múltiplas leituras em batch
        
        Args:
            dispositivo: Instância de DispositivoIoT
            readings_list: Lista de dicts com dados das leituras
            individuo: Instância de Individuo (opcional)
            
        Returns:
            List[LeituraIoT]: Lista de leituras criadas
        """
        leituras = []
        erros = []
        
        for reading_data in readings_list:
            try:
                leitura = cls.process_reading(dispositivo, reading_data, individuo)
                leituras.append(leitura)
            except Exception as e:
                logger.error(f"Erro ao processar leitura: {e}")
                erros.append({
                    'reading': reading_data,
                    'error': str(e)
                })
        
        if erros:
            logger.warning(f"Processamento batch completado com {len(erros)} erro(s)")
        
        return leituras, erros
    
    @classmethod
    def reprocess_unprocessed_readings(cls, dispositivo=None, limit=100):
        """
        Reprocessa leituras não processadas
        
        Args:
            dispositivo: Filtrar por dispositivo específico (opcional)
            limit: Número máximo de leituras para processar
            
        Returns:
            int: Número de leituras processadas
        """
        queryset = LeituraIoT.objects.filter(processado=False)
        
        if dispositivo:
            queryset = queryset.filter(dispositivo=dispositivo)
        
        leituras = queryset.order_by('timestamp')[:limit]
        processadas = 0
        
        for leitura in leituras:
            try:
                config = leitura.dispositivo.configuracao
                if config.criar_registro_automatico:
                    confiabilidade = cls._calcular_confiabilidade(
                        leitura.qualidade_sinal,
                        leitura.nivel_bateria,
                        leitura.dispositivo
                    )
                    
                    registro = cls._criar_registro_treinamento(
                        leitura,
                        leitura.dispositivo,
                        leitura.individuo,
                        config,
                        confiabilidade
                    )
                    
                    if registro:
                        leitura.processado = True
                        leitura.registro_treinamento = registro
                        leitura.save(update_fields=['processado', 'registro_treinamento'])
                        processadas += 1
            except Exception as e:
                logger.error(f"Erro ao reprocessar leitura {leitura.id}: {e}")
        
        logger.info(f"Reprocessadas {processadas} leituras")
        return processadas
