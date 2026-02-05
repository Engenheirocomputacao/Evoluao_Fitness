from django.core.management.base import BaseCommand
from treinamento.models import RegistroTreinamento
from django.db.models import Q
import random
from datetime import timedelta

class Command(BaseCommand):
    help = 'Popula o campo duracao nos registros de treinamento existentes com valores aleatórios.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a atualização mesmo dos registros que já têm duração preenchida',
        )

    def handle(self, *args, **options):
        force_update = options['force']
        
        # Consulta para obter registros que precisam ser atualizados
        if force_update:
            registros = RegistroTreinamento.objects.all()
            self.stdout.write(f'Atualizando todos os {registros.count()} registros de treinamento com duração...')
        else:
            registros = RegistroTreinamento.objects.filter(duracao__isnull=True)
            self.stdout.write(f'Atualizando {registros.count()} registros de treinamento com duração...')
        
        # Atualizar os registros com valores aleatórios de duração
        atualizados = 0
        for registro in registros:
            # Gerar um valor aleatório de duração baseado no tipo de treinamento
            tipo_treinamento = registro.treinamento.nome.lower()
            
            if 'força' in tipo_treinamento or 'musculação' in tipo_treinamento or 'resistência' in tipo_treinamento:
                # Treinamentos de força geralmente duram entre 30 e 120 minutos
                minutos = random.randint(30, 120)
            elif 'corrida' in tipo_treinamento or 'velocidade' in tipo_treinamento:
                # Corridas podem durar entre 20 e 180 minutos
                minutos = random.randint(20, 180)
            elif 'natação' in tipo_treinamento:
                # Natação geralmente entre 30 e 90 minutos
                minutos = random.randint(30, 90)
            elif 'yoga' in tipo_treinamento or 'alongamento' in tipo_treinamento:
                # Yoga/alongamento entre 20 e 60 minutos
                minutos = random.randint(20, 60)
            else:
                # Outros treinamentos entre 20 e 120 minutos
                minutos = random.randint(20, 120)
            
            # Converter minutos em timedelta
            duracao = timedelta(minutes=minutos)
            registro.duracao = duracao
            registro.save()
            atualizados += 1
            
            # Exibir progresso a cada 100 registros
            if atualizados % 100 == 0:
                self.stdout.write(f'  {atualizados} registros atualizados...', ending='\r')
                self.stdout.flush()
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Sucesso! {atualizados} registros de treinamento atualizados com duração.'
            )
        )
        
        # Mostrar estatísticas
        total_registros = RegistroTreinamento.objects.count()
        registros_com_duracao = RegistroTreinamento.objects.exclude(duracao__isnull=True).count()
        
        self.stdout.write(f'Total de registros: {total_registros}')
        self.stdout.write(f'Registros com duração: {registros_com_duracao}')
        self.stdout.write(f'Registros sem duração: {total_registros - registros_com_duracao}')