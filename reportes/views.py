from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, F, ExpressionWrapper, DecimalField, Value
from django.db.models.functions import Abs, NullIf, Cast
from users.decorators import login_requerido
from .views_crud import form_crear, form_editar, form_eliminar, exportar_csv
from users.models import Usuario, Rol
from .models import Refacciones, Proyectos, ProyectoEstatus, ProyectoPrioridad, Cliente, ProyectoAsignacion, ProyectosActividades, Costos, Productos, Cotizaciones, CotizacionProductos, FormatoPdf
import time
from decimal import Decimal, ROUND_HALF_UP
from supabase import create_client
from django.conf import settings
from django.urls import reverse
import os
from django.http import JsonResponse
from itertools import chain
from django.utils import timezone

def proyectos_por_cliente(request):
    cliente_id = request.GET.get('cliente_id')
    proyectos  = Proyectos.objects.filter(
        cliente_id=cliente_id,
        activo=True
    ).order_by('nombre')

    data = [
        {'valor': str(p.pk), 'label': p.nombre}
        for p in proyectos
    ]
    return JsonResponse(data, safe=False)

#---------------ACTIVIDADES---------------#
@login_requerido
def reporte_proyectos_actividades(request, pk):

    q         = request.GET.get('q', '').strip()
    columna   = request.GET.get('columna', '')
    orden     = request.GET.get('orden', 'proyect_id')
    direccion = request.GET.get('dir', 'asc')
    per_page  = int(request.GET.get('per_page', 10))
    page      = request.GET.get('page', 1)

    usuario_id = request.session.get('usuario_id')
    usuario_rol = request.session.get('usuario_rol')

    qs = ProyectosActividades.objects.filter(proyecto_id=pk).all()
    qs = qs.order_by('-fecha_creacion')
    if usuario_rol != 0:
        qs = qs.filter(
            empleado_id=usuario_id
        )

    # Verificar si ya hay actividad hoy
    hoy = timezone.localdate()
    actividad_hoy = ProyectosActividades.objects.filter(
        proyecto_id=pk,
        empleado_id=usuario_id,
        fecha_creacion__date=hoy
    ).exists()

    if q:
        if columna == 'proyecto_id':
            qs = qs.filter(proyecto_id__icontains=q)
        elif columna == 'empleado_id':
            qs = qs.filter(empleado_id__icontains=q)
        else:
            qs = qs.filter(
                Q(proyecto_id__icontains=q) |
                Q(empleado_id__icontains=q)
            )

    campos_validos = ['proyectos_actividades_id', 'proyecto_id', 'empleado_id', 'fecha_creacion']
    if orden in campos_validos:
        orden_str = f'-{orden}' if direccion == 'desc' else orden
        qs = qs.order_by(orden_str)

    per_page_opciones = [10, 25, 50, 100]
    if per_page not in per_page_opciones:
        per_page = 10

    paginator = Paginator(qs, per_page)
    registros = paginator.get_page(page)

    columnas = [
        {'campo': 'proyectos_actividades_id', 'label': 'ID', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'actividad_realizada', 'label': 'Actividad Realizada', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'horas', 'label': 'Horas', 'tipo': 'numero', 'ordenable': True},
        {'campo': 'fecha_creacion', 'label': 'Fecha', 'tipo': 'datetime', 'ordenable': True},
    ]
    if usuario_rol == 0:
        columnas.insert(1, {
            'campo': 'empleado',
            'label': 'Empleado',
            'tipo': 'texto',
            'ordenable': True
        })

    columnas_filtrables = [
        {'campo': 'proyecto',      'label': 'Proyecto'},
        {'campo': 'empleado', 'label': 'Empleado'},
    ]

    context = {
        'registros':           registros,
        'total_registros':     paginator.count,
        'columnas':            columnas,
        'columnas_filtrables': columnas_filtrables,
        'per_page':            per_page,
        'per_page_opciones':   per_page_opciones,
        'reporte_titulo':      'Actividades de Proyecto',
        'reporte_subtitulo':   'Gestión actividades en el proyecto',
        'reporte_breadcrumb':  'Inicio / Actividades',
        'validaciones_crear': ['Ya registraste una actividad hoy, puedes editar o eliminar la creada hoy.'] if actividad_hoy else [],
        'puede_crear':         True,
        'puede_editar':        True,
        'puede_eliminar':      True,
        'puede_exportar':      True,
        'url_crear': reverse('reportes:proyectos_actividades_crear',args=[pk]),
        'url_editar_base': '/reportes/proyectos_actividades/',
        'url_eliminar_base': '/reportes/proyectos_actividades/',
        'btn_crear_texto':     'Nueva actividad',
    }

    return render(request, 'reportes/reporte_base.html', context)

def get_campos_actividades():
    return [
        {
            'nombre': 'actividad_realizada',
            'label': 'Actividad',
            'tipo': 'textarea',
            'requerido': True,
            'ancho': 'completo',
            'placeholder': 'Actividad realizada',
        },
        {
            'nombre': 'horas',
            'label': 'Horas',
            'tipo': 'number',
            'requerido': True,
            'ancho': 'medio',
            'placeholder': 'Horas realizadas',
        },
    ]

@login_requerido
def proyectos_actividades_crear(request, pk):
    return form_crear(
        request,
        model=ProyectosActividades,
        campos_def=get_campos_actividades(),
        form_titulo='Nueva Actividad',
        url_lista='reportes:proyectos_actividades',
        extra_context={
            'defaults': {
                'proyecto_id': pk,
                'empleado_id': request.session.get('usuario_id'),
            }
        }
    )

@login_requerido
def proyectos_actividades_editar(request, pk):
    campos = get_campos_actividades()

    return form_editar(
        request,
        model=ProyectosActividades,
        pk=pk,
        campos_def=campos,
        form_titulo='Editar Actividad',
        url_lista='reportes:proyectos_actividades',
    )

@login_requerido
def proyectos_actividades_eliminar(request, pk):
    return form_eliminar(request, ProyectosActividades, pk)


#---------------USUARIOS---------------#
@login_requerido
def reporte_usuarios(request):
    # ── Parámetros GET ────────────────────────────────────────────
    q          = request.GET.get('q', '').strip()
    columna    = request.GET.get('columna', '')
    orden      = request.GET.get('orden', 'user_id')
    direccion  = request.GET.get('dir', 'asc')
    per_page   = int(request.GET.get('per_page', 10))
    page       = request.GET.get('page', 1)

    # ── Queryset base ─────────────────────────────────────────────
    empresa_id = request.session.get('usuario_empresa_id')
    qs = Usuario.objects.select_related('rol').filter(empresa_id=empresa_id).all()

    # ── Filtro búsqueda ───────────────────────────────────────────
    if q:
        if columna == 'username':
            qs = qs.filter(username__icontains=q)
        elif columna == 'email':
            qs = qs.filter(email__icontains=q)
        else:
            # Búsqueda general en todas las columnas de texto
            qs = qs.filter(
                Q(username__icontains=q) |
                Q(email__icontains=q)
            )

    # ── Ordenamiento ──────────────────────────────────────────────
    campos_validos = ['user_id', 'username', 'email', 'rol_id']
    if orden in campos_validos:
        orden_str = f'-{orden}' if direccion == 'desc' else orden
        qs = qs.order_by(orden_str)

    # ── Paginación ────────────────────────────────────────────────
    per_page_opciones = [10, 25, 50, 100]
    if per_page not in per_page_opciones:
        per_page = 10

    paginator   = Paginator(qs, per_page)
    registros   = paginator.get_page(page)

    # ── Columnas de la tabla ──────────────────────────────────────
    # campo:    nombre del atributo en el modelo
    # label:    encabezado visible
    # tipo:     texto | badge | fecha | datetime | moneda | boolean
    # ordenable: True/False
    columnas = [
        {'campo': 'user_id',  'label': 'ID',       'tipo': 'texto',   'ordenable': True},
        {'campo': 'username', 'label': 'Usuario',   'tipo': 'texto',   'ordenable': True},
        {'campo': 'email',    'label': 'Correo',    'tipo': 'texto',   'ordenable': True},
        {'campo': 'rol_id',   'label': 'Rol',       'tipo': 'texto',   'ordenable': True},
    ]

    # ── Columnas filtrables (para el select del filtro) ───────────
    columnas_filtrables = [
        {'campo': 'username', 'label': 'Usuario'},
        {'campo': 'email',    'label': 'Correo'},
    ]

    context = {
        # Datos
        'registros':          registros,
        'total_registros':    paginator.count,
        'columnas':           columnas,
        'columnas_filtrables': columnas_filtrables,
        'per_page':           per_page,
        'per_page_opciones':  per_page_opciones,

        # Encabezado
        'reporte_titulo':     'Usuarios',
        'reporte_subtitulo':  'Gestión de usuarios del sistema',
        'reporte_breadcrumb': 'Inicio / Usuarios',

        # Permisos CRUD (controla qué botones se muestran)
        'puede_crear': request.session.get('usuario_rol') == 0,
        'puede_editar': request.session.get('usuario_rol') == 0,
        'puede_eliminar': request.session.get('usuario_rol') == 0,
        'puede_exportar': True,
        # URLs CRUD
        'url_crear': '/reportes/usuarios/crear/',
        'btn_crear_texto': 'Nuevo usuario',
    }

    return render(request, 'reportes/reporte_base.html', context)

