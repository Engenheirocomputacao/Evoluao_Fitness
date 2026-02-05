from django.core.management.base import BaseCommand
from treinamento.models import RegistroTreinamento
from django.db.models import Q
import random

class Command(BaseCommand):
    help = 'Popula o campo esforco_percebido nos registros de treinamento existentes com valores aleatórios de 1 a 10.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Força a atualização mesmo dos registros que já têm esforco_percebido preenchido',
        )

    def handle(self, *args, **options):
        force_update = options['force']
        
        # Consulta para obter registros que precisam ser atualizados
        if force_update:
            registros = RegistroTreinamento.objects.all()
            self.stdout.write(f'Atualizando todos os {registros.count()} registros de treinamento com esforco_percebido...')
        else:
            registros = RegistroTreinamento.objects.filter(esforco_percebido__isnull=True)
            self.stdout.write(f'Atualizando {registros.count()} registros de treinamento com esforco_percebido...')
        
        # Atualizar os registros com valores aleatórios de esforço percebido
        atualizados = 0
        for registro in registros:
            # Gerar um valor aleatório de 1 a 10 para o esforço percebido
            # O valor pode ser ajustado com base no tipo de treinamento
            valor_esforco = random.randint(1, 10)
            
            # Opcionalmente, podemos ajustar o valor com base em outros fatores
            # Por exemplo, registros com valor_alcançado mais alto podem ter esforço mais alto
            if registro.valor_alcançado:
                # Ajuste proporcional baseado no valor alcançado
                base_esforco = int(registro.valor_alcançado / 10)  # Ajuste baseado no valor
                ajuste = random.randint(-2, 2)  # Pequeno ajuste aleatório
                valor_esforco = max(1, min(10, base_esforco + ajuste))
            
            registro.esforco_percebido = valor_esforco
            registro.save()
            atualizados += 1
            
            # Exibir progresso a cada 100 registros
            if atualizados % 100 == 0:
                self.stdout.write(f'  {atualizados} registros atualizados...', ending='\r')
                self.stdout.flush()
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(
                f'Sucesso! {atualizados} registros de treinamento atualizados com esforco_percebido.'
            )
        )
        
        # Mostrar estatísticas
        total_registros = RegistroTreinamento.objects.count()
        registros_com_esforco = RegistroTreinamento.objects.exclude(esforco_percebido__isnull=True).count()
        
        self.stdout.write(f'Total de registros: {total_registros}')
        self.stdout.write(f'Registros com esforco_percebido: {registros_com_esforco}')
        self.stdout.write(f'Registros sem esforco_percebido: {total_registros - registros_com_esforco}')