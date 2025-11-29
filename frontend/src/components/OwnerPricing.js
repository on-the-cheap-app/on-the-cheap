import React, { useEffect, useState } from 'react';
import axios from 'axios';

const API = (process.env.REACT_APP_BACKEND_URL || '') + '/api';

const OwnerPricing = () => {
  const [currentTier, setCurrentTier] = useState('free');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadSubscriptionStatus();
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

  const handleSubscribe = async (plan) => {
    try {
      setLoading(true);
      const token = localStorage.getItem('owner_token');
      if (!token) {
        alert('Please log in to subscribe');
        return;
      }

      const response = await axios.post(
        `${API}/owners/subscription/create-checkout-session`,
        { tier: plan },
        { headers: { Authorization: `Bearer ${token}` } }
      );

      if (response.data.url) {
        // Redirect to Stripe Checkout
        window.location.href = response.data.url;
      }
    } catch (error) {
      console.error('Error creating checkout session:', error);
      alert('Failed to start subscription. Please try again.');
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
        
        {/* Custom Subscription Cards */}
        <div className="grid md:grid-cols-3 gap-8 max-w-6xl mx-auto">
          {/* Starter Plan - Free */}
          <div className="bg-white rounded-lg shadow-lg border-2 border-gray-200 p-8 flex flex-col">
            <h3 className="text-2xl font-bold text-gray-900 mb-2">Starter</h3>
            <div className="mb-4">
              <span className="text-4xl font-bold">$0</span>
              <span className="text-gray-600">/month</span>
            </div>
            <p className="text-gray-600 mb-6">Perfect for getting started</p>
            <ul className="mb-8 space-y-3 flex-grow">
              <li className="flex items-start">
                <svg className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                </svg>
                <span>1 restaurant location</span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                </svg>
                <span>Up to 5 specials per month</span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                </svg>
                <span>Basic analytics</span>
              </li>
            </ul>
            <button 
              disabled
              className="w-full py-3 px-6 rounded-lg bg-gray-200 text-gray-500 font-semibold cursor-not-allowed"
            >
              Current Plan
            </button>
          </div>

          {/* Pro Plan */}
          <div className="bg-white rounded-lg shadow-xl border-4 border-orange-500 p-8 flex flex-col relative transform scale-105">
            <div className="absolute -top-4 left-1/2 transform -translate-x-1/2 bg-orange-500 text-white px-4 py-1 rounded-full text-sm font-semibold">
              POPULAR
            </div>
            <h3 className="text-2xl font-bold text-gray-900 mb-2">Pro</h3>
            <div className="mb-4">
              <span className="text-4xl font-bold">$99</span>
              <span className="text-gray-600">/month</span>
            </div>
            <p className="text-gray-600 mb-6">For growing restaurants</p>
            <ul className="mb-8 space-y-3 flex-grow">
              <li className="flex items-start">
                <svg className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                </svg>
                <span>Up to 3 locations</span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                </svg>
                <span>Unlimited specials</span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                </svg>
                <span>Advanced analytics</span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                </svg>
                <span>Priority support</span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                </svg>
                <span>Digital coupons</span>
              </li>
            </ul>
            <button 
              onClick={() => handleSubscribe('pro')}
              className="w-full py-3 px-6 rounded-lg bg-orange-500 hover:bg-orange-600 text-white font-semibold transition-colors"
            >
              Start 14-Day Free Trial
            </button>
          </div>

          {/* Enterprise Plan */}
          <div className="bg-white rounded-lg shadow-lg border-2 border-gray-200 p-8 flex flex-col">
            <h3 className="text-2xl font-bold text-gray-900 mb-2">Enterprise</h3>
            <div className="mb-4">
              <span className="text-4xl font-bold">$299</span>
              <span className="text-gray-600">/month</span>
            </div>
            <p className="text-gray-600 mb-6">For restaurant chains</p>
            <ul className="mb-8 space-y-3 flex-grow">
              <li className="flex items-start">
                <svg className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                </svg>
                <span>Unlimited locations</span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                </svg>
                <span>Unlimited specials</span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                </svg>
                <span>White-label solution</span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                </svg>
                <span>Dedicated account manager</span>
              </li>
              <li className="flex items-start">
                <svg className="w-5 h-5 text-green-500 mr-2 flex-shrink-0 mt-0.5" fill="currentColor" viewBox="0 0 20 20">
                  <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                </svg>
                <span>Custom integrations</span>
              </li>
            </ul>
            <button 
              onClick={() => handleSubscribe('enterprise')}
              className="w-full py-3 px-6 rounded-lg bg-gray-900 hover:bg-gray-800 text-white font-semibold transition-colors"
            >
              Start 14-Day Free Trial
            </button>
          </div>
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