def get_campos_usuario():
    return [
        {
            'nombre': 'username', #nombre en el modelos
            'label': 'Usuario',
            'tipo': 'text',
            'requerido': True,
            'ancho': 'completo',
            'placeholder': 'Nombre del usuario',
        },
        {
            'nombre': 'email',
            'label': 'Email',
            'tipo': 'text',
            'requerido': True,
            'ancho': 'completo',
            'placeholder': 'Correo electronico',
            'filas': 3,
        },
        {
            'nombre': 'password1',
            'label': 'Contraseña',
            'tipo': 'password',
            'requerido': True,
            'ancho': 'medio',
            'especial': True,
            'solo_crear': True,
            'placeholder': 'Mínimo 8 caracteres',
        },
        {
            'nombre': 'password2',
            'label': 'Confirmar contraseña',
            'tipo': 'password',
            'requerido': True,
            'ancho': 'medio',
            'especial': True,
            'solo_crear': True,
            'placeholder': 'Repite la contraseña',
        },
        {
            'nombre': 'rol',
            'label': 'Rol',
            'tipo': 'select',
            'campo_fk': 'rol',
            'requerido': True,
            'ancho': 'medio',
            'queryset': Rol.objects.order_by('rol_id'),
        },
    ]


@login_requerido
def create_user(request):
    print(f"CREATE USER - Method: {request.method}")
    return form_crear(
        request,
        model=Usuario,
        campos_def=get_campos_usuario(),
        form_titulo='Nuevo usuario',
        url_lista='reporte_usuarios',
    )

@login_requerido
def edit_user(request, pk):
    return form_editar(
        request,
        model=Usuario,
        pk=pk,
        campos_def=get_campos_usuario(),
        form_titulo='Editar usuario',
        url_lista='reporte_usuarios',
    )

@login_requerido
def delete_user(request, pk):
    return form_eliminar(request, Usuario, pk)

#-----------------------REFACCIONES-----------------------#
@login_requerido
def reporte_refacciones(request):

    q         = request.GET.get('q', '').strip()
    columna   = request.GET.get('columna', '')
    orden     = request.GET.get('orden', 'refaccion_id')
    direccion = request.GET.get('dir', 'asc')
    per_page  = int(request.GET.get('per_page', 10))
    page      = request.GET.get('page', 1)

    qs = Refacciones.objects.all()
    print(f"Primera refaccion: {qs.first().__dict__}")

    if q:
        if columna == 'nombre':
            qs = qs.filter(nombre__icontains=q)
        elif columna == 'descripcion':
            qs = qs.filter(descripcion__icontains=q)
        else:
            qs = qs.filter(
                Q(nombre__icontains=q) |
                Q(descripcion__icontains=q)
            )

    campos_validos = ['refaccion_id', 'nombre', 'descripcion', 'fecha']
    if orden in campos_validos:
        orden_str = f'-{orden}' if direccion == 'desc' else orden
        qs = qs.order_by(orden_str)

    per_page_opciones = [10, 25, 50, 100]
    if per_page not in per_page_opciones:
        per_page = 10

    paginator = Paginator(qs, per_page)
    registros = paginator.get_page(page)

    columnas = [
        {'campo': 'refaccion_id', 'label': 'ID', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'nombre', 'label': 'Nombre', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'descripcion', 'label': 'Descripción', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'fecha_creacion', 'label': 'Fecha', 'tipo': 'datetime', 'ordenable': True},
    ]

    columnas_filtrables = [
        {'campo': 'nombre',      'label': 'Nombre'},
        {'campo': 'descripcion', 'label': 'Descripción'},
    ]

    context = {
        'registros':           registros,
        'total_registros':     paginator.count,
        'columnas':            columnas,
        'columnas_filtrables': columnas_filtrables,
        'per_page':            per_page,
        'per_page_opciones':   per_page_opciones,
        'reporte_titulo':      'Refacciones',
        'reporte_subtitulo':   'Gestión de refacciones',
        'reporte_breadcrumb':  'Inicio / Refacciones',
        'puede_crear':         request.session.get('usuario_rol') == 0,
        'puede_editar':        False,
        'puede_eliminar':      False,
        'puede_exportar':      True,
        'url_crear':           '/reportes/refacciones/crear/',
        'btn_crear_texto':     'Nueva refacción',
    }

    return render(request, 'reportes/reporte_base.html', context)

