import React, { useState } from 'react';
import AddressInput from './AddressInput';
import LocationDisplay from './LocationDisplay';
import useGeocoding from '../hooks/useGeocoding';

const GeocodingDemo = ({ className = "" }) => {
  const [selectedLocation, setSelectedLocation] = useState(null);
  const [reverseResults, setReverseResults] = useState([]);
  const [batchAddresses, setBatchAddresses] = useState(['']);
  const [batchResults, setBatchResults] = useState(null);
  const [coordinates, setCoordinates] = useState({ lat: '', lng: '' });
  const [activeTab, setActiveTab] = useState('forward');

  const { reverseGeocode, batchGeocode, loading, error } = useGeocoding();

  const handleAddressSelect = (geocodeResult) => {
    setSelectedLocation(geocodeResult);
    setReverseResults([]);
  };

  const handleReverseGeocode = async () => {
    if (!coordinates.lat || !coordinates.lng) return;
    
    try {
      const results = await reverseGeocode(
        parseFloat(coordinates.lat), 
        parseFloat(coordinates.lng)
      );
      setReverseResults(results);
    } catch (err) {
      console.error('Reverse geocoding failed:', err);
    }
  };

  const handleBatchGeocode = async () => {
    const validAddresses = batchAddresses.filter(addr => addr.trim().length > 0);
    if (validAddresses.length === 0) return;

    try {
      const results = await batchGeocode(validAddresses);
      setBatchResults(results);
    } catch (err) {
      console.error('Batch geocoding failed:', err);
    }
  };

  const addBatchAddress = () => {
    if (batchAddresses.length < 10) {
      setBatchAddresses([...batchAddresses, '']);
    }
  };

  const updateBatchAddress = (index, value) => {
    const newAddresses = [...batchAddresses];
    newAddresses[index] = value;
    setBatchAddresses(newAddresses);
  };

  const removeBatchAddress = (index) => {
    if (batchAddresses.length > 1) {
      setBatchAddresses(batchAddresses.filter((_, i) => i !== index));
    }
  };

  const getCurrentLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (position) => {
          setCoordinates({
            lat: position.coords.latitude.toString(),
            lng: position.coords.longitude.toString()
          });
        },
        (error) => {
          console.error('Error getting location:', error);
        }
      );
    }
  };

  const tabs = [
    { id: 'forward', label: 'Forward Geocoding', icon: '🔍' },
    { id: 'reverse', label: 'Reverse Geocoding', icon: '📍' },
    { id: 'batch', label: 'Batch Geocoding', icon: '📋' }
  ];

  return (
    <div className={`bg-white rounded-lg shadow-lg p-6 ${className}`}>
      <h2 className="text-2xl font-bold text-gray-900 mb-4">
        🌍 Google Geocoding API Demo
      </h2>

      {/* Tab Navigation */}
      <div className="flex space-x-1 mb-6">
        {tabs.map(tab => (
          <button
            key={tab.id}
            onClick={() => setActiveTab(tab.id)}
            className={`px-4 py-2 rounded-md text-sm font-medium transition-colors ${
              activeTab === tab.id
                ? 'bg-blue-500 text-white'
                : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
            }`}
          >
            {tab.icon} {tab.label}
          </button>
        ))}
      </div>

      {/* Forward Geocoding Tab */}
      {activeTab === 'forward' && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Enter an address to convert to coordinates:
            </label>
            <AddressInput
              onAddressSelect={handleAddressSelect}
              placeholder="Try: 1600 Amphitheatre Parkway, Mountain View, CA"
              className="w-full"
              region="US"
            />
          </div>

          {selectedLocation && (
            <LocationDisplay
              geocodeResult={selectedLocation}
              showCoordinates={true}
              showComponents={true}
              className="mt-4"
            />
          )}
        </div>
      )}

      {/* Reverse Geocoding Tab */}
      {activeTab === 'reverse' && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Enter coordinates to convert to addresses:
            </label>
            <div className="flex space-x-2">
              <input
                type="number"
                step="any"
                placeholder="Latitude"
                value={coordinates.lat}
                onChange={(e) => setCoordinates({...coordinates, lat: e.target.value})}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <input
                type="number"
                step="any"
                placeholder="Longitude"
                value={coordinates.lng}
                onChange={(e) => setCoordinates({...coordinates, lng: e.target.value})}
                className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
              <button
                onClick={getCurrentLocation}
                className="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 transition-colors"
                title="Use current location"
              >
                📱
              </button>
              <button
                onClick={handleReverseGeocode}
                disabled={loading || !coordinates.lat || !coordinates.lng}
                className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:bg-gray-300 transition-colors"
              >
                {loading ? '⏳' : '🔍'} Geocode
              </button>
            </div>
          </div>

          {reverseResults.length > 0 && (
            <div className="space-y-2">
              <h3 className="text-lg font-semibold text-gray-900">
                Found {reverseResults.length} address(es):
              </h3>
              {reverseResults.map((result, index) => (
                <LocationDisplay
                  key={index}
                  geocodeResult={result}
                  showCoordinates={false}
                  compact={true}
                  className="border p-2 rounded"
                />
              ))}
            </div>
          )}
        </div>
      )}

      {/* Batch Geocoding Tab */}
      {activeTab === 'batch' && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Enter multiple addresses (up to 10):
            </label>
            <div className="space-y-2">
              {batchAddresses.map((address, index) => (
                <div key={index} className="flex space-x-2">
                  <input
                    type="text"
                    placeholder={`Address ${index + 1}`}
                    value={address}
                    onChange={(e) => updateBatchAddress(index, e.target.value)}
                    className="flex-1 px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                  {batchAddresses.length > 1 && (
                    <button
                      onClick={() => removeBatchAddress(index)}
                      className="px-3 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors"
                    >
                      ✕
                    </button>
                  )}
                </div>
              ))}
            </div>
            <div className="flex space-x-2 mt-2">
              <button
                onClick={addBatchAddress}
                disabled={batchAddresses.length >= 10}
                className="px-4 py-2 bg-green-500 text-white rounded-md hover:bg-green-600 disabled:bg-gray-300 transition-colors"
              >
                ➕ Add Address
              </button>
              <button
                onClick={handleBatchGeocode}
                disabled={loading || batchAddresses.every(addr => !addr.trim())}
                className="px-4 py-2 bg-blue-500 text-white rounded-md hover:bg-blue-600 disabled:bg-gray-300 transition-colors"
              >
                {loading ? '⏳' : '🔍'} Batch Geocode
              </button>
            </div>
          </div>

          {batchResults && (
            <div className="space-y-4">
              {batchResults.results.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-green-700">
                    ✅ Successful Results ({batchResults.results.length}):
                  </h3>
                  <div className="space-y-2 mt-2">
                    {batchResults.results.map((result, index) => (
                      <LocationDisplay
                        key={index}
                        geocodeResult={result}
                        compact={true}
                        className="border border-green-200 bg-green-50 p-2 rounded"
                      />
                    ))}
                  </div>
                </div>
              )}

              {batchResults.errors.length > 0 && (
                <div>
                  <h3 className="text-lg font-semibold text-red-700">
                    ❌ Errors ({batchResults.errors.length}):
                  </h3>
                  <div className="space-y-2 mt-2">
                    {batchResults.errors.map((error, index) => (
                      <div
                        key={index}
                        className="border border-red-200 bg-red-50 p-2 rounded text-red-700"
                      >
                        <strong>Address {parseInt(error.index) + 1}:</strong> {error.address}<br/>
                        <em>Error: {error.error}</em>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Global Error Display */}
      {error && (
        <div className="mt-4 p-3 bg-red-100 border border-red-400 text-red-700 rounded">
          <strong>Error:</strong> {error}
        </div>
      )}
    </div>
  );
};

export default GeocodingDemo;