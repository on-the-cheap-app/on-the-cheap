import React, { useState, useEffect } from 'react';
import { 
  XMarkIcon,
  PhotoIcon,
  CalendarDaysIcon,
  ClockIcon,
  TagIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';

const SpecialCreator = ({ token, restaurants, onClose, onSpecialCreated, editingSpecial = null }) => {
  const [formData, setFormData] = useState({
    restaurant_id: editingSpecial?.restaurant_id || (restaurants.length === 1 ? restaurants[0].id : ''),
    name: editingSpecial?.name || '',
    description: editingSpecial?.description || '',
    special_type: editingSpecial?.special_type || 'daily',
    discount_type: editingSpecial?.discount_type || 'percentage',
    discount_value: editingSpecial?.discount_value || '',
    original_price: editingSpecial?.original_price || '',
    start_date: editingSpecial?.start_date || new Date().toISOString().split('T')[0],
    end_date: editingSpecial?.end_date || '',
    start_time: editingSpecial?.start_time || '11:00',
    end_time: editingSpecial?.end_time || '23:00',
    days_of_week: editingSpecial?.days_of_week || ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday'],
    is_recurring: editingSpecial?.is_recurring ?? true,
    terms: editingSpecial?.terms || '',
    max_redemptions: editingSpecial?.max_redemptions || '',
    image_url: editingSpecial?.image_url || ''
  });
  
  const [imageFile, setImageFile] = useState(null);
  const [imagePreview, setImagePreview] = useState(editingSpecial?.image_url || '');
  const [uploading, setUploading] = useState(false);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');

  const backendUrl = process.env.REACT_APP_BACKEND_URL 
    ? `${process.env.REACT_APP_BACKEND_URL}/api` 
    : '/api';

  const specialTypes = [
    { value: 'daily', label: 'Daily Special', icon: '🍽️' },
    { value: 'happy_hour', label: 'Happy Hour', icon: '🍻' },
    { value: 'lunch', label: 'Lunch Special', icon: '☀️' },
    { value: 'dinner', label: 'Dinner Special', icon: '🌙' },
    { value: 'weekend', label: 'Weekend Special', icon: '🎉' },
    { value: 'limited_time', label: 'Limited Time Offer', icon: '⏰' }
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
    if (type === 'checkbox' && name === 'days_of_week') {
      const day = value;
      setFormData(prev => ({
        ...prev,
        days_of_week: checked 
          ? [...prev.days_of_week, day]
          : prev.days_of_week.filter(d => d !== day)
      }));
    } else {
      setFormData(prev => ({
        ...prev,
        [name]: type === 'checkbox' ? checked : value
      }));
    }
  };

  const handleImageChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      if (file.size > 5 * 1024 * 1024) {
        setError('Image must be less than 5MB');
        return;
      }
      setImageFile(file);
      const reader = new FileReader();
      reader.onloadend = () => {
        setImagePreview(reader.result);
      };
      reader.readAsDataURL(file);
    }
  };

  const uploadImage = async () => {
    if (!imageFile) return formData.image_url;
    
    setUploading(true);
    try {
      const uploadFormData = new FormData();
      uploadFormData.append('file', imageFile);
      
      const response = await fetch(`${backendUrl}/upload/image`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`
        },
        body: uploadFormData
      });
      
      if (!response.ok) {
        throw new Error('Failed to upload image');
      }
      
      const data = await response.json();
      return data.url;
    } catch (err) {
      console.error('Image upload error:', err);
      // If upload fails, continue without image
      return '';
    } finally {
      setUploading(false);
    }
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
      if (!formData.name.trim()) {
        throw new Error('Please enter a special name');
      }
      if (!formData.description.trim()) {
        throw new Error('Please enter a description');
      }

      // Upload image if selected
      let imageUrl = formData.image_url;
      if (imageFile) {
        imageUrl = await uploadImage();
      }

      const specialData = {
        ...formData,
        image_url: imageUrl,
        discount_value: formData.discount_value ? parseFloat(formData.discount_value) : null,
        original_price: formData.original_price ? parseFloat(formData.original_price) : null,
        max_redemptions: formData.max_redemptions ? parseInt(formData.max_redemptions) : null
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
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[90vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="bg-gradient-to-r from-orange-500 to-red-500 text-white p-4 flex justify-between items-center flex-shrink-0">
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

          {/* Special Name */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Special Name *
            </label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              placeholder="e.g., Half-Price Wings Wednesday"
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
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
              placeholder="Describe your special offer..."
              rows={3}
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
              required
            />
          </div>

          {/* Special Type */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Special Type
            </label>
            <div className="grid grid-cols-3 gap-2">
              {specialTypes.map(type => (
                <button
                  key={type.value}
                  type="button"
                  onClick={() => setFormData(prev => ({ ...prev, special_type: type.value }))}
                  className={`p-2 border rounded-lg text-sm flex items-center justify-center ${
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

          {/* Discount */}
          <div className="mb-4 grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Discount Type
              </label>
              <select
                name="discount_type"
                value={formData.discount_type}
                onChange={handleInputChange}
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
              >
                <option value="percentage">Percentage Off</option>
                <option value="fixed">Fixed Amount Off</option>
                <option value="bogo">Buy One Get One</option>
                <option value="price">Special Price</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                {formData.discount_type === 'percentage' ? 'Discount %' : 
                 formData.discount_type === 'bogo' ? 'BOGO Details' : 'Amount ($)'}
              </label>
              <input
                type={formData.discount_type === 'bogo' ? 'text' : 'number'}
                name="discount_value"
                value={formData.discount_value}
                onChange={handleInputChange}
                placeholder={formData.discount_type === 'percentage' ? '50' : 
                             formData.discount_type === 'bogo' ? 'Free' : '5.00'}
                className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
              />
            </div>
          </div>

          {/* Schedule */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-2">
              <CalendarDaysIcon className="w-4 h-4 inline mr-1" />
              Schedule
            </label>
            <div className="bg-gray-50 p-4 rounded-lg">
              <div className="flex items-center mb-3">
                <input
                  type="checkbox"
                  name="is_recurring"
                  checked={formData.is_recurring}
                  onChange={handleInputChange}
                  className="mr-2"
                />
                <span className="text-sm text-gray-700">Recurring special</span>
              </div>

              {formData.is_recurring ? (
                <div>
                  <p className="text-sm text-gray-600 mb-2">Active on:</p>
                  <div className="flex flex-wrap gap-2">
                    {daysOfWeek.map(day => (
                      <label key={day.value} className="flex items-center">
                        <input
                          type="checkbox"
                          name="days_of_week"
                          value={day.value}
                          checked={formData.days_of_week.includes(day.value)}
                          onChange={handleInputChange}
                          className="mr-1"
                        />
                        <span className="text-sm">{day.label}</span>
                      </label>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-xs text-gray-600 mb-1">Start Date</label>
                    <input
                      type="date"
                      name="start_date"
                      value={formData.start_date}
                      onChange={handleInputChange}
                      className="w-full p-2 border border-gray-300 rounded-lg text-sm"
                    />
                  </div>
                  <div>
                    <label className="block text-xs text-gray-600 mb-1">End Date</label>
                    <input
                      type="date"
                      name="end_date"
                      value={formData.end_date}
                      onChange={handleInputChange}
                      className="w-full p-2 border border-gray-300 rounded-lg text-sm"
                    />
                  </div>
                </div>
              )}

              <div className="grid grid-cols-2 gap-4 mt-3">
                <div>
                  <label className="block text-xs text-gray-600 mb-1">
                    <ClockIcon className="w-3 h-3 inline mr-1" />
                    Start Time
                  </label>
                  <input
                    type="time"
                    name="start_time"
                    value={formData.start_time}
                    onChange={handleInputChange}
                    className="w-full p-2 border border-gray-300 rounded-lg text-sm"
                  />
                </div>
                <div>
                  <label className="block text-xs text-gray-600 mb-1">
                    <ClockIcon className="w-3 h-3 inline mr-1" />
                    End Time
                  </label>
                  <input
                    type="time"
                    name="end_time"
                    value={formData.end_time}
                    onChange={handleInputChange}
                    className="w-full p-2 border border-gray-300 rounded-lg text-sm"
                  />
                </div>
              </div>
            </div>
          </div>

          {/* Image Upload */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              <PhotoIcon className="w-4 h-4 inline mr-1" />
              Special Image (optional)
            </label>
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-4 text-center hover:border-orange-400 transition-colors">
              {imagePreview ? (
                <div className="relative">
                  <img 
                    src={imagePreview} 
                    alt="Preview" 
                    className="max-h-40 mx-auto rounded-lg"
                  />
                  <button
                    type="button"
                    onClick={() => {
                      setImageFile(null);
                      setImagePreview('');
                      setFormData(prev => ({ ...prev, image_url: '' }));
                    }}
                    className="absolute top-1 right-1 bg-red-500 text-white p-1 rounded-full hover:bg-red-600"
                  >
                    <XMarkIcon className="w-4 h-4" />
                  </button>
                </div>
              ) : (
                <label className="cursor-pointer">
                  <PhotoIcon className="w-12 h-12 mx-auto text-gray-400 mb-2" />
                  <p className="text-sm text-gray-600">Click to upload image</p>
                  <p className="text-xs text-gray-400">PNG, JPG up to 5MB</p>
                  <input
                    type="file"
                    accept="image/*"
                    onChange={handleImageChange}
                    className="hidden"
                  />
                </label>
              )}
            </div>
          </div>

          {/* Terms & Conditions */}
          <div className="mb-4">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Terms & Conditions (optional)
            </label>
            <input
              type="text"
              name="terms"
              value={formData.terms}
              onChange={handleInputChange}
              placeholder="e.g., Dine-in only, Limit 2 per table"
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
            />
          </div>

          {/* Max Redemptions */}
          <div className="mb-6">
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Maximum Redemptions (optional)
            </label>
            <input
              type="number"
              name="max_redemptions"
              value={formData.max_redemptions}
              onChange={handleInputChange}
              placeholder="Leave empty for unlimited"
              className="w-full p-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-orange-500"
            />
          </div>
        </form>

        {/* Footer */}
        <div className="border-t p-4 bg-gray-50 flex justify-end gap-3 flex-shrink-0">
          <button
            type="button"
            onClick={onClose}
            className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-100"
          >
            Cancel
          </button>
          <button
            onClick={handleSubmit}
            disabled={saving || uploading}
            className="px-6 py-2 bg-gradient-to-r from-orange-500 to-red-500 text-white rounded-lg hover:from-orange-600 hover:to-red-600 disabled:opacity-50"
          >
            {saving ? 'Saving...' : uploading ? 'Uploading...' : editingSpecial ? 'Update Special' : 'Create Special'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default SpecialCreator;
