#!/bin/bash
echo "=== Complete Mobile App Setup ==="

mkdir -p src/services src/screens src/components src/navigation src/theme

# APIService.js
cat > src/services/APIService.js << 'FILECONTENT'
import axios from 'axios';
import AsyncStorage from '@react-native-async-storage/async-storage';

class APIService {
  constructor() {
    this.baseURL = 'https://dealstack-5.preview.emergentagent.com/api';
    this.api = axios.create({ baseURL: this.baseURL, timeout: 15000 });
    this.api.interceptors.request.use(async (config) => {
      const token = await AsyncStorage.getItem('auth_token');
      if (token) config.headers.Authorization = 'Bearer ' + token;
      return config;
    });
  }
  async searchRestaurants(params) { const r = await this.api.get('/restaurants/search', { params }); return r.data; }
  async forwardGeocode(address) {
    const r = await this.api.get('/geocode', { params: { address } });
    if (r.data && r.data.coordinates) return { latitude: r.data.coordinates.latitude, longitude: r.data.coordinates.longitude, formatted_address: r.data.formatted_address };
    throw new Error('Geocode failed');
  }
  async login(email, password) {
    const r = await this.api.post('/users/login', { email, password });
    await AsyncStorage.setItem('auth_token', r.data.access_token);
    await AsyncStorage.setItem('user_data', JSON.stringify(r.data.user));
    return r.data;
  }
  async register(userData) {
    const r = await this.api.post('/users/register', userData);
    await AsyncStorage.setItem('auth_token', r.data.access_token);
    await AsyncStorage.setItem('user_data', JSON.stringify(r.data.user));
    return r.data;
  }
  async getFavorites() { const r = await this.api.get('/users/favorites'); return r.data; }
  async getCurrentUser() { const d = await AsyncStorage.getItem('user_data'); return d ? JSON.parse(d) : null; }
  async logout() { await AsyncStorage.multiRemove(['auth_token', 'user_data']); }
  async isAuthenticated() { const t = await AsyncStorage.getItem('auth_token'); return !!t; }
  async getNearbyCoupons(lat, lng, rad) { const r = await this.api.get('/coupons/near', { params: { latitude: lat, longitude: lng, radius: rad || 16094 } }); return r.data; }
  async getSavedCoupons() { const r = await this.api.get('/users/coupons/saved'); return r.data; }
  async saveCoupon(id) { const r = await this.api.post('/users/coupons/' + id + '/save'); return r.data; }
  async removeSavedCoupon(id) { const r = await this.api.delete('/users/coupons/' + id + '/save'); return r.data; }
}
export default new APIService();
FILECONTENT
echo "Created APIService.js"

# colors.js
cat > src/theme/colors.js << 'FILECONTENT'
import { DefaultTheme } from 'react-native-paper';
export const colors = { primary: '#ea580c', primaryLight: '#fb923c', background: '#fef3c7', surface: '#ffffff', accent: '#dc2626', text: '#374151', textLight: '#6b7280', textDark: '#111827', border: '#d1d5db', success: '#059669', warning: '#d97706', error: '#dc2626', foodTruck: '#f59e0b' };
export const theme = { ...DefaultTheme, colors: { ...DefaultTheme.colors, primary: colors.primary, accent: colors.accent, background: colors.background, surface: colors.surface, text: colors.text } };
export const spacing = { xs: 4, sm: 8, md: 16, lg: 24, xl: 32 };
export const borderRadius = { sm: 4, md: 8, lg: 12 };
FILECONTENT
echo "Created colors.js"

# OneSignalService.js
cat > src/services/OneSignalService.js << 'FILECONTENT'
class OneSignalService { initialize() {} }
export default new OneSignalService();
FILECONTENT
echo "Created OneSignalService.js"

# RestaurantCard.js
cat > src/components/RestaurantCard.js << 'FILECONTENT'
import React from 'react';
import { View, Text, StyleSheet, Image } from 'react-native';
import { Card, Title, Button } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { colors, spacing, borderRadius } from '../theme/colors';

const RestaurantCard = ({ restaurant, onPress }) => {
  const photo = restaurant.photos && restaurant.photos.length > 0 ? restaurant.photos[0] : null;
  const hasSpecials = restaurant.specials && restaurant.specials.length > 0;
  return (
    <Card style={styles.card} onPress={onPress}>
      {photo ? <Image source={{ uri: photo.url }} style={styles.photo} /> : <View style={styles.noPhoto}><Icon name="image-off" size={48} color={colors.textLight} /></View>}
      <Card.Content>
        <View style={styles.header}>
          <Title style={styles.title} numberOfLines={1}>{restaurant.name}</Title>
          {restaurant.is_mobile_vendor && <View style={styles.badge}><Icon name="truck" size={12} color="#fff" /><Text style={styles.badgeText}>Food Truck</Text></View>}
        </View>
        <View style={styles.row}><Icon name="map-marker" size={16} color={colors.textLight} /><Text style={styles.address} numberOfLines={1}>{restaurant.address}</Text></View>
        {restaurant.rating && <View style={styles.row}><Icon name="star" size={16} color={colors.warning} /><Text style={styles.rating}>{restaurant.rating.toFixed(1)}</Text></View>}
        <View style={styles.specialsRow}><Icon name={hasSpecials ? "tag-multiple" : "information-outline"} size={16} color={hasSpecials ? colors.success : colors.textLight} /><Text style={hasSpecials ? styles.specialsText : styles.noSpecials}>{hasSpecials ? restaurant.specials.length + ' special(s)' : 'No specials'}</Text></View>
        <Button mode="contained" onPress={onPress} style={styles.btn}>View Details</Button>
      </Card.Content>
    </Card>
  );
};
const styles = StyleSheet.create({
  card: { marginBottom: 16, borderRadius: 12, overflow: 'hidden' },
  photo: { width: '100%', height: 180 },
  noPhoto: { height: 180, backgroundColor: colors.background, justifyContent: 'center', alignItems: 'center' },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 },
  title: { flex: 1, fontSize: 18, fontWeight: 'bold' },
  badge: { flexDirection: 'row', alignItems: 'center', backgroundColor: colors.foodTruck, paddingHorizontal: 8, paddingVertical: 4, borderRadius: 4 },
  badgeText: { color: '#fff', fontSize: 12, marginLeft: 4 },
  row: { flexDirection: 'row', alignItems: 'center', marginBottom: 4 },
  address: { marginLeft: 4, color: colors.textLight, flex: 1 },
  rating: { marginLeft: 4, fontWeight: '500' },
  specialsRow: { flexDirection: 'row', alignItems: 'center', marginTop: 8, marginBottom: 12 },
  specialsText: { marginLeft: 4, color: colors.success, fontWeight: '500' },
  noSpecials: { marginLeft: 4, color: colors.textLight, fontStyle: 'italic' },
  btn: { marginTop: 4 },
});
export default RestaurantCard;
FILECONTENT
echo "Created RestaurantCard.js"

