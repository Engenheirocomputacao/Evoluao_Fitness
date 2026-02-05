"""
Management command para popular o aplicativo com dados completos e realistas
Simula uso em PC, Mobile e IoT
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from django.db import transaction
from treinamento.models import Individuo, Treinamento, RegistroTreinamento
from treinamento.iot_models import DispositivoIoT, LeituraIoT, ConfiguracaoDispositivo, AlertaIoT
from treinamento.services.iot_processor import IoTDataProcessor
from datetime import timedelta, datetime
from decimal import Decimal
import random
import time

class Command(BaseCommand):
    help = 'Popula o aplicativo com dados completos para demonstração (PC, Mobile, IoT)'

    def add_arguments(self, parser):
        parser.add_argument('--users', type=int, default=5, help='Número de usuários para criar')
        parser.add_argument('--months', type=int, default=6, help='Meses de histórico para gerar')
        parser.add_argument('--clean', action='store_true', help='Limpar dados existentes antes de criar')

    def handle(self, *args, **options):
        num_users = options['users']
        months_history = options['months']
        clean_db = options['clean']

        if clean_db:
            self.stdout.write(self.style.WARNING('Limpando banco de dados...'))
            LeituraIoT.objects.all().delete()
            AlertaIoT.objects.all().delete()
            ConfiguracaoDispositivo.objects.all().delete()
            DispositivoIoT.objects.all().delete()
            RegistroTreinamento.objects.all().delete()
            # Não deletamos Indivíduos/Users para não quebrar login atual, apenas dados relacionados
            self.stdout.write(self.style.SUCCESS('Dados limpos com sucesso!'))

        self.stdout.write(self.style.NOTICE(f'Iniciando população massiva...'))
        self.stdout.write(f'- Usuários: {num_users}')
        self.stdout.write(f'- Histórico: {months_history} meses')

        # 1. Configurar Tipos de Treinamento Básicos
        self._setup_training_types()

        # 2. Criar/Atualizar Usuários
        users = self._create_users(num_users)

        # 3. Gerar Histórico de Treinos Manuais (PC/Mobile)
        for user in users:
            self._generate_manual_history(user, months_history)

        # 4. Gerar Dispositivos e Dados IoT
        for user in users:
            self._generate_iot_data(user, months_history)

        self.stdout.write(self.style.SUCCESS('\nPopulação concluída com sucesso!'))
        self.stdout.write(self.style.NOTICE('Credenciais padrão: username=user_X, password=password123'))

    def _setup_training_types(self):
        types = [
            ('Musculação', 'kg', 'Treino de força e hipertrofia'),
            ('Corrida', 'km', 'Corrida livre ou esteira'),
            ('Caminhada', 'km', 'Caminhada leve ou moderada'),
            ('Ciclismo', 'km', 'Bicicleta ergométrica ou estrada'),
            ('Natação', 'm', 'Natação em piscina'),
            ('HIIT', 'kcal', 'Treino intervalado de alta intensidade'),
            ('Yoga', 'min', 'Prática de Yoga e flexibilidade'),
            ('Crossfit', 'rep', 'WODs e exercícios funcionais'),
        ]
        count = 0
        for name, unit, desc in types:
            _, created = Treinamento.objects.get_or_create(
                nome=name,
                defaults={'unidade_medida': unit, 'descricao': desc}
            )
            if created: count += 1
        self.stdout.write(f'✓ Tipos de treinamento configurados ({count} criados)')

    def _create_users(self, num):
        users = []
        profiles = [
            {'sexo': 'masculino', 'peso_base': 75, 'perfil': 'iniciante'},
            {'sexo': 'feminino', 'peso_base': 60, 'perfil': 'intermediario'},
            {'sexo': 'masculino', 'peso_base': 85, 'perfil': 'avancado'},
            {'sexo': 'feminino', 'peso_base': 55, 'perfil': 'atleta'},
            {'sexo': 'masculino', 'peso_base': 95, 'perfil': 'perda_peso'},
        ]

        for i in range(num):
            profile = profiles[i % len(profiles)]
            username = f'user_{i+1}'
            
            user, created = User.objects.get_or_create(username=username, defaults={'email': f'{username}@fit.com'})
            if created:
                user.set_password('password123')
                user.save()

            individuo, _ = Individuo.objects.get_or_create(
                user=user,
                defaults={
                    'nome_completo': f'Usuário {profile["perfil"].title()} {i+1}',
                    'data_nascimento': timezone.now().date() - timedelta(days=365*random.randint(20, 40)),
                    'peso': profile['peso_base'],
                    'sexo': profile['sexo'],
                    'ativo': True
                }
            )
            users.append(individuo)
        
        self.stdout.write(f'✓ {len(users)} usuários processados')
        return users

    def _generate_manual_history(self, user, months):
        """Gera histórico de treinos manuais simulando inserção via App/Web"""
        start_date = timezone.now() - timedelta(days=30*months)
        current_date = start_date
        records_count = 0

        # Define frequência baseada no perfil (simplificado aqui)
        frequency = random.choice([2, 3, 4, 5]) # dias por semana
        
        while current_date < timezone.now():
            if current_date.weekday() < frequency: # Simula dias de treino
                # Escolhe 1 ou 2 treinos por dia
                for _ in range(random.randint(1, 2)):
                    treino = Treinamento.objects.order_by('?').first()
                    
                    # Gera valor realista
                    valor = 0
                    if treino.unidade_medida == 'km':
                        valor = random.uniform(3, 15)
                    elif treino.unidade_medida == 'kg':
                        valor = random.uniform(20, 100)
                    elif treino.unidade_medida == 'min':
                        valor = random.uniform(30, 90)
                    else:
                        valor = random.uniform(10, 500)

                    RegistroTreinamento.objects.create(
                        individuo=user,
                        treinamento=treino,
                        data=current_date.date(),
                        valor_alcançado=round(Decimal(valor), 2),
                        esporte=treino.nome.lower(),
                        fonte_dados='manual',
                        confiabilidade=100,
                        observacoes=f"Treino registrado via App Mobile em {current_date.strftime('%d/%m/%Y')}"
                    )
                    records_count += 1
            
            current_date += timedelta(days=1)
        
        self.stdout.write(f'  - {user.nome_completo}: {records_count} registros manuais criados')

    def _generate_iot_data(self, user, months):
        """Gera dispositivos e histórico de sensores"""
        # Cria dispositivos
        devices_config = [
            {'type': 'heartrate', 'name': 'Monitor Cardíaco Pro', 'unit': 'bpm'},
            {'type': 'steps', 'name': 'Smart Band 5', 'unit': 'steps'},
            {'type': 'gps', 'name': 'GPS Tracker X', 'unit': 'km'}
        ]
        
        # Seleciona 1 ou 2 dispositivos para o usuário
        user_devices = random.sample(devices_config, random.randint(1, 2))
        
        total_readings = 0
        
        for dev_conf in user_devices:
            dev_id = f"{dev_conf['type'].upper()}_{user.id}_{random.randint(1000, 9999)}"
            device, _ = DispositivoIoT.objects.get_or_create(
                device_id=dev_id,
                defaults={
                    'nome': dev_conf['name'],
                    'tipo': dev_conf['type'],
                    'proprietario': user,
                    'status': 'active',
                    'ultimo_ping': timezone.now()
                }
            )
            
            # Configuração
            ConfiguracaoDispositivo.objects.get_or_create(
                dispositivo=device,
                defaults={
                    'intervalo_leitura': 60,
                    'criar_registro_automatico': dev_conf['type'] in ['steps', 'gps'],
                    'treinamento_padrao': Treinamento.objects.get(nome='Caminhada') if dev_conf['type'] == 'steps' else None
                }
            )

            # Gera leituras para os últimos 7 dias (para não explodir o banco com meses de dados segundo a segundo)
            # Para meses anteriores, gera apenas "resumos" diários
            
            # 1. Dados detalhados (última semana)
            start_date = timezone.now() - timedelta(days=7)
            current = start_date
            
            while current < timezone.now():
                # Simula uso durante o dia (8h as 22h)
                if 8 <= current.hour <= 22:
                    should_record = False
                    if dev_conf['type'] == 'heartrate':
                        should_record = True # Monitora sempre
                    elif dev_conf['type'] == 'steps':
                        should_record = random.random() > 0.5 # Caminha as vezes
                    else:
                        should_record = random.random() > 0.9 # GPS liga pouco
                    
                    if should_record:
                        # Gera leitura
                        val = 0
                        if dev_conf['type'] == 'heartrate':
                            val = random.normalvariate(80, 15)
                        elif dev_conf['type'] == 'steps':
                            val = random.randint(0, 100) # Passos no intervalo
                        else:
                            val = random.uniform(0.1, 0.5) # Km
                            
                        LeituraIoT.objects.create(
                            dispositivo=device,
                            individuo=user,
                            timestamp=current,
                            tipo_sensor=dev_conf['type'],
                            valor=round(Decimal(val), 2),
                            unidade=dev_conf['unit'],
                            qualidade_sinal='good',
                            processado=True
                        )
                        total_readings += 1
                        
                # Avança tempo (simulando intervalos de 1 hora para não ficar muito lento o script)
                current += timedelta(hours=1)

        self.stdout.write(f'  - {user.nome_completo}: {len(user_devices)} dispositivos, {total_readings} leituras recentes')
