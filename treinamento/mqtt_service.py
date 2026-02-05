"""
Serviço MQTT para comunicação com dispositivos IoT
Gerencia conexão, subscrição de tópicos e processamento de dados
"""
import json
import logging
import paho.mqtt.client as mqtt
from django.conf import settings
from django.utils import timezone
from decimal import Decimal
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


class MQTTService:
    """
    Serviço singleton para gerenciar conexão MQTT
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(MQTTService, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self._initialized = True
        self.client = None
        self.connected = False
        
        # Configurações do broker MQTT
        self.broker_host = getattr(settings, 'MQTT_BROKER_HOST', 'localhost')
        self.broker_port = getattr(settings, 'MQTT_BROKER_PORT', 1883)
        self.broker_username = getattr(settings, 'MQTT_USERNAME', None)
        self.broker_password = getattr(settings, 'MQTT_PASSWORD', None)
        self.client_id = getattr(settings, 'MQTT_CLIENT_ID', 'django_fitness_app')
        
        # Tópicos
        self.base_topic = getattr(settings, 'MQTT_BASE_TOPIC', 'fitness/device')
        
    def connect(self):
        """Estabelece conexão com o broker MQTT"""
        if self.connected:
            logger.info("MQTT já está conectado")
            return
        
        try:
            self.client = mqtt.Client(client_id=self.client_id, protocol=mqtt.MQTTv5)
            
            # Configurar callbacks
            self.client.on_connect = self._on_connect
            self.client.on_disconnect = self._on_disconnect
            self.client.on_message = self._on_message
            
            # Autenticação se configurada
            if self.broker_username and self.broker_password:
                self.client.username_pw_set(self.broker_username, self.broker_password)
            
            # Conectar ao broker
            logger.info(f"Conectando ao broker MQTT em {self.broker_host}:{self.broker_port}")
            self.client.connect(self.broker_host, self.broker_port, 60)
            
            # Iniciar loop em background
            self.client.loop_start()
            
        except Exception as e:
            logger.error(f"Erro ao conectar ao MQTT broker: {e}")
            raise
    
    def disconnect(self):
        """Desconecta do broker MQTT"""
        if self.client and self.connected:
            self.client.loop_stop()
            self.client.disconnect()
            self.connected = False
            logger.info("Desconectado do broker MQTT")
    
    def _on_connect(self, client, userdata, flags, rc, properties=None):
        """Callback quando conecta ao broker"""
        if rc == 0:
            self.connected = True
            logger.info("Conectado ao broker MQTT com sucesso")
            
            # Subscrever aos tópicos de interesse
            topics = [
                f"{self.base_topic}/+/heartrate",
                f"{self.base_topic}/+/steps",
                f"{self.base_topic}/+/weight",
                f"{self.base_topic}/+/reps",
                f"{self.base_topic}/+/gps",
                f"{self.base_topic}/+/status",
            ]
            
            for topic in topics:
                client.subscribe(topic)
                logger.info(f"Subscrito ao tópico: {topic}")
        else:
            logger.error(f"Falha ao conectar ao MQTT broker. Código: {rc}")
    
    def _on_disconnect(self, client, userdata, rc, properties=None):
        """Callback quando desconecta do broker"""
        self.connected = False
        if rc != 0:
            logger.warning(f"Desconexão inesperada do broker MQTT. Código: {rc}")
        else:
            logger.info("Desconectado do broker MQTT")
    
    def _on_message(self, client, userdata, msg):
        """Callback quando recebe uma mensagem"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            logger.info(f"Mensagem recebida no tópico {topic}: {payload}")
            
            # Parse do payload JSON
            data = json.loads(payload)
            
            # Processar a mensagem baseado no tópico
            self._process_message(topic, data)
            
        except json.JSONDecodeError as e:
            logger.error(f"Erro ao decodificar JSON: {e}")
        except Exception as e:
            logger.error(f"Erro ao processar mensagem MQTT: {e}")
    
    def _process_message(self, topic, data):
        """Processa mensagem recebida e salva no banco de dados"""
        # Import aqui para evitar circular import
        from .iot_models import DispositivoIoT, LeituraIoT
        from .models import Individuo
        
        # Extrair informações do tópico
        # Formato: fitness/device/{device_id}/{sensor_type}
        topic_parts = topic.split('/')
        if len(topic_parts) < 4:
            logger.warning(f"Tópico inválido: {topic}")
            return
        
        device_id = topic_parts[2]
        sensor_type = topic_parts[3]
        
        # Validar dados obrigatórios
        required_fields = ['value', 'unit', 'timestamp']
        if not all(field in data for field in required_fields):
            logger.warning(f"Campos obrigatórios faltando: {data}")
            return
        
        try:
            # Buscar ou criar dispositivo
            dispositivo, created = DispositivoIoT.objects.get_or_create(
                device_id=device_id,
                defaults={
                    'nome': data.get('device_name', device_id),
                    'tipo': sensor_type,
                    'status': 'active'
                }
            )
            
            # Atualizar último ping
            dispositivo.ultimo_ping = timezone.now()
            dispositivo.save(update_fields=['ultimo_ping'])
            
            # Buscar indivíduo (se especificado)
            individuo = None
            if 'user_id' in data:
                try:
                    individuo = Individuo.objects.get(user_id=data['user_id'])
                except Individuo.DoesNotExist:
                    logger.warning(f"Indivíduo não encontrado: user_id={data['user_id']}")
            
            # Se não tem user_id mas o dispositivo tem proprietário
            if not individuo and dispositivo.proprietario:
                individuo = dispositivo.proprietario
            
            # Parse do timestamp
            timestamp_str = data['timestamp']
            try:
                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', '+00:00'))
            except:
                timestamp = timezone.now()
            
            # Criar leitura IoT
            leitura = LeituraIoT.objects.create(
                dispositivo=dispositivo,
                individuo=individuo,
                timestamp=timestamp,
                tipo_sensor=sensor_type,
                valor=Decimal(str(data['value'])),
                unidade=data['unit'],
                qualidade_sinal=data.get('metadata', {}).get('signal_quality', 'good'),
                nivel_bateria=data.get('metadata', {}).get('battery'),
                metadata=data.get('metadata', {})
            )
            
            logger.info(f"Leitura IoT criada: {leitura}")
            
            # Processar leitura automaticamente se configurado
            if dispositivo.configuracao.criar_registro_automatico if hasattr(dispositivo, 'configuracao') else True:
                self._create_training_record(leitura)
            
            # Verificar alertas
            self._check_alerts(leitura)
            
        except Exception as e:
            logger.error(f"Erro ao processar mensagem: {e}", exc_info=True)
    
    def _create_training_record(self, leitura):
        """Cria registro de treinamento automaticamente a partir de uma leitura"""
        from .models import RegistroTreinamento, Treinamento
        from .iot_models import ConfiguracaoDispositivo
        
        # Verificar se já foi processado
        if leitura.processado:
            return
        
        # Verificar se tem indivíduo associado
        if not leitura.individuo:
            logger.warning(f"Leitura {leitura.id} não tem indivíduo associado")
            return
        
        try:
            # Obter configuração do dispositivo
            try:
                config = leitura.dispositivo.configuracao
                treinamento_padrao = config.treinamento_padrao
                
                # Aplicar calibração
                valor_calibrado = (leitura.valor * config.fator_calibracao) + config.offset_calibracao
            except ConfiguracaoDispositivo.DoesNotExist:
                treinamento_padrao = None
                valor_calibrado = leitura.valor
            
            # Se não tem treinamento padrão, tentar buscar baseado no tipo de sensor
            if not treinamento_padrao:
                sensor_to_training = {
                    'heartrate': 'Frequência Cardíaca',
                    'steps': 'Passos',
                    'weight': 'Peso',
                    'reps': 'Repetições',
                }
                
                training_name = sensor_to_training.get(leitura.tipo_sensor)
                if training_name:
                    treinamento_padrao, _ = Treinamento.objects.get_or_create(
                        nome=training_name,
                        defaults={
                            'unidade_medida': leitura.unidade,
                            'descricao': f'Criado automaticamente para sensor {leitura.tipo_sensor}'
                        }
                    )
            
            if not treinamento_padrao:
                logger.warning(f"Nenhum treinamento configurado para {leitura.tipo_sensor}")
                return
            
            # Mapear tipo de sensor para esporte
            sensor_to_sport = {
                'heartrate': 'corrida',
                'steps': 'caminhada',
                'weight': 'musculacao',
                'reps': 'musculacao',
                'gps': 'corrida',
            }
            
            esporte = sensor_to_sport.get(leitura.tipo_sensor, 'outro')
            
            # Criar registro de treinamento
            registro = RegistroTreinamento.objects.create(
                individuo=leitura.individuo,
                treinamento=treinamento_padrao,
                data=leitura.timestamp.date(),
                valor_alcançado=valor_calibrado,
                esporte=esporte,
                fonte_dados='iot',
                confiabilidade=self._calculate_confidence(leitura),
                observacoes=f'Criado automaticamente de dispositivo {leitura.dispositivo.nome}'
            )
            
            # Marcar leitura como processada
            leitura.processado = True
            leitura.registro_treinamento = registro
            leitura.save(update_fields=['processado', 'registro_treinamento'])
            
            logger.info(f"Registro de treinamento criado automaticamente: {registro}")
            
        except Exception as e:
            logger.error(f"Erro ao criar registro de treinamento: {e}", exc_info=True)
    
    def _calculate_confidence(self, leitura):
        """Calcula score de confiabilidade baseado em vários fatores"""
        confidence = Decimal('100.0')
        
        # Reduzir baseado na qualidade do sinal
        signal_quality_map = {
            'excellent': 0,
            'good': 5,
            'fair': 15,
            'poor': 30,
        }
        confidence -= Decimal(str(signal_quality_map.get(leitura.qualidade_sinal, 10)))
        
        # Reduzir se bateria baixa
        if leitura.nivel_bateria and leitura.nivel_bateria < 20:
            confidence -= Decimal('10.0')
        
        # Reduzir se leitura é muito antiga
        age = timezone.now() - leitura.timestamp
        if age > timedelta(hours=24):
            confidence -= Decimal('20.0')
        
        return max(confidence, Decimal('0.0'))
    
    def _check_alerts(self, leitura):
        """Verifica se a leitura está fora dos limites e cria alertas"""
        from .iot_models import AlertaIoT, ConfiguracaoDispositivo
        
        try:
            config = leitura.dispositivo.configuracao
            
            # Verificar valor muito baixo
            if config.valor_minimo_alerta and leitura.valor < config.valor_minimo_alerta:
                AlertaIoT.objects.create(
                    dispositivo=leitura.dispositivo,
                    individuo=leitura.individuo,
                    leitura=leitura,
                    tipo='low_value',
                    severidade='warning',
                    mensagem=f'{leitura.tipo_sensor} muito baixo: {leitura.valor}{leitura.unidade} (mínimo: {config.valor_minimo_alerta})'
                )
            
            # Verificar valor muito alto
            if config.valor_maximo_alerta and leitura.valor > config.valor_maximo_alerta:
                AlertaIoT.objects.create(
                    dispositivo=leitura.dispositivo,
                    individuo=leitura.individuo,
                    leitura=leitura,
                    tipo='high_value',
                    severidade='critical' if leitura.tipo_sensor == 'heartrate' else 'warning',
                    mensagem=f'{leitura.tipo_sensor} muito alto: {leitura.valor}{leitura.unidade} (máximo: {config.valor_maximo_alerta})'
                )
            
            # Verificar bateria baixa
            if leitura.nivel_bateria and leitura.nivel_bateria < 15:
                AlertaIoT.objects.create(
                    dispositivo=leitura.dispositivo,
                    individuo=leitura.individuo,
                    leitura=leitura,
                    tipo='low_battery',
                    severidade='info',
                    mensagem=f'Bateria baixa no dispositivo {leitura.dispositivo.nome}: {leitura.nivel_bateria}%'
                )
                
        except ConfiguracaoDispositivo.DoesNotExist:
            # Sem configuração, não verificar alertas
            pass
        except Exception as e:
            logger.error(f"Erro ao verificar alertas: {e}")
    
    def publish(self, device_id, sensor_type, data):
        """Publica mensagem para um dispositivo"""
        if not self.connected:
            logger.warning("Não conectado ao broker MQTT")
            return False
        
        topic = f"{self.base_topic}/{device_id}/{sensor_type}"
        payload = json.dumps(data)
        
        try:
            result = self.client.publish(topic, payload, qos=1)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                logger.info(f"Mensagem publicada em {topic}: {payload}")
                return True
            else:
                logger.error(f"Erro ao publicar mensagem: {result.rc}")
                return False
        except Exception as e:
            logger.error(f"Erro ao publicar: {e}")
            return False


# Instância global do serviço
mqtt_service = MQTTService()
