import { useState, useCallback } from 'react';
import axios from 'axios';

// Custom hook for geocoding operations
const useGeocoding = () => {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Get backend URL from environment
  const getBackendUrl = () => {
    return process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';
  };

  const forwardGeocode = useCallback(async (address, options = {}) => {
    setLoading(true);
    setError(null);
    
    try {
      const requestData = {
        address: address,
        region: options.region || null,
        bounds: options.bounds || null
      };
      
      const response = await axios.post(`${getBackendUrl()}/api/geocode/forward`, requestData);
      return response.data;
    } catch (err) {
      // Handle 404 errors gracefully (address not found)
      if (err.response?.status === 404) {
        const errorMessage = 'Address not found';
        setError(errorMessage);
        // For auto-suggestions, don't throw error to prevent interruptions
        return null;
      }
      
      const errorMessage = err.response?.data?.detail || 'Geocoding failed';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const reverseGeocode = useCallback(async (latitude, longitude, options = {}) => {
    setLoading(true);
    setError(null);
    
    try {
      const requestData = {
        latitude: latitude,
        longitude: longitude,
        result_type: options.resultType || null,
        location_type: options.locationType || null
      };
      
      const response = await axios.post(`${getBackendUrl()}/api/geocode/reverse`, requestData);
      return response.data;
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Reverse geocoding failed';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const batchGeocode = useCallback(async (addresses, options = {}) => {
    setLoading(true);
    setError(null);
    
    try {
      const requestData = {
        addresses: addresses,
        region: options.region || null,
        max_results: options.maxResults || 10
      };
      
      const response = await axios.post(`${getBackendUrl()}/api/geocode/batch`, requestData);
      return response.data;
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Batch geocoding failed';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  const legacyGeocode = useCallback(async (address) => {
    setLoading(true);
    setError(null);
    
    try {
      const response = await axios.get(`${getBackendUrl()}/api/geocode`, {
        params: { address }
      });
      return response.data;
    } catch (err) {
      const errorMessage = err.response?.data?.detail || 'Geocoding failed';
      setError(errorMessage);
      throw new Error(errorMessage);
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    forwardGeocode,
    reverseGeocode,
    batchGeocode,
    legacyGeocode,
    loading,
    error,
    clearError: () => setError(null)
  };
};

export default useGeocoding;