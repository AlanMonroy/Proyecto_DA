# Crear este archivo en: <tu_app>/templatetags/reporte_tags.py
# (puede ir en cualquier app, por ejemplo home/templatetags/reporte_tags.py)
# Asegúrate de que la app tenga un archivo __init__.py en templatetags/

from django import template

register = template.Library()

@register.filter
def getattr(obj, attr):
    """Permite acceder a atributos dinámicos en templates: {{ obj|getattr:campo }}"""
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