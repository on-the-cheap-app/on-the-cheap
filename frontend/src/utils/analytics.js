/**
 * Google Analytics 4 (GA4) Integration for On-the-Cheap App
 * 
 * This module provides comprehensive event tracking for the restaurant discovery app,
 * including user behavior, business metrics, and conversion tracking.
 */

// Check if gtag is available (only in production with real GA4 ID)
const isGtagAvailable = () => {
  return typeof window !== 'undefined' && typeof window.gtag === 'function';
};

// Enhanced ecommerce tracking for restaurant interactions
export const trackRestaurantView = (restaurant) => {
  if (!isGtagAvailable()) {
    console.log('Analytics: Restaurant View -', restaurant.name);
    return;
  }

  window.gtag('event', 'view_item', {
    currency: 'USD',
    value: restaurant.specials?.length || 0,
    items: [{
      item_id: restaurant.id,
      item_name: restaurant.name,
      item_category: 'Restaurant',
      item_variant: restaurant.vendor_type || 'permanent',
      item_brand: restaurant.source,
      location_id: restaurant.address,
      quantity: 1,
      price: restaurant.price_level || 0
    }]
  });

  // Custom restaurant view event
  window.gtag('event', 'restaurant_viewed', {
    restaurant_id: restaurant.id,
    restaurant_name: restaurant.name,
    restaurant_source: restaurant.source,
    has_specials: (restaurant.specials?.length > 0),
    specials_count: restaurant.specials?.length || 0,
    is_mobile_vendor: restaurant.is_mobile_vendor || false,
    vendor_type: restaurant.vendor_type || 'permanent',
    rating: restaurant.rating || null,
    distance_meters: restaurant.distance || null
  });
};

// Search tracking with comprehensive parameters
export const trackRestaurantSearch = (searchParams, resultCount, resultSources) => {
  if (!isGtagAvailable()) {
    console.log('Analytics: Restaurant Search -', searchParams);
    return;
  }

  window.gtag('event', 'search', {
    search_term: searchParams.location || 'GPS Location',
    search_parameters: JSON.stringify({
      radius: searchParams.radius,
      special_type: searchParams.special_type,
      vendor_type: searchParams.vendor_type
    })
  });

  // Custom detailed search event
  window.gtag('event', 'restaurant_search_performed', {
    search_location: searchParams.location || 'GPS Location',
    search_coordinates: `${searchParams.latitude},${searchParams.longitude}`,
    radius_meters: searchParams.radius,
    special_type_filter: searchParams.special_type || 'all',
    vendor_type_filter: searchParams.vendor_type || 'all',
    query: searchParams.query || null,
    results_count: resultCount,
    results_sources: JSON.stringify(resultSources || {}),
    search_method: searchParams.location ? 'address' : 'gps'
  });
};

// User engagement tracking
export const trackViewToggle = (fromView, toView) => {
  if (!isGtagAvailable()) {
    console.log('Analytics: View Toggle -', `${fromView} to ${toView}`);
    return;
  }

  window.gtag('event', 'view_toggle', {
    event_category: 'User Interface',
    event_label: `${fromView}_to_${toView}`,
    from_view: fromView,
    to_view: toView
  });
};

// Filter usage tracking
export const trackFilterChange = (filterType, oldValue, newValue) => {
  if (!isGtagAvailable()) {
    console.log('Analytics: Filter Change -', `${filterType}: ${oldValue} → ${newValue}`);
    return;
  }

  window.gtag('event', 'filter_applied', {
    event_category: 'Search Filters',
    filter_type: filterType,
    old_value: oldValue || 'none',
    new_value: newValue || 'none',
    event_label: `${filterType}_${newValue}`
  });
};

// User authentication tracking
export const trackUserRegistration = (userType = 'user') => {
  if (!isGtagAvailable()) {
    console.log('Analytics: User Registration -', userType);
    return;
  }

  window.gtag('event', 'sign_up', {
    method: 'email',
    event_category: 'User Authentication',
    user_type: userType
  });

  // Custom registration event
  window.gtag('event', 'user_registered', {
    registration_type: userType,
    timestamp: new Date().toISOString()
  });
};

export const trackUserLogin = (userType = 'user') => {
  if (!isGtagAvailable()) {
    console.log('Analytics: User Login -', userType);
    return;
  }

  window.gtag('event', 'login', {
    method: 'email',
    event_category: 'User Authentication',
    user_type: userType
  });
};

// Restaurant interaction tracking
export const trackRestaurantFavorite = (restaurant, action) => {
  if (!isGtagAvailable()) {
    console.log('Analytics: Restaurant Favorite -', action, restaurant.name);
    return;
  }

  const eventName = action === 'add' ? 'add_to_favorites' : 'remove_from_favorites';
  
  window.gtag('event', eventName, {
    currency: 'USD',
    value: restaurant.specials?.length || 0,
    items: [{
      item_id: restaurant.id,
      item_name: restaurant.name,
      item_category: 'Restaurant',
      item_variant: restaurant.vendor_type || 'permanent'
    }]
  });

  // Custom favorite event
  window.gtag('event', 'restaurant_favorited', {
    action: action,
    restaurant_id: restaurant.id,
    restaurant_name: restaurant.name,
    restaurant_source: restaurant.source,
    is_mobile_vendor: restaurant.is_mobile_vendor || false,
    has_specials: (restaurant.specials?.length > 0)
  });
};

