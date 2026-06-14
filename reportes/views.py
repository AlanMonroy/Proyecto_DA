from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from users.decorators import login_requerido
from .views_crud import form_crear, form_editar, form_eliminar

from users.models import Usuario, Rol
from .models import Refacciones, Proyectos, ProyectoEstatus, ProyectoPrioridad, Cliente

# ── Ejemplo: reporte de usuarios ─────────────────────────────────
# Adapta este patrón para cualquier modelo/tabla que necesites.

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
    #qs = Usuario.objects.all()
    qs = Usuario.objects.select_related('rol').all()

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

    q         = request.GET.get('q', '').strip()
    columna   = request.GET.get('columna', '')
    orden     = request.GET.get('orden', 'proyecto_id')
    direccion = request.GET.get('dir', 'asc')
    per_page  = int(request.GET.get('per_page', 10))
    page      = request.GET.get('page', 1)

    #qs = Proyectos.objects.all()
    qs = Proyectos.objects.select_related('estatus', 'prioridad').all()

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
        {'campo': 'cliente_id', 'label': 'Cliente', 'tipo': 'fk', 'ordenable': True},
        {'campo': 'responsable_id', 'label': 'Responsable', 'tipo': 'fk', 'ordenable': True},
        {'campo': 'porcentaje_avance', 'label': 'Avance', 'tipo': 'porcentaje', 'ordenable': True},
        {'campo': 'cotizacion', 'label': 'Cotizacion', 'tipo': 'moneda', 'ordenable': True},
        {'campo': 'costo_real', 'label': 'Costo', 'tipo': 'moneda', 'ordenable': True},
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

    return render(request, 'reportes/reporte_base.html', context)


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
        {'campo': 'rfc', 'label': 'Descripción', 'RFC': 'texto', 'ordenable': True},
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
# Reutilizable para crear y editar
def get_campos_proyecto():
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
            'nombre': 'cotizacion',
            'label': 'Cotización',
            'tipo': 'decimal',
            'requerido': False,
            'ancho': 'medio',
        },
        {
            'nombre': 'costo_real',
            'label': 'Costo Real',
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
    ]

@login_requerido
def proyecto_crear(request):
    return form_crear(
        request,
        model=Proyectos,
        campos_def=get_campos_proyecto(),
        form_titulo='Nuevo Proyecto',
        url_lista='reporte_proyectos',
    )

@login_requerido
def proyecto_editar(request, pk):
    return form_editar(
        request,
        model=Proyectos,
        pk=pk,
        campos_def=get_campos_proyecto(),
        form_titulo='Editar Proyecto',
        url_lista='reporte_proyectos',
    )

@login_requerido
def proyecto_eliminar(request, pk):
    return form_eliminar(request, Proyectos, pk)

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
            'campo_fk': 'rol_id',
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
