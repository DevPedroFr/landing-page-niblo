(function () {
  'use strict';

  /* ── Cookie banner ── */
  document.addEventListener('DOMContentLoaded', function () {
    setTimeout(function () {
      if (!localStorage.getItem('cookiesAccepted')) {
        var banner = document.createElement('div');
        banner.id = 'cookie-banner';
        banner.className = 'cookie-banner';

        var text = document.createTextNode(
          'Este site utiliza cookies para melhorar sua experiência. Ao continuar navegando, você concorda com nossa '
        );
        var link = document.createElement('a');
        link.href = 'politica-de-privacidade.html';
        link.className = 'cookie-link';
        link.textContent = 'Política de Privacidade';
        var dot = document.createTextNode('.');

        var btn = document.createElement('button');
        btn.id = 'accept-cookies';
        btn.className = 'cookie-accept-btn';
        btn.textContent = 'Aceitar';

        banner.appendChild(text);
        banner.appendChild(link);
        banner.appendChild(dot);
        banner.appendChild(btn);
        document.body.appendChild(banner);

        btn.addEventListener('click', function () {
          localStorage.setItem('cookiesAccepted', 'true');
          banner.remove();
        });
      }
    }, 500);
  });

  /* ── Event delegation for data-action ── */
  document.addEventListener('click', function (e) {
    var el = e.target.closest('[data-action]');
    if (!el) return;
    var action = el.dataset.action;
    if (action === 'toggle-menu') toggleMenu();
    else if (action === 'toggle-wa') toggleWA();
    else if (action === 'close-exit') closeExit();
  });

  /* ── Close nav when a nav link is clicked (mobile) ── */
  document.addEventListener('DOMContentLoaded', function () {
    document.querySelectorAll('.nav-links a').forEach(function (link) {
      link.addEventListener('click', function () {
        var links = document.querySelector('.nav-links');
        if (links) links.classList.remove('nav-open');
      });
    });
  });

  /* ── Scroll reveal ── */
  var revealObs = new IntersectionObserver(function (entries) {
    entries.forEach(function (e, i) {
      if (e.isIntersecting) {
        setTimeout(function () { e.target.classList.add('visible'); }, i * 80);
        revealObs.unobserve(e.target);
      }
    });
  }, { threshold: 0.1 });
  document.querySelectorAll('.reveal').forEach(function (el) {
    revealObs.observe(el);
  });

  /* ── Counter animation ── */
  function animateCounter(el) {
    var target = parseInt(el.dataset.target, 10);
    if (!target) return;
    var prefix = target > 100 ? '+' : '';
    var step = target / (1800 / 16);
    var current = 0;
    var timer = setInterval(function () {
      current += step;
      if (current >= target) { current = target; clearInterval(timer); }
      el.textContent = prefix + Math.floor(current).toLocaleString('pt-BR');
    }, 16);
  }
  var statsEl = document.getElementById('stats');
  if (statsEl) {
    var statObs = new IntersectionObserver(function (entries) {
      entries.forEach(function (e) {
        if (e.isIntersecting) {
          e.target.querySelectorAll('[data-target]').forEach(animateCounter);
          statObs.unobserve(e.target);
        }
      });
    }, { threshold: 0.5 });
    statObs.observe(statsEl);
  }

  /* ── WhatsApp toggle ── */
  function toggleWA() {
    var popup = document.getElementById('wpPopup');
    if (popup) popup.classList.toggle('open');
  }

  /* ── Exit intent ── */
  var exitShown = false;
  function maybeShowExit() {
    if (exitShown) return;
    var count = parseInt(sessionStorage.getItem('tabSwitchCount') || '0', 10) + 1;
    sessionStorage.setItem('tabSwitchCount', count);
    if (count % 3 === 0) {
      exitShown = true;
      var ep = document.getElementById('exitPopup');
      if (ep) ep.classList.add('show');
    }
  }
  document.addEventListener('visibilitychange', function () {
    if (document.visibilityState === 'hidden') maybeShowExit();
  });
  function closeExit() {
    exitShown = false;
    var ep = document.getElementById('exitPopup');
    if (ep) ep.classList.remove('show');
  }

  /* ── Mobile menu ── */
  function toggleMenu() {
    var links = document.querySelector('.nav-links');
    if (links) links.classList.toggle('nav-open');
  }

  /* ── Navbar scroll ── */
  window.addEventListener('scroll', function () {
    var nav = document.getElementById('navbar');
    if (!nav) return;
    nav.classList.toggle('nav-scrolled', window.scrollY > 50);
  });

})();