// Social sharing tracking
export const trackRestaurantShare = (restaurant, platform) => {
  if (!isGtagAvailable()) {
    console.log('Analytics: Restaurant Share -', platform, restaurant.name);
    return;
  }

  window.gtag('event', 'share', {
    method: platform,
    content_type: 'restaurant',
    content_id: restaurant.id,
    event_category: 'Social Sharing',
    event_label: `${platform}_${restaurant.vendor_type || 'permanent'}`
  });

  // Custom share event
  window.gtag('event', 'restaurant_shared', {
    platform: platform,
    restaurant_id: restaurant.id,
    restaurant_name: restaurant.name,
    restaurant_source: restaurant.source,
    is_mobile_vendor: restaurant.is_mobile_vendor || false,
    has_specials: (restaurant.specials?.length > 0),
    specials_count: restaurant.specials?.length || 0
  });
};

// Transportation tracking
export const trackRideRequest = (restaurant, rideService) => {
  if (!isGtagAvailable()) {
    console.log('Analytics: Ride Request -', rideService, restaurant.name);
    return;
  }

  window.gtag('event', 'generate_lead', {
    currency: 'USD',
    value: 15.00, // Average ride cost
    event_category: 'Transportation',
    event_label: `${rideService}_${restaurant.vendor_type || 'permanent'}`
  });

  // Custom ride event
  window.gtag('event', 'ride_requested', {
    service: rideService,
    destination_type: restaurant.is_mobile_vendor ? 'mobile_vendor' : 'restaurant',
    restaurant_id: restaurant.id,
    restaurant_name: restaurant.name,
    restaurant_source: restaurant.source,
    has_specials: (restaurant.specials?.length > 0)
  });
};

// Map interaction tracking
export const trackMapInteraction = (action, details = {}) => {
  if (!isGtagAvailable()) {
    console.log('Analytics: Map Interaction -', action, details);
    return;
  }

  window.gtag('event', 'map_interaction', {
    event_category: 'Map Usage',
    action: action,
    event_label: action,
    ...details
  });
};

// Special engagement tracking
export const trackSpecialInteraction = (restaurant, special, action) => {
  if (!isGtagAvailable()) {
    console.log('Analytics: Special Interaction -', action, special.title);
    return;
  }

  window.gtag('event', 'special_engagement', {
    event_category: 'Specials',
    action: action,
    special_type: special.special_type,
    special_price: special.price,
    restaurant_source: restaurant.source,
    is_mobile_vendor: restaurant.is_mobile_vendor || false
  });
};

// Page view tracking for SPA
export const trackPageView = (page_title, page_location) => {
  if (!isGtagAvailable()) {
    console.log('Analytics: Page View -', page_title);
    return;
  }

  window.gtag('config', 'GA_MEASUREMENT_ID', {
    page_title: page_title,
    page_location: page_location
  });
};

// Custom conversion events
export const trackConversion = (conversionType, details = {}) => {
  if (!isGtagAvailable()) {
    console.log('Analytics: Conversion -', conversionType, details);
    return;
  }

  window.gtag('event', 'conversion', {
    event_category: 'Conversions',
    conversion_type: conversionType,
    event_label: conversionType,
    ...details
  });
};

// User session tracking
export const trackSessionStart = () => {
  if (!isGtagAvailable()) {
    console.log('Analytics: Session Start');
    return;
  }

  window.gtag('event', 'session_start', {
    event_category: 'Session',
    timestamp: new Date().toISOString()
  });
};

// Error tracking
export const trackError = (error, context) => {
  if (!isGtagAvailable()) {
    console.log('Analytics: Error -', error, context);
    return;
  }

  window.gtag('event', 'exception', {
    description: error,
    fatal: false,
    context: context
  });
};

// Performance tracking
export const trackPerformance = (metric, value, context = {}) => {
  if (!isGtagAvailable()) {
    console.log('Analytics: Performance -', metric, value);
    return;
  }

  window.gtag('event', 'timing_complete', {
    name: metric,
    value: Math.round(value),
    event_category: 'Performance',
    ...context
  });
};

export default {
  trackRestaurantView,
  trackRestaurantSearch,
  trackViewToggle,
  trackFilterChange,
  trackUserRegistration,
  trackUserLogin,
  trackRestaurantFavorite,
  trackRestaurantShare,
  trackRideRequest,
  trackMapInteraction,
  trackSpecialInteraction,
  trackPageView,
  trackConversion,
  trackSessionStart,
  trackError,
  trackPerformance
};