# CouponCard.js
cat > src/components/CouponCard.js << 'FILECONTENT'
import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Image } from 'react-native';
import { Card } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { colors, spacing } from '../theme/colors';

const CouponCard = ({ coupon, onPress, onSaveToggle, isSaved }) => {
  const getDiscount = () => {
    if (coupon.coupon_type === 'percentage') return coupon.discount_percentage + '% OFF';
    if (coupon.coupon_type === 'fixed_amount') return '$' + coupon.discount_amount + ' OFF';
    if (coupon.coupon_type === 'bogo') return 'BUY 1 GET 1';
    return 'SPECIAL';
  };
  const photo = coupon.restaurant?.photos?.[0]?.url;
  return (
    <TouchableOpacity onPress={onPress}>
      <Card style={styles.card}>
        {photo && <Image source={{ uri: photo }} style={styles.img} />}
        <View style={styles.badge}><Text style={styles.badgeText}>{getDiscount()}</Text></View>
        <View style={styles.content}>
          <Text style={styles.title} numberOfLines={1}>{coupon.title}</Text>
          <Text style={styles.restaurant}>{coupon.restaurant?.name}</Text>
          <Text style={styles.desc} numberOfLines={2}>{coupon.description}</Text>
        </View>
      </Card>
    </TouchableOpacity>
  );
};
const styles = StyleSheet.create({
  card: { marginBottom: 16, borderRadius: 12, overflow: 'hidden' },
  img: { width: '100%', height: 160 },
  badge: { position: 'absolute', top: 12, left: 12, backgroundColor: colors.primary, paddingHorizontal: 16, paddingVertical: 8, borderRadius: 8 },
  badgeText: { color: '#fff', fontSize: 16, fontWeight: 'bold' },
  content: { padding: 16 },
  title: { fontSize: 18, fontWeight: 'bold', marginBottom: 4 },
  restaurant: { fontSize: 14, color: colors.textLight, marginBottom: 8 },
  desc: { fontSize: 14, lineHeight: 20 },
});
export default CouponCard;
FILECONTENT
echo "Created CouponCard.js"

# AppNavigator.js
cat > src/navigation/AppNavigator.js << 'FILECONTENT'
import React from 'react';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createStackNavigator } from '@react-navigation/stack';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import HomeScreen from '../screens/HomeScreen';
import MapScreen from '../screens/MapScreen';
import FavoritesScreen from '../screens/FavoritesScreen';
import ProfileScreen from '../screens/ProfileScreen';
import CouponsScreen from '../screens/CouponsScreen';
import RestaurantDetailScreen from '../screens/RestaurantDetailScreen';
import CouponDetailScreen from '../screens/CouponDetailScreen';
import LoginScreen from '../screens/LoginScreen';
import RegisterScreen from '../screens/RegisterScreen';
import { colors } from '../theme/colors';

const Tab = createBottomTabNavigator();
const Stack = createStackNavigator();

const TabNavigator = () => (
  <Tab.Navigator screenOptions={({ route }) => ({ headerStyle: { backgroundColor: colors.primary }, headerTintColor: '#fff', tabBarActiveTintColor: colors.primary, tabBarInactiveTintColor: colors.textLight, tabBarIcon: ({ color, size }) => {
    let icon = 'circle';
    if (route.name === 'Home') icon = 'silverware-fork-knife';
    if (route.name === 'Coupons') icon = 'ticket-percent';
    if (route.name === 'Map') icon = 'map';
    if (route.name === 'Favorites') icon = 'heart';
    if (route.name === 'Profile') icon = 'account';
    return <Icon name={icon} size={size} color={color} />;
  }})}>
    <Tab.Screen name="Home" component={HomeScreen} options={{ title: 'On-the-Cheap' }} />
    <Tab.Screen name="Coupons" component={CouponsScreen} options={{ title: 'Coupons' }} />
    <Tab.Screen name="Map" component={MapScreen} />
    <Tab.Screen name="Favorites" component={FavoritesScreen} />
    <Tab.Screen name="Profile" component={ProfileScreen} />
  </Tab.Navigator>
);

const AppNavigator = () => (
  <Stack.Navigator screenOptions={{ headerStyle: { backgroundColor: colors.primary }, headerTintColor: '#fff' }}>
    <Stack.Screen name="Main" component={TabNavigator} options={{ headerShown: false }} />
    <Stack.Screen name="RestaurantDetail" component={RestaurantDetailScreen} options={{ title: 'Details' }} />
    <Stack.Screen name="CouponDetail" component={CouponDetailScreen} options={{ title: 'Coupon' }} />
    <Stack.Screen name="Login" component={LoginScreen} options={{ title: 'Sign In' }} />
    <Stack.Screen name="Register" component={RegisterScreen} options={{ title: 'Register' }} />
  </Stack.Navigator>
);

export default AppNavigator;
FILECONTENT
echo "Created AppNavigator.js"

