# Crear este archivo en: <tu_app>/templatetags/reporte_tags.py
# (puede ir en cualquier app, por ejemplo home/templatetags/reporte_tags.py)
# Asegúrate de que la app tenga un archivo __init__.py en templatetags/

from django import template
from django.utils import timezone

register = template.Library()

@register.filter(name='get_attr')
def get_attr(obj, attr):
    try:
        valor = getattr(obj, attr, None)

        if valor is not None:
            return valor
        return obj.__dict__.get(attr, '—')
    except Exception as e:
        print(f"get_attr error: {e}")
        return '—'

@register.filter(name='get_attr_safe')
def get_attr_safe(obj, attr):
    if obj is None:
        return None
    try:
        valor = getattr(obj, attr, None)
        return valor
    except Exception:
        return None

@register.filter
def pluralize(value, suffix='s'):
    """Simple pluralize en español."""
    try:
        return '' if int(value) == 1 else suffix
    except (ValueError, TypeError):
        return ''

@register.filter(name='get_color')
def get_color(fila, col):
    try:
        campo_color = col.get('campo_color', '')
        objeto = getattr(fila, col.get('campo', ''), None)
        if objeto is None:
            return ''
        return getattr(objeto, campo_color, '')
    except Exception:
        return ''

@register.filter(name='get_pk')
def get_pk(obj):
    try:
        return str(obj.pk)
    except Exception:
        return str(obj)

@register.filter(name='get_dict')
def get_dict(diccionario, clave):
    try:
        return diccionario.get(clave, '')
    except Exception:
        return ''