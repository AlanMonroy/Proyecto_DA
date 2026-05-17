from django.shortcuts import render, redirect
from django.contrib import messages

from .models import Usuario
from .forms import RegisterForm, LoginForm
from django.contrib.auth.hashers import check_password

def auth_page(request):
    register_form = RegisterForm()
    login_form = LoginForm()
    active_tab = 'login'

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        # ── Registro ──────────────────────────────────────────────
        if form_type == 'register':
            active_tab = 'register'
            register_form = RegisterForm(request.POST)

            if register_form.is_valid():
                usuario = register_form.save(commit=False)
                usuario.set_password(register_form.cleaned_data['password1'])
                usuario.save()
                messages.success(request, f'¡Bienvenido, {usuario.username}!')
                return redirect('home')  # cambia a tu URL destino
            else:
                messages.error(request, 'Por favor corrige los errores.')

        # ── Login ─────────────────────────────────────────────────
        elif form_type == 'login':
            active_tab = 'login'
            login_form = LoginForm(request.POST)

            if login_form.is_valid():
                username = login_form.cleaned_data['username']
                password = login_form.cleaned_data['password']

                try:
                    usuario = Usuario.objects.get(username=username)
                    if usuario.check_password(password):
                        # Guardamos el usuario en sesión manualmente
                        request.session['usuario_id'] = usuario.id
                        request.session['usuario_name'] = usuario.username
                        request.session['usuario_rol'] = usuario.rol_id
                        messages.success(request, f'¡Hola de nuevo, {usuario.username}!')
                        return redirect('home')  # cambia a tu URL destino
                    else:
                        messages.error(request, 'Usuario o contraseña incorrectos.')
                except Usuario.DoesNotExist:
                    messages.error(request, 'Usuario o contraseña incorrectos.')

    context = {
        'register_form': register_form,
        'login_form': login_form,
        'active_tab': active_tab,
    }
    return render(request, 'users/login.html', context)