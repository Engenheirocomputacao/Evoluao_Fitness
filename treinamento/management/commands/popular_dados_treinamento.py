from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from datetime import date, timedelta
import random
from treinamento.models import Treinamento, RegistroTreinamento, Individuo

class Command(BaseCommand):
    help = 'Popula o banco de dados com registros de treinamento para múltiplos usuários'

    def handle(self, *args, **options):
        # Lista de usuários
        usernames = ['Carlos@', 'Newuser', 'carlos@', 'carlos@1', 'maria', 'pamela', 'testeusuario_']
        
        # Obter treinamentos
        try:
            treinamento_forca = Treinamento.objects.get(nome='Força')
            treinamento_velocidade = Treinamento.objects.get(nome='Velocidade')
            treinamento_resistencia = Treinamento.objects.get(nome='Resistência')
        except Treinamento.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f'Treinamento não encontrado: {e}'))
            return
        
        # Período de datas
        data_inicio = date(2025, 11, 1)
        data_fim = date(2025, 12, 31)
        
        total_registros_criados = 0
        
        self.stdout.write(f"Iniciando população de dados...")
        self.stdout.write(f"Período: {data_inicio} a {data_fim}")
        self.stdout.write(f"Usuários: {', '.join(usernames)}")
        self.stdout.write("-" * 50)
        
        for username in usernames:
            try:
                user = User.objects.get(username=username)
                individuo, created = Individuo.objects.get_or_create(user=user)
                
                if created:
                    self.stdout.write(f"Indivíduo criado para {username}")
                
                registros_usuario = 0
                
                # Gerar registros para cada dia no período
                data_atual = data_inicio
                while data_atual <= data_fim:
                    # Pular alguns dias aleatoriamente para simular realidade (80% de chance de treinar)
                    if random.random() < 0.8:
                        # Gerar 3 registros diários (um para cada categoria)
                        
                        # Registro de Força (kg)
                        valor_forca = round(random.uniform(20, 150), 2)  # 20-150 kg
                        duracao_forca = timedelta(minutes=random.randint(30, 90))
                        esforco_forca = random.randint(3, 9)
                        
                        registro, created = RegistroTreinamento.objects.get_or_create(
                            individuo=individuo,
                            treinamento=treinamento_forca,
                            data=data_atual,
                            defaults={
                                'valor_alcançado': valor_forca,
                                'duracao': duracao_forca,
                                'esforco_percebido': esforco_forca,
                                'observacoes': f'Treino de força dia {data_atual.day}'
                            }
                        )
                        if created:
                            registros_usuario += 1
                        
                        # Registro de Velocidade (km/h)
                        valor_velocidade = round(random.uniform(8, 25), 2)  # 8-25 km/h
                        duracao_velocidade = timedelta(minutes=random.randint(20, 60))
                        esforco_velocidade = random.randint(4, 10)
                        
                        registro, created = RegistroTreinamento.objects.get_or_create(
                            individuo=individuo,
                            treinamento=treinamento_velocidade,
                            data=data_atual,
                            defaults={
                                'valor_alcançado': valor_velocidade,
                                'duracao': duracao_velocidade,
                                'esforco_percebido': esforco_velocidade,
                                'observacoes': f'Treino de velocidade dia {data_atual.day}'
                            }
                        )
                        if created:
                            registros_usuario += 1
                        
                        # Registro de Resistência (minutos)
                        valor_resistencia = round(random.uniform(15, 120), 2)  # 15-120 min
                        duracao_resistencia = timedelta(minutes=int(valor_resistencia))
                        esforco_resistencia = random.randint(3, 8)
                        
                        registro, created = RegistroTreinamento.objects.get_or_create(
                            individuo=individuo,
                            treinamento=treinamento_resistencia,
                            data=data_atual,
                            defaults={
                                'valor_alcançado': valor_resistencia,
                                'duracao': duracao_resistencia,
                                'esforco_percebido': esforco_resistencia,
                                'observacoes': f'Treino de resistência dia {data_atual.day}'
                            }
                        )
                        if created:
                            registros_usuario += 1
                    
                    data_atual += timedelta(days=1)
                
                self.stdout.write(self.style.SUCCESS(f"✓ {username}: {registros_usuario} registros criados"))
                total_registros_criados += registros_usuario
                
            except User.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"✗ Usuário {username} não encontrado"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Erro ao processar usuário {username}: {e}"))
        
        self.stdout.write("-" * 50)
        self.stdout.write(self.style.SUCCESS(f"Total de registros criados: {total_registros_criados}"))
        
        # Estatísticas finais
        total_registros_db = RegistroTreinamento.objects.count()
        self.stdout.write(f"Total de registros no banco: {total_registros_db}")
        
        # Registros por usuário
        self.stdout.write("\nRegistros por usuário:")
        for username in usernames:
            try:
                user = User.objects.get(username=username)
                individuo = Individuo.objects.get(user=user)
                count = RegistroTreinamento.objects.filter(individuo=individuo).count()
                self.stdout.write(f"- {username}: {count} registros")
            except:
                self.stdout.write(f"- {username}: 0 registros")
