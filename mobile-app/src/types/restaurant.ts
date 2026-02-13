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
  location?: {
    latitude: number;
    longitude: number;
  };
  // Direct lat/lng from API (some endpoints return this format)
  latitude?: number;
  longitude?: number;
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

// Coupon Types
export enum CouponType {
  PERCENTAGE = 'percentage',
  FIXED_AMOUNT = 'fixed_amount',
  BOGO = 'bogo',
  FREE_ITEM = 'free_item',
  COMBO_DEAL = 'combo_deal',
}

export enum CouponStatus {
  ACTIVE = 'active',
  PAUSED = 'paused',
  EXPIRED = 'expired',
  DRAFT = 'draft',
}

export interface Coupon {
  id: string;
  restaurant_id: string;
  owner_id: string;
  title: string;
  description: string;
  coupon_type: CouponType;
  
  // Discount details
  discount_percentage?: number;
  discount_amount?: number;
  free_item?: string;
  combo_price?: number;
  
  // Validity and limits
  valid_from: string;
  valid_until: string;
  max_redemptions?: number;
  max_per_customer: number;
  minimum_purchase?: number;
  
  // Usage tracking
  total_redemptions: number;
  total_revenue_impact: number;
  unique_customers: number;
  
  // Targeting
  target_audience: string;
  days_of_week: string[];
  time_restrictions?: {
    start: string;
    end: string;
  };
  
  // Marketing
  terms_conditions?: string;
  promotional_message?: string;
  
  // QR Code and redemption
  qr_code?: string;
  redemption_code: string;
  
  // Metadata
  status: CouponStatus;
  created_at: string;
  updated_at: string;
  
  // Analytics
  views: number;
  saves: number;
  click_rate: number;
  conversion_rate: number;
  
  // Restaurant info (for enriched coupons)
  restaurant?: {
    name: string;
    address: string;
    cuisine_type: string[];
    photos: Photo[];
  };
}

export interface CouponCreateData {
  title: string;
  description: string;
  coupon_type: CouponType;
  discount_percentage?: number;
  discount_amount?: number;
  free_item?: string;
  combo_price?: number;
  valid_from: string;
  valid_until: string;
  max_redemptions?: number;
  max_per_customer: number;
  minimum_purchase?: number;
  target_audience: string;
  days_of_week: string[];
  time_restrictions?: {
    start: string;
    end: string;
  };
  terms_conditions?: string;
  promotional_message?: string;
}