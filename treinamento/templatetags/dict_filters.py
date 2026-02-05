from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """
    Retorna o valor de um dicionário para uma chave fornecida.
    Uso no template: {{ dicionario|get_item:chave }}
    """
    return dictionary.get(key, {})
