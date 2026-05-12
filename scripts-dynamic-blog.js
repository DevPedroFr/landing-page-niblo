(function () {
  'use strict';

  document.addEventListener('DOMContentLoaded', function () {
    var latestGrid = document.getElementById('latest-posts-grid');
    if (!latestGrid) return;

    fetch('/api/public/posts?limit=4')
      .then(function (response) {
        if (!response.ok) {
          throw new Error('Nao foi possivel carregar os posts');
        }
        return response.json();
      })
      .then(function (posts) {
        if (!Array.isArray(posts) || !posts.length) return;

        latestGrid.innerHTML = posts.map(function (post) {
          return '' +
            '<a href="' + post.url + '" class="blog-card reveal visible">' +
              '<div class="blog-img" style="background-image:url(\'' + post.cover_image + '\'); background-position:center; background-size:cover; background-repeat:no-repeat;"></div>' +
              '<div class="blog-footer"><span>Clique e saiba mais</span><span class="arrow-icon">→</span></div>' +
            '</a>';
        }).join('');
      })
      .catch(function () {
      });
  });
})();