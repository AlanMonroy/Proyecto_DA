from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('usuarios/', views.reporte_usuarios, name='reporte_usuarios'),
    path('refacciones/', views.reporte_refacciones, name='reporte_refacciones'),
    path('proyectos/', views.reporte_proyectos, name='reporte_proyectos'),
    path('proyectos/crear/',         views.proyecto_crear,   name='proyecto_crear'),
    path('proyectos/<int:pk>/editar/', views.proyecto_editar, name='proyecto_editar'),
    #path('proyectos/<int:pk>/eliminar/', views.proyecto_eliminar, name='proyecto_eliminar'),
]