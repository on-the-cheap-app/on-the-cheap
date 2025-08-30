import { useState, useEffect, useCallback } from 'react';

export const usePWA = () => {
  const [isInstallable, setIsInstallable] = useState(false);
  const [isInstalled, setIsInstalled] = useState(false);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [swRegistration, setSwRegistration] = useState(null);
  const [deferredPrompt, setDeferredPrompt] = useState(null);

  // Register service worker
  useEffect(() => {
    const registerSW = async () => {
      if ('serviceWorker' in navigator) {
        try {
          const registration = await navigator.serviceWorker.register('/sw.js', {
            scope: '/'
          });
          
          setSwRegistration(registration);
          console.log('📱 PWA Service Worker registered successfully:', registration.scope);
          
          // Check for updates
          registration.addEventListener('updatefound', () => {
            console.log('🔄 Service Worker update found');
            const newWorker = registration.installing;
            
            if (newWorker) {
              newWorker.addEventListener('statechange', () => {
                if (newWorker.state === 'installed' && navigator.serviceWorker.controller) {
                  console.log('✅ New Service Worker installed, app will update on next load');
                  // Could show update notification here
                }
              });
            }
          });

          // Listen for controlling service worker changes
          navigator.serviceWorker.addEventListener('controllerchange', () => {
            console.log('🔄 Service Worker controller changed');
            window.location.reload();
          });

        } catch (error) {
          console.error('❌ Service Worker registration failed:', error);
        }
      }
    };

    registerSW();
  }, []);

  // Handle install prompt
  useEffect(() => {
    const handleBeforeInstallPrompt = (e) => {
      console.log('📱 PWA install prompt available');
      e.preventDefault();
      setDeferredPrompt(e);
      setIsInstallable(true);
    };

    const handleAppInstalled = () => {
      console.log('🎉 PWA installed successfully');
      setIsInstalled(true);
      setIsInstallable(false);
      setDeferredPrompt(null);
    };

    window.addEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
    window.addEventListener('appinstalled', handleAppInstalled);

    return () => {
      window.removeEventListener('beforeinstallprompt', handleBeforeInstallPrompt);
      window.removeEventListener('appinstalled', handleAppInstalled);
    };
  }, []);

  // Monitor online/offline status
  useEffect(() => {
    const handleOnline = () => {
      console.log('🌐 App back online');
      setIsOnline(true);
    };

    const handleOffline = () => {
      console.log('📱 App offline');
      setIsOnline(false);
    };

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Check if app is already installed (running in standalone mode)
  useEffect(() => {
    const checkIfInstalled = () => {
      const isStandalone = window.matchMedia('(display-mode: standalone)').matches;
      const isIOSStandalone = window.navigator.standalone === true;
      
      if (isStandalone || isIOSStandalone) {
        setIsInstalled(true);
        setIsInstallable(false);
        console.log('📱 App is running in installed/standalone mode');
      }
    };

    checkIfInstalled();
  }, []);

  // Install the PWA
  const installPWA = useCallback(async () => {
    if (!deferredPrompt) {
      console.log('❌ No install prompt available');
      return false;
    }

    try {
      console.log('📱 Showing PWA install prompt');
      deferredPrompt.prompt();
      
      const { outcome } = await deferredPrompt.userChoice;
      console.log('📱 User install choice:', outcome);
      
      if (outcome === 'accepted') {
        setIsInstalled(true);
        setIsInstallable(false);
      }
      
      setDeferredPrompt(null);
      return outcome === 'accepted';
    } catch (error) {
      console.error('❌ Failed to install PWA:', error);
      return false;
    }
  }, [deferredPrompt]);

  // Update service worker
  const updateSW = useCallback(async () => {
    if (swRegistration) {
      try {
        await swRegistration.update();
        console.log('🔄 Service Worker update triggered');
      } catch (error) {
        console.error('❌ Failed to update Service Worker:', error);
      }
    }
  }, [swRegistration]);

  // Cache restaurant data for offline use
  const cacheRestaurantData = useCallback(async (restaurants, location) => {
    if ('caches' in window) {
      try {
        const cache = await caches.open('on-the-cheap-restaurants-v1');
        
        // Cache restaurant search results
        const cacheData = {
          restaurants,
          location,
          timestamp: Date.now(),
          version: '1.0.0'
        };
        
        const response = new Response(JSON.stringify(cacheData), {
          headers: { 'Content-Type': 'application/json' }
        });
        
        await cache.put('/api/cached-restaurants', response);
        console.log('💾 Restaurant data cached for offline use');
      } catch (error) {
        console.error('❌ Failed to cache restaurant data:', error);
      }
    }
  }, []);

  // Get cached restaurant data
  const getCachedRestaurantData = useCallback(async () => {
    if ('caches' in window) {
      try {
        const cache = await caches.open('on-the-cheap-restaurants-v1');
        const response = await cache.match('/api/cached-restaurants');
        
        if (response) {
          const data = await response.json();
          
          // Check if cache is not too old (24 hours)
          const cacheAge = Date.now() - data.timestamp;
          const maxAge = 24 * 60 * 60 * 1000; // 24 hours
          
          if (cacheAge < maxAge) {
            console.log('📦 Using cached restaurant data');
            return data;
          }
        }
      } catch (error) {
        console.error('❌ Failed to get cached restaurant data:', error);
      }
    }
    return null;
  }, []);

  return {
    isInstallable,
    isInstalled,
    isOnline,
    installPWA,
    updateSW,
    cacheRestaurantData,
    getCachedRestaurantData,
    swRegistration
  };
};