import axios, { AxiosInstance, AxiosResponse } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

class APIService {
  private api: AxiosInstance;
  private baseURL = 'https://cheapdeals-app.preview.emergentagent.com/api';

  constructor() {
    this.api = axios.create({
      baseURL: this.baseURL,
      timeout: 10000,
    });

    // Add auth token to requests
    this.api.interceptors.request.use(async (config) => {
      const token = await AsyncStorage.getItem('auth_token');
      if (token) {
        config.headers.Authorization = `Bearer ${token}`;
      }
      return config;
    });

    // Handle token expiration
    this.api.interceptors.response.use(
      (response) => response,
      async (error) => {
        if (error.response?.status === 401) {
          await AsyncStorage.removeItem('auth_token');
          await AsyncStorage.removeItem('user_data');
        }
        return Promise.reject(error);
      }
    );
  }

  // Restaurant search
  async searchRestaurants(params: {
    latitude: number;
    longitude: number;
    radius?: number;
    special_type?: string;
    vendor_type?: string;
  }) {
    try {
      const response = await this.api.get('/restaurants/search', { params });
      return response.data;
    } catch (error) {
      console.error('API Error - Restaurant Search:', error);
      throw error;
    }
  }

  // Geocoding
  async geocodeAddress(address: string) {
    try {
      const response = await this.api.get('/geocode', {
        params: { address }
      });
      return response.data;
    } catch (error) {
      console.error('API Error - Geocoding:', error);
      throw error;
    }
  }

  // User authentication
  async login(email: string, password: string) {
    try {
      const response = await this.api.post('/auth/login', {
        email,
        password,
      });
      
      const { token, user } = response.data;
      await AsyncStorage.setItem('auth_token', token);
      await AsyncStorage.setItem('user_data', JSON.stringify(user));
      
      return response.data;
    } catch (error) {
      console.error('API Error - Login:', error);
      throw error;
    }
  }

  async register(userData: {
    first_name: string;
    last_name: string;
    email: string;
    password: string;
  }) {
    try {
      const response = await this.api.post('/auth/register', userData);
      
      const { token, user } = response.data;
      await AsyncStorage.setItem('auth_token', token);
      await AsyncStorage.setItem('user_data', JSON.stringify(user));
      
      return response.data;
    } catch (error) {
      console.error('API Error - Register:', error);
      throw error;
    }
  }

  // User favorites
  async getFavorites() {
    try {
      const response = await this.api.get('/users/favorites');
      return response.data;
    } catch (error) {
      console.error('API Error - Get Favorites:', error);
      throw error;
    }
  }

  async toggleFavorite(restaurantId: string) {
    try {
      const response = await this.api.post('/users/favorites/toggle', {
        restaurant_id: restaurantId,
      });
      return response.data;
    } catch (error) {
      console.error('API Error - Toggle Favorite:', error);
      throw error;
    }
  }

  // Special types
  async getSpecialTypes() {
    try {
      const response = await this.api.get('/special-types');
      return response.data;
    } catch (error) {
      console.error('API Error - Special Types:', error);
      throw error;
    }
  }

  // Notifications
  async sendTestNotification() {
    try {
      const response = await this.api.post('/notifications/test');
      return response.data;
    } catch (error) {
      console.error('API Error - Test Notification:', error);
      throw error;
    }
  }

  // User session management
  async getCurrentUser() {
    try {
      const userData = await AsyncStorage.getItem('user_data');
      return userData ? JSON.parse(userData) : null;
    } catch (error) {
      console.error('Error getting current user:', error);
      return null;
    }
  }

  async logout() {
    try {
      await AsyncStorage.multiRemove(['auth_token', 'user_data']);
      console.log('User logged out successfully');
    } catch (error) {
      console.error('Error logging out:', error);
    }
  }

  // Check authentication status
  async isAuthenticated(): Promise<boolean> {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      return !!token;
    } catch (error) {
      console.error('Error checking auth status:', error);
      return false;
    }
  }
}

export default new APIService();