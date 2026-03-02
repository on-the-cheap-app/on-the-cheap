import { OneSignal } from 'react-native-onesignal';
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
      return;
    }

    const oneSignalAppId = appId || ONESIGNAL_APP_ID;
    
    if (!oneSignalAppId) {
      return;
    }

    try {
      // Initialize OneSignal (no verbose logging in production)
      OneSignal.initialize(oneSignalAppId);
      
      // Set up notification handlers
      this.setupNotificationHandlers();
      
      this.initialized = true;
    } catch (error) {
      // Silently fail - push notifications just won't work
    }
  }

  /**
   * Set up notification event handlers
   */
  private setupNotificationHandlers() {
    // Handle notification click (when user taps on notification)
    OneSignal.Notifications.addClickListener((event) => {
      const notification = event.notification;
      const additionalData = notification.additionalData as NotificationData || {};
      
      // Call registered callback if exists
      if (this.clickCallback) {
        this.clickCallback(additionalData);
      }
    });

    // Handle notification received in foreground
    OneSignal.Notifications.addForegroundLifecycleListener((event) => {
      // Allow notification to display normally
    });

    // Track permission changes
    OneSignal.Notifications.addPermissionObserver((event) => {
      // Permission state tracked silently
    });

    // Track subscription changes
    OneSignal.User.pushSubscription.addObserver((event) => {
      // Subscription changes tracked silently
    });
  }

  /**
   * Request push notification permission from user
   */
  async requestPermission(): Promise<boolean> {
    try {
      const granted = await OneSignal.Notifications.requestPermission(true);
      return granted;
    } catch (error) {
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
    } catch (error) {
      // Silently fail
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
    } catch (error) {
      // Silently fail
    }
  }

  /**
   * Tag user with favorite restaurant
   */
  async tagFavoriteRestaurant(restaurantId: string) {
    try {
      await OneSignal.User.addTag('favorite_restaurant', restaurantId);
    } catch (error) {
      // Silently fail
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
    } catch (error) {
      // Silently fail
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
    } catch (error) {
      // Silently fail
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
    } catch (error) {
      // Silently fail
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
    } catch (error) {
      // Silently fail
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
