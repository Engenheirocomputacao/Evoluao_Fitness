from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from datetime import date, timedelta
import random
from treinamento.models import Treinamento, RegistroTreinamento, Individuo

class Command(BaseCommand):
    help = 'Popula o banco de dados com registros de treinamento para o usuário rodrigues'

    def handle(self, *args, **options):
        # Usuário específico
        username = 'rodrigues'
        
        # Obter ou criar treinamentos
        treinamento_forca, created = Treinamento.objects.get_or_create(
            nome='Força',
            defaults={
                'unidade_medida': 'kg',
                'descricao': 'Treinamento de força e musculação'
            }
        )
        
        treinamento_velocidade, created = Treinamento.objects.get_or_create(
            nome='Velocidade',
            defaults={
                'unidade_medida': 'km',
                'descricao': 'Treinamento de velocidade e corrida'
            }
        )
        
        treinamento_resistencia, created = Treinamento.objects.get_or_create(
            nome='Resistência',
            defaults={
                'unidade_medida': 'min',
                'descricao': 'Treinamento de resistência aeróbica'
            }
        )
        
        # Período de datas solicitado
        data_inicio = date(2025, 11, 1)
        data_fim = date(2026, 1, 9)
        
        total_registros_criados = 0
        
        self.stdout.write(f"Iniciando população de dados para o usuário: {username}")
        self.stdout.write(f"Período: {data_inicio} a {data_fim}")
        self.stdout.write("-" * 50)
        
        try:
            user = User.objects.get(username=username)
            individuo, created = Individuo.objects.get_or_create(
                user=user,
                defaults={
                    'nome_completo': 'Rodrigues',
                    'ativo': True
                }
            )
            
            if created:
                self.stdout.write(f"Indivíduo criado para {username}")
            
            registros_usuario = 0
            
            # Gerar registros para cada dia no período
            data_atual = data_inicio
            while data_atual <= data_fim:
                # Gerar 3 registros diários (um para cada categoria)
                
                # Registro de Força (kg)
                valor_forca = round(random.uniform(40, 120), 2)  # 40-120 kg
                horas_forca = random.randint(0, 1)
                minutos_forca = random.randint(30, 90)
                duracao_forca = timedelta(hours=horas_forca, minutes=minutos_forca)
                esforco_forca = random.randint(3, 9)
                
                # Observações específicas para força
                observacoes_forca = [
                    "Levantamento de peso terra",
                    "Supino reto com barra",
                    "Agachamento livre",
                    "Desenvolvimento militar",
                    "Rosca direta com halteres",
                    "Elevação lateral",
                    "Puxada frontal",
                    "Remada curvada",
                    "Cadeira flexora",
                    "Gêmeos em pé"
                ]
                
                registro, created = RegistroTreinamento.objects.get_or_create(
                    individuo=individuo,
                    treinamento=treinamento_forca,
                    data=data_atual,
                    defaults={
                        'valor_alcançado': valor_forca,
                        'duracao': duracao_forca,
                        'esforco_percebido': esforco_forca,
                        'esporte': 'musculacao',
                        'observacoes': random.choice(observacoes_forca)
                    }
                )
                if created:
                    registros_usuario += 1
                
                # Registro de Velocidade (km)
                valor_velocidade = round(random.uniform(5, 15), 2)  # 5-15 km
                horas_velocidade = random.randint(0, 1)
                minutos_velocidade = random.randint(20, 60)
                duracao_velocidade = timedelta(hours=horas_velocidade, minutes=minutos_velocidade)
                esforco_velocidade = random.randint(4, 10)
                
                # Observações específicas para velocidade
                observacoes_velocidade = [
                    "Sprints de 100 metros",
                    "Corrida intervalada",
                    "Tiros em pista de atletismo",
                    "Corrida de 400 metros",
                    "Progressão de velocidade",
                    "Fartlek training",
                    "Corrida com mudanças de ritmo",
                    "Sprints em subida",
                    "Corrida de resistência de velocidade",
                    "Drills de aceleração"
                ]
                
                registro, created = RegistroTreinamento.objects.get_or_create(
                    individuo=individuo,
                    treinamento=treinamento_velocidade,
                    data=data_atual,
                    defaults={
                        'valor_alcançado': valor_velocidade,
                        'duracao': duracao_velocidade,
                        'esforco_percebido': esforco_velocidade,
                        'esporte': 'corrida',
                        'observacoes': random.choice(observacoes_velocidade)
                    }
                )
                if created:
                    registros_usuario += 1
                
                # Registro de Resistência (minutos)
                valor_resistencia = round(random.uniform(20, 90), 2)  # 20-90 min
                horas_resistencia = valor_resistencia // 60
                minutos_resistencia = int(valor_resistencia % 60)
                duracao_resistencia = timedelta(hours=horas_resistencia, minutes=minutos_resistencia)
                esforco_resistencia = random.randint(3, 8)
                
                # Esportes e observações específicas para resistência
                esportes_resistencia = [
                    ('corrida', 'Corrida contínua moderada'),
                    ('ciclismo', 'Ciclismo estacionário'),
                    ('natacao', 'Natação livre'),
                    ('caminhada', 'Caminhada rápida'),
                    ('outro', 'Pular corda'),
                    ('corrida', 'Corrida na esteira'),
                    ('ciclismo', 'Bicicleta ergométrica'),
                    ('caminhada', 'Caminhada na esteira'),
                    ('outro', 'Step dance'),
                    ('ciclismo', 'Aula de spinning')
                ]
                
                esporte_escolhido, observacao_escolhida = random.choice(esportes_resistencia)
                
                registro, created = RegistroTreinamento.objects.get_or_create(
                    individuo=individuo,
                    treinamento=treinamento_resistencia,
                    data=data_atual,
                    defaults={
                        'valor_alcançado': valor_resistencia,
                        'duracao': duracao_resistencia,
                        'esforco_percebido': esforco_resistencia,
                        'esporte': esporte_escolhido,
                        'observacoes': observacao_escolhida
                    }
                )
                if created:
                    registros_usuario += 1
                
                data_atual += timedelta(days=1)
            
            self.stdout.write(self.style.SUCCESS(f"✓ {username}: {registros_usuario} registros criados"))
            total_registros_criados += registros_usuario
            
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"✗ Usuário {username} não encontrado"))
            self.stdout.write(self.style.WARNING("Dica: Crie o usuário primeiro com: python manage.py createsuperuser ou crie um usuário normal"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Erro ao processar usuário {username}: {e}"))
        
        self.stdout.write("-" * 50)
        self.stdout.write(self.style.SUCCESS(f"Total de registros criados: {total_registros_criados}"))
        
        # Estatísticas finais
        if total_registros_criados > 0:
            total_registros_db = RegistroTreinamento.objects.count()
            self.stdout.write(f"Total de registros no banco: {total_registros_db}")
            
            # Registros do usuário rodrigues
            try:
                user = User.objects.get(username=username)
                individuo = Individuo.objects.get(user=user)
                count = RegistroTreinamento.objects.filter(individuo=individuo).count()
                self.stdout.write(f"- {username}: {count} registros")
                
                # Estatísticas por tipo de treinamento
                for treinamento in [treinamento_forca, treinamento_velocidade, treinamento_resistencia]:
                    count_tipo = RegistroTreinamento.objects.filter(
                        individuo=individuo, 
                        treinamento=treinamento
                    ).count()
                    self.stdout.write(f"  - {treinamento.nome}: {count_tipo} registros")
                    
            except:
                self.stdout.write(f"- {username}: 0 registros")
