from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.core.paginator import Paginator
from django.db.models import Q, Sum, F, ExpressionWrapper, DecimalField, Value
from django.db.models.functions import Abs, NullIf, Cast
from users.decorators import login_requerido
from .views_crud import form_crear, form_editar, form_eliminar, exportar_csv
from users.models import Usuario, Rol
from .models import Refacciones, Proyectos, ProyectoEstatus, ProyectoPrioridad, Cliente, ProyectoAsignacion, Costos, Productos, Cotizaciones, CotizacionProductos

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

    return render(request, 'reportes/reporte_base.html', context)

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
            'queryset': Usuario.objects.all(),
            'queryset_actual': None,
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
    campos = get_campos_proyecto()
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

    q         = request.GET.get('q', '').strip()
    columna   = request.GET.get('columna', '')
    orden     = request.GET.get('orden', 'cotizacion_id')
    per_page  = int(request.GET.get('per_page', 10))
    page      = request.GET.get('page', 1)

    dec = DecimalField(max_digits=20, decimal_places=2)
    cien = Cast(Value(100), output_field=dec)

    qs = Cotizaciones.objects.annotate(
        costo_partida=Sum(
            ExpressionWrapper(
                F('cotizacionproductos__cantidad') * F('cotizacionproductos__producto__costo'),
                output_field=dec
            )
        )
    ).annotate(
        venta_partida=ExpressionWrapper(
            F('costo_partida') / NullIf(
                (cien - Cast(F('margen'), output_field=dec)) / cien,
                Cast(Value(0), output_field=dec)
            ),
            output_field=dec
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

    paginator = Paginator(qs, per_page)
    registros = paginator.get_page(page)

    columnas = [
        {'campo': 'cotizacion_id', 'label': 'ID', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'proyecto', 'label': 'Proyecto', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'nombre', 'label': 'Nombre', 'tipo': 'texto', 'ordenable': True},
        {'campo': 'costo_partida', 'label': 'Costo de Partida', 'tipo': 'moneda', 'ordenable': True},
        {'campo': 'margen', 'label': 'Margen', 'tipo': 'numero', 'ordenable': True},
        {'campo': 'venta_partida', 'label': 'Venta de partida', 'tipo': 'numero', 'ordenable': True},
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
        'reporte_titulo':      'Cotizaciones',
        'reporte_subtitulo':   'Gestión de cotizaciones',
        'reporte_breadcrumb':  'Inicio / Cotizaciones',
        'puede_crear':         request.session.get('usuario_rol') == 0,
        'puede_editar':        request.session.get('usuario_rol') == 0,
        'puede_eliminar':      request.session.get('usuario_rol') == 0,
        'puede_exportar':      True,
        'url_crear':            '/reportes/cotizaciones/crear/',
        'url_exportar':         '/reportes/cotizaciones/exportar/',
        'btn_crear_texto':      'Nueva Cotizacion',
    }

    return render(request, 'reportes/reporte_base.html', context)

def get_campos_cotizaciones():
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
            'nombre': 'nombre',
            'label': 'Nombre',
            'tipo': 'text',
            'requerido': True,
            'ancho': 'completo',
            'placeholder': 'Nombre de la cotizacion',
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
            'valor_campo_total': 'costo_partida',
        },
        {
            'nombre': 'margen',
            'label': 'Margen',
            'tipo': 'number',
            'requerido': False,
            'ancho': 'medio',
        },
        {
            'nombre': 'venta_partida',
            'label': 'Venta de partida',
            'tipo': 'readonly',
            'requerido': False,
            'ancho': 'medio',
            'campo_valor': 'venta_partida',
        },
    ]

@login_requerido
def create_cotizacion(request):
    return form_crear(
        request,
        model=Cotizaciones,
        campos_def=get_campos_cotizaciones(),
        form_titulo='Nueva cotizacion',
        url_lista='reporte_cotizaciones',
    )

