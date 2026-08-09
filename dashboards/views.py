from django.shortcuts import render, redirect
from reportes.models import Proyectos, ProyectosActividades
from django.db.models import Sum
from users.decorators import login_requerido
from django.utils import timezone

@login_requerido
def proyectos(request):
    if request.session.get('usuario_rol') != 0:
        return redirect('home-user')

    empresa_id = request.session.get('usuario_empresa_id')
    proyectos = Proyectos.objects.filter(empresa_id = empresa_id).all()

    #CALCULO DE HORAS
    hoy = timezone.now().date()
    registros = []

    for proyecto in proyectos:
        # Horas acumuladas del empleado en este proyecto
        horas = ProyectosActividades.objects.filter(
            proyecto_id=proyecto.pk,
            proyecto__empresa_id = empresa_id
        ).aggregate(total=Sum('horas'))['total'] or 0

        # Días faltantes
        if proyecto.fecha_fin:
            dias_faltantes = (proyecto.fecha_fin - hoy).days
        else:
            dias_faltantes = None

        registros.append({
            'proyecto':       proyecto,
            'horas':          horas,
            'dias_faltantes': dias_faltantes,
        })

    #-------------ORDENAR DATOS PARA EL CHART-------------#
    actividades = ProyectosActividades.objects.filter(proyecto__empresa_id = empresa_id).values(
        'proyecto_id',
        'proyecto__nombre',
        'empleado_id',
        'empleado__username'
    ).annotate(
        total_horas=Sum('horas')
    ).order_by(
        'proyecto_id',
        'empleado_id'
    )

    proyectos_ids = []
    proyectos_nombres = []
    empleados = {}

    for actividad in actividades:

        proyecto_id = actividad['proyecto_id']
        proyecto_nombre = actividad['proyecto__nombre']

        empleado_id = actividad['empleado_id']
        empleado_nombre = actividad['empleado__username']

        if proyecto_id not in proyectos_ids:
            proyectos_ids.append(proyecto_id)
            proyectos_nombres.append(proyecto_nombre)

        if empleado_id not in empleados:
            empleados[empleado_id] = {
                'name': empleado_nombre,
                'data': {}
            }

        empleados[empleado_id]['data'][proyecto_id] = float(
            actividad['total_horas'] or 0
        )

    series = []
    for empleado in empleados.values():

        data = []

        for proyecto_id in proyectos_ids:
            data.append(
                empleado['data'].get(proyecto_id, 0)
            )

        series.append({
            'name': empleado['name'],
            'data': data
        })
    #---------------------------------------#
    context = {
        'registros':          registros,
        'reporte_breadcrumb': 'Inicio / Proyectos',
        'chart_series': series,
        'chart_categories': proyectos_nombres,
    }

    return render(request, 'dashboards/proyectos.html', context)