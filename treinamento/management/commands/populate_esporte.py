from django.core.management.base import BaseCommand
from treinamento.models import RegistroTreinamento, Treinamento
import random

class Command(BaseCommand):
    help = 'Popula o campo esporte nos registros de treinamento existentes com valores baseados no tipo de treinamento.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a atualização mesmo dos registros que já têm esporte preenchido',
        )

    def handle(self, *args, **options):
        force_update = options['force']
        
        # Definir mapeamento de treinamentos para esportes
        mapeamento_esporte = {
            'força': 'musculacao',
            'musculação': 'musculacao',
            'peso': 'musculacao',
            'resistência': 'corrida',
            'resistencia': 'corrida',
            'corrida': 'corrida',
            'cardio': 'corrida',
            'cardiovascular': 'corrida',
            'velocidade': 'corrida',
            'ciclismo': 'ciclismo',
            'bike': 'ciclismo',
            'natação': 'natacao',
            'natacao': 'natacao',
            'submerso': 'natacao',
            'funcional': 'musculacao',
            'crossfit': 'musculacao',
            'yoga': 'outro',
            'pilates': 'outro',
            'alongamento': 'outro',
            'flexibilidade': 'outro',
            'treinamento': 'musculacao',
        }
        
        # Consulta para obter registros que precisam ser atualizados
        if force_update:
            registros = RegistroTreinamento.objects.all()
            self.stdout.write(f'Atualizando todos os {registros.count()} registros de treinamento com esporte...')
        else:
            registros = RegistroTreinamento.objects.filter(esporte='outro')
            self.stdout.write(f'Atualizando {registros.count()} registros de treinamento com esporte...')
        
        # Atualizar os registros com valores apropriados de esporte
        atualizados = 0
        for registro in registros:
            # Obter o nome do treinamento e determinar o esporte apropriado
            nome_treinamento = registro.treinamento.nome.lower()
            
            # Procurar correspondência no mapeamento
            esporte_definido = 'outro'  # valor padrão
            for termo, esporte in mapeamento_esporte.items():
                if termo in nome_treinamento:
                    esporte_definido = esporte
                    break
            
            # Atualizar o registro se o esporte for diferente
            if registro.esporte != esporte_definido:
                registro.esporte = esporte_definido
                registro.save()
                atualizados += 1
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Sucesso! {atualizados} registros de treinamento atualizados com esporte apropriado.'
            )
        )