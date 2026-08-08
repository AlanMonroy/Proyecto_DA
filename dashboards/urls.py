from django.urls import path
from . import views

app_name = 'dashboards'

urlpatterns = [
    path('proyectos/', views.proyectos, name='proyectos'),
]