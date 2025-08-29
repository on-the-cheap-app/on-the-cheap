import React, { useEffect, useRef } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { MapPin, Star, Clock, DollarSign } from 'lucide-react';

// Fix for default markers in Leaflet with React
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

// Custom restaurant marker icon
const createRestaurantIcon = (restaurant) => {
  const hasSpecials = restaurant.specials?.length > 0;
  const isMobileVendor = restaurant.is_mobile_vendor;
  const iconColor = hasSpecials ? '#ea580c' : '#6b7280'; // Orange for specials, gray for no specials
  
  // Different emoji for mobile vendors vs restaurants
  const emoji = isMobileVendor ? '🚛' : '🍽️';
  
  return L.divIcon({
    html: `
      <div style="
        background-color: ${iconColor};
        width: 24px;
        height: 24px;
        border-radius: 50%;
        border: 2px solid white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        color: white;
        font-size: 12px;
        font-weight: bold;
      ">
        ${emoji}
      </div>
    `,
    className: 'custom-restaurant-marker',
    iconSize: [24, 24],
    iconAnchor: [12, 12]
  });
};

// Current location marker icon
const createCurrentLocationIcon = () => {
  return L.divIcon({
    html: `
      <div style="
        background-color: #3b82f6;
        width: 16px;
        height: 16px;
        border-radius: 50%;
        border: 3px solid white;
        box-shadow: 0 2px 4px rgba(0,0,0,0.3);
        position: relative;
      ">
        <div style="
          position: absolute;
          top: -8px;
          left: -8px;
          width: 32px;
          height: 32px;
          border-radius: 50%;
          background-color: rgba(59, 130, 246, 0.3);
          animation: pulse 2s infinite;
        "></div>
      </div>
    `,
    className: 'current-location-marker',
    iconSize: [16, 16],
    iconAnchor: [8, 8]
  });
};

// Component to fit map bounds to restaurants
function FitBounds({ restaurants, currentLocation }) {
  const map = useMap();
  
  useEffect(() => {
    if (restaurants.length > 0) {
      const bounds = [];
      
      // Add current location to bounds if available
      if (currentLocation) {
        bounds.push([currentLocation.latitude, currentLocation.longitude]);
      }
      
      // Add restaurant locations to bounds
      restaurants.forEach(restaurant => {
        if (restaurant.location?.latitude && restaurant.location?.longitude) {
          bounds.push([restaurant.location.latitude, restaurant.location.longitude]);
        }
      });
      
      if (bounds.length > 0) {
        const leafletBounds = L.latLngBounds(bounds);
        map.fitBounds(leafletBounds, { 
          padding: [20, 20],
          maxZoom: 16
        });
      }
    }
  }, [restaurants, currentLocation, map]);
  
  return null;
}

