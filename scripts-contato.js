// scripts-contato.js
// Cookie banner for contato.html (static HTML element approach)
document.addEventListener('DOMContentLoaded', function () {
  if (!localStorage.getItem('cookiesAccepted')) {
    var el = document.getElementById('cookie-banner');
    if (el) el.removeAttribute('hidden');
  }
  var btn = document.getElementById('accept-cookies');
  if (btn) {
    btn.addEventListener('click', function () {
      localStorage.setItem('cookiesAccepted', 'true');
      var el = document.getElementById('cookie-banner');
      if (el) el.setAttribute('hidden', '');
    });
  }