# HomeScreen.js
cat > src/screens/HomeScreen.js << 'FILECONTENT'
import React, { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, Alert } from 'react-native';
import { Searchbar, Button, Card, Title, Chip, ActivityIndicator, Menu } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import * as Location from 'expo-location';
import APIService from '../services/APIService';
import RestaurantCard from '../components/RestaurantCard';
import { colors } from '../theme/colors';

const HomeScreen = ({ navigation }) => {
  const [searchQuery, setSearchQuery] = useState('');
  const [restaurants, setRestaurants] = useState([]);
  const [loading, setLoading] = useState(false);
  const [location, setLocation] = useState(null);
  const [lastSearch, setLastSearch] = useState('');
  const [radius, setRadius] = useState(16094);
  const [venueType, setVenueType] = useState('all');
  const [menuVisible, setMenuVisible] = useState(false);

  const radiusOptions = [{ label: '5 miles', value: 8047 }, { label: '10 miles', value: 16094 }, { label: '20 miles', value: 32187 }, { label: '50 miles', value: 80467 }];
  const venueTypes = [{ label: 'All', value: 'all', icon: 'silverware-fork-knife' }, { label: 'Restaurants', value: 'restaurant', icon: 'silverware-variant' }, { label: 'Food Trucks', value: 'mobile', icon: 'truck' }, { label: 'Bars', value: 'bar', icon: 'glass-cocktail' }, { label: 'Pop-ups', value: 'popup', icon: 'party-popper' }];

  const getNearMe = async () => {
    setLoading(true);
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') { Alert.alert('Error', 'Location permission required'); setLoading(false); return; }
      const pos = await Location.getCurrentPositionAsync({});
      setLocation(pos.coords);
      const params = { latitude: pos.coords.latitude, longitude: pos.coords.longitude, radius };
      if (venueType !== 'all') params.vendor_type = venueType;
      const result = await APIService.searchRestaurants(params);
      setRestaurants(result.restaurants || []);
      setLastSearch('your location');
    } catch (e) { Alert.alert('Error', 'Could not get location'); }
    setLoading(false);
  };

  const searchAddress = async () => {
    if (!searchQuery.trim()) { Alert.alert('Error', 'Enter a city or address'); return; }
    setLoading(true);
    try {
      const geo = await APIService.forwardGeocode(searchQuery);
      if (geo && geo.latitude) {
        setLocation({ latitude: geo.latitude, longitude: geo.longitude });
        const params = { latitude: geo.latitude, longitude: geo.longitude, radius };
        if (venueType !== 'all') params.vendor_type = venueType;
        const result = await APIService.searchRestaurants(params);
        setRestaurants(result.restaurants || []);
        setLastSearch(geo.formatted_address || searchQuery);
      } else { Alert.alert('Not Found', 'Could not find location'); }
    } catch (e) { Alert.alert('Error', 'Search failed'); }
    setLoading(false);
  };

  const applyFilters = () => { if (location) { setLoading(true); const params = { latitude: location.latitude, longitude: location.longitude, radius }; if (venueType !== 'all') params.vendor_type = venueType; APIService.searchRestaurants(params).then(r => { setRestaurants(r.restaurants || []); setLoading(false); }).catch(() => setLoading(false)); } };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.section}>
        <Card style={styles.card}>
          <Card.Content>
            <Title>Find Restaurant Specials</Title>
            <Text style={styles.sub}>Search by city or use location</Text>
            <Searchbar placeholder="City, State" value={searchQuery} onChangeText={setSearchQuery} onSubmitEditing={searchAddress} style={styles.search} />
            <View style={styles.row}>
              <Button mode="outlined" onPress={getNearMe} disabled={loading} icon="crosshairs-gps" style={styles.btn}>Near Me</Button>
              <Button mode="contained" onPress={searchAddress} disabled={loading} style={styles.btn}>Search</Button>
            </View>
          </Card.Content>
        </Card>
        <Card style={styles.card}>
          <Card.Content>
            <Title style={styles.filterTitle}>Filters</Title>
            <Text style={styles.label}>Distance</Text>
            <Menu visible={menuVisible} onDismiss={() => setMenuVisible(false)} anchor={<Button mode="outlined" onPress={() => setMenuVisible(true)} icon="map-marker-distance">{radiusOptions.find(o => o.value === radius)?.label}</Button>}>
              {radiusOptions.map(o => <Menu.Item key={o.value} onPress={() => { setRadius(o.value); setMenuVisible(false); }} title={o.label} />)}
            </Menu>
            <Text style={[styles.label, { marginTop: 16 }]}>Venue Type</Text>
            <View style={styles.chips}>{venueTypes.map(t => <Chip key={t.value} selected={venueType === t.value} onPress={() => setVenueType(t.value)} icon={t.icon} style={styles.chip}>{t.label}</Chip>)}</View>
            <Button mode="contained" onPress={applyFilters} style={styles.apply} disabled={!location} icon="filter">Apply Filters</Button>
          </Card.Content>
        </Card>
      </View>
      {loading && <View style={styles.loading}><ActivityIndicator size="large" color={colors.primary} /><Text style={styles.loadingText}>Finding restaurants...</Text></View>}
      {!loading && restaurants.length > 0 && <View style={styles.results}><Text style={styles.resultsTitle}>Found {restaurants.length} restaurants near {lastSearch}</Text>{restaurants.map(r => <RestaurantCard key={r.id} restaurant={r} onPress={() => navigation.navigate('RestaurantDetail', { restaurant: r })} />)}</View>}
      {!loading && restaurants.length === 0 && <View style={styles.welcome}><Icon name="silverware-fork-knife" size={80} color={colors.primary} /><Text style={styles.welcomeTitle}>Welcome to On-the-Cheap!</Text><Text style={styles.welcomeText}>Tap Near Me or search a location</Text></View>}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  section: { padding: 16 },
  card: { marginBottom: 16 },
  sub: { color: colors.textLight, marginBottom: 16 },
  search: { marginBottom: 16 },
  row: { flexDirection: 'row', gap: 8 },
  btn: { flex: 1 },
  filterTitle: { fontSize: 18, marginBottom: 8 },
  label: { fontSize: 14, fontWeight: '600', marginBottom: 4 },
  chips: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  chip: { marginBottom: 4 },
  apply: { marginTop: 16 },
  loading: { padding: 32, alignItems: 'center' },
  loadingText: { marginTop: 8, color: colors.textLight },
  results: { padding: 16 },
  resultsTitle: { fontSize: 16, fontWeight: '600', marginBottom: 16 },
  welcome: { alignItems: 'center', padding: 32, marginTop: 50 },
  welcomeTitle: { fontSize: 24, fontWeight: 'bold', marginTop: 24, textAlign: 'center' },
  welcomeText: { fontSize: 16, color: colors.textLight, textAlign: 'center', marginTop: 8 },
});

