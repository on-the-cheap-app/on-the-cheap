import { useEffect, useState, useCallback } from 'react';
import OneSignal from 'react-onesignal';

export const useNotifications = () => {
  const [isEnabled, setIsEnabled] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  useEffect(() => {
    const initializeOneSignal = async () => {
      try {
        setIsLoading(true);
        
        await OneSignal.init({
          appId: process.env.REACT_APP_ONESIGNAL_APP_ID,
          allowLocalhostAsSecureOrigin: true, // For development/testing
        });
        
        setIsInitialized(true);
        
        // Check current permission status
        const permission = await OneSignal.Notifications.permission;
        setIsEnabled(permission === true);
        
        console.log('OneSignal initialized successfully');
      } catch (error) {
        console.error('Failed to initialize OneSignal:', error);
      } finally {
        setIsLoading(false);
      }
    };

    initializeOneSignal();
  }, []);

  const requestPermission = useCallback(async () => {
    if (!isInitialized) {
      console.error('OneSignal not initialized yet');
      return false;
    }

    try {
      setIsLoading(true);
      
      // Show the permission prompt
      await OneSignal.Slidedown.promptPush();
      
      // Check the result
      const permission = await OneSignal.Notifications.permission;
      const granted = permission === true;
      setIsEnabled(granted);
      
      if (granted) {
        console.log('Push notifications enabled successfully');
        
        // Tag user as having notifications enabled
        await OneSignal.User.addTags({
          notifications_enabled: 'true',
          enabled_date: new Date().toISOString()
        });
      }
      
      return granted;
    } catch (error) {
      console.error('Failed to request notification permission:', error);
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