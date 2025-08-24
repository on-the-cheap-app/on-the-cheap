import React, { useState } from 'react';
import useGeocoding from '../hooks/useGeocoding';

const LocationDisplay = ({ 
  geocodeResult, 
  showCoordinates = true,
  showComponents = false,
  onLocationUpdate = null,
  className = "",
  compact = false
}) => {
  const [showDetails, setShowDetails] = useState(false);
  const { reverseGeocode, loading } = useGeocoding();

  const handleCoordinateClick = async () => {
    if (onLocationUpdate && geocodeResult) {
      try {
        const results = await reverseGeocode(
          geocodeResult.latitude, 
          geocodeResult.longitude
        );
        onLocationUpdate(results);
      } catch (err) {
        console.error('Failed to update location:', err);
      }
    }
  };

  const formatAddressComponents = (components) => {
    return components.reduce((acc, component) => {
      const type = component.types[0];
      acc[type] = component.long_name;
      return acc;
    }, {});
  };

  if (!geocodeResult) {
    return null;
  }

  const formattedComponents = showComponents ? 
    formatAddressComponents(geocodeResult.address_components || []) : {};

  if (compact) {
    return (
      <div className={`text-sm text-gray-600 ${className}`}>
        <div className="truncate" title={geocodeResult.formatted_address}>
          📍 {geocodeResult.formatted_address}
        </div>
        {showCoordinates && (
          <div className="text-xs text-gray-500">
            {geocodeResult.latitude.toFixed(4)}, {geocodeResult.longitude.toFixed(4)}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className={`bg-white rounded-lg shadow-md p-4 ${className}`}>
      <div className="space-y-3">
        <div>
          <h3 className="text-lg font-semibold text-gray-900 flex items-center">
            📍 Location Information
          </h3>
          <p className="text-gray-700 mt-1">
            {geocodeResult.formatted_address}
          </p>
        </div>

        {showCoordinates && (
          <div className="flex items-center space-x-2">
            <span className="text-sm text-gray-600">Coordinates:</span>
            <button
              onClick={handleCoordinateClick}
              disabled={loading || !onLocationUpdate}
              className="text-sm text-blue-600 hover:text-blue-800 disabled:text-gray-400 transition-colors"
              title={onLocationUpdate ? "Click to get alternate addresses" : "Read-only coordinates"}
            >
              {geocodeResult.latitude.toFixed(6)}, {geocodeResult.longitude.toFixed(6)}
            </button>
            {loading && (
              <div className="animate-spin h-4 w-4 border-2 border-blue-500 rounded-full border-t-transparent"></div>
            )}
          </div>
        )}

        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">Place ID:</span>
          <code className="text-xs bg-gray-100 px-2 py-1 rounded font-mono">
            {geocodeResult.place_id}
          </code>
        </div>

        <div className="flex items-center space-x-2">
          <span className="text-sm text-gray-600">Accuracy:</span>
          <span className={`text-sm px-2 py-1 rounded-full text-xs ${
            geocodeResult.geometry_type === 'ROOFTOP' 
              ? 'bg-green-100 text-green-800' 
              : geocodeResult.geometry_type === 'RANGE_INTERPOLATED'
                ? 'bg-yellow-100 text-yellow-800'
                : 'bg-gray-100 text-gray-800'
          }`}>
            {geocodeResult.geometry_type}
          </span>
        </div>

        {showComponents && geocodeResult.address_components && (
          <div>
            <button
              onClick={() => setShowDetails(!showDetails)}
              className="text-sm text-blue-600 hover:text-blue-800 flex items-center transition-colors"
            >
              {showDetails ? 'Hide' : 'Show'} Address Components
              <svg 
                className={`ml-1 h-4 w-4 transform transition-transform ${showDetails ? 'rotate-180' : ''}`}
                fill="none" 
                viewBox="0 0 24 24" 
                stroke="currentColor"
              >
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            {showDetails && (
              <div className="mt-2 space-y-1 bg-gray-50 p-3 rounded-md">
                {Object.entries(formattedComponents).map(([type, value]) => (
                  <div key={type} className="flex justify-between text-sm">
                    <span className="text-gray-600 capitalize font-medium">
                      {type.replace(/_/g, ' ')}:
                    </span>
                    <span className="text-gray-800">{value}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default LocationDisplay;