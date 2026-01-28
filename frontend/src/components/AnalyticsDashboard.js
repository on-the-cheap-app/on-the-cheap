import React, { useState, useEffect } from 'react';
import { 
  BarChart3, 
  Eye, 
  MousePointerClick, 
  Share2, 
  Heart, 
  MapPin, 
  Phone,
  CheckCircle,
  TrendingUp,
  Clock,
  Calendar
} from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL 
  ? `${process.env.REACT_APP_BACKEND_URL}/api` 
  : '/api';

const AnalyticsDashboard = ({ token }) => {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [period, setPeriod] = useState(30);

  useEffect(() => {
    fetchAnalytics();
  }, [token, period]);

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/owners/analytics?days=${period}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setAnalytics(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching analytics:', err);
      setError('Failed to load analytics data');
    } finally {
      setLoading(false);
    }
  };

  const StatCard = ({ icon: Icon, label, value, subtext, color = 'orange' }) => {
    const colorClasses = {
      orange: 'bg-orange-50 text-orange-600 border-orange-100',
      blue: 'bg-blue-50 text-blue-600 border-blue-100',
      green: 'bg-green-50 text-green-600 border-green-100',
      purple: 'bg-purple-50 text-purple-600 border-purple-100',
      pink: 'bg-pink-50 text-pink-600 border-pink-100',
      indigo: 'bg-indigo-50 text-indigo-600 border-indigo-100',
      teal: 'bg-teal-50 text-teal-600 border-teal-100',
      amber: 'bg-amber-50 text-amber-600 border-amber-100'
    };

    return (
      <div className={`rounded-lg p-4 border ${colorClasses[color]}`}>
        <div className="flex items-center gap-3">
          <Icon className="w-8 h-8 opacity-80" />
          <div>
            <p className="text-2xl font-bold">{value.toLocaleString()}</p>
            <p className="text-sm opacity-80">{label}</p>
            {subtext && <p className="text-xs opacity-60">{subtext}</p>}
          </div>
        </div>
      </div>
    );
  };

  const SimpleBarChart = ({ data, label }) => {
    if (!data || data.length === 0) return null;
    
    const maxValue = Math.max(...data.map(d => d.views || d.count || 0));
    
    return (
      <div className="mt-4">
        <p className="text-sm text-gray-500 mb-2">{label}</p>
        <div className="flex items-end gap-1 h-32">
          {data.slice(-14).map((item, idx) => {
            const value = item.views || item.count || 0;
            const height = maxValue > 0 ? (value / maxValue) * 100 : 0;
            return (
              <div 
                key={idx} 
                className="flex-1 bg-orange-400 rounded-t hover:bg-orange-500 transition-colors cursor-pointer group relative"
                style={{ height: `${Math.max(height, 2)}%` }}
                title={`${item.date || `Hour ${item.hour}`}: ${value}`}
              >
                <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-1 px-2 py-1 bg-gray-800 text-white text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity whitespace-nowrap z-10">
                  {item.date || `${item.hour}:00`}: {value}
                </div>
              </div>
            );
          })}
        </div>
        <div className="flex justify-between text-xs text-gray-400 mt-1">
          <span>{data[0]?.date || '0:00'}</span>
          <span>{data[data.length - 1]?.date || '23:00'}</span>
        </div>
      </div>
    );
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[1, 2, 3, 4].map(i => (
              <div key={i} className="h-24 bg-gray-200 rounded"></div>
            ))}
          </div>
          <div className="h-48 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="text-center text-red-500">
          <p>{error}</p>
          <button 
            onClick={fetchAnalytics}
            className="mt-2 text-orange-500 hover:text-orange-600"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="flex items-center justify-between mb-6">
          <div className="flex items-center gap-3">
            <div className="p-2 bg-orange-100 rounded-lg">
              <BarChart3 className="w-6 h-6 text-orange-600" />
            </div>
            <div>
              <h2 className="text-xl font-bold text-gray-900">Analytics Dashboard</h2>
              <p className="text-sm text-gray-500">Track customer engagement with your restaurant</p>
            </div>
          </div>
          
          {/* Period Selector */}
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-gray-400" />
            <select
              value={period}
              onChange={(e) => setPeriod(Number(e.target.value))}
              className="border border-gray-300 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-orange-500"
              data-testid="period-selector"
            >
              <option value={7}>Last 7 days</option>
              <option value={30}>Last 30 days</option>
              <option value={90}>Last 90 days</option>
            </select>
          </div>
        </div>

        {/* Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <StatCard 
            icon={Eye} 
            label="Total Views" 
            value={analytics?.total_views || 0}
            color="blue"
          />
          <StatCard 
            icon={MousePointerClick} 
            label="Total Clicks" 
            value={analytics?.total_clicks || 0}
            subtext={`${analytics?.click_through_rate || 0}% CTR`}
            color="green"
          />
          <StatCard 
            icon={Share2} 
            label="Shares" 
            value={analytics?.total_shares || 0}
            color="purple"
          />
          <StatCard 
            icon={Heart} 
            label="Favorites" 
            value={analytics?.total_favorites || 0}
            color="pink"
          />
        </div>

        {/* Secondary Stats */}
        <div className="grid grid-cols-3 gap-4 mt-4">
          <StatCard 
            icon={MapPin} 
            label="Directions" 
            value={analytics?.total_directions || 0}
            color="indigo"
          />
          <StatCard 
            icon={Phone} 
            label="Calls" 
            value={analytics?.total_calls || 0}
            color="teal"
          />
          <StatCard 
            icon={CheckCircle} 
            label="Check-ins" 
            value={analytics?.total_checkins || 0}
            color="amber"
          />
        </div>
      </div>

      {/* Charts Section */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Daily Views Chart */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-5 h-5 text-orange-500" />
            <h3 className="font-semibold text-gray-900">Views Over Time</h3>
          </div>
          {analytics?.daily_stats?.length > 0 ? (
            <SimpleBarChart data={analytics.daily_stats} label="Daily views" />
          ) : (
            <div className="text-center py-8 text-gray-400">
              <Eye className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>No view data yet</p>
            </div>
          )}
        </div>

        {/* Hourly Distribution */}
        <div className="bg-white rounded-lg shadow-md p-6">
          <div className="flex items-center gap-2 mb-4">
            <Clock className="w-5 h-5 text-orange-500" />
            <h3 className="font-semibold text-gray-900">Peak Hours</h3>
          </div>
          {analytics?.hourly_distribution?.some(h => h.count > 0) ? (
            <SimpleBarChart data={analytics.hourly_distribution} label="Activity by hour" />
          ) : (
            <div className="text-center py-8 text-gray-400">
              <Clock className="w-12 h-12 mx-auto mb-2 opacity-50" />
              <p>No hourly data yet</p>
            </div>
          )}
        </div>
      </div>

      {/* Engagement Insights */}
      <div className="bg-white rounded-lg shadow-md p-6">
        <h3 className="font-semibold text-gray-900 mb-4">Engagement Insights</h3>
        
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {/* Click-Through Rate */}
          <div className="bg-gradient-to-br from-green-50 to-emerald-50 rounded-lg p-4 border border-green-100">
            <p className="text-sm text-green-700 font-medium">Click-Through Rate</p>
            <p className="text-3xl font-bold text-green-600 mt-1">
              {analytics?.click_through_rate || 0}%
            </p>
            <p className="text-xs text-green-600 mt-2">
              {analytics?.total_clicks || 0} clicks from {analytics?.total_views || 0} views
            </p>
          </div>

          {/* Conversion Funnel */}
          <div className="bg-gradient-to-br from-blue-50 to-indigo-50 rounded-lg p-4 border border-blue-100">
            <p className="text-sm text-blue-700 font-medium">Action Rate</p>
            <p className="text-3xl font-bold text-blue-600 mt-1">
              {analytics?.total_clicks > 0 
                ? Math.round(((analytics?.total_directions || 0) + (analytics?.total_calls || 0)) / analytics?.total_clicks * 100)
                : 0}%
            </p>
            <p className="text-xs text-blue-600 mt-2">
              Users who clicked directions or called
            </p>
          </div>

          {/* Check-in Rate */}
          <div className="bg-gradient-to-br from-amber-50 to-orange-50 rounded-lg p-4 border border-amber-100">
            <p className="text-sm text-amber-700 font-medium">Verified Visits</p>
            <p className="text-3xl font-bold text-amber-600 mt-1">
              {analytics?.total_checkins || 0}
            </p>
            <p className="text-xs text-amber-600 mt-2">
              Customers who checked in at your venue
            </p>
          </div>
        </div>
      </div>

      {/* Recent Check-ins */}
      {analytics?.recent_checkins?.length > 0 && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="font-semibold text-gray-900 mb-4">Recent Check-ins</h3>
          <div className="space-y-2">
            {analytics.recent_checkins.map((checkin, idx) => (
              <div key={idx} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div className="flex items-center gap-3">
                  <CheckCircle className="w-5 h-5 text-green-500" />
                  <div>
                    <p className="text-sm font-medium text-gray-900">
                      Verified check-in
                    </p>
                    <p className="text-xs text-gray-500">
                      {new Date(checkin.timestamp).toLocaleString()}
                    </p>
                  </div>
                </div>
                <span className="text-xs text-gray-400">
                  {checkin.distance}m away
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* No Data State */}
      {analytics?.total_views === 0 && (
        <div className="bg-orange-50 border border-orange-200 rounded-lg p-6 text-center">
          <BarChart3 className="w-12 h-12 text-orange-400 mx-auto mb-3" />
          <h3 className="font-semibold text-orange-800 mb-2">No analytics data yet</h3>
          <p className="text-sm text-orange-600">
            Analytics will appear here as customers interact with your restaurant listing.
            Make sure your restaurant is visible in search results!
          </p>
        </div>
      )}
    </div>
  );
};

export default AnalyticsDashboard;
