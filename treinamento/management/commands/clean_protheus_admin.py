"""
Management command para limpar dados dos usuários Protheus e Admin
Útil para reexecutar a população do zero
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from treinamento.models import Individuo, RegistroTreinamento
from treinamento.iot_models import LeituraIoT, DispositivoIoT, ConfiguracaoDispositivo

class Command(BaseCommand):
    help = 'Limpa dados dos usuários Protheus e Admin'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirma a exclusão dos dados'
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(self.style.WARNING(
                '\nATENÇÃO: Este comando irá apagar todos os dados dos usuários Protheus e Admin.\n'
                'Use --confirm para executar a limpeza.\n'
            ))
            return
        
        self.stdout.write(self.style.SUCCESS('Iniciando limpeza de dados...\n'))
        
        # Contadores
        count_registros = 0
        count_leituras = 0
        count_dispositivos = 0
        count_configuracoes = 0
        
        try:
            # Usuário Protheus
            try:
                protheus_user = User.objects.get(username='protheus')
                protheus = Individuo.objects.get(user=protheus_user)
                
                self.stdout.write(f' Limpando dados de Protheus ({protheus.nome_completo})...')
                
                # Ler leituras IoT
                leituras_protheus = LeituraIoT.objects.filter(individuo=protheus).count()
                LeituraIoT.objects.filter(individuo=protheus).delete()
                count_leituras += leituras_protheus
                
                # Dispositivos
                dispositivos_protheus = DispositivoIoT.objects.filter(proprietario=protheus)
                for device in dispositivos_protheus:
                    configs = ConfiguracaoDispositivo.objects.filter(dispositivo=device).count()
                    ConfiguracaoDispositivo.objects.filter(dispositivo=device).delete()
                    count_configuracoes += configs
                
                count_dispositivos += dispositivos_protheus.count()
                dispositivos_protheus.delete()
                
                # Registros de treinamento
                registros_protheus = RegistroTreinamento.objects.filter(individuo=protheus).count()
                RegistroTreinamento.objects.filter(individuo=protheus).delete()
                count_registros += registros_protheus
                
                # Remover perfil Individuo (o usuário será mantido)
                protheus.delete()
                
                self.stdout.write(self.style.SUCCESS(
                    f'  ✓ Protheus: {registros_protheus} registros, '
                    f'{leituras_protheus} leituras, '
                    f'{dispositivos_protheus.count() if False else len(list(dispositivos_protheus))} dispositivos'
                ))
                
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING('  Usuário Protheus não encontrado.'))
            
            # Usuário Admin
            try:
                admin_user = User.objects.get(username='admin')
                admin = Individuo.objects.get(user=admin_user)
                
                self.stdout.write(f'\n Limpando dados de Admin ({admin.nome_completo})...')
                
                # Leituras IoT
                leituras_admin = LeituraIoT.objects.filter(individuo=admin).count()
                LeituraIoT.objects.filter(individuo=admin).delete()
                count_leituras += leituras_admin
                
                # Dispositivos
                dispositivos_admin = DispositivoIoT.objects.filter(proprietario=admin)
                for device in dispositivos_admin:
                    configs = ConfiguracaoDispositivo.objects.filter(dispositivo=device).count()
                    ConfiguracaoDispositivo.objects.filter(dispositivo=device).delete()
                    count_configuracoes += configs
                
                count_dispositivos += dispositivos_admin.count()
                dispositivos_admin.delete()
                
                # Registros de treinamento
                registros_admin = RegistroTreinamento.objects.filter(individuo=admin).count()
                RegistroTreinamento.objects.filter(individuo=admin).delete()
                count_registros += registros_admin
                
                # Remover perfil Individuo (o usuário será mantido)
                admin.delete()
                
                self.stdout.write(self.style.SUCCESS(
                    f'  ✓ Admin: {registros_admin} registros, '
                    f'{leituras_admin} leituras, '
                    f'{dispositivos_admin.count() if False else len(list(dispositivos_admin))} dispositivos'
                ))
                
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING('  Usuário Admin não encontrado.'))
            
            # Resumo
            self.stdout.write(self.style.SUCCESS('\n' + '='*60))
            self.stdout.write(self.style.SUCCESS('RESUMO DA LIMPEZA'))
            self.stdout.write(self.style.SUCCESS('='*60))
            self.stdout.write(f'Total de registros apagados: {count_registros}')
            self.stdout.write(f'Total de leituras apagadas: {count_leituras}')
            self.stdout.write(f'Total de dispositivos apagados: {count_dispositivos}')
            self.stdout.write(f'Total de configurações apagadas: {count_configuracoes}')
            self.stdout.write(self.style.SUCCESS('\nLimpeza concluída com sucesso!'))
            self.stdout.write(self.style.SUCCESS('Agora você pode executar: python3 manage.py populate_protheus_admin'))
            self.stdout.write(self.style.SUCCESS('='*60 + '\n'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\nErro durante limpeza: {e}'))
            raise
