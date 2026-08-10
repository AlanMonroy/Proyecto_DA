'use strict';

/* ─── Tab switching ──────────────────────────────────────────────── */
function switchTab(target) {
  const paneRegister = document.getElementById('pane-register');
  const paneLogin    = document.getElementById('pane-login');
  const btnRegister  = document.getElementById('btn-register');
  const btnLogin     = document.getElementById('btn-login');
  const indicator    = document.querySelector('.tab-indicator');

  if (target === 'login') {
    paneRegister.classList.add('hidden');
    paneLogin.classList.remove('hidden');
    paneLogin.style.animation = 'none';
    void paneLogin.offsetWidth;           // reflow para re-disparar animación
    paneLogin.style.animation = '';

    btnRegister.classList.remove('active');
    btnLogin.classList.add('active');
    indicator.classList.add('right');
  } else {
    paneLogin.classList.add('hidden');
    paneRegister.classList.remove('hidden');
    paneRegister.style.animation = 'none';
    void paneRegister.offsetWidth;
    paneRegister.style.animation = '';

    btnLogin.classList.remove('active');
    btnRegister.classList.add('active');
    indicator.classList.remove('right');
  }
}

/* ─── Bind tab buttons ──────────────────────────────────────────── */
document.querySelectorAll('.tab-btn, .link-btn').forEach(function (btn) {
  btn.addEventListener('click', function () {
    switchTab(this.dataset.target);
  });
});

/* ─── Password visibility toggle ────────────────────────────────── */
document.querySelectorAll('.toggle-pw').forEach(function (btn) {
  btn.addEventListener('click', function () {
    var inputId = this.dataset.target;
    var input   = document.getElementById(inputId);
    if (!input) return;

    var isHidden = input.type === 'password';
    input.type   = isHidden ? 'text' : 'password';

    /* swap icon: ojo abierto / ojo tachado */
    var svgOpen  = '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>';
    var svgClosed = '<path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/>';
    var svg = this.querySelector('svg');
    if (svg) svg.innerHTML = isHidden ? svgClosed : svgOpen;

    this.setAttribute('aria-label', isHidden ? 'Ocultar contraseña' : 'Mostrar contraseña');
  });
});