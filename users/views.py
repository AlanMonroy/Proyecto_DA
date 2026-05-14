from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages

from .forms import RegisterForm, LoginForm


def auth_page(request):
    """
    Vista principal que muestra el formulario de registro y login
    en la misma página. El tab activo se controla con `active_tab`.
    """
    register_form = RegisterForm()
    login_form    = LoginForm()
    active_tab    = 'login'

    if request.method == 'POST':
        form_type = request.POST.get('form_type')

        # ── Registro ──────────────────────────────────────────────
        if form_type == 'register':
            active_tab    = 'register'
            register_form = RegisterForm(request.POST)

            if register_form.is_valid():
                user = register_form.save(commit=False)
                user.email      = register_form.cleaned_data['email']
                user.first_name = register_form.cleaned_data['first_name']
                user.last_name  = register_form.cleaned_data['last_name']
                user.save()

                login(request, user)
                messages.success(request, f'¡Bienvenido, {user.first_name}!')
                return redirect('dashboard')     # cambia a tu URL destino
            else:
                messages.error(request, 'Por favor corrige los errores del formulario.')

        # ── Login ─────────────────────────────────────────────────
        elif form_type == 'login':
            active_tab = 'login'
            login_form = LoginForm(request=request, data=request.POST)

            if login_form.is_valid():
                user = login_form.get_user()
                login(request, user)

                # Mantener sesión si "recordarme" está marcado
                if not request.POST.get('remember_me'):
                    request.session.set_expiry(0)   # sesión de navegador

                messages.success(request, f'¡Hola de nuevo, {user.first_name or user.username}!')
                return redirect(request.GET.get('next', 'dashboard'))
            else:
                messages.error(request, 'Usuario o contraseña incorrectos.')

    context = {
        'register_form': register_form,
        'login_form':    login_form,
        'active_tab':    active_tab,
    }
    return render(request, 'users/login.html', context)


def users(request):
    """Alias para compatibilidad — redirige a auth_page."""
    return auth_page(request)


@login_required
def logout_view(request):
    """Cierra sesión y redirige al formulario de acceso."""
    if request.method == 'POST':
        logout(request)
        messages.info(request, 'Sesión cerrada correctamente.')
    return redirect('users:auth_page')