@login_requerido
def edit_cotizacion(request, pk):
    dec = DecimalField(max_digits=20, decimal_places=2)
    cien = Cast(Value(100), output_field=dec)

    qs = Cotizaciones.objects.annotate(
        costo_partida=Sum(
            ExpressionWrapper(
                F('cotizacionproductos__cantidad') * F('cotizacionproductos__producto__costo'),
                output_field=dec
            )
        )
    ).annotate(
        venta_partida=ExpressionWrapper(
            F('costo_partida') / NullIf(
                (cien - Cast(F('margen'), output_field=dec)) / cien,
                Cast(Value(0), output_field=dec)
            ),
            output_field=dec
        )
    ).all()

    return form_editar(
        request,
        model=Cotizaciones,
        pk=pk,
        campos_def=get_campos_cotizaciones(),
        form_titulo='Editar cotizacion',
        url_lista='reporte_cotizaciones',
        extra_context={'queryset_editar': qs, 'url_pdf': f'/reportes/cotizaciones/{pk}/pdf/',},
    )

@login_requerido
def delete_cotizacion(request, pk):
    return form_eliminar(request, Cotizaciones, pk)

@login_requerido
def exportar_cotizaciones(request):
    dec  = DecimalField(max_digits=20, decimal_places=2)
    cien = Cast(Value(100), output_field=dec)

    qs = Cotizaciones.objects.annotate(
        costo_partida=Sum(
            ExpressionWrapper(
                F('cotizacionproductos__cantidad') * F('cotizacionproductos__producto__costo'),
                output_field=dec
            )
        )
    ).annotate(
        venta_partida=ExpressionWrapper(
            F('costo_partida') / NullIf(
                (cien - Cast(F('margen'), output_field=dec)) / cien,
                Cast(Value(0), output_field=dec)
            ),
            output_field=dec
        )
    ).all()

    columnas = [
        {'campo': 'cotizacion_id',  'label': 'ID'},
        {'campo': 'nombre',         'label': 'Nombre'},
        {'campo': 'costo_partida',  'label': 'Costo de Partida'},
        {'campo': 'margen',         'label': 'Margen'},
        {'campo': 'venta_partida',  'label': 'Venta de Partida'},
        {'campo': 'fecha_creacion', 'label': 'Creado'},
    ]

    return exportar_csv(request, qs, columnas, 'cotizaciones')

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_RIGHT, TA_CENTER
import io

