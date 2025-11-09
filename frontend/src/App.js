import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";
import { MapPin, Clock, DollarSign, Phone, Globe, Star, Search, Navigation, Building2, ArrowLeft, User, Heart, Share2, MessageCircle, Car, ExternalLink, X, Map, List, Truck, Bell } from "lucide-react";
import { Button } from "./components/ui/button";
import { Input } from "./components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "./components/ui/card";
import { Badge } from "./components/ui/badge";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "./components/ui/select";
import OwnerPortal from "./OwnerPortal";
import UserAuth from "./UserAuth";
import OwnerAuth from './components/OwnerAuth';
import OwnerDashboard from './components/OwnerDashboard';
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

// Get backend URL from environment variables
const BACKEND_URL = process.env.REACT_APP_BACKEND_URL || '';
const API = BACKEND_URL || '/api';

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
  
  return {
    sms: `sms:?body=${encodedMessage}`,
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

const openShareLink = (url, platform) => {
  // For mobile apps, try to open the native app first, then fallback to web
  if (platform === 'sms') {
    window.location.href = url;
  } else {
    window.open(url, '_blank', 'noopener,noreferrer');
  }
};

// Analytics-enabled share function
const handleShare = (restaurant, platform) => {
  Analytics.trackRestaurantShare(restaurant, platform);
  const shareUrls = getShareUrls(restaurant);
  openShareLink(shareUrls[platform], platform);
};

// Analytics-enabled ride function  
const handleRide = (restaurant, service) => {
  Analytics.trackRideRequest(restaurant, service);
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
  
  // Owner dashboard state
  const [showOwnerAuth, setShowOwnerAuth] = useState(false);
  const [showOwnerDashboard, setShowOwnerDashboard] = useState(false);

  const [viewMode, setViewMode] = useState('list'); // 'list' or 'map'
  const [selectedVendorType, setSelectedVendorType] = useState('all'); // 'all', 'permanent', 'mobile'
  const [showNotificationPreferences, setShowNotificationPreferences] = useState(false);
  const [activeView, setActiveView] = useState('restaurants'); // 'restaurants' or 'coupons'
  
  // OneSignal hook
  const { isEnabled: notificationsEnabled, isInitialized: notificationsInitialized, tagUser } = useNotifications();
  
  // PWA hook
  const { cacheRestaurantData, getCachedRestaurantData, isOnline } = usePWA();

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
      searchRestaurants(coords.latitude, coords.longitude);
    } catch (error) {
      console.error("Error geocoding location:", error);
      setLoading(false);
    }
  };

  // Enhanced handler for AddressInput component
  const handleAddressSelect = (geocodeResult) => {
    setSearchLocation(geocodeResult.formatted_address);
    setCoordinates({
      latitude: geocodeResult.latitude,
      longitude: geocodeResult.longitude
    });
    setLoading(true);
    searchRestaurants(geocodeResult.latitude, geocodeResult.longitude);
  };

  // Handler for manual text input in AddressInput
  const handleAddressInputChange = (value) => {
    setSearchLocation(value);
  };

  const searchRestaurants = async (latitude, longitude) => {
    if (!latitude || !longitude) return;
    
    setLoading(true);
    const searchStartTime = performance.now();
    
    try {
      const params = {
        latitude,
        longitude,
        radius: searchRadius,
      };

      if (selectedSpecialType && selectedSpecialType !== "all") {
        params.special_type = selectedSpecialType;
      }
      
      if (selectedVendorType && selectedVendorType !== "all") {
        params.vendor_type = selectedVendorType;
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
      
      // Track search analytics
      Analytics.trackRestaurantSearch({
        location: searchLocation,
        latitude,
        longitude,
        radius: searchRadius,
        special_type: selectedSpecialType,
        vendor_type: selectedVendorType,
        query: null
      }, searchResults.length, sourceSummary);
      
      // Track search performance
      Analytics.trackPerformance('restaurant_search', searchTime, {
        results_count: searchResults.length,
        has_filters: !!(selectedSpecialType || selectedVendorType)
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
      } else {
        await axios.post(`${API}/users/favorites/${restaurantId}`, {}, {
          headers: { Authorization: `Bearer ${userToken}` }
        });
        const newFavorites = [...userFavorites, restaurant];
        setUserFavorites(newFavorites);
        
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
    if (userData) {
      fetchUserFavorites();
    } else {
      setUserFavorites([]);
    }
  };

  const handleUserLogout = () => {
    setCurrentUser(null);
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
                  <button
                    onClick={handleLogout}
                    className="px-3 py-1 bg-gray-500 text-white text-sm rounded hover:bg-gray-600 transition-colors"
                  >
                    Logout
                  </button>
                </div>
              ) : (
                <div className="flex items-center space-x-2">
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
                            {restaurant.phone}
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
            <div className="mt-4 text-xs text-gray-500">
              © 2024 On-the-Cheap. Find deals, save money, eat well.
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
}

export default App;