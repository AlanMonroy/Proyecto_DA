"""
views_crud.py — Vistas genéricas HTMX para CRUD
Importa y usa en cualquier app de reportes.
"""
from django.shortcuts import render, get_object_or_404
import csv
from django.http import HttpResponse
from decimal import Decimal, ROUND_HALF_UP
from django.contrib import messages


def get_form_campos(campos, objeto=None):
    """
    Procesa los campos del formulario y carga opciones de ForeignKey.
    campos: lista de dicts definidos en la vista
    objeto: instancia del modelo (None si es creación)
    """
    for campo in campos:
        # Cargar opciones de select desde queryset
        if campo.get('tipo') in ('select', 'select_con_nuevo', 'select_cascada') and 'queryset' in campo:
            qs = campo['queryset']
            campo['opciones'] = [
                {'valor': str(obj.pk), 'label': str(obj)}
                for obj in qs
            ]

        if campo.get('tipo') == 'lov' and 'queryset' in campo:
            qs = campo['queryset']
            campo['opciones'] = [
                {'valor': str(obj.pk), 'label': str(obj)}
                for obj in qs
            ]
            if objeto and 'queryset_actual' in campo and campo['queryset_actual'] is not None:
                actuales_pks = list(campo['queryset_actual'])
                campo['valores_actuales'] = [
                    {'valor': str(obj.pk), 'label': str(obj)}
                    for obj in qs if obj.pk in actuales_pks
                ]
            else:
                campo['valores_actuales'] = []

        if campo.get('tipo') == 'lineas' and 'queryset' in campo:
            qs = campo['queryset']
            campo['opciones'] = [
                {
                    'producto_id': obj.pk,
                    'nombre': obj.nombre,
                    'costo': obj.costo,
                }
                for obj in qs
            ]
            if objeto and 'modelo_lineas' in campo:
                lineas_qs = campo['modelo_lineas'].objects.filter(
                    **{campo['campo_obj'] + '_id': objeto.pk}
                ).select_related('producto')
                campo['lineas_actuales'] = [
                    {
                        'producto_id': l.producto_id,
                        'nombre': l.producto.nombre,
                        'costo': l.producto.costo or Decimal('1'),
                        'cantidad': l.cantidad or Decimal('1'),
                        'exportacion': l.exportacion or Decimal('1'),
                        'margen': l.margen or Decimal('1'),
                        'costo_unitario': (
                            costo_unitario := (
                                ((l.producto.costo or Decimal('1')) * (l.exportacion or Decimal('1'))) /
                                (Decimal('1') - ((l.margen or Decimal('1'))/ Decimal('100')))
                            ).quantize(Decimal('0.00'), rounding=ROUND_HALF_UP)
                        ),
                        'subtotal': (costo_unitario * l.cantidad).quantize(Decimal('0.00'),rounding=ROUND_HALF_UP),
                    }
                    for l in lineas_qs
                ]
            else:
                campo['lineas_actuales'] = []

    return campos