@login_requerido
def pdf_cotizacion(request, pk):
    # Obtener cotizacion con productos
    dec  = DecimalField(max_digits=20, decimal_places=2)
    cien = Cast(Value(100), output_field=dec)

    cotizacion = Cotizaciones.objects.annotate(
        costo_partida=Sum(
            ExpressionWrapper(
                F('cotizacionproductos__cantidad') * F('cotizacionproductos__producto__costo'),
                output_field=dec
            )
        )
    ).annotate(
        venta_partida=ExpressionWrapper(
            F('costo_partida') / NullIf(
                (cien - Cast(F('margen'), output_field=dec)) / cien,
                Cast(Value(0), output_field=dec)
            ),
            output_field=dec
        )
    ).get(pk=pk)

    productos = CotizacionProductos.objects.filter(
        cotizacion_id=pk
    ).select_related('producto')

    # Crear PDF en memoria
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75*inch,
        leftMargin=0.75*inch,
        topMargin=0.75*inch,
        bottomMargin=0.75*inch
    )

    styles = getSampleStyleSheet()
    story  = []

    # ── Estilos personalizados ────────────────────────────────
    estilo_titulo = ParagraphStyle(
        'titulo',
        parent=styles['Title'],
        fontSize=20,
        textColor=colors.HexColor('#1a1a2e'),
        spaceAfter=4,
    )
    estilo_subtitulo = ParagraphStyle(
        'subtitulo',
        parent=styles['Normal'],
        fontSize=10,
        textColor=colors.HexColor('#6b6b6b'),
        spaceAfter=20,
    )
    estilo_label = ParagraphStyle(
        'label',
        parent=styles['Normal'],
        fontSize=8,
        textColor=colors.HexColor('#6b6b6b'),
        spaceAfter=2,
    )
    estilo_valor = ParagraphStyle(
        'valor',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#1c1c1c'),
        spaceAfter=12,
    )
    estilo_derecha = ParagraphStyle(
        'derecha',
        parent=styles['Normal'],
        fontSize=11,
        textColor=colors.HexColor('#1c1c1c'),
        alignment=TA_RIGHT,
    )

    # ── Encabezado ────────────────────────────────────────────
    story.append(Paragraph('Cotización', estilo_titulo))
    story.append(Paragraph(cotizacion.nombre, estilo_subtitulo))
    story.append(Spacer(1, 0.1*inch))

    # ── Tabla de productos ────────────────────────────────────
    encabezados = ['Producto', 'Costo Unit.', 'Importación', 'Costo de Venta', 'Cantidad', 'Subtotal']
    filas = [encabezados]

    for p in productos:
        costo_unit  = p.producto.costo or 0
        importacion = p.importacion or 0
        costo_venta = costo_unit * importacion
        subtotal    = costo_venta * p.cantidad

        filas.append([
            p.producto.nombre,
            f'${costo_unit:,.2f}',
            f'${importacion:,.2f}',
            f'${costo_venta:,.2f}',
            str(p.cantidad),
            f'${subtotal:,.2f}',
        ])

    tabla = Table(filas, colWidths=[
        2.0*inch, 1.0*inch, 1.0*inch, 1.2*inch, 0.8*inch, 1.0*inch
    ])

    tabla.setStyle(TableStyle([
        # Encabezado
        ('BACKGROUND',    (0, 0), (-1, 0),  colors.HexColor('#1a1a2e')),
        ('TEXTCOLOR',     (0, 0), (-1, 0),  colors.white),
        ('FONTNAME',      (0, 0), (-1, 0),  'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, 0),  9),
        ('ALIGN',         (0, 0), (-1, 0),  'CENTER'),
        ('BOTTOMPADDING', (0, 0), (-1, 0),  8),
        ('TOPPADDING',    (0, 0), (-1, 0),  8),
        # Filas
        ('FONTNAME',      (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE',      (0, 1), (-1, -1), 9),
        ('ALIGN',         (1, 1), (-1, -1), 'RIGHT'),
        ('ALIGN',         (0, 1), (0, -1),  'LEFT'),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [colors.white, colors.HexColor('#f7f4ef')]),
        ('TOPPADDING',    (0, 1), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 1), (-1, -1), 6),
        ('LINEBELOW',     (0, 0), (-1, -1), 0.5, colors.HexColor('#e0dbd2')),
    ]))

    story.append(tabla)
    story.append(Spacer(1, 0.3*inch))

    # ── Resumen ───────────────────────────────────────────────
    costo   = cotizacion.costo_partida  or 0
    margen  = cotizacion.margen         or 0
    venta   = cotizacion.venta_partida  or 0

    resumen = [
        ['Costo de partida:',  f'${costo:,.2f}'],
        ['Margen:',            f'{margen}%'],
        ['Venta de partida:',  f'${venta:,.2f}'],
    ]

    tabla_resumen = Table(resumen, colWidths=[4.5*inch, 2.5*inch])
    tabla_resumen.setStyle(TableStyle([
        ('FONTNAME',      (0, 0), (-1, -2), 'Helvetica'),
        ('FONTNAME',      (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE',      (0, 0), (-1, -1), 10),
        ('ALIGN',         (1, 0), (1, -1),  'RIGHT'),
        ('TEXTCOLOR',     (0, 0), (0, -1),  colors.HexColor('#6b6b6b')),
        ('TEXTCOLOR',     (1, 0), (1, -1),  colors.HexColor('#1c1c1c')),
        ('LINEABOVE',     (0, -1), (-1, -1), 1, colors.HexColor('#1a1a2e')),
        ('TOPPADDING',    (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
    ]))

    story.append(tabla_resumen)

    # ── Generar PDF ───────────────────────────────────────────
    doc.build(story)
    buffer.seek(0)

    response = HttpResponse(buffer, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="cotizacion_{cotizacion.nombre}.pdf"'
    return response
