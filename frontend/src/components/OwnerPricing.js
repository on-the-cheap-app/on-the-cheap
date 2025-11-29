import React, { useEffect, useState } from 'react';
import axios from 'axios';

const API = (process.env.REACT_APP_BACKEND_URL || '') + '/api';

const OwnerPricing = () => {
  const [currentTier, setCurrentTier] = useState('free');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSubscriptionStatus();
    
    // Load Stripe pricing table script
    const script = document.createElement('script');
    script.src = 'https://js.stripe.com/v3/pricing-table.js';
    script.async = true;
    document.body.appendChild(script);

    return () => {
      // Cleanup script on unmount
      if (document.body.contains(script)) {
        document.body.removeChild(script);
      }
    };
  }, []);

  const loadSubscriptionStatus = async () => {
    try {
      const token = localStorage.getItem('owner_token');
      if (!token) return;

      const response = await axios.get(`${API}/owners/subscription/status`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      
      setCurrentTier(response.data.tier);
    } catch (error) {
      console.error('Error loading subscription status:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="w-full px-4 sm:px-6">{/* Added padding back for better spacing */}
      {/* Header */}
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          Choose Your Plan
        </h1>
        <p className="text-xl text-gray-600 mb-2">
          Grow your restaurant with the right tools
        </p>
        {currentTier !== 'free' && (
          <div className="inline-block bg-orange-100 text-orange-800 px-4 py-2 rounded-full text-sm font-medium">
            Current Plan: {currentTier.toUpperCase()}
          </div>
        )}
      </div>

      {/* Feature Comparison Table */}
      <div className="mb-12 bg-white rounded-lg shadow-lg overflow-hidden">
        <div className="px-6 py-4 bg-orange-500 text-white">
          <h2 className="text-2xl font-bold">Compare Features</h2>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="bg-gray-50">
                <th className="px-6 py-3 text-left text-sm font-semibold text-gray-900">Feature</th>
                <th className="px-6 py-3 text-center text-sm font-semibold text-gray-900">
                  <div>Starter</div>
                  <div className="text-orange-600 font-bold">FREE</div>
                </th>
                <th className="px-6 py-3 text-center text-sm font-semibold text-gray-900">
                  <div>Pro</div>
                  <div className="text-orange-600 font-bold">$99/mo</div>
                </th>
                <th className="px-6 py-3 text-center text-sm font-semibold text-gray-900">
                  <div>Enterprise</div>
                  <div className="text-orange-600 font-bold">$299/mo</div>
                </th>
              </tr>
            </thead>
            <tbody className="divide-y divide-gray-200">
              <tr>
                <td className="px-6 py-4 text-sm text-gray-900">Restaurant Locations</td>
                <td className="px-6 py-4 text-center text-sm">1</td>
                <td className="px-6 py-4 text-center text-sm">Up to 3</td>
                <td className="px-6 py-4 text-center text-sm">Unlimited</td>
              </tr>
              <tr className="bg-gray-50">
                <td className="px-6 py-4 text-sm text-gray-900">Daily Specials per Month</td>
                <td className="px-6 py-4 text-center text-sm">5</td>
                <td className="px-6 py-4 text-center text-sm">Unlimited</td>
                <td className="px-6 py-4 text-center text-sm">Unlimited</td>
              </tr>
              <tr>
                <td className="px-6 py-4 text-sm text-gray-900">Digital Coupons</td>
                <td className="px-6 py-4 text-center text-sm">❌</td>
                <td className="px-6 py-4 text-center text-sm">✅</td>
                <td className="px-6 py-4 text-center text-sm">✅</td>
              </tr>
              <tr className="bg-gray-50">
                <td className="px-6 py-4 text-sm text-gray-900">Analytics Dashboard</td>
                <td className="px-6 py-4 text-center text-sm">❌</td>
                <td className="px-6 py-4 text-center text-sm">✅ Basic</td>
                <td className="px-6 py-4 text-center text-sm">✅ Advanced</td>
              </tr>
              <tr>
                <td className="px-6 py-4 text-sm text-gray-900">Priority Listing</td>
                <td className="px-6 py-4 text-center text-sm">❌</td>
                <td className="px-6 py-4 text-center text-sm">✅</td>
                <td className="px-6 py-4 text-center text-sm">✅</td>
              </tr>
              <tr className="bg-gray-50">
                <td className="px-6 py-4 text-sm text-gray-900">AI-Driven Upselling</td>
                <td className="px-6 py-4 text-center text-sm">❌</td>
                <td className="px-6 py-4 text-center text-sm">❌</td>
                <td className="px-6 py-4 text-center text-sm">✅</td>
              </tr>
              <tr>
                <td className="px-6 py-4 text-sm text-gray-900">Dynamic Pricing</td>
                <td className="px-6 py-4 text-center text-sm">❌</td>
                <td className="px-6 py-4 text-center text-sm">❌</td>
                <td className="px-6 py-4 text-center text-sm">✅</td>
              </tr>
              <tr className="bg-gray-50">
                <td className="px-6 py-4 text-sm text-gray-900">POS Integration</td>
                <td className="px-6 py-4 text-center text-sm">❌</td>
                <td className="px-6 py-4 text-center text-sm">❌</td>
                <td className="px-6 py-4 text-center text-sm">✅</td>
              </tr>
              <tr>
                <td className="px-6 py-4 text-sm text-gray-900">API Access</td>
                <td className="px-6 py-4 text-center text-sm">❌</td>
                <td className="px-6 py-4 text-center text-sm">❌</td>
                <td className="px-6 py-4 text-center text-sm">✅</td>
              </tr>
              <tr className="bg-gray-50">
                <td className="px-6 py-4 text-sm text-gray-900">Support</td>
                <td className="px-6 py-4 text-center text-sm">Email</td>
                <td className="px-6 py-4 text-center text-sm">Email</td>
                <td className="px-6 py-4 text-center text-sm">Dedicated Manager</td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

      {/* Stripe Pricing Table */}
      <div className="bg-white rounded-lg shadow-lg p-6 mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6 text-center">
          Start Your Free Trial Today
        </h2>
        <p className="text-center text-gray-600 mb-8">
          14-day free trial on all paid plans. No credit card required until trial ends.
        </p>
        
        {/* Embedded Stripe Pricing Table */}
        <div className="stripe-pricing-table-container">
          <stripe-pricing-table 
            pricing-table-id="prctbl_1SYBXi047XGR3G7TsMDvxF4N"
            publishable-key="pk_live_51SYAoi047XGR3G7TJMKQbnegkq4TOVz92pt3BcDd7KpKvLySHuOeLkeClGiXQm6jOCvScFMDP6BGTG9yxc4kZjpf00kiQsm6gg">
          </stripe-pricing-table>
        </div>
      </div>

      {/* Benefits Section */}
      <div className="grid md:grid-cols-3 gap-6 mb-12">
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-orange-500 text-3xl mb-4">🎯</div>
          <h3 className="font-bold text-lg mb-2">Increase Foot Traffic</h3>
          <p className="text-gray-600 text-sm">
            Fill seats during off-peak hours with targeted specials and promotions.
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-orange-500 text-3xl mb-4">📊</div>
          <h3 className="font-bold text-lg mb-2">Data-Driven Insights</h3>
          <p className="text-gray-600 text-sm">
            Understand customer behavior and optimize your marketing strategy.
          </p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <div className="text-orange-500 text-3xl mb-4">💰</div>
          <h3 className="font-bold text-lg mb-2">Maximize Revenue</h3>
          <p className="text-gray-600 text-sm">
            AI-powered recommendations help you price dynamically and upsell effectively.
          </p>
        </div>
      </div>

      {/* FAQ Section */}
      <div className="bg-white rounded-lg shadow-lg p-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-6">Frequently Asked Questions</h2>
        <div className="space-y-4">
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">How does the 14-day free trial work?</h3>
            <p className="text-gray-600 text-sm">
              Start using Pro or Enterprise features immediately. You won't be charged until after 14 days. 
              Cancel anytime during the trial with no charges.
            </p>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Can I upgrade or downgrade my plan?</h3>
            <p className="text-gray-600 text-sm">
              Yes! You can upgrade anytime (prorated charge). Downgrades take effect at the end of your billing period.
            </p>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">What payment methods do you accept?</h3>
            <p className="text-gray-600 text-sm">
              We accept all major credit cards (Visa, Mastercard, American Express) and PayPal.
            </p>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">Is there a setup fee?</h3>
            <p className="text-gray-600 text-sm">
              No setup fees, no hidden charges. Pay only the monthly or annual subscription.
            </p>
          </div>
          <div>
            <h3 className="font-semibold text-gray-900 mb-2">What happens if I cancel?</h3>
            <p className="text-gray-600 text-sm">
              You keep access until the end of your billing period, then automatically downgrade to the free Starter plan.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OwnerPricing;
