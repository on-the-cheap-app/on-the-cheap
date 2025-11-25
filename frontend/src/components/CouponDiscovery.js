import React, { useState, useEffect } from 'react';
import {
  TagIcon,
  MapPinIcon,
  ClockIcon,
  XMarkIcon,
  HeartIcon as HeartIconOutline,
  BookmarkIcon as BookmarkIconOutline,
  QrCodeIcon,
  SparklesIcon,
  GiftIcon,
  ArrowRightIcon,
  MagnifyingGlassIcon
} from '@heroicons/react/24/outline';
import {
  HeartIcon as HeartIconSolid,
  BookmarkIcon as BookmarkIconSolid
} from '@heroicons/react/24/solid';

const CouponDiscovery = ({ userLocation, isAuthenticated, token, onLoginRequired }) => {
  const [coupons, setCoupons] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [selectedCoupon, setSelectedCoupon] = useState(null);
  const [savedCoupons, setSavedCoupons] = useState(new Set());
  const [showRedeemModal, setShowRedeemModal] = useState(false);

  const backendUrl = process.env.REACT_APP_BACKEND_URL 
    ? `${process.env.REACT_APP_BACKEND_URL}/api` 
    : '/api';

  useEffect(() => {
    if (userLocation) {
      loadNearbyCoupons();
    }
    if (isAuthenticated && token) {
      loadSavedCoupons();
    }
  }, [userLocation, isAuthenticated, token]);

  const loadNearbyCoupons = async () => {
    try {
      setLoading(true);
      const response = await fetch(
        `${backendUrl}/coupons/near?latitude=${userLocation.latitude}&longitude=${userLocation.longitude}&radius=10`
      );

      if (response.ok) {
        const data = await response.json();
        setCoupons(data.coupons || []);
      } else {
        setError('Failed to load coupons');
      }
    } catch (error) {
      console.error('Error loading coupons:', error);
      setError('Network error while loading coupons');
    } finally {
      setLoading(false);
    }
  };

  const loadSavedCoupons = async () => {
    try {
      const response = await fetch(`${backendUrl}/users/coupons/saved`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        const savedIds = new Set(data.coupons.map(c => c.id));
        setSavedCoupons(savedIds);
      }
    } catch (error) {
      console.error('Error loading saved coupons:', error);
    }
  };

  const handleSaveCoupon = async (couponId, e) => {
    e.stopPropagation();
    
    if (!isAuthenticated) {
      onLoginRequired();
      return;
    }

    try {
      const isSaved = savedCoupons.has(couponId);
      const method = isSaved ? 'DELETE' : 'POST';
      
      const response = await fetch(`${backendUrl}/users/coupons/${couponId}/save`, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        setSavedCoupons(prev => {
          const newSet = new Set(prev);
          if (isSaved) {
            newSet.delete(couponId);
          } else {
            newSet.add(couponId);
          }
          return newSet;
        });
      }
    } catch (error) {
      console.error('Error saving coupon:', error);
    }
  };

  const handleViewCoupon = async (coupon) => {
    // Track view
    try {
      await fetch(`${backendUrl}/coupons/${coupon.id}/view`, {
        method: 'POST'
      });
    } catch (error) {
      console.error('Error tracking view:', error);
    }

    setSelectedCoupon(coupon);
  };

  const handleRedeem = () => {
    if (!isAuthenticated) {
      onLoginRequired();
      return;
    }
    setShowRedeemModal(true);
  };

  const getCouponDiscount = (coupon) => {
    if (coupon.coupon_type === 'percentage') {
      return `${coupon.discount_percentage}% OFF`;
    } else if (coupon.coupon_type === 'fixed_amount') {
      return `$${coupon.discount_amount} OFF`;
    } else if (coupon.coupon_type === 'bogo') {
      return 'BUY 1 GET 1';
    } else if (coupon.coupon_type === 'free_item') {
      return `FREE ${coupon.free_item}`;
    } else if (coupon.coupon_type === 'combo_deal') {
      return `COMBO $${coupon.combo_price}`;
    }
    return 'SPECIAL OFFER';
  };

  const isExpiringSoon = (validUntil) => {
    const daysUntilExpiry = Math.ceil((new Date(validUntil) - new Date()) / (1000 * 60 * 60 * 24));
    return daysUntilExpiry <= 3 && daysUntilExpiry > 0;
  };

  const isExpired = (validUntil) => {
    return new Date(validUntil) < new Date();
  };

  if (!userLocation) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="bg-gradient-to-r from-orange-50 to-red-50 rounded-lg p-12 text-center border-2 border-orange-200">
          <GiftIcon className="w-16 h-16 text-orange-500 mx-auto mb-4" />
          <h2 className="text-2xl font-bold text-gray-800 mb-2">Discover Amazing Deals!</h2>
          <p className="text-gray-600 mb-6">
            Search for a location above to see exclusive coupons and special offers near you.
          </p>
          <div className="flex items-center justify-center text-orange-600">
            <SparklesIcon className="w-5 h-5 mr-2" />
            <span className="font-medium">Save money on your favorite restaurants!</span>
          </div>
        </div>
      </div>
    );
  }

  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="flex items-center justify-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500"></div>
          <span className="ml-3 text-gray-600">Loading amazing deals...</span>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2 className="text-3xl font-bold text-gray-800 flex items-center">
              <TagIcon className="w-8 h-8 text-orange-500 mr-3" />
              Digital Coupons Near You
            </h2>
            <p className="text-gray-600 mt-2">
              {coupons.length} exclusive {coupons.length === 1 ? 'deal' : 'deals'} available
            </p>
          </div>
          {isAuthenticated && (
            <button
              onClick={loadSavedCoupons}
              className="flex items-center px-4 py-2 bg-orange-100 text-orange-700 rounded-lg hover:bg-orange-200 transition-colors"
            >
              <BookmarkIconSolid className="w-5 h-5 mr-2" />
              {savedCoupons.size} Saved
            </button>
          )}
        </div>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
          {error}
        </div>
      )}

      {coupons.length === 0 ? (
        <div className="text-center py-12 bg-gray-50 rounded-lg">
          <TagIcon className="w-16 h-16 text-gray-400 mx-auto mb-4" />
          <h3 className="text-xl font-semibold text-gray-700 mb-2">No Coupons Available Yet</h3>
          <p className="text-gray-600">
            Check back soon! Restaurants are adding new deals daily.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {coupons.map((coupon) => (
            <div
              key={coupon.id}
              onClick={() => handleViewCoupon(coupon)}
              className="bg-white rounded-lg shadow-lg overflow-hidden hover:shadow-xl transition-all cursor-pointer transform hover:scale-105"
            >
              {/* Restaurant Image */}
              {coupon.restaurant?.photos && coupon.restaurant.photos.length > 0 && (
                <div className="relative h-48 overflow-hidden">
                  <img
                    src={coupon.restaurant.photos[0].url}
                    alt={coupon.restaurant.name}
                    className="w-full h-full object-cover"
                  />
                  <div className="absolute top-2 right-2">
                    <button
                      onClick={(e) => handleSaveCoupon(coupon.id, e)}
                      className="p-2 bg-white rounded-full shadow-lg hover:bg-gray-50 transition-colors"
                    >
                      {savedCoupons.has(coupon.id) ? (
                        <BookmarkIconSolid className="w-5 h-5 text-orange-500" />
                      ) : (
                        <BookmarkIconOutline className="w-5 h-5 text-gray-600" />
                      )}
                    </button>
                  </div>
                </div>
              )}

              {/* Discount Badge */}
              <div className="bg-gradient-to-r from-orange-500 to-red-500 text-white p-4 text-center">
                <div className="text-2xl font-bold">{getCouponDiscount(coupon)}</div>
                <div className="text-sm opacity-90">{coupon.title}</div>
              </div>

              {/* Coupon Info */}
              <div className="p-4">
                <h3 className="font-bold text-gray-800 mb-2">{coupon.restaurant?.name}</h3>
                <p className="text-sm text-gray-600 mb-3 line-clamp-2">{coupon.description}</p>

                {/* Stats */}
                <div className="flex items-center justify-between text-xs text-gray-500 mb-3">
                  <div className="flex items-center">
                    <BookmarkIconOutline className="w-4 h-4 mr-1" />
                    {coupon.saves || 0} saved
                  </div>
                  <div className="flex items-center">
                    <TagIcon className="w-4 h-4 mr-1" />
                    {coupon.total_redemptions || 0} redeemed
                  </div>
                </div>

                {/* Expiry Warning */}
                {isExpiringSoon(coupon.valid_until) && (
                  <div className="bg-yellow-50 border border-yellow-200 text-yellow-800 px-3 py-2 rounded-lg text-xs mb-3">
                    <ClockIcon className="w-4 h-4 inline mr-1" />
                    Expires soon: {new Date(coupon.valid_until).toLocaleDateString()}
                  </div>
                )}

                {isExpired(coupon.valid_until) && (
                  <div className="bg-red-50 border border-red-200 text-red-800 px-3 py-2 rounded-lg text-xs mb-3">
                    Expired on {new Date(coupon.valid_until).toLocaleDateString()}
                  </div>
                )}

                {/* CTA Button */}
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleViewCoupon(coupon);
                  }}
                  className="w-full px-4 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors flex items-center justify-center"
                  disabled={isExpired(coupon.valid_until)}
                >
                  {isExpired(coupon.valid_until) ? (
                    'Expired'
                  ) : (
                    <>
                      View Coupon
                      <ArrowRightIcon className="w-4 h-4 ml-2" />
                    </>
                  )}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Coupon Detail Modal */}
      {selectedCoupon && (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
          <div className="bg-white rounded-xl shadow-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
            {/* Modal Header */}
            <div className="bg-gradient-to-r from-orange-500 to-red-500 text-white p-6 relative">
              <button
                onClick={() => setSelectedCoupon(null)}
                className="absolute top-4 right-4 text-white hover:text-orange-200"
              >
                <XMarkIcon className="w-6 h-6" />
              </button>
              
              <div className="text-center">
                <div className="text-4xl font-bold mb-2">{getCouponDiscount(selectedCoupon)}</div>
                <div className="text-xl">{selectedCoupon.title}</div>
              </div>
            </div>

            {/* Restaurant Info */}
            <div className="p-6 border-b">
              <h3 className="text-2xl font-bold text-gray-800 mb-2">{selectedCoupon.restaurant?.name}</h3>
              <p className="text-gray-600 flex items-center">
                <MapPinIcon className="w-5 h-5 mr-2" />
                {selectedCoupon.restaurant?.address}
              </p>
            </div>

            {/* QR Code Section */}
            <div className="p-6 bg-gray-50 border-b text-center">
              <h4 className="font-semibold text-gray-800 mb-4">Scan to Redeem</h4>
              {selectedCoupon.qr_code ? (
                <div className="inline-block bg-white p-4 rounded-lg shadow-lg">
                  <img
                    src={selectedCoupon.qr_code}
                    alt="QR Code"
                    className="w-64 h-64 mx-auto"
                  />
                  <div className="mt-4 text-center">
                    <p className="text-xs text-gray-500 mb-1">Redemption Code</p>
                    <p className="text-2xl font-mono font-bold text-orange-600">
                      {selectedCoupon.redemption_code}
                    </p>
                  </div>
                </div>
              ) : (
                <div className="text-gray-500">QR Code not available</div>
              )}
            </div>

            {/* Coupon Details */}
            <div className="p-6 space-y-4">
              <div>
                <h4 className="font-semibold text-gray-800 mb-2">Description</h4>
                <p className="text-gray-600">{selectedCoupon.description}</p>
              </div>

              {selectedCoupon.promotional_message && (
                <div className="bg-orange-50 border-l-4 border-orange-500 p-4">
                  <p className="text-orange-800 font-medium">{selectedCoupon.promotional_message}</p>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4 text-sm">
                <div>
                  <p className="text-gray-500">Valid From</p>
                  <p className="font-medium">{new Date(selectedCoupon.valid_from).toLocaleDateString()}</p>
                </div>
                <div>
                  <p className="text-gray-500">Valid Until</p>
                  <p className="font-medium">{new Date(selectedCoupon.valid_until).toLocaleDateString()}</p>
                </div>
              </div>

              {selectedCoupon.minimum_purchase && (
                <div className="bg-yellow-50 border border-yellow-200 p-3 rounded-lg">
                  <p className="text-sm text-yellow-800">
                    Minimum purchase: ${selectedCoupon.minimum_purchase}
                  </p>
                </div>
              )}

              {selectedCoupon.max_per_customer && (
                <div className="text-sm text-gray-600">
                  Limit: {selectedCoupon.max_per_customer} per customer
                </div>
              )}

              {selectedCoupon.terms_conditions && (
                <div>
                  <h4 className="font-semibold text-gray-800 mb-2">Terms & Conditions</h4>
                  <p className="text-sm text-gray-600">{selectedCoupon.terms_conditions}</p>
                </div>
              )}

              <div className="flex gap-3">
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    handleSaveCoupon(selectedCoupon.id, e);
                  }}
                  className="flex-1 px-6 py-3 bg-orange-100 text-orange-700 rounded-lg hover:bg-orange-200 transition-colors flex items-center justify-center"
                >
                  {savedCoupons.has(selectedCoupon.id) ? (
                    <>
                      <BookmarkIconSolid className="w-5 h-5 mr-2" />
                      Saved
                    </>
                  ) : (
                    <>
                      <BookmarkIconOutline className="w-5 h-5 mr-2" />
                      Save Coupon
                    </>
                  )}
                </button>
                
                <button
                  onClick={() => {
                    window.open(`https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(selectedCoupon.restaurant?.address)}`, '_blank');
                  }}
                  className="flex-1 px-6 py-3 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-lg hover:from-orange-600 hover:to-red-600 transition-colors flex items-center justify-center"
                >
                  <MapPinIcon className="w-5 h-5 mr-2" />
                  Get Directions
                </button>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default CouponDiscovery;
