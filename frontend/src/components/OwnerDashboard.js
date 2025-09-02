import React, { useState, useEffect } from 'react';
import { 
  ChartBarIcon, 
  BuildingStorefrontIcon, 
  CalendarDaysIcon, 
  ClockIcon,
  CheckCircleIcon,
  ExclamationTriangleIcon,
  PlusIcon,
  EyeIcon,
  HeartIcon,
  DocumentTextIcon,
  TagIcon,
  GiftIcon,
  SparklesIcon,
  QrCodeIcon,
  TrendingUpIcon
} from '@heroicons/react/24/outline';
import CouponCreator from './CouponCreator';

const OwnerDashboard = ({ user, token, onClose }) => {
  const [dashboardData, setDashboardData] = useState(null);
  const [restaurants, setRestaurants] = useState([]);
  const [specials, setSpecials] = useState([]);
  const [coupons, setCoupons] = useState([]);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [showCouponCreator, setShowCouponCreator] = useState(false);
  const [selectedRestaurant, setSelectedRestaurant] = useState(null);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || '/api';

  useEffect(() => {
    if (user && token) {
      loadDashboardData();
    }
  }, [user, token]);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load dashboard stats, restaurants, specials, and coupons in parallel
      const [statsResponse, restaurantsResponse, specialsResponse, couponsResponse] = await Promise.all([
        fetch(`${backendUrl}/owners/dashboard`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${backendUrl}/owners/restaurants`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${backendUrl}/owners/specials`, {
          headers: { 'Authorization': `Bearer ${token}` }
        }),
        fetch(`${backendUrl}/owners/coupons`, {
          headers: { 'Authorization': `Bearer ${token}` }
        })
      ]);

      if (statsResponse.ok) {
        const stats = await statsResponse.json();
        setDashboardData(stats);
      }

      if (restaurantsResponse.ok) {
        const restaurantsData = await restaurantsResponse.json();
        setRestaurants(restaurantsData.restaurants || []);
      }

      if (specialsResponse.ok) {
        const specialsData = await specialsResponse.json();
        setSpecials(specialsData.specials || []);
      }

      if (couponsResponse.ok) {
        const couponsData = await couponsResponse.json();
        setCoupons(couponsData.coupons || []);
      }

    } catch (error) {
      console.error('Error loading dashboard data:', error);
      setError('Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const handleCreateSpecial = (restaurantId = null) => {
    // TODO: Open special creation modal
    console.log('Create special for restaurant:', restaurantId);
    alert('Special creation modal coming soon! Restaurant ID: ' + (restaurantId || 'No restaurant selected'));
  };

  const handleClaimRestaurant = (e) => {
    // Prevent any default behavior and event propagation
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    
    // TODO: Open restaurant claim modal
    console.log('Opening restaurant claim modal');
    alert('Restaurant claim modal coming soon! This will allow you to search for and claim existing restaurants in our database.');
  };

  const handleCreateCoupon = (restaurant = null) => {
    if (restaurants.length === 0) {
      alert('You need to have at least one restaurant to create coupons. Please claim a restaurant first!');
      return;
    }
    
    setSelectedRestaurant(restaurant || restaurants[0]);
    setShowCouponCreator(true);
  };

  const handleCouponSuccess = (newCoupon) => {
    setCoupons(prev => [newCoupon, ...prev]);
    setShowCouponCreator(false);
    setSelectedRestaurant(null);
  };

  if (loading) {
    return (
      <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
        <div className="bg-white rounded-lg p-8 max-w-md w-full mx-4">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-orange-500 mx-auto"></div>
          <p className="text-center mt-4 text-gray-600">Loading dashboard...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-orange-500 to-red-500 text-white p-6 flex justify-between items-center">
          <div>
            <h2 className="text-2xl font-bold">Restaurant Owner Dashboard</h2>
            <p className="text-orange-100">Welcome back, {user?.first_name || 'Owner'}!</p>
          </div>
          <button
            onClick={onClose}
            className="text-white hover:text-orange-200 transition-colors"
          >
            <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        <div className="flex flex-col md:flex-row h-full">
          {/* Sidebar Navigation */}
          <div className="bg-gray-50 p-4 md:w-64 border-r">
            <nav className="space-y-2">
              <button
                onClick={() => setActiveTab('dashboard')}
                className={`w-full flex items-center px-4 py-2 text-left rounded-lg transition-colors ${
                  activeTab === 'dashboard' 
                    ? 'bg-orange-100 text-orange-700 border-orange-200' 
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <ChartBarIcon className="w-5 h-5 mr-3" />
                Dashboard
              </button>
              <button
                onClick={() => setActiveTab('restaurants')}
                className={`w-full flex items-center px-4 py-2 text-left rounded-lg transition-colors ${
                  activeTab === 'restaurants' 
                    ? 'bg-orange-100 text-orange-700 border-orange-200' 
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <BuildingStorefrontIcon className="w-5 h-5 mr-3" />
                My Restaurants
              </button>
              <button
                onClick={() => setActiveTab('coupons')}
                className={`w-full flex items-center px-4 py-2 text-left rounded-lg transition-colors ${
                  activeTab === 'coupons' 
                    ? 'bg-orange-100 text-orange-700 border-orange-200' 
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <TagIcon className="w-5 h-5 mr-3" />
                Digital Coupons
                {coupons.length > 0 && (
                  <span className="ml-auto bg-orange-500 text-white text-xs px-2 py-1 rounded-full">
                    {coupons.length}
                  </span>
                )}
              </button>
              <button
                onClick={() => setActiveTab('specials')}
                className={`w-full flex items-center px-4 py-2 text-left rounded-lg transition-colors ${
                  activeTab === 'specials' 
                    ? 'bg-orange-100 text-orange-700 border-orange-200' 
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <CalendarDaysIcon className="w-5 h-5 mr-3" />
                Specials
              </button>
            </nav>
          </div>

          {/* Main Content */}
          <div className="flex-1 p-6 overflow-y-auto">
            {error && (
              <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-6">
                {error}
              </div>
            )}

            {/* Dashboard Tab */}
            {activeTab === 'dashboard' && (
              <div>
                <h3 className="text-xl font-semibold text-gray-800 mb-6">Dashboard Overview</h3>
                
                {/* Stats Cards */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                  <div className="bg-white p-6 rounded-lg shadow border">
                    <div className="flex items-center">
                      <BuildingStorefrontIcon className="w-8 h-8 text-blue-500" />
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Total Restaurants</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {dashboardData?.total_restaurants || 0}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white p-6 rounded-lg shadow border">
                    <div className="flex items-center">
                      <ClockIcon className="w-8 h-8 text-yellow-500" />
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Pending Claims</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {dashboardData?.pending_claims || 0}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white p-6 rounded-lg shadow border">
                    <div className="flex items-center">
                      <CheckCircleIcon className="w-8 h-8 text-green-500" />
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Active Specials</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {dashboardData?.active_specials || 0}
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white p-6 rounded-lg shadow border">
                    <div className="flex items-center">
                      <ExclamationTriangleIcon className="w-8 h-8 text-orange-500" />
                      <div className="ml-4">
                        <p className="text-sm font-medium text-gray-600">Pending Specials</p>
                        <p className="text-2xl font-bold text-gray-900">
                          {dashboardData?.pending_specials || 0}
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Performance Metrics */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div className="bg-white p-6 rounded-lg shadow border">
                    <h4 className="text-lg font-semibold text-gray-800 mb-4">Performance Metrics</h4>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <EyeIcon className="w-5 h-5 text-gray-400 mr-2" />
                          <span className="text-gray-600">Total Views</span>
                        </div>
                        <span className="font-semibold">{dashboardData?.total_views || 0}</span>
                      </div>
                      <div className="flex items-center justify-between">
                        <div className="flex items-center">
                          <HeartIcon className="w-5 h-5 text-red-400 mr-2" />
                          <span className="text-gray-600">Total Favorites</span>
                        </div>
                        <span className="font-semibold">{dashboardData?.total_favorites || 0}</span>
                      </div>
                    </div>
                  </div>

                  <div className="bg-white p-6 rounded-lg shadow border">
                    <h4 className="text-lg font-semibold text-gray-800 mb-4">Quick Actions</h4>
                    <div className="space-y-3">
                      <button
                        onClick={handleCreateSpecial}
                        className="w-full flex items-center justify-center px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors"
                        disabled={restaurants.length === 0}
                      >
                        <PlusIcon className="w-5 h-5 mr-2" />
                        Create New Special
                      </button>
                      <button
                        onClick={handleClaimRestaurant}
                        className="w-full flex items-center justify-center px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                      >
                        <BuildingStorefrontIcon className="w-5 h-5 mr-2" />
                        Claim Restaurant
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Restaurants Tab */}
            {activeTab === 'restaurants' && (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-xl font-semibold text-gray-800">My Restaurants</h3>
                  <button
                    onClick={(e) => {
                      e.preventDefault();
                      handleClaimRestaurant(e);
                    }}
                    className="flex items-center px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors"
                  >
                    <PlusIcon className="w-5 h-5 mr-2" />
                    Claim Restaurant
                  </button>
                </div>

                {restaurants.length === 0 ? (
                  <div className="text-center py-12">
                    <BuildingStorefrontIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <h4 className="text-lg font-medium text-gray-600 mb-2">No Restaurants Yet</h4>
                    <p className="text-gray-500 mb-4">Claim your first restaurant to start managing specials</p>
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        handleClaimRestaurant(e);
                      }}
                      className="px-6 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors"
                    >
                      Claim Restaurant
                    </button>
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {restaurants.map((restaurant) => (
                      <div key={restaurant.id} className="bg-white rounded-lg shadow border overflow-hidden">
                        {restaurant.photos && restaurant.photos.length > 0 && (
                          <img
                            src={restaurant.photos[0].url}
                            alt={restaurant.name}
                            className="w-full h-48 object-cover"
                          />
                        )}
                        <div className="p-4">
                          <h4 className="font-semibold text-gray-800 mb-2">{restaurant.name}</h4>
                          <p className="text-sm text-gray-600 mb-2">{restaurant.address}</p>
                          {restaurant.cuisine_type && (
                            <div className="flex flex-wrap gap-1 mb-3">
                              {restaurant.cuisine_type.slice(0, 2).map((cuisine, index) => (
                                <span
                                  key={index}
                                  className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded"
                                >
                                  {cuisine}
                                </span>
                              ))}
                            </div>
                          )}
                          <button
                            onClick={(e) => {
                              e.preventDefault();
                              handleCreateSpecial(restaurant.id);
                            }}
                            className="w-full px-3 py-2 bg-orange-100 text-orange-700 text-sm rounded hover:bg-orange-200 transition-colors"
                          >
                            Manage Specials
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Specials Tab */}
            {activeTab === 'specials' && (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-xl font-semibold text-gray-800">My Specials</h3>
                  <button
                    onClick={(e) => {
                      e.preventDefault();
                      handleCreateSpecial(e);
                    }}
                    className="flex items-center px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors"
                    disabled={restaurants.length === 0}
                  >
                    <PlusIcon className="w-5 h-5 mr-2" />
                    Create Special
                  </button>
                </div>

                {specials.length === 0 ? (
                  <div className="text-center py-12">
                    <CalendarDaysIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <h4 className="text-lg font-medium text-gray-600 mb-2">No Specials Yet</h4>
                    <p className="text-gray-500 mb-4">Create your first special to attract customers</p>
                    <button
                      onClick={(e) => {
                        e.preventDefault();
                        handleCreateSpecial(e);
                      }}
                      className="px-6 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors"
                      disabled={restaurants.length === 0}
                    >
                      Create Special
                    </button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {specials.map((special) => (
                      <div key={special.id} className="bg-white rounded-lg shadow border p-6">
                        <div className="flex justify-between items-start mb-4">
                          <div>
                            <h4 className="font-semibold text-gray-800 text-lg">{special.title}</h4>
                            <p className="text-gray-600">{special.description}</p>
                          </div>
                          <div className="flex items-center">
                            <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                              special.approval_status === 'approved' 
                                ? 'bg-green-100 text-green-800'
                                : special.approval_status === 'pending'
                                ? 'bg-yellow-100 text-yellow-800'
                                : 'bg-red-100 text-red-800'
                            }`}>
                              {special.approval_status.charAt(0).toUpperCase() + special.approval_status.slice(1)}
                            </span>
                          </div>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <span className="text-gray-500">Type:</span>
                            <p className="font-medium">{special.special_type}</p>
                          </div>
                          <div>
                            <span className="text-gray-500">Price:</span>
                            <p className="font-medium">
                              {special.price ? `$${special.price}` : 'N/A'}
                            </p>
                          </div>
                          <div>
                            <span className="text-gray-500">Time:</span>
                            <p className="font-medium">{special.time_start} - {special.time_end}</p>
                          </div>
                          <div>
                            <span className="text-gray-500">Days:</span>
                            <p className="font-medium">{special.days_available.join(', ')}</p>
                          </div>
                        </div>

                        {special.admin_notes && (
                          <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded">
                            <div className="flex items-start">
                              <DocumentTextIcon className="w-5 h-5 text-blue-500 mr-2 mt-0.5" />
                              <div>
                                <p className="text-sm font-medium text-blue-800">Admin Notes:</p>
                                <p className="text-sm text-blue-700">{special.admin_notes}</p>
                              </div>
                            </div>
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default OwnerDashboard;