@login_requerido
def reporte_proyectos(request):
    inicio = time.perf_counter()

    q         = request.GET.get('q', '').strip()
    columna   = request.GET.get('columna', '')
    orden     = request.GET.get('orden', 'proyecto_id')
    direccion = request.GET.get('dir', 'asc')
    per_page  = int(request.GET.get('per_page', 10))
    page      = request.GET.get('page', 1)

    qs = Proyectos.objects.select_related(
        'estatus', 'prioridad', 'cliente'
    ).annotate(
        total_costos=Sum('costos__costo'),
        utilidad=ExpressionWrapper(
            F('precio_venta') - Sum('costos__costo'),
            output_field=DecimalField()
        ),
        margen=ExpressionWrapper(
            ((F('precio_venta') - Sum('costos__costo')) / F('precio_venta')) * 100,
            output_field=DecimalField()
        )
    ).all()

    if q:
        if columna == 'nombre':
            qs = qs.filter(nombre__icontains=q)
        elif columna == 'descripcion':
            qs = qs.filter(descripcion__icontains=q)
        else:
            qs = qs.filter(
                Q(nombre__icontains=q) |
                Q(descripcion__icontains=q)
            )

    campos_validos = [
        'proyecto_id',
        'nombre',
        'estatus',
        'prioridad',
        'fecha_inicio',
        'fecha_fin',
        'fecha_creacion'
    ]

    if orden in campos_validos:
        orden_str = f'-{orden}' if direccion == 'desc' else orden
        qs = qs.order_by(orden_str)

    per_page_opciones = [10, 25, 50, 100]
    if per_page not in per_page_opciones:
        per_page = 10

    paginator = Paginator(qs, per_page)
    registros = paginator.get_page(page)

    columnas = [
        {'campo': 'proyecto_id', 'label': 'ID', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'nombre', 'label': 'Nombre', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'descripcion', 'label': 'Descripción', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'estatus', 'label': 'Estatus', 'tipo': 'color_badge', 'campo_color': 'color', 'ordenable': True},
        {'campo': 'prioridad', 'label': 'Prioridad', 'tipo': 'color_badge', 'campo_color': 'color', 'ordenable': True},
        {'campo': 'cliente', 'label': 'Cliente', 'tipo': 'fk', 'ordenable': True},
        {'campo': 'responsable_id', 'label': 'Responsable', 'tipo': 'fk', 'ordenable': True},
        {'campo': 'porcentaje_avance', 'label': 'Avance', 'tipo': 'porcentaje', 'ordenable': True},
        {'campo': 'precio_venta', 'label': 'Precio de venta', 'tipo': 'moneda', 'ordenable': True},
        {'campo': 'total_costos', 'label': 'Costos', 'tipo': 'moneda', 'ordenable': True},
        {'campo': 'utilidad', 'label': 'Utilidad', 'tipo': 'moneda', 'ordenable': True},
        {'campo': 'margen', 'label': 'Margen bruto', 'tipo': 'numero', 'ordenable': True},
        #{'campo': 'costo_real', 'label': 'Costo', 'tipo': 'moneda', 'ordenable': True},
        {'campo': 'tipo_proyecto', 'label': 'Tipo Proyecto', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'categoria', 'label': 'Categoria', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'activo', 'label': 'Activo', 'tipo': 'boolean', 'ordenable': True},
        {'campo': 'fecha_inicio', 'label': 'Fecha Inicio', 'tipo': 'date', 'ordenable': True},
        {'campo': 'fecha_fin', 'label': 'Fecha Fin', 'tipo': 'date', 'ordenable': True},
        {'campo': 'fecha_creacion', 'label': 'Creado', 'tipo': 'datetime', 'ordenable': True},
    ]

    columnas_filtrables = [
        {'campo': 'nombre',      'label': 'Nombre'},
        {'campo': 'descripcion', 'label': 'Descripción'},
    ]

    context = {
        'registros':           registros,
        'total_registros':     paginator.count,
        'columnas':            columnas,
        'columnas_filtrables': columnas_filtrables,
        'per_page':            per_page,
        'per_page_opciones':   per_page_opciones,
        'reporte_titulo':      'Proyectos',
        'reporte_subtitulo':   'Gestión de proyectos',
        'reporte_breadcrumb':  'Inicio / Proyectos',
        'puede_crear':         request.session.get('usuario_rol') == 0,
        'puede_editar':        request.session.get('usuario_rol') == 0,
        'puede_eliminar':      request.session.get('usuario_rol') == 0,
        'puede_exportar':      True,
        'url_crear':           '/reportes/proyectos/crear/',
        'btn_crear_texto':     'Nuevo Proyecto',
    }
    print(time.perf_counter() - inicio)
    return render(request, 'reportes/reporte_base.html', context)

def get_campos_proyecto(request):
    empresa_id = request.session.get('usuario_empresa_id')
    return [
        {
            'nombre': 'nombre',
            'label': 'Nombre',
            'tipo': 'text',
            'requerido': True,
            'ancho': 'completo',
            'placeholder': 'Nombre del proyecto',
        },
        {
            'nombre': 'descripcion',
            'label': 'Descripción',
            'tipo': 'textarea',
            'requerido': False,
            'ancho': 'completo',
            'placeholder': 'Descripción del proyecto',
            'filas': 3,
        },
        {
            'nombre': 'cliente',
            'label': 'Cliente',
            'tipo': 'select',
            'campo_fk': 'cliente',
            'requerido': True,
            'ancho': 'medio',
            'queryset': Cliente.objects.filter(activo=True).order_by('nombre_cliente'),
        },
        {
            'nombre': 'estatus',
            'label': 'Estatus',
            'tipo': 'select',
            'campo_fk': 'estatus',
            'requerido': True,
            'ancho': 'medio',
            'queryset': ProyectoEstatus.objects.filter(activo=True).order_by('orden'),
        },
        {
            'nombre': 'prioridad',
            'label': 'Prioridad',
            'tipo': 'select',
            'campo_fk': 'prioridad',
            'requerido': True,
            'ancho': 'medio',
            'queryset': ProyectoPrioridad.objects.filter(activo=True).order_by('orden'),
        },
        {
            'nombre': 'porcentaje_avance',
            'label': 'Avance (%)',
            'tipo': 'decimal',
            'requerido': False,
            'ancho': 'medio',
            'min': 0,
            'max': 100,
        },
        {
            'nombre': 'precio_venta',
            'label': 'Precio de venta',
            'tipo': 'decimal',
            'requerido': False,
            'ancho': 'medio',
        },
        {
            'nombre': 'tipo_proyecto',
            'label': 'Tipo de Proyecto',
            'tipo': 'text',
            'requerido': False,
            'ancho': 'medio',
            'placeholder': 'Ej. Interno, Externo',
        },
        {
            'nombre': 'categoria',
            'label': 'Categoría',
            'tipo': 'text',
            'requerido': False,
            'ancho': 'medio',
            'placeholder': 'Ej. Desarrollo, Mantenimiento',
        },
        {
            'nombre': 'fecha_inicio',
            'label': 'Fecha Inicio',
            'tipo': 'date',
            'requerido': False,
            'ancho': 'medio',
        },
        {
            'nombre': 'fecha_fin',
            'label': 'Fecha Fin',
            'tipo': 'date',
            'requerido': False,
            'ancho': 'medio',
        },
        {
            'nombre': 'activo',
            'label': 'Activo',
            'tipo': 'boolean',
            'requerido': False,
            'ancho': 'completo',
            'label_check': 'Este proyecto está activo',
        },
        {
            'nombre': 'usuarios_asignados',
            'label': 'Usuarios asignados',
            'tipo': 'lov',
            'requerido': False,
            'ancho': 'completo',
            'solo_editar': True,
            'especial': True,
            'modelo_rel': ProyectoAsignacion,  # ← modelo intermedio
            'campo_obj': 'proyecto',  # ← campo del proyecto
            'campo_rel': 'empleado',  # ← campo del usuario
            'queryset': Usuario.objects.filter(empresa_id=empresa_id).all(),
            'queryset_actual': None,
        },
    ]

@login_requerido
def proyecto_crear(request):
    return form_crear(
        request,
        model=Proyectos,
        campos_def=get_campos_proyecto(request),
        form_titulo='Nuevo Proyecto',
        url_lista='reporte_proyectos',
    )

@login_requerido
def proyecto_editar(request, pk):
    campos = get_campos_proyecto(request)
    for campo in campos:
        if campo['nombre'] == 'usuarios_asignados':
            campo['queryset_actual'] = ProyectoAsignacion.objects.filter(proyecto_id=pk).values_list('empleado_id',
                                                                                                     flat=True)

    return form_editar(
        request,
        model=Proyectos,
        pk=pk,
        campos_def=campos,
        form_titulo='Editar Proyecto',
        url_lista='reporte_proyectos',
    )

@login_requerido
def proyecto_eliminar(request, pk):
    return form_eliminar(request, Proyectos, pk)

