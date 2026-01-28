/**
 * Analytics Service
 * Tracks user engagement with restaurants and specials
 */

const API = process.env.REACT_APP_BACKEND_URL 
  ? `${process.env.REACT_APP_BACKEND_URL}/api` 
  : '/api';

// Event types
export const AnalyticsEventType = {
  CARD_VIEW: 'card_view',
  CARD_CLICK: 'card_click',
  SPECIAL_VIEW: 'special_view',
  SHARE_CLICK: 'share_click',
  FAVORITE_ADD: 'favorite_add',
  FAVORITE_REMOVE: 'favorite_remove',
  DIRECTIONS_CLICK: 'directions_click',
  CALL_CLICK: 'call_click',
  CHECKIN_ATTEMPT: 'checkin_attempt',
  CHECKIN_VERIFIED: 'checkin_verified',
  CHECKIN_FAILED: 'checkin_failed'
};

// Track viewed cards to avoid duplicate tracking
const viewedCards = new Set();

/**
 * Track an analytics event
 * @param {string} eventType - Type of event from AnalyticsEventType
 * @param {string} restaurantId - Restaurant ID
 * @param {object} options - Additional options (specialId, metadata)
 */
export const trackEvent = async (eventType, restaurantId, options = {}) => {
  try {
    // Skip duplicate card views in same session
    if (eventType === AnalyticsEventType.CARD_VIEW) {
      if (viewedCards.has(restaurantId)) {
        return; // Already tracked this card view
      }
      viewedCards.add(restaurantId);
    }

    const userId = localStorage.getItem('user_id') || null;
    
    const payload = {
      event_type: eventType,
      restaurant_id: restaurantId,
      special_id: options.specialId || null,
      user_id: userId,
      metadata: options.metadata || null
    };

    // Fire and forget - don't wait for response
    fetch(`${API}/analytics/event`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(payload)
    }).catch(err => {
      // Silently fail - don't disrupt user experience
      console.debug('Analytics event failed:', err);
    });
  } catch (error) {
    // Silently fail
    console.debug('Analytics tracking error:', error);
  }
};

/**
 * Track when a restaurant card is viewed (displayed in search results)
 */
export const trackCardView = (restaurantId) => {
  trackEvent(AnalyticsEventType.CARD_VIEW, restaurantId);
};

/**
 * Track when a user clicks on a restaurant card
 */
export const trackCardClick = (restaurantId) => {
  trackEvent(AnalyticsEventType.CARD_CLICK, restaurantId);
};

/**
 * Track when a user views a specific special/deal
 */
export const trackSpecialView = (restaurantId, specialId) => {
  trackEvent(AnalyticsEventType.SPECIAL_VIEW, restaurantId, { specialId });
};

/**
 * Track when a user clicks share button
 */
export const trackShareClick = (restaurantId, shareType = 'unknown') => {
  trackEvent(AnalyticsEventType.SHARE_CLICK, restaurantId, {
    metadata: { share_type: shareType }
  });
};

/**
 * Track when a user adds restaurant to favorites
 */
export const trackFavoriteAdd = (restaurantId) => {
  trackEvent(AnalyticsEventType.FAVORITE_ADD, restaurantId);
};

/**
 * Track when a user removes restaurant from favorites
 */
export const trackFavoriteRemove = (restaurantId) => {
  trackEvent(AnalyticsEventType.FAVORITE_REMOVE, restaurantId);
};

/**
 * Track when a user clicks "Get Directions"
 */
export const trackDirectionsClick = (restaurantId) => {
  trackEvent(AnalyticsEventType.DIRECTIONS_CLICK, restaurantId);
};

/**
 * Track when a user clicks phone number
 */
export const trackCallClick = (restaurantId) => {
  trackEvent(AnalyticsEventType.CALL_CLICK, restaurantId);
};

/**
 * Verify user check-in at a restaurant
 * @param {string} restaurantId - Restaurant to check in to
 * @param {string} token - User's auth token
 * @returns {Promise<object>} - Check-in result
 */
export const verifyCheckIn = async (restaurantId, token) => {
  return new Promise((resolve, reject) => {
    if (!navigator.geolocation) {
      reject(new Error('Geolocation is not supported by your browser'));
      return;
    }

    navigator.geolocation.getCurrentPosition(
      async (position) => {
        try {
          const response = await fetch(`${API}/analytics/checkin`, {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
              restaurant_id: restaurantId,
              latitude: position.coords.latitude,
              longitude: position.coords.longitude
            })
          });

          const data = await response.json();
          
          if (!response.ok) {
            throw new Error(data.detail || 'Check-in failed');
          }

          resolve(data);
        } catch (error) {
          reject(error);
        }
      },
      (error) => {
        let message = 'Unable to get your location';
        switch (error.code) {
          case error.PERMISSION_DENIED:
            message = 'Location permission denied. Please enable location access to check in.';
            break;
          case error.POSITION_UNAVAILABLE:
            message = 'Location information unavailable.';
            break;
          case error.TIMEOUT:
            message = 'Location request timed out.';
            break;
          default:
            break;
        }
        reject(new Error(message));
      },
      {
        enableHighAccuracy: true,
        timeout: 10000,
        maximumAge: 0
      }
    );
  });
};

/**
 * Reset viewed cards tracking (call on new search)
 */
export const resetViewedCards = () => {
  viewedCards.clear();
};

export default {
  trackEvent,
  trackCardView,
  trackCardClick,
  trackSpecialView,
  trackShareClick,
  trackFavoriteAdd,
  trackFavoriteRemove,
  trackDirectionsClick,
  trackCallClick,
  verifyCheckIn,
  resetViewedCards,
  AnalyticsEventType
};
