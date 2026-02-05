"""
Management command para popular especificamente o usuário ADMIN
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from treinamento.models import Individuo, Treinamento, RegistroTreinamento
from treinamento.iot_models import DispositivoIoT, LeituraIoT, ConfiguracaoDispositivo
from datetime import timedelta
from decimal import Decimal
import random

class Command(BaseCommand):
    help = 'Popula o usuário admin com dados de teste'

    def handle(self, *args, **options):
        username = 'admin' # Assumindo que o usuário logado é 'admin'
        
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Usuário {username} não encontrado!'))
            return

        # Garante que existe um perfil de Individuo
        individuo, created = Individuo.objects.get_or_create(
            user=user,
            defaults={
                'nome_completo': 'Administrador do Sistema',
                'data_nascimento': '1990-01-01',
                'peso': 80.0,
                'sexo': 'masculino',
                'ativo': True
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'Perfil de Indivíduo criado para {username}'))

        self.stdout.write(self.style.NOTICE(f'Populando dados para: {individuo.nome_completo}'))

        # 1. Gerar Treinos Manuais (Últimos 3 meses)
        treinos = list(Treinamento.objects.all())
        if not treinos:
            self.stdout.write(self.style.ERROR('Nenhum tipo de treinamento encontrado. Rode populate_full_app primeiro ou crie treinos.'))
            return

        count_manual = 0
        start_date = timezone.now() - timedelta(days=90)
        current = start_date
        
        while current < timezone.now():
            if current.weekday() in [0, 2, 4, 6]: # 4x por semana
                treino = random.choice(treinos)
                val = random.uniform(5, 50) if treino.unidade_medida == 'km' else random.uniform(20, 100)
                
                RegistroTreinamento.objects.create(
                    individuo=individuo,
                    treinamento=treino,
                    data=current.date(),
                    valor_alcançado=round(Decimal(val), 2),
                    esporte=treino.nome.lower(),
                    fonte_dados='manual',
                    confiabilidade=100
                )
                count_manual += 1
            current += timedelta(days=1)
            
        self.stdout.write(f'✓ {count_manual} registros manuais criados')

        # 2. Criar Dispositivos IoT
        devices_specs = [
            {'type': 'heartrate', 'name': 'Admin Heart Monitor', 'unit': 'bpm'},
            {'type': 'steps', 'name': 'Admin Pedometer', 'unit': 'steps'},
            {'type': 'gps', 'name': 'Admin GPS Watch', 'unit': 'km'}
        ]

        count_iot = 0
        for spec in devices_specs:
            dev_id = f"ADMIN_{spec['type'].upper()}_{random.randint(100,999)}"
            device, _ = DispositivoIoT.objects.get_or_create(
                device_id=dev_id,
                defaults={
                    'nome': spec['name'],
                    'tipo': spec['type'],
                    'proprietario': individuo,
                    'status': 'active',
                    'ultimo_ping': timezone.now()
                }
            )
            
            # Configuração
            ConfiguracaoDispositivo.objects.get_or_create(
                dispositivo=device,
                defaults={
                    'intervalo_leitura': 60,
                    'criar_registro_automatico': True
                }
            )

            # Gerar leituras recentes (últimas 24h a cada 15 min)
            current_time = timezone.now() - timedelta(hours=24)
            while current_time < timezone.now():
                val = 0
                if spec['type'] == 'heartrate': val = random.uniform(60, 140)
                elif spec['type'] == 'steps': val = random.randint(0, 500)
                else: val = random.uniform(0, 2)

                LeituraIoT.objects.create(
                    dispositivo=device,
                    individuo=individuo,
                    timestamp=current_time,
                    tipo_sensor=spec['type'],
                    valor=round(Decimal(val), 2),
                    unidade=spec['unit'],
                    qualidade_sinal='good',
                    processado=True
                )
                count_iot += 1
                current_time += timedelta(minutes=15)

        self.stdout.write(f'✓ {len(devices_specs)} dispositivos e {count_iot} leituras IoT criadas')
        self.stdout.write(self.style.SUCCESS('Admin populado com sucesso!'))
