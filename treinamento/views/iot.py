"""
Views para IoT - Gerenciamento de dispositivos e ingestão de dados
"""
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.db.models import Count, Avg, Max, Q
from django.utils import timezone
from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from datetime import timedelta
import json
import logging

from ..models import Individuo
from ..iot_models import DispositivoIoT, LeituraIoT, ConfiguracaoDispositivo, AlertaIoT
from ..services.iot_processor import IoTDataProcessor
from ..services.alert_manager import AlertManager
from ..forms import DispositivoIoTForm, ConfiguracaoDispositivoForm

logger = logging.getLogger(__name__)


# ============= Device Management Views =============

@login_required
def iot_dashboard(request):
    """
    Dashboard principal de IoT mostrando dispositivos, leituras recentes e alertas
    """
    try:
        individuo = request.user.individuo
    except Individuo.DoesNotExist:
        messages.error(request, "Você precisa completar seu perfil primeiro.")
        return redirect('perfil')
    
    # Estatísticas de dispositivos
    dispositivos = DispositivoIoT.objects.filter(proprietario=individuo)
    total_dispositivos = dispositivos.count()
    dispositivos_online = sum(1 for d in dispositivos if d.esta_online())
    dispositivos_offline = total_dispositivos - dispositivos_online
    
    # Adiciona estatísticas para cada dispositivo
    for dispositivo in dispositivos:
        dispositivo.total_leituras = dispositivo.leituras.count()
        dispositivo.leituras_hoje = dispositivo.leituras.filter(
            timestamp__date=timezone.now().date()
        ).count()
        dispositivo.alertas_ativos = dispositivo.alertas.filter(resolvido=False).count()
    
    # Alertas ativos
    alertas_ativos = AlertManager.get_active_alerts_for_user(individuo, limit=5)
    alertas_criticos = AlertManager.get_critical_alerts_count(individuo)
    
    # Leituras recentes (últimos 7 dias para mostrar mais dados)
    last_7_days = timezone.now() - timedelta(days=7)
    leituras_recentes = LeituraIoT.objects.filter(
        dispositivo__proprietario=individuo,
        timestamp__gte=last_7_days
    ).order_by('-timestamp')[:50]  # Aumentado para 50 leituras
    
    # Dados para gráfico (leituras por hora nas últimas 168h - 7 dias)
    leituras_por_hora = []
    for i in range(168):  # 7 dias * 24 horas
        hora_inicio = timezone.now() - timedelta(hours=i+1)
        hora_fim = timezone.now() - timedelta(hours=i)
        count = LeituraIoT.objects.filter(
            dispositivo__proprietario=individuo,
            timestamp__gte=hora_inicio,
            timestamp__lt=hora_fim
        ).count()
        leituras_por_hora.append({
            'hora': hora_inicio.strftime('%d/%m %H:00'),
            'count': count
        })
    leituras_por_hora.reverse()
    
    context = {
        'dispositivos': dispositivos,
        'total_dispositivos': total_dispositivos,
        'dispositivos_online': dispositivos_online,
        'dispositivos_offline': dispositivos_offline,
        'alertas_ativos': alertas_ativos,
        'alertas_criticos': alertas_criticos,
        'leituras_recentes': leituras_recentes,
        'leituras_por_hora': json.dumps(leituras_por_hora),
    }
    
    return render(request, 'treinamento/iot/dashboard.html', context)


@login_required
def device_list(request):
    """
    Lista todos os dispositivos do usuário
    """
    try:
        individuo = request.user.individuo
    except Individuo.DoesNotExist:
        messages.error(request, "Você precisa completar seu perfil primeiro.")
        return redirect('perfil')
    
    dispositivos = DispositivoIoT.objects.filter(proprietario=individuo).order_by('-ultimo_ping')
    
    # Adiciona estatísticas para cada dispositivo
    for dispositivo in dispositivos:
        dispositivo.total_leituras = dispositivo.leituras.count()
        dispositivo.leituras_hoje = dispositivo.leituras.filter(
            timestamp__date=timezone.now().date()
        ).count()
        dispositivo.alertas_ativos = dispositivo.alertas.filter(resolvido=False).count()
    
    context = {
        'dispositivos': dispositivos,
    }
    
    return render(request, 'treinamento/iot/device_list.html', context)