export default HomeScreen;
FILECONTENT
echo "Created HomeScreen.js"

# LoginScreen.js
cat > src/screens/LoginScreen.js << 'FILECONTENT'
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
  const [showPw, setShowPw] = useState(false);

  const login = async () => {
    if (!email.trim() || !password) { Alert.alert('Error', 'Enter email and password'); return; }
    setLoading(true);
    try {
      const r = await APIService.login(email.trim().toLowerCase(), password);
      Alert.alert('Success', 'Login successful!', [{ text: 'OK', onPress: () => { if (route?.params?.onLoginSuccess) route.params.onLoginSuccess(r.user); navigation.goBack(); }}]);
    } catch (e) { Alert.alert('Error', e.response?.data?.detail || 'Invalid email or password'); }
    setLoading(false);
  };

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        <View style={styles.header}><Icon name="silverware-fork-knife" size={64} color={colors.primary} /><Title style={styles.title}>Welcome Back!</Title><Text style={styles.sub}>Sign in to find deals</Text></View>
        <Card style={styles.card}><Card.Content>
          <TextInput label="Email" value={email} onChangeText={setEmail} mode="outlined" keyboardType="email-address" autoCapitalize="none" autoCorrect={false} style={styles.input} disabled={loading} />
          <TextInput label="Password" value={password} onChangeText={setPassword} mode="outlined" secureTextEntry={!showPw} style={styles.input} disabled={loading} right={<TextInput.Icon icon={showPw ? "eye-off" : "eye"} onPress={() => setShowPw(!showPw)} />} />
          <Button mode="contained" onPress={login} disabled={loading} style={styles.btn}>{loading ? 'Signing in...' : 'Sign In'}</Button>
          <Text style={styles.divider}>No account?</Text>
          <Button mode="outlined" onPress={() => navigation.navigate('Register')} disabled={loading}>Create Account</Button>
        </Card.Content></Card>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  scroll: { flexGrow: 1, justifyContent: 'center', padding: 24 },
  header: { alignItems: 'center', marginBottom: 32 },
  title: { fontSize: 28, fontWeight: 'bold', marginTop: 16 },
  sub: { color: colors.textLight, marginTop: 8 },
  card: { elevation: 4 },
  input: { marginBottom: 16 },
  btn: { marginTop: 8, marginBottom: 24 },
  divider: { textAlign: 'center', color: colors.textLight, marginBottom: 16 },
});

export default LoginScreen;
FILECONTENT
echo "Created LoginScreen.js"

# RegisterScreen.js
cat > src/screens/RegisterScreen.js << 'FILECONTENT'
import React, { useState } from 'react';
import { View, Text, StyleSheet, Alert, ScrollView, KeyboardAvoidingView, Platform } from 'react-native';
import { Card, Title, TextInput, Button } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import APIService from '../services/APIService';
import { colors } from '../theme/colors';

const RegisterScreen = ({ navigation, route }) => {
  const [firstName, setFirstName] = useState('');
  const [lastName, setLastName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirm, setConfirm] = useState('');
  const [loading, setLoading] = useState(false);
  const [showPw, setShowPw] = useState(false);

  const register = async () => {
    if (!firstName.trim() || !lastName.trim() || !email.trim() || !password) { Alert.alert('Error', 'Fill all fields'); return; }
    if (password.length < 6) { Alert.alert('Error', 'Password must be 6+ characters'); return; }
    if (password !== confirm) { Alert.alert('Error', 'Passwords do not match'); return; }
    setLoading(true);
    try {
      const r = await APIService.register({ first_name: firstName.trim(), last_name: lastName.trim(), email: email.trim().toLowerCase(), password });
      Alert.alert('Success', 'Account created!', [{ text: 'OK', onPress: () => { if (route?.params?.onRegistrationSuccess) route.params.onRegistrationSuccess(r.user); navigation.goBack(); }}]);
    } catch (e) { Alert.alert('Error', e.response?.data?.detail || 'Registration failed'); }
    setLoading(false);
  };

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        <View style={styles.header}><Icon name="account-plus" size={64} color={colors.primary} /><Title style={styles.title}>Create Account</Title></View>
        <Card style={styles.card}><Card.Content>
          <View style={styles.nameRow}><TextInput label="First Name" value={firstName} onChangeText={setFirstName} mode="outlined" style={[styles.input, styles.half]} disabled={loading} /><TextInput label="Last Name" value={lastName} onChangeText={setLastName} mode="outlined" style={[styles.input, styles.half]} disabled={loading} /></View>
          <TextInput label="Email" value={email} onChangeText={setEmail} mode="outlined" keyboardType="email-address" autoCapitalize="none" style={styles.input} disabled={loading} />
          <TextInput label="Password" value={password} onChangeText={setPassword} mode="outlined" secureTextEntry={!showPw} style={styles.input} disabled={loading} right={<TextInput.Icon icon={showPw ? "eye-off" : "eye"} onPress={() => setShowPw(!showPw)} />} />
          <TextInput label="Confirm Password" value={confirm} onChangeText={setConfirm} mode="outlined" secureTextEntry={!showPw} style={styles.input} disabled={loading} />
          <Button mode="contained" onPress={register} disabled={loading} style={styles.btn}>{loading ? 'Creating...' : 'Create Account'}</Button>
          <Button mode="outlined" onPress={() => navigation.goBack()} disabled={loading}>Back to Sign In</Button>
        </Card.Content></Card>
      </ScrollView>
    </KeyboardAvoidingView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  scroll: { flexGrow: 1, justifyContent: 'center', padding: 24 },
  header: { alignItems: 'center', marginBottom: 32 },
  title: { fontSize: 28, fontWeight: 'bold', marginTop: 16 },
  card: { elevation: 4 },
  nameRow: { flexDirection: 'row', gap: 8 },
  input: { marginBottom: 16 },
  half: { flex: 1 },
  btn: { marginTop: 8, marginBottom: 16 },
});

