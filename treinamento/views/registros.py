"""
Registros and treinamentos views for treinamento app.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Avg

from ..models import Treinamento, RegistroTreinamento
from ..forms import RegistroTreinamentoForm
from ..utils import get_or_create_individuo


@login_required

def treinamentos_view(request, treinamento_id=None):
    """View para gerenciar treinamentos"""
    individuo = get_or_create_individuo(request.user)

    # Obter todos os treinamentos ordenados por nome
    treinamentos = Treinamento.objects.all().order_by('nome')

    # Obter os últimos registros de cada treinamento para o usuário logado
    registros_por_treinamento = {}

    for treinamento in treinamentos:
        ultimo_registro = RegistroTreinamento.objects.filter(
            individuo=individuo,
            treinamento=treinamento
        ).order_by('-data').first()

        if ultimo_registro:
            registros_por_treinamento[treinamento.id] = {
                'valor': ultimo_registro.valor_alcançado,
                'data': ultimo_registro.data,
                'unidade': treinamento.get_unidade_medida_display()
            }
            registros_por_treinamento[str(treinamento.id)] = {
                'valor': ultimo_registro.valor_alcançado,
                'data': ultimo_registro.data,
                'unidade': treinamento.get_unidade_medida_display()
            }
        else:
            registros_por_treinamento[treinamento.id] = {
                'valor': None,
                'data': None,
                'unidade': treinamento.get_unidade_medida_display()
            }
            registros_por_treinamento[str(treinamento.id)] = {
                'valor': None,
                'data': None,
                'unidade': treinamento.get_unidade_medida_display()
            }

    # Obter os 10 últimos registros de cada pilar
    registros_forca = RegistroTreinamento.objects.filter(
        individuo=individuo,
        treinamento__nome__icontains='força'
    ).select_related('treinamento').order_by('-data', '-id')[:10]

    registros_velocidade = RegistroTreinamento.objects.filter(
        individuo=individuo,
        treinamento__nome__icontains='velocidade'
    ).select_related('treinamento').order_by('-data', '-id')[:10]

    registros_resistencia = RegistroTreinamento.objects.filter(
        individuo=individuo,
        treinamento__nome__icontains='resist'
    ).select_related('treinamento').order_by('-data', '-id')[:10]

    # Obter registros para os novos tipos de treinamento
    registros_flexoes = RegistroTreinamento.objects.filter(
        individuo=individuo,
        treinamento__nome__icontains='flex'
    ).select_related('treinamento').order_by('-data', '-id')[:10]

    registros_corrida_leve = RegistroTreinamento.objects.filter(
        individuo=individuo,
        treinamento__nome__icontains='corrida leve'
    ).select_related('treinamento').order_by('-data', '-id')[:10]

    registros_caminhada = RegistroTreinamento.objects.filter(
        individuo=individuo,
        treinamento__nome__icontains='caminhada'
    ).select_related('treinamento').order_by('-data', '-id')[:10]

    registros_natacao = RegistroTreinamento.objects.filter(
        individuo=individuo,
        treinamento__nome__icontains='nata'
    ).select_related('treinamento').order_by('-data', '-id')[:10]

    registros_ciclismo = RegistroTreinamento.objects.filter(
        individuo=individuo,
        treinamento__nome__icontains='cicl'
    ).select_related('treinamento').order_by('-data', '-id')[:10]

    context = {
        'individuo': individuo,
        'treinamentos': treinamentos,
        'registros_por_treinamento': registros_por_treinamento,
        'registros_forca': registros_forca,
        'registros_velocidade': registros_velocidade,
        'registros_resistencia': registros_resistencia,
        'registros_flexoes': registros_flexoes,
        'registros_corrida_leve': registros_corrida_leve,
        'registros_caminhada': registros_caminhada,
        'registros_natacao': registros_natacao,
        'registros_ciclismo': registros_ciclismo,
    }

    return render(request, 'treinamento/treinamentos.html', context)


@login_required
def registros_view(request):
    """View para gerenciar registros de treinamento"""
    individuo = get_or_create_individuo(request.user)
    
    from django.core.paginator import Paginator
    
    registros = RegistroTreinamento.objects.filter(individuo=individuo).order_by('-data')
    
    # Paginação: 10 registros por página
    paginator = Paginator(registros, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    treinamentos = Treinamento.objects.all()
    
    # Calcular a média dos registros
    media_geral = registros.aggregate(Avg('valor_alcançado'))['valor_alcançado__avg']
    if media_geral is None:
        media_geral = 0.0
    
    # Calcular a média dos registros da página atual
    media_pagina = page_obj.object_list.aggregate(Avg('valor_alcançado'))['valor_alcançado__avg']
    if media_pagina is None:
        media_pagina = 0.0
    
    # Verificar se é uma requisição POST para criar/editar registro
    if request.method == 'POST':
        # Verificar se é uma operação de exclusão
        if 'delete_registro' in request.POST:
            registro_id = request.POST.get('registro_id')
            try:
                registro = RegistroTreinamento.objects.get(
                    id=registro_id,
                    individuo=individuo
                )
                registro.delete()
                messages.success(request, 'Registro excluído com sucesso!')
            except RegistroTreinamento.DoesNotExist:
                messages.error(request, 'Registro não encontrado.')
            return redirect('registros_view')
        
        # Verificar se é uma operação de edição
        registro_id = request.POST.get('registro_id')
        if registro_id:
            try:
                registro = RegistroTreinamento.objects.get(
                    id=registro_id,
                    individuo=individuo
                )
                form = RegistroTreinamentoForm(request.POST, instance=registro, individuo=individuo)
            except RegistroTreinamento.DoesNotExist:
                messages.error(request, 'Registro não encontrado.')
                form = RegistroTreinamentoForm(request.POST, individuo=individuo)
        else:
            # Operação de criação
            form = RegistroTreinamentoForm(request.POST, individuo=individuo)
        
        if form.is_valid():
            registro = form.save(commit=False)
            registro.individuo = individuo
            registro.save()
            action = "atualizado" if registro_id else "adicionado"
            messages.success(request, f'Registro {action} com sucesso!')
            return redirect('registros_view')
        else:
            messages.error(request, 'Por favor, corrija os erros abaixo.')
    else:
        form = RegistroTreinamentoForm(individuo=individuo)
    
    context = {
        'individuo': individuo,
        'registros': page_obj,
        'treinamentos': treinamentos,
        'form': form,
        'media_geral': media_geral,
    }
    return render(request, 'treinamento/registros.html', context)
