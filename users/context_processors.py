from .models import MenuOpcion
from django.urls import reverse, NoReverseMatch

def menu_usuario(request):
    rol_id = request.session.get('usuario_rol')
    if rol_id is None:
        return {'menu_opciones': []}

    opciones_raw = MenuOpcion.objects.filter(rol_id=rol_id)
    opciones_validas = []

    for opcion in opciones_raw:
        try:
            reverse(opcion.url_name)  # verifica si la URL existe
            opciones_validas.append(opcion)
        except NoReverseMatch:
            pass  # ignora opciones con URLs inválidas

    return {'menu_opciones': opciones_validas}