#-------------CLIENTES-------------#
@login_requerido
def reporte_clientes(request):

    q         = request.GET.get('q', '').strip()
    columna   = request.GET.get('columna', '')
    orden     = request.GET.get('orden', 'proyecto_id')
    direccion = request.GET.get('dir', 'asc')
    per_page  = int(request.GET.get('per_page', 10))
    page      = request.GET.get('page', 1)

    qs = Cliente.objects.all()

    if q:
        if columna == 'nombre_cliente':
            qs = qs.filter(nombre_cliente_icontains=q)
        elif columna == 'rfc':
            qs = qs.filter(rfc__icontains=q)
        else:
            qs = qs.filter(
                Q(nombre_cliente_icontains=q) |
                Q(rfc__icontains=q)
            )

    campos_validos = [
        'cliente_id',
        'nombre_cliente',
        'rfc',
        'nombre_contacto',
        'email_contacto',
        'telefono_contacto',
        'fecha_creacion'
    ]
    if orden in campos_validos:
        orden_str = f'-{orden}' if direccion == 'desc' else orden
        qs = qs.order_by(orden_str)

    per_page_opciones = [10, 25, 50, 100]
    if per_page not in per_page_opciones:
        per_page = 10

    paginator = Paginator(qs, per_page)
    registros = paginator.get_page(page)

    columnas = [
        {'campo': 'cliente_id', 'label': 'ID', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'nombre_cliente', 'label': 'Nombre', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'rfc', 'label': 'RFC', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'direccion', 'label': 'Direccion', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'nombre_contacto', 'label': 'Contacto - Nombre', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'email_contacto', 'label': 'Contacto - Email', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'telefono_contacto', 'label': 'Contacto - Telefono', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'activo', 'label': 'Activo', 'tipo': 'boolean', 'ordenable': True},
        {'campo': 'fecha_creacion', 'label': 'Creado', 'tipo': 'datetime', 'ordenable': True},
    ]

    columnas_filtrables = [
        {'campo': 'nombre_cliente',      'label': 'Nombre'},
        {'campo': 'rfc', 'label': 'RFC'},
    ]

    context = {
        'registros':           registros,
        'total_registros':     paginator.count,
        'columnas':            columnas,
        'columnas_filtrables': columnas_filtrables,
        'per_page':            per_page,
        'per_page_opciones':   per_page_opciones,
        'reporte_titulo':      'Clientes',
        'reporte_subtitulo':   'Gestión de clientes',
        'reporte_breadcrumb':  'Inicio / Clientes',
        'puede_crear':         request.session.get('usuario_rol') == 0,
        'puede_editar':        request.session.get('usuario_rol') == 0,
        'puede_eliminar':      request.session.get('usuario_rol') == 0,
        'puede_exportar':      True,
        'url_crear':           '/reportes/clientes/crear/',
        'btn_crear_texto':     'Nuevo Cliente',
    }

    return render(request, 'reportes/reporte_base.html', context)


# ── FORMULARIOS ───────────────────────────

#-----------CLIENTES------------#
def get_campos_cliente():
    return [
        {
            'nombre': 'nombre_cliente', #nombre en el models
            'label': 'Nombre',
            'tipo': 'text',
            'requerido': True,
            'ancho': 'completo',
            'placeholder': 'Nombre del cliente',
        },
        {
            'nombre': 'rfc',
            'label': 'RFC',
            'tipo': 'text',
            'requerido': True,
            'ancho': 'completo',
            'placeholder': 'RFC',
        },
        {
            'nombre': 'direccion',
            'label': 'Direccion',
            'tipo': 'text',
            'requerido': False,
            'ancho': 'completo',
            'placeholder': 'Direccion',
            'filas': 3,
        },
        {
            'nombre': 'nombre_contacto',
            'label': 'Nombre del contacto',
            'tipo': 'text',
            'requerido': True,
            'ancho': 'completo',
            'placeholder': 'Nombre del contacto',
        },
        {
            'nombre': 'email_contacto',
            'label': 'Email del contacto',
            'tipo': 'text',
            'requerido': True,
            'ancho': 'medio',
            'placeholder': 'Email del contacto',
        },
        {
            'nombre': 'telefono_contacto',
            'label': 'Telefono del contacto',
            'tipo': 'text',
            'requerido': False,
            'ancho': 'medio',
            'placeholder': 'Telefono del contacto',
        },
        {
            'nombre': 'activo',
            'label': 'Activo',
            'tipo': 'boolean',
            'requerido': False,
            'ancho': 'completo',
            'label_check': 'Este cliente está activo',
            'solo_editar': True,
        },
    ]

@login_requerido
def create_cliente(request):
    print(f"CREATE USER - Method: {request.method}")
    return form_crear(
        request,
        model=Cliente,
        campos_def=get_campos_cliente(),
        form_titulo='Nuevo cliente',
        url_lista='reporte_clientes',
    )

@login_requerido
def edit_cliente(request, pk):
    return form_editar(
        request,
        model=Cliente,
        pk=pk,
        campos_def=get_campos_cliente(),
        form_titulo='Editar cliente',
        url_lista='reporte_clientes',
    )

@login_requerido
def delete_cliente(request, pk):
    return form_eliminar(request, Cliente, pk)

#-----------COSTOS------------#
@login_requerido
def reporte_costos(request):

    q         = request.GET.get('q', '').strip()
    columna   = request.GET.get('columna', '')
    orden     = request.GET.get('orden', 'costo_id')
    per_page  = int(request.GET.get('per_page', 10))
    page      = request.GET.get('page', 1)

    qs = Costos.objects.all()

    if q:
        if columna == 'nombre':
            qs = qs.filter(nombre_icontains=q)
        else:
            qs = qs.filter(
                Q(nombre_icontains=q)
            )

    campos_validos = [
        'costo_id',
        'proyecto',
        'nombre',
        'descripcion',
        'costo',
        'fecha_creacion'
    ]
    if orden in campos_validos:
        orden_str = f'-{orden}'
        qs = qs.order_by(orden_str)

    per_page_opciones = [10, 25, 50, 100]
    if per_page not in per_page_opciones:
        per_page = 10

    paginator = Paginator(qs, per_page)
    registros = paginator.get_page(page)

    columnas = [
        {'campo': 'costo_id', 'label': 'ID', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'proyecto', 'label': 'Proyecto', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'nombre', 'label': 'Nombre', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'descripcion', 'label': 'Descripcion', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'costo', 'label': 'Costo', 'tipo': 'moneda', 'ordenable': True},
        {'campo': 'fecha_creacion', 'label': 'Creado', 'tipo': 'datetime', 'ordenable': True},
    ]

    columnas_filtrables = [
        {'campo': 'Proyecto', 'label': 'Proyecto'},
    ]

    context = {
        'registros':           registros,
        'total_registros':     paginator.count,
        'columnas':            columnas,
        'columnas_filtrables': columnas_filtrables,
        'per_page':            per_page,
        'per_page_opciones':   per_page_opciones,
        'reporte_titulo':      'Costos',
        'reporte_subtitulo':   'Gestión de costos',
        'reporte_breadcrumb':  'Inicio / Costos',
        'puede_crear':         request.session.get('usuario_rol') == 0,
        'puede_editar':        request.session.get('usuario_rol') == 0,
        'puede_eliminar':      request.session.get('usuario_rol') == 0,
        'puede_exportar':      True,
        'url_crear':           '/reportes/costos/crear/',
        'btn_crear_texto':     'Nuevo Costo',
    }

    return render(request, 'reportes/reporte_base.html', context)

def get_campos_costos():
    return [
        {
            'nombre': 'proyecto',
            'label': 'Proyecto',
            'tipo': 'select',
            'campo_fk': 'proyecto',
            'requerido': True,
            'ancho': 'completo',
            'queryset': Proyectos.objects.filter(activo=True).order_by('nombre'),
        },
        {
            'nombre': 'nombre', #nombre en el models
            'label': 'Nombre',
            'tipo': 'text',
            'requerido': True,
            'ancho': 'completo',
            'placeholder': 'Nombre del costo',
        },
        {
            'nombre': 'descripcion',
            'label': 'Descripcion',
            'tipo': 'text',
            'requerido': True,
            'ancho': 'completo',
            'placeholder': 'Descripcion del costo',
        },
        {
            'nombre': 'costo',
            'label': 'Costo Monetario',
            'tipo': 'decimal',
            'requerido': True,
            'ancho': 'medio',
        },
    ]

@login_requerido
def create_costo(request):
    return form_crear(
        request,
        model=Costos,
        campos_def=get_campos_costos(),
        form_titulo='Nuevo costo',
        url_lista='reporte_costos',
    )

