// Restaurant and related interfaces for mobile app

export interface Photo {
  url: string;
  width: number;
  height: number;
  is_fallback: boolean;
}

export interface RestaurantSpecial {
  id: string;
  title: string;
  description: string;
  special_type: string;
  price?: number;
  original_price?: number;
  days_available: string[];
  time_start: string;
  time_end: string;
  is_active: boolean;
  created_at: string;
}

export interface Restaurant {
  id: string;
  name: string;
  address: string;
  location: {
    latitude: number;
    longitude: number;
  };
  phone?: string;
  website?: string;
  cuisine_type: string[];
  rating?: number;
  price_level?: number;
  photos: Photo[];
  specials: RestaurantSpecial[];
  specials_message?: string;
  has_current_specials?: boolean;
  is_verified: boolean;
  is_mobile_vendor?: boolean;
  vendor_type?: string;
  distance?: number;
  source: string;
  created_at: string;
}

export interface SearchParams {
  latitude: number;
  longitude: number;
  radius?: number;
  special_type?: string;
  vendor_type?: string;
  query?: string;
  limit?: number;
}

export interface User {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  favorite_restaurant_ids: string[];
  preferences?: Record<string, any>;
  created_at: string;
}

export interface AuthResponse {
  message: string;
  access_token: string;
  token_type: string;
  user_type: string;
  user: User;
}