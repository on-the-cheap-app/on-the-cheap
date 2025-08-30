import { OneSignal } from 'react-native-onesignal';

class OneSignalService {
  private static initialized = false;

  static initialize() {
    if (this.initialized) {
      return;
    }

    console.log('📱 Initializing OneSignal for React Native...');

    // Initialize OneSignal with your App ID
    OneSignal.initialize('4ca64e1c-b430-436d-8037-ffc9d4176b62');

    // Request notification permission
    OneSignal.Notifications.requestPermission(true);

    // Set up notification event handlers
    this.setupEventHandlers();

    this.initialized = true;
    console.log('✅ OneSignal initialized successfully');
  }

  private static setupEventHandlers() {
    // Handle notification received while app is in foreground
    OneSignal.Notifications.addEventListener('foregroundWillDisplay', (event) => {
      console.log('📱 Notification received in foreground:', event.notification);
      
      // Customize notification display
      event.preventDefault();
      event.notification.display();
    });

    // Handle notification clicked/opened
    OneSignal.Notifications.addEventListener('click', (event) => {
      console.log('📱 Notification clicked:', event.notification);
      
      // Handle notification click - navigate to specific screen
      const data = event.notification.additionalData;
      if (data?.restaurantId) {
        // Navigate to restaurant detail screen
        // NavigationService.navigate('RestaurantDetail', { id: data.restaurantId });
      }
    });
  }

  // Tag user for targeted notifications
  static tagUser(tags: Record<string, string | number | boolean>) {
    try {
      OneSignal.User.addTags(tags);
      console.log('📱 User tagged successfully:', tags);
    } catch (error) {
      console.error('❌ Failed to tag user:', error);
    }
  }

  // Get user ID for backend integration
  static getUserId(): Promise<string | null> {
    return new Promise((resolve) => {
      const userId = OneSignal.User.pushSubscription.id;
      resolve(userId || null);
    });
  }

  // Set user email for targeted campaigns
  static setEmail(email: string) {
    try {
      OneSignal.User.addEmail(email);
      console.log('📱 Email set for user:', email);
    } catch (error) {
      console.error('❌ Failed to set email:', error);
    }
  }

  // Send notification data to backend for user targeting
  static async syncWithBackend(userId: string, preferences: any) {
    try {
      const oneSignalId = await this.getUserId();
      
      if (oneSignalId) {
        // Send to backend for user association
        const response = await fetch('https://special-hunter.preview.emergentagent.com/api/users/sync-notifications', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            userId,
            oneSignalId,
            preferences,
          }),
        });

        if (response.ok) {
          console.log('📱 Notifications synced with backend');
        }
      }
    } catch (error) {
      console.error('❌ Failed to sync with backend:', error);
    }
  }

  // Check notification permission status
  static async hasPermission(): Promise<boolean> {
    try {
      const permission = await OneSignal.Notifications.hasPermission();
      return permission;
    } catch (error) {
      console.error('❌ Failed to check permission:', error);
      return false;
    }
  }

  // Request notification permission
  static async requestPermission(): Promise<boolean> {
    try {
      const granted = await OneSignal.Notifications.requestPermission(true);
      console.log('📱 Notification permission:', granted ? 'granted' : 'denied');
      return granted;
    } catch (error) {
      console.error('❌ Failed to request permission:', error);
      return false;
    }
  }
}

export default OneSignalService;