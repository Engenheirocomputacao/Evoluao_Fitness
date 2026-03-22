"""
Management command para popular dados dos usuários Protheus e Admin
Período: 05/02/2026 até a data atual
- Mínimo de 3 registros diários por usuário
- Dispositivos IoT com leituras no mesmo período
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from treinamento.models import Individuo, Treinamento, RegistroTreinamento
from treinamento.iot_models import DispositivoIoT, LeituraIoT, ConfiguracaoDispositivo
from datetime import timedelta, date
from decimal import Decimal
import random

class Command(BaseCommand):
    help = 'Popula dados dos usuários Protheus e Admin desde 05/02/2026'

    def add_arguments(self, parser):
        parser.add_argument(
            '--start-date',
            type=str,
            default='2026-02-05',
            help='Data inicial no formato YYYY-MM-DD'
        )

    def get_or_create_user(self, username, full_name, email, is_superuser=False):
        """Cria ou obtém usuário e seu perfil Individuo"""
        try:
            user = User.objects.get(username=username)
            self.stdout.write(f'Usuário {username} já existe.')
        except User.DoesNotExist:
            if is_superuser:
                user = User.objects.create_superuser(username, email, 'adminpass')
            else:
                user = User.objects.create_user(username, email, 'protheus123')
            self.stdout.write(self.style.SUCCESS(f'Usuário {username} criado.'))
        
        # Garante que existe perfil Individuo
        individuo, created = Individuo.objects.get_or_create(
            user=user,
            defaults={
                'nome_completo': full_name,
                'data_nascimento': date(1990, 1, 1),
                'peso': 80.0,
                'sexo': 'masculino',
                'ativo': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Perfil de Indivíduo criado para {username}'))
        
        return individuo

    def create_training_records(self, individuo, start_date, end_date):
        """Cria pelo menos 3 registros diários de treinamento"""
        treinos = list(Treinamento.objects.all())
        
        if not treinos:
            self.stdout.write(self.style.WARNING('Criando treinamentos básicos...'))
            treinos = [
                Treinamento.objects.create(nome="Corrida", unidade_medida="km", descricao="Treino de corrida", esporte="corrida"),
                Treinamento.objects.create(nome="Musculação", unidade_medida="kg", descricao="Treino de força", esporte="musculacao"),
                Treinamento.objects.create(nome="Ciclismo", unidade_medida="km", descricao="Treino de ciclismo", esporte="ciclismo"),
                Treinamento.objects.create(nome="Natação", unidade_medida="min", descricao="Treino de natação", esporte="natacao"),
                Treinamento.objects.create(nome="Caminhada", unidade_medida="km", descricao="Caminhada leve", esporte="caminhada"),
            ]
        
        esportes_map = {
            'corrida': {'valor_base': (5, 15), 'unidade': 'km', 'esforco_base': (6, 9)},
            'musculacao': {'valor_base': (40, 120), 'unidade': 'kg', 'esforco_base': (7, 10)},
            'ciclismo': {'valor_base': (10, 40), 'unidade': 'km', 'esforco_base': (5, 8)},
            'natacao': {'valor_base': (30, 60), 'unidade': 'min', 'esforco_base': (6, 9)},
            'caminhada': {'valor_base': (3, 8), 'unidade': 'km', 'esforco_base': (3, 5)},
        }
        
        count = 0
        current_date = start_date
        
        while current_date <= end_date:
            # Criar pelo menos 3 registros por dia
            num_registros = random.randint(3, 5)
            
            for i in range(num_registros):
                treino = random.choice(treinos)
                esporte = treino.nome.lower()
                
                # Ajustar valores baseados no esporte
                if esporte in esportes_map:
                    valor_min, valor_max = esportes_map[esporte]['valor_base']
                    esforco_min, esforco_max = esportes_map[esporte]['esforco_base']
                else:
                    valor_min, valor_max = 10, 50
                    esforco_min, esforco_max = 5, 8
                
                valor = round(Decimal(random.uniform(valor_min, valor_max)), 2)
                esforco = random.randint(esforco_min, esforco_max)
                
                # Criar duração aleatória
                duracao_minutos = random.randint(20, 90)
                duracao = timedelta(minutes=duracao_minutos)
                
                # Verificar se já existe registro para este horário
                hora_registro = random.randint(6, 21)  # Entre 6h e 21h
                minuto_registro = random.randint(0, 59)
                
                try:
                    from datetime import datetime
                    data_completa = datetime(current_date.year, current_date.month, current_date.day, 
                                           hora_registro, minuto_registro)
                    
                    # Evitar duplicatas exatas
                    if not RegistroTreinamento.objects.filter(
                        individuo=individuo,
                        treinamento=treino,
                        data=current_date,
                        valor_alcançado=valor
                    ).exists():
                        RegistroTreinamento.objects.create(
                            individuo=individuo,
                            treinamento=treino,
                            data=current_date,
                            valor_alcançado=valor,
                            esporte=esporte,
                            esforco_percebido=esforco,
                            duracao=duracao,
                            fonte_dados='manual',
                            confiabilidade=round(Decimal(random.uniform(95, 100)), 2),
                            observacoes=f'Treino automático - período {current_date.strftime("%d/%m/%Y")}'
                        )
                        count += 1
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'Erro ao criar registro: {e}'))
            
            current_date += timedelta(days=1)
        
        return count

    def create_iot_devices_and_readings(self, individuo, start_date, end_date):
        """Cria dispositivos IoT e suas leituras no período especificado"""
        devices_specs = [
            {
                'type': 'heartrate', 
                'name': f'{individuo.nome_completo.split()[0]} Heart Monitor',
                'unit': 'bpm',
                'valor_range': (60, 180),
                'treino_relacionado': 'Corrida'
            },
            {
                'type': 'steps', 
                'name': f'{individuo.nome_completo.split()[0]} Pedometer',
                'unit': 'steps',
                'valor_range': (500, 15000),
                'treino_relacionado': 'Caminhada'
            },
            {
                'type': 'gps', 
                'name': f'{individuo.nome_completo.split()[0]} GPS Watch',
                'unit': 'km',
                'valor_range': (1, 15),
                'treino_relacionado': 'Corrida'
            },
            {
                'type': 'reps', 
                'name': f'{individuo.nome_completo.split()[0]} Rep Counter',
                'unit': 'repetitions',
                'valor_range': (20, 100),
                'treino_relacionado': 'Musculação'
            }
        ]

        count_devices = 0
        count_readings = 0
        
        for spec in devices_specs:
            dev_id = f"{individuo.user.username.upper()}_{spec['type'].upper()}_{random.randint(100, 999)}"
            
            device, created = DispositivoIoT.objects.get_or_create(
                device_id=dev_id,
                defaults={
                    'nome': spec['name'],
                    'tipo': spec['type'],
                    'proprietario': individuo,
                    'status': 'active',
                    'ultimo_ping': timezone.now(),
                    'fabricante': 'FitTech',
                    'modelo': f'FT-{spec["type"].upper()}-001',
                    'firmware_version': '1.0.0'
                }
            )
            
            if created:
                count_devices += 1
                self.stdout.write(self.style.SUCCESS(f'Dispositivo {device.nome} criado.'))
            
            # Configuração do dispositivo
            ConfiguracaoDispositivo.objects.get_or_create(
                dispositivo=device,
                defaults={
                    'intervalo_leitura': 60,
                    'criar_registro_automatico': True,
                    'fator_calibracao': Decimal('1.000'),
                    'offset_calibracao': Decimal('0.00')
                }
            )
            
            # Gerar leituras para todo o período
            current_datetime = timezone.make_aware(timezone.datetime.combine(start_date, timezone.datetime.min.time()))
            end_datetime = timezone.make_aware(timezone.datetime.combine(end_date, timezone.datetime.max.time()))
            
            while current_datetime <= end_datetime:
                # Gerar 3-5 leituras por dia por dispositivo
                num_leituras = random.randint(3, 5)
                
                for _ in range(num_leituras):
                    val = random.uniform(spec['valor_range'][0], spec['valor_range'][1])
                    
                    # Adicionar metadados para GPS
                    metadata = None
                    if spec['type'] == 'gps':
                        metadata = {
                            'latitude': random.uniform(-23.6, -23.4),
                            'longitude': random.uniform(-46.7, -46.5),
                            'altitude': random.uniform(700, 800)
                        }
                    
                    LeituraIoT.objects.create(
                        dispositivo=device,
                        individuo=individuo,
                        timestamp=current_datetime + timedelta(hours=random.randint(6, 20)),
                        tipo_sensor=spec['type'],
                        valor=round(Decimal(val), 2),
                        unidade=spec['unit'],
                        qualidade_sinal=random.choice(['excellent', 'good', 'fair']),
                        nivel_bateria=random.randint(20, 100),
                        metadata=metadata,
                        processado=True
                    )
                    count_readings += 1
                
                current_datetime += timedelta(days=1)
        
        return count_devices, count_readings

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('Iniciando população de dados...'))
        
        # Parse da data inicial
        start_date_str = options['start_date']
        start_date = timezone.datetime.strptime(start_date_str, '%Y-%m-%d').date()
        end_date = timezone.now().date()
        
        self.stdout.write(f'Período: {start_date.strftime("%d/%m/%Y")} até {end_date.strftime("%d/%m/%Y")}')
        self.stdout.write(f'Total de dias: {(end_date - start_date).days + 1}')
        
        # Criar/usuários Protheus e Admin
        self.stdout.write(self.style.SUCCESS('\n=== Criando Usuários ==='))
        
        # Usuário Protheus
        protheus = self.get_or_create_user(
            username='protheus',
            full_name='Protheus Silva',
            email='protheus@example.com',
            is_superuser=False
        )
        
        # Usuário Admin
        admin = self.get_or_create_user(
            username='admin',
            full_name='Administrador do Sistema',
            email='admin@example.com',
            is_superuser=True
        )
        
        # Criar registros de treinamento
        self.stdout.write(self.style.SUCCESS('\n=== Criando Registros de Treinamento ==='))
        
        self.stdout.write(f'\nPopulando dados para Protheus...')
        protheus_count = self.create_training_records(protheus, start_date, end_date)
        self.stdout.write(self.style.SUCCESS(f'{protheus_count} registros criados para Protheus'))
        
        self.stdout.write(f'\nPopulando dados para Admin...')
        admin_count = self.create_training_records(admin, start_date, end_date)
        self.stdout.write(self.style.SUCCESS(f'{admin_count} registros criados para Admin'))
        
        # Criar dispositivos IoT e leituras
        self.stdout.write(self.style.SUCCESS('\n=== Criando Dispositivos IoT e Leituras ==='))
        
        self.stdout.write(f'\nPopulando IoT para Protheus...')
        protheus_devices, protheus_readings = self.create_iot_devices_and_readings(protheus, start_date, end_date)
        self.stdout.write(self.style.SUCCESS(f'{protheus_devices} dispositivos e {protheus_readings} leituras criados para Protheus'))
        
        self.stdout.write(f'\nPopulando IoT para Admin...')
        admin_devices, admin_readings = self.create_iot_devices_and_readings(admin, start_date, end_date)
        self.stdout.write(self.style.SUCCESS(f'{admin_devices} dispositivos e {admin_readings} leituras criados para Admin'))
        
        # Resumo final
        total_registros = RegistroTreinamento.objects.filter(
            individuo__user__username__in=['protheus', 'admin']
        ).count()
        
        total_dispositivos = DispositivoIoT.objects.filter(
            proprietario__user__username__in=['protheus', 'admin']
        ).count()
        
        total_leituras = LeituraIoT.objects.filter(
            individuo__user__username__in=['protheus', 'admin']
        ).count()
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*50))
        self.stdout.write(self.style.SUCCESS('RESUMO FINAL'))
        self.stdout.write(self.style.SUCCESS('='*50))
        self.stdout.write(f'Total de registros de treinamento: {total_registros}')
        self.stdout.write(f'Total de dispositivos IoT: {total_dispositivos}')
        self.stdout.write(f'Total de leituras IoT: {total_leituras}')
        self.stdout.write(self.style.SUCCESS('\nPopulação de dados concluída com sucesso!'))
