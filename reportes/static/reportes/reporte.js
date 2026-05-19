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