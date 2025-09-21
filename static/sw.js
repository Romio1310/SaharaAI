// Sahara AI - Service Worker for PWA
const CACHE_NAME = 'sahara-v1.0.0';
const STATIC_CACHE = 'sahara-static-v1';
const DYNAMIC_CACHE = 'sahara-dynamic-v1';

// Files to cache for offline functionality
const STATIC_FILES = [
    '/',
    '/static/css/style_modern.css',
    '/static/js/app_modern.js',
    '/static/manifest.json',
    'https://cdn.tailwindcss.com',
    'https://unpkg.com/alpinejs@3.x.x/dist/cdn.min.js',
    'https://unpkg.com/aos@2.3.1/dist/aos.css',
    'https://unpkg.com/aos@2.3.1/dist/aos.js',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css',
    'https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=Poppins:wght@300;400;500;600;700&display=swap'
];

// Install event - cache static assets
self.addEventListener('install', event => {
    console.log('[SW] Installing...');
    
    event.waitUntil(
        Promise.all([
            caches.open(STATIC_CACHE).then(cache => {
                console.log('[SW] Caching static files');
                return cache.addAll(STATIC_FILES);
            }),
            self.skipWaiting()
        ])
    );
});

// Activate event - clean up old caches
self.addEventListener('activate', event => {
    console.log('[SW] Activating...');
    
    event.waitUntil(
        Promise.all([
            caches.keys().then(cacheNames => {
                return Promise.all(
                    cacheNames.map(cacheName => {
                        if (cacheName !== STATIC_CACHE && cacheName !== DYNAMIC_CACHE) {
                            console.log('[SW] Deleting old cache:', cacheName);
                            return caches.delete(cacheName);
                        }
                    })
                );
            }),
            self.clients.claim()
        ])
    );
});

// Fetch event - serve from cache with network fallback
self.addEventListener('fetch', event => {
    const { request } = event;
    const { url, method } = request;

    // Skip non-GET requests
    if (method !== 'GET') return;

    // Skip external domains (except CDNs)
    if (!url.startsWith(self.location.origin) && !isCDNRequest(url)) return;

    event.respondWith(
        cacheFirst(request)
            .catch(() => networkFirst(request))
            .catch(() => fallbackResponse(request))
    );
});

// Cache-first strategy for static assets
async function cacheFirst(request) {
    const cachedResponse = await caches.match(request);
    if (cachedResponse) {
        return cachedResponse;
    }
    throw new Error('Not in cache');
}

// Network-first strategy for dynamic content
async function networkFirst(request) {
    try {
        const response = await fetch(request);
        
        if (response.ok) {
            // Cache successful responses
            const cache = await caches.open(DYNAMIC_CACHE);
            cache.put(request, response.clone());
        }
        
        return response;
    } catch (error) {
        // Try cache as fallback
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        throw error;
    }
}

// Fallback responses for offline scenarios
function fallbackResponse(request) {
    const { destination } = request;
    
    switch (destination) {
        case 'document':
            return caches.match('/') || createOfflinePage();
        
        case 'image':
            return createOfflineImage();
        
        case 'font':
        case 'style':
        case 'script':
            return new Response('', { status: 503 });
        
        default:
            if (request.url.includes('/chat')) {
                return createOfflineChatResponse();
            }
            return new Response('Offline', { status: 503 });
    }
}

// Helper functions
function isCDNRequest(url) {
    const cdnDomains = [
        'cdn.tailwindcss.com',
        'unpkg.com',
        'cdnjs.cloudflare.com',
        'fonts.googleapis.com',
        'fonts.gstatic.com'
    ];
    return cdnDomains.some(domain => url.includes(domain));
}

function createOfflinePage() {
    const html = `
        <!DOCTYPE html>
        <html>
        <head>
            <title>Sahara - Offline</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                body { 
                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                    margin: 0;
                    padding: 20px;
                    background: linear-gradient(135deg, #6366f1, #8b5cf6);
                    color: white;
                    min-height: 100vh;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                }
                .container {
                    text-align: center;
                    background: rgba(255,255,255,0.1);
                    backdrop-filter: blur(10px);
                    padding: 40px;
                    border-radius: 20px;
                    border: 1px solid rgba(255,255,255,0.2);
                }
                .icon { font-size: 64px; margin-bottom: 20px; }
                h1 { margin: 0 0 10px 0; }
                p { opacity: 0.8; margin-bottom: 30px; }
                button {
                    background: white;
                    color: #6366f1;
                    border: none;
                    padding: 12px 24px;
                    border-radius: 8px;
                    font-weight: 600;
                    cursor: pointer;
                }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="icon">🌐</div>
                <h1>You're Offline</h1>
                <p>Sahara needs an internet connection to provide AI support.</p>
                <button onclick="window.location.reload()">Try Again</button>
            </div>
        </body>
        </html>
    `;
    return new Response(html, {
        headers: { 'Content-Type': 'text/html' }
    });
}

function createOfflineImage() {
    // Create a simple SVG placeholder
    const svg = `
        <svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
            <rect width="200" height="200" fill="#f3f4f6"/>
            <text x="50%" y="50%" text-anchor="middle" fill="#9ca3af" font-size="16">
                Image Offline
            </text>
        </svg>
    `;
    return new Response(svg, {
        headers: { 'Content-Type': 'image/svg+xml' }
    });
}

function createOfflineChatResponse() {
    const offlineResponse = {
        message: "I'm currently offline, but I'll be here when you reconnect! 🌸 Your mental health journey continues even when we're apart. Take deep breaths, practice self-care, and know that support will be available soon.",
        context: "offline",
        source: "offline_mode"
    };
    
    return new Response(JSON.stringify(offlineResponse), {
        headers: { 'Content-Type': 'application/json' }
    });
}

// Background sync for when connection is restored
self.addEventListener('sync', event => {
    if (event.tag === 'sahara-sync') {
        event.waitUntil(syncData());
    }
});

async function syncData() {
    // Sync any pending data when connection is restored
    console.log('[SW] Syncing data...');
    
    // You can implement specific sync logic here
    // For example, sending queued mood entries or chat messages
}

// Push notifications (for future implementation)
self.addEventListener('push', event => {
    if (!event.data) return;
    
    const data = event.data.json();
    const options = {
        body: data.body || 'New message from Sahara',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/badge-72x72.png',
        vibrate: [200, 100, 200],
        data: data,
        actions: [
            {
                action: 'open',
                title: 'Open Sahara',
                icon: '/static/icons/open-icon.png'
            },
            {
                action: 'close',
                title: 'Dismiss',
                icon: '/static/icons/close-icon.png'
            }
        ]
    };
    
    event.waitUntil(
        self.registration.showNotification('Sahara AI', options)
    );
});

// Handle notification clicks
self.addEventListener('notificationclick', event => {
    event.notification.close();
    
    if (event.action === 'open') {
        event.waitUntil(
            clients.openWindow('/')
        );
    }
});

console.log('[SW] Service Worker loaded successfully');