@login_required
def device_detail(request, device_id):
    """
    Detalhes de um dispositivo específico
    """
    try:
        individuo = request.user.individuo
    except Individuo.DoesNotExist:
        messages.error(request, "Você precisa completar seu perfil primeiro.")
        return redirect('perfil')
    
    dispositivo = get_object_or_404(DispositivoIoT, id=device_id, proprietario=individuo)
    
    # Leituras com paginação
    leituras_list = dispositivo.leituras.order_by('-timestamp')
    paginator = Paginator(leituras_list, 12)  # 12 leituras por página
    
    page_number = request.GET.get('page')
    try:
        leituras = paginator.page(page_number)
    except PageNotAnInteger:
        leituras = paginator.page(1)
    except EmptyPage:
        leituras = paginator.page(paginator.num_pages)
    
    # Estatísticas
    total_leituras = dispositivo.leituras.count()
    leituras_processadas = dispositivo.leituras.filter(processado=True).count()
    
    # Alertas
    alertas = dispositivo.alertas.order_by('-criado_em')[:10]
    alertas_ativos = dispositivo.alertas.filter(resolvido=False).count()
    
    # Configuração
    try:
        config = dispositivo.configuracao
    except ConfiguracaoDispositivo.DoesNotExist:
        config = None
    
    # Preparar dados JSON para o gráfico (últimas 50 leituras)
    leituras_chart = dispositivo.leituras.order_by('-timestamp')[:50]
    leituras_json = json.dumps([
        {
            'timestamp': leitura.timestamp.strftime('%H:%M'),
            'valor': float(leitura.valor)
        }
        for leitura in reversed(leituras_chart)
    ])
    
    # Preparar dados para mapa se for dispositivo GPS
    coordenadas_mapa = []
    if dispositivo.tipo == 'gps':
        # Pegar todas as leituras com coordenadas e ordenar por timestamp
        leituras_gps = dispositivo.leituras.filter(
            metadata__isnull=False
        ).exclude(
            metadata__latitude__isnull=True,
            metadata__longitude__isnull=True
        ).order_by('timestamp')
        
        coordenadas_mapa = [
            {
                'lat': leitura.metadata['latitude'],
                'lng': leitura.metadata['longitude'],
                'timestamp': leitura.timestamp.isoformat(),
                'distancia': float(leitura.valor),
                'speed': leitura.metadata.get('speed', 0),
                'altitude': leitura.metadata.get('altitude', 0),
            }
            for leitura in leituras_gps
            if leitura.metadata and isinstance(leitura.metadata, dict)
            and 'latitude' in leitura.metadata and 'longitude' in leitura.metadata
        ]
    
    context = {
        'dispositivo': dispositivo,
        'leituras': leituras,
        'total_leituras': total_leituras,
        'leituras_processadas': leituras_processadas,
        'alertas': alertas,
        'alertas_ativos': alertas_ativos,
        'config': config,
        'leituras_json': leituras_json,
        'coordenadas_mapa': coordenadas_mapa,
    }
    
    return render(request, 'treinamento/iot/device_detail.html', context)


@login_required
def device_create(request):
    """
    Cria um novo dispositivo IoT
    """
    try:
        individuo = request.user.individuo
    except Individuo.DoesNotExist:
        messages.error(request, "Você precisa completar seu perfil primeiro.")
        return redirect('perfil')
    
    if request.method == 'POST':
        form = DispositivoIoTForm(request.POST, individuo=individuo)
        if form.is_valid():
            dispositivo = form.save(commit=False)
            dispositivo.proprietario = individuo
            dispositivo.save()
            
            # Cria configuração padrão
            config_form = ConfiguracaoDispositivoForm(request.POST)
            if config_form.is_valid():
                configuracao = config_form.save(commit=False)
                configuracao.dispositivo = dispositivo
                configuracao.save()
            
            messages.success(request, f"Dispositivo '{dispositivo.nome}' criado com sucesso!")
            return redirect('iot_dashboard')
    else:
        form = DispositivoIoTForm(individuo=individuo)
        config_form = ConfiguracaoDispositivoForm()
    
    context = {
        'form': form,
        'config_form': config_form,
        'editing': False,
    }
    
    return render(request, 'treinamento/iot/device_create.html', context)

