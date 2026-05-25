# Crear este archivo en: <tu_app>/templatetags/reporte_tags.py
# (puede ir en cualquier app, por ejemplo home/templatetags/reporte_tags.py)
# Asegúrate de que la app tenga un archivo __init__.py en templatetags/

from django import template

register = template.Library()

@register.filter(name='get_attr')
def get_attr(obj, attr):
    try:
        return getattr(obj, attr, '—')
    except Exception:
        return '—'

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