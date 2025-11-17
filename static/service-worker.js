self.addEventListener('install', e => {
  e.waitUntil(
    caches.open('robo-cache').then(cache => {
      return cache.addAll([
        '/',
        '/painel',
        '/static/style.css',
        '/static/script.js',
        '/static/chart.min.js'
      ]);
    })
  );
});

self.addEventListener('fetch', e => {
  e.respondWith(
    caches.match(e.request).then(response => response || fetch(e.request))
  );
});
