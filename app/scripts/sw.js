// The service worker of the shell. scripts/build.ts replaces the two placeholders below.
const VERSION = "__VERSION__";
const PRECACHE = "__PRECACHE__";

// Lesson audio, the code runner and the account stay on the network.
const NETWORK_ONLY =
  /^\/(?:run|health|auth|api)(?:\/|$)|\.(?:mp3|opus|ogg|m4a|wav)$/;

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches
      .open(VERSION)
      .then((cache) => cache.addAll(PRECACHE))
      .then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches
      .keys()
      .then((keys) =>
        Promise.all(
          keys
            .filter((key) => key !== VERSION)
            .map((key) => caches.delete(key)),
        ),
      )
      .then(() => self.clients.claim()),
  );
});

async function fromNetwork(request) {
  const response = await fetch(request);
  if (response.ok) {
    const cache = await caches.open(VERSION);
    void cache.put(request, response.clone());
  }
  return response;
}

// The shell asks the network first, so a deploy shows at once, and falls back to the cache offline.
async function networkFirst(request) {
  try {
    return await fromNetwork(request);
  } catch {
    const cached = await caches.match(request, {
      ignoreSearch: request.mode === "navigate",
    });
    if (cached) return cached;
    if (request.mode === "navigate")
      return (await caches.match("/")) ?? Response.error();
    return Response.error();
  }
}

// Hashed files never change under their name.
async function cacheFirst(request) {
  return (await caches.match(request)) ?? fromNetwork(request);
}

// A course index answers from the cache and refreshes it for the next launch.
async function staleWhileRevalidate(request) {
  const cached = await caches.match(request);
  const fresh = fromNetwork(request).catch(() => undefined);
  return cached ?? (await fresh) ?? Response.error();
}

self.addEventListener("fetch", (event) => {
  const { request } = event;
  const url = new URL(request.url);
  if (
    request.method !== "GET" ||
    url.origin !== location.origin ||
    request.headers.has("range")
  )
    return;
  if (NETWORK_ONLY.test(url.pathname)) return;
  if (request.mode === "navigate") {
    if (url.pathname.endsWith("/lesson.html")) return;
    event.respondWith(networkFirst(request));
  } else if (url.pathname.startsWith("/assets/")) {
    event.respondWith(cacheFirst(request));
  } else if (
    url.pathname.endsWith(".json") &&
    PRECACHE.includes(url.pathname)
  ) {
    event.respondWith(staleWhileRevalidate(request));
  } else if (PRECACHE.includes(url.pathname)) {
    event.respondWith(networkFirst(request));
  }
});

self.addEventListener("push", (event) => {
  let note = {};
  try {
    note = event.data?.json() ?? {};
  } catch {}
  event.waitUntil(
    self.registration.showNotification(note.title ?? "Rising", {
      body: note.body,
      icon: "/icons/icon-192.png",
      tag: "racha",
      data: { url: note.url },
    }),
  );
});

self.addEventListener("notificationclick", (event) => {
  event.notification.close();
  const target = new URL(event.notification.data?.url ?? "/", location.origin);
  const url = target.origin === location.origin ? target.href : location.origin;
  event.waitUntil(
    self.clients.matchAll({ type: "window" }).then((windows) => {
      const open = windows.find((client) => client.url === url);
      return open ? open.focus() : self.clients.openWindow(url);
    }),
  );
});
