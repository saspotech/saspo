// Service Worker for Saspo World PWA
self.addEventListener('install', (e) => {
  self.skipWaiting();
});

self.addEventListener('fetch', (e) => {
  // Pass all requests through to the network
  e.respondWith(fetch(e.request));
});