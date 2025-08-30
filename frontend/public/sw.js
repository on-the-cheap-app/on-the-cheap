// On-the-Cheap PWA Service Worker
const CACHE_NAME = 'on-the-cheap-v1.0.0';
const OFFLINE_URL = '/offline.html';

// Resources to cache for offline functionality
const urlsToCache = [
  '/',
  '/static/css/main.css',
  '/static/js/main.js',
  '/manifest.json',
  OFFLINE_URL
];

// API endpoints to cache for offline functionality
const API_CACHE_NAME = 'on-the-cheap-api-v1.0.0';
const apiUrlsToCache = [
  // Cache search results for offline viewing
  // These will be populated dynamically
];

// Install event - cache essential resources
self.addEventListener('install', event => {
  console.log('📱 PWA Service Worker installing...');
  
  event.waitUntil(
    Promise.all([
      // Cache app shell
      caches.open(CACHE_NAME).then(cache => {
        console.log('📦 Caching app shell');
        return cache.addAll(urlsToCache.filter(url => url !== OFFLINE_URL));
      }),
      
      // Cache offline page separately (it might not exist yet)
      caches.open(CACHE_NAME).then(cache => {
        return fetch(OFFLINE_URL).then(response => {
          if (response.ok) {
            return cache.put(OFFLINE_URL, response);
          }
        }).catch(() => {
          console.log('⚠️ Offline page not found, will create fallback');
        });
      })
    ])
  );
  
  // Skip waiting to activate immediately
  self.skipWaiting();
});

// Activate event - cleanup old caches
self.addEventListener('activate', event => {
  console.log('🚀 PWA Service Worker activated');
  
  event.waitUntil(
    caches.keys().then(cacheNames => {
      return Promise.all(
        cacheNames.map(cacheName => {
          if (cacheName !== CACHE_NAME && cacheName !== API_CACHE_NAME) {
            console.log('🗑️ Deleting old cache:', cacheName);
            return caches.delete(cacheName);
          }
        })
      );
    })
  );
  
  // Claim all clients immediately
  return self.clients.claim();
});

// Fetch event - serve cached content when offline
self.addEventListener('fetch', event => {
  const { request } = event;
  const url = new URL(request.url);

  // Handle API requests (cache restaurant data)
  if (url.pathname.includes('/api/')) {
    event.respondWith(handleApiRequest(request));
    return;
  }

  // Handle navigation requests (HTML pages)
  if (request.mode === 'navigate') {
    event.respondWith(handleNavigationRequest(request));
    return;
  }

  // Handle other requests (CSS, JS, images)
  event.respondWith(handleResourceRequest(request));
});

// Handle API requests with caching strategy
async function handleApiRequest(request) {
  const url = new URL(request.url);
  
  try {
    // Try network first for fresh data
    const networkResponse = await fetch(request);
    
    if (networkResponse.ok) {
      // Cache successful API responses
      const cache = await caches.open(API_CACHE_NAME);
      
      // Only cache GET requests for restaurant data
      if (request.method === 'GET' && 
          (url.pathname.includes('/restaurants') || url.pathname.includes('/specials'))) {
        const responseClone = networkResponse.clone();
        await cache.put(request, responseClone);
        console.log('💾 Cached API response:', url.pathname);
      }
    }
    
    return networkResponse;
  } catch (error) {
    console.log('📡 API request failed, trying cache:', url.pathname);
    
    // If network fails, try cache
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      console.log('📦 Serving cached API response:', url.pathname);
      return cachedResponse;
    }
    
    // Return offline API response
    return new Response(
      JSON.stringify({
        error: 'Offline',
        message: 'This feature requires an internet connection',
        cached: false
      }),
      {
        status: 503,
        headers: { 'Content-Type': 'application/json' }
      }
    );
  }
}

