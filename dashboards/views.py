from django.shortcuts import render, redirect
from reportes.models import Proyectos, ProyectosActividades
from django.db.models import Sum
from users.decorators import login_requerido
from django.utils import timezone

@login_requerido
def proyectos(request):
    if request.session.get('usuario_rol') != 0:
        return redirect('home-user')

    proyectos = Proyectos.objects.all()

    hoy = timezone.now().date()
    registros = []

    for a in proyectos:
        proyecto = a.proyecto_id

        # Horas acumuladas del empleado en este proyecto
        horas = ProyectosActividades.objects.filter(
            proyecto_id=proyecto.pk,
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

    context = {
        'registros':          registros,
        'reporte_breadcrumb': 'Inicio / Proyectos',
    }

    return render(request, 'dashboard/proyectos.html', context)