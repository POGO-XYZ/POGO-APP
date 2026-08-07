/* POGO-APP service worker
 *
 * Two jobs:
 *   1. Keep the app usable offline once it has been opened.
 *   2. Load instantly on repeat visits without ever showing stale data.
 *
 * Strategy differs by what's being fetched:
 *   - App shell (HTML, CSS, fonts, icons): cache first, refreshed in the
 *     background. These change rarely and should never block a load.
 *   - Archive data (manifest, listings): network first, cache as fallback.
 *     Always current when online; still readable when not.
 *   - Media (thumbnails, artwork): cache first, kept in a separate store
 *     that can grow without pushing out the shell.
 */

const VERSION = "v2";
const SHELL = "pogo-shell-" + VERSION;
const DATA = "pogo-data-" + VERSION;
const MEDIA = "pogo-media-" + VERSION;

const SHELL_FILES = [
  "./",
  "./index.html",
  "./archive.html",
  "./text-renderer.html",
  "./art-to-text-live-sequence.html",
  "./fonts.css",
  "./pogo-mark.svg",
  "./pogo-mark-light.svg",
  "./splash.png",
  "./app.webmanifest",
  "./fonts/unbounded-400.woff2",
  "./fonts/unbounded-700.woff2",
  "./fonts/dongle-300.woff2",
  "./fonts/dongle-400.woff2",
  "./fonts/dongle-700.woff2",
  "./fonts/annie-400.woff2",
  "./icons/icon-192.png",
  "./icons/icon-512.png"
];

self.addEventListener("install", function (event) {
  event.waitUntil(
    caches.open(SHELL)
      .then(function (cache) { return cache.addAll(SHELL_FILES); })
      .then(function () { return self.skipWaiting(); })
      .catch(function () { /* a missing file shouldn't block installation */ })
  );
});

self.addEventListener("activate", function (event) {
  event.waitUntil(
    caches.keys().then(function (keys) {
      return Promise.all(keys.map(function (k) {
        if (k !== SHELL && k !== DATA && k !== MEDIA) return caches.delete(k);
      }));
    }).then(function () { return self.clients.claim(); })
  );
});

function networkFirst(request, cacheName) {
  return fetch(request).then(function (response) {
    if (response && response.ok) {
      var copy = response.clone();
      caches.open(cacheName).then(function (c) { c.put(request, copy); });
    }
    return response;
  }).catch(function () {
    return caches.match(request);
  });
}

function cacheFirst(request, cacheName) {
  return caches.match(request).then(function (hit) {
    if (hit) {
      // refresh quietly for next time
      fetch(request).then(function (res) {
        if (res && res.ok) {
          caches.open(cacheName).then(function (c) { c.put(request, res); });
        }
      }).catch(function () {});
      return hit;
    }
    return fetch(request).then(function (res) {
      if (res && res.ok) {
        var copy = res.clone();
        caches.open(cacheName).then(function (c) { c.put(request, copy); });
      }
      return res;
    });
  });
}

self.addEventListener("fetch", function (event) {
  var req = event.request;
  if (req.method !== "GET") return;

  var url = new URL(req.url);

  // Archive data must be current when a connection exists
  if (/manifest\.json$|LISTINGS\.JSON$/i.test(url.pathname)) {
    event.respondWith(networkFirst(req, DATA));
    return;
  }

  // Artwork and thumbnails
  if (/\/thumbs\//.test(url.pathname) ||
      /raw\.githubusercontent\.com/.test(url.hostname)) {
    event.respondWith(cacheFirst(req, MEDIA));
    return;
  }

  // Everything else served from this origin is app shell
  if (url.origin === location.origin) {
    event.respondWith(
      cacheFirst(req, SHELL).catch(function () {
        return caches.match("./index.html");
      })
    );
  }
});
