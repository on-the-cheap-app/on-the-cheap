import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import axios from "axios";
import { MapPin, Clock, DollarSign, Phone, Globe, Star, Search, Navigation, Building2, ArrowLeft, User, Heart, Share2, MessageCircle, Car, ExternalLink, X, Map, List, Truck, Bell, CheckCircle } from "lucide-react";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import OwnerPortal from "./OwnerPortal";
import UserAuth from "./UserAuth";
import OwnerAuth from './components/OwnerAuth';
import OwnerDashboard from './components/OwnerDashboard';
import PrivacyPolicyModal from './components/PrivacyPolicyModal';
import AddressInput from "./components/AddressInput";

import RestaurantMap from "./components/RestaurantMap";
import NotificationPreferences from "./components/NotificationPreferences";
import PWAInstallBanner from "./components/PWAInstallBanner";
import PWAManualInstall from "./components/PWAManualInstall";
import OfflineIndicator from "./components/OfflineIndicator";
import CouponDiscovery from "./components/CouponDiscovery";
import useNotifications from "./hooks/useNotifications";
import { usePWA } from "./hooks/usePWA";
import * as Analytics from './utils/analytics';
import PartnerInfo from "./pages/PartnerInfo";
import { 
  trackCardView, 
  trackCardClick, 
  trackShareClick, 
  trackFavoriteAdd, 
  trackFavoriteRemove,
  trackDirectionsClick,
  trackCallClick,
  trackSpecialView,
  verifyCheckIn,
  resetViewedCards
} from './services/analyticsService';
import CheckInButton from './components/CheckInButton';

// Get backend URL from environment variables
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
// Ensure API always has /api suffix for backend routes
const API = BACKEND_URL ? `${BACKEND_URL}/api` : '/api';

// Debug logging
console.log('🔍 App.js Debug - BACKEND_URL:', BACKEND_URL);
console.log('🔍 App.js Debug - API:', API);
console.log('🔍 App.js Debug - process.env.REACT_APP_BACKEND_URL:', process.env.REACT_APP_BACKEND_URL);

// App link for sharing - uses current domain or fallback
const APP_LINK = process.env.REACT_APP_FRONTEND_URL || window.location.origin;

// Helper functions for sharing and rides
const generateShareMessage = (restaurant) => {
  const specialsText = restaurant.specials?.length > 0 
    ? `Current specials: ${restaurant.specials.map(s => `${s.title} - $${s.price}`).join(', ')}`
    : restaurant.specials_message || 'Check for current specials';
  
  return `Check out ${restaurant.name}! 📍 ${restaurant.address} - ${specialsText}. Found via On-the-Cheap app 🍴 ${APP_LINK}`;
};

const getShareUrls = (restaurant) => {
  const message = generateShareMessage(restaurant);
  const encodedMessage = encodeURIComponent(message);
  
  // SMS URL format varies by platform
  // iOS: sms:&body=  |  Android: sms:?body=  |  Desktop: sms:?body= (but often unreliable)
  const userAgent = navigator.userAgent;
  const isIOS = /iPad|iPhone|iPod/.test(userAgent);
  const isMac = /Macintosh/.test(userAgent) && !isIOS;
  
  // For Mac desktop with Google Messages, use the Android format
  const smsUrl = isIOS 
    ? `sms:&body=${encodedMessage}` 
    : `sms:?body=${encodedMessage}`;
  
  return {
    sms: smsUrl,
    whatsapp: `https://wa.me/?text=${encodedMessage}`,
    // Removed telegram and messenger - unreliable
  };
};

const getRideUrls = (restaurant) => {
  const address = encodeURIComponent(restaurant.address || '');
  const lat = restaurant.location?.latitude;
  const lng = restaurant.location?.longitude;
  
  return {
    uber: `https://m.uber.com/ul/?action=setPickup&pickup=my_location&dropoff[formatted_address]=${address}${lat && lng ? `&dropoff[latitude]=${lat}&dropoff[longitude]=${lng}` : ''}`,
    lyft: lat && lng 
      ? `https://lyft.com/ride?id=lyft&destination[latitude]=${lat}&destination[longitude]=${lng}`
      : `https://lyft.com/ride?id=lyft&destination[address]=${address}`
  };
};

const openShareLink = async (url, platform, message) => {
  // For SMS on desktop, try Web Share API first (works better with Google Messages)
  if (platform === 'sms') {
    // Check if Web Share API is available and we're on desktop
    const isMobile = /Android|iPhone|iPad|iPod/i.test(navigator.userAgent);
    
    if (!isMobile && navigator.share) {
      try {
        await navigator.share({ text: message });
        return;
      } catch (err) {
        // User cancelled or share failed, fall through to URL method
        if (err.name === 'AbortError') return;
      }
    }
    
    // Fallback to sms: URL
    window.location.href = url;
  } else {
    window.open(url, '_blank', 'noopener,noreferrer');
  }
};

// Analytics-enabled share function
const handleShare = (restaurant, platform) => {
  Analytics.trackRestaurantShare(restaurant, platform);
  trackShareClick(restaurant.id, platform); // Track for owner analytics
  const shareUrls = getShareUrls(restaurant);
  const message = generateShareMessage(restaurant);
  openShareLink(shareUrls[platform], platform, message);
};

// Analytics-enabled ride function  
const handleRide = (restaurant, service) => {
  Analytics.trackRideRequest(restaurant, service);
  trackDirectionsClick(restaurant.id); // Track for owner analytics
  const rideUrls = getRideUrls(restaurant);
  openShareLink(rideUrls[service], service);
};

