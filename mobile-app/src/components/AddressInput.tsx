import React, { useState, useEffect } from 'react';
import {
  View,
  StyleSheet,
  FlatList,
  TouchableOpacity,
} from 'react-native';
import {
  Searchbar,
  Text,
  Card,
  ActivityIndicator,
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

import APIService from '../services/APIService';
import { colors, spacing } from '../theme/colors';

interface AddressSuggestion {
  formatted_address: string;
  latitude: number;
  longitude: number;
  place_id: string;
}

interface AddressInputProps {
  placeholder?: string;
  onAddressSelect: (result: AddressSuggestion) => void;
  onQueryChange?: (query: string) => void;
  initialValue?: string;
  region?: string;
  style?: any;
}

const AddressInput: React.FC<AddressInputProps> = ({
  placeholder = "Enter city or address",
  onAddressSelect,
  onQueryChange,
  initialValue = "",
  region = "US",
  style,
}) => {
  const [query, setQuery] = useState(initialValue);
  const [suggestions, setSuggestions] = useState<AddressSuggestion[]>([]);
  const [loading, setLoading] = useState(false);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Debounced search for suggestions
  useEffect(() => {
    if (query.length < 3) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    const timeoutId = setTimeout(() => {
      searchAddressSuggestions(query);
    }, 800); // Increased debounce from 500ms to 800ms

    return () => clearTimeout(timeoutId);
  }, [query]);

  const searchAddressSuggestions = async (searchQuery: string) => {
    if (!searchQuery.trim() || searchQuery.length < 3) {
      return;
    }

    setLoading(true);
    try {
      const response = await APIService.forwardGeocode(searchQuery, region);
      
      // Convert response to our suggestion format
      const suggestion: AddressSuggestion = {
        formatted_address: response.formatted_address,
        latitude: response.latitude,
        longitude: response.longitude,
        place_id: response.place_id,
      };
      
      setSuggestions([suggestion]);
      setShowSuggestions(true);
    } catch (error) {
      console.error('Address suggestion error:', error);
      setSuggestions([]);
      setShowSuggestions(false);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestionSelect = (suggestion: AddressSuggestion) => {
    setQuery(suggestion.formatted_address);
    setShowSuggestions(false);
    setSuggestions([]);
    onAddressSelect(suggestion);
    
    // Prevent immediate re-triggering of search with delay
    setTimeout(() => {
      setShowSuggestions(false);
      setSuggestions([]);
    }, 200);
  };

  const handleQueryChange = (text: string) => {
    setQuery(text);
    onQueryChange?.(text);
    if (text.length < 3) {
      setShowSuggestions(false);
      setSuggestions([]);
    }
  };

  const handleSubmitEditing = () => {
    setShowSuggestions(false);  // Force close suggestions
    setSuggestions([]);         // Clear suggestions array
    
    if (suggestions.length > 0) {
      handleSuggestionSelect(suggestions[0]);
    } else if (query.trim()) {
      // Try to geocode the current query directly
      searchAddressSuggestions(query);
    }
  };

  const clearInput = () => {
    setQuery('');
    setSuggestions([]);
    setShowSuggestions(false);
  };

  const renderSuggestion = ({ item }: { item: AddressSuggestion }) => (
    <TouchableOpacity 
      onPress={() => handleSuggestionSelect(item)}
      activeOpacity={0.7}
    >
      <Card style={styles.suggestionCard}>
        <Card.Content style={styles.suggestionContent}>
          <Icon 
            name="map-marker" 
            size={16} 
            color={colors.textLight} 
            style={styles.suggestionIcon}
          />
          <Text style={styles.suggestionText} numberOfLines={2}>
            {item.formatted_address}
          </Text>
        </Card.Content>
      </Card>
    </TouchableOpacity>
  );

  return (
    <View style={[styles.container, style]}>
      <Searchbar
        placeholder={placeholder}
        value={query}
        onChangeText={handleQueryChange}
        onSubmitEditing={handleSubmitEditing}
        style={styles.searchbar}
        icon="map-search"
        clearIcon={query ? "close" : undefined}
        onClearIconPress={clearInput}
        loading={loading}
      />
      
      {showSuggestions && suggestions.length > 0 && (
        <View style={styles.suggestionsContainer}>
          <FlatList
            data={suggestions}
            renderItem={renderSuggestion}
            keyExtractor={(item) => item.place_id}
            style={styles.suggestionsList}
            keyboardShouldPersistTaps="handled"
            nestedScrollEnabled={true}
          />
        </View>
      )}
      
      {loading && query.length >= 3 && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="small" color={colors.primary} />
          <Text style={styles.loadingText}>Searching locations...</Text>
        </View>
      )}
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    position: 'relative',
    zIndex: 1000,
  },
  searchbar: {
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  suggestionsContainer: {
    position: 'absolute',
    top: 56, // Height of searchbar
    left: 0,
    right: 0,
    backgroundColor: colors.surface,
    borderRadius: 8,
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    maxHeight: 200,
    zIndex: 1001,
  },
  suggestionsList: {
    flex: 1,
  },
  suggestionCard: {
    margin: 4,
    elevation: 1,
  },
  suggestionContent: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.sm,
  },
  suggestionIcon: {
    marginRight: spacing.sm,
  },
  suggestionText: {
    flex: 1,
    fontSize: 14,
    color: colors.textDark,
  },
  loadingContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.sm,
    backgroundColor: colors.surface,
    marginTop: spacing.xs,
    borderRadius: 8,
  },
  loadingText: {
    marginLeft: spacing.sm,
    fontSize: 12,
    color: colors.textLight,
  },
});

export default AddressInput;