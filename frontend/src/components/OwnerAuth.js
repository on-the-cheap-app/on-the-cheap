import React, { useState } from 'react';
import { BuildingStorefrontIcon, EyeIcon, EyeSlashIcon } from '@heroicons/react/24/outline';

const OwnerAuth = ({ onClose, onAuthSuccess }) => {
  const [isLogin, setIsLogin] = useState(true);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  
  const [formData, setFormData] = useState({
    // Login fields
    email: '',
    password: '',
    // Registration fields
    first_name: '',
    last_name: '',
    phone: '',
    business_name: '',
    business_type: 'restaurant'
  });

  const backendUrl = process.env.REACT_APP_BACKEND_URL || '/api';

  // Debug logging
  console.log('🔍 OwnerAuth Debug - backendUrl:', backendUrl);
  console.log('🔍 OwnerAuth Debug - process.env.REACT_APP_BACKEND_URL:', process.env.REACT_APP_BACKEND_URL);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const endpoint = isLogin ? '/owners/login' : '/owners/register';
      const payload = isLogin 
        ? { email: formData.email, password: formData.password }
        : formData;

      console.log('🔍 Debug - Submitting to:', `${backendUrl}${endpoint}`);
      console.log('🔍 Debug - Payload:', payload);
      console.log('🔍 Debug - Is Login:', isLogin);

      const response = await fetch(`${backendUrl}${endpoint}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      console.log('🔍 Debug - Response status:', response.status);
      console.log('🔍 Debug - Response ok:', response.ok);

      const data = await response.json();
      console.log('🔍 Debug - Response data:', data);

      if (response.ok) {
        if (isLogin) {
          // Login successful
          console.log('🔍 Debug - Calling onAuthSuccess with:', data.owner || data.user, data.access_token);
          onAuthSuccess(data.owner || data.user, data.access_token, 'owner');
        } else {
          // Registration successful - automatically login
          setError('');
          setIsLogin(true);
          setFormData({
            ...formData,
            first_name: '',
            last_name: '',
            phone: '',
            business_name: '',
            business_type: 'restaurant'
          });
          alert('Registration successful! Please log in with your credentials.');
        }
      } else {
        console.log('🔍 Debug - Error response:', data);
        setError(data.detail || 'Authentication failed');
      }
    } catch (error) {
      console.error('🔍 Debug - Auth error:', error);
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleInputChange = (e) => {
    setFormData({
      ...formData,
      [e.target.name]: e.target.value
    });
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-md w-full max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="bg-gradient-to-r from-orange-500 to-red-500 text-white p-6 flex justify-between items-center">
          <div className="flex items-center">
            <BuildingStorefrontIcon className="w-8 h-8 mr-3" />
            <div>
              <h2 className="text-xl font-bold">
                {isLogin ? 'Owner Login' : 'Owner Registration'}
              </h2>
              <p className="text-orange-100 text-sm">
                {isLogin ? 'Access your restaurant dashboard' : 'Join as a restaurant owner'}
              </p>
            </div>
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

        <div className="p-6">
          {error && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded mb-4">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Registration-only fields */}
            {!isLogin && (
              <>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="first_name" className="block text-sm font-medium text-gray-700 mb-1">
                      First Name *
                    </label>
                    <input
                      type="text"
                      id="first_name"
                      name="first_name"
                      value={formData.first_name}
                      onChange={handleInputChange}
                      required={!isLogin}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                      placeholder="John"
                    />
                  </div>
                  <div>
                    <label htmlFor="last_name" className="block text-sm font-medium text-gray-700 mb-1">
                      Last Name *
                    </label>
                    <input
                      type="text"
                      id="last_name"
                      name="last_name"
                      value={formData.last_name}
                      onChange={handleInputChange}
                      required={!isLogin}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                      placeholder="Smith"
                    />
                  </div>
                </div>

                <div>
                  <label htmlFor="business_name" className="block text-sm font-medium text-gray-700 mb-1">
                    Business Name
                  </label>
                  <input
                    type="text"
                    id="business_name"
                    name="business_name"
                    value={formData.business_name}
                    onChange={handleInputChange}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    placeholder="Smith's Bistro"
                  />
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label htmlFor="phone" className="block text-sm font-medium text-gray-700 mb-1">
                      Phone Number *
                    </label>
                    <input
                      type="tel"
                      id="phone"
                      name="phone"
                      value={formData.phone}
                      onChange={handleInputChange}
                      required={!isLogin}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                      placeholder="+1-555-0123"
                    />
                  </div>
                  <div>
                    <label htmlFor="business_type" className="block text-sm font-medium text-gray-700 mb-1">
                      Business Type
                    </label>
                    <select
                      id="business_type"
                      name="business_type"
                      value={formData.business_type}
                      onChange={handleInputChange}
                      className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                    >
                      <option value="restaurant">Restaurant</option>
                      <option value="bar">Bar</option>
                      <option value="cafe">Cafe</option>
                      <option value="food_truck">Food Truck</option>
                      <option value="bakery">Bakery</option>
                      <option value="other">Other</option>
                    </select>
                  </div>
                </div>
              </>
            )}

            {/* Common fields */}
            <div>
              <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-1">
                Email Address *
              </label>
              <input
                type="email"
                id="email"
                name="email"
                value={formData.email}
                onChange={handleInputChange}
                required
                className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                placeholder="owner@restaurant.com"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-1">
                Password *
              </label>
              <div className="relative">
                <input
                  type={showPassword ? 'text' : 'password'}
                  id="password"
                  name="password"
                  value={formData.password}
                  onChange={handleInputChange}
                  required
                  minLength={8}
                  className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-orange-500 focus:border-transparent"
                  placeholder={isLogin ? 'Enter your password' : 'At least 8 characters'}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute inset-y-0 right-0 pr-3 flex items-center text-gray-400 hover:text-gray-600"
                >
                  {showPassword ? (
                    <EyeSlashIcon className="w-5 h-5" />
                  ) : (
                    <EyeIcon className="w-5 h-5" />
                  )}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-orange-500 text-white py-2 px-4 rounded-md hover:bg-orange-600 focus:outline-none focus:ring-2 focus:ring-orange-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              {loading ? (
                <div className="flex items-center justify-center">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2"></div>
                  {isLogin ? 'Signing In...' : 'Creating Account...'}
                </div>
              ) : (
                isLogin ? 'Sign In' : 'Create Account'
              )}
            </button>
          </form>

          {/* Toggle between login and registration */}
          <div className="mt-6 text-center">
            <p className="text-gray-600">
              {isLogin ? "Don't have an owner account?" : "Already have an account?"}
            </p>
            <button
              onClick={() => {
                setIsLogin(!isLogin);
                setError('');
                setFormData({
                  email: '',
                  password: '',
                  first_name: '',
                  last_name: '',
                  phone: '',
                  business_name: '',
                  business_type: 'restaurant'
                });
              }}
              className="text-orange-500 hover:text-orange-600 font-medium mt-1 transition-colors"
            >
              {isLogin ? 'Register as Owner' : 'Sign In Instead'}
            </button>
          </div>

          {/* Info section */}
          <div className="mt-6 p-4 bg-orange-50 border border-orange-200 rounded-lg">
            <h4 className="font-medium text-orange-800 mb-2">Owner Account Benefits:</h4>
            <ul className="text-sm text-orange-700 space-y-1">
              <li>• Claim your restaurant listings</li>
              <li>• Create and manage daily specials</li>
              <li>• Track customer engagement</li>
              <li>• Boost visibility with verified badge</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};

export default OwnerAuth;