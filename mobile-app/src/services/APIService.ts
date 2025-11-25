import axios, { AxiosInstance, AxiosResponse } from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';
import { Restaurant, SearchParams, AuthResponse, User, Coupon, CouponCreateData } from '../types/restaurant';

class APIService {
  private api: AxiosInstance;
  private baseURL = process.env.REACT_APP_BACKEND_URL || '/api';
  private authCache: { isAuthenticated: boolean; timestamp: number } | null = null;
  private readonly AUTH_CACHE_DURATION = 5000; // 5 seconds cache

  constructor() {
    console.log('🔧 APIService initializing with baseURL:', this.baseURL);
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
      console.log('📡 API Request:', config.method?.toUpperCase(), config.url);
      return config;
    });

    // Add response/error interceptors for debugging
    this.api.interceptors.response.use(
      (response) => {
        console.log('✅ API Response:', response.config.method?.toUpperCase(), response.config.url, response.status);
        return response;
      },
      (error) => {
        console.error('❌ API Error:', error.config?.method?.toUpperCase(), error.config?.url, error.response?.status, error.message);
        return Promise.reject(error);
      }
    );

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
  async searchRestaurants(params: SearchParams) {
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

  async forwardGeocode(address: string, region?: string) {
    try {
      const payload: any = { address };
      if (region) {
        payload.region = region;
      }
      
      const response = await this.api.post('/geocode/forward', payload);
      return response.data;
    } catch (error) {
      console.error('API Error - Forward Geocoding:', error);
      throw error;
    }
  }

  // User authentication
  async login(email: string, password: string): Promise<AuthResponse> {
    try {
      const response = await this.api.post('/users/login', {
        email,
        password,
      });
      
      const { access_token, user } = response.data;
      await AsyncStorage.setItem('auth_token', access_token);
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
  }): Promise<AuthResponse> {
    try {
      const response = await this.api.post('/users/register', userData);
      
      const { access_token, user } = response.data;
      await AsyncStorage.setItem('auth_token', access_token);
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

  async addFavorite(restaurantId: string) {
    try {
      const response = await this.api.post(`/users/favorites/${restaurantId}`);
      return response.data;
    } catch (error) {
      console.error('API Error - Add Favorite:', error);
      throw error;
    }
  }

  async removeFavorite(restaurantId: string) {
    try {
      const response = await this.api.delete(`/users/favorites/${restaurantId}`);
      return response.data;
    } catch (error) {
      console.error('API Error - Remove Favorite:', error);
      throw error;
    }
  }

  // Toggle favorite (combined add/remove logic)
  async toggleFavorite(restaurantId: string, isFavorite: boolean) {
    try {
      if (isFavorite) {
        return await this.removeFavorite(restaurantId);
      } else {
        return await this.addFavorite(restaurantId);
      }
    } catch (error) {
      console.error('API Error - Toggle Favorite:', error);
      throw error;
    }
  }

  // Special types
  async getSpecialTypes() {
    try {
      const response = await this.api.get('/specials/types');
      return response.data.special_types;
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
  async getCurrentUser(): Promise<User | null> {
    try {
      const userData = await AsyncStorage.getItem('user_data');
      return userData ? JSON.parse(userData) : null;
    } catch (error) {
      console.error('Error getting current user:', error);
      return null;
    }
  }

  async getCurrentUserFromServer(): Promise<User> {
    try {
      const response = await this.api.get('/users/me');
      return response.data;
    } catch (error) {
      console.error('API Error - Get Current User from Server:', error);
      throw error;
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

  // Check if user is authenticated with server validation
  async isAuthenticated(): Promise<boolean> {
    try {
      const token = await AsyncStorage.getItem('auth_token');
      if (!token) {
        return false;
      }

      // Validate token with server
      try {
        const response = await this.api.get('/users/me');
        return response.status === 200;
      } catch (error) {
        // Token is invalid, clear it
        await AsyncStorage.removeItem('auth_token');
        await AsyncStorage.removeItem('user_data');
        return false;
      }
    } catch (error) {
      console.error('Error checking authentication:', error);
      return false;
    }
  }

  // =================== COUPON SERVICES ===================

  // Get coupons near a location (for customers)
  async getNearbyCoupons(latitude: number, longitude: number, radius: number = 16094) {
    try {
      const response = await this.api.get('/coupons/near', {
        params: { latitude, longitude, radius }
      });
      return response.data;
    } catch (error) {
      console.error('API Error - Get Nearby Coupons:', error);
      throw error;
    }
  }

  // Get a single coupon by ID
  async getCouponDetails(couponId: string) {
    try {
      const response = await this.api.get(`/coupons/${couponId}`);
      return response.data;
    } catch (error) {
      console.error('API Error - Get Coupon Details:', error);
      throw error;
    }
  }

  // Save a coupon (add to user's saved coupons)
  async saveCoupon(couponId: string) {
    try {
      const response = await this.api.post(`/users/coupons/${couponId}/save`);
      return response.data;
    } catch (error) {
      console.error('API Error - Save Coupon:', error);
      throw error;
    }
  }

  // Remove a coupon from saved
  async removeSavedCoupon(couponId: string) {
    try {
      const response = await this.api.delete(`/users/coupons/${couponId}/save`);
      return response.data;
    } catch (error) {
      console.error('API Error - Remove Saved Coupon:', error);
      throw error;
    }
  }

  // Get user's saved coupons
  async getSavedCoupons() {
    try {
      const response = await this.api.get('/users/coupons/saved');
      return response.data;
    } catch (error) {
      console.error('API Error - Get Saved Coupons:', error);
      throw error;
    }
  }

  // Track coupon view (analytics)
  async trackCouponView(couponId: string) {
    try {
      const response = await this.api.post(`/coupons/${couponId}/view`);
      return response.data;
    } catch (error) {
      console.error('API Error - Track Coupon View:', error);
      // Don't throw error for analytics tracking
      return null;
    }
  }

  // Redeem a coupon
  async redeemCoupon(couponId: string, orderTotal?: number) {
    try {
      const response = await this.api.post(`/coupons/${couponId}/redeem`, {
        order_total: orderTotal
      });
      return response.data;
    } catch (error) {
      console.error('API Error - Redeem Coupon:', error);
      throw error;
    }
  }

  // =================== OWNER COUPON SERVICES ===================

  // Create a coupon (owner only)
  async createCoupon(restaurantId: string, couponData: any) {
    try {
      const response = await this.api.post(`/owners/coupons?restaurant_id=${restaurantId}`, couponData);
      return response.data;
    } catch (error) {
      console.error('API Error - Create Coupon:', error);
      throw error;
    }
  }

  // Get owner's coupons
  async getOwnerCoupons(restaurantId?: string) {
    try {
      const params = restaurantId ? { restaurant_id: restaurantId } : {};
      const response = await this.api.get('/owners/coupons', { params });
      return response.data;
    } catch (error) {
      console.error('API Error - Get Owner Coupons:', error);
      throw error;
    }
  }

  // Update coupon status (pause/activate)
  async updateCouponStatus(couponId: string, status: string) {
    try {
      const response = await this.api.patch(`/coupons/${couponId}/status`, { status });
      return response.data;
    } catch (error) {
      console.error('API Error - Update Coupon Status:', error);
      throw error;
    }
  }

  // Delete a coupon
  async deleteCoupon(couponId: string) {
    try {
      const response = await this.api.delete(`/coupons/${couponId}`);
      return response.data;
    } catch (error) {
      console.error('API Error - Delete Coupon:', error);
      throw error;
    }
  }

  // Get coupon analytics
  async getCouponAnalytics(couponId: string, days: number = 30) {
    try {
      const response = await this.api.get(`/coupons/${couponId}/analytics`, {
        params: { days }
      });
      return response.data;
    } catch (error) {
      console.error('API Error - Get Coupon Analytics:', error);
      throw error;
    }
  }
}

export default new APIService();