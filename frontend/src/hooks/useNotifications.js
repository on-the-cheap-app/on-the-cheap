import { useEffect, useState, useCallback } from 'react';
import OneSignal from 'react-onesignal';

// Global flag to prevent multiple initializations
let isOneSignalInitialized = false;

export const useNotifications = () => {
  const [isEnabled, setIsEnabled] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    let timeoutId;
    
    const initializeOneSignal = async () => {
      try {
        setIsLoading(true);
        
        // Check our global flag first
        if (isOneSignalInitialized) {
          console.log('OneSignal initialization already in progress or completed');
          setIsInitialized(true);
          setIsLoading(false);
          setIsEnabled(false); // Will be updated when permission is checked
          return;
        }
        
        // Check if OneSignal is already initialized
        if (window.OneSignal && window.OneSignal._initCalled) {
          console.log('OneSignal already initialized, using existing instance');
          setIsInitialized(true);
          
          // Check current permission status
          try {
            const permission = await OneSignal.Notifications.permission;
            setIsEnabled(permission === true);
          } catch (permError) {
            console.log('Permission check failed, defaulting to false');
            setIsEnabled(false);
          }
          
          setIsLoading(false);
          return;
        }
        
        // Also check if OneSignal is available and ready
        if (window.OneSignal && typeof window.OneSignal.push === 'function') {
          // Use the push method to ensure we don't double-initialize
          window.OneSignal.push(function() {
            console.log('OneSignal was already available, setting as initialized');
            setIsInitialized(true);
            setIsLoading(false);
            
            try {
              OneSignal.Notifications.permission.then(permission => {
                setIsEnabled(permission === true);
              }).catch(() => {
                setIsEnabled(false);
              });
            } catch (e) {
              setIsEnabled(false);
            }
          });
          return;
        }
        
        // Set our global flag before initializing
        isOneSignalInitialized = true;
        
        // Initialize OneSignal if not already done
        console.log('🔔 Starting OneSignal initialization...');
        
        // Add timeout wrapper for the init call itself
        const initPromise = OneSignal.init({
          appId: process.env.REACT_APP_ONESIGNAL_APP_ID,
          allowLocalhostAsSecureOrigin: true, // For development/testing
        });
        
        // Race between init and a 8-second timeout
        const initTimeout = new Promise((_, reject) => {
          setTimeout(() => reject(new Error('Init timeout')), 8000);
        });
        
        await Promise.race([initPromise, initTimeout]);
        
        console.log('🔔 OneSignal initialization completed');
        setIsInitialized(true);
        
        // Check current permission status
        try {
          const permission = await OneSignal.Notifications.permission;
          setIsEnabled(permission === true);
        } catch (permError) {
          console.log('Permission check failed, defaulting to false');
          setIsEnabled(false);
        }
        
        console.log('OneSignal initialized successfully');
      } catch (error) {
        console.error('Failed to initialize OneSignal:', error);
        
        // If it's already initialized error, still set as initialized
        if (error.message && error.message.includes('already initialized')) {
          console.log('OneSignal was already initialized, setting as ready');
          setIsInitialized(true);
          setIsEnabled(false); // Default to false, user can enable later
        } else if (error.message && error.message.includes('Init timeout')) {
          console.warn('OneSignal initialization timed out, enabling fallback mode');
          setIsInitialized(true); // Enable fallback mode
          setIsEnabled(false);
        } else {
          console.warn('OneSignal initialization failed, enabling fallback mode');
          setIsInitialized(true); // Enable fallback mode even if init failed
          setIsEnabled(false);
        }
      } finally {
        setIsLoading(false);
      }
    };

    // Set a timeout to prevent infinite loading
    timeoutId = setTimeout(() => {
      console.warn('OneSignal initialization timeout after 15 seconds, proceeding with fallback mode');
      setIsLoading(false);
      setIsInitialized(true); // Set as initialized so user can still access settings
      setIsEnabled(false);
      isOneSignalInitialized = true; // Prevent further initialization attempts
    }, 15000); // 15 second timeout (increased from 10)

    initializeOneSignal();
    
    return () => {
      if (timeoutId) {
        clearTimeout(timeoutId);
      }
    };
  }, []);

  const requestPermission = useCallback(async () => {
    console.log('🔔 Permission request initiated...');
    
    if (!isInitialized) {
      console.error('OneSignal not initialized yet');
      alert('OneSignal is not ready yet. Please try again in a moment.');
      return false;
    }

    try {
      setIsLoading(true);
      
      // First check if browser supports notifications
      if (!('Notification' in window)) {
        alert('This browser does not support notifications');
        return false;
      }
      
      console.log('🔔 Browser supports notifications, current permission:', Notification.permission);
      
      // If permission is already denied, guide user to enable manually
      if (Notification.permission === 'denied') {
        alert('Notifications are blocked. Please click the lock icon in your address bar and allow notifications, then refresh the page.');
        return false;
      }
      
      // If permission is already granted, just update state
      if (Notification.permission === 'granted') {
        console.log('🔔 Permission already granted');
        setIsEnabled(true);
        
        // Tag user as having notifications enabled
        try {
          await OneSignal.User.addTags({
            notifications_enabled: 'true',
            enabled_date: new Date().toISOString()
          });
        } catch (tagError) {
          console.error('Failed to tag user:', tagError);
        }
        
        return true;
      }
      
      // Try browser permission API first (more reliable)
      try {
        console.log('🔔 Requesting permission via browser API...');
        const permission = await Notification.requestPermission();
        const granted = permission === 'granted';
        
        console.log('🔔 Browser API permission result:', permission, 'granted:', granted);
        setIsEnabled(granted);
        
        if (granted) {
          console.log('Push notifications enabled successfully via browser API');
          
          // Tag user as having notifications enabled
          try {
            await OneSignal.User.addTags({
              notifications_enabled: 'true',
              enabled_date: new Date().toISOString()
            });
          } catch (tagError) {
            console.error('Failed to tag user:', tagError);
          }
        } else if (permission === 'denied') {
          console.log('🔔 User denied permission');
          alert('Notifications were denied. To enable them later, click the lock icon in your address bar and change notification settings to "Allow".');
        } else {
          console.log('🔔 User dismissed permission prompt');
          // Don't show an error for dismissal, just log it
        }
        
        return granted;
        
      } catch (browserError) {
        console.log('🔔 Browser API failed, trying OneSignal slidedown:', browserError);
        
        // Fallback to OneSignal slidedown
        try {
          console.log('🔔 Attempting OneSignal slidedown prompt...');
          await OneSignal.Slidedown.promptPush();
          
          // Wait a moment for the permission to be processed
          await new Promise(resolve => setTimeout(resolve, 1000));
          
          // Check the result
          const permission = await OneSignal.Notifications.permission;
          const granted = permission === true;
          console.log('🔔 OneSignal permission result:', granted);
          
          setIsEnabled(granted);
          
          if (granted) {
            console.log('Push notifications enabled successfully via OneSignal');
            
            // Tag user as having notifications enabled
            await OneSignal.User.addTags({
              notifications_enabled: 'true',
              enabled_date: new Date().toISOString()
            });
          }
          
          return granted;
          
        } catch (slidedownError) {
          console.log('🔔 OneSignal slidedown also failed:', slidedownError);
          
          // Handle specific OneSignal errors gracefully
          if (slidedownError.message && slidedownError.message.includes('Permission dismissed')) {
            console.log('🔔 User dismissed OneSignal permission prompt');
            return false; // Don't show error for dismissal
          }
          
          throw slidedownError; // Re-throw other errors
        }
      }
      
    } catch (error) {
      console.error('Failed to request notification permission:', error);
      alert('Failed to enable notifications. Please try refreshing the page.');
      return false;
    } finally {
      setIsLoading(false);
    }
  }, [isInitialized]);

  const tagUser = useCallback(async (tags) => {
    if (!isInitialized || !isEnabled) {
      console.warn('OneSignal not ready for tagging');
      return false;
    }

    try {
      await OneSignal.User.addTags(tags);
      console.log('User tagged successfully:', tags);
      return true;
    } catch (error) {
      console.error('Failed to tag user:', error);
      return false;
    }
  }, [isInitialized, isEnabled]);

  const setUserPreferences = useCallback(async (preferences) => {
    const tags = {
      // Notification preferences
      notify_new_specials: preferences.newSpecials ? 'true' : 'false',
      notify_favorite_updates: preferences.favoriteUpdates ? 'true' : 'false',
      notify_daily_digest: preferences.dailyDigest ? 'true' : 'false',
      
      // User preferences for targeting
      preferred_cuisine: preferences.cuisine || '',
      dietary_restrictions: preferences.dietary?.join(',') || '',
      notification_time: preferences.preferredTime || 'anytime'
    };

    return await tagUser(tags);
  }, [tagUser]);

  return {
    isEnabled,
    isInitialized,
    isLoading,
    requestPermission,
    tagUser,
    setUserPreferences
  };
};

export default useNotifications;