from django.core.management.base import BaseCommand
from treinamento.models import Individuo
import random

class Command(BaseCommand):
    help = 'Popula o campo peso nos indivíduos existentes com valores realistas baseados no sexo.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a atualização mesmo dos indivíduos que já têm peso preenchido',
        )

    def handle(self, *args, **options):
        force_update = options['force']
        
        # Consulta para obter indivíduos que precisam ser atualizados
        if force_update:
            individuos = Individuo.objects.all()
            self.stdout.write(f'Atualizando todos os {individuos.count()} indivíduos com peso...')
        else:
            individuos = Individuo.objects.filter(peso__isnull=True)
            self.stdout.write(f'Atualizando {individuos.count()} indivíduos com peso...')
        
        # Atualizar os indivíduos com valores realistas de peso
        atualizados = 0
        for individuo in individuos:
            # Determinar faixa de peso baseada no sexo
            if individuo.sexo == 'masculino':
                # Peso médio para homens: 70-100kg
                peso = round(random.uniform(65.0, 95.0), 2)
            elif individuo.sexo == 'feminino':
                # Peso médio para mulheres: 55-80kg
                peso = round(random.uniform(50.0, 80.0), 2)
            else:
                # Se sexo não estiver definido, escolher aleatoriamente
                sexo_aleatorio = random.choice(['masculino', 'feminino'])
                if sexo_aleatorio == 'masculino':
                    peso = round(random.uniform(65.0, 95.0), 2)
                else:
                    peso = round(random.uniform(50.0, 80.0), 2)
            
            # Atualizar o indivíduo com o peso gerado
            individuo.peso = peso
            individuo.save()
            atualizados += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Sucesso! {atualizados} indivíduos atualizados com peso realista.'
            )
        )