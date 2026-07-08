"""
views_crud.py — Vistas genéricas HTMX para CRUD
Importa y usa en cualquier app de reportes.
"""
from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages


def get_form_campos(campos, objeto=None):
    """
    Procesa los campos del formulario y carga opciones de ForeignKey.
    campos: lista de dicts definidos en la vista
    objeto: instancia del modelo (None si es creación)
    """
    for campo in campos:
        # Cargar opciones de select desde queryset
        if campo.get('tipo') == 'select' and 'queryset' in campo:
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
                        'costo': l.producto.costo,
                        'cantidad': l.cantidad,
                        'subtotal': l.producto.costo * l.cantidad,
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
            elif tipo in ('number', 'decimal') and valor:
                try:
                    datos[nombre] = float(valor) if tipo == 'decimal' else int(valor)
                except ValueError:
                    errores[nombre] = 'Valor numérico inválido.'
            elif tipo == 'select' and valor:
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
            try:
                obj = model(**datos)
                if hasattr(obj, 'activo') and 'activo' not in datos:
                    obj.activo = True
                if p1:
                    obj.set_password(p1)
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
                        nombre     = campo['nombre']
                        modelo_lin = campo.get('modelo_lineas')
                        campo_obj  = campo.get('campo_obj')
                        campo_prod = campo.get('campo_prod')
                        if modelo_lin and campo_obj and campo_prod:
                            productos = request.POST.getlist(nombre + '_producto')
                            for producto_id in productos:
                                cantidad = request.POST.get(f'cantidad_{producto_id}', 1)
                                modelo_lin.objects.create(**{
                                    campo_obj + '_id': obj.pk,
                                    campo_prod + '_id': producto_id,
                                    'cantidad': cantidad,
                                })

                response = HttpResponse(status=204)
                response['HX-Trigger'] = 'refreshTabla'
                return response
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
    if queryset:
        objeto = get_object_or_404(queryset, pk=pk) #Usar query con datos agregados
    else:
        objeto = get_object_or_404(model, pk=pk) #usar model normal

    # Filtrar campos solo_crear
    campos_def = [c for c in campos_def if not c.get('solo_crear')]
    campos = get_form_campos(campos_def, objeto)

    if request.method == 'POST':
        errores = {}

        for campo in campos:
            nombre    = campo['nombre']
            requerido = campo.get('requerido', False)
            tipo      = campo.get('tipo', 'text')

            if campo.get('especial'):
                continue

            valor = request.POST.get(nombre, '').strip()

            if requerido and not valor:
                errores[nombre] = 'Este campo es obligatorio.'
                continue

            if tipo == 'boolean':
                setattr(objeto, nombre, valor == 'true')
            elif tipo in ('number', 'decimal') and valor:
                try:
                    setattr(objeto, nombre, float(valor) if tipo == 'decimal' else int(valor))
                except ValueError:
                    errores[nombre] = 'Valor numérico inválido.'
            elif tipo == 'select' and valor:
                campo_fk = campo.get('campo_fk', nombre)
                setattr(objeto, campo_fk + '_id', valor)
            elif valor:
                setattr(objeto, nombre, valor)
            elif not requerido:
                setattr(objeto, nombre, None)

        if not errores:
            try:
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
                            productos = request.POST.getlist(nombre + '_producto')
                            for producto_id in productos:
                                cantidad = request.POST.get(f'cantidad_{producto_id}', 1)
                                modelo_lin.objects.create(**{
                                    campo_obj + '_id': objeto.pk,
                                    campo_prod + '_id': producto_id,
                                    'cantidad': cantidad,
                                })

                response = HttpResponse(status=204)
                response['HX-Trigger'] = 'refreshTabla'
                return response
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