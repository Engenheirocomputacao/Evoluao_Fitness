"""
Dashboard and home views for treinamento app.
"""
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Avg, Count, Max, Min, StdDev
from django.utils import timezone
from datetime import timedelta, datetime

from ..models import Individuo, Treinamento, RegistroTreinamento
from ..utils import calcular_dias_consecutivos, get_or_create_individuo


def home_view(request):
    """Página inicial com botões de navegação para as funcionalidades"""
    if request.user.is_authenticated:
        individuo = get_or_create_individuo(request.user)

        # Estatísticas básicas para exibir na página inicial
        total_registros = RegistroTreinamento.objects.filter(individuo=individuo).count()
        total_treinamentos = RegistroTreinamento.objects.filter(individuo=individuo).values('treinamento').distinct().count()
        media_geral = RegistroTreinamento.objects.filter(individuo=individuo).aggregate(Avg('valor_alcançado'))['valor_alcançado__avg'] or 0
        dias_consecutivos = calcular_dias_consecutivos(individuo)

        # Últimos 10 registros de cada pilar (por nome do treinamento)

        ultimos_forca = RegistroTreinamento.objects.filter(
            individuo=individuo,
            treinamento__nome__icontains='força'
        ).select_related('treinamento').order_by('-data', '-id')[:3]

        ultimos_velocidade = RegistroTreinamento.objects.filter(
            individuo=individuo,
            treinamento__nome__icontains='velocidade'
        ).select_related('treinamento').order_by('-data', '-id')[:3]

        ultimos_resistencia = RegistroTreinamento.objects.filter(
            individuo=individuo,
            treinamento__nome__icontains='resist'
        ).select_related('treinamento').order_by('-data', '-id')[:3]

        context = {
            'individuo': individuo,
            'total_registros': total_registros,
            'total_treinamentos': total_treinamentos,
            'media_geral': media_geral,
            'dias_consecutivos': dias_consecutivos,
            'ultimos_forca': ultimos_forca,
            'ultimos_velocidade': ultimos_velocidade,
            'ultimos_resistencia': ultimos_resistencia,
        }
    else:
        context = {}

    return render(request, 'treinamento/home.html', context)


