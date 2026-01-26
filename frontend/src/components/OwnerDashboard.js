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
  TrendingUpIcon,
  GlobeAltIcon
} from '@heroicons/react/24/outline';
import CouponCreator from './CouponCreator';
import RestaurantClaimModal from './RestaurantClaimModal';
import OwnerPricing from './OwnerPricing';
import OwnerBilling from './OwnerBilling';
import SpecialCreator from './SpecialCreator';

// Global timezones organized by region
const TIMEZONES = [
  // North America
  { value: 'America/New_York', label: 'Eastern Time (ET) - New York' },
  { value: 'America/Chicago', label: 'Central Time (CT) - Chicago' },
  { value: 'America/Denver', label: 'Mountain Time (MT) - Denver' },
  { value: 'America/Phoenix', label: 'Arizona (no DST)' },
  { value: 'America/Los_Angeles', label: 'Pacific Time (PT) - Los Angeles' },
  { value: 'America/Anchorage', label: 'Alaska Time (AKT)' },
  { value: 'Pacific/Honolulu', label: 'Hawaii Time (HT)' },
  { value: 'America/Toronto', label: 'Eastern Time - Toronto' },
  { value: 'America/Vancouver', label: 'Pacific Time - Vancouver' },
  { value: 'America/Mexico_City', label: 'Mexico City' },
  
  // South America
  { value: 'America/Sao_Paulo', label: 'São Paulo, Brazil' },
  { value: 'America/Buenos_Aires', label: 'Buenos Aires, Argentina' },
  { value: 'America/Bogota', label: 'Bogotá, Colombia' },
  { value: 'America/Lima', label: 'Lima, Peru' },
  
  // Europe
  { value: 'Europe/London', label: 'London, UK (GMT/BST)' },
  { value: 'Europe/Paris', label: 'Paris, France (CET)' },
  { value: 'Europe/Berlin', label: 'Berlin, Germany (CET)' },
  { value: 'Europe/Madrid', label: 'Madrid, Spain (CET)' },
  { value: 'Europe/Rome', label: 'Rome, Italy (CET)' },
  { value: 'Europe/Amsterdam', label: 'Amsterdam, Netherlands (CET)' },
  { value: 'Europe/Moscow', label: 'Moscow, Russia (MSK)' },
  { value: 'Europe/Istanbul', label: 'Istanbul, Turkey' },
  
  // Asia
  { value: 'Asia/Dubai', label: 'Dubai, UAE (GST)' },
  { value: 'Asia/Kolkata', label: 'India (IST)' },
  { value: 'Asia/Bangkok', label: 'Bangkok, Thailand (ICT)' },
  { value: 'Asia/Singapore', label: 'Singapore (SGT)' },
  { value: 'Asia/Hong_Kong', label: 'Hong Kong (HKT)' },
  { value: 'Asia/Shanghai', label: 'China (CST)' },
  { value: 'Asia/Tokyo', label: 'Tokyo, Japan (JST)' },
  { value: 'Asia/Seoul', label: 'Seoul, South Korea (KST)' },
  { value: 'Asia/Manila', label: 'Manila, Philippines' },
  { value: 'Asia/Jakarta', label: 'Jakarta, Indonesia' },
  
  // Oceania
  { value: 'Australia/Sydney', label: 'Sydney, Australia (AEST)' },
  { value: 'Australia/Melbourne', label: 'Melbourne, Australia (AEST)' },
  { value: 'Australia/Perth', label: 'Perth, Australia (AWST)' },
  { value: 'Pacific/Auckland', label: 'Auckland, New Zealand (NZST)' },
  
  // Africa
  { value: 'Africa/Cairo', label: 'Cairo, Egypt (EET)' },
  { value: 'Africa/Johannesburg', label: 'Johannesburg, South Africa (SAST)' },
  { value: 'Africa/Lagos', label: 'Lagos, Nigeria (WAT)' },
  { value: 'Africa/Nairobi', label: 'Nairobi, Kenya (EAT)' },
];

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
  const [showCouponAnalytics, setShowCouponAnalytics] = useState(false);
  const [selectedCoupon, setSelectedCoupon] = useState(null);
  const [couponAnalytics, setCouponAnalytics] = useState(null);
  const [showQRCode, setShowQRCode] = useState(false);
  const [editingProfile, setEditingProfile] = useState(false);
  const [profileData, setProfileData] = useState({
    first_name: user?.first_name || '',
    last_name: user?.last_name || '',
    business_name: user?.business_name || '',
    phone: user?.phone || ''
  });
  const [showClaimModal, setShowClaimModal] = useState(false);
  const [showSpecialCreator, setShowSpecialCreator] = useState(false);
  const [editingSpecial, setEditingSpecial] = useState(null);
  
  // Transfer & Delete Profile States
  const [showTransferModal, setShowTransferModal] = useState(false);
  const [transferRestaurantId, setTransferRestaurantId] = useState(null);
  const [transferEmail, setTransferEmail] = useState('');
  const [showDeleteProfileModal, setShowDeleteProfileModal] = useState(false);
  const [deleteConfirmEmail, setDeleteConfirmEmail] = useState('');
  const [deletePassword, setDeletePassword] = useState('');
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState('');

  const backendUrl = process.env.REACT_APP_BACKEND_URL 
    ? `${process.env.REACT_APP_BACKEND_URL}/api` 
    : '/api';

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
    if (restaurants.length === 0) {
      alert('You need to have at least one restaurant to create specials. Please claim a restaurant first!');
      return;
    }
    setEditingSpecial(null);
    setShowSpecialCreator(true);
  };

  const handleEditSpecial = (special) => {
    setEditingSpecial(special);
    setShowSpecialCreator(true);
  };

  const handleSpecialCreated = (savedSpecial) => {
    if (editingSpecial) {
      // Update existing special in list
      setSpecials(prev => prev.map(s => s.id === savedSpecial.id ? savedSpecial : s));
    } else {
      // Add new special to list
      setSpecials(prev => [savedSpecial, ...prev]);
    }
    // Reload dashboard stats
    loadDashboardData();
  };

  const handleDeleteSpecial = async (specialId) => {
    if (!window.confirm('Are you sure you want to delete this special? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`${backendUrl}/owners/specials/${specialId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setSpecials(prev => prev.filter(s => s.id !== specialId));
        loadDashboardData();
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Failed to delete special');
      }
    } catch (error) {
      console.error('Error deleting special:', error);
      alert('Network error while deleting special');
    }
  };

  const handleTimezoneChange = async (restaurantId, newTimezone) => {
    try {
      const response = await fetch(`${backendUrl}/restaurants/${restaurantId}/timezone`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ timezone: newTimezone })
      });

      if (response.ok) {
        // Update local state
        setRestaurants(prev => prev.map(r => 
          r.id === restaurantId ? { ...r, timezone: newTimezone } : r
        ));
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Failed to update timezone');
      }
    } catch (error) {
      console.error('Error updating timezone:', error);
      alert('Network error while updating timezone');
    }
  };

  const handleClaimRestaurant = (e) => {
    // Prevent any default behavior and event propagation
    if (e) {
      e.preventDefault();
      e.stopPropagation();
    }
    
    setShowClaimModal(true);
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

  const handleCouponStatusUpdate = async (couponId, newStatus) => {
    try {
      const response = await fetch(`${backendUrl}/coupons/${couponId}/status?status=${newStatus}`, {
        method: 'PATCH',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        // Update local state
        setCoupons(prev => prev.map(c =>
          c.id === couponId ? { ...c, status: newStatus } : c
        ));
      } else {
        alert('Failed to update coupon status');
      }
    } catch (error) {
      console.error('Error updating coupon status:', error);
      alert('Network error while updating coupon');
    }
  };

  const handleDeleteCoupon = async (couponId) => {
    if (!window.confirm('Are you sure you want to delete this coupon? This action cannot be undone.')) {
      return;
    }

    try {
      const response = await fetch(`${backendUrl}/coupons/${couponId}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        // Remove from local state
        setCoupons(prev => prev.filter(c => c.id !== couponId));
      } else {
        alert('Failed to delete coupon');
      }
    } catch (error) {
      console.error('Error deleting coupon:', error);
      alert('Network error while deleting coupon');
    }
  };

  const handleViewAnalytics = async (coupon) => {
    try {
      setSelectedCoupon(coupon);
      setShowCouponAnalytics(true);
      
      const response = await fetch(`${backendUrl}/coupons/${coupon.id}/analytics?days=30`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setCouponAnalytics(data);
      }
    } catch (error) {
      console.error('Error loading analytics:', error);
    }
  };

  const handleViewQRCode = (coupon) => {
    setSelectedCoupon(coupon);
    setShowQRCode(true);
  };

  const handleUpdateProfile = async () => {
    try {
      const response = await fetch(`${backendUrl}/owners/profile`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(profileData)
      });

      if (response.ok) {
        const data = await response.json();
        alert('Profile updated successfully!');
        setEditingProfile(false);
        // Update user data in parent if needed
      } else {
        const errorData = await response.json();
        alert(errorData.detail || 'Failed to update profile');
      }
    } catch (error) {
      console.error('Error updating profile:', error);
      alert('Network error while updating profile');
    }
  };

  const handleTransferRestaurant = async () => {
    if (!transferEmail.trim()) {
      setActionError('Please enter the new owner\'s email address');
      return;
    }

    try {
      setActionLoading(true);
      setActionError('');

      const response = await fetch(`${backendUrl}/owners/restaurants/${transferRestaurantId}/transfer`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({ new_owner_email: transferEmail })
      });

      const data = await response.json();

      if (response.ok) {
        alert(data.message);
        setShowTransferModal(false);
        setTransferEmail('');
        setTransferRestaurantId(null);
        loadDashboardData(); // Refresh the dashboard
      } else {
        setActionError(data.detail || 'Failed to transfer restaurant');
      }
    } catch (error) {
      console.error('Error transferring restaurant:', error);
      setActionError('Network error. Please try again.');
    } finally {
      setActionLoading(false);
    }
  };

  const handleDeleteProfile = async () => {
    if (!deleteConfirmEmail.trim() || !deletePassword.trim()) {
      setActionError('Please fill in all fields');
      return;
    }

    try {
      setActionLoading(true);
      setActionError('');

      const response = await fetch(`${backendUrl}/owners/profile`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          confirm_email: deleteConfirmEmail,
          password: deletePassword
        })
      });

      const data = await response.json();

      if (response.ok) {
        alert(data.message + ` (${data.restaurants_unlinked} restaurants unlinked)`);
        setShowDeleteProfileModal(false);
        onClose(); // Close dashboard and log out
        window.location.reload(); // Refresh to clear auth state
      } else {
        setActionError(data.detail || 'Failed to delete profile');
      }
    } catch (error) {
      console.error('Error deleting profile:', error);
      setActionError('Network error. Please try again.');
    } finally {
      setActionLoading(false);
    }
  };

  const openTransferModal = (restaurantId) => {
    setTransferRestaurantId(restaurantId);
    setTransferEmail('');
    setActionError('');
    setShowTransferModal(true);
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4 overflow-hidden">
      <div className="bg-white rounded-lg shadow-xl max-w-6xl w-full h-[90vh] flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-orange-500 to-red-500 text-white p-6 flex justify-between items-center flex-shrink-0 rounded-t-lg">
          <div>
            <h2 className="text-2xl font-bold">Restaurant Owner Dashboard</h2>
            <p className="text-orange-100">Welcome back, {user?.first_name || 'Owner'}!</p>
          </div>
          <div className="flex items-center space-x-3">
            <button
              onClick={onClose}
              className="px-4 py-2 bg-white bg-opacity-20 hover:bg-opacity-30 text-white rounded-lg transition-colors flex items-center"
            >
              <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10 19l-7-7m0 0l7-7m-7 7h18" />
              </svg>
              Back to Home
            </button>
            <button
              onClick={onClose}
              className="text-white hover:text-orange-200 transition-colors"
            >
              <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </button>
          </div>
        </div>

        <div className="flex flex-col md:flex-row flex-1 min-h-0 overflow-hidden">
          {/* Sidebar Navigation */}
          <div className="bg-gray-50 p-4 md:w-64 border-r flex-shrink-0 md:overflow-y-auto">
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
              <button
                onClick={() => setActiveTab('profile')}
                className={`w-full flex items-center px-4 py-2 text-left rounded-lg transition-colors ${
                  activeTab === 'profile' 
                    ? 'bg-orange-100 text-orange-700 border-orange-200' 
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <DocumentTextIcon className="w-5 h-5 mr-3" />
                My Profile
              </button>
              
              {/* Divider */}
              <div className="border-t border-gray-200 my-2"></div>
              
              <button
                onClick={() => setActiveTab('pricing')}
                className={`w-full flex items-center px-4 py-2 text-left rounded-lg transition-colors ${
                  activeTab === 'pricing' 
                    ? 'bg-orange-100 text-orange-700 border-orange-200' 
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                Pricing & Plans
              </button>
              
              <button
                onClick={() => setActiveTab('billing')}
                className={`w-full flex items-center px-4 py-2 text-left rounded-lg transition-colors ${
                  activeTab === 'billing' 
                    ? 'bg-orange-100 text-orange-700 border-orange-200' 
                    : 'text-gray-600 hover:bg-gray-100'
                }`}
              >
                <svg className="w-5 h-5 mr-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 10h18M7 15h1m4 0h1m-7 4h12a3 3 0 003-3V8a3 3 0 00-3-3H6a3 3 0 00-3 3v8a3 3 0 003 3z" />
                </svg>
                Billing
              </button>
            </nav>
          </div>

          {/* Main Content */}
          <div className="flex-1 p-6 overflow-y-scroll" style={{minHeight: 0}}>
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
                        onClick={() => handleCreateCoupon()}
                        className="w-full flex items-center justify-center px-4 py-2 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-lg hover:from-orange-600 hover:to-red-600 transition-all transform hover:scale-105"
                        disabled={restaurants.length === 0}
                      >
                        <SparklesIcon className="w-5 h-5 mr-2" />
                        Create Digital Coupon
                      </button>
                      <button
                        onClick={handleCreateSpecial}
                        className="w-full flex items-center justify-center px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
                        disabled={restaurants.length === 0}
                      >
                        <PlusIcon className="w-5 h-5 mr-2" />
                        Create New Special
                      </button>
                      <button
                        onClick={handleClaimRestaurant}
                        className="w-full flex items-center justify-center px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
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
                          
                          {/* Timezone Selector */}
                          <div className="mb-3">
                            <label className="flex items-center text-xs text-gray-600 mb-1">
                              <GlobeAltIcon className="w-3 h-3 mr-1" />
                              Time Zone
                            </label>
                            <select
                              value={restaurant.timezone || 'America/Chicago'}
                              onChange={(e) => handleTimezoneChange(restaurant.id, e.target.value)}
                              className="w-full px-2 py-1 text-sm border border-gray-300 rounded focus:ring-2 focus:ring-orange-500 focus:border-orange-500"
                            >
                              {TIMEZONES.map((tz) => (
                                <option key={tz.value} value={tz.value}>
                                  {tz.label}
                                </option>
                              ))}
                            </select>
                          </div>
                          
                          <button
                            onClick={(e) => {
                              e.preventDefault();
                              handleCreateSpecial(restaurant.id);
                            }}
                            className="w-full px-3 py-2 bg-orange-100 text-orange-700 text-sm rounded hover:bg-orange-200 transition-colors mb-2"
                          >
                            Manage Specials
                          </button>
                          <button
                            onClick={(e) => {
                              e.preventDefault();
                              openTransferModal(restaurant.id);
                            }}
                            className="w-full px-3 py-2 bg-gray-100 text-gray-600 text-sm rounded hover:bg-gray-200 transition-colors flex items-center justify-center"
                          >
                            <ArrowRightOnRectangleIcon className="w-4 h-4 mr-1" />
                            Transfer Ownership
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}

            {/* Digital Coupons Tab */}
            {activeTab === 'coupons' && (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-xl font-semibold text-gray-800">Digital Coupons</h3>
                  <button
                    onClick={() => handleCreateCoupon()}
                    className="flex items-center px-4 py-2 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-lg hover:from-orange-600 hover:to-red-600 transition-all transform hover:scale-105"
                    disabled={restaurants.length === 0}
                  >
                    <SparklesIcon className="w-5 h-5 mr-2" />
                    Create Coupon
                  </button>
                </div>

                {coupons.length === 0 ? (
                  <div className="text-center py-12 bg-gradient-to-br from-orange-50 to-red-50 rounded-lg border-2 border-dashed border-orange-300">
                    <GiftIcon className="w-16 h-16 text-orange-400 mx-auto mb-4" />
                    <h4 className="text-lg font-medium text-gray-800 mb-2">Start Driving Foot Traffic!</h4>
                    <p className="text-gray-600 mb-4 max-w-md mx-auto">
                      Create irresistible digital coupons that customers cannot resist. 
                      Get QR codes, track redemptions, and watch your revenue grow!
                    </p>
                    {restaurants.length === 0 ? (
                      <div className="mb-4">
                        <p className="text-sm text-orange-600 mb-2">You need to claim a restaurant first</p>
                        <button
                          onClick={handleClaimRestaurant}
                          className="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors"
                        >
                          Claim Restaurant
                        </button>
                      </div>
                    ) : (
                      <button
                        onClick={() => handleCreateCoupon()}
                        className="px-6 py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-lg hover:from-orange-600 hover:to-red-600 transition-all transform hover:scale-105"
                      >
                        <SparklesIcon className="w-5 h-5 mr-2 inline" />
                        Create Your First Coupon
                      </button>
                    )}
                  </div>
                ) : (
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {coupons.map((coupon) => (
                      <div key={coupon.id} className="bg-white rounded-lg shadow-lg border overflow-hidden hover:shadow-xl transition-shadow">
                        {/* Coupon Header */}
                        <div className={`p-4 text-white bg-gradient-to-r ${
                          coupon.status === 'active' 
                            ? 'from-green-500 to-green-600' 
                            : coupon.status === 'paused' 
                            ? 'from-yellow-500 to-yellow-600'
                            : 'from-gray-500 to-gray-600'
                        }`}>
                          <div className="flex justify-between items-start">
                            <div>
                              <h4 className="font-bold text-lg">{coupon.title}</h4>
                              <p className="text-sm opacity-90">{coupon.description}</p>
                            </div>
                            <div className="text-right">
                              <div className="text-2xl font-bold">
                                {coupon.coupon_type === 'percentage' && `${coupon.discount_percentage}%`}
                                {coupon.coupon_type === 'fixed_amount' && `$${coupon.discount_amount}`}
                                {coupon.coupon_type === 'bogo' && 'BOGO'}
                                {coupon.coupon_type === 'free_item' && 'FREE'}
                                {coupon.coupon_type === 'combo_deal' && `$${coupon.combo_price}`}
                              </div>
                              <div className="text-xs opacity-75">
                                {coupon.coupon_type === 'percentage' && 'OFF'}
                                {coupon.coupon_type === 'fixed_amount' && 'OFF'}
                                {coupon.coupon_type === 'combo_deal' && 'COMBO'}
                              </div>
                            </div>
                          </div>
                        </div>

                        {/* Coupon Stats */}
                        <div className="p-4">
                          <div className="grid grid-cols-3 gap-4 mb-4">
                            <div className="text-center">
                              <div className="text-lg font-bold text-gray-800">{coupon.views || 0}</div>
                              <div className="text-xs text-gray-500">Views</div>
                            </div>
                            <div className="text-center">
                              <div className="text-lg font-bold text-gray-800">{coupon.saves || 0}</div>
                              <div className="text-xs text-gray-500">Saves</div>
                            </div>
                            <div className="text-center">
                              <div className="text-lg font-bold text-green-600">{coupon.total_redemptions || 0}</div>
                              <div className="text-xs text-gray-500">Redeemed</div>
                            </div>
                          </div>

                          <div className="space-y-2 text-sm">
                            <div className="flex justify-between">
                              <span className="text-gray-600">Valid until:</span>
                              <span className="font-medium">{new Date(coupon.valid_until).toLocaleDateString()}</span>
                            </div>
                            <div className="flex justify-between">
                              <span className="text-gray-600">Max uses:</span>
                              <span className="font-medium">{coupon.max_redemptions || 'Unlimited'}</span>
                            </div>
                          </div>

                          <div className="mt-4 space-y-2">
                            <div className="flex space-x-2">
                              <button
                                onClick={() => handleViewAnalytics(coupon)}
                                className="flex-1 px-3 py-2 bg-blue-100 text-blue-700 text-sm rounded hover:bg-blue-200 transition-colors"
                              >
                                <ChartBarIcon className="w-4 h-4 inline mr-1" />
                                Analytics
                              </button>
                              <button
                                onClick={() => handleViewQRCode(coupon)}
                                className="flex-1 px-3 py-2 bg-orange-100 text-orange-700 text-sm rounded hover:bg-orange-200 transition-colors"
                              >
                                <QrCodeIcon className="w-4 h-4 inline mr-1" />
                                QR Code
                              </button>
                            </div>
                            
                            <div className="flex space-x-2">
                              {coupon.status === 'active' ? (
                                <button
                                  onClick={() => handleCouponStatusUpdate(coupon.id, 'paused')}
                                  className="flex-1 px-3 py-2 bg-yellow-100 text-yellow-700 text-sm rounded hover:bg-yellow-200 transition-colors"
                                >
                                  Pause
                                </button>
                              ) : (
                                <button
                                  onClick={() => handleCouponStatusUpdate(coupon.id, 'active')}
                                  className="flex-1 px-3 py-2 bg-green-100 text-green-700 text-sm rounded hover:bg-green-200 transition-colors"
                                >
                                  Activate
                                </button>
                              )}
                              <button
                                onClick={() => handleDeleteCoupon(coupon.id)}
                                className="flex-1 px-3 py-2 bg-red-100 text-red-700 text-sm rounded hover:bg-red-200 transition-colors"
                              >
                                Delete
                              </button>
                            </div>
                          </div>
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
                        <div className="flex gap-4">
                          {/* Special Image */}
                          {special.image && (
                            <div className="flex-shrink-0">
                              <img 
                                src={special.image} 
                                alt={special.title}
                                className="w-32 h-32 object-cover rounded-lg"
                              />
                            </div>
                          )}
                          
                          <div className="flex-1">
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

                        {/* Valid Period */}
                        <div className="mt-4 pt-4 border-t border-gray-100">
                          <div className="flex flex-wrap items-center justify-between">
                            <div className="text-sm text-gray-500">
                              <span>Valid: {new Date(special.valid_from).toLocaleDateString()} - {new Date(special.valid_until).toLocaleDateString()}</span>
                              {special.discount_percentage && (
                                <span className="ml-4 px-2 py-1 bg-green-100 text-green-700 rounded-full text-xs font-medium">
                                  {special.discount_percentage}% OFF
                                </span>
                              )}
                            </div>
                            <div className="flex space-x-2 mt-2 sm:mt-0">
                              <button
                                onClick={() => handleEditSpecial(special)}
                                className="px-3 py-1 bg-blue-100 text-blue-700 text-sm rounded hover:bg-blue-200 transition-colors"
                              >
                                Edit
                              </button>
                              <button
                                onClick={() => handleDeleteSpecial(special.id)}
                                className="px-3 py-1 bg-red-100 text-red-700 text-sm rounded hover:bg-red-200 transition-colors"
                              >
                                Delete
                              </button>
                            </div>
                          </div>
                        </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>

            {/* Profile Tab */}
            {activeTab === 'profile' && (
              <div>
                <div className="flex justify-between items-center mb-6">
                  <h3 className="text-xl font-semibold text-gray-800">My Profile</h3>
                  {!editingProfile && (
                    <button
                      onClick={() => setEditingProfile(true)}
                      className="px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors"
                    >
                      Edit Profile
                    </button>
                  )}
                </div>

                <div className="bg-white rounded-lg shadow border p-6">
                  <div className="space-y-4">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          First Name
                        </label>
                        {editingProfile ? (
                          <input
                            type="text"
                            value={profileData.first_name}
                            onChange={(e) => setProfileData(prev => ({...prev, first_name: e.target.value}))}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                          />
                        ) : (
                          <p className="text-gray-900">{user?.first_name || 'Not set'}</p>
                        )}
                      </div>

                      <div>
                        <label className="block text-sm font-medium text-gray-700 mb-2">
                          Last Name
                        </label>
                        {editingProfile ? (
                          <input
                            type="text"
                            value={profileData.last_name}
                            onChange={(e) => setProfileData(prev => ({...prev, last_name: e.target.value}))}
                            className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                          />
                        ) : (
                          <p className="text-gray-900">{user?.last_name || 'Not set'}</p>
                        )}
                      </div>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Business Name
                      </label>
                      {editingProfile ? (
                        <input
                          type="text"
                          value={profileData.business_name}
                          onChange={(e) => setProfileData(prev => ({...prev, business_name: e.target.value}))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                        />
                      ) : (
                        <p className="text-gray-900">{user?.business_name || 'Not set'}</p>
                      )}
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Email
                      </label>
                      <p className="text-gray-900">{user?.email}</p>
                      <p className="text-xs text-gray-500 mt-1">Email cannot be changed</p>
                    </div>

                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Phone
                      </label>
                      {editingProfile ? (
                        <input
                          type="tel"
                          value={profileData.phone}
                          onChange={(e) => setProfileData(prev => ({...prev, phone: e.target.value}))}
                          className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                          placeholder="(555) 123-4567"
                        />
                      ) : (
                        <p className="text-gray-900">{user?.phone || 'Not set'}</p>
                      )}
                    </div>

                    {editingProfile && (
                      <div className="flex space-x-3 pt-4">
                        <button
                          onClick={handleUpdateProfile}
                          className="flex-1 px-4 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 transition-colors"
                        >
                          Save Changes
                        </button>
                        <button
                          onClick={() => {
                            setEditingProfile(false);
                            setProfileData({
                              first_name: user?.first_name || '',
                              last_name: user?.last_name || '',
                              business_name: user?.business_name || '',
                              phone: user?.phone || ''
                            });
                          }}
                          className="flex-1 px-4 py-2 bg-gray-300 text-gray-700 rounded-lg hover:bg-gray-400 transition-colors"
                        >
                          Cancel
                        </button>
                      </div>
                    )}
                  </div>
                </div>

                {/* Danger Zone */}
                <div className="mt-8 p-6 border-2 border-red-200 rounded-lg bg-red-50">
                  <h4 className="text-lg font-semibold text-red-700 mb-2">Danger Zone</h4>
                  <p className="text-sm text-red-600 mb-4">
                    Once you delete your profile, all your data will be permanently removed. Your restaurants will be unlinked but remain in the system.
                  </p>
                  <button
                    onClick={() => {
                      setDeleteConfirmEmail('');
                      setDeletePassword('');
                      setActionError('');
                      setShowDeleteProfileModal(true);
                    }}
                    className="px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors"
                  >
                    Delete My Profile
                  </button>
                </div>
              </div>
            )}

        {/* Coupon Creator Modal */}
        {showCouponCreator && selectedRestaurant && (
          <CouponCreator
            restaurant={selectedRestaurant}
            token={token}
            onClose={() => {
              setShowCouponCreator(false);
              setSelectedRestaurant(null);
            }}
            onSuccess={handleCouponSuccess}
          />
        )}

        {/* Restaurant Claim Modal */}
        {showClaimModal && (
          <RestaurantClaimModal
            token={token}
            onClose={() => setShowClaimModal(false)}
            onSuccess={() => {
              setShowClaimModal(false);
              loadDashboardData(); // Reload dashboard data
            }}
          />
        )}

        {/* Special Creator Modal */}
        {showSpecialCreator && (
          <SpecialCreator
            restaurants={restaurants}
            token={token}
            editingSpecial={editingSpecial}
            onClose={() => {
              setShowSpecialCreator(false);
              setEditingSpecial(null);
            }}
            onSpecialCreated={handleSpecialCreated}
          />
        )}

        {/* QR Code Modal */}
        {showQRCode && selectedCoupon && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-md w-full p-6">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-xl font-bold text-gray-800">Coupon QR Code</h3>
                <button
                  onClick={() => {
                    setShowQRCode(false);
                    setSelectedCoupon(null);
                  }}
                  className="text-gray-500 hover:text-gray-700"
                >
                  <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>

              <div className="text-center">
                <h4 className="font-semibold text-gray-800 mb-2">{selectedCoupon.title}</h4>
                <p className="text-sm text-gray-600 mb-4">{selectedCoupon.description}</p>

                {selectedCoupon.qr_code ? (
                  <div className="bg-white p-4 rounded-lg border-2 border-gray-200 mb-4">
                    <img
                      src={selectedCoupon.qr_code}
                      alt="QR Code"
                      className="w-full max-w-xs mx-auto"
                    />
                  </div>
                ) : (
                  <div className="bg-gray-100 p-8 rounded-lg mb-4">
                    <QrCodeIcon className="w-16 h-16 text-gray-400 mx-auto" />
                    <p className="text-gray-500 mt-2">QR Code not available</p>
                  </div>
                )}

                <div className="bg-orange-50 p-4 rounded-lg mb-4">
                  <p className="text-xs text-gray-600 mb-1">Redemption Code</p>
                  <p className="text-2xl font-mono font-bold text-orange-600">{selectedCoupon.redemption_code}</p>
                </div>

                <button
                  onClick={() => {
                    // Download QR code
                    const link = document.createElement('a');
                    link.href = selectedCoupon.qr_code;
                    link.download = `coupon-${selectedCoupon.id}-qr.png`;
                    link.click();
                  }}
                  className="w-full px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors"
                >
                  Download QR Code
                </button>
              </div>
            </div>
          </div>
        )}

        {/* Analytics Modal */}
        {showCouponAnalytics && selectedCoupon && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full max-h-[90vh] overflow-y-auto">
              <div className="bg-gradient-to-r from-blue-500 to-purple-500 text-white p-6">
                <div className="flex justify-between items-center">
                  <div>
                    <h3 className="text-2xl font-bold">Coupon Analytics</h3>
                    <p className="text-blue-100">{selectedCoupon.title}</p>
                  </div>
                  <button
                    onClick={() => {
                      setShowCouponAnalytics(false);
                      setSelectedCoupon(null);
                      setCouponAnalytics(null);
                    }}
                    className="text-white hover:text-blue-200"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
              </div>

              <div className="p-6">
                {couponAnalytics ? (
                  <>
                    {/* Key Metrics */}
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
                      <div className="bg-blue-50 p-4 rounded-lg text-center">
                        <div className="text-3xl font-bold text-blue-600">{couponAnalytics.total_views || 0}</div>
                        <div className="text-sm text-gray-600">Views</div>
                      </div>
                      <div className="bg-purple-50 p-4 rounded-lg text-center">
                        <div className="text-3xl font-bold text-purple-600">{couponAnalytics.total_saves || 0}</div>
                        <div className="text-sm text-gray-600">Saves</div>
                      </div>
                      <div className="bg-green-50 p-4 rounded-lg text-center">
                        <div className="text-3xl font-bold text-green-600">{couponAnalytics.total_redemptions || 0}</div>
                        <div className="text-sm text-gray-600">Redemptions</div>
                      </div>
                      <div className="bg-orange-50 p-4 rounded-lg text-center">
                        <div className="text-3xl font-bold text-orange-600">{couponAnalytics.unique_customers || 0}</div>
                        <div className="text-sm text-gray-600">Customers</div>
                      </div>
                    </div>

                    {/* Financial Impact */}
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-6">
                      <div className="bg-gradient-to-br from-green-50 to-emerald-50 p-6 rounded-lg border border-green-200">
                        <h4 className="font-semibold text-gray-800 mb-2">Revenue Impact</h4>
                        <div className="text-3xl font-bold text-green-600 mb-1">
                          ${(couponAnalytics.estimated_revenue_generated || 0).toFixed(2)}
                        </div>
                        <p className="text-sm text-gray-600">Estimated revenue generated</p>
                      </div>
                      <div className="bg-gradient-to-br from-red-50 to-rose-50 p-6 rounded-lg border border-red-200">
                        <h4 className="font-semibold text-gray-800 mb-2">Discount Given</h4>
                        <div className="text-3xl font-bold text-red-600 mb-1">
                          ${(couponAnalytics.total_discount_given || 0).toFixed(2)}
                        </div>
                        <p className="text-sm text-gray-600">Total discounts applied</p>
                      </div>
                    </div>

                    {/* Engagement Rates */}
                    <div className="bg-gray-50 p-6 rounded-lg mb-6">
                      <h4 className="font-semibold text-gray-800 mb-4">Engagement Metrics</h4>
                      <div className="space-y-3">
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span className="text-gray-600">View to Save Rate</span>
                            <span className="font-medium">{(couponAnalytics.view_to_save_rate || 0).toFixed(1)}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-purple-500 rounded-full h-2 transition-all"
                              style={{ width: `${Math.min(couponAnalytics.view_to_save_rate || 0, 100)}%` }}
                            ></div>
                          </div>
                        </div>
                        <div>
                          <div className="flex justify-between text-sm mb-1">
                            <span className="text-gray-600">Save to Redemption Rate</span>
                            <span className="font-medium">{(couponAnalytics.save_to_redemption_rate || 0).toFixed(1)}%</span>
                          </div>
                          <div className="w-full bg-gray-200 rounded-full h-2">
                            <div
                              className="bg-green-500 rounded-full h-2 transition-all"
                              style={{ width: `${Math.min(couponAnalytics.save_to_redemption_rate || 0, 100)}%` }}
                            ></div>
                          </div>
                        </div>
                      </div>
                    </div>

                    {/* ROI */}
                    <div className={`p-6 rounded-lg border-2 ${
                      (couponAnalytics.roi_percentage || 0) > 0
                        ? 'bg-gradient-to-br from-green-50 to-emerald-50 border-green-300'
                        : 'bg-gradient-to-br from-yellow-50 to-amber-50 border-yellow-300'
                    }`}>
                      <div className="flex items-center justify-between">
                        <div>
                          <h4 className="font-semibold text-gray-800 mb-1">Return on Investment (ROI)</h4>
                          <p className="text-sm text-gray-600">Based on last 30 days</p>
                        </div>
                        <div className="text-right">
                          <div className={`text-4xl font-bold ${
                            (couponAnalytics.roi_percentage || 0) > 0 ? 'text-green-600' : 'text-yellow-600'
                          }`}>
                            {(couponAnalytics.roi_percentage || 0).toFixed(1)}%
                          </div>
                        </div>
                      </div>
                    </div>
                  </>
                ) : (
                  <div className="text-center py-8">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                    <p className="text-gray-600">Loading analytics...</p>
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* Pricing Tab */}
        {activeTab === 'pricing' && (
          <div style={{height: '100%', overflow: 'auto'}}>
            <OwnerPricing />
          </div>
        )}

        {/* Billing Tab */}
        {activeTab === 'billing' && (
          <div>
            <OwnerBilling />
          </div>
        )}
      </div>
    </div>
  );
};

export default OwnerDashboard;