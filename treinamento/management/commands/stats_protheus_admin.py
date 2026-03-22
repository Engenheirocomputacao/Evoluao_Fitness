"""
Management command para exibir estatísticas rápidas dos dados populados
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from treinamento.models import Individuo, RegistroTreinamento
from treinamento.iot_models import DispositivoIoT, LeituraIoT
from collections import Counter

class Command(BaseCommand):
    help = 'Exibe estatísticas rápidas dos dados dos usuários Protheus e Admin'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('📊 ESTATÍSTICAS RÁPIDAS - PROTHEUS E ADMIN'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
        
        try:
            protheus_user = User.objects.get(username='protheus')
            admin_user = User.objects.get(username='admin')
            
            protheus = Individuo.objects.get(user=protheus_user)
            admin = Individuo.objects.get(user=admin_user)
            
            # Usuários
            self.stdout.write(self.style.SUCCESS('👤 USUÁRIOS:'))
            self.stdout.write(f'   • Protheus: {protheus.nome_completo}')
            self.stdout.write(f'   • Admin: {admin.nome_completo}\n')
            
            # Registros de Treinamento
            regs_protheus = RegistroTreinamento.objects.filter(individuo=protheus).order_by('-data')
            regs_admin = RegistroTreinamento.objects.filter(individuo=admin).order_by('-data')
            
            self.stdout.write(self.style.SUCCESS('📝 REGISTROS DE TREINAMENTO:'))
            self.stdout.write(f'   • Protheus: {regs_protheus.count()} registros')
            self.stdout.write(f'   • Admin: {regs_admin.count()} registros')
            self.stdout.write(f'   • Total: {regs_protheus.count() + regs_admin.count()} registros\n')
            
            # Período
            if regs_protheus.exists():
                self.stdout.write(f'   📅 Período Protheus: {regs_protheus.last().data} até {regs_protheus.first().data}')
            if regs_admin.exists():
                self.stdout.write(f'   📅 Período Admin: {regs_admin.last().data} até {regs_admin.first().data}\n')
            
            # Esportes mais praticados
            self.stdout.write(self.style.SUCCESS('\n   🏃 ESPORTES MAIS PRATICADOS:'))
            
            esportes_protheus = Counter([r.esporte for r in regs_protheus])
            esportes_admin = Counter([r.esporte for r in regs_admin])
            
            self.stdout.write('   Protheus:')
            for esporte, count in esportes_protheus.most_common(5):
                self.stdout.write(f'      {esporte.capitalize()}: {count}')
            
            self.stdout.write('   Admin:')
            for esporte, count in esportes_admin.most_common(5):
                self.stdout.write(f'      {esporte.capitalize()}: {count}')
            
            # Dispositivos IoT
            devices_protheus = DispositivoIoT.objects.filter(proprietario=protheus)
            devices_admin = DispositivoIoT.objects.filter(proprietario=admin)
            
            self.stdout.write(self.style.SUCCESS('\n\n🔧 DISPOSITIVOS IoT:'))
            self.stdout.write(f'   • Protheus: {devices_protheus.count()} dispositivos')
            self.stdout.write(f'   • Admin: {devices_admin.count()} dispositivos')
            self.stdout.write(f'   • Total: {devices_protheus.count() + devices_admin.count()} dispositivos\n')
            
            # Tipos de dispositivos
            tipos_protheus = Counter([d.tipo for d in devices_protheus])
            tipos_admin = Counter([d.tipo for d in devices_admin])
            
            self.stdout.write('   Protheus:')
            for tipo, count in tipos_protheus.items():
                self.stdout.write(f'      {tipo.capitalize()}: {count}')
            
            self.stdout.write('   Admin:')
            for tipo, count in tipos_admin.items():
                self.stdout.write(f'      {tipo.capitalize()}: {count}')
            
            # Leituras IoT
            leituras_protheus = LeituraIoT.objects.filter(individuo=protheus)
            leituras_admin = LeituraIoT.objects.filter(individuo=admin)
            
            self.stdout.write(self.style.SUCCESS('\n\n📈 LEITURAS IoT:'))
            self.stdout.write(f'   • Protheus: {leituras_protheus.count()} leituras')
            self.stdout.write(f'   • Admin: {leituras_admin.count()} leituras')
            self.stdout.write(f'   • Total: {leituras_protheus.count() + leituras_admin.count()} leituras\n')
            
            # Média de leituras por dispositivo
            if devices_protheus.count() > 0:
                media_protheus = leituras_protheus.count() / devices_protheus.count()
                self.stdout.write(f'   • Média Protheus: {media_protheus:.1f} leituras/dispositivo')
            
            if devices_admin.count() > 0:
                media_admin = leituras_admin.count() / devices_admin.count()
                self.stdout.write(f'   • Média Admin: {media_admin:.1f} leituras/dispositivo')
            
            # Métricas adicionais
            self.stdout.write(self.style.SUCCESS('\n\n📊 MÉTRICAS ADICIONAIS:'))
            
            # Total de dias no período
            if regs_protheus.exists() and regs_admin.exists():
                data_inicial = min(regs_protheus.last().data, regs_admin.last().data)
                data_final = max(regs_protheus.first().data, regs_admin.first().data)
                total_dias = (data_final - data_inicial).days + 1
                
                total_registros = regs_protheus.count() + regs_admin.count()
                media_diaria = total_registros / total_dias if total_dias > 0 else 0
                
                self.stdout.write(f'   • Período total: {total_dias} dias')
                self.stdout.write(f'   • Total de registros: {total_registros}')
                self.stdout.write(f'   • Média de registros/dia: {media_diaria:.2f}')
            
            # Esforço médio
            esforco_protheus = regs_protheus.filter(esforco_percebido__isnull=False).aggregate(
                avg_esforco=Avg('esforco_percebido')
            )['avg_esforco']
            
            esforco_admin = regs_admin.filter(esforco_percebido__isnull=False).aggregate(
                avg_esforco=Avg('esforco_percebido')
            )['avg_esforco']
            
            if esforco_protheus:
                self.stdout.write(f'   • Esforço médio Protheus: {esforco_protheus:.1f}/10')
            if esforco_admin:
                self.stdout.write(f'   • Esforço médio Admin: {esforco_admin:.1f}/10')
            
            self.stdout.write(self.style.SUCCESS('\n' + '='*70))
            self.stdout.write(self.style.SUCCESS('✅ DADOS VERIFICADOS COM SUCESSO!'))
            self.stdout.write(self.style.SUCCESS('='*70 + '\n'))
            
        except User.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Usuário não encontrado: {e}'))
            self.stdout.write(self.style.WARNING('Execute primeiro: python3 manage.py populate_protheus_admin\n'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'\n❌ Erro: {e}\n'))

# Import necessário para o aggregate funcionar
from django.db.models import Avg
