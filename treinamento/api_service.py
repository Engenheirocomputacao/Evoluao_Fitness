import requests
import random
from datetime import date, timedelta
from django.contrib.auth.models import User
from .models import Individuo, Treinamento, RegistroTreinamento
from decimal import Decimal

# URL da API de simulação
DUMMY_API_URL = "https://dummyjson.com/products"

def fetch_and_process_training_data():
    """
    Busca dados simulados de treinamento de uma API externa (DummyJSON)
    e os processa para criar registros de treinamento no banco de dados.
    """
    try:
        response = requests.get(DUMMY_API_URL)
        response.raise_for_status()  # Levanta exceção para códigos de status HTTP ruins
        data = response.json()
    except requests.exceptions.RequestException as e:
        print(f"Erro ao consumir a API: {e}")
        return False

    products = data.get('products', [])
    if not products:
        print("Nenhum produto encontrado na resposta da API.")
        return False

    # Garante que haja indivíduos e treinamentos para associar os registros
    individuos = list(Individuo.objects.all())
    treinamentos = list(Treinamento.objects.all())

    if not individuos or not treinamentos:
        print("É necessário ter indivíduos e treinamentos cadastrados para criar registros.")
        # Para fins de teste, vamos criar um treinamento padrão se não houver
        if not treinamentos:
            Treinamento.objects.create(nome="Treinamento Padrão", unidade_medida="rep", descricao="Treinamento de teste para simulação de API")
            treinamentos = list(Treinamento.objects.all())
        # Se ainda não houver indivíduos, o sistema de login deve garantir isso.
        # Por enquanto, vamos assumir que o admin será criado e, portanto, um Indivíduo
        # será criado na próxima etapa de login/registro.

        if not individuos:
            # Se não houver indivíduos, não podemos criar registros.
            print("Nenhum indivíduo encontrado. Não é possível criar registros de treinamento.")
            return False

    
    new_records_count = 0
    for product in products:
        # Usaremos o 'rating' do produto como o 'valor_alcançado'
        valor_alcançado = Decimal(str(product.get('rating', 0.0)))
        
        # Seleciona um indivíduo e um treinamento aleatoriamente
        individuo = random.choice(individuos)
        treinamento = random.choice(treinamentos)
        
        # Define uma data aleatória nos últimos 30 dias
        dias_atras = random.randint(1, 30)
        data_registro = date.today() - timedelta(days=dias_atras)

        # Cria o registro de treinamento
        try:
            RegistroTreinamento.objects.create(
                individuo=individuo,
                treinamento=treinamento,
                data=data_registro,
                valor_alcançado=valor_alcançado,
                observacoes=f"Dados simulados da API DummyJSON (Produto: {product.get('title')})"
            )
            new_records_count += 1
        except Exception as e:
            # Ignora se a combinação (individuo, treinamento, data) já existir (unique_together)
            if "UNIQUE constraint failed" not in str(e):
                print(f"Erro ao criar registro: {e}")
            pass

    print(f"Processamento de dados da API concluído. {new_records_count} novos registros criados.")
    return True

def calculate_average_performance(individuo_id=None, treinamento_id=None):
    """
    Calcula a média de desempenho (valor_alcançado) para um indivíduo e/ou treinamento.
    """
    from django.db.models import Avg
    
    queryset = RegistroTreinamento.objects.all()
    
    if individuo_id:
        queryset = queryset.filter(individuo__id=individuo_id)
        
    if treinamento_id:
        queryset = queryset.filter(treinamento__id=treinamento_id)
        
    average = queryset.aggregate(Avg('valor_alcançado'))['valor_alcançado__avg']
    
    return average if average is not None else Decimal('0.00')
