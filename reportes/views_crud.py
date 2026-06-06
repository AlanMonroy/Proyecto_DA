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
    return campos


def form_crear(request, model, campos_def, form_titulo, url_lista,
               template_form='reportes/modal_form.html',
               template_lista=None, extra_context=None):
    """
    Vista genérica para crear un registro vía HTMX.

    model:       clase del modelo Django
    campos_def:  lista de dicts con la definición de campos
    form_titulo: título del modal
    url_lista:   nombre de la URL del reporte (para refrescar la tabla)
    """
    print(f"Method: {request.method}, Path: {request.path}")
    campos = get_form_campos(campos_def)

    if request.method == 'POST':
        errores = {}
        datos   = {}

        for campo in campos:
            nombre    = campo['nombre']
            requerido = campo.get('requerido', False)
            tipo      = campo.get('tipo', 'text')

            valor = request.POST.get(nombre, '').strip()

            if requerido and not valor:
                errores[nombre] = 'Este campo es obligatorio.'
                continue

            # Convertir según tipo
            if tipo == 'boolean':
                datos[nombre] = valor == 'true'
            elif tipo in ('number', 'decimal') and valor:
                try:
                    datos[nombre] = float(valor) if tipo == 'decimal' else int(valor)
                except ValueError:
                    errores[nombre] = 'Valor numérico inválido.'
            elif tipo == 'select' and valor:
                # Para ForeignKey pasamos el ID
                campo_fk = campo.get('campo_fk', nombre)
                datos[campo_fk] = valor
            elif valor:
                datos[nombre] = valor

        if not errores:
            try:
                obj = model(**datos)
                obj.save()
                print(f"Guardado: {obj}")  # ← agrega esto
                response = HttpResponse(status=204)
                response['HX-Trigger'] = 'refreshTabla'
                return response
            except Exception as e:
                print(f"Error al guardar: {e}")  # ← agrega esto
                errores['__all__'] = str(e)

        print(f"Errores: {errores}")

        # Si hay errores, re-renderiza el modal con errores
        context = {
            'form_titulo':  form_titulo,
            'form_campos':  campos,
            'form_action':  request.path,
            'objeto':       None,
            'errores':      errores,
            **(extra_context or {}),
        }
        return render(request, template_form, context)

    # GET — mostrar modal
    context = {
        'form_titulo': form_titulo,
        'form_campos': campos,
        'form_action': request.path,
        'objeto':      None,
        'errores':     {},
        'valores_post': request.POST,  #guardar los valores llenados para no volver a llenar
        **(extra_context or {}),
    }
    return render(request, template_form, context)


def form_editar(request, model, pk, campos_def, form_titulo, url_lista,
                template_form='reportes/modal_form.html',
                extra_context=None):
    """Vista genérica para editar un registro vía HTMX."""
    objeto = get_object_or_404(model, pk=pk)
    campos = get_form_campos(campos_def, objeto)

    if request.method == 'POST':
        errores = {}

        for campo in campos:
            nombre    = campo['nombre']
            requerido = campo.get('requerido', False)
            tipo      = campo.get('tipo', 'text')

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