// scripts-solucoes.js
// Multi-cloud connection lines — unique to solucoes.html

(function () {

  function getCenter(el, scene) {
    var eRect = el.getBoundingClientRect();
    var sRect = scene.getBoundingClientRect();
    return {
      x: eRect.left - sRect.left + eRect.width  / 2,
      y: eRect.top  - sRect.top  + eRect.height / 2
    };
  }

  function drawLine(canvas, x1, y1, x2, y2, delay) {
    var dx  = x2 - x1;
    var dy  = y2 - y1;
    var len = Math.sqrt(dx * dx + dy * dy);
    var ang = Math.atan2(dy, dx) * 180 / Math.PI;

    var div = document.createElement('div');
    div.className = 'mc3d-line';
    div.style.width        = len + 'px';
    div.style.left         = x1 + 'px';
    div.style.top          = y1 + 'px';
    div.style.transform    = 'rotate(' + ang + 'deg)';
    div.style.animationDelay = delay + 's';
    canvas.appendChild(div);
  }

  function buildLines() {
    var scene  = document.getElementById('mc3d-scene');
    var canvas = document.getElementById('mc3d-lines-canvas');
    var hub    = document.getElementById('mc3d-center');

    if (!scene || !canvas || !hub) return;

    var nodes = [
      { id: 'mc3d-n1', delay: 0.0 },
      { id: 'mc3d-n2', delay: 0.6 },
      { id: 'mc3d-n3', delay: 1.2 },
      { id: 'mc3d-n4', delay: 1.8 },
      { id: 'mc3d-n5', delay: 2.4 }
    ];

    canvas.innerHTML = '';
    var c = getCenter(hub, scene);

    nodes.forEach(function (n) {
      var el = document.getElementById(n.id);
      if (!el) return;
      var p = getCenter(el, scene);
      drawLine(canvas, c.x, c.y, p.x, p.y, n.delay);
    });
  }

  window.addEventListener('load', buildLines);

  var resizeTimer;
  window.addEventListener('resize', function () {
    clearTimeout(resizeTimer);
    resizeTimer = setTimeout(buildLines, 100);
  });

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', buildLines);
  } else {
    requestAnimationFrame(function () {
      requestAnimationFrame(buildLines);
    });
  }

})();
