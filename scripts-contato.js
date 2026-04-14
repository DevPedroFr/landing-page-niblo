// scripts-contato.js
// Funções JS migradas do inline de contato.html

// MENU MOBILE
function toggleMenu() {
  const navLinks = document.getElementById('navLinks');
  navLinks.classList.toggle('mobile-open');
}

// WHATSAPP TOGGLE
function toggleWA() {
  const popup = document.getElementById('wpPopup');
  popup.classList.toggle('open');
}

// FECHAR EXIT POPUP
function closeExit() {
  document.getElementById('exitPopup').classList.remove('show');
}

// EXIT INTENT
let exitShown = false;
function maybeShowExit() {
  if (exitShown) return;
  let count = parseInt(sessionStorage.getItem('tabSwitchCount') || '0') + 1;
  sessionStorage.setItem('tabSwitchCount', count);
  if (count % 3 === 0) {
    exitShown = true;
    document.getElementById('exitPopup').classList.add('show');
  }
}
document.addEventListener('visibilitychange', function() {
  if (document.visibilityState === 'hidden') {
    maybeShowExit();
  }
});

// NAVBAR SCROLL
window.addEventListener('scroll', function() {
  const nav = document.getElementById('navbar');
  if (window.scrollY > 50) {
    nav.style.background = 'rgba(255,255,255,0.98)';
    nav.style.boxShadow = '0 2px 20px rgba(0,0,0,0.06)';
  } else {
    nav.style.background = 'rgba(255,255,255,0.85)';
    nav.style.boxShadow = 'none';
  }
});

// FECHAR MENU AO CLICAR EM LINK
window.addEventListener('DOMContentLoaded', function() {
  document.querySelectorAll('.nav-links a').forEach(link => {
    link.addEventListener('click', () => {
      document.getElementById('navLinks').classList.remove('mobile-open');
    });
  });

  // GOOGLE FORMS MODAL
  // O formulário de contato agora é gerenciado via Google Forms popup (ver contato.html)
});
