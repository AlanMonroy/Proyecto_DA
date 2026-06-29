from django.shortcuts import render, redirect
from users.decorators import login_requerido
from reportes.models import ProyectoAsignacion, ProyectosActividades
from django.db.models import Sum
from django.utils import timezone

@login_requerido
def home(request):
    return render(request, 'home/home.html')

@login_requerido
def home_admin(request):
    # Solo rol 0 puede entrar aquí
    if request.session.get('usuario_rol') != 0:
        return redirect('home-user')
    return render(request, 'home/home_admin.html')

@login_requerido
def home_user(request):
    # Solo rol 1 puede entrar aquí
    if request.session.get('usuario_rol') != 1:
        return redirect('home-admin')
    return render(request, 'home/home_admin.html')

@login_requerido
def proyectos_by_user(request):
    if request.session.get('usuario_rol') != 1:
        return redirect('home-admin')

    usuario_id = request.session.get('usuario_id')

    asignaciones = ProyectoAsignacion.objects.filter(
        empleado_id=usuario_id
    ).select_related('proyecto', 'proyecto__estatus', 'proyecto__prioridad')

    hoy = timezone.now().date()
    registros = []

    for a in asignaciones:
        proyecto = a.proyecto

        # Horas acumuladas del empleado en este proyecto
        horas = ProyectosActividades.objects.filter(
            proyecto_id=proyecto.pk,
            empleado_id=usuario_id
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
        'reporte_breadcrumb': 'Inicio / Proyectos Asignados',
    }

    return render(request, 'home/proyectos_by_user.html', context)