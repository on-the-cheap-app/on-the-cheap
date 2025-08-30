import React, { useState, useEffect } from 'react';
import useNotifications from '../hooks/useNotifications';
import * as Analytics from '../utils/analytics';

const NotificationPreferences = ({ user, onClose }) => {
  const { isEnabled, isInitialized, isLoading, requestPermission, setUserPreferences } = useNotifications();
  
  const [preferences, setPreferences] = useState({
    newSpecials: true,
    favoriteUpdates: true,
    dailyDigest: false,
    cuisine: '',
    dietary: [],
    preferredTime: 'anytime'
  });

  const [saving, setSaving] = useState(false);

  useEffect(() => {
    // Track analytics
    Analytics.trackConversion('notification_preferences_view', {
      user_id: user?.id,
      notifications_enabled: isEnabled
    });
  }, [user?.id, isEnabled]);

  const handleEnableNotifications = async () => {
    const granted = await requestPermission();
    
    if (granted) {
      Analytics.trackConversion('notification_permission_granted', {
        user_id: user?.id
      });
    } else {
      Analytics.trackConversion('notification_permission_denied', {
        user_id: user?.id
      });
    }
  };

  const handleSavePreferences = async () => {
    if (!isEnabled) return;
    
    setSaving(true);
    try {
      const success = await setUserPreferences(preferences);
      
      if (success) {
        Analytics.trackConversion('notification_preferences_updated', {
          user_id: user?.id,
          preferences: preferences
        });
        
        // Show success message
        alert('Notification preferences saved successfully!');
      } else {
        alert('Failed to save preferences. Please try again.');
      }
    } catch (error) {
      console.error('Error saving preferences:', error);
      alert('Failed to save preferences. Please try again.');
    } finally {
      setSaving(false);
    }
  };

  const handlePreferenceChange = (key, value) => {
    setPreferences(prev => ({
      ...prev,
      [key]: value
    }));
  };

  const handleDietaryChange = (dietary, checked) => {
    setPreferences(prev => ({
      ...prev,
      dietary: checked 
        ? [...prev.dietary, dietary]
        : prev.dietary.filter(d => d !== dietary)
    }));
  };

  if (!isInitialized) {
    return (
      <div className="bg-white p-6 rounded-lg shadow-lg max-w-md mx-auto">
        <div className="animate-pulse">
          <div className="h-6 bg-gray-200 rounded mb-4"></div>
          <div className="space-y-3">
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
            <div className="h-4 bg-gray-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white p-6 rounded-lg shadow-lg max-w-md mx-auto">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-semibold text-gray-900">
          🔔 Notification Preferences
        </h3>
        <button 
          onClick={onClose}
          className="text-gray-400 hover:text-gray-600"
        >
          ✕
        </button>
      </div>

      {!isEnabled ? (
        <div className="text-center py-6">
          <div className="text-gray-600 mb-4">
            <div className="text-4xl mb-2">🔕</div>
            <p className="text-sm">Push notifications are not enabled</p>
          </div>
          
          <div className="bg-blue-50 p-4 rounded-lg mb-4">
            <p className="text-sm text-blue-800 mb-2">
              Get notified about:
            </p>
            <ul className="text-sm text-blue-700 space-y-1">
              <li>• New daily specials near you</li>
              <li>• Updates to your favorite restaurants</li>
              <li>• Limited-time offers and deals</li>
            </ul>
          </div>

          <button
            onClick={handleEnableNotifications}
            disabled={isLoading}
            className="w-full bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Setting up...' : 'Enable Notifications'}
          </button>
        </div>
      ) : (
        <div className="space-y-4">
          <div className="bg-green-50 p-3 rounded-lg flex items-center">
            <span className="text-green-600 mr-2">✅</span>
            <span className="text-sm text-green-800">
              Notifications enabled
            </span>
          </div>

          <div>
            <h4 className="font-medium text-gray-900 mb-3">Notification Types</h4>
            
            <div className="space-y-3">
              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={preferences.newSpecials}
                  onChange={(e) => handlePreferenceChange('newSpecials', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 mr-3"
                />
                <div>
                  <div className="font-medium text-sm">New Specials Near You</div>
                  <div className="text-xs text-gray-600">When restaurants add new specials in your area</div>
                </div>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={preferences.favoriteUpdates}
                  onChange={(e) => handlePreferenceChange('favoriteUpdates', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 mr-3"
                />
                <div>
                  <div className="font-medium text-sm">Favorite Restaurant Updates</div>
                  <div className="text-xs text-gray-600">When your favorited restaurants have new offers</div>
                </div>
              </label>

              <label className="flex items-center">
                <input
                  type="checkbox"
                  checked={preferences.dailyDigest}
                  onChange={(e) => handlePreferenceChange('dailyDigest', e.target.checked)}
                  className="rounded border-gray-300 text-blue-600 mr-3"
                />
                <div>
                  <div className="font-medium text-sm">Daily Specials Digest</div>
                  <div className="text-xs text-gray-600">Daily summary of specials (once per day)</div>
                </div>
              </label>
            </div>
          </div>

          <div>
            <h4 className="font-medium text-gray-900 mb-3">Preferences</h4>
            
            <div className="space-y-3">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Preferred Cuisine
                </label>
                <select
                  value={preferences.cuisine}
                  onChange={(e) => handlePreferenceChange('cuisine', e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                >
                  <option value="">Any cuisine</option>
                  <option value="american">American</option>
                  <option value="italian">Italian</option>
                  <option value="mexican">Mexican</option>
                  <option value="asian">Asian</option>
                  <option value="indian">Indian</option>
                  <option value="mediterranean">Mediterranean</option>
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Dietary Restrictions
                </label>
                <div className="space-y-2">
                  {['vegetarian', 'vegan', 'gluten-free', 'dairy-free'].map((dietary) => (
                    <label key={dietary} className="flex items-center">
                      <input
                        type="checkbox"
                        checked={preferences.dietary.includes(dietary)}
                        onChange={(e) => handleDietaryChange(dietary, e.target.checked)}
                        className="rounded border-gray-300 text-blue-600 mr-2"
                      />
                      <span className="text-sm capitalize">{dietary}</span>
                    </label>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Preferred Notification Time
                </label>
                <select
                  value={preferences.preferredTime}
                  onChange={(e) => handlePreferenceChange('preferredTime', e.target.value)}
                  className="w-full border border-gray-300 rounded-lg px-3 py-2 text-sm"
                >
                  <option value="anytime">Anytime</option>
                  <option value="morning">Morning (8AM - 12PM)</option>
                  <option value="afternoon">Afternoon (12PM - 6PM)</option>
                  <option value="evening">Evening (6PM - 10PM)</option>
                </select>
              </div>
            </div>
          </div>

          <div className="flex space-x-3 pt-4">
            <button
              onClick={handleSavePreferences}
              disabled={saving}
              className="flex-1 bg-blue-600 text-white py-2 px-4 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? 'Saving...' : 'Save Preferences'}
            </button>
            
            <button
              onClick={onClose}
              className="px-4 py-2 text-gray-600 hover:text-gray-800"
            >
              Cancel
            </button>
          </div>
        </div>
      )}
    </div>
  );
};

export default NotificationPreferences;