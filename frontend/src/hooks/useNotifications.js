import { useEffect, useState } from 'react';

const useNotifications = () => {
  const [isEnabled, setIsEnabled] = useState(false);
  const [isInitialized, setIsInitialized] = useState(false);
  const [hasPermission, setHasPermission] = useState(false);
  const [isLoading, setIsLoading] = useState(false);

  // Temporarily disable OneSignal to focus on core functionality
  useEffect(() => {
    console.log('OneSignal temporarily disabled for debugging');
    setIsInitialized(true);
  }, []);

  const requestPermission = async () => {
    try {
      if ('Notification' in window) {
        const permission = await Notification.requestPermission();
        const granted = permission === 'granted';
        setHasPermission(granted);
        setIsEnabled(granted);
        return granted;
      }
      return false;
    } catch (error) {
      console.error('Error requesting notification permission:', error);
      return false;
    }
  };

  const updatePreferences = async (preferences) => {
    console.log('Notification preferences updated:', preferences);
    return true;
  };

  return {
    isEnabled,
    isInitialized,
    hasPermission,
    isLoading,
    requestPermission,
    updatePreferences,
  };
};

export default useNotifications;