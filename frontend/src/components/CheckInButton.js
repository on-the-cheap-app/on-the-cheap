import React, { useState } from 'react';
import { MapPin, CheckCircle, X, Loader2, Navigation } from 'lucide-react';
import { verifyCheckIn } from '../services/analyticsService';

const CheckInButton = ({ restaurant, userToken, onSuccess }) => {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleCheckIn = async () => {
    if (!userToken) {
      setError('Please log in to check in');
      return;
    }

    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const checkInResult = await verifyCheckIn(restaurant.id, userToken);
      setResult(checkInResult);
      
      if (checkInResult.verified && onSuccess) {
        onSuccess(checkInResult);
      }
    } catch (err) {
      setError(err.message || 'Check-in failed');
    } finally {
      setLoading(false);
    }
  };

  const handleDismiss = () => {
    setResult(null);
    setError(null);
  };

  // Show result state
  if (result) {
    return (
      <div className={`rounded-lg p-4 ${result.verified ? 'bg-green-50 border border-green-200' : 'bg-yellow-50 border border-yellow-200'}`}>
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            {result.verified ? (
              <CheckCircle className="w-6 h-6 text-green-500 flex-shrink-0 mt-0.5" />
            ) : (
              <Navigation className="w-6 h-6 text-yellow-500 flex-shrink-0 mt-0.5" />
            )}
            <div>
              <p className={`font-medium ${result.verified ? 'text-green-800' : 'text-yellow-800'}`}>
                {result.verified ? 'Check-in Verified!' : 'Not Close Enough'}
              </p>
              <p className={`text-sm ${result.verified ? 'text-green-600' : 'text-yellow-600'}`}>
                {result.message}
              </p>
            </div>
          </div>
          <button 
            onClick={handleDismiss}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
      </div>
    );
  }

  // Show error state
  if (error) {
    return (
      <div className="rounded-lg p-4 bg-red-50 border border-red-200">
        <div className="flex items-start justify-between">
          <div className="flex items-start gap-3">
            <X className="w-6 h-6 text-red-500 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium text-red-800">Check-in Failed</p>
              <p className="text-sm text-red-600">{error}</p>
            </div>
          </div>
          <button 
            onClick={handleDismiss}
            className="text-gray-400 hover:text-gray-600"
          >
            <X className="w-5 h-5" />
          </button>
        </div>
        <button
          onClick={handleCheckIn}
          className="mt-3 text-sm text-red-600 hover:text-red-700 underline"
        >
          Try again
        </button>
      </div>
    );
  }

  // Default check-in button
  return (
    <button
      onClick={handleCheckIn}
      disabled={loading}
      className="flex items-center gap-2 px-4 py-2 bg-gradient-to-r from-orange-500 to-amber-500 text-white rounded-lg hover:from-orange-600 hover:to-amber-600 transition-all shadow-md disabled:opacity-50 disabled:cursor-not-allowed"
      data-testid="checkin-button"
    >
      {loading ? (
        <>
          <Loader2 className="w-5 h-5 animate-spin" />
          <span>Verifying location...</span>
        </>
      ) : (
        <>
          <MapPin className="w-5 h-5" />
          <span>I'm Here - Check In</span>
        </>
      )}
    </button>
  );
};

export default CheckInButton;
