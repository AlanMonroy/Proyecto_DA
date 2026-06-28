from django.urls import path
from . import views

urlpatterns = [
    path('',       views.home,       name='home'),
    path('admin/', views.home_admin, name='home-admin'),
    path('user/',  views.home_user,  name='home-user'),
    path('proyectos_by_user/',  views.proyectos_by_user,  name='proyectos_by_user'),
]