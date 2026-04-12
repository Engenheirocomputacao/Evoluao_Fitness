"""
Management command para popular dados realistas de treino e IoT para o usuário Protheus
Período: 15/03/2026 até 12/04/2026
- Foco em Ciclismo, Natação e Corrida
- Tipos: Força, Velocidade e Resistência
- Dispositivos IoT com dados correlacionados
- Device/25 com localização em Sorocaba
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from treinamento.models import Individuo, Treinamento, RegistroTreinamento
from treinamento.iot_models import DispositivoIoT, LeituraIoT, ConfiguracaoDispositivo
from datetime import timedelta, date, datetime
from decimal import Decimal
import random
import json

class Command(BaseCommand):
    help = 'Popula dados realistas de treino e IoT para Protheus (15/03/2026 a 12/04/2026)'

    def handle(self, *args, **options):
        # Configurações
        data_inicio = date(2026, 3, 15)
        data_fim = date(2026, 4, 12)
        username = 'Protheus'
        
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.SUCCESS('🏋️ POPULAÇÃO DE DADOS - USUÁRIO PROTHEUS'))
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(f'📅 Período: {data_inicio} até {data_fim}')
        self.stdout.write(f'👤 Usuário: {username}')
        self.stdout.write('-'*70)
        
        # Obter ou criar usuário Protheus
        individuo = self.get_or_create_protheus(username)
        
        # Criar treinamentos necessários
        treinos = self.create_training_types()
        
        # Gerar registros de treino realistas
        total_treinos = self.create_realistic_training_records(individuo, treinos, data_inicio, data_fim)
        self.stdout.write(self.style.SUCCESS(f'\n✅ {total_treinos} registros de treino criados!'))
        
        # Criar dispositivos IoT e leituras
        total_devices, total_readings = self.create_iot_devices_and_readings(individuo, data_inicio, data_fim)
        self.stdout.write(self.style.SUCCESS(f'✅ {total_devices} dispositivos IoT criados!'))
        self.stdout.write(self.style.SUCCESS(f'✅ {total_readings} leituras IoT criadas!'))
        
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('🎉 POPULAÇÃO CONCLUÍDA COM SUCESSO!'))
        self.stdout.write(self.style.SUCCESS('='*70))
        self.stdout.write(self.style.WARNING('\n💡 Dicas:'))
        self.stdout.write('   • Acesse /treinamento/registros/ para ver os treinos')
        self.stdout.write('   • Acesse /iot/ para ver dispositivos e leituras')
        self.stdout.write('   • Dispositivo 25 tem localização em Sorocaba/SP\n')

    def get_or_create_protheus(self, username):
        """Cria ou obtém usuário Protheus"""
        try:
            user = User.objects.get(username=username)
            self.stdout.write(f'✅ Usuário {username} encontrado')
        except User.DoesNotExist:
            user = User.objects.create_user(
                username=username,
                email='protheus@evolucaofitness.com',
                password='protheus123'
            )
            self.stdout.write(self.style.SUCCESS(f'✅ Usuário {username} criado'))
        
        individuo, created = Individuo.objects.get_or_create(
            user=user,
            defaults={
                'nome_completo': 'Protheus Silva',
                'data_nascimento': date(1992, 5, 15),
                'peso': Decimal('78.5'),
                'sexo': 'masculino',
                'ativo': True,
                'endereco_cidade': 'Sorocaba',
                'endereco_estado': 'SP',
            }
        )
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✅ Perfil de Protheus criado'))
        
        return individuo

    def create_training_types(self):
        """Cria tipos de treinamento necessários"""
        treinos_data = [
            ('Força', 'kg', 'Treinamento de força e musculação'),
            ('Velocidade', 'km', 'Treinamento de velocidade e sprints'),
            ('Resistência', 'min', 'Treinamento de resistência aeróbica'),
            ('Ciclismo', 'km', 'Treino de bicicleta - estrada ou ergométrica'),
            ('Natação', 'm', 'Treino de natação em piscina'),
            ('Corrida', 'km', 'Treino de corrida - rua ou esteira'),
        ]
        
        treinos = {}
        for nome, unidade, descricao in treinos_data:
            treino, created = Treinamento.objects.get_or_create(
                nome=nome,
                defaults={
                    'unidade_medida': unidade,
                    'descricao': descricao
                }
            )
            treinos[nome] = treino
            if created:
                self.stdout.write(f'   📝 Treinamento "{nome}" criado')
        
        return treinos

    def create_realistic_training_records(self, individuo, treinos, data_inicio, data_fim):
        """Cria registros de treino realistas com progressão"""
        count = 0
        
        # Planos de treino semanais realistas
        # Cada semana tem foco diferente
        plano_semanal = [
            # Segunda, Terça, Quarta, Quinta, Sexta, Sábado, Domingo
            ['Corrida', 'Força', 'Natação', 'Velocidade', 'Ciclismo', 'Resistência', None],  # Semana 1
            ['Ciclismo', 'Natação', 'Força', 'Corrida', 'Resistência', 'Velocidade', None],  # Semana 2
            ['Natação', 'Corrida', 'Ciclismo', 'Força', 'Velocidade', 'Resistência', None],  # Semana 3
            ['Força', 'Ciclismo', 'Corrida', 'Natação', 'Resistência', 'Velocidade', None],  # Semana 4
        ]
        
        # Histórico de desempenho para progressão realista
        historico = {
            'Corrida': {'valor_base': 7.0, 'progressao': 0.15},  # km - melhora 0.15km por semana
            'Ciclismo': {'valor_base': 25.0, 'progressao': 0.8},  # km - melhora 0.8km por semana
            'Natação': {'valor_base': 1500, 'progressao': 50},  # metros - melhora 50m por semana
            'Força': {'valor_base': 65.0, 'progressao': 1.2},  # kg - melhora 1.2kg por semana
            'Velocidade': {'valor_base': 5.5, 'progressao': 0.1},  # km - melhora 0.1km por semana
            'Resistência': {'valor_base': 45, 'progressao': 2},  # min - melhora 2min por semana
        }
        
        # Observações realistas por tipo de treino
        observacoes_map = {
            'Corrida': [
                'Corrida leve no parque',
                'Treino intervalado na esteira',
                'Corrida longa - preparação para prova',
                'Rodagem leve regenerativa',
                'Corrida com elevação - treino de subidas',
            ],
            'Ciclismo': [
                'Pedal estrada - rota clássica',
                'Treino de cadência na ergométrica',
                'Percorro longo - resistência',
                'Treino de sprint final',
                'Rodagem leve com amigos',
            ],
            'Natação': [
                'Treino de técnica - crawl',
                'Séries de velocidade',
                'Natação contínua - resistência',
                'Treino de pernada e braçada',
                'Séries mistas - todos os estilos',
            ],
            'Força': [
                'Treino de membros superiores',
                'Treino de membros inferiores',
                'Circuito funcional',
                'Treino de core e estabilidade',
                'Superséries - peitoral e costas',
            ],
            'Velocidade': [
                'Tiros de 400m',
                'Sprints curtos - 100m',
                'Treino de velocidade progressiva',
                'Intervalado de alta intensidade',
                'Velocidade com resistência',
            ],
            'Resistência': [
                'Treino aeróbico zone 2',
                'Bike longa - resistência',
                'Corrida longa contínua',
                'Treino misto - bike + corrida',
                'Resistência muscular localizada',
            ],
        }
        
        data_atual = data_inicio
        semana_atual = 0
        
        while data_atual <= data_fim:
            # Determina semana atual (0-3)
            dias_decorridos = (data_atual - data_inicio).days
            semana_atual = (dias_decorridos // 7) % 4
            
            # Dia da semana (0=segunda, 6=domingo)
            dia_semana = data_atual.weekday()
            
            # Obtém treino do plano semanal
            treino_nome = plano_semanal[semana_atual][dia_semana]
            
            if treino_nome:
                treino = treinos[treino_nome]
                
                # Calcula valor com progressão
                semanas_treino = dias_decorridos // 7
                hist = historico[treino_nome]
                valor_base = hist['valor_base'] + (hist['progressao'] * semanas_treino)
                
                # Adiciona variação realista (±10%)
                variacao = random.uniform(-0.10, 0.10)
                valor = valor_base * (1 + variacao)
                
                # Arredonda conforme tipo
                if treino_nome in ['Corrida', 'Ciclismo', 'Velocidade']:
                    valor = round(valor, 2)
                elif treino_nome == 'Natação':
                    valor = int(valor / 50) * 50  # Múltiplos de 50m
                else:
                    valor = round(valor, 1)
                
                # Calcula duração proporcional ao valor
                duracao_base = {
                    'Corrida': valor * 5.5,  # ~5:30 min/km
                    'Ciclismo': valor * 2.2,  # ~27 km/h
                    'Natação': valor * 0.025,  # ~1:40/100m
                    'Força': random.randint(45, 75),
                    'Velocidade': random.randint(30, 50),
                    'Resistência': valor,
                }
                duracao_minutos = int(duracao_base.get(treino_nome, 45))
                duracao = timedelta(minutes=duracao_minutos)
                
                # Esforço percebido baseado no tipo e duração
                esforco_base = {
                    'Corrida': 7,
                    'Ciclismo': 6,
                    'Natação': 7,
                    'Força': 8,
                    'Velocidade': 9,
                    'Resistência': 6,
                }
                esforco = min(10, max(1, esforco_base.get(treino_nome, 6) + random.randint(-1, 1)))
                
                # Esporte relacionado
                esporte_map = {
                    'Corrida': 'corrida',
                    'Ciclismo': 'ciclismo',
                    'Natação': 'natacao',
                    'Força': 'musculacao',
                    'Velocidade': 'corrida',
                    'Resistência': 'caminhada',
                }
                esporte = esporte_map.get(treino_nome, 'outro')
                
                # Observação realista
                observacao = random.choice(observacoes_map.get(treino_nome, ['Treino regular']))
                
                # GPS track para atividades ao ar livre
                percurso_gps = None
                if treino_nome in ['Corrida', 'Ciclismo', 'Velocidade']:
                    # Simula coordenadas de Sorocaba
                    lat_base = -23.5015 + random.uniform(-0.02, 0.02)
                    lon_base = -47.4526 + random.uniform(-0.02, 0.02)
                    percurso_gps = {
                        'type': 'LineString',
                        'coordinates': [
                            [lon_base, lat_base],
                            [lon_base + random.uniform(0.001, 0.005), lat_base + random.uniform(-0.001, 0.001)],
                            [lon_base + random.uniform(0.002, 0.008), lat_base + random.uniform(-0.002, 0.002)],
                            [lon_base + random.uniform(0.003, 0.010), lat_base + random.uniform(-0.003, 0.003)],
                        ]
                    }
                
                # Cria registro
                try:
                    RegistroTreinamento.objects.create(
                        individuo=individuo,
                        treinamento=treino,
                        data=data_atual,
                        valor_alcançado=Decimal(str(valor)),
                        esporte=esporte,
                        esforco_percebido=esforco,
                        duracao=duracao,
                        percurso_gps=percurso_gps,
                        fonte_dados='manual',
                        confiabilidade=Decimal('100.00'),
                        observacoes=observacao
                    )
                    count += 1
                    
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f'   ❌ Erro em {data_atual}: {e}'))
            
            data_atual += timedelta(days=1)
        
        self.stdout.write(f'\n📊 Registros de treino criados: {count}')
        return count

    def create_iot_devices_and_readings(self, individuo, data_inicio, data_fim):
        """Cria dispositivos IoT e leituras correlacionadas"""
        devices_count = 0
        readings_count = 0
        
        # Configurações de dispositivos
        devices_config = [
            {
                'device_id': 'PROTHEUS_HR_001',
                'nome': 'Protheus Heart Monitor',
                'tipo': 'heartrate',
                'unidade': 'bpm',
                'valor_range': (65, 175),
                'treino_relacionado': ['Corrida', 'Ciclismo', 'Natação'],
            },
            {
                'device_id': 'PROTHEUS_GPS_002',
                'nome': 'Protheus GPS Watch',
                'tipo': 'gps',
                'unidade': 'km',
                'valor_range': (3, 45),
                'treino_relacionado': ['Corrida', 'Ciclismo', 'Velocidade'],
                'sorocaba_location': True,  # Device 25 terá localização Sorocaba
            },
            {
                'device_id': 'PROTHEUS_STEPS_003',
                'nome': 'Protheus Step Counter',
                'tipo': 'steps',
                'unidade': 'steps',
                'valor_range': (500, 15000),
                'treino_relacionado': ['Corrida', 'Resistência'],
            },
            {
                'device_id': 'PROTHEUS_REPS_004',
                'nome': 'Protheus Rep Counter',
                'tipo': 'reps',
                'unidade': 'rep',
                'valor_range': (20, 150),
                'treino_relacionado': ['Força'],
            },
        ]
        
        # Cria dispositivos
        for idx, config in enumerate(devices_config, start=22):  # Começa do 22 para chegar no 25
            dispositivo, created = DispositivoIoT.objects.get_or_create(
                device_id=config['device_id'],
                defaults={
                    'nome': config['nome'],
                    'tipo': config['tipo'],
                    'proprietario': individuo,
                    'status': 'active',
                    'ultimo_ping': datetime.now(),
                    'fabricante': 'ESP32 Fitness',
                    'modelo': f'ESP32-{config["tipo"].upper()}-V2',
                    'mac_address': f'00:1A:2B:{idx:02X}:4C:{idx:02X}',
                }
            )
            
            if created:
                devices_count += 1
                self.stdout.write(f'   📱 Dispositivo {config["device_id"]} criado (ID: {dispositivo.id})')
                
                # Cria configuração do dispositivo
                ConfiguracaoDispositivo.objects.get_or_create(
                    dispositivo=dispositivo,
                    defaults={
                        'intervalo_leitura': 30 if config['tipo'] == 'heartrate' else 60,
                        'criar_registro_automatico': True,
                        'valor_minimo_alerta': Decimal(str(config['valor_range'][0] * 0.8)),
                        'valor_maximo_alerta': Decimal(str(config['valor_range'][1] * 1.2)),
                    }
                )
            
            # Gera leituras IoT para cada dia de treino
            leituras = self.generate_iot_readings(
                dispositivo, 
                individuo, 
                data_inicio, 
                data_fim,
                config,
                dispositivo.id == 25  # Se for device 25, usa Sorocaba
            )
            readings_count += leituras
        
        self.stdout.write(f'\n📡 Dispositivos IoT: {devices_count}')
        self.stdout.write(f'📊 Leituras IoT: {readings_count}')
        
        return devices_count, readings_count

    def generate_iot_readings(self, dispositivo, individuo, data_inicio, data_fim, config, is_sorocaba=False):
        """Gera leituras IoT realistas para o período"""
        count = 0
        
        # Coordenadas de Sorocaba
        sorocaba_coords = {
            'lat': -23.5015,
            'lon': -47.4526,
            'cidade': 'Sorocaba',
            'estado': 'SP',
        }
        
        data_atual = data_inicio
        
        while data_atual <= data_fim:
            # Pula domingos (dia de descanso)
            if data_atual.weekday() == 6:
                data_atual += timedelta(days=1)
                continue
            
            # Número de leituras por dia baseado no tipo
            if dispositivo.tipo == 'heartrate':
                # Durante treino: leitura a cada 30 min (6h de treino = 12 leituras)
                num_leituras = random.randint(8, 16)
            elif dispositivo.tipo == 'gps':
                # GPS: leitura a cada km (~5-10 pontos)
                num_leituras = random.randint(5, 12)
            elif dispositivo.tipo == 'steps':
                # Passos: leitura por hora ativa (12h * 500-2000 passos/hora)
                num_leituras = random.randint(1, 3)  # Agregado
            else:
                # Reps: durante treino de força
                num_leituras = random.randint(3, 8)
            
            for i in range(num_leituras):
                # Timestamp durante o dia (6h-21h)
                hora = random.randint(6, 20)
                minuto = random.randint(0, 59)
                timestamp = datetime(data_atual.year, data_atual.month, data_atual.day, hora, minuto)
                
                # Valor baseado no tipo
                valor_min, valor_max = config['valor_range']
                
                if dispositivo.tipo == 'heartrate':
                    # Simula variação durante treino
                    if random.random() < 0.3:
                        # Zona de aquecimento
                        valor = random.uniform(90, 120)
                    elif random.random() < 0.6:
                        # Zona aeróbica
                        valor = random.uniform(130, 155)
                    else:
                        # Zona anaeróbica
                        valor = random.uniform(155, valor_max)
                elif dispositivo.tipo == 'gps' and is_sorocaba:
                    # GPS com coordenadas de Sorocaba
                    valor = random.uniform(valor_min, valor_max)
                    
                else:
                    valor = random.uniform(valor_min, valor_max)
                
                # Metadados
                metadata = {
                    'qualidade_sinal': random.choice(['excellent', 'good', 'good', 'fair']),
                    'nivel_bateria': random.randint(35, 100),
                }
                
                # Adiciona localização para GPS em Sorocaba
                if dispositivo.tipo == 'gps' and is_sorocaba:
                    metadata.update({
                        'location': {
                            'city': sorocaba_coords['cidade'],
                            'state': sorocaba_coords['estado'],
                            'country': 'Brasil',
                        },
                        'gps_coordinates': {
                            'latitude': sorocaba_coords['lat'] + random.uniform(-0.03, 0.03),
                            'longitude': sorocaba_coords['lon'] + random.uniform(-0.03, 0.03),
                            'altitude': random.uniform(580, 650),  # Altitude de Sorocaba
                        },
                        'route_name': random.choice([
                            'Parque das Águas - Sorocaba',
                            'Trilha do Campolim',
                            'Rota Itavuvu',
                            'Centro Histórico - Sorocaba',
                            'Parque Linear - Sorocaba',
                        ])
                    })
                elif dispositivo.tipo == 'heartrate':
                    metadata['zona_treinamento'] = random.choice([
                        'aquecimento', 'aerobica', 'anaerobica', 'recuperacao'
                    ])
                
                # Cria leitura
                try:
                    LeituraIoT.objects.create(
                        dispositivo=dispositivo,
                        individuo=individuo,
                        timestamp=timestamp,
                        tipo_sensor=dispositivo.tipo,
                        valor=round(Decimal(str(valor)), 2),
                        unidade=config['unidade'],
                        qualidade_sinal=metadata['qualidade_sinal'],
                        nivel_bateria=metadata['nivel_bateria'],
                        metadata=metadata,
                        processado=True,
                    )
                    count += 1
                except Exception as e:
                    pass  # Silenciosamente ignora duplicatas
            
            data_atual += timedelta(days=1)
        
        return count
