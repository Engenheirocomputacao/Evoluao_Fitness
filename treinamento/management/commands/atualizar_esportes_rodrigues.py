from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from treinamento.models import RegistroTreinamento, Individuo, Treinamento

class Command(BaseCommand):
    help = 'Atualiza os registros existentes do usuário rodrigues com os esportes apropriados'

    def handle(self, *args, **options):
        username = 'rodrigues'
        
        try:
            user = User.objects.get(username=username)
            individuo = Individuo.objects.get(user=user)
            
            # Obter treinamentos
            treinamento_forca = Treinamento.objects.get(nome='Força')
            treinamento_velocidade = Treinamento.objects.get(nome='Velocidade')
            treinamento_resistencia = Treinamento.objects.get(nome='Resistência')
            
            total_atualizados = 0
            
            self.stdout.write(f"Atualizando registros do usuário: {username}")
            self.stdout.write("-" * 50)
            
            # Atualizar registros de Força
            registros_forca = RegistroTreinamento.objects.filter(
                individuo=individuo,
                treinamento=treinamento_forca
            )
            
            observacoes_forca = [
                "Levantamento de peso terra",
                "Supino reto com barra",
                "Agachamento livre",
                "Desenvolvimento militar",
                "Rosca direta com halteres",
                "Elevação lateral",
                "Puxada frontal",
                "Remada curvada",
                "Cadeira flexora",
                "Gêmeos em pé"
            ]
            
            for i, registro in enumerate(registros_forca):
                registro.esporte = 'musculacao'
                registro.observacoes = observacoes_forca[i % len(observacoes_forca)]
                registro.save()
                total_atualizados += 1
            
            self.stdout.write(self.style.SUCCESS(f"✓ Força: {len(registros_forca)} registros atualizados"))
            
            # Atualizar registros de Velocidade
            registros_velocidade = RegistroTreinamento.objects.filter(
                individuo=individuo,
                treinamento=treinamento_velocidade
            )
            
            observacoes_velocidade = [
                "Sprints de 100 metros",
                "Corrida intervalada",
                "Tiros em pista de atletismo",
                "Corrida de 400 metros",
                "Progressão de velocidade",
                "Fartlek training",
                "Corrida com mudanças de ritmo",
                "Sprints em subida",
                "Corrida de resistência de velocidade",
                "Drills de aceleração"
            ]
            
            for i, registro in enumerate(registros_velocidade):
                registro.esporte = 'corrida'
                registro.observacoes = observacoes_velocidade[i % len(observacoes_velocidade)]
                registro.save()
                total_atualizados += 1
            
            self.stdout.write(self.style.SUCCESS(f"✓ Velocidade: {len(registros_velocidade)} registros atualizados"))
            
            # Atualizar registros de Resistência
            registros_resistencia = RegistroTreinamento.objects.filter(
                individuo=individuo,
                treinamento=treinamento_resistencia
            )
            
            esportes_resistencia = [
                ('corrida', 'Corrida contínua moderada'),
                ('ciclismo', 'Ciclismo estacionário'),
                ('natacao', 'Natação livre'),
                ('caminhada', 'Caminhada rápida'),
                ('outro', 'Pular corda'),
                ('corrida', 'Corrida na esteira'),
                ('ciclismo', 'Bicicleta ergométrica'),
                ('caminhada', 'Caminhada na esteira'),
                ('outro', 'Step dance'),
                ('ciclismo', 'Aula de spinning')
            ]
            
            for i, registro in enumerate(registros_resistencia):
                esporte_escolhido, observacao_escolhida = esportes_resistencia[i % len(esportes_resistencia)]
                registro.esporte = esporte_escolhido
                registro.observacoes = observacao_escolhida
                registro.save()
                total_atualizados += 1
            
            self.stdout.write(self.style.SUCCESS(f"✓ Resistência: {len(registros_resistencia)} registros atualizados"))
            
            self.stdout.write("-" * 50)
            self.stdout.write(self.style.SUCCESS(f"Total de registros atualizados: {total_atualizados}"))
            
            # Estatísticas finais por esporte
            self.stdout.write("\nDistribuição por esporte:")
            from django.db.models import Count
            estatisticas = RegistroTreinamento.objects.filter(
                individuo=individuo
            ).values('esporte').annotate(
                quantidade=Count('id')
            ).order_by('esporte')
            
            for estat in estatisticas:
                self.stdout.write(f"- {estat['esporte']}: {estat['quantidade']} registros")
                
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"✗ Usuário {username} não encontrado"))
        except Individuo.DoesNotExist:
            self.stdout.write(self.style.ERROR(f"✗ Indivíduo para {username} não encontrado"))
        except Treinamento.DoesNotExist as e:
            self.stdout.write(self.style.ERROR(f"✗ Treinamento não encontrado: {e}"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Erro ao atualizar registros: {e}"))
