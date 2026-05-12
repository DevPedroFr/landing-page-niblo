(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var body = document.body;
    if (!body || !body.dataset.pageKey) return;

    fetch('/api/public/site-content/' + encodeURIComponent(body.dataset.pageKey))
      .then(function (response) {
        if (!response.ok) {
          throw new Error('Falha ao carregar conteúdo gerenciado');
        }
        return response.json();
      })
      .then(function (payload) {
        var content = payload && payload.content ? payload.content : {};
        document.querySelectorAll('[data-content-key]').forEach(function (element) {
          var key = element.dataset.contentKey;
          if (!Object.prototype.hasOwnProperty.call(content, key)) return;
          if ((element.dataset.contentMode || 'text') === 'html') {
            element.innerHTML = content[key] || '';
            return;
          }
          element.textContent = content[key] || '';
        });
      })
      .catch(function () {
      });
  });
})();