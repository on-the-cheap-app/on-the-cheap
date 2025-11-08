import React, { useState } from 'react';
import {
  MagnifyingGlassIcon,
  XMarkIcon,
  MapPinIcon,
  BuildingStorefrontIcon,
  CheckCircleIcon
} from '@heroicons/react/24/outline';

const RestaurantClaimModal = ({ onClose, token, onSuccess }) => {
  const [searchLocation, setSearchLocation] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [coordinates, setCoordinates] = useState(null);

  const backendUrl = process.env.REACT_APP_BACKEND_URL || '/api';

  const handleLocationSearch = async () => {
    if (!searchLocation.trim()) {
      setError('Please enter a location');
      return;
    }

    try {
      setLoading(true);
      setError('');
      
      // Geocode the location
      const geocodeResponse = await fetch(`${backendUrl}/geocode/forward`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ address: searchLocation })
      });

      if (!geocodeResponse.ok) {
        throw new Error('Location not found');
      }

      const geocodeData = await geocodeResponse.json();
      setCoordinates({
        latitude: geocodeData.latitude,
        longitude: geocodeData.longitude
      });

      // Search for restaurants
      await searchRestaurants(geocodeData.latitude, geocodeData.longitude);
    } catch (error) {
      console.error('Error searching location:', error);
      setError('Failed to find location. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const searchRestaurants = async (latitude, longitude) => {
    try {
      const params = new URLSearchParams({
        latitude: latitude.toString(),
        longitude: longitude.toString(),
        radius: '16094', // 10 miles
        limit: '50'
      });

      if (searchQuery.trim()) {
        params.append('query', searchQuery);
      }

      const response = await fetch(`${backendUrl}/restaurants/search?${params}`);

      if (!response.ok) {
        throw new Error('Failed to search restaurants');
      }

      const data = await response.json();
      setSearchResults(data.restaurants || []);

      if (data.restaurants.length === 0) {
        setError('No restaurants found. Try a different location or search term.');
      }
    } catch (error) {
      console.error('Error searching restaurants:', error);
      setError('Failed to search restaurants');
    }
  };

  const handleClaimRestaurant = async (restaurant) => {
    try {
      setLoading(true);
      setError('');
      setSuccess('');

      const response = await fetch(`${backendUrl}/owners/claims`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          restaurant_id: restaurant.id,
          restaurant_name: restaurant.name,
          restaurant_address: restaurant.address,
          proof_of_ownership: 'Pending verification'
        })
      });

      const data = await response.json();

      if (response.ok) {
        setSuccess(`Claim submitted for ${restaurant.name}! It will be reviewed by our team.`);
        setTimeout(() => {
          onSuccess();
          onClose();
        }, 2000);
      } else {
        setError(data.detail || 'Failed to submit claim');
      }
    } catch (error) {
      console.error('Error claiming restaurant:', error);
      setError('Network error. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-orange-500 to-red-500 text-white p-6 relative">
          <button
            onClick={onClose}
            className="absolute top-4 right-4 text-white hover:text-orange-200 transition-colors"
          >
            <XMarkIcon className="w-6 h-6" />
          </button>
          
          <h2 className="text-2xl font-bold">Claim Your Restaurant</h2>
          <p className="text-orange-100">Search for your restaurant and submit a claim</p>
        </div>

        {/* Search Section */}
        <div className="p-6 border-b bg-gray-50">
          <div className="space-y-4">
            <div className="flex gap-3">
              <input
                type="text"
                value={searchLocation}
                onChange={(e) => setSearchLocation(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleLocationSearch()}
                placeholder="Enter city or address (e.g., San Francisco, CA)"
                className="flex-1 px-4 py-3 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
              <button
                onClick={handleLocationSearch}
                disabled={loading}
                className="px-6 py-3 bg-orange-500 text-white rounded-lg hover:bg-orange-600 transition-colors disabled:opacity-50 flex items-center"
              >
                <MagnifyingGlassIcon className="w-5 h-5 mr-2" />
                Search Location
              </button>
            </div>

            {coordinates && (
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && searchRestaurants(coordinates.latitude, coordinates.longitude)}
                placeholder="Filter by restaurant name..."
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-orange-500"
              />
            )}
          </div>

          {error && (
            <div className="mt-4 p-4 bg-red-50 border border-red-200 text-red-700 rounded-lg">
              {error}
            </div>
          )}

          {success && (
            <div className="mt-4 p-4 bg-green-50 border border-green-200 text-green-700 rounded-lg flex items-center">
              <CheckCircleIcon className="w-5 h-5 mr-2" />
              {success}
            </div>
          )}
        </div>

        {/* Results Section */}
        <div className="p-6 overflow-y-auto max-h-[50vh]">
          {loading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-orange-500 mx-auto mb-4"></div>
              <p className="text-gray-600">Searching restaurants...</p>
            </div>
          ) : searchResults.length > 0 ? (
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800 mb-4">
                Found {searchResults.length} restaurant{searchResults.length !== 1 ? 's' : ''}
              </h3>
              <div className="grid grid-cols-1 gap-4">
                {searchResults.map((restaurant) => (
                  <div
                    key={restaurant.id}
                    className="bg-white border rounded-lg p-4 hover:shadow-md transition-shadow"
                  >
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-start">
                          {restaurant.photos && restaurant.photos.length > 0 && (
                            <img
                              src={restaurant.photos[0].url}
                              alt={restaurant.name}
                              className="w-20 h-20 rounded-lg object-cover mr-4"
                            />
                          )}
                          <div>
                            <h4 className="font-semibold text-gray-800 mb-1">{restaurant.name}</h4>
                            <p className="text-sm text-gray-600 flex items-center mb-2">
                              <MapPinIcon className="w-4 h-4 mr-1" />
                              {restaurant.address}
                            </p>
                            {restaurant.cuisine_type && restaurant.cuisine_type.length > 0 && (
                              <div className="flex flex-wrap gap-1">
                                {restaurant.cuisine_type.slice(0, 3).map((cuisine, index) => (
                                  <span
                                    key={index}
                                    className="px-2 py-1 bg-gray-100 text-gray-600 text-xs rounded"
                                  >
                                    {cuisine}
                                  </span>
                                ))}
                              </div>
                            )}
                            {restaurant.source && (
                              <p className="text-xs text-gray-500 mt-2">
                                Source: {restaurant.source === 'owner_managed' ? 'Owner Managed' : restaurant.source === 'google_places' ? 'Google Places' : 'Foursquare'}
                              </p>
                            )}
                          </div>
                        </div>
                      </div>
                      <button
                        onClick={() => handleClaimRestaurant(restaurant)}
                        disabled={loading || restaurant.source === 'owner_managed'}
                        className={`ml-4 px-4 py-2 rounded-lg transition-colors flex items-center ${
                          restaurant.source === 'owner_managed'
                            ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                            : 'bg-orange-500 text-white hover:bg-orange-600'
                        }`}
                      >
                        <BuildingStorefrontIcon className="w-4 h-4 mr-1" />
                        {restaurant.source === 'owner_managed' ? 'Already Claimed' : 'Claim'}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          ) : coordinates ? (
            <div className="text-center py-8 text-gray-500">
              <BuildingStorefrontIcon className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p>No restaurants found in this area.</p>
              <p className="text-sm mt-2">Try a different location or search term.</p>
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <MagnifyingGlassIcon className="w-16 h-16 mx-auto mb-4 text-gray-300" />
              <p>Search for your restaurant location to get started</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default RestaurantClaimModal;
