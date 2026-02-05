# Execute este comando no shell do Django: python3 manage.py shell

import os
import sys
from datetime import date, timedelta
import random

# Lista de usuários
usernames = ['Carlos@', 'Newuser', 'carlos@', 'carlos@1', 'maria', 'pamela', 'testeusuario_']

# Obter treinamentos
treinamento_forca = Treinamento.objects.get(nome='Força')
treinamento_velocidade = Treinamento.objects.get(nome='Velocidade')
treinamento_resistencia = Treinamento.objects.get(nome='Resistência')

# Período de datas
data_inicio = date(2025, 11, 1)
data_fim = date(2025, 12, 31)
total_registros = 0

print(f'Populando dados de {data_inicio} a {data_fim} para {len(usernames)} usuários...')

for username in usernames:
    try:
        user = User.objects.get(username=username)
        individuo, created = Individuo.objects.get_or_create(user=user)
        registros_usuario = 0
        
        data_atual = data_inicio
        while data_atual <= data_fim:
            # 80% de chance de treinar no dia
            if random.random() < 0.8:
                # Registro de Força (20-85 kg)
                valor_forca = round(random.uniform(20, 85), 2)
                duracao_forca = timedelta(minutes=random.randint(30, 90))
                esforco_forca = random.randint(3, 9)
                
                reg, created = RegistroTreinamento.objects.get_or_create(
                    individuo=individuo, 
                    treinamento=treinamento_forca, 
                    data=data_atual,
                    defaults={
                        'valor_alcançado': valor_forca, 
                        'duracao': duracao_forca, 
                        'esforco_percebido': esforco_forca
                    }
                )
                if created: registros_usuario += 1
                
                # Registro de Velocidade (8-25 km/h)
                valor_velocidade = round(random.uniform(8, 25), 2)
                duracao_velocidade = timedelta(minutes=random.randint(20, 60))
                esforco_velocidade = random.randint(4, 10)
                
                reg, created = RegistroTreinamento.objects.get_or_create(
                    individuo=individuo, 
                    treinamento=treinamento_velocidade, 
                    data=data_atual,
                    defaults={
                        'valor_alcançado': valor_velocidade, 
                        'duracao': duracao_velocidade, 
                        'esforco_percebido': esforco_velocidade
                    }
                )
                if created: registros_usuario += 1
                
                # Registro de Resistência (15-120 min)
                valor_resistencia = round(random.uniform(15, 120), 2)
                duracao_resistencia = timedelta(minutes=int(valor_resistencia))
                esforco_resistencia = random.randint(3, 8)
                
                reg, created = RegistroTreinamento.objects.get_or_create(
                    individuo=individuo, 
                    treinamento=treinamento_resistencia, 
                    data=data_atual,
                    defaults={
                        'valor_alcançado': valor_resistencia, 
                        'duracao': duracao_resistencia, 
                        'esforco_percebido': esforco_resistencia
                    }
                )
                if created: registros_usuario += 1
            
            data_atual += timedelta(days=1)
        
        print(f'✓ {username}: {registros_usuario} registros criados')
        total_registros += registros_usuario
        
    except Exception as e:
        print(f'✗ Erro {username}: {e}')

print(f'Total de registros criados: {total_registros}')
print(f'Total no banco: {RegistroTreinamento.objects.count()}')
