"""
Utility functions for treinamento views.
"""
from datetime import timedelta
from django.utils import timezone


def is_admin_user(user):
    """Verifica se o usuário é administrador"""
    return user.is_staff or user.is_superuser


def calcular_dias_consecutivos(individuo):
    """Calcula dias consecutivos de treinamento"""
    from .models import RegistroTreinamento
    
    registros = RegistroTreinamento.objects.filter(
        individuo=individuo
    ).order_by('-data')
    
    if not registros.exists():
        return 0
    
    dias_consecutivos = 0
    data_atual = timezone.now().date()
    
    # Converter registros em uma lista de datas únicas
    datas_registros = sorted(set([registro.data for registro in registros]), reverse=True)
    
    if not datas_registros:
        return 0
    
    # Verificar se o registro mais recente é de hoje ou ontem
    if datas_registros[0] == data_atual:
        dias_consecutivos = 1
    elif datas_registros[0] == data_atual - timedelta(days=1):
        dias_consecutivos = 1
    else:
        return 0
    
    # Contar dias consecutivos
    for i in range(1, len(datas_registros)):
        data_atual_registro = datas_registros[i]
        data_anterior = datas_registros[i-1]
        
        # Verificar se há um dia de diferença entre os registros
        if (data_anterior - data_atual_registro).days == 1:
            dias_consecutivos += 1
        else:
            break
    
    return dias_consecutivos


def get_or_create_individuo(user):
    """Obtém ou cria um perfil de Indivíduo para o usuário"""
    from .models import Individuo
    
    try:
        return user.individuo
    except Individuo.DoesNotExist:
        return Individuo.objects.create(
            user=user,
            nome_completo=user.username
        )
