'use strict';

/* ─── Modal eliminar ─────────────────────────────────────── */
/*function confirmarEliminar(url, nombre) {
  document.getElementById('modal-item-nombre').textContent = nombre;
  document.getElementById('modal-form-eliminar').action = url;
  document.getElementById('modal-eliminar').classList.add('visible');
}*/
function confirmarEliminar(url, nombre) {
  document.getElementById('modal-item-nombre').textContent = nombre;
  const form = document.getElementById('modal-form-eliminar');
  form.setAttribute('hx-post', url);
  htmx.process(form);  // ← re-procesa HTMX en el form
  document.getElementById('modal-eliminar').classList.add('visible');
}

function cerrarModal() {
  document.getElementById('modal-eliminar').classList.remove('visible');
}

// Cerrar con click fuera del modal
document.getElementById('modal-eliminar').addEventListener('click', function (e) {
  if (e.target === this) cerrarModal();
});

// Cerrar con Escape
document.addEventListener('keydown', function (e) {
  if (e.key === 'Escape') cerrarModal();
});

/* ─── Limpiar búsqueda ───────────────────────────────────── */
function clearSearch() {
  const form  = document.getElementById('filtros-form');
  const input = form.querySelector('input[name="q"]');
  if (input) { input.value = ''; form.submit(); }
}

/* ─── Cambiar registros por página ──────────────────────── */
function changePerPage(value) {
  const url    = new URL(window.location.href);
  url.searchParams.set('per_page', value);
  url.searchParams.set('page', '1');
  window.location.href = url.toString();
}

/* ─── Submit automático al escribir (debounce) ───────────── */
const inputBusqueda = document.querySelector('.input-busqueda');
if (inputBusqueda) {
  let timer;
  inputBusqueda.addEventListener('input', function () {
    clearTimeout(timer);
    timer = setTimeout(function () {
      document.getElementById('filtros-form').submit();
    }, 500);
  });
}

/* ─── LOV ─────────────────────────────────────────────────── */
function lovBuscar(nombre, query, total) {
  const dropdown = document.getElementById('lov-dropdown-' + nombre);
  const opciones = dropdown.querySelectorAll('.lov-opcion');
  const q = query.toLowerCase().trim();

  let visibles = 0;
  opciones.forEach(function(op) {
    const label = op.dataset.label.toLowerCase();
    const yaSeleccionado = op.classList.contains('ya-seleccionado');
    if (!yaSeleccionado && (q === '' || label.includes(q))) {
      op.classList.remove('oculto');
      visibles++;
    } else if (!yaSeleccionado) {
      op.classList.add('oculto');
    }
  });

  dropdown.classList.toggle('visible', visibles > 0);
}

function lovSeleccionar(nombre, valor, label, el) {
  const tags     = document.getElementById('lov-tags-' + nombre);
  const input    = document.querySelector('#lov-' + nombre + ' .lov-input');
  const dropdown = document.getElementById('lov-dropdown-' + nombre);

  // Evitar duplicados
  if (tags.querySelector('[data-valor="' + valor + '"]')) return;

  // Crear tag
  const tag = document.createElement('span');
  tag.className = 'lov-tag';
  tag.dataset.valor = valor;
  tag.innerHTML = `
    ${label}
    <button type="button" onclick="lovRemove('${nombre}', '${valor}', this)">×</button>
    <input type="hidden" name="${nombre}" value="${valor}" />
  `;
  tags.appendChild(tag);

  // Marcar opción como ya seleccionada
  el.classList.add('ya-seleccionado');

  // Limpiar input y cerrar dropdown
  input.value = '';
  dropdown.classList.remove('visible');
}

function lovRemove(nombre, valor, btn) {
  const tag      = btn.closest('.lov-tag');
  const dropdown = document.getElementById('lov-dropdown-' + nombre);

  // Desmarcar opción en dropdown
  const opcion = dropdown.querySelector('[data-valor="' + valor + '"]');
  if (opcion) opcion.classList.remove('ya-seleccionado');

  tag.remove();
}

// Cerrar dropdown al hacer click fuera
document.addEventListener('click', function(e) {
  document.querySelectorAll('.lov-dropdown.visible').forEach(function(d) {
    if (!d.closest('.lov-input-wrap').contains(e.target)) {
      d.classList.remove('visible');
    }
  });
});

/* ─── Lineas ─────────────────────────────────────────────── */
function lineasBuscar(nombre, query) {
  const dropdown = document.getElementById('lineas-dropdown-' + nombre);
  const opciones = dropdown.querySelectorAll('.lov-opcion');
  const q = query.toLowerCase().trim();
  const body = document.getElementById('lineas-body-' + nombre);
  const yaAgregados = Array.from(body.querySelectorAll('.linea-row'))
    .map(r => r.dataset.productoId);

  let visibles = 0;
  opciones.forEach(function(op) {
    const yaEsta = yaAgregados.includes(op.dataset.id);
    const coincide = q === '' || op.dataset.nombre.toLowerCase().includes(q);
    if (!yaEsta && coincide) {
      op.classList.remove('oculto');
      visibles++;
    } else {
      op.classList.add('oculto');
    }
  });
  dropdown.classList.toggle('visible', visibles > 0);
}