def form_crear(request, model, campos_def, form_titulo, url_lista,
               template_form='reportes/modal_form.html',
               template_lista=None, extra_context=None):

    campos_def = [c for c in campos_def if not c.get('solo_editar')]
    campos = get_form_campos(campos_def)

    if request.method == 'POST':
        errores = {}
        datos   = {}

        for campo in campos:
            nombre    = campo['nombre']
            requerido = campo.get('requerido', False)
            tipo      = campo.get('tipo', 'text')

            if campo.get('especial'):  # ← salta lineas, lov, password
                continue

            valor = request.POST.get(nombre, '').strip()

            if requerido and not valor and tipo != 'boolean':
                errores[nombre] = 'Este campo es obligatorio.'
                continue

            if tipo == 'boolean':
                datos[nombre] = nombre in request.POST
            elif tipo in ('number', 'decimal', 'number_readonly') and valor:
                try:
                    datos[nombre] = float(valor) if tipo == 'decimal' else int(valor)
                except ValueError:
                    errores[nombre] = 'Valor numérico inválido.'
            elif tipo in ('select', 'select_con_nuevo', 'select_cascada') and valor:
                valor_trigger = campo.get('valor_trigger')
                if valor_trigger and valor == valor_trigger:
                    pass
                else:
                    campo_fk = campo.get('campo_fk', nombre)
                    datos[campo_fk + '_id'] = valor
            elif valor:
                datos[nombre] = valor

        if not errores:
            p1 = request.POST.get('password1', '')
            p2 = request.POST.get('password2', '')
            if p1 or p2:
                if p1 != p2:
                    errores['password2'] = 'Las contraseñas no coinciden.'
                elif len(p1) < 8:
                    errores['password1'] = 'La contraseña debe tener al menos 8 caracteres.'

        if not errores:
            # Aplicar valores por defecto
            defaults = extra_context.pop('defaults', {}) if extra_context else {}
            datos.update(defaults)

            try:
                obj = model(**datos)
                if hasattr(obj, 'activo') and 'activo' not in datos:
                    obj.activo = True
                if p1:
                    obj.set_password(p1)

                # ── Calcular campos readonly ──────────────────────────
                if hasattr(obj, 'unidad_costo_unitario'):

                    obj.unidad_descripcion = request.POST.get(
                        "unidad_descripcion", ""
                    ).strip()

                    unidad_costo = Decimal(str(request.POST.get("unidad_costo", 0) or 0))
                    unidad_exp = Decimal(str(request.POST.get("unidad_exportacion", 0) or 0))
                    unidad_margen = Decimal(str(request.POST.get("unidad_margen", 0) or 0))
                    unidad_cant = Decimal(str(request.POST.get("unidad_cantidad", 0) or 0))

                    obj.unidad_costo = unidad_costo
                    obj.unidad_exportacion = unidad_exp
                    obj.unidad_margen = unidad_margen
                    obj.unidad_cantidad = unidad_cant

                    divisor = Decimal("1") - (unidad_margen / Decimal("100"))

                    if divisor and unidad_exp:
                        costo_unitario = (
                                unidad_costo * unidad_exp / divisor
                        ).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
                    else:
                        costo_unitario = Decimal("0")

                    obj.unidad_costo_unitario = costo_unitario
                    obj.unidad_total = (
                            costo_unitario * unidad_cant
                    ).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)

                obj.save()  # ← obj.pk ya existe aquí

                # Guardar LOV (relaciones simples)
                for campo in campos:
                    if campo.get('tipo') in ('lov', 'multiselect') and campo.get('especial'):
                        nombre     = campo['nombre']
                        valores    = request.POST.getlist(nombre)
                        modelo_rel = campo.get('modelo_rel')
                        campo_obj  = campo.get('campo_obj')
                        campo_rel  = campo.get('campo_rel')
                        if modelo_rel and campo_obj and campo_rel:
                            for valor in valores:
                                modelo_rel.objects.create(**{
                                    campo_obj + '_id': obj.pk,
                                    campo_rel + '_id': valor,
                                })

                # Guardar lineas (relaciones con cantidad)
                for campo in campos:
                    if campo.get('tipo') == 'lineas' and campo.get('especial'):
                        nombre = campo['nombre']
                        modelo_lin = campo.get('modelo_lineas')
                        campo_obj = campo.get('campo_obj')
                        campo_prod = campo.get('campo_prod')
                        if modelo_lin and campo_obj and campo_prod:
                            modelo_lin.objects.filter(**{campo_obj + '_id': obj.pk}).delete()
                            print(f"Eliminados registros de {modelo_lin} para pk={obj.pk}")
                            productos = request.POST.getlist(nombre + '_producto')
                            print(f"Intentando crear {len(productos)} productos")
                            for producto_id in productos:
                                cantidad = request.POST.get(f'cantidad_{producto_id}', 1) or 1
                                exportacion = request.POST.get(f'exportacion_{producto_id}', 0) or 0
                                margen = request.POST.get(f'margen_{producto_id}', 0) or 0
                                print(
                                    f"Creando: cotizacion_id={obj.pk}, producto_id={producto_id}, cantidad={cantidad}, exportacion={exportacion}, margen={margen}")
                                try:
                                    obj_creado = modelo_lin.objects.create(**{
                                        campo_obj + '_id': obj.pk,
                                        campo_prod + '_id': producto_id,
                                        'cantidad': cantidad,
                                        'exportacion': exportacion,
                                        'margen': margen,
                                    })
                                    print(f"Creado OK: {obj_creado.pk}")
                                except Exception as e:
                                    print(f"Error al crear: {e}")


                # Si es página completa redirigir, si es HTMX responder 204
                if request.htmx:
                    response = HttpResponse(status=204)
                    response['HX-Trigger'] = 'refreshTabla'
                    return response
                else:
                    from django.shortcuts import redirect
                    return redirect(url_lista)  # ← redirige al reporte

            except Exception as e:
                errores['__all__'] = str(e)

        print(f"Errores: {errores}")

        context = {
            'form_titulo':  form_titulo,
            'form_campos':  campos,
            'form_action':  request.path,
            'objeto':       None,
            'errores':      errores,
            'valores_post': request.POST,
            **(extra_context or {}),
        }
        return render(request, template_form, context)

    context = {
        'form_titulo':  form_titulo,
        'form_campos':  campos,
        'form_action':  request.path,
        'objeto':       None,
        'errores':      {},
        'valores_post': {},
        **(extra_context or {}),
    }
    return render(request, template_form, context)

