#!/usr/bin/env python
import os
import sys
import django

# Add the project directory to the Python path
sys.path.append('/home/marco/Downloads/Evolução_Fitness')

# Set up Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'controle_treinamento.settings')
django.setup()

from treinamento.models import RegistroTreinamento, Treinamento, Individuo

def check_data():
    print("=== Verificando dados no banco ===")
    
    # Check if models exist and have data
    try:
        individuos_count = Individuo.objects.count()
        treinamentos_count = Treinamento.objects.count()
        registros_count = RegistroTreinamento.objects.count()
        
        print(f"Indivíduos: {individuos_count}")
        print(f"Treinamentos: {treinamentos_count}")
        print(f"Registros: {registros_count}")
        
        if registros_count > 0:
            print("\n=== Últimos registros ===")
            for reg in RegistroTreinamento.objects.order_by('-data')[:5]:
                print(f"- {reg.individuo.nome_completo}: {reg.treinamento.nome} = {reg.valor_alcançado}")
        else:
            print("\n=== Criando dados de exemplo ===")
            create_sample_data()
            
    except Exception as e:
        print(f"Erro ao acessar dados: {e}")

def create_sample_data():
    try:
        # Create sample individual if doesn't exist
        user_individuo, created = Individuo.objects.get_or_create(
            user_id=1,  # Assuming first user
            defaults={'nome_completo': 'Usuário Teste'}
        )
        
        # Create sample trainings if they don't exist
        treinamentos = [
            {'nome': 'Corrida', 'descricao': 'Corrida ao ar livre', 'unidade_medida': 'km'},
            {'nome': 'Musculação', 'descricao': 'Treinamento de força', 'unidade_medida': 'min'},
            {'nome': 'Natação', 'descricao': 'Natação livre', 'unidade_medida': 'm'},
        ]
        
        for treino_data in treinamentos:
            treino, created = Treinamento.objects.get_or_create(
                nome=treino_data['nome'],
                defaults=treino_data
            )
            print(f"Treinamento '{treino.nome}' {'criado' if created else 'já existia'}")
        
        # Create sample records
        import random
        from datetime import datetime, timedelta
        
        treinamentos = Treinamento.objects.all()
        for i in range(10):
            treino = random.choice(treinamentos)
            valor = random.uniform(5, 10)
            data = datetime.now() - timedelta(days=random.randint(0, 30))
            
            registro, created = RegistroTreinamento.objects.get_or_create(
                individuo=user_individuo,
                treinamento=treino,
                data=data.date(),
                defaults={'valor_alcançado': valor}
            )
            if created:
                print(f"Registro criado: {treino.nome} = {valor:.2f} em {data.date()}")
        
        print("\nDados de exemplo criados com sucesso!")
        
    except Exception as e:
        print(f"Erro ao criar dados: {e}")

if __name__ == '__main__':
    check_data()
