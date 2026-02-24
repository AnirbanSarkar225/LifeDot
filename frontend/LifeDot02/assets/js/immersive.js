/* LifeDot Immersive Interactions
   - Cursor (desktop fine pointer)
   - Page transitions for internal links
   - Small utilities (reduced motion guard)
*/

(function () {
  const prefersReducedMotion = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  const isFinePointer = window.matchMedia && window.matchMedia('(hover: hover) and (pointer: fine)').matches;

  function ensureTransitionOverlay() {
    if (document.querySelector('.ld-transition')) return;
    const el = document.createElement('div');
    el.className = 'ld-transition';
    document.body.appendChild(el);
  }

  function initPageTransitions() {
    ensureTransitionOverlay();
    const overlay = document.querySelector('.ld-transition');
    if (!overlay) return;

    document.addEventListener('click', (e) => {
      const a = e.target && e.target.closest ? e.target.closest('a') : null;
      if (!a) return;

      const href = a.getAttribute('href') || '';
      const target = a.getAttribute('target');

      if (!href || href.startsWith('#')) return;
      if (href.startsWith('mailto:') || href.startsWith('tel:')) return;
      if (target === '_blank') return;
      if (e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;

      // Same-origin (static file) navigation only
      e.preventDefault();
      overlay.classList.add('is-active');

      window.setTimeout(() => {
        window.location.href = href;
      }, 440);
    }, { capture: true });

    // Fade overlay away on load (if back/forward)
    window.addEventListener('pageshow', () => {
      overlay.classList.remove('is-active');
    });
  }

  function initCursor() {
    if (prefersReducedMotion || !isFinePointer) return;

    let cursor = document.querySelector('.cursor') || document.querySelector('.cursor-dot');
    let ring = document.querySelector('.cursor-ring');

    if (!cursor) {
      cursor = document.createElement('div');
      cursor.className = 'cursor';
      cursor.id = 'cursor';
      document.body.appendChild(cursor);
    }

    if (!ring) {
      ring = document.createElement('div');
      ring.className = 'cursor-ring';
      ring.id = 'cursorRing';
      document.body.appendChild(ring);
    }

    let mx = window.innerWidth / 2;
    let my = window.innerHeight / 2;
    let rx = mx;
    let ry = my;

    const setCursor = (x, y) => {
      cursor.style.left = x + 'px';
      cursor.style.top = y + 'px';
    };

    const setRing = (x, y) => {
      ring.style.left = x + 'px';
      ring.style.top = y + 'px';
    };

    document.addEventListener('mousemove', (e) => {
      mx = e.clientX;
      my = e.clientY;
      setCursor(mx, my);
    }, { passive: true });

    function loop() {
      rx += (mx - rx) * 0.14;
      ry += (my - ry) * 0.14;
      setRing(rx, ry);
      requestAnimationFrame(loop);
    }
    loop();

    const interactive = 'a, button, input, textarea, select, [data-cursor], .feature-card';
    document.querySelectorAll(interactive).forEach((el) => {
      el.addEventListener('mouseenter', () => {
        ring.classList.add('hover');
        const accent = el.getAttribute('data-cursor-accent');
        if (accent) ring.setAttribute('data-accent', accent);
      });
      el.addEventListener('mouseleave', () => {
        ring.classList.remove('hover');
        ring.removeAttribute('data-accent');
      });
    });
  }

  function ready(fn) {
    if (document.readyState === 'loading') {
      document.addEventListener('DOMContentLoaded', fn);
    } else {
      fn();
    }
  }

  ready(() => {
    initPageTransitions();
    initCursor();
  });
})();

