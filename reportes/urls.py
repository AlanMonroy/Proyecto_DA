from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('usuarios/', views.reporte_usuarios, name='reporte_usuarios'),
    path('usuarios/crear/', views.create_user,   name='create_user'),
    path('usuarios/<int:pk>/editar/', views.edit_user, name='edit_user'),
    path('refacciones/', views.reporte_refacciones, name='reporte_refacciones'),
    path('proyectos/', views.reporte_proyectos, name='reporte_proyectos'),
    path('proyectos/crear/', views.proyecto_crear,   name='proyecto_crear'),
    path('proyectos/<int:pk>/editar/', views.proyecto_editar, name='proyecto_editar'),
    path('clientes/', views.reporte_clientes, name='reporte_clientes'),
    #path('proyectos/<int:pk>/eliminar/', views.proyecto_eliminar, name='proyecto_eliminar'),
]