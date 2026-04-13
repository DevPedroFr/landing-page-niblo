// scripts-sobre.js
// COOKIES BANNER UNIVERSAL
window.addEventListener('DOMContentLoaded', function() {
  setTimeout(function() {
    if (!localStorage.getItem('cookiesAccepted')) {
      var banner = document.createElement('div');
      banner.id = 'cookie-banner';
      banner.style = 'position:fixed;bottom:0;left:0;width:100%;background:#222;color:#fff;padding:18px 12px;z-index:9999;text-align:center;font-size:1rem;';
      banner.innerHTML = 'Este site utiliza cookies para melhorar sua experiência. Ao continuar navegando, você concorda com nossa <a href="termos-de-uso.txt" target="_blank" style="color:#ffd700;text-decoration:underline;">Política de Cookies</a>.' +
        '<button id="accept-cookies" style="margin-left:18px;background:#ffd700;color:#222;border:none;padding:8px 18px;border-radius:4px;cursor:pointer;font-weight:600;">Aceitar</button>';
      document.body.appendChild(banner);
      document.getElementById('accept-cookies').onclick = function() {
        localStorage.setItem('cookiesAccepted', 'true');
        banner.style.display = 'none';
      };
    }
  }, 500);

  // Gira os cards MVV ao toque/click em dispositivos móveis
  function isMobile() {
    return window.innerWidth <= 1024;
  }
  var cards = document.querySelectorAll('.mvv-card');
  cards.forEach(function(card) {
    card.addEventListener('click', function() {
      if (isMobile()) {
        card.classList.toggle('mvv-flip');
      }
    });
  });
});
