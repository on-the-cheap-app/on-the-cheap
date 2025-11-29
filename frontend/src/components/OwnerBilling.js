import React, { useEffect, useState } from 'react';
import axios from 'axios';

const API = (process.env.REACT_APP_BACKEND_URL || '') + '/api';

const OwnerBilling = () => {
  const [subscription, setSubscription] = useState(null);
  const [loading, setLoading] = useState(true);
  const [canceling, setCanceling] = useState(false);

  useEffect(() => {
    loadSubscriptionStatus();
    
    // Check for successful checkout session
    const sessionId = searchParams.get('session_id');
    if (sessionId) {
      checkCheckoutStatus(sessionId);
    }
  }, [searchParams]);

  const loadSubscriptionStatus = async () => {
    try {
      const token = localStorage.getItem('owner_token');
      if (!token) {
        navigate('/owner');
        return;
      }

      const response = await axios.get(`${API}/owners/subscription/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setSubscription(response.data);
    } catch (error) {
      console.error('Error loading subscription:', error);
      if (error.response?.status === 401) {
        navigate('/owner');
      }
    } finally {
      setLoading(false);
    }
  };

  const checkCheckoutStatus = async (sessionId) => {
    try {
      const token = localStorage.getItem('owner_token');
      const response = await axios.get(
        `${API}/owners/subscription/checkout/${sessionId}/status`,
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      if (response.data.payment_status === 'paid') {
        // Show success message
        alert('🎉 Subscription activated! Your trial has started.');
        // Reload subscription status
        await loadSubscriptionStatus();
        // Remove session_id from URL
        navigate('/owner/billing', { replace: true });
      }
    } catch (error) {
      console.error('Error checking checkout status:', error);
    }
  };

  const handleCancelSubscription = async (immediate = false) => {
    const confirmMessage = immediate
      ? 'Are you sure you want to cancel immediately? You will lose access to paid features right away and be downgraded to the free plan.'
      : 'Are you sure you want to cancel? You will keep access until the end of your billing period.';
    
    if (!window.confirm(confirmMessage)) {
      return;
    }

    setCanceling(true);
    try {
      const token = localStorage.getItem('owner_token');
      const response = await axios.post(
        `${API}/owners/subscription/cancel?immediate=${immediate}`,
        {},
        { headers: { Authorization: `Bearer ${token}` } }
      );
      
      alert(response.data.message);
      await loadSubscriptionStatus();
    } catch (error) {
      console.error('Error canceling subscription:', error);
      alert('Failed to cancel subscription. Please try again or contact support.');
    } finally {
      setCanceling(false);
    }
  };

  const handleUpgrade = () => {
    navigate('/owner/pricing');
  };

  if (loading) {
    return (
      <div className="flex justify-center items-center min-h-screen">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500"></div>
      </div>
    );
  }

  if (!subscription) {
    return (
      <div className="max-w-4xl mx-auto px-4 py-8">
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6 text-center">
          <p className="text-yellow-800">Unable to load subscription information.</p>
        </div>
      </div>
    );
  }

  const { tier, status, billing_period, limits, usage, trial_ends_at, period_end, cancel_at_period_end } = subscription;

  const getTierBadgeColor = (tier) => {
    switch (tier) {
      case 'free': return 'bg-gray-100 text-gray-800';
      case 'pro': return 'bg-blue-100 text-blue-800';
      case 'enterprise': return 'bg-purple-100 text-purple-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusBadgeColor = (status) => {
    switch (status) {
      case 'active': return 'bg-green-100 text-green-800';
      case 'trialing': return 'bg-orange-100 text-orange-800';
      case 'past_due': return 'bg-red-100 text-red-800';
      case 'canceled': return 'bg-gray-100 text-gray-800';
      default: return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="max-w-6xl mx-auto px-4 py-8">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">Billing & Subscription</h1>
        <p className="text-gray-600">Manage your subscription and view usage</p>
      </div>

      {/* Trial Banner */}
      {status === 'trialing' && trial_ends_at && (
        <div className="mb-6 bg-orange-50 border border-orange-200 rounded-lg p-4">
          <div className="flex items-center">
            <span className="text-2xl mr-3">🎉</span>
            <div>
              <p className="font-semibold text-orange-900">Free Trial Active</p>
              <p className="text-sm text-orange-700">
                Your trial ends on {new Date(trial_ends_at).toLocaleDateString()}. 
                You won't be charged until then.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Cancellation Notice */}
      {cancel_at_period_end && (
        <div className="mb-6 bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex items-center">
            <span className="text-2xl mr-3">⚠️</span>
            <div>
              <p className="font-semibold text-yellow-900">Subscription Canceling</p>
              <p className="text-sm text-yellow-700">
                Your subscription will end on {period_end ? new Date(period_end).toLocaleDateString() : 'N/A'}. 
                You'll be downgraded to the free plan.
              </p>
            </div>
          </div>
        </div>
      )}

      <div className="grid md:grid-cols-2 gap-6 mb-8">
        {/* Current Plan Card */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Current Plan</h2>
          
          <div className="space-y-3">
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Tier:</span>
              <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getTierBadgeColor(tier)}`}>
                {tier.toUpperCase()}
              </span>
            </div>
            
            <div className="flex justify-between items-center">
              <span className="text-gray-600">Status:</span>
              <span className={`px-3 py-1 rounded-full text-sm font-semibold ${getStatusBadgeColor(status)}`}>
                {status.toUpperCase()}
              </span>
            </div>
            
            {billing_period && (
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Billing:</span>
                <span className="font-semibold text-gray-900">{billing_period}</span>
              </div>
            )}
            
            {period_end && (
              <div className="flex justify-between items-center">
                <span className="text-gray-600">Next billing date:</span>
                <span className="font-semibold text-gray-900">
                  {new Date(period_end).toLocaleDateString()}
                </span>
              </div>
            )}
          </div>

          {tier !== 'enterprise' && (
            <button
              onClick={handleUpgrade}
              className="mt-6 w-full bg-orange-500 text-white py-2 px-4 rounded-lg hover:bg-orange-600 font-semibold transition"
            >
              {tier === 'free' ? 'Upgrade to Pro' : 'Upgrade to Enterprise'}
            </button>
          )}
        </div>

        {/* Usage Card */}
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Current Usage</h2>
          
          <div className="space-y-4">
            {/* Locations */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-gray-600">Restaurant Locations</span>
                <span className="font-semibold text-gray-900">
                  {usage.locations} / {limits.max_locations === -1 ? '∞' : limits.max_locations}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-orange-500 h-2 rounded-full"
                  style={{
                    width: limits.max_locations === -1 
                      ? '0%' 
                      : `${Math.min((usage.locations / limits.max_locations) * 100, 100)}%`
                  }}
                ></div>
              </div>
            </div>

            {/* Specials */}
            <div>
              <div className="flex justify-between items-center mb-2">
                <span className="text-gray-600">Specials This Month</span>
                <span className="font-semibold text-gray-900">
                  {usage.specials_this_month} / {limits.max_specials_per_month === -1 ? '∞' : limits.max_specials_per_month}
                </span>
              </div>
              <div className="w-full bg-gray-200 rounded-full h-2">
                <div
                  className="bg-orange-500 h-2 rounded-full"
                  style={{
                    width: limits.max_specials_per_month === -1 
                      ? '0%' 
                      : `${Math.min((usage.specials_this_month / limits.max_specials_per_month) * 100, 100)}%`
                  }}
                ></div>
              </div>
              {tier === 'free' && usage.specials_this_month >= limits.max_specials_per_month && (
                <p className="text-sm text-red-600 mt-2">
                  ⚠️ Limit reached! Upgrade to Pro for unlimited specials.
                </p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Features Card */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
        <h2 className="text-xl font-bold text-gray-900 mb-4">Your Features</h2>
        
        <div className="grid md:grid-cols-2 gap-4">
          <div className="flex items-center">
            <span className="mr-3">{limits.analytics_enabled ? '✅' : '❌'}</span>
            <span className="text-gray-700">Analytics Dashboard</span>
          </div>
          <div className="flex items-center">
            <span className="mr-3">{limits.digital_coupons ? '✅' : '❌'}</span>
            <span className="text-gray-700">Digital Coupons</span>
          </div>
          <div className="flex items-center">
            <span className="mr-3">{limits.priority_listing ? '✅' : '❌'}</span>
            <span className="text-gray-700">Priority Listing</span>
          </div>
          <div className="flex items-center">
            <span className="mr-3">{limits.ai_features_enabled ? '✅' : '❌'}</span>
            <span className="text-gray-700">AI Features</span>
          </div>
          <div className="flex items-center">
            <span className="mr-3">{limits.api_access ? '✅' : '❌'}</span>
            <span className="text-gray-700">API Access</span>
          </div>
          <div className="flex items-center">
            <span className="mr-3">{limits.dedicated_support ? '✅' : '❌'}</span>
            <span className="text-gray-700">Dedicated Support</span>
          </div>
        </div>
      </div>

      {/* Actions */}
      {tier !== 'free' && status !== 'canceled' && !cancel_at_period_end && (
        <div className="bg-white rounded-lg shadow-lg p-6">
          <h2 className="text-xl font-bold text-gray-900 mb-4">Manage Subscription</h2>
          
          <div className="space-y-3">
            <button
              onClick={() => handleCancelSubscription(false)}
              disabled={canceling}
              className="w-full md:w-auto px-6 py-2 border border-red-300 text-red-700 rounded-lg hover:bg-red-50 transition disabled:opacity-50"
            >
              {canceling ? 'Processing...' : 'Cancel Subscription (End of Period)'}
            </button>
            
            <button
              onClick={() => handleCancelSubscription(true)}
              disabled={canceling}
              className="w-full md:w-auto px-6 py-2 border border-red-500 text-red-700 rounded-lg hover:bg-red-50 transition disabled:opacity-50 ml-0 md:ml-3"
            >
              {canceling ? 'Processing...' : 'Cancel Immediately'}
            </button>
          </div>
          
          <p className="text-sm text-gray-500 mt-4">
            Need help? Contact our support team at support@onthecheapapp.com
          </p>
        </div>
      )}
    </div>
  );
};

export default OwnerBilling;
