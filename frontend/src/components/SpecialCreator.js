import React, { useState } from 'react';
import { 
  XMarkIcon,
  CalendarDaysIcon,
  ClockIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';

const SpecialCreator = ({ token, restaurants, onClose, onSpecialCreated, editingSpecial = null }) => {
  const today = new Date().toISOString().split('T')[0];
  const nextMonth = new Date(Date.now() + 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0];

  const [formData, setFormData] = useState({
    restaurant_id: editingSpecial?.restaurant_id || (restaurants.length === 1 ? restaurants[0].id : ''),
    title: editingSpecial?.title || '',
    description: editingSpecial?.description || '',
    special_type: editingSpecial?.special_type || 'daily_special',
    price: editingSpecial?.price || '',
    original_price: editingSpecial?.original_price || '',
    discount_percentage: editingSpecial?.discount_percentage || '',
    days_available: editingSpecial?.days_available || ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
    time_start: editingSpecial?.time_start || '11:00',
    time_end: editingSpecial?.time_end || '21:00',
    valid_from: editingSpecial?.valid_from?.split('T')[0] || today,
    valid_until: editingSpecial?.valid_until?.split('T')[0] || nextMonth,
    max_redemptions: editingSpecial?.max_redemptions || '',
    terms_conditions: editingSpecial?.terms_conditions || ''
  });
  
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const backendUrl = process.env.REACT_APP_BACKEND_URL 
    ? `${process.env.REACT_APP_BACKEND_URL}/api` 
    : '/api';

  const specialTypes = [
    { value: 'daily_special', label: 'Daily Special', icon: '🍽️' },
    { value: 'happy_hour', label: 'Happy Hour', icon: '🍻' },
    { value: 'lunch_special', label: 'Lunch Special', icon: '☀️' },
    { value: 'dinner_special', label: 'Dinner Special', icon: '🌙' },
    { value: 'discount', label: 'Discount', icon: '💰' },
    { value: 'bogo', label: 'Buy One Get One', icon: '🎁' }
  ];

  const daysOfWeek = [
    { value: 'monday', label: 'Mon' },
    { value: 'tuesday', label: 'Tue' },
    { value: 'wednesday', label: 'Wed' },
    { value: 'thursday', label: 'Thu' },
    { value: 'friday', label: 'Fri' },
    { value: 'saturday', label: 'Sat' },
    { value: 'sunday', label: 'Sun' }
  ];

  const handleInputChange = (e) => {
    const { name, value, type, checked } = e.target;
    if (type === 'checkbox' && name === 'day_checkbox') {
      const day = value;
      setFormData(prev => ({
        ...prev,
        days_available: checked 
          ? [...prev.days_available, day]
          : prev.days_available.filter(d => d !== day)
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: value
      }));
    }
  };

  const toggleDay = (day) => {
    setFormData(prev => ({
      ...prev,
      days_available: prev.days_available.includes(day)
        ? prev.days_available.filter(d => d !== day)
        : [...prev.days_available, day]
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setSaving(true);

    try {
      // Validate required fields
      if (!formData.restaurant_id) {
        throw new Error('Please select a restaurant');
      }
      if (!formData.title.trim()) {
        throw new Error('Please enter a special title');
      }
      if (!formData.description.trim()) {
        throw new Error('Please enter a description');
      }
      if (formData.days_available.length === 0) {
        throw new Error('Please select at least one day');
      }

      const specialData = {
        restaurant_id: formData.restaurant_id,
        title: formData.title.trim(),
        description: formData.description.trim(),
        special_type: formData.special_type,
        price: formData.price ? parseFloat(formData.price) : null,
        original_price: formData.original_price ? parseFloat(formData.original_price) : null,
        discount_percentage: formData.discount_percentage ? parseInt(formData.discount_percentage) : null,
        days_available: formData.days_available,
        time_start: formData.time_start,
        time_end: formData.time_end,
        valid_from: formData.valid_from,
        valid_until: formData.valid_until,
        max_redemptions: formData.max_redemptions ? parseInt(formData.max_redemptions) : null,
        terms_conditions: formData.terms_conditions || null
      };

      const url = editingSpecial 
        ? `${backendUrl}/owners/specials/${editingSpecial.id}`
        : `${backendUrl}/owners/specials`;
      
      const method = editingSpecial ? 'PUT' : 'POST';

      const response = await fetch(url, {
        method,
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify(specialData)
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Failed to save special');
      }

      const savedSpecial = await response.json();
      onSpecialCreated(savedSpecial);
      onClose();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-[60] p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full h-[90vh] flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-orange-500 to-red-500 text-white p-4 flex justify-between items-center flex-shrink-0 rounded-t-lg">
          <div className="flex items-center">
            <SparklesIcon className="w-6 h-6 mr-2" />
            <h2 className="text-xl font-bold">
              {editingSpecial ? 'Edit Special' : 'Create New Special'}
            </h2>
          </div>
          <button onClick={onClose} className="text-white hover:bg-white/20 p-1 rounded">
            <XMarkIcon className="w-6 h-6" />
          </button>
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="flex-1 overflow-y-auto p-6">
          {error && (
            <div className="bg-red-50 text-red-700 p-3 rounded-lg mb-4">
              {error}
            </div>
          )}

          {/* Restaurant Selection */}
          {restaurants.length > 1 && (
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Restaurant *
              </label>
              <select
                name="restaurant_id"
                value={formData.restaurant_id}
                onChange={handleInputChange}
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
                required
              >
                <option value="">Select a restaurant</option>
                {restaurants.map(r => (
                  <option key={r.id} value={r.id}>{r.name}</option>
                ))}
              </select>
            </div>
          )}

          {/* Special Title */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Special Title *
            </label>
            <input
              type="text"
              name="title"
              value={formData.title}
              onChange={handleInputChange}
              placeholder="e.g., Half-Price Wings Wednesday"
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
              maxLength={100}
              required
            />
          </div>

          {/* Description */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description *
            </label>
            <textarea
              name="description"
              value={formData.description}
              onChange={handleInputChange}
              placeholder="Describe your special offer in detail..."
              rows={3}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
              maxLength={500}
              required
            />
            <p className="text-xs text-gray-500 mt-1">{formData.description.length}/500 characters</p>
          </div>

          {/* Special Type */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Special Type
            </label>
            <div className="grid grid-cols-3 gap-2">
              {specialTypes.map(type => (
                <button
                  key={type.value}
                  type="button"
                  onClick={() => setFormData(prev => ({ ...prev, special_type: type.value }))}
                  className={`p-2 border rounded-lg text-sm flex items-center justify-center transition-colors ${
                    formData.special_type === type.value
                      ? 'border-orange-500 bg-orange-50 text-orange-700'
                      : 'border-gray-300 hover:border-gray-400'
                  }`}
                >
                  <span className="mr-1">{type.icon}</span>
                  {type.label}
                </button>
              ))}
            </div>
          </div>

          {/* Pricing */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              Pricing (optional)
            </label>
            <div className="grid grid-cols-3 gap-3">
              <div>
                <label className="block text-xs text-gray-600 mb-1">Special Price</label>
                <div className="relative">
                  <span className="absolute left-3 top-2 text-gray-500">$</span>
                  <input
                    type="number"
                    name="price"
                    value={formData.price}
                    onChange={handleInputChange}
                    placeholder="9.99"
                    step="0.01"
                    min="0"
                    className="w-full p-2 pl-7 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Original Price</label>
                <div className="relative">
                  <span className="absolute left-3 top-2 text-gray-500">$</span>
                  <input
                    type="number"
                    name="original_price"
                    value={formData.original_price}
                    onChange={handleInputChange}
                    placeholder="19.99"
                    step="0.01"
                    min="0"
                    className="w-full p-2 pl-7 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
                  />
                </div>
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Discount %</label>
                <div className="relative">
                  <input
                    type="number"
                    name="discount_percentage"
                    value={formData.discount_percentage}
                    onChange={handleInputChange}
                    placeholder="50"
                    min="0"
                    max="100"
                    className="w-full p-2 pr-7 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
                  />
                  <span className="absolute right-3 top-2 text-gray-500">%</span>
                </div>
              </div>
            </div>
          </div>

          {/* Days Available */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <CalendarDaysIcon className="w-4 h-4 inline mr-1" />
              Days Available *
            </label>
            <div className="flex flex-wrap gap-2">
              {daysOfWeek.map(day => (
                <button
                  key={day.value}
                  type="button"
                  onClick={() => toggleDay(day.value)}
                  className={`px-3 py-1 rounded-full text-sm transition-colors ${
                    formData.days_available.includes(day.value)
                      ? 'bg-orange-500 text-white'
                      : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                  }`}
                >
                  {day.label}
                </button>
              ))}
            </div>
          </div>

          {/* Time Range */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <ClockIcon className="w-4 h-4 inline mr-1" />
              Time Range *
            </label>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-gray-600 mb-1">Start Time</label>
                <input
                  type="time"
                  name="time_start"
                  value={formData.time_start}
                  onChange={handleInputChange}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
                  required
                />
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">End Time</label>
                <input
                  type="time"
                  name="time_end"
                  value={formData.time_end}
                  onChange={handleInputChange}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
                  required
                />
              </div>
            </div>
          </div>

          {/* Valid Date Range */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <CalendarDaysIcon className="w-4 h-4 inline mr-1" />
              Valid Period *
            </label>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-xs text-gray-600 mb-1">From</label>
                <input
                  type="date"
                  name="valid_from"
                  value={formData.valid_from}
                  onChange={handleInputChange}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
                  required
                />
              </div>
              <div>
                <label className="block text-xs text-gray-600 mb-1">Until</label>
                <input
                  type="date"
                  name="valid_until"
                  value={formData.valid_until}
                  onChange={handleInputChange}
                  className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
                  required
                />
              </div>
            </div>
          </div>

          {/* Terms & Max Redemptions */}
          <div className="mb-4 grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Redemptions
              </label>
              <input
                type="number"
                name="max_redemptions"
                value={formData.max_redemptions}
                onChange={handleInputChange}
                placeholder="Unlimited"
                min="1"
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
              />
            </div>
            <div className="col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Terms & Conditions
              </label>
              <input
                type="text"
                name="terms_conditions"
                value={formData.terms_conditions}
                onChange={handleInputChange}
                placeholder="e.g., Dine-in only, Limit 2 per table"
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
                maxLength={1000}
              />
            </div>
          </div>

          {/* Info Box */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
            <p className="text-sm text-blue-800">
              <strong>Note:</strong> Your special will be submitted for approval. Once approved, it will be visible to customers searching in your area.
            </p>
          </div>
        </form>

        {/* Footer */}
        <div className="border-t p-4 bg-gray-50 flex justify-end gap-3 flex-shrink-0 rounded-b-lg">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={saving}
            className="px-6 py-2 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-lg hover:from-orange-600 hover:to-red-600 disabled:opacity-50"
          >
            {saving ? 'Saving...' : editingSpecial ? 'Update Special' : 'Create Special'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SpecialCreator;