@login_required
def device_edit(request, device_id):
    """
    Edita um dispositivo IoT existente
    """
    try:
        individuo = request.user.individuo
    except Individuo.DoesNotExist:
        messages.error(request, "Você precisa completar seu perfil primeiro.")
        return redirect('perfil')
    
    dispositivo = get_object_or_404(DispositivoIoT, id=device_id, proprietario=individuo)
    
    try:
        configuracao = dispositivo.configuracao
    except ConfiguracaoDispositivo.DoesNotExist:
        configuracao = None
    
    if request.method == 'POST':
        form = DispositivoIoTForm(request.POST, instance=dispositivo, individuo=individuo)
        if configuracao:
            config_form = ConfiguracaoDispositivoForm(request.POST, instance=configuracao)
        else:
            config_form = ConfiguracaoDispositivoForm(request.POST)
        
        if form.is_valid() and config_form.is_valid():
            dispositivo = form.save()
            
            if configuracao:
                configuracao = config_form.save()
            else:
                configuracao = config_form.save(commit=False)
                configuracao.dispositivo = dispositivo
                configuracao.save()
            
            messages.success(request, f"Dispositivo '{dispositivo.nome}' atualizado com sucesso!")
            return redirect('device_detail', device_id=device_id)
    else:
        form = DispositivoIoTForm(instance=dispositivo, individuo=individuo)
        if configuracao:
            config_form = ConfiguracaoDispositivoForm(instance=configuracao)
        else:
            config_form = ConfiguracaoDispositivoForm()
    
    context = {
        'form': form,
        'config_form': config_form,
        'dispositivo': dispositivo,
        'editing': True,
    }
    
    return render(request, 'treinamento/iot/device_create.html', context)

@login_required
@require_http_methods(["POST"])
def device_delete(request, device_id):
    """
    Deleta um dispositivo
    """
    try:
        individuo = request.user.individuo
    except Individuo.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Perfil não encontrado'}, status=400)
    
    dispositivo = get_object_or_404(DispositivoIoT, id=device_id, proprietario=individuo)
    device_name = dispositivo.nome
    
    dispositivo.delete()
    
    messages.success(request, f"Dispositivo '{device_name}' removido com sucesso.")
    return redirect('device_list')


# ============= Alert Management Views =============

@login_required
def alert_list(request):
    """
    Lista todos os alertas do usuário
    """
    try:
        individuo = request.user.individuo
    except Individuo.DoesNotExist:
        messages.error(request, "Você precisa completar seu perfil primeiro.")
        return redirect('perfil')
    
    # Filtros
    show_resolved = request.GET.get('show_resolved', 'false') == 'true'
    severity_filter = request.GET.get('severity')
    
    alertas = AlertaIoT.objects.filter(individuo=individuo)
    
    if not show_resolved:
        alertas = alertas.filter(resolvido=False)
    
    if severity_filter:
        alertas = alertas.filter(severidade=severity_filter)
    
    alertas = alertas.order_by('-criado_em')
    
    context = {
        'alertas': alertas,
        'show_resolved': show_resolved,
        'severity_filter': severity_filter,
    }
    
    return render(request, 'treinamento/iot/alert_list.html', context)


@login_required
@require_http_methods(["POST"])
def alert_mark_viewed(request, alert_id):
    """
    Marca alerta como visualizado
    """
    try:
        individuo = request.user.individuo
    except Individuo.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Perfil não encontrado'}, status=400)
    
    alerta = get_object_or_404(AlertaIoT, id=alert_id, individuo=individuo)
    
    success = AlertManager.mark_as_viewed(alert_id)
    
    return JsonResponse({'success': success})


@login_required
@require_http_methods(["POST"])
def alert_mark_resolved(request, alert_id):
    """
    Marca alerta como resolvido
    """
    try:
        individuo = request.user.individuo
    except Individuo.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Perfil não encontrado'}, status=400)
    
    alerta = get_object_or_404(AlertaIoT, id=alert_id, individuo=individuo)
    
    success = AlertManager.mark_as_resolved(alert_id)
    
    return JsonResponse({'success': success})


# ============= Data Ingestion API =============