function lineasAgregar(nombre, productoId, productoNombre, costo, el) {
  const body     = document.getElementById('lineas-body-' + nombre);
  const dropdown = document.getElementById('lineas-dropdown-' + nombre);
  const input    = dropdown.closest('.lov-input-wrap').querySelector('.lov-input');

  const tr = document.createElement('tr');
  tr.className = 'linea-row';
  tr.dataset.productoId = productoId;
  tr.innerHTML = `
    <td>${productoNombre}</td>
    <td class="linea-costo">$${costo}</td>
    <td>
      <input type="number" class="linea-cantidad"
             name="cantidad_${productoId}"
             value="1" min="1"
             onchange="lineasActualizar('${nombre}')" />
    </td>
    <td>
      <input type="number" class="linea-exportacion"
             name="exportacion_${productoId}"
             value="0" min="0"
             onchange="lineasActualizar('${nombre}')" />
    </td>
    <td>
      <input type="number" class="linea-margen"
             name="margen_${productoId}"
             value="0" min="0"
             onchange="lineasActualizar('${nombre}')" />
    </td>
    <td class="linea-costo-venta">$0</td>
    <td class="linea-subtotal">$${costo}</td>
    <td>
      <button type="button" class="linea-eliminar"
              onclick="lineasEliminar('${nombre}', this)">×</button>
    </td>
    <input type="hidden" name="${nombre}_producto" value="${productoId}" />
  `;
  body.appendChild(tr);

  el.classList.add('oculto');
  input.value = '';
  dropdown.classList.remove('visible');
  lineasActualizar(nombre);
}

function lineasEliminar(nombre, btn) {
  const row = btn.closest('.linea-row');
  const productoId = row.dataset.productoId;
  const dropdown = document.getElementById('lineas-dropdown-' + nombre);
  const op = dropdown.querySelector(`[data-id="${productoId}"]`);
  if (op) op.classList.remove('oculto');
  row.remove();
  lineasActualizar(nombre);
}

function formatoMoneda(valor) {
    return '$' + valor.toLocaleString('es-MX', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
    });
}

function redondear(valor, decimales) {
  return Math.round(valor * Math.pow(10, decimales)) / Math.pow(10, decimales);
}

function lineasActualizar(nombre) {
  const body  = document.getElementById('lineas-body-' + nombre);
  const total = document.getElementById('lineas-total-' + nombre);
  let suma = 0;

  body.querySelectorAll('.linea-row').forEach(function(row) {
    const costo       = parseFloat(row.querySelector('.linea-costo').textContent.replace('$','').replace(',','')) || 0;
    const cantidad    = parseInt(row.querySelector('.linea-cantidad').value)      || 0;
    const exportacion = parseFloat(row.querySelector('.linea-exportacion').value) || 0;
    const margen      = parseFloat(row.querySelector('.linea-margen').value)      || 0;

    const divisor        = 1 - (margen / 100);
    const costo_unitario = (divisor !== 0 && exportacion !== 0)
      ? redondear((costo * exportacion) / divisor, 2)  // ← redondear por línea
      : 0;

    const subtotal = redondear(costo_unitario * cantidad, 2);  // ← redondear por línea

    row.querySelector('.linea-costo-venta').textContent = formatoMoneda(costo_unitario);
    row.querySelector('.linea-subtotal').textContent    = formatoMoneda(subtotal);
    suma = redondear(suma + subtotal, 2);  // ← redondear la suma acumulada
  });

  if (total) total.textContent = formatoMoneda(suma);
}

/*function previewImagen(input, previewId) {
    const preview = document.getElementById(previewId);

    if (input.files && input.files[0]) {
        const reader = new FileReader();

        reader.onload = function(e) {
            preview.src = e.target.result;
        };

        reader.readAsDataURL(input.files[0]);
    }
}*/

function previewImagen(input) {

    const uploader = input.closest(".image-uploader");

    const preview = uploader.querySelector("img");
    const message = uploader.querySelector(".upload-message");
    const fileName = uploader.querySelector(".file-name");


    if (input.files && input.files[0]) {

        const file = input.files[0];


        if (!file.type.startsWith("image/")) {

            alert("Seleccione una imagen válida");

            input.value = "";

            return;
        }


        const reader = new FileReader();


        reader.onload = function(e) {

            preview.src = e.target.result;

            preview.classList.remove("hidden");

            message.classList.add("hidden");

            fileName.textContent = file.name;

        };


        reader.readAsDataURL(file);

    }

}

function toggleCampoOculto(select) {
  const campoOculto  = select.dataset.campoOculto;
  const valorTrigger = select.dataset.valorTrigger;
  const div          = document.getElementById('campo-' + campoOculto);
  const input        = div ? div.querySelector('input') : null;
  console.log('campoOculto:', campoOculto);
  console.log('div encontrado:', div);

  if (select.value === valorTrigger) {
    div.style.display = 'block';
    if (input) input.required = true;
  } else {
    div.style.display = 'none';
    if (input) { input.required = false; input.value = ''; }
  }
}