@login_requerido
def edit_costo(request, pk):
    return form_editar(
        request,
        model=Costos,
        pk=pk,
        campos_def=get_campos_costos(),
        form_titulo='Editar costo',
        url_lista='reporte_costos',
    )

@login_requerido
def delete_costo(request, pk):
    return form_eliminar(request, Costos, pk)

#-----------PRODUCTOS------------#
@login_requerido
def reporte_productos(request):

    q         = request.GET.get('q', '').strip()
    columna   = request.GET.get('columna', '')
    orden     = request.GET.get('orden', 'producto_id')
    per_page  = int(request.GET.get('per_page', 10))
    page      = request.GET.get('page', 1)

    qs = Productos.objects.all()

    if q:
        if columna == 'nombre':
            qs = qs.filter(nombre_icontains=q)
        else:
            qs = qs.filter(
                Q(nombre_icontains=q)
            )

    campos_validos = [
        'producto_id',
        'nombre',
        'modelo',
        'descripcion',
        'costo',
        'fecha_creacion'
    ]

    if orden in campos_validos:
        orden_str = f'-{orden}'
        qs = qs.order_by(orden_str)

    per_page_opciones = [10, 25, 50, 100]
    if per_page not in per_page_opciones:
        per_page = 10

    paginator = Paginator(qs, per_page)
    registros = paginator.get_page(page)

    columnas = [
        {'campo': 'producto_id', 'label': 'ID', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'nombre', 'label': 'Nombre', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'modelo', 'label': 'Modelo', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'descripcion', 'label': 'Descripcion', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'costo', 'label': 'Costo', 'tipo': 'moneda', 'ordenable': True},
        {'campo': 'fecha_creacion', 'label': 'Creado', 'tipo': 'datetime', 'ordenable': True},
    ]

    columnas_filtrables = [
        {'campo': 'nombre', 'label': 'Nombre'},
    ]

    context = {
        'registros':           registros,
        'total_registros':     paginator.count,
        'columnas':            columnas,
        'columnas_filtrables': columnas_filtrables,
        'per_page':            per_page,
        'per_page_opciones':   per_page_opciones,
        'reporte_titulo':      'Productos',
        'reporte_subtitulo':   'Gestión de productos',
        'reporte_breadcrumb':  'Inicio / Productos',
        'puede_crear':         request.session.get('usuario_rol') == 0,
        'puede_editar':        request.session.get('usuario_rol') == 0,
        'puede_eliminar':      request.session.get('usuario_rol') == 0,
        'puede_exportar':      True,
        'url_crear':           '/reportes/productos/crear/',
        'btn_crear_texto':     'Nuevo Producto',
    }

    return render(request, 'reportes/reporte_base.html', context)

def get_campos_productos():
    return [
        {
            'nombre': 'nombre',
            'label': 'Nombre',
            'tipo': 'text',
            'requerido': True,
            'ancho': 'completo',
            'placeholder': 'Nombre del producto',
        },
        {
            'nombre': 'modelo',
            'label': 'Modelo',
            'tipo': 'text',
            'requerido': False,
            'ancho': 'completo',
            'placeholder': 'Modelo del producto',
        },
        {
            'nombre': 'descripcion',
            'label': 'Descripcion',
            'tipo': 'text',
            'requerido': True,
            'ancho': 'completo',
            'placeholder': 'Descripcion del producto',
        },
        {
            'nombre': 'costo',
            'label': 'Costo del producto',
            'tipo': 'decimal',
            'requerido': True,
            'ancho': 'medio',
        },
    ]

@login_requerido
def create_producto(request):
    return form_crear(
        request,
        model=Productos,
        campos_def=get_campos_productos(),
        form_titulo='Nuevo producto',
        url_lista='reporte_productos',
    )

@login_requerido
def edit_producto(request, pk):
    return form_editar(
        request,
        model=Productos,
        pk=pk,
        campos_def=get_campos_productos(),
        form_titulo='Editar producto',
        url_lista='reporte_productos',
    )

@login_requerido
def delete_producto(request, pk):
    return form_eliminar(request, Productos, pk)

#-----------COTIZACIONES------------#
@login_requerido
def reporte_cotizaciones(request):
    inicio = time.perf_counter()

    q         = request.GET.get('q', '').strip()
    columna   = request.GET.get('columna', '')
    orden     = request.GET.get('orden', 'cotizacion_id')
    per_page  = int(request.GET.get('per_page', 10))
    page      = request.GET.get('page', 1)

    dec = DecimalField(max_digits=20, decimal_places=2)
    cien = Cast(Value(100), output_field=dec)

    qs = Cotizaciones.objects.annotate(
        costo_unitario=Sum(
            ExpressionWrapper(
                (F('cotizacionproductos__producto__costo') * F('cotizacionproductos__exportacion')) /
                NullIf(1 - (F('cotizacionproductos__margen') / Cast(Value(100), output_field=dec)), Cast(Value(0), output_field=dec)),
                output_field=dec
            ),
            distinct=True  # ← agrega esto
        )
    ).all()

    if q:
        if columna == 'nombre':
            qs = qs.filter(nombre_icontains=q)
        else:
            qs = qs.filter(
                Q(nombre_icontains=q)
            )

    campos_validos = [
        'cotizacion_id',
        'nombre',
        'fecha_creacion'
    ]

    if orden in campos_validos:
        orden_str = f'-{orden}'
        qs = qs.order_by(orden_str)

    per_page_opciones = [10, 25, 50, 100]
    if per_page not in per_page_opciones:
        per_page = 10

    # Calcular totales ANTES de paginar
    qs_list = list(qs)  # ← convierte a lista
    for cotizacion in qs_list:
        productos = CotizacionProductos.objects.filter(
            cotizacion_id=cotizacion.pk
        ).select_related('producto')

        total_partida = Decimal('0')
        for p in productos:
            cantidad = p.cantidad or 0
            costo = p.producto.costo or 0
            exportacion = p.exportacion or 0
            margen = p.margen or 0
            if margen != 100:
                costo_unitario = (
                        (Decimal(str(costo)) * Decimal(str(exportacion))) /
                        (Decimal('1') - (Decimal(str(margen)) / Decimal('100')))
                ).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
                total_partida += (costo_unitario * cantidad).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)

        total_partida += cotizacion.unidad_total
        cotizacion.total = total_partida

    # Paginar la lista con totales ya calculados
    paginator = Paginator(qs_list, per_page)
    registros = paginator.get_page(page)

    columnas = [
        {'campo': 'cotizacion_id', 'label': 'ID', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'cliente', 'label': 'Cliente', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'proyecto', 'label': 'Proyecto', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'nombre', 'label': 'Nombre', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'total', 'label': 'Total', 'tipo': 'moneda', 'ordenable': True},
        {'campo': 'fecha_creacion', 'label': 'Creado', 'tipo': 'datetime', 'ordenable': True},
    ]

    columnas_filtrables = [
        {'campo': 'nombre', 'label': 'Nombre'},
    ]

    context = {
        'registros':            registros,
        'total_registros':      paginator.count,
        'columnas':             columnas,
        'columnas_filtrables':  columnas_filtrables,
        'per_page':             per_page,
        'per_page_opciones':    per_page_opciones,
        'reporte_titulo':       'Cotizaciones',
        'reporte_subtitulo':    'Gestión de cotizaciones',
        'reporte_breadcrumb':   'Inicio / Cotizaciones',
        'puede_crear':          request.session.get('usuario_rol') == 0,
        'puede_editar':         request.session.get('usuario_rol') == 0,
        'puede_eliminar':       request.session.get('usuario_rol') == 0,
        'puede_exportar':       True,
        'url_crear':            '/reportes/cotizaciones/crear/',
        'url_exportar':         '/reportes/cotizaciones/exportar/',
        'url_formato_pdf':      '/reportes/cotizaciones/formato_pdf/',
        'btn_crear_texto':      'Nueva Cotizacion',
        'template': 'page',
    }
    #print(time.perf_counter() - inicio)
    return render(request, 'reportes/reporte_base.html', context)

