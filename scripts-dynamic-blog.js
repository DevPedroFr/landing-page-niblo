(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var latestGrid = document.getElementById('latest-posts-grid');
    if (!latestGrid) return;

    function buildCard(post) {
      var card = document.createElement('a');
      card.href = post.url;
      card.className = 'blog-card reveal visible';

      var image = document.createElement('div');
      image.className = 'blog-img';
      image.style.backgroundImage = 'url("' + post.cover_image + '")';
      image.style.backgroundPosition = 'center';
      image.style.backgroundSize = 'cover';
      image.style.backgroundRepeat = 'no-repeat';

      var footer = document.createElement('div');
      footer.className = 'blog-footer';

      var label = document.createElement('span');
      label.textContent = 'Clique e saiba mais';

      var arrow = document.createElement('span');
      arrow.className = 'arrow-icon';
      arrow.textContent = '→';

      footer.appendChild(label);
      footer.appendChild(arrow);
      card.appendChild(image);
      card.appendChild(footer);
      return card;
    }

    fetch('/api/public/posts?limit=4')
      .then(function (response) {
        if (!response.ok) {
          throw new Error('Nao foi possivel carregar os posts');
        }
        return response.json();
      })
      .then(function (posts) {
        if (!Array.isArray(posts) || !posts.length) return;
        latestGrid.replaceChildren.apply(latestGrid, posts.map(buildCard));
      })
      .catch(function () {
      });
  });
})();