#!/bin/bash
echo "Setting up On-the-Cheap Mobile App..."

mkdir -p src/services src/screens src/components src/navigation src/theme

cat > src/services/APIService.js << 'EOF'
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

class APIService {
  constructor() {
    this.baseURL = 'https://eatdeals-mobile.preview.emergentagent.com/api';
    this.api = axios.create({ baseURL: this.baseURL, timeout: 15000 });
    this.api.interceptors.request.use(async (config) => {
      const token = await AsyncStorage.getItem('auth_token');
      if (token) config.headers.Authorization = 'Bearer ' + token;
      return config;
    });
  }

  async searchRestaurants(params) {
    const response = await this.api.get('/restaurants/search', { params });
    return response.data;
  }

  async geocodeAddress(address) {
    const response = await this.api.get('/geocode', { params: { address } });
    return response.data;
  }

  async forwardGeocode(address) {
    const response = await this.api.get('/geocode', { params: { address } });
    if (response.data && response.data.coordinates) {
      return { latitude: response.data.coordinates.latitude, longitude: response.data.coordinates.longitude, formatted_address: response.data.formatted_address };
    }
    throw new Error('Geocode failed');
  }

  async login(email, password) {
    const response = await this.api.post('/users/login', { email, password });
    await AsyncStorage.setItem('auth_token', response.data.access_token);
    await AsyncStorage.setItem('user_data', JSON.stringify(response.data.user));
    return response.data;
  }

  async register(userData) {
    const response = await this.api.post('/users/register', userData);
    await AsyncStorage.setItem('auth_token', response.data.access_token);
    await AsyncStorage.setItem('user_data', JSON.stringify(response.data.user));
    return response.data;
  }

  async getFavorites() {
    const response = await this.api.get('/users/favorites');
    return response.data;
  }

  async getCurrentUser() {
    const userData = await AsyncStorage.getItem('user_data');
    return userData ? JSON.parse(userData) : null;
  }

  async logout() {
    await AsyncStorage.multiRemove(['auth_token', 'user_data']);
  }

  async isAuthenticated() {
    const token = await AsyncStorage.getItem('auth_token');
    return !!token;
  }

  async getNearbyCoupons(latitude, longitude, radius) {
    const response = await this.api.get('/coupons/near', { params: { latitude, longitude, radius: radius || 16094 } });
    return response.data;
  }

  async getSavedCoupons() {
    const response = await this.api.get('/users/coupons/saved');
    return response.data;
  }

  async saveCoupon(couponId) {
    const response = await this.api.post('/users/coupons/' + couponId + '/save');
    return response.data;
  }

  async removeSavedCoupon(couponId) {
    const response = await this.api.delete('/users/coupons/' + couponId + '/save');
    return response.data;
  }
}

export default new APIService();
EOF

cat > src/theme/colors.js << 'EOF'
import { DefaultTheme } from 'react-native-paper';

export const colors = {
  primary: '#ea580c',
  primaryLight: '#fb923c',
  background: '#fef3c7',
  surface: '#ffffff',
  accent: '#dc2626',
  text: '#374151',
  textLight: '#6b7280',
  textDark: '#111827',
  border: '#d1d5db',
  success: '#059669',
  warning: '#d97706',
  error: '#dc2626',
  foodTruck: '#f59e0b',
};

export const theme = {
  ...DefaultTheme,
  colors: { ...DefaultTheme.colors, primary: colors.primary, accent: colors.accent, background: colors.background, surface: colors.surface, text: colors.text },
};

export const spacing = { xs: 4, sm: 8, md: 16, lg: 24, xl: 32 };
export const borderRadius = { sm: 4, md: 8, lg: 12 };
EOF

cat > src/screens/HomeScreen.js << 'EOF'
import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, StyleSheet, RefreshControl, Alert } from 'react-native';
import { Searchbar, Button, Card, Title, Chip, ActivityIndicator, Menu } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import * as Location from 'expo-location';
import APIService from '../services/APIService';
import RestaurantCard from '../components/RestaurantCard';
import { colors, spacing } from '../theme/colors';