@login_required
def dashboard_view(request):
    individuo = get_or_create_individuo(request.user)
    dias_consecutivos = calcular_dias_consecutivos(individuo)

    # 1. Dados do Indivíduo Logado
    meus_registros = RegistroTreinamento.objects.filter(individuo=individuo).order_by('-data')[:10]
    minhas_medias = RegistroTreinamento.objects.filter(individuo=individuo).values('treinamento__nome').annotate(media=Avg('valor_alcançado'))
    
    # 2. Dados Gerais (para comparação)
    media_geral = RegistroTreinamento.objects.all().aggregate(Avg('valor_alcançado'))['valor_alcançado__avg']
    
    # 3. Dados para o gráfico de comparação de indivíduos (Top 10)
    top_individuos = RegistroTreinamento.objects.values('individuo__nome_completo').annotate(
        media_geral_individuo=Avg('valor_alcançado'),
        total_registros=Count('id')
    ).order_by('-media_geral_individuo')[:10]
    
    # 4. Dados para o gráfico de desempenho por treinamento
    desempenho_treinamento = RegistroTreinamento.objects.values('treinamento__nome').annotate(
        media=Avg('valor_alcançado'),
        contagem=Count('id')
    ).order_by('-media')
    
    # 5. Tipos de treinamento disponíveis
    tipos_treinamento = Treinamento.objects.all().values_list('nome', flat=True)
    
    # 6. Dados para comparação detalhada
    individuos_com_melhor_treinamento = []
    for ind in top_individuos:
        melhor_treinamento = RegistroTreinamento.objects.filter(
            individuo__nome_completo=ind['individuo__nome_completo']
        ).values('treinamento__nome').annotate(
            media=Avg('valor_alcançado')
        ).order_by('-media').first()
        
        ind['melhor_treinamento'] = melhor_treinamento['treinamento__nome'] if melhor_treinamento and 'treinamento__nome' in melhor_treinamento else 'N/A'
        
        if media_geral:
            diferenca_percentual = ((ind['media_geral_individuo'] - media_geral) / media_geral) * 100
            ind['diferenca_percentual'] = round(diferenca_percentual, 1)
        else:
            ind['diferenca_percentual'] = 0
        
        individuos_com_melhor_treinamento.append(ind)
    
    # 7. Dados para evolução temporal (últimos 4 meses)
    evolucao_temporal = []
    hoje = timezone.now().date()
    
    for i in range(4):
        mes_inicio = hoje.replace(day=1) - timedelta(days=30*i)
        mes_fim = (mes_inicio + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        registros_mes = RegistroTreinamento.objects.filter(
            individuo=individuo,
            data__gte=mes_inicio,
            data__lte=mes_fim
        )
        
        media_mes = registros_mes.aggregate(Avg('valor_alcançado'))['valor_alcançado__avg'] or 0
        
        evolucao_temporal.append({
            'mes': mes_inicio.strftime('%m/%Y'),
            'media': round(float(media_mes), 2),
            'total_registros': registros_mes.count()
        })
    
    evolucao_temporal.reverse()
    
    # 8. Distribuição de desempenho
    distribuicao_desempenho = {
        'excelente': RegistroTreinamento.objects.filter(valor_alcançado__gte=9).count(),
        'bom': RegistroTreinamento.objects.filter(valor_alcançado__gte=7, valor_alcançado__lt=9).count(),
        'regular': RegistroTreinamento.objects.filter(valor_alcançado__gte=5, valor_alcançado__lt=7).count(),
        'precisa_melhorar': RegistroTreinamento.objects.filter(valor_alcançado__lt=5).count()
    }
    
    # 9. Comparação por tipo de treinamento
    comparacao_tipo_treinamento = []
    for tipo in tipos_treinamento:
        if tipo:
            media_tipo = RegistroTreinamento.objects.filter(
                treinamento__nome=tipo
            ).aggregate(Avg('valor_alcançado'))['valor_alcançado__avg'] or 0
            
            media_usuario_tipo = RegistroTreinamento.objects.filter(
                individuo=individuo,
                treinamento__nome=tipo
            ).aggregate(Avg('valor_alcançado'))['valor_alcançado__avg'] or 0
            
            comparacao_tipo_treinamento.append({
                'tipo': tipo,
                'media_geral': round(float(media_tipo), 2),
                'media_usuario': round(float(media_usuario_tipo), 2),
                'diferenca': round(float(media_usuario_tipo - media_tipo), 2)
            })
    
    # 10. Melhores performances por tipo de treinamento (Top 5)
    melhores_performances = RegistroTreinamento.objects.values(
        'individuo__nome_completo', 
        'treinamento__nome'
    ).annotate(
        melhor_valor=Max('valor_alcançado')
    ).order_by('-melhor_valor')[:5]
    
    # 11. Consistência do usuário
    consistencia_usuario = RegistroTreinamento.objects.filter(
        individuo=individuo
    ).aggregate(
        desvio_padrao=StdDev('valor_alcançado')
    )['desvio_padrao'] or 0
    
    # 12. Ranking por tipo de treinamento
    ranking_por_tipo = {}
    for tipo in tipos_treinamento:
        if tipo:
            ranking_tipo = RegistroTreinamento.objects.filter(
                treinamento__nome=tipo
            ).values('individuo__nome_completo').annotate(
                media=Avg('valor_alcançado')
            ).order_by('-media')[:5]
            
            posicao_usuario = None
            for i, item in enumerate(ranking_tipo, 1):
                if item['individuo__nome_completo'] == individuo.nome_completo:
                    posicao_usuario = i
                    break
            
            ranking_por_tipo[tipo] = {
                'ranking': list(ranking_tipo),
                'posicao_usuario': posicao_usuario
            }
    
    # 13. Dados para heatmap de frequência
    dias_semana = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']
    horas_dia = ['6h', '8h', '10h', '12h', '14h', '16h', '18h', '20h']
    
    heatmap_frequencia = []
    for dia in dias_semana:
        for hora in horas_dia:
            frequencia = RegistroTreinamento.objects.filter(
                individuo=individuo,
                data__week_day=dias_semana.index(dia) + 1 if dias_semana.index(dia) < 6 else 1
            ).count() + 1
            heatmap_frequencia.append({
                'dia': dia,
                'hora': hora,
                'frequencia': min(frequencia, 10)
            })
    
    # 14. Dados para correlação
    correlacao_metricas = []
    registros_usuario = RegistroTreinamento.objects.filter(individuo=individuo)[:20]
    for registro in registros_usuario:
        correlacao_metricas.append({
            'frequencia': RegistroTreinamento.objects.filter(
                individuo=individuo,
                treinamento=registro.treinamento
            ).count(),
            'desempenho': float(registro.valor_alcançado),
            'treinamento': registro.treinamento.nome
        })

    context = {
        'individuo': individuo,
        'meus_registros': meus_registros,
        'minhas_medias': minhas_medias,
        'media_geral': media_geral,
        'top_individuos': individuos_com_melhor_treinamento,
        'desempenho_treinamento': desempenho_treinamento,
        'tipos_treinamento': list(tipos_treinamento),
        'evolucao_temporal': evolucao_temporal,
        'distribuicao_desempenho': distribuicao_desempenho,
        'comparacao_tipo_treinamento': comparacao_tipo_treinamento,
        'melhores_performances': list(melhores_performances),
        'consistencia_usuario': round(float(consistencia_usuario), 2),
        'ranking_por_tipo': ranking_por_tipo,
        'heatmap_frequencia': heatmap_frequencia,
        'correlacao_metricas': correlacao_metricas,
        'dias_consecutivos': dias_consecutivos,
    }
    return render(request, 'treinamento/dashboard.html', context)


@login_required
def dashboard_data_api(request):
    """API endpoint para retornar dados da dashboard em formato JSON"""
    try:
        individuo = request.user.individuo
    except Individuo.DoesNotExist:
        return JsonResponse({'error': 'Perfil não encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': f'Erro ao obter perfil: {str(e)}'}, status=500)
    
    try:
        # Parâmetros de filtro
        period_days = request.GET.get('period', 'all')  # Mudado de '30' para 'all' para mostrar todo o histórico
        training_type = request.GET.get('training_type', '')
        date_from = request.GET.get('date_from', '')
        date_to = request.GET.get('date_to', '')
        aggregation = request.GET.get('aggregation', 'weekly')

        # Base queryset
        queryset = RegistroTreinamento.objects.filter(individuo=individuo)

        # Aplicar filtros
        if period_days != 'all':
            try:
                days = int(period_days)
                start_date = timezone.now() - timedelta(days=days)
                queryset = queryset.filter(data__gte=start_date)
            except (ValueError, TypeError):
                pass

        if training_type:
            queryset = queryset.filter(treinamento__nome__icontains=training_type)

        if date_from:
            try:
                start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset = queryset.filter(data__gte=start_date)
            except (ValueError, TypeError):
                pass

        if date_to:
            try:
                end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset = queryset.filter(data__lte=end_date)
            except (ValueError, TypeError):
                pass

        # Dados filtrados
        meus_registros = queryset.order_by('-data')[:10]
        minhas_medias = queryset.values('treinamento__nome').annotate(media=Avg('valor_alcançado'))
        media_geral = queryset.aggregate(Avg('valor_alcançado'))['valor_alcançado__avg']

        # Dados para gráficos
        desempenho_treinamento = queryset.values('treinamento__nome').annotate(
            media=Avg('valor_alcançado'),
            contagem=Count('id')
        ).order_by('-media')

        # Evolução temporal
        evolucao_data = []
        evolucao_labels = []
        now = timezone.now()
        
        if aggregation == 'daily':
            # Últimos 14 dias
            for i in range(14):
                d = now - timedelta(days=i)
                day_data = queryset.filter(data__date=d.date())
                day_avg = day_data.aggregate(Avg('valor_alcançado'))['valor_alcançado__avg'] or 0
                evolucao_data.append(float(day_avg))
                evolucao_labels.append(d.strftime('%d/%m'))
        elif aggregation == 'monthly':
            # Últimos 6 meses
            for i in range(6):
                # Aproximação de meses
                m_start = (now.replace(day=1) - timedelta(days=i*30)).replace(day=1)
                # Próximo mês início - 1 dia
                m_end = (m_start + timedelta(days=32)).replace(day=1)
                month_data = queryset.filter(data__gte=m_start, data__lt=m_end)
                month_avg = month_data.aggregate(Avg('valor_alcançado'))['valor_alcançado__avg'] or 0
                evolucao_data.append(float(month_avg))
                evolucao_labels.append(m_start.strftime('%m/%y'))
        elif aggregation == 'yearly':
            # Últimos 3 anos
            current_year = now.year
            for i in range(3):
                year = current_year - i
                year_data = queryset.filter(data__year=year)
                year_avg = year_data.aggregate(Avg('valor_alcançado'))['valor_alcançado__avg'] or 0
                evolucao_data.append(float(year_avg))
                evolucao_labels.append(str(year))
        else: # weekly
            # Últimas 8 semanas
            for i in range(8):
                week_start = now - timedelta(weeks=i+1)
                week_end = now - timedelta(weeks=i)
                week_data = queryset.filter(data__gte=week_start, data__lt=week_end)
                week_avg = week_data.aggregate(Avg('valor_alcançado'))['valor_alcançado__avg'] or 0
                evolucao_data.append(float(week_avg))
                evolucao_labels.append(f'S {8-i}')
                
        evolucao_labels.reverse()
        evolucao_data.reverse()

        # Top indivíduos (buscar todos para encontrar posição do usuário)
        ranking_completo = []
        for item in RegistroTreinamento.objects.values('individuo__nome_completo').annotate(
            media_geral_individuo=Avg('valor_alcançado')
        ).order_by('-media_geral_individuo'):
            # Buscar avatar do indivíduo
            try:
                avatar_individuo = Individuo.objects.get(nome_completo=item['individuo__nome_completo'])
                avatar_url = avatar_individuo.avatar.url if avatar_individuo.avatar else None
            except Individuo.DoesNotExist:
                avatar_url = None
            
            ranking_completo.append({
                'nome_completo': item['individuo__nome_completo'],
                'media_geral_individuo': item['media_geral_individuo'],
                'avatar': avatar_url
            })
        
        # Limitar para 10 no display, mas manter posição do usuário
        top_individuos = ranking_completo[:10]
        
        # Encontrar posição do usuário logado
        posicao_usuario = None
        usuario_logado = request.user.individuo.nome_completo
        for i, item in enumerate(ranking_completo, 1):
            if item['nome_completo'] == usuario_logado:
                posicao_usuario = i
                break

        # Atividades recentes
        atividades = []
        for registro in meus_registros:
            atividades.append({
                'id': registro.id,
                'treinamento_nome': registro.treinamento.nome,
                'data': registro.data.strftime('%d/%m/%Y %H:%M'),
                'valor': float(registro.valor_alcançado),
                'unidade': registro.treinamento.unidade_medida,
                'observacoes': registro.observacoes or ''
            })

        # Ranking
        ranking = []
        for i, top in enumerate(top_individuos, 1):
            ranking.append({
                'posicao': i,
                'nome': top['nome_completo'],
                'media': float(top['media_geral_individuo']),
                'avatar': top['avatar']
            })
        
        # Adicionar dados do usuário se não estiver no top 10
        if posicao_usuario and posicao_usuario > 10:
            usuario_ranking = ranking_completo[posicao_usuario - 1]
            ranking.append({
                'posicao': posicao_usuario,
                'nome': usuario_ranking['nome_completo'],
                'media': float(usuario_ranking['media_geral_individuo']),
                'avatar': usuario_ranking['avatar'],
                'is_usuario_logado': True
            })
        elif posicao_usuario and posicao_usuario <= 10:
            # Marcar o usuário no top 10
            for item in ranking:
                if item['nome'] == usuario_logado:
                    item['is_usuario_logado'] = True
                    break

        # Estatísticas
        stats = {
            'total_registros': queryset.count(),
            'media_geral': float(media_geral) if media_geral else 0.0,
            'tipos_treinamento': minhas_medias.count(),
            'dias_consecutivos': calcular_dias_consecutivos(individuo)
        }
        
        # Distribuição de desempenho com categorização por tipo de treinamento
        # Primeiro obter todos os registros
        registros = queryset.select_related('treinamento')
        
        # Categorizar por tipo de treinamento e nível de desempenho
        distribuicao = {
            'excelente': {
                'count': registros.filter(valor_alcançado__gte=9).count(),
                'treinos': {
                    'força': registros.filter(valor_alcançado__gte=9, treinamento__nome__icontains='força').count(),
                    'resistência': registros.filter(valor_alcançado__gte=9, treinamento__nome__icontains='resistência').count(),
                    'velocidade': registros.filter(valor_alcançado__gte=9, treinamento__nome__icontains='velocidade').count(),
                    'outros': registros.filter(valor_alcançado__gte=9).exclude(treinamento__nome__icontains='força').exclude(treinamento__nome__icontains='resistência').exclude(treinamento__nome__icontains='velocidade').count()
                }
            },
            'bom': {
                'count': registros.filter(valor_alcançado__gte=7, valor_alcançado__lt=9).count(),
                'treinos': {
                    'força': registros.filter(valor_alcançado__gte=7, valor_alcançado__lt=9, treinamento__nome__icontains='força').count(),
                    'resistência': registros.filter(valor_alcançado__gte=7, valor_alcançado__lt=9, treinamento__nome__icontains='resistência').count(),
                    'velocidade': registros.filter(valor_alcançado__gte=7, valor_alcançado__lt=9, treinamento__nome__icontains='velocidade').count(),
                    'outros': registros.filter(valor_alcançado__gte=7, valor_alcançado__lt=9).exclude(treinamento__nome__icontains='força').exclude(treinamento__nome__icontains='resistência').exclude(treinamento__nome__icontains='velocidade').count()
                }
            },
            'regular': {
                'count': registros.filter(valor_alcançado__gte=5, valor_alcançado__lt=7).count(),
                'treinos': {
                    'força': registros.filter(valor_alcançado__gte=5, valor_alcançado__lt=7, treinamento__nome__icontains='força').count(),
                    'resistência': registros.filter(valor_alcançado__gte=5, valor_alcançado__lt=7, treinamento__nome__icontains='resistência').count(),
                    'velocidade': registros.filter(valor_alcançado__gte=5, valor_alcançado__lt=7, treinamento__nome__icontains='velocidade').count(),
                    'outros': registros.filter(valor_alcançado__gte=5, valor_alcançado__lt=7).exclude(treinamento__nome__icontains='força').exclude(treinamento__nome__icontains='resistência').exclude(treinamento__nome__icontains='velocidade').count()
                }
            },
            'precisa_melhorar': {
                'count': registros.filter(valor_alcançado__lt=5).count(),
                'treinos': {
                    'força': registros.filter(valor_alcançado__lt=5, treinamento__nome__icontains='força').count(),
                    'resistência': registros.filter(valor_alcançado__lt=5, treinamento__nome__icontains='resistência').count(),
                    'velocidade': registros.filter(valor_alcançado__lt=5, treinamento__nome__icontains='velocidade').count(),
                    'outros': registros.filter(valor_alcançado__lt=5).exclude(treinamento__nome__icontains='força').exclude(treinamento__nome__icontains='resistência').exclude(treinamento__nome__icontains='velocidade').count()
                }
            }
        }

        # Comparação por tipo de treinamento
        tipos_disponiveis = Treinamento.objects.all().values_list('nome', flat=True)
        comparacao_tipo_treinamento = []
        
        queryset_comparacao = RegistroTreinamento.objects.all()
        
        if period_days != 'all':
            try:
                days = int(period_days)
                start_date = timezone.now() - timedelta(days=days)
                queryset_comparacao = queryset_comparacao.filter(data__gte=start_date)
            except (ValueError, TypeError):
                pass

        if training_type:
            queryset_comparacao = queryset_comparacao.filter(treinamento__nome__icontains=training_type)

        if date_from:
            try:
                start_date = datetime.strptime(date_from, '%Y-%m-%d').date()
                queryset_comparacao = queryset_comparacao.filter(data__gte=start_date)
            except (ValueError, TypeError):
                pass

        if date_to:
            try:
                end_date = datetime.strptime(date_to, '%Y-%m-%d').date()
                queryset_comparacao = queryset_comparacao.filter(data__lte=end_date)
            except (ValueError, TypeError):
                pass

        for tipo in tipos_disponiveis:
            if tipo:
                media_tipo = queryset_comparacao.filter(
                    treinamento__nome=tipo
                ).aggregate(Avg('valor_alcançado'))['valor_alcançado__avg'] or 0
                
                media_usuario_tipo = queryset.filter(
                    treinamento__nome=tipo
                ).aggregate(Avg('valor_alcançado'))['valor_alcançado__avg'] or 0
                
                comparacao_tipo_treinamento.append({
                    'tipo': tipo,
                    'media_geral': round(float(media_tipo), 2),
                    'media_usuario': round(float(media_usuario_tipo), 2),
                    'diferenca': round(float(media_usuario_tipo - media_tipo), 2)
                })

        # Heatmap
        dias_semana = ['Dom', 'Seg', 'Ter', 'Qua', 'Qui', 'Sex', 'Sáb']
        horas_dia = ['6h', '8h', '10h', '12h', '14h', '16h', '18h', '20h']
        
        heatmap_data = []
        for dia in dias_semana:
            for hora in horas_dia:
                frequencia = queryset.filter(
                    data__week_day=dias_semana.index(dia) + 1 if dias_semana.index(dia) < 6 else 1
                ).count() + 1
                heatmap_data.append({
                    'dia': dia,
                    'hora': hora,
                    'frequencia': min(frequencia, 10)
                })
        
        # Correlação
        correlacao_data = []
        for registro in queryset[:20]:
            correlacao_data.append({
                'frequencia': queryset.filter(treinamento=registro.treinamento).count(),
                'desempenho': float(registro.valor_alcançado),
                'treinamento': registro.treinamento.nome
            })
        
        # ===== NOVOS DADOS =====
        
        # 1. ESFORÇO PERCEBIDO
        esforco_por_treino = queryset.values('treinamento__nome').annotate(
            media_esforco=Avg('esforco_percebido'),
            media_desempenho=Avg('valor_alcançado')
        ).exclude(media_esforco__isnull=True).order_by('-media_desempenho')
        
        # 1.1 ESFORÇO PERCEBIDO POR TIPO DE TREINAMENTO (força, resistência, velocidade)
        esforco_por_tipo = []
        
        # Força
        forca_registros = queryset.filter(
            treinamento__nome__icontains='força'
        ).values('treinamento__nome').annotate(
            media_esforco=Avg('esforco_percebido'),
            media_desempenho=Avg('valor_alcançado')
        ).exclude(media_esforco__isnull=True)
        
        for item in forca_registros:
            esforco_por_tipo.append({
                'treino': item['treinamento__nome'],
                'esforco': round(float(item['media_esforco'] or 0), 1),
                'desempenho': round(float(item['media_desempenho']), 2),
                'tipo': 'força'
            })
        
        # Resistência
        resistencia_registros = queryset.filter(
            treinamento__nome__icontains='resist'
        ).values('treinamento__nome').annotate(
            media_esforco=Avg('esforco_percebido'),
            media_desempenho=Avg('valor_alcançado')
        ).exclude(media_esforco__isnull=True)
        
        for item in resistencia_registros:
            esforco_por_tipo.append({
                'treino': item['treinamento__nome'],
                'esforco': round(float(item['media_esforco'] or 0), 1),
                'desempenho': round(float(item['media_desempenho']), 2),
                'tipo': 'resistência'
            })
        
        # Velocidade
        velocidade_registros = queryset.filter(
            treinamento__nome__icontains='velocidade'
        ).values('treinamento__nome').annotate(
            media_esforco=Avg('esforco_percebido'),
            media_desempenho=Avg('valor_alcançado')
        ).exclude(media_esforco__isnull=True)
        
        for item in velocidade_registros:
            esforco_por_tipo.append({
                'treino': item['treinamento__nome'],
                'esforco': round(float(item['media_esforco'] or 0), 1),
                'desempenho': round(float(item['media_desempenho']), 2),
                'tipo': 'velocidade'
            })
        
        # 2. DURAÇÃO DO TREINO
        from django.db.models.functions import Extract
        duracao_stats = {}
        for tipo in Treinamento.objects.all():
            registros_tipo = queryset.filter(treinamento=tipo).exclude(duracao__isnull=True)
            if registros_tipo.exists():
                # Converter duration para minutos
                duracao_media = registros_tipo.aggregate(Avg('duracao'))['duracao__avg']
                if duracao_media:
                    duracao_minutos = duracao_media.total_seconds() / 60
                    media_desempenho = registros_tipo.aggregate(Avg('valor_alcançado'))['valor_alcançado__avg']
                    duracao_stats[tipo.nome] = {
                        'media_minutos': round(duracao_minutos, 1),
                        'media_desempenho': round(float(media_desempenho), 2),
                        'produtividade': round(float(media_desempenho) / (duracao_minutos or 1), 3),  # Resultado por minuto
                        'contagem': registros_tipo.count()
                    }
        
        # 3. DESEMPENHO POR ESPORTE
        esporte_stats = queryset.values('esporte').annotate(
            media=Avg('valor_alcançado'),
            contagem=Count('id'),
            esforco_medio=Avg('esforco_percebido')
        ).exclude(esporte='').filter(esporte__isnull=False).order_by('-media')
        
        esporte_labels = {
            'corrida': 'Corrida',
            'ciclismo': 'Ciclismo',
            'caminhada': 'Caminhada',
            'natacao': 'Natação',
            'musculacao': 'Musculação',
            'outro': 'Outro'
        }
        
        esporte_data = []
        for esporte in esporte_stats:
            label = esporte_labels.get(esporte['esporte'], esporte['esporte'])
            esporte_data.append({
                'nome': label,
                'media': round(float(esporte['media']), 2),
                'contagem': esporte['contagem'],
                'esforco_medio': round(float(esporte['esforco_medio'] or 0), 1)
            })
        
        # 4. PESO DO USUÁRIO (Correlação)
        
        # Função auxiliar para obter peso para uma data específica
        def obter_peso_para_data(individuo, data_registro):
            from ..models import PesoHistorico
            from django.utils import timezone

            # Procurar primeiro no histórico de peso para a data específica ou mais próxima
            peso_historico = PesoHistorico.objects.filter(
                individuo=individuo,
                data_registro__lte=data_registro
            ).order_by('-data_registro').first()

            if peso_historico:
                return float(peso_historico.peso)
            else:
                # Se não encontrar no histórico, usar o peso atual
                return float(individuo.peso) if individuo.peso else 0.0

        peso_atual = individuo.peso
        peso_history = {}
        
        # SEMPRE criar dados de desempenho, mesmo sem peso
        # Primeiros e últimos registros para calcular tendência
        primeiro_registro = queryset.order_by('data').first()
        ultimo_registro = queryset.order_by('-data').first()
        
        if primeiro_registro and ultimo_registro:
            # Obter média geral do usuário para normalizar
            media_usuario = queryset.aggregate(Avg('valor_alcançado'))['valor_alcançado__avg'] or 10
            media_usuario = float(media_usuario) if media_usuario else 10
            
            primeira_media_bruta = queryset.filter(
                data__gte=primeiro_registro.data,
                data__lte=primeiro_registro.data + timedelta(days=7)
            ).aggregate(Avg('valor_alcançado'))['valor_alcançado__avg'] or 0
            
            ultima_media_bruta = queryset.filter(
                data__gte=ultimo_registro.data - timedelta(days=7),
                data__lte=ultimo_registro.data
            ).aggregate(Avg('valor_alcançado'))['valor_alcançado__avg'] or 0
            
            # Converter para escala de 0-10
            primeira_media = min(10, float(primeira_media_bruta) * 10 / max(media_usuario, 1))
            ultima_media = min(10, float(ultima_media_bruta) * 10 / max(media_usuario, 1))
            
            # Criar histórico de desempenho ao longo do tempo
            registros_ordenados = queryset.order_by('data')
            historico_desempenho = []
            
            # Pegar registros espaçados para criar histórico
            total_registros = registros_ordenados.count()
            if total_registros > 0:
                # Pegar no máximo 10 pontos para o histórico
                intervalo = max(1, total_registros // 10)
                for i in range(0, total_registros, intervalo):
                    registro = registros_ordenados[i]
                    # Converter o valor_alcançado para uma escala de 0-10 baseada na média do usuário
                    media_usuario = queryset.aggregate(Avg('valor_alcançado'))['valor_alcançado__avg'] or 10
                    media_usuario = float(media_usuario) if media_usuario else 10
                    valor_normalizado = min(10, float(registro.valor_alcançado) * 10 / max(media_usuario, 1))
                    
                    # Obter peso correspondente à data do registro (pode ser 0 se não tiver peso)
                    peso_no_periodo = obter_peso_para_data(individuo, registro.data)

                    historico_desempenho.append({
                        'data': registro.data.isoformat(),
                        'peso': peso_no_periodo,  # Peso na data do registro (ou 0)
                        'desempenho_medio': round(valor_normalizado, 2)
                    })
                
                # Se tivermos poucos registros, adicionar o primeiro e último
                if total_registros > 0:
                    primeiro = registros_ordenados.first()
                    ultimo = registros_ordenados.last()
                    if primeiro != ultimo:
                        # Adicionar primeiro e último se não estiverem no histórico
                        primeiro_existe = any(r['data'] == primeiro.data.isoformat() for r in historico_desempenho)
                        ultimo_existe = any(r['data'] == ultimo.data.isoformat() for r in historico_desempenho)
                        
                        if not primeiro_existe:
                            media_usuario = queryset.aggregate(Avg('valor_alcançado'))['valor_alcançado__avg'] or 10
                            media_usuario = float(media_usuario) if media_usuario else 10
                            valor_primeiro_normalizado = min(10, float(primeiro.valor_alcançado) * 10 / max(media_usuario, 1))
                            peso_no_periodo = obter_peso_para_data(individuo, primeiro.data)
                            historico_desempenho.append({
                                'data': primeiro.data.isoformat(),
                                'peso': peso_no_periodo,
                                'desempenho_medio': round(valor_primeiro_normalizado, 2)
                            })
                        if not ultimo_existe:
                            media_usuario = queryset.aggregate(Avg('valor_alcançado'))['valor_alcançado__avg'] or 10
                            media_usuario = float(media_usuario) if media_usuario else 10
                            valor_ultimo_normalizado = min(10, float(ultimo.valor_alcançado) * 10 / max(media_usuario, 1))
                            peso_no_periodo = obter_peso_para_data(individuo, ultimo.data)
                            historico_desempenho.append({
                                'data': ultimo.data.isoformat(),
                                'peso': peso_no_periodo,
                                'desempenho_medio': round(valor_ultimo_normalizado, 2)
                            })
                
                # Ordenar histórico por data
                historico_desempenho.sort(key=lambda x: x['data'])
        
        # Montar estrutura de peso_history SEMPRE (mesmo sem peso)
        if primeiro_registro and ultimo_registro:
            peso_history = {
                'peso_atual': float(peso_atual) if peso_atual else None,
                'desempenho_inicial': float(round(primeira_media, 2)),
                'desempenho_atual': float(round(ultima_media, 2)),
                'melhora_desempenho': float(round(ultima_media - primeira_media, 2)),
                'historico': historico_desempenho
            }
        else:
            # Sem dados de treinamento
            peso_history = {
                'peso_atual': float(peso_atual) if peso_atual else None,
                'desempenho_inicial': 0,
                'desempenho_atual': 0,
                'melhora_desempenho': 0,
                'historico': []
            }
        
        # 5. COMPARAÇÃO COM PEERS (Sexo e Faixa Etária)
        def calcular_idade(data_nascimento):
            today = timezone.now().date()
            return today.year - data_nascimento.year - ((today.month, today.day) < (data_nascimento.month, data_nascimento.day))
        
        idade_usuario = calcular_idade(individuo.data_nascimento) if individuo.data_nascimento else None
        sexo_usuario = individuo.sexo
        
        peers_stats = {
            'idade': idade_usuario,
            'sexo': sexo_usuario,
            'sua_media': round(float(media_geral or 0), 2),
            'total_treinos': queryset.count(),
            'percentil_estimado': None,
            'status_comparativo': 'Dados insuficientes'
        }
        
        # Estimar posição (simplificado - comparar com todos)
        if media_geral:
            total_usuarios = Individuo.objects.count()
            usuarios_com_melhor_media = Individuo.objects.annotate(
                media=Avg('registros__valor_alcançado')
            ).filter(media__gt=media_geral).count()
            
            if total_usuarios > 0:
                percentil = round((1 - (usuarios_com_melhor_media / total_usuarios)) * 100, 1)
                peers_stats['percentil_estimado'] = percentil
                
                if percentil >= 75:
                    peers_stats['status_comparativo'] = 'Excelente'
                elif percentil >= 50:
                    peers_stats['status_comparativo'] = 'Acima da Média'
                elif percentil >= 25:
                    peers_stats['status_comparativo'] = 'Média'
                else:
                    peers_stats['status_comparativo'] = 'Abaixo da Média'
        
        # Melhores performances por tipo de treinamento (Top 5)
        melhores_performances = RegistroTreinamento.objects.values(
            'individuo__nome_completo', 
            'treinamento__nome'
        ).annotate(
            melhor_valor=Max('valor_alcançado')
        ).order_by('-melhor_valor')[:5]
        
        response_data = {
            'stats': stats,
            'desempenho_treinamento': [
                {
                    'nome': item['treinamento__nome'],
                    'media': float(item['media']),
                    'contagem': item['contagem']
                } for item in desempenho_treinamento
            ],
            'evolucao': {
                'labels': evolucao_labels,
                'data': evolucao_data
            },
            'distribuicao': distribuicao,
            'top_individuos': ranking,
            'atividades_recentes': atividades[:5],
            'minhas_medias': [
                {
                    'treinamento': item['treinamento__nome'],
                    'media': float(item['media'])
                } for item in minhas_medias
            ],
            'comparacao_tipo_treinamento': comparacao_tipo_treinamento,
            'heatmap_frequencia': heatmap_data,
            'correlacao_metricas': correlacao_data,
            'melhores_performances': [
                {
                    'individuo_nome': item['individuo__nome_completo'],
                    'treinamento_nome': item['treinamento__nome'],
                    'melhor_valor': float(item['melhor_valor'])
                } for item in melhores_performances
            ],
            # NOVOS DADOS
            'esforco_por_treino': [
                {
                    'treino': item['treinamento__nome'],
                    'esforco': round(float(item['media_esforco'] or 0), 1),
                    'desempenho': round(float(item['media_desempenho']), 2)
                } for item in esforco_por_treino
            ],
            'esforco_por_tipo': [
                {
                    'treino': item['treino'],
                    'esforco': item['esforco'],
                    'desempenho': item['desempenho'],
                    'tipo': item['tipo']
                } for item in esforco_por_tipo
            ],
            'duracao_por_treino': duracao_stats,
            'esporte_stats': esporte_data,
            'peso_desempenho': peso_history,
            'peers_comparison': peers_stats
        }

        return JsonResponse(response_data)
    except Exception as e:
        import traceback
        return JsonResponse({'error': f'Erro ao processar dados: {str(e)}', 'traceback': traceback.format_exc()}, status=500)


def sobre_view(request):
    """Página com informações sobre o projeto"""
    return render(request, 'treinamento/sobre.html')
