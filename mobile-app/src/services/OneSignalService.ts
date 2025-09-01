// Simplified OneSignal service for mobile app
// TODO: Implement full OneSignal integration

interface NotificationData {
  restaurantId?: string;
  title?: string;
  message?: string;
}

class OneSignalService {
  private initialized = false;

  initialize() {
    if (this.initialized) {
      return;
    }

    console.log('OneSignal Service initialized (placeholder)');
    this.initialized = true;
  }

  async setExternalUserId(userId: string) {
    console.log('Setting external user ID:', userId);
    // TODO: Implement OneSignal.setExternalUserId(userId)
  }

  async sendNotification(data: NotificationData) {
    console.log('Sending notification:', data);
    // TODO: Implement notification sending
  }

  async requestPermissions() {
    console.log('Requesting notification permissions');
    // TODO: Implement permission request
    return true;
  }

  async getPlayerId(): Promise<string | null> {
    console.log('Getting player ID');
    // TODO: Implement player ID retrieval
    return null;
  }
}

export default new OneSignalService();