import { OneSignal, LogLevel } from 'react-native-onesignal';
import { Platform } from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

// OneSignal App ID
const ONESIGNAL_APP_ID = 'e841b137-33e1-439c-8284-7cebb747fde7';

interface NotificationData {
  restaurantId?: string;
  specialId?: string;
  screen?: string;
  type?: string;
  title?: string;
  message?: string;
}

type NotificationClickCallback = (data: NotificationData) => void;

class OneSignalService {
  private initialized = false;
  private userId: string | null = null;
  private clickCallback: NotificationClickCallback | null = null;

  /**
   * Initialize OneSignal SDK
   * Should be called once when app starts
   */
  initialize(appId?: string) {
    if (this.initialized) {
      console.log('OneSignal already initialized');
      return;
    }

    const oneSignalAppId = appId || ONESIGNAL_APP_ID;
    
    if (!oneSignalAppId) {
      console.warn('OneSignal App ID not configured. Push notifications will not work.');
      console.warn('Set ONESIGNAL_APP_ID in your environment or pass it to initialize()');
      return;
    }

    try {
      // Enable verbose logging in development
      if (__DEV__) {
        OneSignal.Debug.setLogLevel(LogLevel.Verbose);
      }

      // Initialize OneSignal
      OneSignal.initialize(oneSignalAppId);
      
      // Set up notification handlers
      this.setupNotificationHandlers();
      
      this.initialized = true;
      console.log('OneSignal initialized successfully');
    } catch (error) {
      console.error('Failed to initialize OneSignal:', error);
    }
  }

  /**
   * Set up notification event handlers
   */
  private setupNotificationHandlers() {
    // Handle notification click (when user taps on notification)
    OneSignal.Notifications.addClickListener((event) => {
      console.log('OneSignal notification clicked:', event);
      
      const notification = event.notification;
      const additionalData = notification.additionalData as NotificationData || {};
      
      // Call registered callback if exists
      if (this.clickCallback) {
        this.clickCallback(additionalData);
      }
    });

    // Handle notification received in foreground
    OneSignal.Notifications.addForegroundLifecycleListener((event) => {
      console.log('OneSignal notification received in foreground:', event);
      // Allow notification to display normally
      // Call event.preventDefault() if you want to suppress it
    });

    // Track permission changes
    OneSignal.Notifications.addPermissionObserver((event) => {
      console.log('OneSignal permission changed:', event.permission);
    });

    // Track subscription changes
    OneSignal.User.pushSubscription.addObserver((event) => {
      console.log('OneSignal push subscription changed:', event);
      if (event.current) {
        console.log('Subscription ID:', event.current.id);
        console.log('Opted In:', event.current.optedIn);
      }
    });
  }

  /**
   * Request push notification permission from user
   */
  async requestPermission(): Promise<boolean> {
    try {
      const granted = await OneSignal.Notifications.requestPermission(true);
      console.log('Push notification permission:', granted ? 'granted' : 'denied');
      return granted;
    } catch (error) {
      console.error('Failed to request permission:', error);
      return false;
    }
  }

  /**
   * Check if user has granted notification permission
   */
  async hasPermission(): Promise<boolean> {
    try {
      const permission = await OneSignal.Notifications.getPermissionAsync();
      return permission;
    } catch (error) {
      console.error('Failed to check permission:', error);
      return false;
    }
  }

  /**
   * Register click callback for handling notification taps
   */
  onNotificationClick(callback: NotificationClickCallback) {
    this.clickCallback = callback;
  }

  /**
   * Login user to OneSignal (link to your user ID)
   */
  async loginUser(userId: string, email?: string) {
    try {
      this.userId = userId;
      
      // Set external user ID
      await OneSignal.login(userId);
      
      // Add email if provided
      if (email) {
        await OneSignal.User.addEmail(email);
      }
      
      // Store locally for reference
      await AsyncStorage.setItem('onesignal_user_id', userId);
      
      console.log('User logged into OneSignal:', userId);
    } catch (error) {
      console.error('Failed to login user to OneSignal:', error);
    }
  }

  /**
   * Logout user from OneSignal
   */
  async logoutUser() {
    try {
      await OneSignal.logout();
      this.userId = null;
      await AsyncStorage.removeItem('onesignal_user_id');
      console.log('User logged out of OneSignal');
    } catch (error) {
      console.error('Failed to logout user from OneSignal:', error);
    }
  }

  /**
   * Tag user with favorite restaurant
   */
  async tagFavoriteRestaurant(restaurantId: string) {
    try {
      await OneSignal.User.addTag('favorite_restaurant', restaurantId);
      console.log('Tagged user with favorite restaurant:', restaurantId);
    } catch (error) {
      console.error('Failed to tag favorite restaurant:', error);
    }
  }

  /**
   * Tag user with multiple favorite restaurants
   */
  async tagFavoriteRestaurants(restaurantIds: string[]) {
    try {
      const tags: { [key: string]: string } = {};
      
      // Store all favorites as comma-separated string
      tags['favorite_restaurants'] = restaurantIds.join(',');
      
      // Also store each individually for filtering
      restaurantIds.slice(0, 10).forEach((id, index) => {
        tags[`fav_${index}`] = id;
      });
      
      await OneSignal.User.addTags(tags);
      console.log('Tagged user with favorite restaurants:', restaurantIds.length);
    } catch (error) {
      console.error('Failed to tag favorite restaurants:', error);
    }
  }

  /**
   * Remove favorite restaurant tag
   */
  async untagFavoriteRestaurant(restaurantId: string) {
    try {
      // Get current favorites and remove this one
      // For simplicity, we'll just remove the main tag
      await OneSignal.User.removeTag('favorite_restaurant');
      console.log('Removed favorite restaurant tag');
    } catch (error) {
      console.error('Failed to remove favorite restaurant tag:', error);
    }
  }

  /**
   * Tag user with engagement data
   */
  async tagEngagement(action: string, value: string) {
    try {
      const timestamp = Math.floor(Date.now() / 1000).toString();
      await OneSignal.User.addTags({
        [`last_${action}`]: timestamp,
        [`${action}_value`]: value,
      });
      console.log('Tagged user engagement:', action, value);
    } catch (error) {
      console.error('Failed to tag engagement:', error);
    }
  }

  /**
   * Tag user with notification preferences
   */
  async setNotificationPreferences(preferences: {
    newSpecials?: boolean;
    specialsStarting?: boolean;
    dailyDigest?: boolean;
  }) {
    try {
      const tags: { [key: string]: string } = {};
      
      if (preferences.newSpecials !== undefined) {
        tags['notify_new_specials'] = preferences.newSpecials ? '1' : '0';
      }
      if (preferences.specialsStarting !== undefined) {
        tags['notify_specials_starting'] = preferences.specialsStarting ? '1' : '0';
      }
      if (preferences.dailyDigest !== undefined) {
        tags['notify_daily_digest'] = preferences.dailyDigest ? '1' : '0';
      }
      
      await OneSignal.User.addTags(tags);
      console.log('Set notification preferences:', preferences);
    } catch (error) {
      console.error('Failed to set notification preferences:', error);
    }
  }

  /**
   * Get current subscription ID (player ID)
   */
  async getSubscriptionId(): Promise<string | null> {
    try {
      const subscription = OneSignal.User.pushSubscription;
      return subscription.id || null;
    } catch (error) {
      console.error('Failed to get subscription ID:', error);
      return null;
    }
  }

  /**
   * Check if OneSignal is initialized
   */
  isInitialized(): boolean {
    return this.initialized;
  }
}

export default new OneSignalService();
