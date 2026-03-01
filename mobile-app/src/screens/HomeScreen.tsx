import React, { useState, useEffect, useCallback } from 'react';
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
  SegmentedButtons,
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import * as Location from 'expo-location';

import APIService from '../services/APIService';
import RestaurantCard from '../components/RestaurantCard';
import RestaurantMapView from '../components/RestaurantMapView';
import AddressInput from '../components/AddressInput';
import { colors, spacing } from '../theme/colors';
import { Restaurant, SearchParams } from '../types/restaurant';

const HomeScreen = ({ navigation }: any) => {
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
  const [viewMode, setViewMode] = useState<'list' | 'map'>('list');
  
  // Favorites state
  const [favorites, setFavorites] = useState<Set<string>>(new Set());
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  
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
    checkAuthAndLoadFavorites();
  }, []);

  // Check authentication and load favorites
  const checkAuthAndLoadFavorites = async () => {
    try {
      const authenticated = await APIService.isAuthenticated();
      setIsAuthenticated(authenticated);
      if (authenticated) {
        await loadFavorites();
      }
    } catch (error) {
      console.error('Auth check error:', error);
    }
  };

  // Load user's favorites
  const loadFavorites = async () => {
    try {
      const response = await APIService.getFavorites();
      const favoriteIds = new Set(
        (response.favorites || []).map((fav: any) => fav.id || fav.restaurant_id)
      );
      setFavorites(favoriteIds);
      console.log('📍 Loaded favorites:', favoriteIds.size);
    } catch (error) {
      console.error('Load favorites error:', error);
    }
  };

  // Toggle favorite
  const toggleFavorite = useCallback(async (restaurantId: string) => {
    if (!isAuthenticated) {
      Alert.alert('Login Required', 'Please log in to save favorites');
      return;
    }
    
    const isFavorite = favorites.has(restaurantId);
    
    // Optimistic update
    setFavorites(prev => {
      const newSet = new Set(prev);
      if (isFavorite) {
        newSet.delete(restaurantId);
      } else {
        newSet.add(restaurantId);
      }
      return newSet;
    });
    
    try {
      await APIService.toggleFavorite(restaurantId, isFavorite);
      console.log(`❤️ Favorite ${isFavorite ? 'removed' : 'added'}: ${restaurantId}`);
    } catch (error: any) {
      // Revert on failure
      setFavorites(prev => {
        const newSet = new Set(prev);
        if (isFavorite) {
          newSet.add(restaurantId);
        } else {
          newSet.delete(restaurantId);
        }
        return newSet;
      });
      console.error('Toggle favorite error:', error);
      Alert.alert('Error', error.response?.data?.detail || 'Failed to update favorite');
    }
  }, [isAuthenticated, favorites]);

  // Get current location using expo-location
  const getCurrentLocation = async () => {
    try {
      // Request permission
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') {
        Alert.alert('Permission denied', 'Location permission is required to find nearby restaurants');
        return;
      }

      const position = await Location.getCurrentPositionAsync({
        accuracy: Location.Accuracy.High,
      });
      
      const { latitude, longitude } = position.coords;
      setLocation({ latitude, longitude });
      setLastSearchLocation('Current Location');
      
      // Auto-search nearby restaurants
      searchNearbyRestaurants(latitude, longitude);
    } catch (error) {
      console.error('Location error:', error);
      Alert.alert('Location Error', 'Could not get your current location. Please enter an address to search.');
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
      console.log('🍽️ Restaurant search result:', result.restaurants?.length || 0, 'restaurants found');
      setRestaurants(result.restaurants || []);
      
      // Debug: Log photos for first restaurant
      if (result.restaurants && result.restaurants.length > 0) {
        const firstRestaurant = result.restaurants[0];
        console.log('📸 First restaurant photos:', firstRestaurant.photos?.length || 0, 'photos');
        console.log('📸 First photo URL:', firstRestaurant.photos?.[0]?.url);
        console.log('🏪 First restaurant data keys:', Object.keys(firstRestaurant));
      }
      
      console.log(`Found ${result.restaurants?.length || 0} restaurants within ${formatDistance(selectedRadius)}`);
      console.log('Restaurants array:', result.restaurants?.length || 0, 'total restaurants');
      console.log('First restaurant structure:', result.restaurants?.[0] ? Object.keys(result.restaurants[0]) : 'No restaurants');
    } catch (error) {
      console.error('Search error:', error);
      Alert.alert('Search Error', 'Could not search for restaurants. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  // Search by address
  const searchByAddress = async () => {
    if (!searchLocation.trim()) {
      Alert.alert('Search Required', 'Please enter a city or address');
      return;
    }

    setLoading(true);
    try {
      // First geocode the address
      const geocodeResult = await APIService.geocodeAddress(searchLocation);
      
      if (geocodeResult.coordinates) {
        const { latitude, longitude } = geocodeResult.coordinates;
        setLocation({ latitude, longitude });
        setLastSearchLocation(geocodeResult.formatted_address || searchLocation);
        
        // Then search restaurants
        await searchNearbyRestaurants(latitude, longitude);
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

  // Handle address selection from AddressInput component
  const handleAddressSelect = (result: any) => {
    setSearchLocation(result.formatted_address);
    setLocation({ latitude: result.latitude, longitude: result.longitude });
    setLastSearchLocation(result.formatted_address);
    setLoading(true);
    searchNearbyRestaurants(result.latitude, result.longitude);
  };

  // Handle address query change (for enabling Search button)
  const handleAddressQueryChange = (query: string) => {
    setSearchLocation(query);
  };

  // Format distance helper
  const formatDistance = (meters: number): string => {
    const miles = meters * 0.000621371;
    if (miles < 1) {
      return `${Math.round(miles * 5280)} ft`;
    }
    return `${miles.toFixed(1)} mi`;
  };

  // Clear search and reset state
  const clearSearch = () => {
    setRestaurants([]);
    setSearchLocation('');
    setLastSearchLocation('');
    // Don't reset location - keep it so user can search again
    setSelectedSpecialType('all');
    setSelectedVendorType('all');
    setSelectedRadius(25000);
  };

  // Format special type label
  const getSpecialTypeLabel = (value: string): string => {
    const specialType = specialTypes.find(st => st.value === value);
    return specialType ? specialType.label : value.replace('_', ' ');
  };

  // Format radius label
  const getRadiusLabel = (meters: number): string => {
    const option = radiusOptions.find(opt => opt.value === meters);
    return option ? option.label : formatDistance(meters);
  };

  // Refresh data
  const onRefresh = async () => {
    setRefreshing(true);
    // Refresh auth state and favorites
    await checkAuthAndLoadFavorites();
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
        <Card style={styles.searchCard}>
          <Card.Content>
            <Title style={styles.searchTitle}>Find Restaurant Specials</Title>
            <Paragraph style={styles.searchSubtitle}>
              Search by location or use your current position
            </Paragraph>
            
            {/* Enhanced Address Input with Search Button */}
            <View style={styles.addressSearchRow}>
              <View style={styles.addressInputWrapper}>
                <AddressInput
                  placeholder="Enter city or address (e.g., San Francisco, New York)"
                  onAddressSelect={handleAddressSelect}
                  onQueryChange={handleAddressQueryChange}
                  initialValue={searchLocation}
                  region="US"
                  style={styles.addressInput}
                />
              </View>
              <Button
                mode="contained"
                onPress={searchByAddress}
                style={styles.searchButton}
                disabled={loading || !searchLocation.trim()}
                icon="magnify"
                compact
              >
                Search
              </Button>
            </View>
            
            <View style={styles.buttonRow}>
              <Button
                mode="outlined"
                onPress={getCurrentLocation}
                style={styles.locationButton}
                disabled={loading}
                icon="crosshairs-gps"
              >
                Near Me
              </Button>
              
              {restaurants.length > 0 && (
                <Button
                  mode="outlined"
                  onPress={clearSearch}
                  style={styles.clearButton}
                  disabled={loading}
                  icon="close"
                >
                  Clear
                </Button>
              )}
            </View>
          </Card.Content>
        </Card>

        {/* Advanced Filters */}
        <Card style={styles.filtersCard}>
          <Card.Content>
            <Title style={styles.filtersTitle}>Filters</Title>
            
            {/* Vendor Type Filter */}
            <View style={styles.filterSection}>
              <Text style={styles.filterLabel}>Venue Type</Text>
              <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.chipRow}>
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
                  🚛 Food Trucks
                </Chip>
              </ScrollView>
            </View>

            {/* Special Type Filter */}
            <View style={styles.filterSection}>
              <Text style={styles.filterLabel}>Special Type</Text>
              <Menu
                visible={specialTypeMenuVisible}
                onDismiss={() => setSpecialTypeMenuVisible(false)}
                anchor={
                  <Button
                    mode="outlined"
                    onPress={() => setSpecialTypeMenuVisible(true)}
                    style={styles.dropdownButton}
                    contentStyle={styles.dropdownContent}
                  >
                    {selectedSpecialType === 'all' ? 'All Specials' : getSpecialTypeLabel(selectedSpecialType)}
                    <Icon name="chevron-down" size={16} />
                  </Button>
                }
              >
                <Menu.Item 
                  onPress={() => {
                    setSelectedSpecialType('all');
                    setSpecialTypeMenuVisible(false);
                  }} 
                  title="All Specials" 
                />
                <Divider />
                {specialTypes.map((type) => (
                  <Menu.Item
                    key={type.value}
                    onPress={() => {
                      setSelectedSpecialType(type.value);
                      setSpecialTypeMenuVisible(false);
                    }}
                    title={type.label}
                  />
                ))}
              </Menu>
            </View>

            {/* Radius Filter */}
            <View style={styles.filterSection}>
              <Text style={styles.filterLabel}>Search Radius</Text>
              <Menu
                visible={radiusMenuVisible}
                onDismiss={() => setRadiusMenuVisible(false)}
                anchor={
                  <Button
                    mode="outlined"
                    onPress={() => setRadiusMenuVisible(true)}
                    style={styles.dropdownButton}
                    contentStyle={styles.dropdownContent}
                  >
                    {getRadiusLabel(selectedRadius)}
                    <Icon name="chevron-down" size={16} />
                  </Button>
                }
              >
                {radiusOptions.map((option) => (
                  <Menu.Item
                    key={option.value}
                    onPress={() => {
                      setSelectedRadius(option.value);
                      setRadiusMenuVisible(false);
                    }}
                    title={option.label}
                  />
                ))}
              </Menu>
            </View>
          </Card.Content>
        </Card>
      </View>

      {/* Loading indicator */}
      {loading && (
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color={colors.primary} />
          <Text style={styles.loadingText}>Finding restaurants...</Text>
        </View>
      )}

      {/* Search Results Header */}
      {!loading && restaurants.length > 0 && lastSearchLocation && (
        <View style={styles.resultsHeader}>
          <Card style={styles.resultsCard}>
            <Card.Content>
              <View style={styles.resultsInfo}>
                <Icon name="map-marker" size={20} color={colors.primary} />
                <View style={styles.resultsText}>
                  <Text style={styles.resultsTitle}>
                    Found {restaurants.length} restaurant{restaurants.length !== 1 ? 's' : ''}
                  </Text>
                  <Text style={styles.resultsSubtitle}>
                    within {getRadiusLabel(selectedRadius)} of {lastSearchLocation}
                  </Text>
                </View>
              </View>
              
              {/* View Mode Toggle */}
              <View style={styles.viewToggleContainer}>
                <TouchableOpacity
                  style={[styles.viewToggleButton, viewMode === 'list' && styles.viewToggleActive]}
                  onPress={() => setViewMode('list')}
                >
                  <Icon 
                    name="format-list-bulleted" 
                    size={20} 
                    color={viewMode === 'list' ? '#fff' : colors.textDark} 
                  />
                  <Text style={[styles.viewToggleText, viewMode === 'list' && styles.viewToggleTextActive]}>
                    List
                  </Text>
                </TouchableOpacity>
                <TouchableOpacity
                  style={[styles.viewToggleButton, viewMode === 'map' && styles.viewToggleActive]}
                  onPress={() => setViewMode('map')}
                >
                  <Icon 
                    name="map" 
                    size={20} 
                    color={viewMode === 'map' ? '#fff' : colors.textDark} 
                  />
                  <Text style={[styles.viewToggleText, viewMode === 'map' && styles.viewToggleTextActive]}>
                    Map
                  </Text>
                </TouchableOpacity>
              </View>
            </Card.Content>
          </Card>
        </View>
      )}

      {/* Results - List View */}
      {!loading && restaurants.length > 0 && viewMode === 'list' && (
        <View style={styles.resultsSection}>          
          {restaurants.map((restaurant, index) => {
            console.log(`Rendering restaurant ${index}:`, restaurant.name, 'Photos:', restaurant.photos?.length || 0);
            return (
              <RestaurantCard
                key={restaurant.id}
                restaurant={restaurant}
                onPress={() => navigation.navigate('RestaurantDetail', { restaurant })}
                onToggleFavorite={toggleFavorite}
                isFavorite={favorites.has(restaurant.id)}
              />
            );
          })}
        </View>
      )}

      {/* Results - Map View */}
      {!loading && restaurants.length > 0 && viewMode === 'map' && (
        <View style={styles.mapContainer}>
          <RestaurantMapView
            restaurants={restaurants}
            userLocation={location}
            onRestaurantPress={(restaurant) => navigation.navigate('RestaurantDetail', { restaurant })}
          />
        </View>
      )}

      {/* No results */}
      {!loading && restaurants.length === 0 && lastSearchLocation && (
        <View style={styles.noResultsContainer}>
          <Card style={styles.noResultsCard}>
            <Card.Content style={styles.noResultsContent}>
              <Icon name="silverware-fork-knife" size={64} color={colors.textLight} />
              <Text style={styles.noResultsTitle}>No restaurants found</Text>
              <Text style={styles.noResultsText}>
                Try expanding your search radius or removing filters
              </Text>
              <Button
                mode="outlined"
                onPress={() => {
                  if (location) {
                    searchNearbyRestaurants();
                  }
                }}
                style={styles.retryButton}
              >
                Search Again
              </Button>
            </Card.Content>
          </Card>
        </View>
      )}

      {/* Welcome message */}
      {!loading && restaurants.length === 0 && !lastSearchLocation && (
        <View style={styles.welcomeContainer}>
          <Card style={styles.welcomeCard}>
            <Card.Content style={styles.welcomeContent}>
              <Icon name="silverware-fork-knife" size={80} color={colors.primary} />
              <Text style={styles.welcomeTitle}>Welcome to On-the-Cheap!</Text>
              <Text style={styles.welcomeText}>
                Enter a location or enable location services to discover amazing restaurant deals near you
              </Text>
            </Card.Content>
          </Card>
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
  },
  searchCard: {
    marginBottom: spacing.md,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  searchTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.textDark,
    marginBottom: spacing.xs,
  },
  searchSubtitle: {
    fontSize: 14,
    color: colors.textLight,
    marginBottom: spacing.md,
  },
  addressInput: {
    marginBottom: spacing.md,
  },
  addressSearchRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  addressInputWrapper: {
    flex: 1,
  },
  searchButton: {
    marginTop: 0,
    backgroundColor: colors.primary,
  },
  buttonRow: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  locationButton: {
    flex: 1,
    borderColor: colors.primary,
  },
  clearButton: {
    flex: 1,
    borderColor: colors.textLight,
  },
  filtersCard: {
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  filtersTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: colors.textDark,
    marginBottom: spacing.md,
  },
  filterSection: {
    marginBottom: spacing.md,
  },
  filterLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: colors.textDark,
    marginBottom: spacing.sm,
  },
  chipRow: {
    flexDirection: 'row',
  },
  filterChip: {
    marginRight: spacing.sm,
  },
  dropdownButton: {
    justifyContent: 'space-between',
    borderColor: colors.border,
  },
  dropdownContent: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  loadingContainer: {
    padding: spacing.xl,
    alignItems: 'center',
  },
  loadingText: {
    marginTop: spacing.sm,
    color: colors.textLight,
  },
  resultsHeader: {
    paddingHorizontal: spacing.md,
    paddingBottom: spacing.sm,
  },
  resultsCard: {
    elevation: 1,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 1,
  },
  resultsInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  resultsText: {
    marginLeft: spacing.sm,
    flex: 1,
  },
  resultsTitle: {
    fontSize: 16,
    fontWeight: 'bold',
    color: colors.textDark,
  },
  resultsSubtitle: {
    fontSize: 14,
    color: colors.textLight,
    marginTop: spacing.xs,
  },
  viewToggleContainer: {
    flexDirection: 'row',
    marginTop: spacing.md,
    backgroundColor: colors.background,
    borderRadius: 8,
    padding: 4,
  },
  viewToggleButton: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    paddingVertical: spacing.sm,
    paddingHorizontal: spacing.md,
    borderRadius: 6,
  },
  viewToggleActive: {
    backgroundColor: colors.primary,
  },
  viewToggleText: {
    marginLeft: spacing.xs,
    fontSize: 14,
    fontWeight: '600',
    color: colors.textDark,
  },
  viewToggleTextActive: {
    color: '#fff',
  },
  mapContainer: {
    height: 500,
    marginHorizontal: spacing.md,
    marginBottom: spacing.md,
    borderRadius: 12,
    overflow: 'hidden',
  },
  resultsSection: {
    padding: spacing.md,
    paddingTop: 0,
  },
  noResultsContainer: {
    padding: spacing.md,
  },
  noResultsCard: {
    elevation: 1,
  },
  noResultsContent: {
    alignItems: 'center',
    paddingVertical: spacing.xl,
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
    lineHeight: 20,
  },
  retryButton: {
    marginTop: spacing.sm,
  },
  welcomeContainer: {
    padding: spacing.md,
  },
  welcomeCard: {
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
  },
  welcomeContent: {
    alignItems: 'center',
    paddingVertical: spacing.xl,
  },
  welcomeTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: colors.textDark,
    marginTop: spacing.lg,
    marginBottom: spacing.md,
    textAlign: 'center',
  },
  welcomeText: {
    fontSize: 16,
    color: colors.textLight,
    textAlign: 'center',
    lineHeight: 22,
    paddingHorizontal: spacing.md,
  },
});

export default HomeScreen;