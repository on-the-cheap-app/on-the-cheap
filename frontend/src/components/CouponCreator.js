import React, { useState, useEffect } from 'react';
import { 
  TagIcon,
  CalendarDaysIcon,
  ClockIcon,
  GiftIcon,
  ChartBarIcon,
  QrCodeIcon,
  SparklesIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XMarkIcon
} from '@heroicons/react/24/outline';

const CouponCreator = ({ restaurant, onClose, onSuccess, token }) => {
  const [step, setStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const [couponData, setCouponData] = useState({
    title: '',
    description: '',
    coupon_type: 'percentage',
    discount_percentage: 20,
    discount_amount: 5.00,
    free_item: '',
    combo_price: 15.00,
    valid_from: new Date().toISOString().split('T')[0],
    valid_until: new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0], // 30 days from now
    max_redemptions: 100,
    max_per_customer: 1,
    minimum_purchase: 0,
    target_audience: 'all_customers',
    days_of_week: ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
    time_restrictions: null,
    terms_conditions: '',
    promotional_message: ''
  });

  const backendUrl = process.env.REACT_APP_BACKEND_URL 
    ? `${process.env.REACT_APP_BACKEND_URL}/api` 
    : '/api';

  const couponTypes = [
    {
      id: 'percentage',
      name: 'Percentage Off',
      description: 'Save a percentage on total order',
      icon: '📊',
      example: '20% off your entire order',
      popular: true
    },
    {
      id: 'fixed_amount',
      name: 'Fixed Amount Off',
      description: 'Save a fixed dollar amount',
      icon: '💵',
      example: '$5 off orders over $25'
    },
    {
      id: 'bogo',
      name: 'Buy One Get One',
      description: 'Classic BOGO deal',
      icon: '🎁',
      example: 'Buy 1 appetizer, get 1 free',
      popular: true
    },
    {
      id: 'free_item',
      name: 'Free Item',
      description: 'Get a specific item free',
      icon: '🆓',
      example: 'Free dessert with entree'
    },
    {
      id: 'combo_deal',
      name: 'Combo Deal',
      description: 'Special combo pricing',
      icon: '🍽️',
      example: 'Burger + fries + drink = $15'
    }
  ];

  const targetAudiences = [
    { id: 'all_customers', name: 'All Customers', icon: '👥' },
    { id: 'new_customers', name: 'New Customers Only', icon: '🆕' },
    { id: 'returning_customers', name: 'Returning Customers', icon: '↩️' },
    { id: 'loyal_customers', name: 'Loyal Customers', icon: '⭐' }
  ];

  const daysOfWeek = [
    { id: 'monday', name: 'Mon', fullName: 'Monday' },
    { id: 'tuesday', name: 'Tue', fullName: 'Tuesday' },
    { id: 'wednesday', name: 'Wed', fullName: 'Wednesday' },
    { id: 'thursday', name: 'Thu', fullName: 'Thursday' },
    { id: 'friday', name: 'Fri', fullName: 'Friday' },
    { id: 'saturday', name: 'Sat', fullName: 'Saturday' },
    { id: 'sunday', name: 'Sun', fullName: 'Sunday' }
  ];

  const handleInputChange = (field, value) => {
    setCouponData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const handleDayToggle = (day) => {
    setCouponData(prev => ({
      ...prev,
      days_of_week: prev.days_of_week.includes(day)
        ? prev.days_of_week.filter(d => d !== day)
        : [...prev.days_of_week, day]
    }));
  };

  const validateStep = (stepNumber) => {
    switch (stepNumber) {
      case 1:
        return couponData.title.length > 0 && couponData.description.length > 0;
      case 2:
        if (couponData.coupon_type === 'percentage') {
          return couponData.discount_percentage > 0 && couponData.discount_percentage <= 100;
        } else if (couponData.coupon_type === 'fixed_amount') {
          return couponData.discount_amount > 0;
        } else if (couponData.coupon_type === 'free_item') {
          return couponData.free_item.length > 0;
        } else if (couponData.coupon_type === 'combo_deal') {
          return couponData.combo_price > 0;
        }
        return true;
      case 3:
        return new Date(couponData.valid_from) < new Date(couponData.valid_until);
      default:
        return true;
    }
  };

  const generatePreview = () => {
    const selectedType = couponTypes.find(t => t.id === couponData.coupon_type);
    let discount = '';
    
    if (couponData.coupon_type === 'percentage') {
      discount = `${couponData.discount_percentage}% OFF`;
    } else if (couponData.coupon_type === 'fixed_amount') {
      discount = `$${couponData.discount_amount} OFF`;
    } else if (couponData.coupon_type === 'bogo') {
      discount = 'BUY 1 GET 1 FREE';
    } else if (couponData.coupon_type === 'free_item') {
      discount = `FREE ${couponData.free_item.toUpperCase()}`;
    } else if (couponData.coupon_type === 'combo_deal') {
      discount = `COMBO DEAL $${couponData.combo_price}`;
    }

    return { selectedType, discount };
  };

  const handleSubmit = async () => {
    setLoading(true);
    setError('');
    
    try {
      const response = await fetch(`${backendUrl}/owners/coupons?restaurant_id=${restaurant.id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify(couponData)
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess('🎉 Coupon created successfully! Your QR code is ready for customers.');
        setTimeout(() => {
          onSuccess(data);
          onClose();
        }, 2000);
      } else {
        setError(data.detail || 'Failed to create coupon');
      }
    } catch (error) {
      console.error('Error creating coupon:', error);
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const { selectedType, discount } = generatePreview();

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-orange-500 to-red-500 text-white p-6 relative flex-shrink-0">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-white hover:text-orange-200 transition-colors"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
          
          <div className="flex items-center">
            <SparklesIcon className="w-8 h-8 mr-3" />
            <div>
              <h2 className="text-2xl font-bold">Create Digital Coupon</h2>
              <p className="text-orange-100">{restaurant.name} • Drive foot traffic with irresistible deals!</p>
            </div>
          </div>

          {/* Progress bar */}
          <div className="mt-4">
            <div className="flex items-center justify-between text-sm mb-2">
              <span>Step {step} of 4</span>
              <span>{Math.round((step / 4) * 100)}% Complete</span>
            </div>
            <div className="w-full bg-orange-600 rounded-full h-2">
              <div 
                className="bg-white rounded-full h-2 transition-all duration-300"
                style={{ width: `${(step / 4) * 100}%` }}
              ></div>
            </div>
          </div>
        </div>

        <div className="flex flex-1 min-h-0">
          {/* Main Form */}
          <div className="flex-1 p-6 overflow-y-auto">
            {error && (
              <div className="mb-4 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg flex items-center">
                <ExclamationTriangleIcon className="w-5 h-5 mr-2" />
                {error}
              </div>
            )}

            {success && (
              <div className="mb-4 p-4 bg-green-50 border border-green-200 text-green-700 rounded-lg flex items-center">
                <CheckCircleIcon className="w-5 h-5 mr-2" />
                {success}
              </div>
            )}

            {/* Step 1: Basic Info */}
            {step === 1 && (
              <div className="space-y-6">
                <div className="text-center mb-6">
                  <h3 className="text-xl font-semibold text-gray-800 mb-2">Let's Create Your Irresistible Offer!</h3>
                  <p className="text-gray-600">First, give your coupon a compelling title and description</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Coupon Title *
                  </label>
                  <input
                    type="text"
                    value={couponData.title}
                    onChange={(e) => handleInputChange('title', e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    placeholder="e.g., Happy Hour Special, Weekend Brunch Deal..."
                    maxLength={100}
                  />
                  <p className="text-xs text-gray-500 mt-1">{couponData.title.length}/100 characters</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Description *
                  </label>
                  <textarea
                    value={couponData.description}
                    onChange={(e) => handleInputChange('description', e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    rows={4}
                    placeholder="Describe what makes this offer special. Be specific about what customers get!"
                    maxLength={500}
                  ></textarea>
                  <p className="text-xs text-gray-500 mt-1">{couponData.description.length}/500 characters</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Promotional Message (Optional)
                  </label>
                  <input
                    type="text"
                    value={couponData.promotional_message}
                    onChange={(e) => handleInputChange('promotional_message', e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    placeholder="e.g., Limited time only! Don't miss out!"
                    maxLength={200}
                  />
                </div>
              </div>
            )}

            {/* Step 2: Discount Type & Amount */}
            {step === 2 && (
              <div className="space-y-6">
                <div className="text-center mb-6">
                  <h3 className="text-xl font-semibold text-gray-800 mb-2">Choose Your Discount Type</h3>
                  <p className="text-gray-600">Select the type of deal that will drive the most customers</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  {couponTypes.map((type) => (
                    <div
                      key={type.id}
                      onClick={() => handleInputChange('coupon_type', type.id)}
                      className={`relative p-4 border-2 rounded-lg cursor-pointer transition-all hover:shadow-md ${
                        couponData.coupon_type === type.id
                          ? 'border-orange-500 bg-orange-50'
                          : 'border-gray-200 hover:border-orange-300'
                      }`}
                    >
                      {type.popular && (
                        <div className="absolute -top-2 -right-2 bg-red-500 text-white text-xs px-2 py-1 rounded-full">
                          Popular!
                        </div>
                      )}
                      <div className="flex items-start">
                        <span className="text-2xl mr-3">{type.icon}</span>
                        <div>
                          <h4 className="font-semibold text-gray-800">{type.name}</h4>
                          <p className="text-sm text-gray-600 mb-2">{type.description}</p>
                          <p className="text-xs text-orange-600 font-medium">{type.example}</p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Discount Value Input */}
                <div className="bg-gray-50 p-4 rounded-lg">
                  <h4 className="font-semibold text-gray-800 mb-3">Configure Your Discount</h4>
                  
                  {couponData.coupon_type === 'percentage' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Discount Percentage
                      </label>
                      <div className="flex items-center">
                        <input
                          type="number"
                          value={couponData.discount_percentage}
                          onChange={(e) => handleInputChange('discount_percentage', parseInt(e.target.value))}
                          className="w-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                          min="1"
                          max="100"
                        />
                        <span className="ml-2 text-gray-600">% off</span>
                        <div className="ml-4 text-sm text-gray-500">
                          Sweet spot: 15-25% drives good traffic without hurting margins
                        </div>
                      </div>
                    </div>
                  )}

                  {couponData.coupon_type === 'fixed_amount' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Discount Amount
                      </label>
                      <div className="flex items-center">
                        <span className="text-gray-600 mr-2">$</span>
                        <input
                          type="number"
                          value={couponData.discount_amount}
                          onChange={(e) => handleInputChange('discount_amount', parseFloat(e.target.value))}
                          className="w-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                          min="0.01"
                          step="0.01"
                        />
                        <span className="ml-2 text-gray-600">off order</span>
                      </div>
                    </div>
                  )}

                  {couponData.coupon_type === 'free_item' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Free Item
                      </label>
                      <input
                        type="text"
                        value={couponData.free_item}
                        onChange={(e) => handleInputChange('free_item', e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                        placeholder="e.g., appetizer, dessert, drink..."
                      />
                    </div>
                  )}

                  {couponData.coupon_type === 'combo_deal' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Combo Price
                      </label>
                      <div className="flex items-center">
                        <span className="text-gray-600 mr-2">$</span>
                        <input
                          type="number"
                          value={couponData.combo_price}
                          onChange={(e) => handleInputChange('combo_price', parseFloat(e.target.value))}
                          className="w-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                          min="0.01"
                          step="0.01"
                        />
                        <span className="ml-2 text-gray-600">for the combo</span>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Step 3: Validity & Limits */}
            {step === 3 && (
              <div className="space-y-6">
                <div className="text-center mb-6">
                  <h3 className="text-xl font-semibold text-gray-800 mb-2">Set Validity & Limits</h3>
                  <p className="text-gray-600">Control when and how your coupon can be used</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Valid From
                    </label>
                    <input
                      type="date"
                      value={couponData.valid_from}
                      onChange={(e) => handleInputChange('valid_from', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Valid Until
                    </label>
                    <input
                      type="date"
                      value={couponData.valid_until}
                      onChange={(e) => handleInputChange('valid_until', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                    />
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Max Redemptions
                    </label>
                    <input
                      type="number"
                      value={couponData.max_redemptions}
                      onChange={(e) => handleInputChange('max_redemptions', parseInt(e.target.value) || null)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                      placeholder="Unlimited"
                      min="1"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Per Customer Limit
                    </label>
                    <input
                      type="number"
                      value={couponData.max_per_customer}
                      onChange={(e) => handleInputChange('max_per_customer', parseInt(e.target.value))}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                      min="1"
                    />
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Minimum Purchase ($)
                    </label>
                    <input
                      type="number"
                      value={couponData.minimum_purchase}
                      onChange={(e) => handleInputChange('minimum_purchase', parseFloat(e.target.value) || 0)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
                      min="0"
                      step="0.01"
                      placeholder="0 (no minimum)"
                    />
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Target Audience
                  </label>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                    {targetAudiences.map((audience) => (
                      <div
                        key={audience.id}
                        onClick={() => handleInputChange('target_audience', audience.id)}
                        className={`p-3 border-2 rounded-lg cursor-pointer text-center transition-all ${
                          couponData.target_audience === audience.id
                            ? 'border-orange-500 bg-orange-50'
                            : 'border-gray-200 hover:border-orange-300'
                        }`}
                      >
                        <div className="text-xl mb-1">{audience.icon}</div>
                        <div className="text-sm font-medium">{audience.name}</div>
                      </div>
                    ))}
                  </div>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-3">
                    Valid Days of Week
                  </label>
                  <div className="flex flex-wrap gap-2">
                    {daysOfWeek.map((day) => (
                      <button
                        key={day.id}
                        onClick={() => handleDayToggle(day.id)}
                        className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                          couponData.days_of_week.includes(day.id)
                            ? 'bg-orange-500 text-white'
                            : 'bg-gray-200 text-gray-700 hover:bg-gray-300'
                        }`}
                      >
                        {day.name}
                      </button>
                    ))}
                  </div>
                </div>
              </div>
            )}

            {/* Step 4: Review & Launch */}
            {step === 4 && (
              <div className="space-y-6">
                <div className="text-center mb-6">
                  <h3 className="text-xl font-semibold text-gray-800 mb-2">Review & Launch Your Coupon</h3>
                  <p className="text-gray-600">Everything looks good? Let's get customers excited!</p>
                </div>

                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Terms & Conditions (Optional)
                  </label>
                  <textarea
                    value={couponData.terms_conditions}
                    onChange={(e) => handleInputChange('terms_conditions', e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    rows={3}
                    placeholder="e.g., Cannot be combined with other offers. Dine-in only. Valid for new customers only..."
                    maxLength={1000}
                  ></textarea>
                </div>

                <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                  <h4 className="font-semibold text-green-800 mb-2 flex items-center">
                    <CheckCircleIcon className="w-5 h-5 mr-2" />
                    Ready to Launch!
                  </h4>
                  <p className="text-green-700 text-sm">
                    Your coupon will be immediately available to customers with a QR code for easy redemption. 
                    You'll get real-time analytics on views, saves, and redemptions.
                  </p>
                </div>
              </div>
            )}
          </div>

          {/* Preview Panel */}
          <div className="w-80 bg-gray-50 p-6 border-l overflow-y-auto flex-shrink-0">
            <h4 className="font-semibold text-gray-800 mb-4 flex items-center">
              <TagIcon className="w-5 h-5 mr-2" />
              Live Preview
            </h4>

            {/* Coupon Preview */}
            <div className="bg-white rounded-lg shadow-lg p-6 mb-6 border-2 border-dashed border-orange-300">
              <div className="text-center">
                <div className="text-3xl font-bold text-orange-500 mb-2">
                  {discount || 'YOUR DISCOUNT'}
                </div>
                <h3 className="text-lg font-semibold text-gray-800 mb-2">
                  {couponData.title || 'Your Coupon Title'}
                </h3>
                <p className="text-sm text-gray-600 mb-4">
                  {couponData.description || 'Your amazing offer description will appear here...'}
                </p>
                
                {couponData.promotional_message && (
                  <div className="bg-red-100 text-red-700 text-xs font-medium px-2 py-1 rounded-full mb-3">
                    {couponData.promotional_message}
                  </div>
                )}

                <div className="border-t border-gray-200 pt-3 mt-3">
                  <div className="flex items-center justify-center text-gray-500 text-xs">
                    <QrCodeIcon className="w-4 h-4 mr-1" />
                    QR Code will appear here
                  </div>
                </div>

                <div className="text-xs text-gray-500 mt-3">
                  Valid: {couponData.valid_from} to {couponData.valid_until}
                </div>
              </div>
            </div>

            {/* Quick Stats */}
            <div className="space-y-3">
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Restaurant:</span>
                <span className="font-medium">{restaurant.name}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Type:</span>
                <span className="font-medium">{selectedType?.name || 'Not selected'}</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Valid Days:</span>
                <span className="font-medium">{couponData.days_of_week.length} days</span>
              </div>
              <div className="flex justify-between text-sm">
                <span className="text-gray-600">Max Uses:</span>
                <span className="font-medium">{couponData.max_redemptions || 'Unlimited'}</span>
              </div>
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="border-t bg-gray-50 px-6 py-4 flex justify-between items-center">
          <div className="flex space-x-2">
            {step > 1 && (
              <button
                onClick={() => setStep(step - 1)}
                className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors"
              >
                Previous
              </button>
            )}
          </div>

          <div className="flex space-x-2">
            {step < 4 ? (
              <button
                onClick={() => setStep(step + 1)}
                disabled={!validateStep(step)}
                className="px-6 py-2 bg-orange-500 text-white rounded-lg hover:bg-orange-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                Next Step
              </button>
            ) : (
              <button
                onClick={handleSubmit}
                disabled={loading || !validateStep(step)}
                className="px-6 py-2 bg-green-500 text-white rounded-lg hover:bg-green-600 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center"
              >
                {loading ? (
                  <>
                    <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white mr-2"></div>
                    Creating...
                  </>
                ) : (
                  <>
                    <SparklesIcon className="w-4 h-4 mr-2" />
                    Launch Coupon!
                  </>
                )}
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default CouponCreator;