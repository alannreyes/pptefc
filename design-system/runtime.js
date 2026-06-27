/* ==========================================================================
   EFC Deck — Runtime
   --------------------------------------------------------------------------
   Navegación con teclas (↑↓←→ Page Up/Down Home End Space).
   Auto-play del video de fondo (con fallback a click si el navegador bloquea).
   Personalización por query string: ?client=NOMBRE&fecha=DD-mes
   ========================================================================== */
(function () {
  'use strict';

  const slides = document.querySelectorAll('.slide');
  if (slides.length === 0) return;

  function currentIdx() {
    const y = window.scrollY + window.innerHeight * 0.4;
    for (let i = slides.length - 1; i >= 0; i--) {
      if (slides[i].offsetTop <= y) return i;
    }
    return 0;
  }

  function go(idx) {
    idx = Math.max(0, Math.min(slides.length - 1, idx));
    slides[idx].scrollIntoView({ behavior: 'smooth' });
  }

  // Navegación con teclado
  window.addEventListener('keydown', function (e) {
    // Ignorar si el foco está en input/textarea
    if (e.target && (e.target.tagName === 'INPUT' || e.target.tagName === 'TEXTAREA')) return;
    const cur = currentIdx();
    if (['ArrowDown', 'ArrowRight', 'PageDown', ' '].includes(e.key)) {
      e.preventDefault(); go(cur + 1);
    } else if (['ArrowUp', 'ArrowLeft', 'PageUp'].includes(e.key)) {
      e.preventDefault(); go(cur - 1);
    } else if (e.key === 'Home') {
      e.preventDefault(); go(0);
    } else if (e.key === 'End') {
      e.preventDefault(); go(slides.length - 1);
    }
  });

  // Asegurar autoplay del video (algunos navegadores bloquean hasta primer click)
  const video = document.querySelector('.bg-video');
  if (video) {
    video.play().catch(function () {
      document.body.addEventListener('click', function () { video.play(); }, { once: true });
    });
  }

  // Personalización por query string (ej. ?client=Nombre+del+Cliente)
  const params = new URLSearchParams(window.location.search);
  const client = params.get('client');
  const fecha = params.get('fecha');

  if (client) {
    document.querySelectorAll('[data-client]').forEach(function (el) {
      el.textContent = client;
    });
  }
  if (fecha) {
    document.querySelectorAll('[data-fecha]').forEach(function (el) {
      el.textContent = fecha;
    });
  }
})();