def get_campos_cotizaciones():
    return [
        {
            'nombre': 'cliente',
            'label': 'Cliente',
            'tipo': 'select_cascada',
            'campo_hijo': 'proyecto',
            'url_cascada': '/reportes/proyectos-por-cliente/',
            'requerido': True,
            'ancho': 'medio',
            'queryset': Cliente.objects.filter(activo=True).order_by('nombre_cliente'),
        },
        {
            'nombre': 'nombre',
            'label': 'Nombre de la cotizacion',
            'tipo': 'text',
            'requerido': True,
            'ancho': 'medio',
            'placeholder': 'Nombre de la cotizacion',
        },
        {
            'nombre': 'proyecto',
            'label': 'Proyecto',
            'tipo': 'select_con_nuevo',
            'campo_oculto': 'servicio',
            'valor_trigger': 'nuevo_servicio',
            'campo_fk': 'proyecto',
            'requerido': False,
            'ancho': 'medio',
            'queryset': Proyectos.objects.filter(activo=True).order_by('nombre'),
        },
        {
            'nombre': 'servicio',
            'label': 'Servicio',
            'tipo': 'text',
            'requerido': False,
            'oculto': True,
            'ancho': 'medio',
            'placeholder': 'Servicio de la cotizacion',
        },
        {
            'nombre': 'equipo',
            'label': 'Equipo',
            'tipo': 'text',
            'requerido': False,
            'ancho': 'completo',
            'placeholder': 'Equipo de la cotizacion',
        },
        {
            'nombre': 'descripcion',
            'label': 'Descripcion',
            'tipo': 'textarea',
            'requerido': False,
            'ancho': 'completo',
            'placeholder': 'Descripcion de la cotizacion',
        },
        {
            'nombre': 'productos',
            'label': 'Productos',
            'tipo': 'lineas',
            'requerido': False,
            'ancho': 'completo',
            'especial': True,
            'modelo_lineas': CotizacionProductos,
            'campo_obj': 'cotizacion',
            'campo_prod': 'producto',
            'queryset': Productos.objects.all().order_by('nombre'),
            'nombre_campo_total': 'Costo de partida total',
            'valor_campo_total': 'total',
        },
        {
            'nombre': 'pie_cotizacion',
            'label': 'Pie de la cotizacion',
            'tipo': 'textarea',
            'requerido': False,
            'ancho': 'completo',
            'placeholder': 'Notas, Consideraciones generales, Requerimientos para operacion',
        },
    ]

@login_requerido
def create_cotizacion(request):
    if request.headers.get("HX-Request"):
        template = "reportes/modal_form.html"
    else:
        template = "reportes/page_form.html"

    return form_crear(
        request,
        model=Cotizaciones,
        campos_def=get_campos_cotizaciones(),
        form_titulo='Nueva cotizacion',
        url_lista='reportes:reporte_cotizaciones',
        template_form=template,
    )

@login_requerido
def edit_cotizacion(request, pk):
    dec  = DecimalField(max_digits=20, decimal_places=2)
    cien = Cast(Value(100), output_field=dec)

    qs = Cotizaciones.objects.annotate(
        costo_unitario=Sum(
            ExpressionWrapper(
                (F('cotizacionproductos__producto__costo') * F('cotizacionproductos__exportacion')) /
                NullIf(1 - (F('cotizacionproductos__margen') / Cast(Value(100), output_field=dec)),
                       Cast(Value(0), output_field=dec)),
                output_field=dec
            ),
            distinct=True
        )
    )

    # Calcular total solo para esta cotizacion
    cotizacion = qs.get(pk=pk)
    #print(f"unidad_costo_unitario: {cotizacion.unidad_costo_unitario}")
    #print(f"unidad_total: {cotizacion.unidad_total}")
    #print(f"dict completo: {cotizacion.__dict__}")
    productos  = CotizacionProductos.objects.filter(
        cotizacion_id=pk
    ).select_related('producto')

    total_partida = Decimal('0')
    for p in productos:
        cantidad    = p.cantidad       or 0
        costo       = p.producto.costo or 0
        exportacion = p.exportacion    or 0
        margen      = p.margen         or 0
        if margen != 100:
            costo_unitario = (
                (Decimal(str(costo)) * Decimal(str(exportacion))) /
                (Decimal('1') - (Decimal(str(margen)) / Decimal('100')))
            ).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
            total_partida += (costo_unitario * cantidad).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)

    total_partida += cotizacion.unidad_total
    cotizacion.total = total_partida

    if request.headers.get("HX-Request"):
        template = "reportes/modal_form.html"
    else:
        template = "reportes/page_form.html"

    return form_editar(
        request,
        model       = Cotizaciones,
        pk          = pk,
        campos_def  = get_campos_cotizaciones(),
        form_titulo = 'Editar cotizacion',
        url_lista   = 'reportes:reporte_cotizaciones',
        template_form = template,
        extra_context = {
            'queryset_editar': qs,
            'objeto_extra':    cotizacion,
            'url_pdf':         f'/reportes/cotizaciones/{pk}/pdf/',
        },
    )

@login_requerido
def delete_cotizacion(request, pk):
    return form_eliminar(request, Cotizaciones, pk)

@login_requerido
def exportar_cotizaciones(request):
    dec  = DecimalField(max_digits=20, decimal_places=2)
    cien = Cast(Value(100), output_field=dec)

    qs = Cotizaciones.objects.annotate(
        costo_unitario=Sum(
            ExpressionWrapper(
                (F('cotizacionproductos__producto__costo') * F('cotizacionproductos__exportacion')) /
                NullIf(1 - (F('cotizacionproductos__margen') / Cast(Value(100), output_field=dec)),
                       Cast(Value(0), output_field=dec)),
                output_field=dec
            ),
            distinct=True  # ← agrega esto
        )
    ).annotate(
        total=Sum(
            ExpressionWrapper(
                (F('cotizacionproductos__producto__costo') * F('cotizacionproductos__exportacion')) /
                NullIf(1 - (F('cotizacionproductos__margen') / Cast(Value(100), output_field=dec)),
                       Cast(Value(0), output_field=dec)) *
                F('cotizacionproductos__cantidad'),
                output_field=dec
            ),
            distinct=True
        )
    ).all()

    columnas = [
        {'campo': 'cotizacion_id',  'label': 'ID'},
        {'campo': 'proyecto',       'label': 'Proyecto'},
        {'campo': 'nombre',         'label': 'Nombre'},
        {'campo': 'costo_partida',  'label': 'Costo de Partida'},
        {'campo': 'margen',         'label': 'Margen'},
        {'campo': 'venta_partida',  'label': 'Venta de Partida'},
        {'campo': 'fecha_creacion', 'label': 'Creado'},
    ]

    return exportar_csv(request, qs, columnas, 'cotizaciones')

from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
from reportlab.lib.utils import ImageReader
import requests
from io import BytesIO
import io

