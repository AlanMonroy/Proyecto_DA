from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('usuarios/', views.reporte_usuarios, name='reporte_usuarios'),
    path('refacciones/', views.reporte_refacciones, name='reporte_refacciones'),
    path('proyectos/', views.reporte_proyectos, name='reporte_proyectos'),
]