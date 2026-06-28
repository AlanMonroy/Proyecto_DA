from django.shortcuts import render, redirect
from users.decorators import login_requerido
@login_requerido
def home(request):
    return render(request, 'home/home.html')

@login_requerido
def home_admin(request):
    # Solo rol 0 puede entrar aquí
    if request.session.get('usuario_rol') != 0:
        return redirect('home-user')
    return render(request, 'home/home_admin.html')

@login_requerido
def home_user(request):
    # Solo rol 1 puede entrar aquí
    if request.session.get('usuario_rol') != 1:
        return redirect('home-admin')
    return render(request, 'home/home_admin.html')

@login_requerido
def proyectos_by_user(request):
    if request.session.get('usuario_rol') != 1:
        return redirect('home-user')
    return render(request, 'home/proyectos_by_user.html')