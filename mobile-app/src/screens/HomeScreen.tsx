import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  RefreshControl,
  Alert,
  TouchableOpacity,
} from 'react-native';
import {
  Searchbar,
  Button,
  Card,
  Title,
  Paragraph,
  Chip,
  ActivityIndicator,
  Menu,
  Divider,
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import Geolocation from 'react-native-geolocation-service';
import { PermissionsAndroid, Platform } from 'react-native';

import APIService from '../services/APIService';
import RestaurantCard from '../components/RestaurantCard';
import AddressInput from '../components/AddressInput';
import { colors, spacing } from '../theme/colors';

interface Restaurant {
  id: string;
  name: string;
  address: string;
  phone?: string;
  website?: string;
  rating?: number;
  specials?: any[];
  is_mobile_vendor?: boolean;
  vendor_type?: string;
  latitude?: number;
  longitude?: number;
}

const HomeScreen = ({ navigation }: any) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [location, setLocation] = useState<{ latitude: number; longitude: number } | null>(null);
  const [selectedSpecialType, setSelectedSpecialType] = useState<string>('all');
  const [selectedVendorType, setSelectedVendorType] = useState<string>('all');
  const [selectedRadius, setSelectedRadius] = useState<number>(25000); // 25km in meters
  const [specialTypes, setSpecialTypes] = useState<any[]>([]);
  const [searchLocation, setSearchLocation] = useState<string>('');
  const [lastSearchLocation, setLastSearchLocation] = useState<string>('');
  
  // Menu states for dropdowns
  const [specialTypeMenuVisible, setSpecialTypeMenuVisible] = useState(false);
  const [radiusMenuVisible, setRadiusMenuVisible] = useState(false);

  // Radius options
  const radiusOptions = [
    { label: '1 mile', value: 1609 },
    { label: '2 miles', value: 3219 },
    { label: '5 miles', value: 8047 },
    { label: '10 miles', value: 16094 },
    { label: '15 miles', value: 24140 },
    { label: '25 miles', value: 40234 },
  ];

  useEffect(() => {
    getCurrentLocation();
    loadSpecialTypes();
  }, []);

  // Get current location
  const getCurrentLocation = async () => {
    try {
      if (Platform.OS === 'android') {
        const granted = await PermissionsAndroid.request(
          PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION
        );
        if (granted !== PermissionsAndroid.RESULTS.GRANTED) {
          Alert.alert('Permission denied', 'Location permission is required to find nearby restaurants');
          return;
        }
      }

      Geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          setLocation({ latitude, longitude });
          
          // Auto-search nearby restaurants
          searchNearbyRestaurants(latitude, longitude);
        },
        (error) => {
          console.error('Location error:', error);
          Alert.alert('Location Error', 'Could not get your current location. Please enter an address to search.');
        },
        { enableHighAccuracy: true, timeout: 15000, maximumAge: 10000 }
      );
    } catch (error) {
      console.error('Location permission error:', error);
    }
  };

  // Load special types
  const loadSpecialTypes = async () => {
    try {
      const types = await APIService.getSpecialTypes();
      setSpecialTypes(types);
    } catch (error) {
      console.error('Error loading special types:', error);
    }
  };

  // Search nearby restaurants
  const searchNearbyRestaurants = async (lat?: number, lng?: number) => {
    if (!lat && !location) {
      Alert.alert('Location Required', 'Please enable location or enter an address');
      return;
    }

    setLoading(true);
    try {
      const searchParams = {
        latitude: lat || location!.latitude,
        longitude: lng || location!.longitude,
        radius: selectedRadius, // Use selected radius instead of hardcoded 25km
        special_type: selectedSpecialType !== 'all' ? selectedSpecialType : undefined,
        vendor_type: selectedVendorType !== 'all' ? selectedVendorType : undefined,
      };

      const result = await APIService.searchRestaurants(searchParams);
      setRestaurants(result.restaurants || []);
      
      console.log(`Found ${result.restaurants?.length || 0} restaurants within ${formatDistance(selectedRadius)}`);
    } catch (error) {
      console.error('Search error:', error);
      Alert.alert('Search Error', 'Could not search for restaurants. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Search by address
  const searchByAddress = async () => {
    if (!searchQuery.trim()) {
      Alert.alert('Search Required', 'Please enter a city or address');
      return;
    }

    setLoading(true);
    try {
      // First geocode the address
      const geocodeResult = await APIService.geocodeAddress(searchQuery);
      
      if (geocodeResult.results && geocodeResult.results.length > 0) {
        const { lat, lng } = geocodeResult.results[0].geometry.location;
        setLocation({ latitude: lat, longitude: lng });
        
        // Then search restaurants
        await searchNearbyRestaurants(lat, lng);
      } else {
        Alert.alert('Address Not Found', 'Could not find the specified address');
      }
    } catch (error) {
      console.error('Address search error:', error);
      Alert.alert('Search Error', 'Could not search by address. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Refresh data
  const onRefresh = async () => {
    setRefreshing(true);
    if (location) {
      await searchNearbyRestaurants();
    } else {
      await getCurrentLocation();
    }
    setRefreshing(false);
  };

  return (
    <ScrollView 
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      <View style={styles.searchSection}>
        <Searchbar
          placeholder="Enter city or address"
          onChangeText={setSearchQuery}
          value={searchQuery}
          onSubmitEditing={searchByAddress}
          style={styles.searchbar}
        />
        
        <View style={styles.buttonRow}>
          <Button
            mode="contained"
            onPress={searchByAddress}
            style={styles.searchButton}
            disabled={loading}
          >
            Search Area
          </Button>
          
          <Button
            mode="outlined"
            onPress={getCurrentLocation}
            style={styles.locationButton}
            disabled={loading}
          >
            <Icon name="crosshairs-gps" size={16} />
            Near Me
          </Button>
        </View>

        {/* Filter chips */}
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.filterSection}>
          <Chip
            selected={selectedVendorType === 'all'}
            onPress={() => setSelectedVendorType('all')}
            style={styles.filterChip}
          >
            All Venues
          </Chip>
          <Chip
            selected={selectedVendorType === 'permanent'}
            onPress={() => setSelectedVendorType('permanent')}
            style={styles.filterChip}
          >
            Restaurants
          </Chip>
          <Chip
            selected={selectedVendorType === 'mobile'}
            onPress={() => setSelectedVendorType('mobile')}
            style={styles.filterChip}
          >
            Food Trucks
          </Chip>
        </ScrollView>
      </View>

      {/* Loading indicator */}
      {loading && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Finding restaurants...</Text>
        </View>
      )}

      {/* Results */}
      {!loading && restaurants.length > 0 && (
        <View style={styles.resultsSection}>
          <Text style={styles.resultsTitle}>
            Found {restaurants.length} restaurant{restaurants.length !== 1 ? 's' : ''}
          </Text>
          
          {restaurants.map((restaurant) => (
            <RestaurantCard
              key={restaurant.id}
              restaurant={restaurant}
              onPress={() => navigation.navigate('RestaurantDetail', { restaurant })}
            />
          ))}
        </View>
      )}

      {/* No results */}
      {!loading && restaurants.length === 0 && location && (
        <View style={styles.noResultsContainer}>
          <Icon name="silverware-fork-knife" size={64} color={colors.textLight} />
          <Text style={styles.noResultsTitle}>No restaurants found</Text>
          <Text style={styles.noResultsText}>
            Try expanding your search area or removing filters
          </Text>
          <Button
            mode="outlined"
            onPress={() => searchNearbyRestaurants()}
            style={styles.retryButton}
          >
            Search Again
          </Button>
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  searchSection: {
    padding: spacing.md,
    backgroundColor: colors.surface,
  },
  searchbar: {
    marginBottom: spacing.sm,
  },
  buttonRow: {
    flexDirection: 'row',
    marginBottom: spacing.sm,
    gap: spacing.sm,
  },
  searchButton: {
    flex: 1,
  },
  locationButton: {
    flex: 1,
  },
  filterSection: {
    marginBottom: spacing.sm,
  },
  filterChip: {
    marginRight: spacing.sm,
  },
  loadingContainer: {
    padding: spacing.xl,
    alignItems: 'center',
  },
  loadingText: {
    marginTop: spacing.sm,
    color: colors.textLight,
  },
  resultsSection: {
    padding: spacing.md,
  },
  resultsTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: colors.textDark,
    marginBottom: spacing.md,
  },
  noResultsContainer: {
    padding: spacing.xl,
    alignItems: 'center',
  },
  noResultsTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.textDark,
    marginTop: spacing.md,
    marginBottom: spacing.sm,
  },
  noResultsText: {
    color: colors.textLight,
    textAlign: 'center',
    marginBottom: spacing.lg,
  },
  retryButton: {
    marginTop: spacing.sm,
  },
});

export default HomeScreen;