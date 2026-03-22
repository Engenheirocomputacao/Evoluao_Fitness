"""
Relatórios and ranking views for treinamento app.
"""
import os
from pathlib import Path
from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Avg, Count, Max, Min
from django.utils import timezone
from datetime import timedelta
from django.conf import settings

from ..models import RegistroTreinamento
from ..utils import is_admin_user, get_or_create_individuo, calcular_dias_consecutivos


@login_required
def relatorios_view(request):
    """View para relatórios e estatísticas"""
    individuo = get_or_create_individuo(request.user)
    
    # Estatísticas detalhadas
    registros = RegistroTreinamento.objects.filter(individuo=individuo)
    
    # Estatísticas por treinamento
    stats_treinamento = list(registros.values('treinamento__nome').annotate(
        total=Count('id'),
        media=Avg('valor_alcançado'),
        maximo=Max('valor_alcançado'),
        minimo=Min('valor_alcançado')
    ).order_by('-media'))
    
    # Calcular largura da barra de progresso e definir cores
    for stat in stats_treinamento:
        media = float(stat['media'] or 0)
        maximo = float(stat['maximo'] or 0)
        minimo = float(stat['minimo'] or 0)
        
        if maximo > minimo:
            # Posicionamento da média entre o mínimo e o máximo
            progresso = ((media - minimo) / (maximo - minimo)) * 100
            stat['progress_width'] = round(progresso, 1)
        elif maximo > 0:
            # Se max == min, mas > 0, atingiu o máximo histórico (ou só tem 1 registro)
            stat['progress_width'] = 100.0
        else:
            stat['progress_width'] = 0.0
            
        # Determinar cor/classe baseada no progresso
        if stat['progress_width'] >= 80:
            stat['progress_color'] = '#10b981' # Green/Success
        elif stat['progress_width'] >= 50:
            stat['progress_color'] = '#f59e0b' # Orange/Warning
        else:
            stat['progress_color'] = '#ef4444' # Red/Danger
    
    # Estatísticas mensais
    stats_mensais = registros.extra(
        select={'month': 'strftime("%%Y-%%m", data)'}
    ).values('month').annotate(
        total=Count('id'),
        media=Avg('valor_alcançado')
    ).order_by('-month')[:12]
    
    context = {
        'individuo': individuo,
        'stats_treinamento': stats_treinamento,
        'stats_mensais': stats_mensais,
        'total_registros': registros.count(),
        'dias_consecutivos': calcular_dias_consecutivos(individuo),
    }
    return render(request, 'treinamento/relatorios.html', context)


@login_required
def ranking_view(request):
    """View para ranking de usuários"""
    individuo = get_or_create_individuo(request.user)
    
    # Lista de avatares disponíveis
    avatar_dir = settings.MEDIA_ROOT / 'avatars'
    available_avatars = []
    if avatar_dir.exists():
        available_avatars = [f.name for f in avatar_dir.iterdir() if f.is_file() and f.suffix.lower() in ['.png', '.jpg', '.jpeg', '.gif']]
    
    # Ranking geral
    ranking_geral_qs = RegistroTreinamento.objects.values('individuo__nome_completo').annotate(
        media_geral=Avg('valor_alcançado'),
        total_registros=Count('id')
    ).filter(total_registros__gte=5).order_by('-media_geral')
    
    # Processa ranking geral para lista com posição
    ranking_geral = []
    user_in_top_10 = False
    user_rank_data = None
    
    for i, item in enumerate(ranking_geral_qs, 1):
        item['rank'] = i
        # Adiciona avatar para top 10
        if i <= 10 and available_avatars:
            avatar_index = (i - 1) % len(available_avatars)
            item['avatar'] = f'/media/avatars/{available_avatars[avatar_index]}'
        else:
            item['avatar'] = None
            
        if i <= 10:
            ranking_geral.append(item)
            if item['individuo__nome_completo'] == individuo.nome_completo:
                user_in_top_10 = True
        
        if item['individuo__nome_completo'] == individuo.nome_completo:
            user_rank_data = item
            
    # Se usuário não estiver no top 10, adiciona ele no final
    if user_rank_data and not user_in_top_10:
        ranking_geral.append(user_rank_data)
        
    posicao_usuario = user_rank_data['rank'] if user_rank_data else None

    # Ranking mensal
    data_inicio_mensal = timezone.now() - timedelta(days=30)
    ranking_mensal_qs = RegistroTreinamento.objects.filter(
        data__gte=data_inicio_mensal
    ).values('individuo__nome_completo').annotate(
        media_mensal=Avg('valor_alcançado'),
        total_registros=Count('id')
    ).filter(total_registros__gte=3).order_by('-media_mensal')
    
    # Processa ranking mensal para lista com posição
    ranking_mensal = []
    user_in_top_10_monthly = False
    user_rank_monthly_data = None
    
    for i, item in enumerate(ranking_mensal_qs, 1):
        item['rank'] = i
        # Adiciona avatar para top 10 mensal
        if i <= 10 and available_avatars:
            avatar_index = (i - 1) % len(available_avatars)
            item['avatar'] = f'/media/avatars/{available_avatars[avatar_index]}'
        else:
            item['avatar'] = None
            
        if i <= 10:
            ranking_mensal.append(item)
            if item['individuo__nome_completo'] == individuo.nome_completo:
                user_in_top_10_monthly = True
        
        if item['individuo__nome_completo'] == individuo.nome_completo:
            user_rank_monthly_data = item
            
    # Se usuário não estiver no top 10, adiciona ele no final
    if user_rank_monthly_data and not user_in_top_10_monthly:
        ranking_mensal.append(user_rank_monthly_data)
    
    context = {
        'individuo': individuo,
        'ranking_geral': ranking_geral,
        'ranking_mensal': ranking_mensal,
        'posicao_usuario': posicao_usuario,
    }
    return render(request, 'treinamento/ranking.html', context)


@login_required
@user_passes_test(is_admin_user)
def admin_only_view(request):
    """View de exemplo que só pode ser acessada por administradores"""
    return render(request, 'treinamento/admin_only.html')
