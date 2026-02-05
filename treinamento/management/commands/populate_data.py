from django.core.management.base import BaseCommand
from treinamento.api_service import fetch_and_process_training_data
from treinamento.models import Treinamento, RegistroTreinamento
from django.contrib.auth.models import User
from treinamento.models import Individuo
import random
from datetime import date, timedelta

class Command(BaseCommand):
    help = 'Busca dados de uma API externa e popula o banco de dados com registros de treinamento.'

    def create_individuals(self):
        # Lista de nomes masculinos e femininos em português
        male_first_names = ['João', 'Pedro', 'Carlos', 'Lucas', 'Gabriel', 'Rafael', 
                          'Mateus', 'Gustavo', 'Fernando', 'André', 'Bruno', 'Marcos']
        
        female_first_names = ['Ana', 'Maria', 'Juliana', 'Patrícia', 'Aline', 'Camila', 
                            'Fernanda', 'Amanda', 'Bianca', 'Carolina', 'Daniela', 'Eduarda']
        
        last_names = ['Silva', 'Santos', 'Oliveira', 'Souza', 'Pereira', 'Costa', 
                     'Ferreira', 'Rodrigues', 'Almeida', 'Nascimento', 'Lima', 'Araújo',
                     'Barbosa', 'Gomes', 'Martins', 'Ribeiro', 'Alves', 'Monteiro']
        
        # Criar 40 homens
        for i in range(40):
            first_name = male_first_names[i % len(male_first_names)]
            last_name1 = random.choice(last_names)
            last_name2 = random.choice(last_names)
            full_name = f"{first_name} {last_name1} {last_name2}"
            username = f"{first_name.lower()}.{last_name1.lower()}"
            
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=f"{username}@example.com",
                    password='senha123'
                )
                birth_date = date.today() - timedelta(days=random.randint(18*365, 60*365))
                
                # Escolhe um avatar aleatório (0 a 4)
                avatar_num = random.randint(0, 4)
                avatar_path = f'avatars/avatar_{avatar_num}.jpg'
                
                Individuo.objects.create(
                    user=user,
                    nome_completo=full_name,
                    data_nascimento=birth_date,
                    ativo=random.choice([True, True, True, False]),  # 75% de chance de estar ativo
                    avatar=avatar_path
                )
                self.stdout.write(self.style.SUCCESS(f'Indivíduo {full_name} criado com avatar {avatar_path}.'))
        
        # Criar 30 mulheres
        for i in range(30):
            first_name = female_first_names[i % len(female_first_names)]
            last_name1 = random.choice(last_names)
            last_name2 = random.choice(last_names)
            full_name = f"{first_name} {last_name1} {last_name2}"
            username = f"{first_name.lower()}.{last_name1.lower()}"
            
            if not User.objects.filter(username=username).exists():
                user = User.objects.create_user(
                    username=username,
                    email=f"{username}@example.com",
                    password='senha123'
                )
                birth_date = date.today() - timedelta(days=random.randint(18*365, 60*365))
                
                # Escolhe um avatar aleatório (0 a 4)
                avatar_num = random.randint(0, 4)
                avatar_path = f'avatars/avatar_{avatar_num}.jpg'
                
                Individuo.objects.create(
                    user=user,
                    nome_completo=full_name,
                    data_nascimento=birth_date,
                    ativo=random.choice([True, True, True, False]),  # 75% de chance de estar ativo
                    avatar=avatar_path
                )
                self.stdout.write(self.style.SUCCESS(f'Indivíduo {full_name} criado com avatar {avatar_path}.'))

    def create_sample_training_records(self):
        """Cria registros de treinamento de exemplo para os indivíduos"""
        treinamentos = list(Treinamento.objects.all())
        if not treinamentos:
            self.stdout.write(self.style.WARNING('Nenhum treinamento encontrado. Criando treinamentos de exemplo...'))
            treinamentos = [
                Treinamento.objects.create(nome="Força", unidade_medida="kg", descricao="Treinamento de levantamento de peso"),
                Treinamento.objects.create(nome="Resistência", unidade_medida="min", descricao="Treinamento cardiovascular"),
                Treinamento.objects.create(nome="Velocidade", unidade_medida="km", descricao="Treinamento de corrida")
            ]
        
        for individuo in Individuo.objects.all():
            for _ in range(random.randint(5, 15)):  # 5-15 registros por indivíduo
                treinamento = random.choice(treinamentos)
                data = date.today() - timedelta(days=random.randint(0, 30))  # Últimos 30 dias
                valor = round(random.uniform(10, 100), 2)
                
                # Ajusta o valor baseado no tipo de treinamento
                if treinamento.unidade_medida == 'min':
                    valor = round(random.uniform(10, 60), 0)  # 10-60 minutos
                elif treinamento.unidade_medida == 'kg':
                    valor = round(random.uniform(20, 150), 1)  # 20-150 kg
                elif treinamento.unidade_medida == 'km':
                    valor = round(random.uniform(1, 10), 1)  # 1-10 km
                
                # Verifica se já existe um registro para essa combinação
                if not RegistroTreinamento.objects.filter(
                    individuo=individuo,
                    treinamento=treinamento,
                    data=data
                ).exists():
                    RegistroTreinamento.objects.create(
                        individuo=individuo,
                        treinamento=treinamento,
                        data=data,
                        valor_alcançado=valor,
                        observacoes="Registro automático de exemplo" if random.random() > 0.7 else ""
                    )

    def handle(self, *args, **options):
        self.stdout.write("Verificando e criando dados iniciais...")
        
        # 1. Cria usuário admin se não existir
        if not User.objects.filter(username='admin').exists():
            user = User.objects.create_superuser('admin', 'admin@example.com', 'adminpass')
            Individuo.objects.create(user=user, nome_completo="Administrador do Sistema")
            self.stdout.write(self.style.SUCCESS('Usuário admin criado.'))
        else:
            self.stdout.write(self.style.SUCCESS('Usuário admin já existe.'))

        # 2. Cria treinamentos de exemplo se não existirem
        if not Treinamento.objects.exists():
            Treinamento.objects.create(nome="Força", unidade_medida="kg", descricao="Treinamento de levantamento de peso")
            Treinamento.objects.create(nome="Resistência", unidade_medida="min", descricao="Treinamento cardiovascular")
            Treinamento.objects.create(nome="Velocidade", unidade_medida="km", descricao="Treinamento de corrida")
            self.stdout.write(self.style.SUCCESS('Treinamentos iniciais criados.'))
        
        # 3. Cria indivíduos de exemplo
        self.stdout.write("Criando indivíduos de exemplo...")
        self.create_individuals()
        
        # 4. Cria registros de treinamento de exemplo
        self.stdout.write("Criando registros de treinamento de exemplo...")
        self.create_sample_training_records()
        
        self.stdout.write(self.style.SUCCESS('Dados de exemplo criados com sucesso!'))
        self.stdout.write(f"Total de indivíduos: {Individuo.objects.count()}")
        self.stdout.write(f"Total de registros de treinamento: {RegistroTreinamento.objects.count()}")