export default RegisterScreen;
FILECONTENT
echo "Created RegisterScreen.js"

# MapScreen.js
cat > src/screens/MapScreen.js << 'FILECONTENT'
import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, StyleSheet, RefreshControl, Linking, Alert } from 'react-native';
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

  useEffect(() => { load(); }, []);

  const load = async () => {
    setLoading(true); setError(null);
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') { setError('Location permission required'); setLoading(false); return; }
      const pos = await Location.getCurrentPositionAsync({});
      setLocation(pos.coords);
      const result = await APIService.searchRestaurants({ latitude: pos.coords.latitude, longitude: pos.coords.longitude, radius: 25000 });
      setRestaurants(result.restaurants || []);
    } catch (e) { setError('Could not load restaurants'); }
    setLoading(false);
  };

  const refresh = async () => { setRefreshing(true); await load(); setRefreshing(false); };
  const openMaps = (r) => { const lat = r.location?.latitude || r.latitude; const lng = r.location?.longitude || r.longitude; if (lat && lng) Linking.openURL('https://www.google.com/maps/search/?api=1&query=' + lat + ',' + lng); else Linking.openURL('https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(r.address)); };

  if (loading) return <View style={styles.center}><ActivityIndicator size="large" color={colors.primary} /><Text style={styles.loadingText}>Finding restaurants...</Text></View>;
  if (error) return <View style={styles.center}><Icon name="alert-circle-outline" size={64} color={colors.error} /><Text style={styles.errorText}>{error}</Text><Button mode="contained" onPress={load} style={styles.retry}>Try Again</Button></View>;

  return (
    <ScrollView style={styles.container} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} />}>
      <Card style={styles.card}><Card.Content style={styles.headerContent}><Icon name="map-marker-radius" size={48} color={colors.primary} /><Title style={styles.title}>Nearby Restaurants</Title><Text style={styles.sub}>{restaurants.length} found</Text><Button mode="contained" onPress={() => location && Linking.openURL('https://www.google.com/maps/search/restaurants/@' + location.latitude + ',' + location.longitude + ',13z')} icon="google-maps" style={styles.mapBtn}>Open in Maps</Button></Card.Content></Card>
      {restaurants.length > 0 && <Card style={styles.card}><Card.Content>{restaurants.slice(0, 20).map((r, i) => <React.Fragment key={r.id || i}><List.Item title={r.name} description={r.address} left={p => <List.Icon {...p} icon="silverware-fork-knife" color={colors.primary} />} right={() => <Button mode="text" onPress={() => openMaps(r)} compact><Icon name="directions" size={20} color={colors.primary} /></Button>} onPress={() => navigation.navigate('RestaurantDetail', { restaurant: r })} />{i < restaurants.length - 1 && <Divider />}</React.Fragment>)}</Card.Content></Card>}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: colors.background, padding: 24 },
  loadingText: { marginTop: 16, color: colors.textLight },
  errorText: { marginTop: 16, color: colors.error, textAlign: 'center' },
  retry: { marginTop: 24 },
  card: { margin: 16, marginBottom: 8 },
  headerContent: { alignItems: 'center', paddingVertical: 24 },
  title: { fontSize: 24, fontWeight: 'bold', marginTop: 16 },
  sub: { color: colors.textLight, marginTop: 4, marginBottom: 16 },
  mapBtn: { marginTop: 8 },
});

export default MapScreen;
FILECONTENT
echo "Created MapScreen.js"

# FavoritesScreen.js
cat > src/screens/FavoritesScreen.js << 'FILECONTENT'
import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, StyleSheet, RefreshControl } from 'react-native';
import { ActivityIndicator } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import APIService from '../services/APIService';
import RestaurantCard from '../components/RestaurantCard';
import { colors } from '../theme/colors';

const FavoritesScreen = ({ navigation }) => {
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => { load(); }, []);
  const load = async () => { try { const r = await APIService.getFavorites(); setFavorites(r.favorites || []); } catch (e) {} setLoading(false); };
  const refresh = async () => { setRefreshing(true); await load(); setRefreshing(false); };

  if (loading) return <View style={styles.center}><ActivityIndicator size="large" color={colors.primary} /></View>;

  return (
    <ScrollView style={styles.container} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} />}>
      {favorites.length > 0 ? (
        <View style={styles.content}><Text style={styles.title}>Your Favorites ({favorites.length})</Text>{favorites.map(r => <RestaurantCard key={r.id} restaurant={r} onPress={() => navigation.navigate('RestaurantDetail', { restaurant: r })} />)}</View>
      ) : (
        <View style={styles.empty}><Icon name="heart-outline" size={64} color={colors.textLight} /><Text style={styles.emptyTitle}>No Favorites Yet</Text><Text style={styles.emptyText}>Save restaurants by tapping the heart</Text></View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  content: { padding: 16 },
  title: { fontSize: 20, fontWeight: 'bold', marginBottom: 16 },
  empty: { alignItems: 'center', padding: 32, marginTop: 100 },
  emptyTitle: { fontSize: 20, fontWeight: 'bold', marginTop: 16 },
  emptyText: { color: colors.textLight, marginTop: 8, textAlign: 'center' },
});