@csrf_exempt
@require_http_methods(["POST"])
def iot_data_ingest(request):
    """
    Endpoint para receber dados de dispositivos IoT
    
    Formato esperado:
    {
        "device_id": "ESP32_001",
        "api_key": "opcional_para_autenticacao",
        "readings": [
            {
                "tipo": "heartrate",
                "valor": 150,
                "timestamp": "2026-01-23T20:00:00Z",
                "unidade": "bpm",
                "qualidade_sinal": "good",
                "nivel_bateria": 85,
                "metadata": {}
            }
        ]
    }
    
    Retorna:
    {
        "success": true,
        "processed": 5,
        "errors": [],
        "alerts": [...]
    }
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Invalid JSON'
        }, status=400)
    
    # Valida campos obrigatórios
    device_id = data.get('device_id')
    if not device_id:
        return JsonResponse({
            'success': False,
            'error': 'device_id is required'
        }, status=400)
    
    readings = data.get('readings', [])
    if not readings:
        return JsonResponse({
            'success': False,
            'error': 'No readings provided'
        }, status=400)
    
    # Busca o dispositivo
    try:
        dispositivo = DispositivoIoT.objects.get(device_id=device_id)
    except DispositivoIoT.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': f'Device {device_id} not found'
        }, status=404)
    
    # Verifica se dispositivo está ativo
    if dispositivo.status == 'inactive':
        return JsonResponse({
            'success': False,
            'error': 'Device is inactive'
        }, status=403)
    
    # TODO: Validar API key se fornecida
    # api_key = data.get('api_key')
    
    # Processa as leituras
    individuo = dispositivo.proprietario
    leituras_criadas, erros = IoTDataProcessor.process_batch_readings(
        dispositivo, 
        readings, 
        individuo
    )
    
    # Busca alertas criados para este dispositivo nas últimas 2 leituras
    alertas_recentes = AlertaIoT.objects.filter(
        dispositivo=dispositivo,
        criado_em__gte=timezone.now() - timedelta(seconds=10)
    ).values('tipo', 'severidade', 'mensagem')
    
    # Resolve alertas de offline se dispositivo estava offline
    if not dispositivo.esta_online():
        AlertManager.resolve_offline_alerts_for_device(dispositivo)
    
    response_data = {
        'success': True,
        'processed': len(leituras_criadas),
        'errors': erros,
        'alerts': list(alertas_recentes),
        'device_status': dispositivo.status,
        'online': dispositivo.esta_online()
    }
    
    logger.info(f"Dados recebidos do dispositivo {device_id}: {len(leituras_criadas)} leituras processadas")
    
    return JsonResponse(response_data)


@csrf_exempt
@require_http_methods(["GET"])
def iot_device_status(request, device_id):
    """
    Endpoint para verificar status do dispositivo
    """
    try:
        dispositivo = DispositivoIoT.objects.get(device_id=device_id)
    except DispositivoIoT.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Device not found'
        }, status=404)
    
    # Configuração
    try:
        config = dispositivo.configuracao
        config_data = {
            'intervalo_leitura': config.intervalo_leitura,
            'criar_registro_automatico': config.criar_registro_automatico,
            'valor_minimo_alerta': float(config.valor_minimo_alerta) if config.valor_minimo_alerta else None,
            'valor_maximo_alerta': float(config.valor_maximo_alerta) if config.valor_maximo_alerta else None,
        }
    except ConfiguracaoDispositivo.DoesNotExist:
        config_data = None
    
    return JsonResponse({
        'success': True,
        'device_id': dispositivo.device_id,
        'nome': dispositivo.nome,
        'tipo': dispositivo.tipo,
        'status': dispositivo.status,
        'online': dispositivo.esta_online(),
        'ultimo_ping': dispositivo.ultimo_ping.isoformat() if dispositivo.ultimo_ping else None,
        'config': config_data
    })


@login_required
def toggle_device_offline(request, device_id):
    """Alterna o status offline/online de um dispositivo"""
    dispositivo = get_object_or_404(DispositivoIoT, id=device_id, proprietario=request.user.individuo)
    
    if request.method == 'POST':
        # Alternar o status
        dispositivo.forcar_offline = not dispositivo.forcar_offline
        dispositivo.save()
        
        status_text = "offline" if dispositivo.forcar_offline else "online"
        messages.success(request, f'Dispositivo {dispositivo.nome} marcado como {status_text}.')
        
        # Se estiver fazendo requisição AJAX
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'forcar_offline': dispositivo.forcar_offline,
                'status_text': status_text,
                'online': dispositivo.esta_online()
            })
    
    return redirect('iot_dashboard')