const HomeScreen = ({ navigation }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [location, setLocation] = useState(null);
  const [lastSearchLocation, setLastSearchLocation] = useState('');
  const [selectedRadius, setSelectedRadius] = useState(16094);
  const [selectedVendorType, setSelectedVendorType] = useState('all');
  const [radiusMenuVisible, setRadiusMenuVisible] = useState(false);

  const radiusOptions = [
    { label: '5 miles', value: 8047 },
    { label: '10 miles', value: 16094 },
    { label: '20 miles', value: 32187 },
    { label: '50 miles', value: 80467 },
  ];

  const vendorTypes = [
    { label: 'All', value: 'all', icon: 'silverware-fork-knife' },
    { label: 'Restaurants', value: 'restaurant', icon: 'silverware-variant' },
    { label: 'Food Trucks', value: 'mobile', icon: 'truck' },
    { label: 'Bars', value: 'bar', icon: 'glass-cocktail' },
    { label: 'Pop-ups', value: 'popup', icon: 'party-popper' },
  ];

  const getCurrentLocation = async () => {
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') return;
      const position = await Location.getCurrentPositionAsync({});
      setLocation(position.coords);
      await searchNearbyRestaurants(position.coords.latitude, position.coords.longitude);
    } catch (error) {
      console.log('Location error');
    }
  };

  const searchNearbyRestaurants = async (lat, lng) => {
    if (!lat) return;
    setLoading(true);
    try {
      const params = { latitude: lat, longitude: lng, radius: selectedRadius };
      if (selectedVendorType !== 'all') params.vendor_type = selectedVendorType;
      const result = await APIService.searchRestaurants(params);
      setRestaurants(result.restaurants || []);
      setLastSearchLocation('your location');
    } catch (error) {
      console.log('Search error');
    } finally {
      setLoading(false);
    }
  };

  const searchByAddress = async () => {
    if (!searchQuery.trim()) { Alert.alert('Error', 'Please enter a city or address'); return; }
    setLoading(true);
    try {
      const geocodeResult = await APIService.forwardGeocode(searchQuery);
      if (geocodeResult && geocodeResult.latitude) {
        setLocation({ latitude: geocodeResult.latitude, longitude: geocodeResult.longitude });
        setLastSearchLocation(geocodeResult.formatted_address || searchQuery);
        await searchNearbyRestaurants(geocodeResult.latitude, geocodeResult.longitude);
      } else {
        Alert.alert('Not Found', 'Could not find that location');
      }
    } catch (error) {
      Alert.alert('Error', 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const applyFilters = () => { if (location) searchNearbyRestaurants(location.latitude, location.longitude); };
  const onRefresh = async () => { setRefreshing(true); if (location) await searchNearbyRestaurants(location.latitude, location.longitude); setRefreshing(false); };

  return (
    <ScrollView style={styles.container} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}>
      <View style={styles.searchSection}>
        <Card style={styles.card}>
          <Card.Content>
            <Title>Find Restaurant Specials</Title>
            <Text style={styles.subtitle}>Search by city or use your location</Text>
            <Searchbar placeholder="Enter city, state" value={searchQuery} onChangeText={setSearchQuery} onSubmitEditing={searchByAddress} style={styles.searchbar} />
            <View style={styles.buttonRow}>
              <Button mode="outlined" onPress={getCurrentLocation} disabled={loading} icon="crosshairs-gps" style={styles.button}>Near Me</Button>
              <Button mode="contained" onPress={searchByAddress} disabled={loading} style={styles.button}>Search</Button>
            </View>
          </Card.Content>
        </Card>
        <Card style={styles.card}>
          <Card.Content>
            <Title style={styles.filterTitle}>Filters</Title>
            <Text style={styles.filterLabel}>Distance</Text>
            <Menu visible={radiusMenuVisible} onDismiss={() => setRadiusMenuVisible(false)} anchor={<Button mode="outlined" onPress={() => setRadiusMenuVisible(true)} icon="map-marker-distance">{radiusOptions.find(o => o.value === selectedRadius)?.label || '10 miles'}</Button>}>
              {radiusOptions.map((option) => (<Menu.Item key={option.value} onPress={() => { setSelectedRadius(option.value); setRadiusMenuVisible(false); }} title={option.label} />))}
            </Menu>
            <Text style={[styles.filterLabel, { marginTop: 16 }]}>Venue Type</Text>
            <View style={styles.chipRow}>
              {vendorTypes.map((type) => (<Chip key={type.value} selected={selectedVendorType === type.value} onPress={() => setSelectedVendorType(type.value)} style={styles.chip} icon={type.icon}>{type.label}</Chip>))}
            </View>
            <Button mode="contained" onPress={applyFilters} style={styles.applyButton} disabled={!location} icon="filter">Apply Filters</Button>
          </Card.Content>
        </Card>
      </View>
      {loading && (<View style={styles.loadingContainer}><ActivityIndicator size="large" color={colors.primary} /><Text style={styles.loadingText}>Finding restaurants...</Text></View>)}
      {!loading && restaurants.length > 0 && (<View style={styles.resultsSection}><Text style={styles.resultsTitle}>Found {restaurants.length} restaurants near {lastSearchLocation}</Text>{restaurants.map((restaurant) => (<RestaurantCard key={restaurant.id} restaurant={restaurant} onPress={() => navigation.navigate('RestaurantDetail', { restaurant })} />))}</View>)}
      {!loading && restaurants.length === 0 && (<View style={styles.welcomeContainer}><Icon name="silverware-fork-knife" size={80} color={colors.primary} /><Text style={styles.welcomeTitle}>Welcome to On-the-Cheap!</Text><Text style={styles.welcomeText}>Enter a location or tap Near Me</Text></View>)}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  searchSection: { padding: 16 },
  card: { marginBottom: 16 },
  subtitle: { color: colors.textLight, marginBottom: 16 },
  searchbar: { marginBottom: 16 },
  buttonRow: { flexDirection: 'row', gap: 8 },
  button: { flex: 1 },
  filterTitle: { fontSize: 18, marginBottom: 8 },
  filterLabel: { fontSize: 14, fontWeight: '600', marginBottom: 4 },
  chipRow: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { marginBottom: 4 },
  applyButton: { marginTop: 16 },
  loadingContainer: { padding: 32, alignItems: 'center' },
  loadingText: { marginTop: 8, color: colors.textLight },
  resultsSection: { padding: 16 },
  resultsTitle: { fontSize: 16, fontWeight: '600', marginBottom: 16 },
  welcomeContainer: { alignItems: 'center', padding: 32, marginTop: 50 },
  welcomeTitle: { fontSize: 24, fontWeight: 'bold', marginTop: 24, textAlign: 'center' },
  welcomeText: { fontSize: 16, color: colors.textLight, textAlign: 'center', marginTop: 8 },
});

export default HomeScreen;
EOF

cat > src/screens/LoginScreen.js << 'EOF'
import React, { useState } from 'react';
import { View, Text, StyleSheet, Alert, ScrollView, KeyboardAvoidingView, Platform } from 'react-native';
import { Card, Title, TextInput, Button } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import APIService from '../services/APIService';
import { colors } from '../theme/colors';

const LoginScreen = ({ navigation, route }) => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPassword, setShowPassword] = useState(false);

  const handleLogin = async () => {
    if (!email.trim() || !password) { Alert.alert('Error', 'Please enter email and password'); return; }
    setLoading(true);
    try {
      const response = await APIService.login(email.trim().toLowerCase(), password);
      Alert.alert('Success', 'Login successful!', [{ text: 'OK', onPress: () => { if (route?.params?.onLoginSuccess) route.params.onLoginSuccess(response.user); navigation.goBack(); }}]);
    } catch (error) {
      Alert.alert('Login Error', error.response?.data?.detail || 'Invalid email or password');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView contentContainerStyle={styles.scrollContainer} keyboardShouldPersistTaps="handled">
        <View style={styles.header}>
          <Icon name="silverware-fork-knife" size={64} color={colors.primary} />
          <Title style={styles.title}>Welcome Back!</Title>
          <Text style={styles.subtitle}>Sign in to find amazing deals</Text>
        </View>
        <Card style={styles.card}>
          <Card.Content>
            <TextInput label="Email" value={email} onChangeText={setEmail} mode="outlined" keyboardType="email-address" autoCapitalize="none" autoCorrect={false} style={styles.input} disabled={loading} />
            <TextInput label="Password" value={password} onChangeText={setPassword} mode="outlined" secureTextEntry={!showPassword} style={styles.input} disabled={loading} right={<TextInput.Icon icon={showPassword ? "eye-off" : "eye"} onPress={() => setShowPassword(!showPassword)} />} />
            <Button mode="contained" onPress={handleLogin} disabled={loading} style={styles.button}>{loading ? 'Signing in...' : 'Sign In'}</Button>
            <Text style={styles.dividerText}>Don't have an account?</Text>
            <Button mode="outlined" onPress={() => navigation.navigate('Register')} disabled={loading}>Create Account</Button>
          </Card.Content>
        </Card>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  scrollContainer: { flexGrow: 1, justifyContent: 'center', padding: 24 },
  header: { alignItems: 'center', marginBottom: 32 },
  title: { fontSize: 28, fontWeight: 'bold', marginTop: 16 },
  subtitle: { color: colors.textLight, marginTop: 8 },
  card: { elevation: 4 },
  input: { marginBottom: 16 },
  button: { marginTop: 8, marginBottom: 24 },
  dividerText: { textAlign: 'center', color: colors.textLight, marginBottom: 16 },
});

