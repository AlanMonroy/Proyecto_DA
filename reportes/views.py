from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from users.decorators import login_requerido

# ── Ejemplo: reporte de usuarios ─────────────────────────────────
# Adapta este patrón para cualquier modelo/tabla que necesites.

from users.models import Usuario  # cambia por tu modelo
from .models import Refacciones


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
    qs = Usuario.objects.all()

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
        'puede_crear':    request.session.get('usuario_rol') == 0,
        'puede_editar':   False,#request.session.get('usuario_rol') == 0,
        'puede_eliminar': False,#request.session.get('usuario_rol') == 0,
        'puede_exportar': True,

        # URLs CRUD
        'url_crear':          '/usuarios/crear/',
        'url_editar':         'usuarios_editar',   # name de la URL (usa {% url %})
        'url_eliminar_base':  '/usuarios/eliminar/',
        'url_exportar':       '/usuarios/exportar/',
        'btn_crear_texto':    'Nuevo usuario',
    }

    return render(request, 'reportes/reporte_base.html', context)


# ── Vista eliminar (reutilizable para cualquier modelo) ──────────
@login_requerido
def eliminar_usuario(request, pk):
    if request.session.get('usuario_rol') != 0:
        return redirect('home-user')

    usuario = get_object_or_404(Usuario, pk=pk)
    if request.method == 'POST':
        usuario.delete()
    return redirect('reporte_usuarios')

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