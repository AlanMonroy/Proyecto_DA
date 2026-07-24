# Crear este archivo en: <tu_app>/templatetags/reporte_tags.py
# (puede ir en cualquier app, por ejemplo home/templatetags/reporte_tags.py)
# Asegúrate de que la app tenga un archivo __init__.py en templatetags/

from django import template

register = template.Library()

@register.filter(name='get_attr')
def get_attr(obj, attr):
    try:
        valor = getattr(obj, attr, None)
        #print(f"get_attr: obj={obj}, attr={attr}, valor={valor}, dict={obj.__dict__.get(attr)}")
        if attr in ('unidad_costo_unitario', 'unidad_total'):
            print(f"get_attr {attr}: valor={valor}, type={type(valor)}")
        if valor is not None:
            return valor
        return obj.__dict__.get(attr, '—')
    except Exception as e:
        print(f"get_attr error: {e}")
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