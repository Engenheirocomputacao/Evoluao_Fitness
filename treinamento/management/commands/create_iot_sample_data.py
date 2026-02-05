"""
Management command para criar dados de exemplo de IoT
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from treinamento.models import Individuo, Treinamento
from treinamento.iot_models import DispositivoIoT, LeituraIoT, ConfiguracaoDispositivo, AlertaIoT
from treinamento.services.iot_processor import IoTDataProcessor
from datetime import timedelta
from decimal import Decimal
import random


class Command(BaseCommand):
    help = 'Cria dados de exemplo para demonstração do sistema IoT'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=2,
            help='Número de usuários para criar dispositivos (padrão: 2)'
        )
        parser.add_argument(
            '--devices-per-user',
            type=int,
            default=3,
            help='Número de dispositivos por usuário (padrão: 3)'
        )
        parser.add_argument(
            '--readings-per-device',
            type=int,
            default=50,
            help='Número de leituras por dispositivo (padrão: 50)'
        )

    def handle(self, *args, **options):
        num_users = options['users']
        devices_per_user = options['devices_per_user']
        readings_per_device = options['readings_per_device']

        self.stdout.write(self.style.NOTICE(
            f'Criando dados de exemplo IoT...\n'
            f'Usuários: {num_users}\n'
            f'Dispositivos por usuário: {devices_per_user}\n'
            f'Leituras por dispositivo: {readings_per_device}\n'
        ))

        # Busca ou cria usuários com perfil de indivíduo
        individuos = []
        for i in range(num_users):
            username = f'usuario_iot_{i+1}'
            email = f'{username}@exemplo.com'
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={'email': email, 'is_staff': False}
            )
            
            if created:
                user.set_password('senha123')
                user.save()
                self.stdout.write(self.style.SUCCESS(f'Usuário criado: {username}'))
            
            # Cria ou busca indivíduo
            individuo, ind_created = Individuo.objects.get_or_create(
                user=user,
                defaults={
                    'nome_completo': f'Usuário IoT {i+1}',
                    'data_nascimento': '1990-01-01',
                    'peso': Decimal('70.00'),
                    'sexo': 'masculino',
                    'ativo': True
                }
            )
            
            if ind_created:
                self.stdout.write(self.style.SUCCESS(f'Indivíduo criado: {individuo.nome_completo}'))
            
            individuos.append(individuo)

        # Garante que existem tipos de treinamento
        treinamentos = {}
        treinamentos_necessarios = [
            ('Caminhada', 'km'),
            ('Corrida', 'km'),
            ('Musculação', 'rep'),
        ]
        
        for nome, unidade in treinamentos_necessarios:
            treinamento, created = Treinamento.objects.get_or_create(
                nome=nome,
                defaults={'unidade_medida': unidade, 'descricao': f'Treinamento de {nome}'}
            )
            treinamentos[nome] = treinamento
            if created:
                self.stdout.write(self.style.SUCCESS(f'Treinamento criado: {nome}'))

        # Tipos de dispositivos com suas características
        device_types = [
            {
                'tipo': 'heartrate',
                'nome_template': 'Monitor Cardíaco',
                'fabricante': 'Polar',
                'modelo': 'H10',
                'sensor_tipo': 'heartrate',
                'unidade': 'bpm',
                'valor_min': 60,
                'valor_max': 200,
                'alerta_min': 50,
                'alerta_max': 180,
                'treinamento': None
            },
            {
                'tipo': 'steps',
                'nome_template': 'Contador de Passos',
                'fabricante': 'Fitbit',
                'modelo': 'Charge 5',
                'sensor_tipo': 'steps',
                'unidade': 'steps',
                'valor_min': 0,
                'valor_max': 30000,
                'alerta_min': None,
                'alerta_max': None,
                'treinamento': treinamentos.get('Caminhada')
            },
            {
                'tipo': 'reps',
                'nome_template': 'Contador Repetições',
                'fabricante': 'GymTracker',
                'modelo': 'Pro V2',
                'sensor_tipo': 'reps',
                'unidade': 'rep',
                'valor_min': 1,
                'valor_max': 100,
                'alerta_min': None,
                'alerta_max': None,
                'treinamento': treinamentos.get('Musculação')
            },
            {
                'tipo': 'gps',
                'nome_template': 'Rastreador GPS',
                'fabricante': 'Garmin',
                'modelo': 'Forerunner 245',
                'sensor_tipo': 'distance',
                'unidade': 'km',
                'valor_min': 0,
                'valor_max': 50,
                'alerta_min': None,
                'alerta_max': None,
                'treinamento': treinamentos.get('Corrida')
            },
        ]

        dispositivos_criados = 0
        leituras_criadas = 0
        alertas_criados = 0

        # Cria dispositivos para cada usuário
        for individuo in individuos:
            self.stdout.write(self.style.NOTICE(f'\nCriando dispositivos para {individuo.nome_completo}...'))
            
            # Seleciona dispositivos aleatórios
            selected_devices = random.sample(device_types, min(devices_per_user, len(device_types)))
            
            for idx, device_spec in enumerate(selected_devices):
                device_id = f"{device_spec['tipo'].upper()}_{individuo.id}_{idx+1:03d}"
                
                # Cria o dispositivo
                dispositivo, created = DispositivoIoT.objects.get_or_create(
                    device_id=device_id,
                    defaults={
                        'nome': f"{device_spec['nome_template']} {idx+1}",
                        'tipo': device_spec['tipo'],
                        'proprietario': individuo,
                        'status': 'active',
                        'fabricante': device_spec['fabricante'],
                        'modelo': device_spec['modelo'],
                        'firmware_version': '1.0.0',
                        'mac_address': f"00:1B:44:11:3A:{idx:02d}",
                        'ip_address': f"192.168.1.{100+idx}",
                        'ultimo_ping': timezone.now()
                    }
                )
                
                if created:
                    dispositivos_criados += 1
                    self.stdout.write(self.style.SUCCESS(f'  Dispositivo criado: {dispositivo.nome} ({device_id})'))
                    
                    # Cria configuração para o dispositivo
                    config = ConfiguracaoDispositivo.objects.create(
                        dispositivo=dispositivo,
                        intervalo_leitura=60,
                        valor_minimo_alerta=device_spec['alerta_min'],
                        valor_maximo_alerta=device_spec['alerta_max'],
                        criar_registro_automatico=True if device_spec['treinamento'] else False,
                        treinamento_padrao=device_spec['treinamento'],
                        fator_calibracao=Decimal('1.000'),
                        offset_calibracao=Decimal('0.00')
                    )
                    
                    # Cria leituras para o dispositivo
                    now = timezone.now()
                    for i in range(readings_per_device):
                        # Distribui leituras nas últimas 7 dias
                        timestamp = now - timedelta(
                            days=random.randint(0, 7),
                            hours=random.randint(0, 23),
                            minutes=random.randint(0, 59)
                        )
                        
                        # Gera valor aleatório baseado no tipo
                        valor_raw = random.uniform(
                            device_spec['valor_min'],
                            device_spec['valor_max']
                        )
                        # Arredonda para 2 casas decimais para evitar problemas com SQLite
                        valor = round(valor_raw, 2)
                        
                        # Ocasionalmente cria leituras fora dos limites para testar alertas
                        if device_spec['alerta_max'] and random.random() < 0.1:  # 10% de chance
                            valor = round(device_spec['alerta_max'] * 1.2, 2)
                        
                        # Qualidade de sinal aleatória (maioria boa)
                        qualidade_opcoes = ['excellent', 'excellent', 'good', 'good', 'good', 'fair', 'poor']
                        qualidade = random.choice(qualidade_opcoes)
                        
                        # Nível de bateria decrescente com o tempo
                        dias_passados = (now - timestamp).days
                        nivel_bateria = max(10, 100 - (dias_passados * 5) - random.randint(0, 10))
                        
                        # Cria a leitura usando o processador IoT
                        reading_data = {
                            'tipo': device_spec['sensor_tipo'],
                            'valor': valor,  # Já está arredondado
                            'timestamp': timestamp,
                            'timestamp': timestamp,
                            'unidade': device_spec['unidade'],
                            'qualidade_sinal': qualidade,
                            'nivel_bateria': nivel_bateria,
                            'metadata': {
                                'source': 'sample_data_generator',
                                'test': True
                            }
                        }
                        
                        try:
                            leitura = IoTDataProcessor.process_reading(
                                dispositivo,
                                reading_data,
                                individuo
                            )
                            leituras_criadas += 1
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'    Erro ao criar leitura: {e}'))
                    
                    # Conta alertas criados para este dispositivo
                    alertas_dispositivo = dispositivo.alertas.count()
                    alertas_criados += alertas_dispositivo
                    
                    if alertas_dispositivo > 0:
                        self.stdout.write(self.style.WARNING(
                            f'    {alertas_dispositivo} alerta(s) criado(s) para este dispositivo'
                        ))

        # Resumo final
        self.stdout.write(self.style.SUCCESS(
            f'\n✓ Dados de exemplo criados com sucesso!\n'
            f'  • Dispositivos: {dispositivos_criados}\n'
            f'  • Leituras: {leituras_criadas}\n'
            f'  • Alertas: {alertas_criados}\n'
        ))
        
        # Dica para visualizar
        self.stdout.write(self.style.NOTICE(
            f'\nPara visualizar os dados:\n'
            f'  • Admin: http://localhost:8000/admin/treinamento/\n'
            f'  • Dashboard IoT: http://localhost:8000/iot/\n'
            f'  • Dispositivos: http://localhost:8000/iot/devices/\n'
            f'  • Alertas: http://localhost:8000/iot/alerts/\n'
        ))
