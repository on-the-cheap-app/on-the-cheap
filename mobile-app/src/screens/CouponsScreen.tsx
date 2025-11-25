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
  ActivityIndicator,
  SegmentedButtons,
  FAB,
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import Geolocation from 'react-native-geolocation-service';
import { PermissionsAndroid, Platform } from 'react-native';

import APIService from '../services/APIService';
import CouponCard from '../components/CouponCard';
import AddressInput from '../components/AddressInput';
import { colors, spacing } from '../theme/colors';
import { Coupon } from '../types/restaurant';

const CouponsScreen = ({ navigation }: any) => {
  const [coupons, setCoupons] = useState<Coupon[]>([]);
  const [savedCouponIds, setSavedCouponIds] = useState<string[]>([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [location, setLocation] = useState<{ latitude: number; longitude: number } | null>(null);
  const [searchLocation, setSearchLocation] = useState<string>('');
  const [viewMode, setViewMode] = useState<string>('discover');
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    checkAuthentication();
    getCurrentLocation();
  }, []); // Only run once on mount

  useEffect(() => {
    if (viewMode === 'saved' && isAuthenticated) {
      loadSavedCoupons();
    } else if (viewMode === 'discover' && location) {
      searchNearbyCoupons(location.latitude, location.longitude);
    }
  }, [viewMode]); // Only run when viewMode changes

  const checkAuthentication = async () => {
    const authenticated = await APIService.isAuthenticated();
    setIsAuthenticated(authenticated);
  };

  const getCurrentLocation = async () => {
    try {
      if (Platform.OS === 'android') {
        const granted = await PermissionsAndroid.request(
          PermissionsAndroid.PERMISSIONS.ACCESS_FINE_LOCATION
        );
        if (granted !== PermissionsAndroid.RESULTS.GRANTED) {
          Alert.alert('Permission denied', 'Location permission is required to find nearby coupons');
          return;
        }
      }

      Geolocation.getCurrentPosition(
        (position) => {
          const { latitude, longitude } = position.coords;
          setLocation({ latitude, longitude });
          searchNearbyCoupons(latitude, longitude);
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

  const searchNearbyCoupons = async (lat?: number, lng?: number) => {
    if (!lat && !location) {
      Alert.alert('Location Required', 'Please enable location or enter an address');
      return;
    }

    setLoading(true);
    try {
      const result = await APIService.getNearbyCoupons(
        lat || location!.latitude,
        lng || location!.longitude,
        16094 // 10 miles
      );
      
      console.log('🎟️ Found coupons:', result.coupons?.length || 0);
      setCoupons(result.coupons || []);
    } catch (error) {
      console.error('Error loading coupons:', error);
      Alert.alert('Error', 'Could not load coupons. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const loadSavedCoupons = async () => {
    if (!isAuthenticated) {
      Alert.alert('Login Required', 'Please login to view saved coupons', [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Login', onPress: () => navigation.navigate('Login') }
      ]);
      setViewMode('discover');
      return;
    }

    setLoading(true);
    try {
      const result = await APIService.getSavedCoupons();
      console.log('💾 Saved coupons:', result.coupons?.length || 0);
      setCoupons(result.coupons || []);
      setSavedCouponIds(result.coupons?.map((c: Coupon) => c.id) || []);
    } catch (error) {
      console.error('Error loading saved coupons:', error);
      Alert.alert('Error', 'Could not load saved coupons. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleAddressSelect = (result: any) => {
    setSearchLocation(result.formatted_address);
    setLocation({ latitude: result.latitude, longitude: result.longitude });
    searchNearbyCoupons(result.latitude, result.longitude);
  };

  const handleCouponPress = (coupon: Coupon) => {
    // Track view
    APIService.trackCouponView(coupon.id);
    navigation.navigate('CouponDetail', { coupon });
  };

  const handleSaveToggle = async (couponId: string, shouldSave: boolean) => {
    if (!isAuthenticated) {
      Alert.alert('Login Required', 'Please login to save coupons', [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Login', onPress: () => navigation.navigate('Login') }
      ]);
      return;
    }

    try {
      if (shouldSave) {
        await APIService.saveCoupon(couponId);
        setSavedCouponIds([...savedCouponIds, couponId]);
        Alert.alert('Success', 'Coupon saved to your collection!');
      } else {
        await APIService.removeSavedCoupon(couponId);
        setSavedCouponIds(savedCouponIds.filter(id => id !== couponId));
        
        // If in saved view, remove from list
        if (viewMode === 'saved') {
          setCoupons(coupons.filter(c => c.id !== couponId));
        }
      }
    } catch (error) {
      console.error('Error toggling coupon save:', error);
      Alert.alert('Error', 'Could not save coupon. Please try again.');
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    if (viewMode === 'saved') {
      await loadSavedCoupons();
    } else if (location) {
      await searchNearbyCoupons();
    } else {
      await getCurrentLocation();
    }
    setRefreshing(false);
  };

  return (
    <View style={styles.container}>
      {/* View Mode Toggle */}
      <View style={styles.segmentContainer}>
        <SegmentedButtons
          value={viewMode}
          onValueChange={setViewMode}
          buttons={[
            {
              value: 'discover',
              label: 'Discover',
              icon: 'compass',
            },
            {
              value: 'saved',
              label: 'Saved',
              icon: 'bookmark',
              disabled: !isAuthenticated,
            },
          ]}
          style={styles.segmentedButtons}
        />
      </View>

      <ScrollView
        style={styles.scrollView}
        refreshControl={
          <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
        }
      >
        {/* Search Section - Only in discover mode */}
        {viewMode === 'discover' && (
          <View style={styles.searchSection}>
            <Card style={styles.searchCard}>
              <Card.Content>
                <Title style={styles.searchTitle}>🎟️ Discover Coupons</Title>
                <Paragraph style={styles.searchSubtitle}>
                  Find amazing deals and save money at local restaurants
                </Paragraph>

                <AddressInput
                  placeholder="Enter city or address"
                  onAddressSelect={handleAddressSelect}
                  initialValue={searchLocation}
                  region="US"
                  style={styles.addressInput}
                />

                <Button
                  mode="outlined"
                  onPress={getCurrentLocation}
                  style={styles.locationButton}
                  disabled={loading}
                  icon="crosshairs-gps"
                >
                  Use My Location
                </Button>
              </Card.Content>
            </Card>
          </View>
        )}

        {/* Loading */}
        {loading && (
          <View style={styles.loadingContainer}>
            <ActivityIndicator size="large" color={colors.primary} />
            <Text style={styles.loadingText}>
              {viewMode === 'saved' ? 'Loading saved coupons...' : 'Finding coupons...'}
            </Text>
          </View>
        )}

        {/* Results Header */}
        {!loading && coupons.length > 0 && (
          <View style={styles.resultsHeader}>
            <Text style={styles.resultsCount}>
              {coupons.length} coupon{coupons.length !== 1 ? 's' : ''} {viewMode === 'saved' ? 'saved' : 'available'}
            </Text>
          </View>
        )}

        {/* Coupons List */}
        {!loading && coupons.length > 0 && (
          <View style={styles.couponsSection}>
            {coupons.map((coupon) => (
              <CouponCard
                key={coupon.id}
                coupon={coupon}
                onPress={() => handleCouponPress(coupon)}
                onSaveToggle={handleSaveToggle}
                isSaved={savedCouponIds.includes(coupon.id)}
              />
            ))}
          </View>
        )}

        {/* No Results */}
        {!loading && coupons.length === 0 && viewMode === 'discover' && location && (
          <View style={styles.noResultsContainer}>
            <Card style={styles.noResultsCard}>
              <Card.Content style={styles.noResultsContent}>
                <Icon name="ticket-percent" size={64} color={colors.textLight} />
                <Text style={styles.noResultsTitle}>No coupons found</Text>
                <Text style={styles.noResultsText}>
                  Try searching a different location or check back later for new deals
                </Text>
              </Card.Content>
            </Card>
          </View>
        )}

        {/* Empty Saved */}
        {!loading && coupons.length === 0 && viewMode === 'saved' && (
          <View style={styles.noResultsContainer}>
            <Card style={styles.noResultsCard}>
              <Card.Content style={styles.noResultsContent}>
                <Icon name="bookmark-outline" size={64} color={colors.textLight} />
                <Text style={styles.noResultsTitle}>No saved coupons yet</Text>
                <Text style={styles.noResultsText}>
                  Discover and save coupons to access them quickly later
                </Text>
                <Button
                  mode="contained"
                  onPress={() => setViewMode('discover')}
                  style={styles.discoverButton}
                >
                  Discover Coupons
                </Button>
              </Card.Content>
            </Card>
          </View>
        )}

        {/* Welcome */}
        {!loading && coupons.length === 0 && viewMode === 'discover' && !location && (
          <View style={styles.welcomeContainer}>
            <Card style={styles.welcomeCard}>
              <Card.Content style={styles.welcomeContent}>
                <Icon name="ticket-percent" size={80} color={colors.primary} />
                <Text style={styles.welcomeTitle}>Digital Coupons</Text>
                <Text style={styles.welcomeText}>
                  Save big at your favorite restaurants with exclusive digital coupons
                </Text>
              </Card.Content>
            </Card>
          </View>
        )}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  segmentContainer: {
    padding: spacing.md,
    paddingBottom: spacing.sm,
    backgroundColor: '#fff',
    borderBottomWidth: 1,
    borderBottomColor: colors.border,
  },
  segmentedButtons: {
    backgroundColor: colors.background,
  },
  scrollView: {
    flex: 1,
  },
  searchSection: {
    padding: spacing.md,
  },
  searchCard: {
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
  locationButton: {
    borderColor: colors.primary,
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
    paddingVertical: spacing.sm,
  },
  resultsCount: {
    fontSize: 16,
    fontWeight: '600',
    color: colors.textDark,
  },
  couponsSection: {
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
  discoverButton: {
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

export default CouponsScreen;