export default FavoritesScreen;
FILECONTENT
echo "Created FavoritesScreen.js"

# ProfileScreen.js
cat > src/screens/ProfileScreen.js << 'FILECONTENT'
import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, StyleSheet, Alert } from 'react-native';
import { Card, Title, Button, ActivityIndicator } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import APIService from '../services/APIService';
import { colors } from '../theme/colors';

const ProfileScreen = ({ navigation }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [isAuth, setIsAuth] = useState(false);

  useEffect(() => { check(); }, []);
  const check = async () => { const auth = await APIService.isAuthenticated(); setIsAuth(auth); if (auth) { const u = await APIService.getCurrentUser(); setUser(u); } setLoading(false); };
  const logout = () => { Alert.alert('Logout', 'Are you sure?', [{ text: 'Cancel', style: 'cancel' }, { text: 'Logout', style: 'destructive', onPress: async () => { await APIService.logout(); setUser(null); setIsAuth(false); }}]); };

  if (loading) return <View style={styles.center}><ActivityIndicator size="large" color={colors.primary} /></View>;

  if (!isAuth) return (
    <ScrollView style={styles.container}>
      <View style={styles.prompt}><Icon name="account-circle" size={80} color={colors.textLight} /><Text style={styles.promptTitle}>Welcome to On-the-Cheap!</Text><Text style={styles.promptSub}>Sign in to save favorites</Text></View>
      <Card style={styles.card}><Card.Content><Button mode="contained" onPress={() => navigation.navigate('Login', { onLoginSuccess: check })} style={styles.btn}>Sign In</Button><Button mode="outlined" onPress={() => navigation.navigate('Register', { onRegistrationSuccess: check })} style={styles.btn}>Create Account</Button></Card.Content></Card>
    </ScrollView>
  );

  return (
    <ScrollView style={styles.container}>
      <Card style={styles.card}><Card.Content style={styles.userInfo}><Icon name="account-circle" size={64} color={colors.primary} /><View style={styles.userDetails}><Title>{user?.first_name} {user?.last_name}</Title><Text style={styles.email}>{user?.email}</Text></View></Card.Content></Card>
      <Card style={styles.card}><Card.Content><Button mode="outlined" onPress={logout} textColor={colors.error}>Logout</Button></Card.Content></Card>
      <Text style={styles.version}>On-the-Cheap v1.0.0</Text>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background, padding: 16 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  prompt: { alignItems: 'center', padding: 32 },
  promptTitle: { fontSize: 24, fontWeight: 'bold', marginTop: 16, textAlign: 'center' },
  promptSub: { color: colors.textLight, marginTop: 8, textAlign: 'center' },
  card: { marginBottom: 16 },
  btn: { marginBottom: 16 },
  userInfo: { flexDirection: 'row', alignItems: 'center' },
  userDetails: { marginLeft: 16 },
  email: { color: colors.textLight },
  version: { textAlign: 'center', color: colors.textLight, marginTop: 24 },
});

export default ProfileScreen;
FILECONTENT
echo "Created ProfileScreen.js"

# CouponsScreen.js
cat > src/screens/CouponsScreen.js << 'FILECONTENT'
import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, StyleSheet, RefreshControl, Alert } from 'react-native';
import { ActivityIndicator, SegmentedButtons } from 'react-native-paper';
import * as Location from 'expo-location';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import APIService from '../services/APIService';
import CouponCard from '../components/CouponCard';
import { colors } from '../theme/colors';

const CouponsScreen = ({ navigation }) => {
  const [coupons, setCoupons] = useState([]);
  const [loading, setLoading] = useState(false);
  const [refreshing, setRefreshing] = useState(false);
  const [location, setLocation] = useState(null);
  const [view, setView] = useState('discover');

  useEffect(() => { getLocation(); }, []);
  useEffect(() => { if (view === 'saved') loadSaved(); else if (location) loadNearby(); }, [view]);

  const getLocation = async () => {
    try { const { status } = await Location.requestForegroundPermissionsAsync(); if (status !== 'granted') return; const pos = await Location.getCurrentPositionAsync({}); setLocation(pos.coords); loadNearby(pos.coords.latitude, pos.coords.longitude); } catch (e) {}
  };

  const loadNearby = async (lat, lng) => {
    if (!lat && !location) return; setLoading(true);
    try { const r = await APIService.getNearbyCoupons(lat || location.latitude, lng || location.longitude); setCoupons(r.coupons || []); } catch (e) {}
    setLoading(false);
  };

  const loadSaved = async () => {
    const auth = await APIService.isAuthenticated(); if (!auth) { Alert.alert('Login Required', 'Please login to see saved coupons'); setView('discover'); return; }
    setLoading(true); try { const r = await APIService.getSavedCoupons(); setCoupons(r.coupons || []); } catch (e) {} setLoading(false);
  };

  const refresh = async () => { setRefreshing(true); if (view === 'saved') await loadSaved(); else await loadNearby(); setRefreshing(false); };

  return (
    <View style={styles.container}>
      <View style={styles.segment}><SegmentedButtons value={view} onValueChange={setView} buttons={[{ value: 'discover', label: 'Discover' }, { value: 'saved', label: 'Saved' }]} /></View>
      <ScrollView style={styles.scroll} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} />}>
        {loading && <View style={styles.loading}><ActivityIndicator size="large" color={colors.primary} /></View>}
        {!loading && coupons.length > 0 && <View style={styles.list}><Text style={styles.count}>{coupons.length} coupon(s)</Text>{coupons.map(c => <CouponCard key={c.id} coupon={c} onPress={() => navigation.navigate('CouponDetail', { coupon: c })} />)}</View>}
        {!loading && coupons.length === 0 && <View style={styles.empty}><Icon name="ticket-percent" size={64} color={colors.textLight} /><Text style={styles.emptyTitle}>{view === 'saved' ? 'No saved coupons' : 'No coupons found'}</Text></View>}
      </ScrollView>
    </View>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  segment: { padding: 16, backgroundColor: '#fff', borderBottomWidth: 1, borderBottomColor: colors.border },
  scroll: { flex: 1 },
  loading: { padding: 32, alignItems: 'center' },
  list: { padding: 16 },
  count: { fontSize: 16, fontWeight: '600', marginBottom: 16 },
  empty: { alignItems: 'center', padding: 32, marginTop: 50 },
  emptyTitle: { fontSize: 20, fontWeight: 'bold', marginTop: 16 },
});

