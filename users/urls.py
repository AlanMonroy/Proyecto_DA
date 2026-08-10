from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

app_name = 'users'

urlpatterns = [
    path('',          views.auth_page,       name='auth_page'),
    path('login/',    views.auth_page,       name='login'),
    path('register/', views.auth_page,       name='register'),
    path('logout/',   views.logout_view, name='logout'),
    path('cambiar-password/', views.cambiar_password, name='cambiar_password'),
    path('password-reset/',
        auth_views.PasswordResetView.as_view(
            template_name='users/password_reset.html',
        ),
        name='password_reset',
    ),
    path('password-reset/sent/',
        auth_views.PasswordResetDoneView.as_view(
            template_name='users/password_reset_done.html',
        ),
        name='password_reset_done',
    ),
    path('password-reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(
            template_name='users/password_reset_confirm.html',
        ),
        name='password_reset_confirm',
    ),
    path('password-reset/complete/',
        auth_views.PasswordResetCompleteView.as_view(
            template_name='users/password_reset_complete.html',
        ),
        name='password_reset_complete',
    ),
]