function App() {
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(false);
  const [searchLocation, setSearchLocation] = useState("");
  const [coordinates, setCoordinates] = useState(null);
  const [specialTypes, setSpecialTypes] = useState([]);
  const [selectedSpecialType, setSelectedSpecialType] = useState("");
  const [searchRadius, setSearchRadius] = useState(8047); // 5 miles default
  const [lastSearch, setLastSearch] = useState(null);
  const [showOwnerPortal, setShowOwnerPortal] = useState(false);
  const [showUserAuth, setShowUserAuth] = useState(false);
  const [currentUser, setCurrentUser] = useState(null);
  const [authToken, setAuthToken] = useState(null);
  const [userFavorites, setUserFavorites] = useState([]);
  const [userType, setUserType] = useState(null); // 'user' or 'owner'
  
  // Ref to track if initial search has been performed
  const hasSearchedRef = useRef(false);
  const coordinatesRef = useRef(null);
  
  // Owner dashboard state
  const [showOwnerAuth, setShowOwnerAuth] = useState(false);
  const [showOwnerDashboard, setShowOwnerDashboard] = useState(false);
  const [showPrivacyPolicy, setShowPrivacyPolicy] = useState(false);

  const [viewMode, setViewMode] = useState('list'); // 'list' or 'map'
  const [selectedVendorType, setSelectedVendorType] = useState('all'); // 'all', 'permanent', 'mobile'
  const [showNotificationPreferences, setShowNotificationPreferences] = useState(false);
  const [activeView, setActiveView] = useState('restaurants'); // 'restaurants' or 'coupons'
  
  // OneSignal hook
  const { isEnabled: notificationsEnabled, isInitialized: notificationsInitialized, tagUser } = useNotifications();
  
  // PWA hook
  const { cacheRestaurantData, getCachedRestaurantData, isOnline } = usePWA();

  // Check if we're on the privacy policy page, delete account page, or partner info page
  const isPrivacyPage = window.location.pathname === '/privacy';
  const isDeleteAccountPage = window.location.pathname === '/delete-account';
  const isPartnerInfoPage = window.location.pathname === '/partner-info';

  useEffect(() => {
    // Initialize analytics
    Analytics.trackSessionStart();
    Analytics.trackPageView('Restaurant Discovery', window.location.href);
    
    fetchSpecialTypes();
    
    // Check if user is already logged in
    const userToken = localStorage.getItem('user_token');
    if (userToken) {
      fetchCurrentUser();
    }
  }, []);

  const fetchCurrentUser = async () => {
    try {
      const userToken = localStorage.getItem('user_token');
      if (userToken) {
        const response = await axios.get(`${API}/users/me`, {
          headers: { Authorization: `Bearer ${userToken}` }
        });
        setCurrentUser(response.data);
        setUserType('user'); // Set userType when restoring session
        fetchUserFavorites();
      }
    } catch (error) {
      console.error('Error fetching current user:', error);
      // If token is invalid, clear it
      localStorage.removeItem('user_token');
    }
  };

  const fetchUserFavorites = async () => {
    try {
      const userToken = localStorage.getItem('user_token');
      if (userToken) {
        const response = await axios.get(`${API}/users/favorites`, {
          headers: { Authorization: `Bearer ${userToken}` }
        });
        const favorites = response.data.favorites || [];
        setUserFavorites(favorites);
      }
    } catch (error) {
      console.error('Error fetching user favorites:', error.response?.data || error.message);
    }
  };

  const fetchSpecialTypes = async () => {
    try {
      const response = await axios.get(`${API}/specials/types`);
      setSpecialTypes(response.data.special_types);
    } catch (error) {
      console.error("Error fetching special types:", error);
    }
  };

  // Auto re-search when filters change (if we already have coordinates from a previous search)
  useEffect(() => {
    // Only re-search if we have done an initial search (tracked via ref)
    if (hasSearchedRef.current && coordinatesRef.current) {
      console.log('Filter changed - re-searching with:', { selectedSpecialType, selectedVendorType, searchRadius });
      // Debounce to avoid too many requests
      const timeoutId = setTimeout(() => {
        searchRestaurants(coordinatesRef.current.latitude, coordinatesRef.current.longitude, {
          specialType: selectedSpecialType,
          vendorType: selectedVendorType,
          radius: searchRadius
        });
      }, 300);
      return () => clearTimeout(timeoutId);
    }
  }, [selectedSpecialType, selectedVendorType, searchRadius]);

  const getCurrentLocation = () => {
    setLoading(true);
    if ("geolocation" in navigator) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          const coords = {
            latitude: position.coords.latitude,
            longitude: position.coords.longitude
          };
          setCoordinates(coords);
          coordinatesRef.current = coords; // Store in ref for filter useEffect
          setSearchLocation("Current Location");
          searchRestaurants(coords.latitude, coords.longitude);
        },
        (error) => {
          console.error("Error getting location:", error);
          setLoading(false);
          alert("Unable to get your location. Please enter a city or address.");
        }
      );
    } else {
      setLoading(false);
      alert("Geolocation is not supported by this browser.");
    }
  };

  const geocodeLocation = async (location) => {
    try {
      // Use backend geocoding endpoint (which uses Google Places API)
      const response = await axios.get(`${API}/geocode`, {
        params: { address: location }
      });
      
      if (response.data.coordinates) {
        return response.data.coordinates;
      }
    } catch (error) {
      console.error('Geocoding error:', error);
    }

    // Fallback: try common locations for basic coverage
    const commonLocations = {
      "san francisco": { latitude: 37.7749, longitude: -122.4194 },
      "new york": { latitude: 40.7128, longitude: -74.0060 },
      "los angeles": { latitude: 34.0522, longitude: -118.2437 },
      "chicago": { latitude: 41.8781, longitude: -87.6298 },
      "miami": { latitude: 25.7617, longitude: -80.1918 },
      "new orleans": { latitude: 29.9511, longitude: -90.0715 },
      "boston": { latitude: 42.3601, longitude: -71.0589 },
      "seattle": { latitude: 47.6062, longitude: -122.3321 },
      "denver": { latitude: 39.7392, longitude: -104.9903 },
      "atlanta": { latitude: 33.7490, longitude: -84.3880 }
    };

    const locationKey = location.toLowerCase();
    for (const [key, coords] of Object.entries(commonLocations)) {
      if (locationKey.includes(key)) {
        return coords;
      }
    }

    // Default to San Francisco if location not recognized
    return { latitude: 37.7749, longitude: -122.4194 };
  };

  const handleLocationSearch = async () => {
    if (!searchLocation.trim()) return;
    
    setLoading(true);
    try {
      const coords = await geocodeLocation(searchLocation);
      setCoordinates(coords);
      coordinatesRef.current = coords; // Store in ref for filter useEffect
      searchRestaurants(coords.latitude, coords.longitude);
    } catch (error) {
      console.error("Error geocoding location:", error);
      setLoading(false);
    }
  };

  // Enhanced handler for AddressInput component
  const handleAddressSelect = (geocodeResult) => {
    setSearchLocation(geocodeResult.formatted_address);
    const coords = {
      latitude: geocodeResult.latitude,
      longitude: geocodeResult.longitude
    };
    setCoordinates(coords);
    coordinatesRef.current = coords; // Store in ref for filter useEffect
    setLoading(true);
    searchRestaurants(geocodeResult.latitude, geocodeResult.longitude);
  };

  // Handler for manual text input in AddressInput
  const handleAddressInputChange = (value) => {
    setSearchLocation(value);
  };

  const searchRestaurants = async (latitude, longitude, filters = {}) => {
    if (!latitude || !longitude) return;
    
    setLoading(true);
    const searchStartTime = performance.now();
    
    // Use passed filters or fall back to current state
    const specialType = filters.specialType !== undefined ? filters.specialType : selectedSpecialType;
    const vendorType = filters.vendorType !== undefined ? filters.vendorType : selectedVendorType;
    const radius = filters.radius !== undefined ? filters.radius : searchRadius;
    
    try {
      const params = {
        latitude,
        longitude,
        radius: radius,
      };

      if (specialType && specialType !== "all") {
        params.special_type = specialType;
      }
      
      if (vendorType && vendorType !== "all") {
        params.vendor_type = vendorType;
      }

      let searchResults, searchLocation, sourceSummary;
      
      if (isOnline) {
        // Online: fetch fresh data
        const response = await axios.get(`${API}/restaurants/search`, { params });
        searchResults = response.data.restaurants;
        searchLocation = response.data.search_location;
        sourceSummary = response.data.source_summary;
        
        // Cache results for offline use
        await cacheRestaurantData(searchResults, { 
          location: searchLocation,
          coordinates: { latitude, longitude },
          params 
        });
      } else {
        // Offline: try to use cached data
        const cachedData = await getCachedRestaurantData();
        if (cachedData && cachedData.restaurants) {
          searchResults = cachedData.restaurants;
          searchLocation = cachedData.location.location || 'Cached Location';
          sourceSummary = null; // No source summary for cached data
          console.log('📦 Using cached restaurant data for offline viewing');
        } else {
          throw new Error('No cached data available offline');
        }
      }
      
      const searchTime = performance.now() - searchStartTime;
      
      setRestaurants(searchResults);
      setLastSearch(searchLocation);
      
      // Mark that we've done at least one search (for filter auto-refresh)
      hasSearchedRef.current = true;
      
      // Track card views for owner analytics (reset and track new results)
      resetViewedCards();
      searchResults.forEach(restaurant => {
        trackCardView(restaurant.id);
      });
      
      // Track search analytics
      Analytics.trackRestaurantSearch({
        location: searchLocation,
        latitude,
        longitude,
        radius: radius,
        special_type: specialType,
        vendor_type: vendorType,
        query: null
      }, searchResults.length, sourceSummary);
      
      // Track search performance
      Analytics.trackPerformance('restaurant_search', searchTime, {
        results_count: searchResults.length,
        has_filters: !!(specialType || vendorType)
      });
      
      setLoading(false);
    } catch (error) {
      console.error("Error searching restaurants:", error);
      Analytics.trackError(error.message, 'restaurant_search');
      setLoading(false);
    }
  };

  const clearSearch = () => {
    setRestaurants([]);
    setSearchLocation("");
    setCoordinates(null);
    setLastSearch(null);
    setSelectedSpecialType("");
    setSelectedVendorType("all"); // Reset vendor type filter
    setSearchRadius(8047); // Reset to 5 miles default
    // Reset refs
    hasSearchedRef.current = false;
    coordinatesRef.current = null;
    Analytics.trackConversion('search_cleared');
    console.log("Search cleared - ready for new search");
  };

  // Analytics wrapper functions for filters
  const handleSpecialTypeChange = (newValue) => {
    Analytics.trackFilterChange('special_type', selectedSpecialType, newValue);
    setSelectedSpecialType(newValue);
  };

  const handleVendorTypeChange = (newValue) => {
    Analytics.trackFilterChange('vendor_type', selectedVendorType, newValue);
    setSelectedVendorType(newValue);
  };

  const handleRadiusChange = (newValue) => {
    const oldRadius = searchRadius;
    const newRadius = parseInt(newValue);
    Analytics.trackFilterChange('search_radius', oldRadius, newRadius);
    setSearchRadius(newRadius);
  };

  const formatTime = (timeStr) => {
    const [hours, minutes] = timeStr.split(':');
    const hour = parseInt(hours);
    const ampm = hour >= 12 ? 'PM' : 'AM';
    const displayHour = hour % 12 || 12;
    return `${displayHour}:${minutes} ${ampm}`;
  };

  const formatDistance = (distanceMeters) => {
    const miles = (distanceMeters * 0.000621371).toFixed(1);
    return `${miles} mi`;
  };

  const getSpecialTypeLabel = (type) => {
    const specialType = specialTypes.find(st => st.value === type);
    return specialType ? specialType.label : type;
  };

  const getSpecialTypeBadgeColor = (type) => {
    const colors = {
      happy_hour: "bg-orange-100 text-orange-800 border-orange-200",
      lunch_special: "bg-green-100 text-green-800 border-green-200",
      dinner_special: "bg-purple-100 text-purple-800 border-purple-200",
      blue_plate: "bg-blue-100 text-blue-800 border-blue-200",
      daily_special: "bg-red-100 text-red-800 border-red-200",
      weekend_special: "bg-yellow-100 text-yellow-800 border-yellow-200"
    };
    return colors[type] || "bg-gray-100 text-gray-800 border-gray-200";
  };

  const toggleFavorite = async (restaurant) => {
    if (!currentUser) {
      setShowUserAuth(true);
      return;
    }

    const isFavorite = userFavorites.some(fav => fav.id === restaurant.id);
    const action = isFavorite ? 'remove' : 'add';

    try {
      const userToken = localStorage.getItem('user_token');
      const restaurantId = restaurant.id;
      
      if (isFavorite) {
        await axios.delete(`${API}/users/favorites/${restaurantId}`, {
          headers: { Authorization: `Bearer ${userToken}` }
        });
        const newFavorites = userFavorites.filter(fav => fav.id !== restaurantId);
        setUserFavorites(newFavorites);
        trackFavoriteRemove(restaurantId); // Track for owner analytics
      } else {
        await axios.post(`${API}/users/favorites/${restaurantId}`, {}, {
          headers: { Authorization: `Bearer ${userToken}` }
        });
        const newFavorites = [...userFavorites, restaurant];
        setUserFavorites(newFavorites);
        trackFavoriteAdd(restaurantId); // Track for owner analytics
        
        // Refresh favorites from server to ensure synchronization
        setTimeout(() => {
          fetchUserFavorites();
        }, 500);
      }
      
      // Track favorite analytics
      Analytics.trackRestaurantFavorite(restaurant, action);
      
    } catch (error) {
      console.error('Error toggling favorite:', error.response?.data || error.message);
      Analytics.trackError(error.message, 'toggle_favorite');
    }
  };

  const handleUserLogin = (userData) => {
    setCurrentUser(userData);
    setUserType('user'); // Set userType when customer logs in
    if (userData) {
      fetchUserFavorites();
    } else {
      setUserFavorites([]);
    }
  };

  const handleUserLogout = () => {
    setCurrentUser(null);
    setUserType(null); // Clear userType on logout
    setUserFavorites([]);
    localStorage.removeItem('user_token');
  };

  const handleAuthSuccess = (userData, token, type = 'user') => {
    setCurrentUser(userData);
    setAuthToken(token);
    setUserType(type);
    setShowUserAuth(false);
    setShowOwnerAuth(false);
    
    if (type === 'owner') {
      setShowOwnerDashboard(true);
      // Store owner-specific token for OwnerBilling and other components
      localStorage.setItem('owner_token', token);
    }
    
    // Store in localStorage for persistence
    localStorage.setItem('authToken', token);
    localStorage.setItem('userData', JSON.stringify(userData));
    localStorage.setItem('userType', type);
  };

  const handleLogout = () => {
    setCurrentUser(null);
    setAuthToken(null);
    setUserType(null);
    setUserFavorites([]);
    setShowOwnerDashboard(false);
    
    // Clear localStorage
    localStorage.removeItem('authToken');
    localStorage.removeItem('userData');
    localStorage.removeItem('userType');
  };

  // If showing owner portal, render it - DISABLED, using new Owner Dashboard system
  // if (showOwnerPortal) {
  //   return <OwnerPortal />;
  // }

  // If on partner info page, show the partner info component
  if (isPartnerInfoPage) {
    return <PartnerInfo />;
  }

  // If on privacy page, show standalone privacy policy
  if (isPrivacyPage) {
    return (
      <div className="min-h-screen bg-gray-50">
        <div className="bg-white shadow-sm">
          <div className="max-w-4xl mx-auto px-4 py-6">
            <a href="/" className="text-orange-500 hover:text-orange-600 flex items-center mb-4">
              <ArrowLeft className="w-5 h-5 mr-2" />
              Back to Home
            </a>
            <h1 className="text-3xl font-bold text-gray-900">Privacy Policy</h1>
            <p className="text-gray-600 mt-2">Last updated: January 11, 2026</p>
          </div>
        </div>
        <div className="max-w-4xl mx-auto px-4 py-8">
          <div className="bg-white rounded-lg shadow-md p-8 space-y-8">
            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">1. Introduction</h2>
              <p className="text-gray-700 leading-relaxed">
                Welcome to On the Cheap ("we," "our," or "us"). We respect your privacy and are committed to protecting your personal data. 
                This privacy policy explains how we collect, use, disclose, and safeguard your information when you use our mobile application 
                and website (collectively, the "Service").
              </p>
            </section>
            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">2. Information We Collect</h2>
              <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-4">2.1 Personal Information</h3>
              <p className="text-gray-700 leading-relaxed mb-3">We may collect personal information that you provide to us, including:</p>
              <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
                <li>Name and email address (for account creation)</li>
                <li>Location data (to show nearby restaurant specials)</li>
                <li>Payment information (processed securely through Stripe)</li>
                <li>Restaurant preferences and favorites</li>
              </ul>
              <h3 className="text-xl font-semibold text-gray-900 mb-3 mt-4">2.2 Usage Information</h3>
              <p className="text-gray-700 leading-relaxed mb-3">We automatically collect certain information when you use our Service:</p>
              <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
                <li>Device information (type, operating system, unique identifiers)</li>
                <li>Log data (IP address, browser type, pages visited)</li>
                <li>Location information (with your permission)</li>
              </ul>
            </section>
            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">3. How We Use Your Information</h2>
              <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
                <li>Provide, maintain, and improve our Service</li>
                <li>Show you relevant restaurant specials and coupons near you</li>
                <li>Process payments and subscription transactions</li>
                <li>Send you notifications about specials you've saved</li>
                <li>Respond to your comments and customer service requests</li>
              </ul>
            </section>
            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">4. Information Sharing</h2>
              <p className="text-gray-700 leading-relaxed mb-3">We do not sell your personal information. We may share your information only:</p>
              <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
                <li><strong>With Service Providers:</strong> Third-party services (Stripe for payments, cloud hosting)</li>
                <li><strong>Legal Requirements:</strong> If required by law or to protect our rights</li>
              </ul>
            </section>
            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">5. Data Security</h2>
              <p className="text-gray-700 leading-relaxed">
                We implement appropriate technical and organizational measures to protect your personal information against unauthorized access, 
                alteration, disclosure, or destruction. This includes encryption of sensitive data and secure servers.
              </p>
            </section>
            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">6. Your Rights</h2>
              <ul className="list-disc list-inside text-gray-700 space-y-2 ml-4">
                <li><strong>Access:</strong> Request a copy of the personal information we hold about you</li>
                <li><strong>Correction:</strong> Update or correct inaccurate information</li>
                <li><strong>Deletion:</strong> Request deletion of your account and personal data</li>
                <li><strong>Location:</strong> Disable location services through your device settings</li>
              </ul>
            </section>
            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">7. Children's Privacy</h2>
              <p className="text-gray-700 leading-relaxed">
                Our Service is not intended for children under 13 years of age. We do not knowingly collect personal information from children under 13.
              </p>
            </section>
            <section>
              <h2 className="text-2xl font-bold text-gray-900 mb-4">8. Contact Us</h2>
              <p className="text-gray-700 leading-relaxed mb-4">If you have questions about this privacy policy, please contact us:</p>
              <div className="bg-gray-50 p-4 rounded-lg">
                <p className="text-gray-700"><strong>On the Cheap</strong></p>
                <p className="text-gray-700">Email: privacy@onthecheapapp.com</p>
                <p className="text-gray-700">Website: https://www.onthecheapapp.com</p>
              </div>
            </section>
          </div>
        </div>
      </div>
    );
  }

  // Delete Account Page
  if (isDeleteAccountPage) {
    const [deleteEmail, setDeleteEmail] = React.useState('');
    const [deleteReason, setDeleteReason] = React.useState('');
    const [deleteSubmitted, setDeleteSubmitted] = React.useState(false);
    const [deleteLoading, setDeleteLoading] = React.useState(false);
    const [deleteError, setDeleteError] = React.useState('');

    const handleDeleteRequest = async (e) => {
      e.preventDefault();
      setDeleteLoading(true);
      setDeleteError('');
      
      try {
        const response = await axios.post(`${API}/users/request-deletion`, {
          email: deleteEmail,
          reason: deleteReason
        });
        setDeleteSubmitted(true);
      } catch (error) {
        setDeleteError('Failed to submit request. Please try again or contact support@onthecheapapp.com');
      }
      setDeleteLoading(false);
    };

    return (
      <div className="min-h-screen bg-gray-50">
        <div className="bg-white shadow-sm">
          <div className="max-w-2xl mx-auto px-4 py-6">
            <a href="/" className="text-orange-500 hover:text-orange-600 flex items-center mb-4">
              <ArrowLeft className="w-5 h-5 mr-2" />
              Back to Home
            </a>
            <h1 className="text-3xl font-bold text-gray-900">Delete Your Account</h1>
            <p className="text-gray-600 mt-2">Request deletion of your account and all associated data</p>
          </div>
        </div>
        <div className="max-w-2xl mx-auto px-4 py-8">
          <div className="bg-white rounded-lg shadow-md p-8">
            {deleteSubmitted ? (
              <div className="text-center py-8">
                <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
                  <svg className="w-8 h-8 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                  </svg>
                </div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">Request Submitted</h2>
                <p className="text-gray-600">
                  Your account deletion request has been received. Your account and all associated data will be deleted within 7 business days. You will receive a confirmation email once complete.
                </p>
              </div>
            ) : (
              <>
                <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-6">
                  <h3 className="font-semibold text-yellow-800 mb-2">⚠️ Warning</h3>
                  <p className="text-yellow-700 text-sm">
                    This action is permanent and cannot be undone. All your data including favorites, saved restaurants, and account information will be permanently deleted.
                  </p>
                </div>
                
                <form onSubmit={handleDeleteRequest} className="space-y-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Email Address *
                    </label>
                    <input
                      type="email"
                      required
                      value={deleteEmail}
                      onChange={(e) => setDeleteEmail(e.target.value)}
                      placeholder="Enter your account email"
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                    />
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Reason for leaving (optional)
                    </label>
                    <textarea
                      value={deleteReason}
                      onChange={(e) => setDeleteReason(e.target.value)}
                      placeholder="Help us improve by sharing why you're leaving"
                      rows={3}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                    />
                  </div>
                  
                  {deleteError && (
                    <div className="bg-red-50 text-red-700 p-3 rounded-lg text-sm">
                      {deleteError}
                    </div>
                  )}
                  
                  <button
                    type="submit"
                    disabled={deleteLoading}
                    className="w-full py-3 px-4 bg-red-600 hover:bg-red-700 text-white font-semibold rounded-lg disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {deleteLoading ? 'Submitting...' : 'Request Account Deletion'}
                  </button>
                </form>
                
                <div className="mt-6 pt-6 border-t">
                  <p className="text-sm text-gray-600">
                    Questions? Contact us at <a href="mailto:support@onthecheapapp.com" className="text-orange-500 hover:underline">support@onthecheapapp.com</a>
                  </p>
                </div>
              </>
            )}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-b from-amber-50 to-orange-50">
      {/* PWA Components */}
      <OfflineIndicator />
      <PWAInstallBanner />
      <PWAManualInstall />
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-6xl mx-auto px-4 py-4 sm:py-6">
          <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
            <div className="text-center sm:flex-1">
              <h1 className="text-2xl sm:text-4xl font-bold text-gray-900 mb-1 sm:mb-2">
                On-the-Cheap
              </h1>
              <p className="text-sm sm:text-lg text-gray-600">
                Find the best restaurant specials near you
              </p>
            </div>
            <div className="flex flex-wrap gap-2 justify-center sm:justify-end">
              {/* Auth buttons */}
              {currentUser ? (
                <div className="flex items-center space-x-2">
                  <span className="text-sm text-gray-600">
                    Welcome, {currentUser.first_name || currentUser.email}!
                    {userType === 'owner' && (
                      <span className="ml-1 px-2 py-1 bg-orange-100 text-orange-700 text-xs rounded-full">
                        Owner
                      </span>
                    )}
                  </span>
                  {userType === 'owner' && (
                    <button
                      onClick={() => setShowOwnerDashboard(true)}
                      className="px-3 py-1 bg-orange-500 text-white text-sm rounded hover:bg-orange-600 transition-colors"
                    >
                      Dashboard
                    </button>
                  )}
                  {/* Show Favorites button for customers (userType === 'user' or not an owner) */}
                  {userType !== 'owner' && (
                    <button
                      onClick={() => setShowUserAuth(true)}
                      className="px-3 py-1 bg-orange-500 text-white text-sm rounded hover:bg-orange-600 transition-colors flex items-center gap-1"
                      data-testid="favorites-btn"
                    >
                      <svg xmlns="http://www.w3.org/2000/svg" className="h-4 w-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                      </svg>
                      Favorites
                    </button>
                  )}
                  <button
                    onClick={handleLogout}
                    className="px-3 py-1 bg-gray-500 text-white text-sm rounded hover:bg-gray-600 transition-colors"
                  >
                    Logout
                  </button>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
                  <a
                    href="/partner-info"
                    className="px-4 py-2 bg-amber-500 text-white rounded hover:bg-amber-600 transition-colors"
                    data-testid="partner-info-link"
                  >
                    Partner With Us
                  </a>
                  <button
                    onClick={() => setShowUserAuth(true)}
                    className="px-4 py-2 bg-orange-500 text-white rounded hover:bg-orange-600 transition-colors"
                  >
                    Sign In
                  </button>
                  <button
                    onClick={() => setShowOwnerAuth(true)}
                    className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600 transition-colors"
                  >
                    Owner Portal
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Navigation Toggle */}
      <div className="bg-white border-b">
        <div className="max-w-6xl mx-auto px-4">
          <div className="flex items-center justify-center space-x-2 py-3">
            <button
              onClick={() => setActiveView('restaurants')}
              className={`px-6 py-2 rounded-lg font-medium transition-all ${
                activeView === 'restaurants'
                  ? 'bg-orange-500 text-white shadow-md'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              🍽️ Restaurants
            </button>
            <button
              onClick={() => setActiveView('coupons')}
              className={`px-6 py-2 rounded-lg font-medium transition-all ${
                activeView === 'coupons'
                  ? 'bg-orange-500 text-white shadow-md'
                  : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
              }`}
            >
              🎟️ Digital Coupons
            </button>
          </div>
        </div>
      </div>

      {/* Main Content - Toggle between Restaurants and Coupons */}
      {activeView === 'restaurants' ? (
        <>
      {/* Search Section */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-4 sm:py-8">
        <Card className="mb-8">
          <CardHeader>
            <CardTitle className="text-xl font-semibold">Find Restaurant Specials</CardTitle>
            <CardDescription>
              Search by location or use your current position to find amazing deals
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1">
                <AddressInput
                  placeholder="Enter city or address (e.g., San Francisco, New York)"
                  initialValue={searchLocation}
                  onAddressSelect={handleAddressSelect}
                  onInputChange={handleAddressInputChange}
                  region="US"
                  className="w-full"
                />
              </div>
              <div className="flex gap-2 flex-wrap">
                <Button 
                  onClick={handleLocationSearch}
                  disabled={!searchLocation.trim() || loading}
                  className="bg-orange-600 hover:bg-orange-700"
                >
                  <Search className="w-4 h-4 mr-2" />
                  Search
                </Button>
                <Button 
                  variant="outline" 
                  onClick={getCurrentLocation}
                  disabled={loading}
                  className="border-orange-600 text-orange-600 hover:bg-orange-50"
                >
                  <Navigation className="w-4 h-4 mr-2" />
                  Use Current Location
                </Button>
                <Button 
                  variant="outline"
                  onClick={clearSearch}
                  disabled={loading}
                  className="border-gray-400 text-gray-600 hover:bg-gray-50"
                >
                  <X className="w-4 h-4 mr-2" />
                  Clear Search
                </Button>
              </div>
            </div>
            
            <div className="flex flex-col md:flex-row gap-4">
              <div className="flex-1">
                <Select value={selectedSpecialType} onValueChange={handleSpecialTypeChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="Filter by special type" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Specials</SelectItem>
                    {specialTypes.map((type) => (
                      <SelectItem key={type.value} value={type.value}>
                        {type.label}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
              </div>
              <div className="flex-1">
                <Select value={selectedVendorType} onValueChange={handleVendorTypeChange}>
                  <SelectTrigger>
                    <SelectValue placeholder="All Venues" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="all">All Venues</SelectItem>
                    <SelectItem value="permanent">Restaurants Only</SelectItem>
                    <SelectItem value="bar">🍺 Bars</SelectItem>
                    <SelectItem value="mobile">🚛 Food Trucks & Pop-ups</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="flex-1">
                <Select value={searchRadius.toString()} onValueChange={handleRadiusChange}>
                  <SelectTrigger>
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="1609">1 mile</SelectItem>
                    <SelectItem value="3219">2 miles</SelectItem>
                    <SelectItem value="8047">5 miles</SelectItem>
                    <SelectItem value="16094">10 miles</SelectItem>
                    <SelectItem value="32187">20 miles</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Loading State */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-orange-600"></div>
            <p className="mt-4 text-gray-600">Finding the best deals near you...</p>
          </div>
        )}

        {/* Results Header */}
        {restaurants.length > 0 && (
          <div className="mb-6">
            <div className="flex items-center justify-between mb-4">
              <div>
                <h2 className="text-2xl font-bold text-gray-900 mb-2">
                  Current Specials Near You
                </h2>
                <p className="text-gray-600">
                  Found {restaurants.length} restaurants with active specials
                  {lastSearch && ` within ${formatDistance(searchRadius)} of your search location`}
                </p>
              </div>
              
              {/* View Toggle Buttons */}
              <div className="flex gap-2 bg-gray-100 p-1 rounded-lg">
                <Button
                  variant={viewMode === 'list' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => {
                    if (viewMode !== 'list') {
                      Analytics.trackViewToggle(viewMode, 'list');
                      setViewMode('list');
                    }
                  }}
                  className={viewMode === 'list' ? 'bg-white shadow-sm' : ''}
                >
                  <List className="w-4 h-4 mr-1" />
                  List
                </Button>
                <Button
                  variant={viewMode === 'map' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => {
                    if (viewMode !== 'map') {
                      Analytics.trackViewToggle(viewMode, 'map');
                      setViewMode('map');
                    }
                  }}
                  className={viewMode === 'map' ? 'bg-white shadow-sm' : ''}
                >
                  <Map className="w-4 h-4 mr-1" />
                  Map
                </Button>
              </div>
            </div>
          </div>
        )}

        {/* Restaurant Results - List and Map Views */}
        {restaurants.length > 0 && (
          <div className="mb-6">
            {viewMode === 'list' ? (
              /* List View */
              <div className="grid gap-4 sm:gap-6 grid-cols-1 md:grid-cols-2 lg:grid-cols-3">
                {restaurants.map((restaurant) => (
                  <Card key={restaurant.id} className="hover:shadow-lg transition-shadow">
                    <CardHeader>
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="flex items-center gap-2 mb-1">
                            <CardTitle className="text-xl font-bold text-gray-900">
                              {restaurant.name}
                            </CardTitle>
                            {restaurant.is_mobile_vendor && (
                              <Badge variant="secondary" className="bg-orange-100 text-orange-800 text-xs">
                                <Truck className="w-3 h-3 mr-1" />
                                Mobile
                              </Badge>
                            )}
                          </div>
                          <CardDescription className="flex items-center mt-1">
                            <MapPin className="w-4 h-4 mr-1" />
                            {restaurant.distance && formatDistance(restaurant.distance)}
                          </CardDescription>
                        </div>
                        <div className="flex items-center gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => toggleFavorite(restaurant)}
                            className="text-gray-400 hover:text-red-500"
                          >
                            <Heart 
                              className={`w-5 h-5 ${
                                userFavorites.some(fav => fav.id === restaurant.id) 
                                  ? 'fill-red-500 text-red-500' 
                                  : ''
                              }`} 
                            />
                          </Button>
                          {restaurant.rating && (
                            <div className="flex items-center">
                              <Star className="w-4 h-4 text-yellow-400 fill-current mr-1" />
                              <span className="text-sm font-medium">{restaurant.rating}</span>
                            </div>
                          )}
                        </div>
                      </div>
                    </CardHeader>
                    
                    {/* Restaurant Photo */}
                    {restaurant.photos && restaurant.photos.length > 0 && (
                      <div className="relative h-48 overflow-hidden">
                        <img
                          src={restaurant.photos[0].url}
                          alt={restaurant.name}
                          className="w-full h-full object-cover"
                          onError={(e) => {
                            console.log('❌ Image load error for:', restaurant.name, restaurant.photos[0].url);
                            e.target.style.display = 'none';
                            e.target.nextSibling.style.display = 'flex';
                          }}
                          onLoad={() => {
                            console.log('✅ Image loaded successfully for:', restaurant.name);
                          }}
                        />
                        <div className="hidden w-full h-full bg-gray-100 items-center justify-center flex-col">
                          <div className="text-gray-400 text-4xl mb-2">🍽️</div>
                          <div className="text-gray-500 text-sm">Photo not available</div>
                        </div>
                        
                        {/* Photo badges */}
                        {restaurant.photos[0].is_fallback && (
                          <div className="absolute top-2 left-2 bg-black bg-opacity-60 text-white text-xs px-2 py-1 rounded">
                            Stock Photo
                          </div>
                        )}
                        
                        {restaurant.photos.length > 1 && (
                          <div className="absolute top-2 right-2 bg-black bg-opacity-60 text-white text-xs px-2 py-1 rounded flex items-center gap-1">
                            <span>📷</span>
                            <span>{restaurant.photos.length}</span>
                          </div>
                        )}
                        
                        {/* Special Images Preview Overlay */}
                        {restaurant.specials?.some(s => s.image) && (
                          <div className="absolute bottom-0 left-0 right-0 bg-gradient-to-t from-black/70 to-transparent p-3">
                            <div className="flex items-center gap-2">
                              <span className="text-white text-xs font-medium">Specials:</span>
                              <div className="flex gap-1 overflow-x-auto">
                                {restaurant.specials.filter(s => s.image).slice(0, 3).map((special) => (
                                  <div key={special.id} className="relative flex-shrink-0" title={special.title}>
                                    <img 
                                      src={special.image} 
                                      alt={special.title}
                                      className="w-10 h-10 rounded object-cover border-2 border-white shadow-sm"
                                    />
                                  </div>
                                ))}
                                {restaurant.specials.filter(s => s.image).length > 3 && (
                                  <div className="w-10 h-10 rounded bg-white/20 border-2 border-white flex items-center justify-center text-white text-xs font-bold">
                                    +{restaurant.specials.filter(s => s.image).length - 3}
                                  </div>
                                )}
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                    
                    {/* Special Preview Banner (when no restaurant photo) */}
                    {(!restaurant.photos || restaurant.photos.length === 0) && restaurant.specials?.some(s => s.image) && (
                      <div className="bg-gradient-to-r from-orange-500 to-amber-500 p-3">
                        <div className="flex items-center gap-2">
                          <span className="text-white text-sm font-medium">🔥 Hot Specials:</span>
                          <div className="flex gap-2 overflow-x-auto">
                            {restaurant.specials.filter(s => s.image).slice(0, 4).map((special) => (
                              <div key={special.id} className="relative flex-shrink-0" title={special.title}>
                                <img 
                                  src={special.image} 
                                  alt={special.title}
                                  className="w-12 h-12 rounded-lg object-cover border-2 border-white shadow-md"
                                />
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    )}
                    
                    <CardContent>
                      <div className="space-y-3">
                        <p className="text-sm text-gray-600 flex items-center">
                          <MapPin className="w-4 h-4 mr-2" />
                          {restaurant.address}
                        </p>
                        
                        {restaurant.phone && (
                          <p className="text-sm text-gray-600 flex items-center">
                            <Phone className="w-4 h-4 mr-2" />
                            <a 
                              href={`tel:${restaurant.phone}`} 
                              className="text-orange-600 hover:underline"
                              onClick={() => trackCallClick(restaurant.id)}
                            >
                              {restaurant.phone}
                            </a>
                          </p>
                        )}
                        
                        {restaurant.website && (
                          <p className="text-sm text-gray-600 flex items-center">
                            <Globe className="w-4 h-4 mr-2" />
                            <a href={restaurant.website} target="_blank" rel="noopener noreferrer" className="text-orange-600 hover:underline">
                              Visit Website
                            </a>
                          </p>
                        )}

                        <div className="flex flex-wrap gap-1 mb-3">
                          {restaurant.cuisine_type?.map((cuisine) => (
                            <Badge key={cuisine} variant="secondary" className="text-xs">
                              {cuisine}
                            </Badge>
                          ))}
                        </div>

                        <div className="border-t pt-3">
                          <h4 className="font-semibold text-gray-900 mb-2">Current Specials</h4>
                          <div className="space-y-3">
                            {restaurant.specials?.length > 0 ? (
                              restaurant.specials.map((special) => (
                                <div key={special.id} className="bg-gradient-to-r from-orange-50 to-amber-50 p-3 rounded-lg">
                                  <div className="flex gap-3">
                                    {/* Special Image */}
                                    {special.image && (
                                      <div className="flex-shrink-0">
                                        <img 
                                          src={special.image} 
                                          alt={special.title}
                                          className="w-20 h-20 object-cover rounded-lg shadow-sm"
                                        />
                                      </div>
                                    )}
                                    
                                    <div className="flex-1 min-w-0">
                                      <div className="flex justify-between items-start mb-2">
                                        <h5 className="font-medium text-gray-900">{special.title}</h5>
                                        <Badge className={getSpecialTypeBadgeColor(special.special_type)}>
                                          {getSpecialTypeLabel(special.special_type)}
                                        </Badge>
                                      </div>
                                      <p className="text-sm text-gray-700 mb-2">{special.description}</p>
                                      <div className="flex items-center justify-between text-sm">
                                        <div className="flex items-center text-green-600 font-medium">
                                          <DollarSign className="w-4 h-4 mr-1" />
                                          ${special.price}
                                          {special.original_price && (
                                            <span className="ml-2 text-gray-500 line-through">
                                              ${special.original_price}
                                            </span>
                                          )}
                                        </div>
                                        <div className="flex items-center text-gray-600">
                                          <Clock className="w-4 h-4 mr-1" />
                                          {formatTime(special.time_start)} - {formatTime(special.time_end)}
                                        </div>
                                      </div>
                                      <div className="mt-2">
                                        <p className="text-xs text-gray-600">
                                          Available: {special.days_available.map(day => 
                                            day.charAt(0).toUpperCase() + day.slice(1)
                                          ).join(', ')}
                                        </p>
                                      </div>
                                    </div>
                                  </div>
                                </div>
                              ))
                            ) : (
                              <div className="text-center py-4 px-3 bg-gray-50 rounded-lg">
                                <p className="text-sm text-gray-600">
                                  {restaurant.specials_message || 'No current specials at this time'}
                                </p>
                              </div>
                            )}
                          </div>
                        </div>
                        
                        {/* Share and Ride Actions */}
                        <div className="border-t pt-4 mt-4">
                          <div className="flex flex-col space-y-3">
                            {/* Share Buttons */}
                            <div>
                              <h5 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                                <Share2 className="w-4 h-4 mr-1" />
                                Share Restaurant
                              </h5>
                              <div className="flex flex-wrap gap-2">
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleShare(restaurant, 'sms')}
                                  className="text-xs"
                                >
                                  <MessageCircle className="w-3 h-3 mr-1" />
                                  Text Message
                                </Button>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleShare(restaurant, 'whatsapp')}
                                  className="text-xs bg-green-50 hover:bg-green-100 text-green-700 border-green-200"
                                >
                                  💬 WhatsApp
                                </Button>
                              </div>
                            </div>
                            
                            {/* Ride Buttons */}
                            <div>
                              <h5 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                                <Car className="w-4 h-4 mr-1" />
                                Get a Ride
                              </h5>
                              <div className="flex gap-2">
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleRide(restaurant, 'uber')}
                                  className="text-xs bg-black text-white hover:bg-gray-800 border-black"
                                >
                                  🚗 Uber
                                </Button>
                                <Button
                                  variant="outline"
                                  size="sm"
                                  onClick={() => handleRide(restaurant, 'lyft')}
                                  className="text-xs bg-pink-600 text-white hover:bg-pink-700 border-pink-600"
                                >
                                  🚙 Lyft
                                </Button>
                              </div>
                            </div>
                            
                            {/* Check-In Button */}
                            <div>
                              <h5 className="text-sm font-medium text-gray-700 mb-2 flex items-center">
                                <CheckCircle className="w-4 h-4 mr-1" />
                                Visiting Now?
                              </h5>
                              <CheckInButton 
                                restaurant={restaurant}
                                userToken={localStorage.getItem('user_token')}
                                onSuccess={(result) => console.log('Check-in successful:', result)}
                              />
                            </div>
                          </div>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                ))}
              </div>
            ) : (
              /* Map View */
              <div className="h-[600px] w-full">
                <RestaurantMap
                  restaurants={restaurants}
                  currentLocation={lastSearch}
                  onRestaurantClick={(restaurant) => {
                    Analytics.trackRestaurantView(restaurant);
                    Analytics.trackMapInteraction('restaurant_marker_click', {
                      restaurant_id: restaurant.id,
                      restaurant_source: restaurant.source,
                      is_mobile_vendor: restaurant.is_mobile_vendor
                    });
                    trackCardClick(restaurant.id); // Track for owner analytics
                    console.log('Restaurant clicked:', restaurant.name);
                  }}
                  className="rounded-lg border"
                />
              </div>
            )}
          </div>
        )}

        {/* No Results */}
        {!loading && restaurants.length === 0 && coordinates && (
          <div className="text-center py-12">
            <div className="max-w-md mx-auto">
              <div className="text-6xl mb-4">🍽️</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                No Active Specials Found
              </h3>
              <p className="text-gray-600 mb-4">
                Try expanding your search radius or check back later for new specials.
              </p>
              <Button 
                onClick={() => {
                  setSearchRadius(16094); // 10 miles
                  if (coordinates) {
                    searchRestaurants(coordinates.latitude, coordinates.longitude);
                  }
                }}
                className="bg-orange-600 hover:bg-orange-700"
              >
                Search Wider Area (10 miles)
              </Button>
            </div>
          </div>
        )}

        {/* Welcome Message */}
        {!loading && restaurants.length === 0 && !coordinates && (
          <div className="text-center py-12">
            <div className="max-w-md mx-auto">
              <div className="text-6xl mb-4">🍻</div>
              <h3 className="text-xl font-semibold text-gray-900 mb-2">
                Welcome to On-the-Cheap!
              </h3>
              <p className="text-gray-600 mb-4">
                Find amazing restaurant specials, happy hours, and daily deals near you. 
                Enter your location above to get started.
              </p>
              <div className="bg-orange-50 p-4 rounded-lg mt-4">
                <p className="text-sm text-orange-800">
                  💡 <strong>Pro tip:</strong> We show only specials that are currently active based on the time and day!
                </p>
              </div>
            </div>
          </div>
        )}
      </div>
      </>
      ) : (
        /* Coupons View */
        <CouponDiscovery
          userLocation={coordinates}
          isAuthenticated={!!currentUser && userType === 'user'}
          token={authToken}
          onLoginRequired={() => setShowUserAuth(true)}
        />
      )}

      {/* User Authentication Modal */}
      {showUserAuth && (
        <UserAuth 
          onClose={() => setShowUserAuth(false)}
          onUserLogin={handleUserLogin}
          currentFavorites={userFavorites}
          onFavoritesUpdate={setUserFavorites}
          onShowNotificationPreferences={() => setShowNotificationPreferences(true)}
        />
      )}

      {/* Owner Authentication Modal */}
      {showOwnerAuth && (
        <OwnerAuth 
          onClose={() => setShowOwnerAuth(false)}
          onAuthSuccess={handleAuthSuccess}
        />
      )}

      {/* Owner Dashboard Modal */}
      {showOwnerDashboard && (
        <OwnerDashboard 
          onClose={() => setShowOwnerDashboard(false)}
          user={currentUser}
          token={authToken}
        />
      )}

      {/* Notification Preferences Modal */}
      {showNotificationPreferences && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-2 sm:p-4 z-50">
          <div className="max-w-2xl w-full max-h-[95vh] sm:max-h-[90vh] overflow-y-auto">
            <NotificationPreferences 
              user={currentUser}
              onClose={() => setShowNotificationPreferences(false)}
            />
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="bg-white border-t mt-12">
        <div className="max-w-6xl mx-auto px-4 py-8">
          <div className="text-center">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">On-the-Cheap</h3>
            <p className="text-gray-600 text-sm">
              Discover the best restaurant specials and save money on great food!
            </p>
            <div className="mt-4 flex justify-center space-x-4 text-sm">
              <button
                onClick={() => setShowPrivacyPolicy(true)}
                className="text-orange-500 hover:text-orange-600 hover:underline"
              >
                Privacy Policy
              </button>
              <span className="text-gray-400">|</span>
              <a href="mailto:support@onthecheapapp.com" className="text-orange-500 hover:text-orange-600 hover:underline">
                Contact Us
              </a>
            </div>
            <div className="mt-4 text-xs text-gray-500">
              © 2025 On-the-Cheap. Find deals, save money, eat well.
            </div>
          </div>
        </div>
      </footer>

      {/* Privacy Policy Modal */}
      {showPrivacyPolicy && (
        <PrivacyPolicyModal onClose={() => setShowPrivacyPolicy(false)} />
      )}
    </div>
  );
}

export default App;