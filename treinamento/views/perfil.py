"""
Perfil and calendar views for treinamento app.
"""
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Avg
from django.utils import timezone

from ..models import RegistroTreinamento
from ..utils import calcular_dias_consecutivos, get_or_create_individuo


@login_required
def perfil_view(request):
    """View para perfil do usuário"""
    individuo = get_or_create_individuo(request.user)
    
    if request.method == 'POST':
        # Verifica se é uma requisição AJAX para upload de avatar
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            if 'avatar' in request.FILES:
                individuo.avatar = request.FILES['avatar']
                individuo.save()
                # Return the URL only if avatar exists and has a URL
                avatar_url = None
                if individuo.avatar and hasattr(individuo.avatar, 'url'):
                    try:
                        avatar_url = individuo.avatar.url
                    except ValueError:
                        avatar_url = None
                
                return JsonResponse({
                    'success': True,
                    'avatar_url': avatar_url
                })
            return JsonResponse({'success': False, 'error': 'Nenhuma imagem fornecida'}, status=400)
        
        # Processamento normal do formulário
        individuo.nome_completo = request.POST.get('nome_completo')
        
        # Processar data de nascimento (formato DD/MM/AAAA -> YYYY-MM-DD)
        data_nascimento_str = request.POST.get('data_nascimento')
        if data_nascimento_str:
            # Converter data do formato DD/MM/AAAA para YYYY-MM-DD
            try:
                if '/' in data_nascimento_str:
                    partes = data_nascimento_str.split('/')
                    if len(partes) == 3:
                        dia, mes, ano = partes
                        # Verifica se cada parte é um número válido
                        dia = dia.zfill(2)
                        mes = mes.zfill(2)
                        ano = ano
                        
                        # Validação adicional para garantir que os valores são válidos
                        dia_int = int(dia)
                        mes_int = int(mes)
                        ano_int = int(ano)
                        
                        if not (1 <= dia_int <= 31 and 1 <= mes_int <= 12 and 1900 <= ano_int <= 2025):
                            messages.error(request, 'Data de nascimento inválida. Verifique os valores (dia, mês, ano).')
                            return render(request, 'treinamento/perfil.html', {
                                'individuo': individuo,
                                'total_registros': RegistroTreinamento.objects.filter(individuo=individuo).count(),
                                'media_geral': RegistroTreinamento.objects.filter(individuo=individuo).aggregate(
                                    Avg('valor_alcançado')
                                )['valor_alcançado__avg'] or 0,
                                'dias_consecutivos': calcular_dias_consecutivos(individuo),
                            })
                        
                        individuo.data_nascimento = f'{ano}-{mes}-{dia}'
                    else:
                        messages.error(request, 'Formato de data de nascimento inválido. Use DD/MM/AAAA.')
                        return render(request, 'treinamento/perfil.html', {
                            'individuo': individuo,
                            'total_registros': RegistroTreinamento.objects.filter(individuo=individuo).count(),
                            'media_geral': RegistroTreinamento.objects.filter(individuo=individuo).aggregate(
                                Avg('valor_alcançado')
                            )['valor_alcançado__avg'] or 0,
                            'dias_consecutivos': calcular_dias_consecutivos(individuo),
                        })
                else:
                    # Se já estiver no formato YYYY-MM-DD
                    individuo.data_nascimento = data_nascimento_str
            except ValueError:
                messages.error(request, 'Data de nascimento inválida. Use DD/MM/AAAA com números válidos.')
                return render(request, 'treinamento/perfil.html', {
                    'individuo': individuo,
                    'total_registros': RegistroTreinamento.objects.filter(individuo=individuo).count(),
                    'media_geral': RegistroTreinamento.objects.filter(individuo=individuo).aggregate(
                        Avg('valor_alcançado')
                    )['valor_alcançado__avg'] or 0,
                    'dias_consecutivos': calcular_dias_consecutivos(individuo),
                })
        else:
            individuo.data_nascimento = None
        
        # Verificar se o peso foi alterado
        novo_peso = request.POST.get('peso')
        if novo_peso:
            novo_peso = float(novo_peso)
            # Verificar se o peso mudou significativamente
            from ..models import PesoHistorico
            from django.utils import timezone
            hoje = timezone.now().date()
            
            # Verificar se já existe um registro de peso para hoje
            try:
                peso_historico = PesoHistorico.objects.get(individuo=individuo, data_registro=hoje)
                # Se já existe, atualizar com o novo peso (correção)
                peso_historico.peso = novo_peso
                peso_historico.observacoes = 'Atualização de perfil'
                peso_historico.save()
            except PesoHistorico.DoesNotExist:
                # Se não existe registro para hoje, criar um novo se a mudança for significativa
                if not individuo.peso or abs(float(individuo.peso) - novo_peso) > 0.01:  # tolerância de 0.01kg
                    PesoHistorico.objects.create(
                        individuo=individuo,
                        peso=novo_peso,
                        data_registro=hoje,
                        observacoes='Atualização de perfil'
                    )
        
        individuo.peso = novo_peso or None
        individuo.sexo = request.POST.get('sexo') or None
        individuo.observacoes = request.POST.get('observacoes') or ''
        individuo.cpf = request.POST.get('cpf') or None
        individuo.telefone = request.POST.get('telefone') or None
        individuo.endereco_rua = request.POST.get('endereco_rua') or ''
        individuo.endereco_numero = request.POST.get('endereco_numero') or ''
        individuo.endereco_complemento = request.POST.get('endereco_complemento') or ''
        individuo.endereco_bairro = request.POST.get('endereco_bairro') or ''
        individuo.endereco_cidade = request.POST.get('endereco_cidade') or ''
        individuo.endereco_estado = request.POST.get('endereco_estado', '').upper() or ''
        individuo.endereco_cep = request.POST.get('endereco_cep') or ''
        individuo.endereco_pais = request.POST.get('endereco_pais') or 'Brasil'
        individuo.save()
        messages.success(request, 'Perfil atualizado com sucesso!')
        return redirect('perfil_view')
    
    # Cálculos para o template
    total_registros = RegistroTreinamento.objects.filter(individuo=individuo).count()
    media_geral = RegistroTreinamento.objects.filter(individuo=individuo).aggregate(
        Avg('valor_alcançado')
    )['valor_alcançado__avg'] or 0
    dias_consecutivos = calcular_dias_consecutivos(individuo)
    
    context = {
        'individuo': individuo,
        'total_registros': total_registros,
        'media_geral': media_geral,
        'dias_consecutivos': dias_consecutivos,
    }
    return render(request, 'treinamento/perfil.html', context)


