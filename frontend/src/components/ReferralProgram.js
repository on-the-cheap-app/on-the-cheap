import React, { useState, useEffect } from 'react';
import { Gift, Copy, Check, Users, Clock, Award, DollarSign } from 'lucide-react';
import axios from 'axios';

const API = process.env.REACT_APP_BACKEND_URL ? `${process.env.REACT_APP_BACKEND_URL}/api` : '/api';

const ReferralProgram = ({ token }) => {
  const [referralData, setReferralData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchReferralData();
  }, [token]);

  const fetchReferralData = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/owners/referrals`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      setReferralData(response.data);
      setError(null);
    } catch (err) {
      console.error('Error fetching referral data:', err);
      setError('Failed to load referral data');
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const getStatusBadge = (status) => {
    const styles = {
      pending: 'bg-yellow-100 text-yellow-800 border-yellow-200',
      qualified: 'bg-green-100 text-green-800 border-green-200',
      rewarded: 'bg-blue-100 text-blue-800 border-blue-200'
    };
    const labels = {
      pending: 'Pending (< 6 months)',
      qualified: 'Qualified!',
      rewarded: 'Reward Applied'
    };
    return (
      <span className={`px-2 py-1 rounded-full text-xs font-medium border ${styles[status] || styles.pending}`}>
        {labels[status] || status}
      </span>
    );
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow-md p-6">
        <div className="animate-pulse space-y-4">
          <div className="h-6 bg-gray-200 rounded w-1/3"></div>
          <div className="h-20 bg-gray-200 rounded"></div>
          <div className="h-40 bg-gray-200 rounded"></div>
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
            onClick={fetchReferralData}
            className="mt-2 text-orange-500 hover:text-orange-600"
          >
            Try Again
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow-md p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-2 bg-orange-100 rounded-lg">
          <Gift className="w-6 h-6 text-orange-600" />
        </div>
        <div>
          <h2 className="text-xl font-bold text-gray-900">Referral Program</h2>
          <p className="text-sm text-gray-500">Earn rewards by referring other restaurant owners</p>
        </div>
      </div>

      {/* How It Works */}
      <div className="bg-gradient-to-r from-orange-50 to-amber-50 rounded-lg p-4 border border-orange-100">
        <h3 className="font-semibold text-gray-900 mb-3">How It Works</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-sm">
          <div className="flex items-start gap-2">
            <div className="w-6 h-6 rounded-full bg-orange-500 text-white flex items-center justify-center text-xs font-bold flex-shrink-0">1</div>
            <div>
              <p className="font-medium text-gray-900">Share Your Code</p>
              <p className="text-gray-600">Give your unique code to other restaurant owners</p>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <div className="w-6 h-6 rounded-full bg-orange-500 text-white flex items-center justify-center text-xs font-bold flex-shrink-0">2</div>
            <div>
              <p className="font-medium text-gray-900">They Get 10% Off</p>
              <p className="text-gray-600">New owners get 10% off their first 6 months</p>
            </div>
          </div>
          <div className="flex items-start gap-2">
            <div className="w-6 h-6 rounded-full bg-orange-500 text-white flex items-center justify-center text-xs font-bold flex-shrink-0">3</div>
            <div>
              <p className="font-medium text-gray-900">You Get 20% Off</p>
              <p className="text-gray-600">After they stay 6 months, you get a 20% discount!</p>
            </div>
          </div>
        </div>
      </div>

      {/* Referral Code */}
      {referralData?.referral_code && (
        <div className="border-2 border-dashed border-orange-300 rounded-lg p-4 bg-orange-50">
          <p className="text-sm text-gray-600 mb-2">Your Referral Code</p>
          <div className="flex items-center gap-3">
            <code className="text-2xl font-bold text-orange-600 tracking-wider">
              {referralData.referral_code}
            </code>
            <button
              onClick={() => copyToClipboard(referralData.referral_code)}
              className="p-2 hover:bg-orange-100 rounded-lg transition-colors"
              title="Copy code"
              data-testid="copy-referral-code"
            >
              {copied ? (
                <Check className="w-5 h-5 text-green-500" />
              ) : (
                <Copy className="w-5 h-5 text-gray-500" />
              )}
            </button>
          </div>
          <button
            onClick={() => copyToClipboard(`Join On-the-Cheap and get 10% off your first 6 months! Use my referral code: ${referralData.referral_code} - Sign up at onthecheapapp.com`)}
            className="mt-3 text-sm text-orange-600 hover:text-orange-700 flex items-center gap-1"
          >
            <Copy className="w-4 h-4" />
            Copy share message
          </button>
        </div>
      )}

      {/* Stats */}
      {referralData?.stats && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="bg-gray-50 rounded-lg p-4 text-center">
            <Users className="w-5 h-5 text-gray-400 mx-auto mb-1" />
            <p className="text-2xl font-bold text-gray-900">{referralData.stats.total_referrals}</p>
            <p className="text-xs text-gray-500">Total Referrals</p>
          </div>
          <div className="bg-yellow-50 rounded-lg p-4 text-center">
            <Clock className="w-5 h-5 text-yellow-500 mx-auto mb-1" />
            <p className="text-2xl font-bold text-yellow-600">{referralData.stats.pending}</p>
            <p className="text-xs text-gray-500">Pending</p>
          </div>
          <div className="bg-green-50 rounded-lg p-4 text-center">
            <Award className="w-5 h-5 text-green-500 mx-auto mb-1" />
            <p className="text-2xl font-bold text-green-600">{referralData.stats.qualified}</p>
            <p className="text-xs text-gray-500">Qualified</p>
          </div>
          <div className="bg-blue-50 rounded-lg p-4 text-center">
            <DollarSign className="w-5 h-5 text-blue-500 mx-auto mb-1" />
            <p className="text-2xl font-bold text-blue-600">{referralData.stats.rewarded}</p>
            <p className="text-xs text-gray-500">Rewards Claimed</p>
          </div>
        </div>
      )}

      {/* Referral List */}
      <div>
        <h3 className="font-semibold text-gray-900 mb-3">Your Referrals</h3>
        {referralData?.referrals?.length > 0 ? (
          <div className="space-y-3">
            {referralData.referrals.map((referral) => (
              <div 
                key={referral.id} 
                className="flex items-center justify-between p-3 bg-gray-50 rounded-lg"
              >
                <div>
                  <p className="font-medium text-gray-900">{referral.referred_owner_name}</p>
                  <p className="text-sm text-gray-500">{referral.referred_owner_business}</p>
                  <p className="text-xs text-gray-400">
                    Joined {new Date(referral.created_at).toLocaleDateString()}
                  </p>
                </div>
                {getStatusBadge(referral.status)}
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 bg-gray-50 rounded-lg">
            <Users className="w-12 h-12 text-gray-300 mx-auto mb-2" />
            <p className="text-gray-500">No referrals yet</p>
            <p className="text-sm text-gray-400">Share your code to start earning rewards!</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ReferralProgram;
