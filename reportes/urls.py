from django.urls import path
from . import views

app_name = 'reportes'

urlpatterns = [
    path('proyectos-por-cliente/', views.proyectos_por_cliente, name='proyectos_por_cliente'), #SELECT CASCADE

    path('usuarios/', views.reporte_usuarios, name='reporte_usuarios'),
    path('usuarios/crear/', views.create_user,   name='create_user'),
    path('usuarios/<int:pk>/editar/', views.edit_user, name='edit_user'),
    path('refacciones/', views.reporte_refacciones, name='reporte_refacciones'),

    path('proyectos/', views.reporte_proyectos, name='reporte_proyectos'),
    path('proyectos/crear/', views.proyecto_crear,   name='proyecto_crear'),
    path('proyectos/<int:pk>/editar/', views.proyecto_editar, name='proyecto_editar'),
    path('proyectos/<int:pk>/eliminar/', views.proyecto_eliminar, name='proyecto_eliminar'),

    path('proyectos_actividades/<int:pk>/', views.reporte_proyectos_actividades, name='proyectos_actividades'),
    path('proyectos_actividades/crear/', views.proyectos_actividades_crear,   name='proyectos_actividades_crear'),
    path('proyectos_actividades/<int:pk>/editar/', views.proyectos_actividades_editar, name='proyectos_actividades_editar'),
    path('proyectos_actividades/<int:pk>/eliminar/', views.proyectos_actividades_eliminar, name='proyectos_actividades_eliminar'),

    path('clientes/', views.reporte_clientes, name='reporte_clientes'),
    path('clientes/crear/', views.create_cliente, name='create_cliente'),
    path('clientes/<int:pk>/editar/', views.edit_cliente, name='edit_cliente'),
    path('clientes/<int:pk>/eliminar/', views.delete_cliente, name='delete_cliente'),

    path('costos/', views.reporte_costos, name='reporte_costos'),
    path('costos/crear/', views.create_costo, name='create_costo'),
    path('costos/<int:pk>/editar/', views.edit_costo, name='edit_costo'),
    path('costos/<int:pk>/eliminar/', views.delete_costo, name='delete_costo'),

    path('productos/', views.reporte_productos, name='reporte_productos'),
    path('productos/crear/', views.create_producto, name='create_producto'),
    path('productos/<int:pk>/editar/', views.edit_producto, name='edit_producto'),
    path('productos/<int:pk>/eliminar/', views.delete_producto, name='delete_producto'),

    path('cotizaciones/', views.reporte_cotizaciones, name='reporte_cotizaciones'),
    path('cotizaciones/crear/', views.create_cotizacion, name='create_cotizacion'),
    path('cotizaciones/<int:pk>/editar/', views.edit_cotizacion, name='edit_cotizacion'),
    path('cotizaciones/<int:pk>/eliminar/', views.delete_cotizacion, name='delete_cotizacion'),
    path('cotizaciones/exportar/', views.exportar_cotizaciones, name='exportar_cotizaciones'),
    path('cotizaciones/<int:pk>/pdf/', views.pdf_cotizacion, name='pdf_cotizacion'),
    path('cotizaciones/formato_pdf/', views.edit_formato_pdf, name='edit_formato_pdf'),
]