def get_campos_formato_pdf():
    return [
        {
            'nombre': 'empresa_email',
            'label': 'Empresa email',
            'tipo': 'text',
            'requerido': False,
            'ancho': 'completo',
            'placeholder': 'Email de la empresa',
        },
        {
            'nombre': 'empresa_web',
            'label': 'Empresa web',
            'tipo': 'text',
            'requerido': False,
            'ancho': 'completo',
            'placeholder': 'Web de la empresa',
        },
        {
            'nombre': 'empresa_telefono',
            'label': 'Empresa telefono',
            'tipo': 'text',
            'requerido': False,
            'ancho': 'completo',
            'placeholder': 'Telefono de la empresa',
        },
        {
            'nombre': 'empresa_ubicacion',
            'label': 'Empresa ubicacion',
            'tipo': 'text',
            'requerido': False,
            'ancho': 'completo',
            'placeholder': 'Ubicacion de la empresa',
        },
        {
            'nombre': 'contacto_nombre',
            'label': 'Contacto nombre',
            'tipo': 'text',
            'requerido': False,
            'ancho': 'completo',
            'placeholder': 'Nombre del contacto',
        },
        {
            'nombre': 'contacto_telefono',
            'label': 'Contacto telefono',
            'tipo': 'text',
            'requerido': False,
            'ancho': 'completo',
            'placeholder': 'Telefono del contacto',
        },
        {
            'nombre': 'contacto_ubicacion',
            'label': 'Contacto ubicacion',
            'tipo': 'text',
            'requerido': False,
            'ancho': 'completo',
            'placeholder': 'Ubicacion del contacto',
        },
        {
            'nombre': 'valido',
            'label': 'Valido por',
            'tipo': 'decimal',
            'requerido': True,
            'ancho': 'medio',
        },
        {
            'nombre': 'empresa_imagen',
            'label': 'Logo empresa',
            'tipo': 'file',
            'requerido': False,
            'ancho': 'completo',
        },
    ]

@login_requerido
def edit_formato_pdf(request):
    formato, created = FormatoPdf.objects.get_or_create(pk=1)

    if request.method == 'POST':
        imagen = request.FILES.get('empresa_imagen')
        if imagen:
            supabase = create_client(
                settings.SUPABASE_URL,
                settings.SUPABASE_SERVICE_ROLE_KEY
            )
            extension = os.path.splitext(imagen.name)[1]  # .png, .jpg, etc.
            ruta = f"formato_pdf/logo_empresa{extension}"
            print(f'RUTA: {ruta}')

            supabase.storage.from_('empresas').upload(
                path=ruta,
                file=imagen.read(),
                file_options={
                    'content-type': imagen.content_type,
                    'upsert': 'true'
                }
            )

            # Obtener URL pública y guardar en el modelo
            url_publica = supabase.storage.from_('empresas').get_public_url(ruta)
            print(f'URL_IMAGEN: {url_publica}')
            formato.empresa_imagen = url_publica
            formato.save()

    return form_editar(
        request,
        model       = FormatoPdf,
        pk          = formato.pk,
        campos_def  = get_campos_formato_pdf(),
        form_titulo = 'Formato PDF Cotizaciones',
        url_lista   = 'reporte_cotizaciones',
    )

def texto_a_parrafo(texto, estilo):
    if not texto:
        return Paragraph('', estilo)
    # Reemplaza saltos de línea por <br/>
    texto_html = texto.replace('\n', '<br/>')
    return Paragraph(texto_html, estilo)