@login_required
def calendar_view(request):
    """Página dedicada para visualização do calendário"""
    individuo = get_or_create_individuo(request.user)
    
    context = {
        'individuo': individuo,
    }
    return render(request, 'treinamento/calendar.html', context)


@login_required
def calendar_data_api(request):
    """API endpoint para retornar dados do calendário em formato JSON"""
    try:
        individuo = request.user.individuo
    except:
        return JsonResponse({'error': 'Perfil não encontrado'}, status=404)
    
    # Obter o mês e ano solicitados (padrão para o mês atual)
    try:
        month = int(request.GET.get('month', timezone.now().month))
        year = int(request.GET.get('year', timezone.now().year))
    except ValueError:
        month = timezone.now().month
        year = timezone.now().year
    
    # Filtrar registros pelo mês e ano especificados
    registros = RegistroTreinamento.objects.filter(
        individuo=individuo,
        data__year=year,
        data__month=month
    ).select_related('treinamento').order_by('data')
    
    # Organizar registros por data
    registros_por_data = {}
    for registro in registros:
        data_str = registro.data.strftime('%Y-%m-%d')
        if data_str not in registros_por_data:
            registros_por_data[data_str] = []
        registros_por_data[data_str].append({
            'treinamento': registro.treinamento.nome,
            'valor': float(registro.valor_alcançado),
            'unidade': registro.treinamento.get_unidade_medida_display(),
            'observacoes': registro.observacoes
        })
    
    # Preparar dados para resposta
    response_data = {
        'month': month,
        'year': year,
        'registros': registros_por_data
    }
    
    return JsonResponse(response_data)