const RestaurantMap = ({ 
  restaurants = [], 
  currentLocation = null,
  onRestaurantClick = null,
  selectedRestaurant = null,
  className = ""
}) => {
  const mapRef = useRef();
  
  // Default center (San Francisco if no location provided)
  const defaultCenter = currentLocation 
    ? [currentLocation.latitude, currentLocation.longitude]
    : [37.7749, -122.4194];

  const formatDistance = (distanceMeters) => {
    const miles = (distanceMeters * 0.000621371).toFixed(1);
    return `${miles} mi`;
  };

  const getSpecialsText = (restaurant) => {
    if (restaurant.specials?.length > 0) {
      return `${restaurant.specials.length} special${restaurant.specials.length !== 1 ? 's' : ''} available`;
    }
    return restaurant.specials_message || 'No current specials';
  };

  return (
    <div className={`w-full h-full ${className}`}>
      <MapContainer
        ref={mapRef}
        center={defaultCenter}
        zoom={13}
        style={{ height: '100%', width: '100%' }}
        className="rounded-lg z-0"
      >
        <TileLayer
          attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
          url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"
        />
        
        {/* Fit bounds to show all restaurants */}
        <FitBounds restaurants={restaurants} currentLocation={currentLocation} />
        
        {/* Current location marker */}
        {currentLocation && (
          <Marker
            position={[currentLocation.latitude, currentLocation.longitude]}
            icon={createCurrentLocationIcon()}
          >
            <Popup>
              <div className="text-center">
                <div className="flex items-center justify-center mb-1">
                  <MapPin className="w-4 h-4 mr-1 text-blue-600" />
                  <span className="font-medium">Your Location</span>
                </div>
                <p className="text-sm text-gray-600">Current position</p>
              </div>
            </Popup>
          </Marker>
        )}
        
        {/* Restaurant markers */}
        {restaurants.map((restaurant, index) => {
          if (!restaurant.location?.latitude || !restaurant.location?.longitude) {
            return null;
          }
          
          return (
            <Marker
              key={restaurant.id || index}
              position={[restaurant.location.latitude, restaurant.location.longitude]}
              icon={createRestaurantIcon(restaurant)}
              eventHandlers={{
                click: () => {
                  if (onRestaurantClick) {
                    onRestaurantClick(restaurant);
                  }
                }
              }}
            >
              <Popup maxWidth={300} className="custom-popup">
                <div className="p-2">
                  <div className="flex items-center gap-2 mb-2">
                    <h3 className="font-semibold text-lg">{restaurant.name}</h3>
                    {restaurant.is_mobile_vendor && (
                      <span className="bg-orange-100 text-orange-800 text-xs px-2 py-1 rounded-full">
                        🚛 Mobile
                      </span>
                    )}
                  </div>
                  
                  {restaurant.address && (
                    <div className="flex items-start mb-2">
                      <MapPin className="w-4 h-4 mr-1 text-gray-500 flex-shrink-0 mt-0.5" />
                      <span className="text-sm text-gray-600">{restaurant.address}</span>
                    </div>
                  )}
                  
                  <div className="flex items-center gap-4 mb-2 text-sm">
                    {restaurant.rating && (
                      <div className="flex items-center">
                        <Star className="w-4 h-4 mr-1 text-yellow-500 fill-current" />
                        <span>{restaurant.rating}</span>
                      </div>
                    )}
                    
                    {restaurant.distance !== undefined && (
                      <div className="flex items-center">
                        <MapPin className="w-4 h-4 mr-1 text-gray-500" />
                        <span>{formatDistance(restaurant.distance)}</span>
                      </div>
                    )}
                    
                    {restaurant.price_level && (
                      <div className="flex items-center">
                        <DollarSign className="w-4 h-4 mr-1 text-green-600" />
                        <span>{'$'.repeat(restaurant.price_level)}</span>
                      </div>
                    )}
                  </div>
                  
                  {/* Specials info */}
                  <div className="border-t pt-2 mt-2">
                    <div className="flex items-center mb-1">
                      <Clock className="w-4 h-4 mr-1 text-orange-600" />
                      <span className="text-sm font-medium">Specials</span>
                    </div>
                    <p className="text-sm text-gray-600">{getSpecialsText(restaurant)}</p>
                    
                    {restaurant.specials?.length > 0 && (
                      <div className="mt-2 space-y-1">
                        {restaurant.specials.slice(0, 2).map((special, idx) => (
                          <div key={idx} className="text-xs bg-orange-50 p-1 rounded">
                            <span className="font-medium">{special.title}</span> - ${special.price}
                          </div>
                        ))}
                        {restaurant.specials.length > 2 && (
                          <p className="text-xs text-gray-500">
                            +{restaurant.specials.length - 2} more specials
                          </p>
                        )}
                      </div>
                    )}
                  </div>
                  
                  {/* Source indicator */}
                  <div className="border-t pt-2 mt-2">
                    <span className="text-xs text-gray-500 capitalize">
                      Source: {restaurant.source?.replace('_', ' ') || 'unknown'}
                    </span>
                  </div>
                </div>
              </Popup>
            </Marker>
          );
        })}
      </MapContainer>
      
      {/* Add pulse animation CSS */}
      <style jsx>{`
        @keyframes pulse {
          0% {
            transform: scale(1);
            opacity: 1;
          }
          70% {
            transform: scale(1.5);
            opacity: 0;
          }
          100% {
            transform: scale(1.5);
            opacity: 0;
          }
        }
      `}</style>
    </div>
  );
};

export default RestaurantMap;