def pdf_cotizacion(request, pk):
    dec  = DecimalField(max_digits=20, decimal_places=2)
    print(f"PDF solicitado para pk={pk}")
    cotizacion = Cotizaciones.objects.annotate(
        costo_unitario=Sum(
            ExpressionWrapper(
                (F('cotizacionproductos__producto__costo') * F('cotizacionproductos__exportacion')) /
                NullIf(1 - (F('cotizacionproductos__margen') / Cast(Value(100), output_field=dec)),
                       Cast(Value(0), output_field=dec)),
                output_field=dec
            ),
            distinct=True
        )
    ).annotate(
        total=Sum(
            ExpressionWrapper(
                (F('cotizacionproductos__producto__costo') * F('cotizacionproductos__exportacion')) /
                NullIf(1 - (F('cotizacionproductos__margen') / Cast(Value(100), output_field=dec)),
                       Cast(Value(0), output_field=dec)) *
                F('cotizacionproductos__cantidad'),
                output_field=dec
            ),
            distinct=True
        )
    ).get(pk=pk)

    productos   = CotizacionProductos.objects.filter(
        cotizacion_id=pk
    ).select_related('producto')
    formato_pdf = FormatoPdf.objects.get(pk=1)

    # ── Logo ──────────────────────────────────────────────────
    logo = None
    if formato_pdf.empresa_imagen:
        try:
            resp        = requests.get(formato_pdf.empresa_imagen, timeout=10)
            resp.raise_for_status()
            img_bytes   = BytesIO(resp.content)
            reader      = ImageReader(img_bytes)
            ancho, alto = reader.getSize()
            logo        = Image(img_bytes)
            escala      = min((2*inch)/ancho, (1*inch)/alto)
            logo.drawWidth  = ancho * escala
            logo.drawHeight = alto  * escala
        except Exception:
            logo = None

    # ── Buffer y doc ──────────────────────────────────────────
    buffer = io.BytesIO()
    doc    = SimpleDocTemplate(
        buffer, pagesize=letter,
        rightMargin=0.6*inch, leftMargin=0.6*inch,
        topMargin=0.6*inch,   bottomMargin=0.6*inch
    )
    styles = getSampleStyleSheet()
    story  = []

    # ── Estilos ───────────────────────────────────────────────
    def estilo(nombre, **kw):
        return ParagraphStyle(nombre, parent=styles['Normal'], **kw)

    e_normal  = estilo('normal',   fontSize=8,  leading=11, textColor=colors.HexColor('#1c1c1c'))
    e_bold    = estilo('bold',     fontSize=8,  leading=11, textColor=colors.HexColor('#1c1c1c'), fontName='Helvetica-Bold')
    e_small   = estilo('small',    fontSize=7,  leading=10, textColor=colors.HexColor('#444444'))
    e_titulo  = estilo('titulo',   fontSize=10, leading=13, textColor=colors.HexColor('#1a1a2e'), fontName='Helvetica-Bold')
    e_servicio= estilo('servicio', fontSize=9,  leading=12, textColor=colors.HexColor('#1c1c1c'), fontName='Helvetica-Bold')
    e_desc    = estilo('desc',     fontSize=8,  leading=11, textColor=colors.HexColor('#1c1c1c'))
    e_th      = ParagraphStyle('th', fontSize=8, textColor=colors.white,
                               fontName='Helvetica-Bold', alignment=1, leading=10)
    e_td      = ParagraphStyle('td', fontSize=8, textColor=colors.HexColor('#1c1c1c'),
                               fontName='Helvetica', leading=10)
    e_td_c = ParagraphStyle('td_c', fontSize=8, textColor=colors.HexColor('#1c1c1c'),
                            fontName='Helvetica', leading=10, alignment=1)
    e_td_r    = ParagraphStyle('td_r', fontSize=8, textColor=colors.HexColor('#1c1c1c'),
                               fontName='Helvetica', leading=10, alignment=2)

    # ── Bloque empresa (izquierda) ────────────────────────────
    empresa_items = []
    if logo:
        empresa_items.append(logo)
        empresa_items.append(Spacer(1, 4))
    empresa_items += [
        Paragraph(formato_pdf.empresa_ubicacion or '', e_small),
        Paragraph(formato_pdf.empresa_email     or '', e_small),
        Paragraph(formato_pdf.empresa_web       or '', e_small),
        Paragraph(f'Tel. {formato_pdf.empresa_telefono}'  or '', e_small),
    ]

    # ── Bloque contacto + cliente (derecha) ───────────────────
    servicio_txt = cotizacion.proyecto.nombre if cotizacion.proyecto_id else (cotizacion.servicio or '')
    fecha_txt    = cotizacion.fecha_creacion.strftime('%d/%m/%y') if cotizacion.fecha_creacion else ''

    tabla_derecha_data = [
        [
            Paragraph('<b>CONTACTO</b>', e_bold),
            Paragraph('<b>CLIENTE</b>', e_bold),
        ],
        [
            Paragraph(formato_pdf.contacto_nombre   or '', e_normal),
            Paragraph(cotizacion.cliente.nombre_cliente if cotizacion.cliente_id else '', e_normal),
        ],
        [
            Paragraph(f'Tel. {formato_pdf.contacto_telefono or ""}', e_normal),
            Paragraph('', e_normal),
        ],
        [
            Paragraph(formato_pdf.contacto_ubicacion or '', e_normal),
            Paragraph(cotizacion.cliente.direccion if cotizacion.cliente_id else '', e_normal),
        ],
        [
            Paragraph('<b>Cotización #:</b>', e_bold),
            Paragraph(cotizacion.nombre or '', e_normal),
        ],
        [
            Paragraph('<b>Fecha:</b>', e_bold),
            Paragraph(fecha_txt, e_normal),
        ],
        [
            Paragraph('<b>Valido por:</b>', e_bold),
            Paragraph(f'{formato_pdf.valido or ""} días', e_normal),
        ],
    ]

    tabla_derecha = Table(tabla_derecha_data, colWidths=[1.6*inch, 1.8*inch])
    tabla_derecha.setStyle(TableStyle([
        ('FONTNAME',      (0, 0), (-1, -1), 'Helvetica'),
        ('FONTSIZE',      (0, 0), (-1, -1), 8),
        ('TOPPADDING',    (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LINEBELOW',     (0, 3), (-1, 3),  0.5, colors.HexColor('#cccccc')),
        ('BACKGROUND',    (0, 0), (-1, 0),  colors.HexColor('#f0ece4')),
    ]))

    # ── Tabla encabezado 2 columnas ───────────────────────────
    empresa_col = empresa_items  # lista de flowables

    header_table = Table(
        [[empresa_col, tabla_derecha]],
        colWidths=[3.8*inch, 3.4*inch]
    )
    header_table.setStyle(TableStyle([
        ('VALIGN',     (0, 0), (-1, -1), 'TOP'),
        ('LINEBELOW',  (0, 0), (-1, 0),  1,   colors.HexColor('#1a1a2e')),
        ('TOPPADDING', (0, 0), (-1, -1), 0),
    ]))
    story.append(header_table)
    story.append(Spacer(1, 0.15*inch))

    # ── Servicio ──────────────────────────────────────────────
    story.append(Paragraph(f'SERVICIO: {servicio_txt}', e_servicio))
    story.append(Spacer(1, 0.05*inch))

    # ── Equipo ────────────────────────────────────────────────
    if cotizacion.equipo:
        story.append(Paragraph(cotizacion.equipo, e_titulo))
        story.append(Spacer(1, 0.05*inch))

    # ── Descripción ───────────────────────────────────────────
    if cotizacion.descripcion:
        story.append(texto_a_parrafo(cotizacion.descripcion, e_desc))
        story.append(Spacer(1, 0.1*inch))

    # ── Tabla productos ───────────────────────────────────────
    """encabezados = [
        Paragraph('Cantidad',        e_th),
        Paragraph('Producto',        e_th),
        Paragraph('Costo',           e_th),
        Paragraph('Exportacion',     e_th),
        Paragraph('Margen',          e_th),
        Paragraph('C.Unitario',      e_th),
        Paragraph('Total (USD)',     e_th),
    ]"""

    encabezados = [
        Paragraph('Cantidad', e_th),
        Paragraph('Producto', e_th),
        Paragraph('Costo Unitario', e_th),
        Paragraph('Total (USD)', e_th),
    ]

    filas         = [encabezados]
    total_partida = Decimal('0')

    #clase para crear nuevo producto
    class ProductoUnidad:
        def __init__(self, cotizacion):
            self.cantidad = cotizacion.unidad_cantidad
            self.exportacion = cotizacion.unidad_exportacion
            self.margen = cotizacion.unidad_margen
            self.producto = type('obj', (object,), {
                'nombre': cotizacion.unidad_descripcion,
                'costo': cotizacion.unidad_costo,
            })()

    if cotizacion.unidad_descripcion and cotizacion.unidad_costo:
        unidad = ProductoUnidad(cotizacion)
        productos_completos = list(chain(productos, [unidad]))
    else:
        productos_completos = productos

    def texto_pdf(texto):
        if not texto:
            return ''
        return texto.replace('\n', '<br/>')

    for p in productos_completos:
        cantidad    = Decimal(str(p.cantidad    or 0))
        costo       = Decimal(str(p.producto.costo or 0))
        exportacion = Decimal(str(p.exportacion or 0))
        margen      = Decimal(str(p.margen      or 0))

        divisor = Decimal('1') - (margen / Decimal('100'))
        costo_unitario = (
            (costo * exportacion) / divisor
        ).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP) if divisor else Decimal('0')

        total = (costo_unitario * cantidad).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
        total_partida += total

        """filas.append([
            Paragraph(str(int(cantidad)),           e_td_r),
            Paragraph(p.producto.nombre or '',      e_td),
            Paragraph(f'$ {costo:,.2f}',            e_td_r),
            Paragraph(str(exportacion),             e_td_r),
            Paragraph(f'{margen}%',                 e_td_r),
            Paragraph(f'$ {costo_unitario:,.2f}',   e_td_r),
            Paragraph(f'$ {total:,.2f}',            e_td_r),
        ])"""
        filas.append([
            Paragraph(str(int(cantidad)), e_td_c),
            Paragraph(texto_pdf(p.producto.nombre) or '', e_td),
            Paragraph(f'$ {costo_unitario:,.2f}', e_td_c),
            Paragraph(f'$ {total:,.2f}', e_td_c),
        ])

    """tabla = Table(filas, colWidths=[
        0.7*inch,   # Cantidad
        2.2*inch,   # Producto
        0.8*inch,   # Costo
        0.8*inch,   # Exportacion
        0.65*inch,  # Margen
        0.85*inch,  # C.Unitario
        0.9*inch,   # Total
    ])"""
    tabla = Table(filas, colWidths=[
        1 * inch,  # Cantidad
        4 * inch,  # Producto
        1 * inch,  # C.Unitario
        1 * inch,  # Total
    ])
    """tabla.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0),  colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.white),
        ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 0),  8),
        ('ALIGN',         (0, 0), (-1, 0),  'CENTER'),
        ('TOPPADDING',    (0, 0), (-1, 0),  6),
        ('BOTTOMPADDING', (0, 0), (-1, 0),  6),
        ('FONTNAME',      (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',      (0, 1), (-1, -1), 8),
        ('ALIGN',         (0, 1), (0, -1),  'CENTER'),
        ('ALIGN',         (1, 1), (1, -1),  'LEFT'),
        ('ALIGN',         (2, 1), (-1, -1), 'RIGHT'),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [colors.white, colors.HexColor('#f7f4ef')]),
        ('TOPPADDING',    (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('LINEBELOW',     (0, 0), (-1, -1), 0.5, colors.HexColor('#e0dbd2')),
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
    ]))"""

    tabla.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 8),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),  # encabezado centrado
        ('TOPPADDING', (0, 0), (-1, 0), 6),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 6),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),  # ← todas las filas centradas
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7f4ef')]),
        ('TOPPADDING', (0, 1), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 4),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, colors.HexColor('#e0dbd2')),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(tabla)
    story.append(Spacer(1, 0.2*inch))

    # ── Resumen ───────────────────────────────────────────────
    resumen = Table(
        [['Total (USD):', f'$ {total_partida:,.2f}']],
        colWidths=[5.9*inch, 1.3*inch]
    )
    resumen.setStyle(TableStyle([
        ('FONTNAME',      (0, 0), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 9),
        ('ALIGN',         (0, 0), (0, 0),   'RIGHT'),
        ('ALIGN',         (1, 0), (1, 0),   'RIGHT'),
        ('LINEABOVE',     (0, 0), (-1, 0),  1, colors.HexColor('#1a1a2e')),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(resumen)
    story.append(Spacer(1, 0.2*inch))

    # ── Pie de cotización ─────────────────────────────────────
    if cotizacion.pie_cotizacion:
        story.append(texto_a_parrafo(cotizacion.pie_cotizacion, e_desc))

    # ── Build ─────────────────────────────────────────────────
    doc.build(story)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="cotizacion_{cotizacion.nombre}.pdf"'
    return response