def form_editar(request, model, pk, campos_def, form_titulo, url_lista,
                template_form='reportes/modal_form.html',
                extra_context=None):

    queryset = extra_context.pop('queryset_editar', None) if extra_context else None
    objeto_extra = extra_context.pop('objeto_extra', None) if extra_context else None

    if objeto_extra:
        objeto = objeto_extra  # ← usar objeto con total calculado
    elif queryset:
        objeto = get_object_or_404(queryset, pk=pk) #Usar query con datos agregados
    else:
        objeto = get_object_or_404(model, pk=pk) #usar model normal

    # Filtrar campos solo_crear
    campos_def = [c for c in campos_def if not c.get('solo_crear')]
    campos = get_form_campos(campos_def, objeto)

    if request.method == 'POST':
        #print(f"POST completo: {dict(request.POST)}")
        errores = {}

        for campo in campos:
            nombre    = campo['nombre']
            requerido = campo.get('requerido', False)
            tipo      = campo.get('tipo', 'text')

            if campo.get('especial'):
                continue

            if tipo == 'file':
                continue

            valor = request.POST.get(nombre, '').strip()

            if requerido and not valor:
                errores[nombre] = 'Este campo es obligatorio.'
                continue

            if tipo == 'boolean':
                setattr(objeto, nombre, valor == 'true')
            elif tipo in ('number', 'decimal', 'number_readonly') and valor:
                try:
                    setattr(objeto, nombre, float(valor) if tipo == 'decimal' else int(valor))
                except ValueError:
                    errores[nombre] = 'Valor numérico inválido.'
            elif tipo in ('select', 'select_con_nuevo', 'select_cascada') and valor:
                valor_trigger = campo.get('valor_trigger')
                campo_fk = campo.get('campo_fk', nombre)
                if valor_trigger and valor == valor_trigger:
                    setattr(objeto, campo_fk + '_id', None)
                else:
                    setattr(objeto, campo_fk + '_id', valor)
            elif valor:
                setattr(objeto, nombre, valor)
            elif not requerido:
                setattr(objeto, nombre, None)

        if not errores:
            try:
                # ── Calcular campos readonly ──────────────────────────
                if hasattr(objeto, 'unidad_costo_unitario'):

                    objeto.unidad_descripcion = request.POST.get(
                        "unidad_descripcion", ""
                    ).strip()

                    unidad_costo = Decimal(str(request.POST.get("unidad_costo", 0) or 0))
                    unidad_exp = Decimal(str(request.POST.get("unidad_exportacion", 0) or 0))
                    unidad_margen = Decimal(str(request.POST.get("unidad_margen", 0) or 0))
                    unidad_cant = Decimal(str(request.POST.get("unidad_cantidad", 0) or 0))

                    objeto.unidad_costo = unidad_costo
                    objeto.unidad_exportacion = unidad_exp
                    objeto.unidad_margen = unidad_margen
                    objeto.unidad_cantidad = unidad_cant

                    divisor = Decimal("1") - (unidad_margen / Decimal("100"))

                    if divisor and unidad_exp:
                        costo_unitario = (
                                unidad_costo * unidad_exp / divisor
                        ).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)
                    else:
                        costo_unitario = Decimal("0")

                    objeto.unidad_costo_unitario = costo_unitario
                    objeto.unidad_total = (
                            costo_unitario * unidad_cant
                    ).quantize(Decimal("0.00"), rounding=ROUND_HALF_UP)

                objeto.save()

                # Guardar lov
                for campo in campos:
                    if campo.get('tipo') == 'lov' and campo.get('especial'):
                        nombre = campo['nombre']
                        valores = request.POST.getlist(nombre)
                        modelo_rel = campo.get('modelo_rel')
                        campo_obj = campo.get('campo_obj')
                        campo_rel = campo.get('campo_rel')

                        print(f"LOV - nombre: {nombre}, valores: {valores}, modelo_rel: {modelo_rel}")

                        if modelo_rel and campo_obj and campo_rel:
                            try:
                                modelo_rel.objects.filter(**{campo_obj + '_id': objeto.pk}).delete()
                                for valor in valores:
                                    obj_creado = modelo_rel.objects.create(**{
                                        campo_obj + '_id': objeto.pk,
                                        campo_rel + '_id': valor
                                    })
                                    print(f"Creado: {obj_creado}")
                            except Exception as e:
                                print(f"Error LOV: {e}")

                # Guardar lineas (relaciones con cantidad)
                for campo in campos:
                    if campo.get('tipo') == 'lineas' and campo.get('especial'):
                        nombre = campo['nombre']
                        modelo_lin = campo.get('modelo_lineas')
                        campo_obj = campo.get('campo_obj')
                        campo_prod = campo.get('campo_prod')
                        if modelo_lin and campo_obj and campo_prod:
                            modelo_lin.objects.filter(**{campo_obj + '_id': objeto.pk}).delete()
                            print(f"Eliminados registros de {modelo_lin} para pk={objeto.pk}")
                            productos = request.POST.getlist(nombre + '_producto')
                            print(f"Intentando crear {len(productos)} productos")
                            for producto_id in productos:
                                cantidad = request.POST.get(f'cantidad_{producto_id}', 1) or 1
                                exportacion = request.POST.get(f'exportacion_{producto_id}', 0) or 0
                                margen = request.POST.get(f'margen_{producto_id}', 0) or 0
                                print(
                                    f"Creando: cotizacion_id={objeto.pk}, producto_id={producto_id}, cantidad={cantidad}, exportacion={exportacion}, margen={margen}")
                                try:
                                    obj_creado = modelo_lin.objects.create(**{
                                        campo_obj + '_id': objeto.pk,
                                        campo_prod + '_id': producto_id,
                                        'cantidad': cantidad,
                                        'exportacion': exportacion,
                                        'margen': margen,
                                    })
                                    print(f"Creado OK: {obj_creado.pk}")
                                except Exception as e:
                                    print(f"Error al crear: {e}")

                # Si es página completa redirigir, si es HTMX responder 204
                if request.htmx:
                    response = HttpResponse(status=204)
                    response['HX-Trigger'] = 'refreshTabla'
                    return response
                else:
                    from django.shortcuts import redirect
                    return redirect(url_lista)  # ← redirige al reporte
            except Exception as e:
                errores['__all__'] = str(e)

        context = {
            'form_titulo': form_titulo,
            'form_campos': campos,
            'form_action': request.path,
            'objeto':      objeto,
            'errores':     errores,
            **(extra_context or {}),
        }
        return render(request, template_form, context)

    context = {
        'form_titulo': f'Editar — {objeto}',
        'form_campos': campos,
        'form_action': request.path,
        'objeto':      objeto,
        'errores':     {},
        **(extra_context or {}),
    }
    return render(request, template_form, context)


def form_eliminar(request, model, pk):
    """Vista genérica para eliminar un registro vía HTMX."""
    objeto = get_object_or_404(model, pk=pk)
    if request.method == 'POST':
        objeto.delete()
        response = HttpResponse(status=204)
        response['HX-Trigger'] = 'refreshTabla'
        return response
    return HttpResponse(status=405)

def exportar_csv(request, queryset, columnas, nombre_archivo):
    """
    Vista genérica para exportar cualquier queryset a CSV.
    queryset:      el queryset a exportar
    columnas:      lista de dicts con 'campo' y 'label' (las mismas del reporte)
    nombre_archivo: nombre del archivo sin extensión
    """
    response = HttpResponse(content_type='text/csv; charset=utf-8')
    response['Content-Disposition'] = f'attachment; filename="{nombre_archivo}.csv"'
    response.write('\ufeff')  # BOM para que Excel abra UTF-8 correctamente

    writer = csv.writer(response)

    # Encabezados
    writer.writerow([col['label'] for col in columnas])

    # Filas
    for obj in queryset:
        fila = []
        for col in columnas:
            valor = getattr(obj, col['campo'], '—')
            if valor is None:
                valor = '—'
            fila.append(str(valor))
        writer.writerow(fila)

    return response