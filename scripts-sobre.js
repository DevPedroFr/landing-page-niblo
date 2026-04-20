// scripts-sobre.js
// MVV cards flip on mobile — specific to sobre.html
document.addEventListener('DOMContentLoaded', function () {
  function isMobile() { return window.innerWidth <= 1024; }
  document.querySelectorAll('.mvv-card').forEach(function (card) {
    card.addEventListener('click', function () {
      if (isMobile()) card.classList.toggle('mvv-flip');
  });
});
