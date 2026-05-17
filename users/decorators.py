from functools import wraps
from django.shortcuts import redirect

def login_requerido(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.session.get('usuario_id'):
            return redirect('users:login')
        return view_func(request, *args, **kwargs)
    return wrapper