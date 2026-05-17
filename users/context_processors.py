from .models import MenuOpcion

def menu_usuario(request):
    rol_id = request.session.get('usuario_rol')
    if rol_id is None:
        return {'menu_opciones': []}

    opciones = MenuOpcion.objects.filter(rol_id=rol_id)
    return {'menu_opciones': opciones}