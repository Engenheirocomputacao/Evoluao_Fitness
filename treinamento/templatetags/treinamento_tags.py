from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def format_duration(value):
    """
    Formata um objeto timedelta como HH:MM
    """
    if isinstance(value, timedelta):
        total_seconds = int(value.total_seconds())
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        return f"{hours:02d}:{minutes:02d}"
    
    # Se já for uma string ou None, retorna como está
    if value is None:
        return ""
        
    return str(value)