export default LoginScreen;
EOF

cat > src/screens/MapScreen.js << 'EOF'
import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, StyleSheet, RefreshControl, Linking } from 'react-native';
import { Card, Button, ActivityIndicator, Title, List, Divider } from 'react-native-paper';
import * as Location from 'expo-location';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import APIService from '../services/APIService';
import { colors } from '../theme/colors';

const MapScreen = ({ navigation }) => {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [location, setLocation] = useState(null);
  const [restaurants, setRestaurants] = useState([]);
  const [error, setError] = useState(null);

  useEffect(() => { loadData(); }, []);

  const loadData = async () => {
    setLoading(true);
    setError(null);
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') { setError('Location permission required'); setLoading(false); return; }
      const position = await Location.getCurrentPositionAsync({});
      setLocation(position.coords);
      const result = await APIService.searchRestaurants({ latitude: position.coords.latitude, longitude: position.coords.longitude, radius: 25000 });
      setRestaurants(result.restaurants || []);
    } catch (err) {
      setError('Could not load restaurants');
    } finally {
      setLoading(false);
    }
  };

  const onRefresh = async () => { setRefreshing(true); await loadData(); setRefreshing(false); };

  const openInMaps = (restaurant) => {
    const lat = restaurant.location?.latitude || restaurant.latitude;
    const lng = restaurant.location?.longitude || restaurant.longitude;
    if (lat && lng) Linking.openURL('https://www.google.com/maps/search/?api=1&query=' + lat + ',' + lng);
    else Linking.openURL('https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(restaurant.address));
  };

  if (loading) return (<View style={styles.centerContainer}><ActivityIndicator size="large" color={colors.primary} /><Text style={styles.loadingText}>Finding restaurants...</Text></View>);
  if (error) return (<View style={styles.centerContainer}><Icon name="alert-circle-outline" size={64} color={colors.error} /><Text style={styles.errorText}>{error}</Text><Button mode="contained" onPress={loadData} style={styles.retryButton}>Try Again</Button></View>);

  return (
    <ScrollView style={styles.container} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={onRefresh} />}>
      <Card style={styles.card}>
        <Card.Content style={styles.headerContent}>
          <Icon name="map-marker-radius" size={48} color={colors.primary} />
          <Title style={styles.title}>Nearby Restaurants</Title>
          <Text style={styles.subtitle}>{restaurants.length} restaurants found</Text>
          <Button mode="contained" onPress={() => location && Linking.openURL('https://www.google.com/maps/search/restaurants/@' + location.latitude + ',' + location.longitude + ',13z')} icon="google-maps" style={styles.mapButton}>Open in Google Maps</Button>
        </Card.Content>
      </Card>
      {restaurants.length > 0 && (
        <Card style={styles.card}>
          <Card.Content>
            {restaurants.slice(0, 20).map((restaurant, index) => (
              <React.Fragment key={restaurant.id || index}>
                <List.Item title={restaurant.name} description={restaurant.address} left={(props) => <List.Icon {...props} icon="silverware-fork-knife" color={colors.primary} />} right={() => <Button mode="text" onPress={() => openInMaps(restaurant)} compact><Icon name="directions" size={20} color={colors.primary} /></Button>} onPress={() => navigation.navigate('RestaurantDetail', { restaurant })} />
                {index < restaurants.length - 1 && <Divider />}
              </React.Fragment>
            ))}
          </Card.Content>
        </Card>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  centerContainer: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: colors.background, padding: 24 },
  loadingText: { marginTop: 16, color: colors.textLight },
  errorText: { marginTop: 16, color: colors.error, textAlign: 'center' },
  retryButton: { marginTop: 24 },
  card: { margin: 16, marginBottom: 8 },
  headerContent: { alignItems: 'center', paddingVertical: 24 },
  title: { fontSize: 24, fontWeight: 'bold', marginTop: 16 },
  subtitle: { color: colors.textLight, marginTop: 4, marginBottom: 16 },
  mapButton: { marginTop: 8 },
});

export default MapScreen;
EOF

echo "Setup complete! Now run: eas build --profile preview --platform android"
