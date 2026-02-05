#!/usr/bin/env python
"""
Script para popular o usuário Protheus com dados realistas de treinamento
com diferentes esportes, similar ao usuário admin
"""

import os
import sys
import django
import random
from datetime import datetime, timedelta, time
from decimal import Decimal

# Configurar o ambiente Django
sys.path.append('/home/marco/Downloads/Evolução_Fitness ')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_treinamento.settings')
django.setup()

from django.contrib.auth.models import User
from treinamento.models import Individuo, RegistroTreinamento, Treinamento
from django.core.management import call_command


def populate_protheus_with_sports():
    # Obter o usuário Protheus
    try:
        protheus_user = User.objects.get(username='Protheus')
        protheus_individuo = Individuo.objects.get(user=protheus_user)
        print("Usuário Protheus encontrado.")
    except User.DoesNotExist:
        print("Usuário Protheus não encontrado!")
        return
    except Individuo.DoesNotExist:
        print("Perfil de indivíduo para Protheus não encontrado!")
        return

    # Definir o período: de 15/12/2025 a 04/02/2026
    start_date = datetime(2025, 12, 15).date()
    end_date = datetime(2026, 2, 4).date()
    
    # Lista de esportes com pesos baseados nos dados do admin
    esportes_com_pesos = [
        ('ciclismo', 20),      # Mais frequente como no admin
        ('natacao', 15),       # Frequente como no admin
        ('corrida', 18),       # Frequente como no admin
        ('caminhada', 12),     # Moderadamente frequente
        ('musculacao', 15),    # Frequente como no admin
        ('resistencia', 10),   # Moderadamente frequente
        ('forca', 10),         # Moderadamente frequente
    ]
    
    # Calcular o total de pesos para probabilidade
    total_peso = sum(peso for _, peso in esportes_com_pesos)
    
    # Criar treinamentos se não existirem
    tipos_treinamento = [
        ('Força', 'kg', 'Treinamento de força com pesos'),
        ('Resistência', 'min', 'Treinamento de resistência cardiovascular'),
        ('Velocidade', 'km', 'Treinamento de velocidade e endurance'),
        ('Ciclismo', 'km', 'Treinamento de ciclismo'),
        ('Corrida', 'km', 'Treinamento de corrida'),
        ('Natação', 'km', 'Treinamento de natação'),
        ('Caminhada', 'km', 'Treinamento de caminhada'),
        ('Musculação', 'rep', 'Treinamento de musculação com repetições'),
    ]
    
    for nome, unidade, descricao in tipos_treinamento:
        treinamento, created = Treinamento.objects.get_or_create(
            nome=nome,
            defaults={
                'unidade_medida': unidade,
                'descricao': descricao
            }
        )
        if created:
            print(f"Criado treinamento: {nome}")

    # Gerar datas de treinamento (excluindo domingos)
    current_date = start_date
    training_dates = []
    
    while current_date <= end_date:
        # Verificar se não é domingo (weekday() = 6 para domingo)
        if current_date.weekday() != 6:  # Não é domingo
            training_dates.append(current_date)
        current_date += timedelta(days=1)
    
    print(f"Total de dias de treinamento (excluindo domingos): {len(training_dates)}")
    
    # Para cada data de treinamento, criar 3 registros com esportes variados
    for date in training_dates:
        # Selecionar 3 esportes aleatoriamente com base nos pesos
        selected_esportes = []
        for _ in range(3):
            rand_val = random.randint(1, total_peso)
            cumulative_weight = 0
            for esporte, peso in esportes_com_pesos:
                cumulative_weight += peso
                if rand_val <= cumulative_weight:
                    selected_esportes.append(esporte)
                    break
        
        # Criar registros para os esportes selecionados
        for esporte in selected_esportes:
            # Definir valores realistas com base no esporte
            if esporte in ['forca', 'musculacao']:
                # Treinamento de força: pesos entre 30-80kg
                valor_registro = round(Decimal(random.uniform(30, 80)), 2)
                treinamento_nome = 'Força' if esporte == 'forca' else 'Musculação'
            elif esporte in ['velocidade', 'corrida', 'caminhada', 'ciclismo']:
                # Treinamento de velocidade/distância: 5-20km
                valor_registro = round(Decimal(random.uniform(5, 20)), 2)
                if esporte == 'corrida':
                    treinamento_nome = 'Corrida'
                elif esporte == 'ciclismo':
                    treinamento_nome = 'Ciclismo'
                elif esporte == 'caminhada':
                    treinamento_nome = 'Caminhada'
                else:
                    treinamento_nome = 'Velocidade'
            elif esporte == 'resistencia':
                # Treinamento de resistência: duração em minutos (20-60)
                valor_registro = round(Decimal(random.uniform(25, 50)), 2)
                treinamento_nome = 'Resistência'
            elif esporte == 'natacao':
                # Natação: distância em km (1-5)
                valor_registro = round(Decimal(random.uniform(1, 5)), 2)
                treinamento_nome = 'Natação'
            
            # Escolher treinamento apropriado
            treinamento = Treinamento.objects.get(nome=treinamento_nome)
            
            # Percepção de esforço (6-9 para atleta intermediário)
            esforco_percebido = random.randint(6, 9)
            
            # Duração do treino (15-120 minutos)
            duracao_minutos = random.randint(15, 120)
            duracao = timedelta(minutes=duracao_minutos)
            
            # Confiabilidade (90-100% para dados realistas)
            confiabilidade = round(Decimal(random.uniform(90, 100)), 2)
            
            # Criar o registro de treinamento
            registro = RegistroTreinamento.objects.create(
                individuo=protheus_individuo,
                treinamento=treinamento,
                data=date,
                valor_alcançado=valor_registro,
                esporte=esporte,
                esforco_percebido=esforco_percebido,
                duracao=duracao,
                confiabilidade=confiabilidade,
                fonte_dados='manual',
                observacoes=f'Treino de {esporte} realizado em nível intermediário'
            )
    
    print(f"Foram criados {len(training_dates) * 3} registros de treinamento para o usuário Protheus")
    
    # Mostrar distribuição dos esportes
    from django.db.models import Count
    sport_stats = RegistroTreinamento.objects.filter(individuo=protheus_individuo).values('esporte').annotate(count=Count('esporte')).order_by('-count')
    print("\nDistribuição final dos esportes para Protheus:")
    for stat in sport_stats:
        print(f"  Esporte: {stat['esporte']}, Contagem: {stat['count']}")


if __name__ == "__main__":
    populate_protheus_with_sports()