export default CouponsScreen;
FILECONTENT
echo "Created CouponsScreen.js"

# RestaurantDetailScreen.js
cat > src/screens/RestaurantDetailScreen.js << 'FILECONTENT'
import React from 'react';
import { View, Text, ScrollView, StyleSheet, Linking, Share } from 'react-native';
import { Card, Title, Button, Chip, List } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { colors } from '../theme/colors';

const RestaurantDetailScreen = ({ route }) => {
  const { restaurant } = route.params;
  const hasSpecials = restaurant.specials && restaurant.specials.length > 0;
  const lat = restaurant.location?.latitude || restaurant.latitude;
  const lng = restaurant.location?.longitude || restaurant.longitude;

  const call = () => { if (restaurant.phone) Linking.openURL('tel:' + restaurant.phone); };
  const text = () => { if (restaurant.phone) Linking.openURL('sms:' + restaurant.phone.replace(/[^0-9]/g, '')); };
  const whatsapp = () => { if (restaurant.phone) Linking.openURL('whatsapp://send?phone=1' + restaurant.phone.replace(/[^0-9]/g, '')).catch(() => {}); };
  const web = () => { if (restaurant.website) Linking.openURL(restaurant.website); };
  const share = async () => { try { await Share.share({ message: 'Check out ' + restaurant.name + ' at ' + restaurant.address }); } catch (e) {} };
  const directions = () => { if (lat && lng) Linking.openURL('https://www.google.com/maps/dir/?api=1&destination=' + lat + ',' + lng); else Linking.openURL('https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(restaurant.address)); };
  const uber = () => { if (lat && lng) Linking.openURL('uber://?action=setPickup&pickup=my_location&dropoff[latitude]=' + lat + '&dropoff[longitude]=' + lng).catch(() => Linking.openURL('https://m.uber.com/ul/?action=setPickup&pickup=my_location&dropoff[latitude]=' + lat + '&dropoff[longitude]=' + lng)); };
  const lyft = () => { if (lat && lng) Linking.openURL('lyft://ridetype?id=lyft&destination[latitude]=' + lat + '&destination[longitude]=' + lng).catch(() => Linking.openURL('https://www.lyft.com/ride?destination[latitude]=' + lat + '&destination[longitude]=' + lng)); };

  return (
    <ScrollView style={styles.container}>
      <Card style={styles.card}><Card.Content>
        <View style={styles.header}><Title style={styles.name}>{restaurant.name}</Title>{restaurant.is_mobile_vendor && <Chip icon="truck" style={styles.chip}>Food Truck</Chip>}</View>
        {restaurant.rating && <View style={styles.row}><Icon name="star" size={16} color={colors.warning} /><Text style={styles.rating}>{restaurant.rating.toFixed(1)}</Text></View>}
        <View style={styles.row}><Icon name="map-marker" size={16} color={colors.textLight} /><Text style={styles.address}>{restaurant.address}</Text></View>
        {restaurant.phone && <View style={styles.row}><Icon name="phone" size={16} color={colors.textLight} /><Text style={styles.phone}>{restaurant.phone}</Text></View>}
      </Card.Content></Card>
      <Card style={styles.card}><Card.Content><Title style={styles.section}>Contact</Title><View style={styles.grid}>{restaurant.phone && <><Button mode="contained" onPress={call} icon="phone" style={styles.gridBtn}>Call</Button><Button mode="outlined" onPress={text} icon="message-text" style={styles.gridBtn}>Text</Button><Button mode="outlined" onPress={whatsapp} icon="whatsapp" style={styles.gridBtn}>WhatsApp</Button></>}{restaurant.website && <Button mode="outlined" onPress={web} icon="web" style={styles.gridBtn}>Website</Button>}<Button mode="outlined" onPress={share} icon="share-variant" style={styles.gridBtn}>Share</Button></View></Card.Content></Card>
      <Card style={styles.card}><Card.Content><Title style={styles.section}>Get a Ride</Title><View style={styles.rideRow}><Button mode="contained" onPress={uber} icon="car" style={[styles.rideBtn, { backgroundColor: '#000' }]}>Uber</Button><Button mode="contained" onPress={lyft} icon="car" style={[styles.rideBtn, { backgroundColor: '#FF00BF' }]}>Lyft</Button></View><Button mode="outlined" onPress={directions} icon="directions" style={styles.dirBtn}>Get Directions</Button></Card.Content></Card>
      <Card style={styles.card}><Card.Content><Title style={styles.section}>Current Specials</Title>{hasSpecials ? restaurant.specials.map((s, i) => <List.Item key={i} title={s.name || s.title || 'Special'} description={s.description} left={p => <List.Icon {...p} icon="tag" color={colors.success} />} />) : <View style={styles.noSpecials}><Icon name="information-outline" size={32} color={colors.textLight} /><Text style={styles.noSpecialsText}>No current specials</Text></View>}</Card.Content></Card>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  card: { margin: 16, marginBottom: 8 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 },
  name: { flex: 1, fontSize: 22, fontWeight: 'bold' },
  chip: { backgroundColor: colors.foodTruck },
  row: { flexDirection: 'row', alignItems: 'center', marginTop: 4 },
  rating: { marginLeft: 4, fontWeight: '500' },
  address: { marginLeft: 4, color: colors.textLight, flex: 1 },
  phone: { marginLeft: 4, color: colors.textLight },
  section: { fontSize: 18, marginBottom: 12 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  gridBtn: { marginBottom: 4 },
  rideRow: { flexDirection: 'row', gap: 8, marginBottom: 12 },
  rideBtn: { flex: 1 },
  dirBtn: { marginTop: 4 },
  noSpecials: { alignItems: 'center', padding: 24 },
  noSpecialsText: { marginTop: 8, color: colors.textLight },
});

export default RestaurantDetailScreen;
FILECONTENT
echo "Created RestaurantDetailScreen.js"

# CouponDetailScreen.js
cat > src/screens/CouponDetailScreen.js << 'FILECONTENT'
import React, { useState } from 'react';
import { View, Text, ScrollView, StyleSheet, Image, Share, Alert } from 'react-native';
import { Button, Card, Title, Divider } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import APIService from '../services/APIService';
import { colors } from '../theme/colors';

const CouponDetailScreen = ({ route }) => {
  const { coupon } = route.params;
  const [saved, setSaved] = useState(false);
  const [loading, setLoading] = useState(false);

  const getDiscount = () => {
    if (coupon.coupon_type === 'percentage') return coupon.discount_percentage + '% OFF';
    if (coupon.coupon_type === 'fixed_amount') return '$' + coupon.discount_amount + ' OFF';
    if (coupon.coupon_type === 'bogo') return 'BUY 1 GET 1 FREE';
    return 'SPECIAL OFFER';
  };

  const formatDate = (d) => new Date(d).toLocaleDateString('en-US', { month: 'long', day: 'numeric', year: 'numeric' });

  const save = async () => {
    setLoading(true);
    try { if (saved) { await APIService.removeSavedCoupon(coupon.id); setSaved(false); } else { await APIService.saveCoupon(coupon.id); setSaved(true); Alert.alert('Saved!', 'Coupon saved'); } } catch (e) { Alert.alert('Error', 'Could not save'); }
    setLoading(false);
  };

  const share = async () => { try { await Share.share({ message: coupon.title + ' - ' + getDiscount() + ' at ' + coupon.restaurant?.name }); } catch (e) {} };

  const photo = coupon.restaurant?.photos?.[0]?.url;

  return (
    <ScrollView style={styles.container}>
      {photo && <Image source={{ uri: photo }} style={styles.img} />}
      <View style={styles.banner}><Text style={styles.bannerText}>{getDiscount()}</Text></View>
      <View style={styles.content}>
        <Title style={styles.title}>{coupon.title}</Title>
        <View style={styles.row}><Icon name="store" size={20} color={colors.primary} /><Text style={styles.restaurant}>{coupon.restaurant?.name}</Text></View>
        <Text style={styles.address}>{coupon.restaurant?.address}</Text>
        <View style={styles.btnRow}><Button mode="contained" onPress={save} icon={saved ? 'bookmark' : 'bookmark-outline'} style={styles.btn} loading={loading}>{saved ? 'Saved' : 'Save'}</Button><Button mode="outlined" onPress={share} icon="share-variant" style={styles.btn}>Share</Button></View>
        <Divider style={styles.divider} />
        <Card style={styles.card}><Card.Content><Text style={styles.section}>About This Offer</Text><Text style={styles.desc}>{coupon.description}</Text></Card.Content></Card>
        <Card style={styles.card}><Card.Content><Text style={styles.section}>Details</Text><View style={styles.detailRow}><Icon name="calendar-range" size={20} color={colors.textLight} /><Text style={styles.detail}>Valid: {formatDate(coupon.valid_from)} - {formatDate(coupon.valid_until)}</Text></View>{coupon.minimum_purchase && <View style={styles.detailRow}><Icon name="currency-usd" size={20} color={colors.textLight} /><Text style={styles.detail}>Minimum: ${coupon.minimum_purchase}</Text></View>}</Card.Content></Card>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  img: { width: '100%', height: 200 },
  banner: { backgroundColor: colors.primary, paddingVertical: 24, alignItems: 'center' },
  bannerText: { color: '#fff', fontSize: 28, fontWeight: 'bold' },
  content: { padding: 16 },
  title: { fontSize: 24, fontWeight: 'bold', marginBottom: 8 },
  row: { flexDirection: 'row', alignItems: 'center' },
  restaurant: { fontSize: 18, fontWeight: '600', marginLeft: 8 },
  address: { color: colors.textLight, marginLeft: 28, marginBottom: 16 },
  btnRow: { flexDirection: 'row', gap: 8, marginBottom: 16 },
  btn: { flex: 1 },
  divider: { marginVertical: 16 },
  card: { marginBottom: 16 },
  section: { fontSize: 18, fontWeight: 'bold', marginBottom: 12 },
  desc: { fontSize: 16, lineHeight: 24 },
  detailRow: { flexDirection: 'row', alignItems: 'center', marginBottom: 8 },
  detail: { marginLeft: 8 },
});

export default CouponDetailScreen;
FILECONTENT
echo "Created CouponDetailScreen.js"

# App.js
cat > App.js << 'FILECONTENT'
import React from 'react';
import { SafeAreaProvider, SafeAreaView } from 'react-native-safe-area-context';
import { StatusBar, StyleSheet } from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { Provider as PaperProvider } from 'react-native-paper';
import AppNavigator from './src/navigation/AppNavigator';
import { theme } from './src/theme/colors';

const App = () => (
  <SafeAreaProvider>
    <PaperProvider theme={theme}>
      <StatusBar barStyle="light-content" backgroundColor={theme.colors.primary} />
      <NavigationContainer>
        <SafeAreaView style={styles.container}>
          <AppNavigator />
        </SafeAreaView>
      </NavigationContainer>
    </PaperProvider>
  </SafeAreaProvider>
);

const styles = StyleSheet.create({ container: { flex: 1, backgroundColor: '#fef3c7' } });

export default App;
FILECONTENT
echo "Created App.js"

echo ""
echo "=== SETUP COMPLETE ==="
echo "Now run: rm -rf node_modules && npm install --legacy-peer-deps && eas build --profile preview --platform android --clear-cache"
