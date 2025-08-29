import React, { useState, useEffect, useRef } from 'react';
import useGeocoding from '../hooks/useGeocoding';

const AddressInput = ({ 
  onAddressSelect, 
  placeholder = "Enter an address", 
  className = "",
  region = null,
  required = false,
  initialValue = "",
  disabled = false
}) => {
  const [inputValue, setInputValue] = useState(initialValue);
  const [suggestions, setSuggestions] = useState([]);
  const [showSuggestions, setShowSuggestions] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  
  const { forwardGeocode, loading, error } = useGeocoding();
  const debounceRef = useRef(null);
  const inputRef = useRef(null);

  // Update input value when initialValue changes
  useEffect(() => {
    setInputValue(initialValue);
  }, [initialValue]);

  // Debounced geocoding for suggestions
  useEffect(() => {
    if (debounceRef.current) {
      clearTimeout(debounceRef.current);
    }

    // Only trigger geocoding for meaningful input (avoid single words, too short phrases)
    const trimmedValue = inputValue.trim();
    const shouldTriggerGeocode = trimmedValue.length > 4 && 
                                !disabled && 
                                (trimmedValue.includes(',') || trimmedValue.split(' ').length >= 2);

    if (shouldTriggerGeocode) {
      debounceRef.current = setTimeout(async () => {
        try {
          console.log('Triggering geocoding for:', trimmedValue);
          const result = await forwardGeocode(trimmedValue, { region });
          if (result) {
            setSuggestions([result]);
            setShowSuggestions(true);
          }
        } catch (err) {
          console.error('Geocoding error:', err);
          setSuggestions([]);
          setShowSuggestions(false);
          // Don't show error for auto-suggestions to avoid UI interruptions
        }
      }, 1000); // Increased debounce delay
    } else {
      setSuggestions([]);
      setShowSuggestions(false);
    }

    return () => {
      if (debounceRef.current) {
        clearTimeout(debounceRef.current);
      }
    };
  }, [inputValue, forwardGeocode, region, disabled]);

  const handleInputChange = (e) => {
    setInputValue(e.target.value);
    setSelectedIndex(-1);
  };

  const handleSuggestionClick = (suggestion) => {
    setInputValue(suggestion.formatted_address);
    setShowSuggestions(false);
    if (onAddressSelect) {
      onAddressSelect(suggestion);
    }
  };

  const handleKeyDown = (e) => {
    if (!showSuggestions || suggestions.length === 0) {
      // Prevent form submission on Enter when no suggestions
      if (e.key === 'Enter') {
        e.preventDefault();
        if (inputValue.length > 2) {
          // Try to geocode current input
          forwardGeocode(inputValue, { region })
            .then(result => {
              setInputValue(result.formatted_address);
              setShowSuggestions(false);
              if (onAddressSelect) {
                onAddressSelect(result);
              }
            })
            .catch(err => {
              console.error('Geocoding failed:', err);
              // Error will be handled by the useGeocoding hook
            });
        }
      }
      return;
    }

    switch (e.key) {
      case 'ArrowDown':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev < suggestions.length - 1 ? prev + 1 : 0
        );
        break;
      case 'ArrowUp':
        e.preventDefault();
        setSelectedIndex(prev => 
          prev > 0 ? prev - 1 : suggestions.length - 1
        );
        break;
      case 'Enter':
        e.preventDefault(); // Always prevent form submission
        if (selectedIndex >= 0) {
          handleSuggestionClick(suggestions[selectedIndex]);
        } else if (inputValue.length > 2) {
          // Try to geocode current input
          forwardGeocode(inputValue, { region })
            .then(result => {
              setInputValue(result.formatted_address);
              setShowSuggestions(false);
              if (onAddressSelect) {
                onAddressSelect(result);
              }
            })
            .catch(err => {
              console.error('Geocoding failed:', err);
              // Error will be handled by the useGeocoding hook
            });
        }
        break;
      case 'Escape':
        setShowSuggestions(false);
        setSelectedIndex(-1);
        break;
      default:
        break;
    }
  };

  const handleBlur = () => {
    // Delay hiding suggestions to allow for clicks
    setTimeout(() => {
      setShowSuggestions(false);
      setSelectedIndex(-1);
    }, 200);
  };

  const handleFocus = () => {
    if (suggestions.length > 0) {
      setShowSuggestions(true);
    }
  };

  return (
    <div className={`relative ${className}`}>
      <input
        ref={inputRef}
        type="text"
        value={inputValue}
        onChange={handleInputChange}
        onKeyDown={handleKeyDown}
        onBlur={handleBlur}
        onFocus={handleFocus}
        placeholder={placeholder}
        required={required}
        disabled={disabled || loading}
        className={`w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500 ${
          disabled ? 'bg-gray-100 cursor-not-allowed' : ''
        } ${error ? 'border-red-500' : ''}`}
      />
      
      {loading && (
        <div className="absolute right-3 top-2">
          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-500"></div>
        </div>
      )}

      {showSuggestions && suggestions.length > 0 && (
        <ul className="absolute z-50 w-full mt-1 bg-white border border-gray-300 rounded-md shadow-lg max-h-60 overflow-auto">
          {suggestions.map((suggestion, index) => (
            <li
              key={suggestion.place_id}
              className={`px-3 py-2 cursor-pointer hover:bg-gray-100 ${
                index === selectedIndex ? 'bg-blue-100' : ''
              }`}
              onClick={() => handleSuggestionClick(suggestion)}
            >
              <div className="text-sm font-medium text-gray-900">
                {suggestion.formatted_address}
              </div>
              <div className="text-xs text-gray-500">
                {suggestion.latitude.toFixed(6)}, {suggestion.longitude.toFixed(6)}
              </div>
            </li>
          ))}
        </ul>
      )}

      {error && (
        <div className="mt-1 text-sm text-red-600">
          {error}
        </div>
      )}
    </div>
  );
};

export default AddressInput;