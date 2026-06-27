'use strict';

/* ─── Modal eliminar ─────────────────────────────────────── */
function confirmarEliminar(url, nombre) {
  document.getElementById('modal-item-nombre').textContent = nombre;
  document.getElementById('modal-form-eliminar').action = url;
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