// Handle navigation requests (page loads)
async function handleNavigationRequest(request) {
  try {
    // Try network first
    const networkResponse = await fetch(request);
    return networkResponse;
  } catch (error) {
    console.log('📡 Navigation request failed, serving offline page');
    
    // If network fails, serve offline page or cached version
    const cachedResponse = await caches.match(OFFLINE_URL);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // Fallback offline page if none cached
    return new Response(
      generateOfflinePage(),
      {
        headers: { 'Content-Type': 'text/html' }
      }
    );
  }
}

// Handle resource requests (CSS, JS, images)
async function handleResourceRequest(request) {
  try {
    // Try cache first for resources
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
      return cachedResponse;
    }
    
    // If not in cache, try network
    const networkResponse = await fetch(request);
    
    // Cache successful responses
    if (networkResponse.ok) {
      const cache = await caches.open(CACHE_NAME);
      cache.put(request, networkResponse.clone());
    }
    
    return networkResponse;
  } catch (error) {
    console.log('📦 Resource not available offline:', request.url);
    
    // Return empty response for failed resources
    return new Response('', { status: 404 });
  }
}

// Generate offline page HTML
function generateOfflinePage() {
  return `
    <!DOCTYPE html>
    <html>
    <head>
      <meta charset="utf-8">
      <meta name="viewport" content="width=device-width, initial-scale=1">
      <title>On-the-Cheap - Offline</title>
      <style>
        body {
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
          background: linear-gradient(to bottom, #fef3c7, #fed7aa);
          margin: 0;
          padding: 20px;
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .container {
          background: white;
          padding: 40px;
          border-radius: 12px;
          box-shadow: 0 4px 6px rgba(0,0,0,0.1);
          text-align: center;
          max-width: 400px;
        }
        h1 { color: #ea580c; margin-bottom: 16px; }
        p { color: #6b7280; margin-bottom: 24px; }
        button {
          background: #ea580c;
          color: white;
          border: none;
          padding: 12px 24px;
          border-radius: 8px;
          cursor: pointer;
          font-size: 16px;
        }
      </style>
    </head>
    <body>
      <div class="container">
        <h1>🍽️ On-the-Cheap</h1>
        <h2>📱 You're Offline</h2>
        <p>No internet connection available. Please check your connection and try again.</p>
        <button onclick="window.location.reload()">🔄 Try Again</button>
        <p><small>Cached restaurant data may still be available</small></p>
      </div>
    </body>
    </html>
  `;
}

// Handle background sync for notifications
self.addEventListener('sync', event => {
  if (event.tag === 'background-sync') {
    console.log('🔄 Background sync triggered');
    event.waitUntil(syncData());
  }
});

// Sync data in background
async function syncData() {
  try {
    // Sync any pending notification preferences or favorites
    console.log('📱 Syncing app data...');
    
    // This would sync any pending user actions when back online
    // For now, just log that sync happened
    console.log('✅ Background sync completed');
  } catch (error) {
    console.log('❌ Background sync failed:', error);
  }
}

// Handle push notifications (works with OneSignal)
self.addEventListener('push', event => {
  console.log('📱 Push notification received');
  
  // OneSignal handles most push logic, but we can add custom handling here
  const data = event.data ? event.data.json() : {};
  
  const notificationOptions = {
    body: data.body || 'New restaurant special available!',
    icon: '/icons/icon-192x192.png',
    badge: '/icons/icon-96x96.png',
    vibrate: [100, 50, 100],
    data: data,
    actions: [
      {
        action: 'view',
        title: 'View Special',
        icon: '/icons/icon-96x96.png'
      },
      {
        action: 'close',
        title: 'Close'
      }
    ]
  };
  
  event.waitUntil(
    self.registration.showNotification(
      data.title || 'On-the-Cheap',
      notificationOptions
    )
  );
});

// Handle notification clicks
self.addEventListener('notificationclick', event => {
  console.log('📱 Notification clicked');
  
  event.notification.close();
  
  if (event.action === 'view') {
    // Open the app to view the special
    event.waitUntil(
      clients.openWindow('/')
    );
  }
});

console.log('📱 On-the-Cheap PWA Service Worker loaded successfully!');