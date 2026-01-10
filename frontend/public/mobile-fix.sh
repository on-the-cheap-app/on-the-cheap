#!/bin/bash
echo "=== Fixing Mobile App Files ==="

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
  async addFavorite(restaurantId) { const r = await this.api.post('/users/favorites/' + restaurantId); return r.data; }
  async removeFavorite(restaurantId) { const r = await this.api.delete('/users/favorites/' + restaurantId); return r.data; }
  async getCurrentUser() { const d = await AsyncStorage.getItem('user_data'); return d ? JSON.parse(d) : null; }
  async logout() { await AsyncStorage.multiRemove(['auth_token', 'user_data']); }
  async isAuthenticated() { const t = await AsyncStorage.getItem('auth_token'); return !!t; }
  async getNearbyCoupons(lat, lng, rad) { const r = await this.api.get('/coupons/near', { params: { latitude: lat, longitude: lng, radius: rad || 16094 } }); return r.data; }
  async getSavedCoupons() { const r = await this.api.get('/users/coupons/saved'); return r.data; }
  async saveCoupon(id) { const r = await this.api.post('/users/coupons/' + id + '/save'); return r.data; }
  async removeSavedCoupon(id) { const r = await this.api.delete('/users/coupons/' + id + '/save'); return r.data; }
}
export default new APIService();
EOF
echo "Created APIService.js"

cat > src/screens/HomeScreen.js << 'EOF'
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
  const [loadingMessage, setLoadingMessage] = useState('Finding restaurants...');
  const [location, setLocation] = useState(null);
  const [lastSearch, setLastSearch] = useState('');
  const [radius, setRadius] = useState(16094);
  const [venueType, setVenueType] = useState('all');
  const [menuVisible, setMenuVisible] = useState(false);

  const radiusOptions = [{ label: '5 miles', value: 8047 }, { label: '10 miles', value: 16094 }, { label: '20 miles', value: 32187 }, { label: '50 miles', value: 80467 }];
  const venueTypes = [{ label: 'All', value: 'all', icon: 'silverware-fork-knife' }, { label: 'Restaurants', value: 'restaurant', icon: 'silverware-variant' }, { label: 'Food Trucks', value: 'mobile', icon: 'truck' }, { label: 'Bars', value: 'bar', icon: 'glass-cocktail' }, { label: 'Pop-ups', value: 'popup', icon: 'party-popper' }];

  const getNearMe = async () => {
    setLoading(true);
    setLoadingMessage('Getting your location...');
    const defaultCoords = { latitude: 30.2672, longitude: -97.7431 };
    
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') { 
        Alert.alert('Error', 'Location permission required'); 
        setLoading(false); 
        return; 
      }
      
      let coords = null;
      
      try {
        const lastKnown = await Promise.race([
          Location.getLastKnownPositionAsync({}),
          new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 3000))
        ]);
        if (lastKnown && lastKnown.coords) coords = lastKnown.coords;
      } catch (e) {}
      
      if (!coords) {
        setLoadingMessage('Finding precise location...');
        try {
          const current = await Promise.race([
            Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Low }),
            new Promise((_, reject) => setTimeout(() => reject(new Error('timeout')), 10000))
          ]);
          if (current && current.coords) coords = current.coords;
        } catch (e) {
          coords = defaultCoords;
        }
      }
      
      if (!coords) coords = defaultCoords;
      
      setLocation(coords);
      setLoadingMessage('Finding restaurants...');
      const params = { latitude: coords.latitude, longitude: coords.longitude, radius: radius };
      if (venueType !== 'all') params.vendor_type = venueType;
      const result = await APIService.searchRestaurants(params);
      setRestaurants(result.restaurants || []);
      setLastSearch('your location');
    } catch (e) { 
      Alert.alert('Error', 'Could not get location'); 
    }
    setLoading(false);
  };

  const searchAddress = async () => {
    if (!searchQuery.trim()) { Alert.alert('Error', 'Enter a city or address'); return; }
    setLoading(true);
    
    var lastError = null;
    for (var attempt = 1; attempt <= 3; attempt++) {
      setLoadingMessage(attempt === 1 ? 'Searching ' + searchQuery + '...' : 'Retrying search (attempt ' + attempt + ')...');
      try {
        const geo = await APIService.forwardGeocode(searchQuery);
        if (geo && geo.latitude) {
          setLocation({ latitude: geo.latitude, longitude: geo.longitude });
          setLoadingMessage('Finding restaurants...');
          const params = { latitude: geo.latitude, longitude: geo.longitude, radius: radius };
          if (venueType !== 'all') params.vendor_type = venueType;
          const result = await APIService.searchRestaurants(params);
          setRestaurants(result.restaurants || []);
          setLastSearch(geo.formatted_address || searchQuery);
          setLoading(false);
          return;
        }
      } catch (e) { 
        lastError = e;
        if (attempt < 3) await new Promise(function(r) { setTimeout(r, 2000); });
      }
    }
    
    Alert.alert('Error', 'Could not find location. Please try again.');
    setLoading(false);
  };

  const applyFilters = () => { 
    if (location) { 
      setLoading(true); 
      setLoadingMessage('Applying filters...');
      const params = { latitude: location.latitude, longitude: location.longitude, radius: radius }; 
      if (venueType !== 'all') params.vendor_type = venueType; 
      APIService.searchRestaurants(params).then(function(r) { 
        setRestaurants(r.restaurants || []); 
        setLoading(false); 
      }).catch(function() { setLoading(false); }); 
    } 
  };

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
            <Menu visible={menuVisible} onDismiss={function() { setMenuVisible(false); }} anchor={<Button mode="outlined" onPress={function() { setMenuVisible(true); }} icon="map-marker-distance">{radiusOptions.find(function(o) { return o.value === radius; }).label}</Button>}>
              {radiusOptions.map(function(o) { return <Menu.Item key={o.value} onPress={function() { setRadius(o.value); setMenuVisible(false); }} title={o.label} />; })}
            </Menu>
            <Text style={[styles.label, { marginTop: 16 }]}>Venue Type</Text>
            <View style={styles.chips}>{venueTypes.map(function(t) { return <Chip key={t.value} selected={venueType === t.value} onPress={function() { setVenueType(t.value); }} icon={t.icon} style={styles.chip}>{t.label}</Chip>; })}</View>
            <Button mode="contained" onPress={applyFilters} style={styles.apply} disabled={!location} icon="filter">Apply Filters</Button>
          </Card.Content>
        </Card>
      </View>
      {loading && <View style={styles.loading}><ActivityIndicator size="large" color={colors.primary} /><Text style={styles.loadingText}>{loadingMessage}</Text></View>}
      {!loading && restaurants.length > 0 && <View style={styles.results}><Text style={styles.resultsTitle}>Found {restaurants.length} restaurants near {lastSearch}</Text>{restaurants.map(function(r) { return <RestaurantCard key={r.id} restaurant={r} onPress={function() { navigation.navigate('RestaurantDetail', { restaurant: r }); }} />; })}</View>}
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
EOF
echo "Created HomeScreen.js"

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

  useEffect(function() { load(); }, []);

  const load = async () => {
    setLoading(true); setError(null);
    const defaultCoords = { latitude: 30.2672, longitude: -97.7431 };
    
    try {
      const { status } = await Location.requestForegroundPermissionsAsync();
      if (status !== 'granted') { 
        setLocation(defaultCoords);
        const result = await APIService.searchRestaurants({ latitude: defaultCoords.latitude, longitude: defaultCoords.longitude, radius: 25000 });
        setRestaurants(result.restaurants || []);
        setLoading(false);
        return;
      }
      
      var coords = defaultCoords;
      try {
        const lastKnown = await Promise.race([
          Location.getLastKnownPositionAsync({}),
          new Promise(function(_, reject) { setTimeout(function() { reject(new Error('timeout')); }, 3000); })
        ]);
        if (lastKnown && lastKnown.coords) coords = lastKnown.coords;
      } catch (e) {}
      
      if (coords === defaultCoords) {
        try {
          const current = await Promise.race([
            Location.getCurrentPositionAsync({ accuracy: Location.Accuracy.Low }),
            new Promise(function(_, reject) { setTimeout(function() { reject(new Error('timeout')); }, 10000); })
          ]);
          if (current && current.coords) coords = current.coords;
        } catch (e) {}
      }
      
      setLocation(coords);
      const result = await APIService.searchRestaurants({ latitude: coords.latitude, longitude: coords.longitude, radius: 25000 });
      setRestaurants(result.restaurants || []);
    } catch (e) { 
      setLocation(defaultCoords);
      try {
        const result = await APIService.searchRestaurants({ latitude: defaultCoords.latitude, longitude: defaultCoords.longitude, radius: 25000 });
        setRestaurants(result.restaurants || []);
      } catch (e2) {
        setError('Could not load restaurants');
      }
    }
    setLoading(false);
  };

  const refresh = async () => { setRefreshing(true); await load(); setRefreshing(false); };
  const openMaps = (r) => { var lat = r.location ? r.location.latitude : r.latitude; var lng = r.location ? r.location.longitude : r.longitude; if (lat && lng) Linking.openURL('https://www.google.com/maps/search/?api=1&query=' + lat + ',' + lng); else Linking.openURL('https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(r.address)); };

  if (loading) return <View style={styles.center}><ActivityIndicator size="large" color={colors.primary} /><Text style={styles.loadingText}>Finding restaurants...</Text></View>;
  if (error) return <View style={styles.center}><Icon name="alert-circle-outline" size={64} color={colors.error} /><Text style={styles.errorText}>{error}</Text><Button mode="contained" onPress={load} style={styles.retry}>Try Again</Button></View>;

  return (
    <ScrollView style={styles.container} refreshControl={<RefreshControl refreshing={refreshing} onRefresh={refresh} />}>
      <Card style={styles.card}><Card.Content style={styles.headerContent}><Icon name="map-marker-radius" size={48} color={colors.primary} /><Title style={styles.title}>Nearby Restaurants</Title><Text style={styles.sub}>{restaurants.length} found</Text><Button mode="contained" onPress={function() { if (location) Linking.openURL('https://www.google.com/maps/search/restaurants/@' + location.latitude + ',' + location.longitude + ',13z'); }} icon="google-maps" style={styles.mapBtn}>Open in Maps</Button></Card.Content></Card>
      {restaurants.length > 0 && <Card style={styles.card}><Card.Content>{restaurants.slice(0, 20).map(function(r, i) { return <React.Fragment key={r.id || i}><List.Item title={r.name} description={r.address} left={function(p) { return <List.Icon {...p} icon="silverware-fork-knife" color={colors.primary} />; }} right={function() { return <Button mode="text" onPress={function() { openMaps(r); }} compact><Icon name="directions" size={20} color={colors.primary} /></Button>; }} onPress={function() { navigation.navigate('RestaurantDetail', { restaurant: r }); }} />{i < restaurants.length - 1 && <Divider />}</React.Fragment>; })}</Card.Content></Card>}
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
EOF
echo "Created MapScreen.js"

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
  const [showPw, setShowPw] = useState(false);

  const login = async () => {
    if (!email.trim() || !password) { Alert.alert('Error', 'Enter email and password'); return; }
    setLoading(true);
    try {
      const r = await APIService.login(email.trim().toLowerCase(), password);
      Alert.alert('Success', 'Login successful!', [{ text: 'OK', onPress: function() { if (route && route.params && route.params.onLoginSuccess) route.params.onLoginSuccess(r.user); navigation.goBack(); }}]);
    } catch (e) { Alert.alert('Error', e.response && e.response.data && e.response.data.detail ? e.response.data.detail : 'Invalid email or password'); }
    setLoading(false);
  };

  return (
    <KeyboardAvoidingView style={styles.container} behavior={Platform.OS === 'ios' ? 'padding' : 'height'}>
      <ScrollView contentContainerStyle={styles.scroll} keyboardShouldPersistTaps="handled">
        <View style={styles.header}><Icon name="silverware-fork-knife" size={64} color={colors.primary} /><Title style={styles.title}>Welcome Back!</Title><Text style={styles.sub}>Sign in to find deals</Text></View>
        <Card style={styles.card}><Card.Content>
          <TextInput label="Email" value={email} onChangeText={setEmail} mode="outlined" keyboardType="email-address" autoCapitalize="none" autoCorrect={false} style={styles.input} disabled={loading} />
          <TextInput label="Password" value={password} onChangeText={setPassword} mode="outlined" secureTextEntry={!showPw} style={styles.input} disabled={loading} right={<TextInput.Icon icon={showPw ? "eye-off" : "eye"} onPress={function() { setShowPw(!showPw); }} />} />
          <Button mode="contained" onPress={login} disabled={loading} style={styles.btn}>{loading ? 'Signing in...' : 'Sign In'}</Button>
          <Text style={styles.divider}>No account?</Text>
          <Button mode="outlined" onPress={function() { navigation.navigate('Register'); }} disabled={loading}>Create Account</Button>
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
EOF
echo "Created LoginScreen.js"

cat > src/screens/RestaurantDetailScreen.js << 'EOF'
import React, { useState, useEffect } from 'react';
import { View, Text, ScrollView, StyleSheet, Linking, Share, Alert } from 'react-native';
import { Card, Title, Button, Chip, List, IconButton } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import APIService from '../services/APIService';
import { colors } from '../theme/colors';

const RestaurantDetailScreen = ({ route, navigation }) => {
  const { restaurant } = route.params;
  const [isFavorite, setIsFavorite] = useState(false);
  const [loading, setLoading] = useState(false);
  const [isLoggedIn, setIsLoggedIn] = useState(false);

  const hasSpecials = restaurant.specials && restaurant.specials.length > 0;
  const lat = restaurant.location ? restaurant.location.latitude : restaurant.latitude;
  const lng = restaurant.location ? restaurant.location.longitude : restaurant.longitude;

  useEffect(function() { checkFavoriteStatus(); }, []);

  const checkFavoriteStatus = async () => {
    const auth = await APIService.isAuthenticated();
    setIsLoggedIn(auth);
    if (auth) {
      try {
        const user = await APIService.getCurrentUser();
        if (user && user.favorite_restaurant_ids) {
          setIsFavorite(user.favorite_restaurant_ids.includes(restaurant.id));
        }
      } catch (e) {}
    }
  };

  const toggleFavorite = async () => {
    if (!isLoggedIn) {
      Alert.alert('Login Required', 'Please sign in to save favorites', [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Sign In', onPress: function() { navigation.navigate('Login'); } }
      ]);
      return;
    }
    setLoading(true);
    try {
      if (isFavorite) {
        await APIService.removeFavorite(restaurant.id);
        setIsFavorite(false);
        Alert.alert('Removed', 'Removed from favorites');
      } else {
        await APIService.addFavorite(restaurant.id);
        setIsFavorite(true);
        Alert.alert('Saved!', 'Added to favorites');
      }
    } catch (e) {
      Alert.alert('Error', 'Could not update favorites');
    }
    setLoading(false);
  };

  const call = () => { if (restaurant.phone) Linking.openURL('tel:' + restaurant.phone); };
  const text = () => { if (restaurant.phone) Linking.openURL('sms:' + restaurant.phone.replace(/[^0-9]/g, '')); };
  const whatsapp = () => { if (restaurant.phone) Linking.openURL('whatsapp://send?phone=1' + restaurant.phone.replace(/[^0-9]/g, '')).catch(function() {}); };
  const web = () => { if (restaurant.website) Linking.openURL(restaurant.website); };
  const share = async () => { try { await Share.share({ message: 'Check out ' + restaurant.name + ' at ' + restaurant.address }); } catch (e) {} };
  const directions = () => { if (lat && lng) Linking.openURL('https://www.google.com/maps/dir/?api=1&destination=' + lat + ',' + lng); else Linking.openURL('https://www.google.com/maps/search/?api=1&query=' + encodeURIComponent(restaurant.address)); };
  const uber = () => { if (lat && lng) Linking.openURL('uber://?action=setPickup&pickup=my_location&dropoff[latitude]=' + lat + '&dropoff[longitude]=' + lng).catch(function() { Linking.openURL('https://m.uber.com/ul/?action=setPickup&pickup=my_location&dropoff[latitude]=' + lat + '&dropoff[longitude]=' + lng); }); };
  const lyft = () => { if (lat && lng) Linking.openURL('lyft://ridetype?id=lyft&destination[latitude]=' + lat + '&destination[longitude]=' + lng).catch(function() { Linking.openURL('https://www.lyft.com/ride?destination[latitude]=' + lat + '&destination[longitude]=' + lng); }); };

  return (
    <ScrollView style={styles.container}>
      <Card style={styles.card}><Card.Content>
        <View style={styles.header}>
          <View style={styles.titleContainer}>
            <Title style={styles.name}>{restaurant.name}</Title>
            {restaurant.is_mobile_vendor && <Chip icon="truck" style={styles.chip}>Food Truck</Chip>}
          </View>
          <IconButton 
            icon={isFavorite ? "heart" : "heart-outline"} 
            iconColor={isFavorite ? colors.error : colors.textLight}
            size={28}
            onPress={toggleFavorite}
            disabled={loading}
          />
        </View>
        {restaurant.rating && <View style={styles.row}><Icon name="star" size={16} color={colors.warning} /><Text style={styles.rating}>{restaurant.rating.toFixed(1)}</Text></View>}
        <View style={styles.row}><Icon name="map-marker" size={16} color={colors.textLight} /><Text style={styles.address}>{restaurant.address}</Text></View>
        {restaurant.phone && <View style={styles.row}><Icon name="phone" size={16} color={colors.textLight} /><Text style={styles.phone}>{restaurant.phone}</Text></View>}
      </Card.Content></Card>
      <Card style={styles.card}><Card.Content><Title style={styles.section}>Contact</Title><View style={styles.grid}>{restaurant.phone && <><Button mode="contained" onPress={call} icon="phone" style={styles.gridBtn}>Call</Button><Button mode="outlined" onPress={text} icon="message-text" style={styles.gridBtn}>Text</Button><Button mode="outlined" onPress={whatsapp} icon="whatsapp" style={styles.gridBtn}>WhatsApp</Button></>}{restaurant.website && <Button mode="outlined" onPress={web} icon="web" style={styles.gridBtn}>Website</Button>}<Button mode="outlined" onPress={share} icon="share-variant" style={styles.gridBtn}>Share</Button></View></Card.Content></Card>
      <Card style={styles.card}><Card.Content><Title style={styles.section}>Get a Ride</Title><View style={styles.rideRow}><Button mode="contained" onPress={uber} icon="car" style={[styles.rideBtn, { backgroundColor: '#000' }]}>Uber</Button><Button mode="contained" onPress={lyft} icon="car" style={[styles.rideBtn, { backgroundColor: '#FF00BF' }]}>Lyft</Button></View><Button mode="outlined" onPress={directions} icon="directions" style={styles.dirBtn}>Get Directions</Button></Card.Content></Card>
      <Card style={styles.card}><Card.Content><Title style={styles.section}>Current Specials</Title>{hasSpecials ? restaurant.specials.map(function(s, i) { return <List.Item key={i} title={s.name || s.title || 'Special'} description={s.description} left={function(p) { return <List.Icon {...p} icon="tag" color={colors.success} />; }} />; }) : <View style={styles.noSpecials}><Icon name="information-outline" size={32} color={colors.textLight} /><Text style={styles.noSpecialsText}>No current specials</Text></View>}</Card.Content></Card>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: colors.background },
  card: { margin: 16, marginBottom: 8 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 8 },
  titleContainer: { flex: 1 },
  name: { fontSize: 22, fontWeight: 'bold' },
  chip: { backgroundColor: '#f59e0b', marginTop: 8, alignSelf: 'flex-start' },
  row: { flexDirection: 'row', alignItems: 'center', marginTop: 4 },
  rating: { marginLeft: 4, fontWeight: '500' },
  address: { marginLeft: 4, color: '#6b7280', flex: 1 },
  phone: { marginLeft: 4, color: '#6b7280' },
  section: { fontSize: 18, marginBottom: 12 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 8 },
  gridBtn: { marginBottom: 4 },
  rideRow: { flexDirection: 'row', gap: 8, marginBottom: 12 },
  rideBtn: { flex: 1 },
  dirBtn: { marginTop: 4 },
  noSpecials: { alignItems: 'center', padding: 24 },
  noSpecialsText: { marginTop: 8, color: '#6b7280' },
});

export default RestaurantDetailScreen;
EOF
echo "Created RestaurantDetailScreen.js"

echo ""
echo "=== FIX COMPLETE ==="
echo "Now run: git add -A && git commit -m 'Fix all screens' && eas build --profile preview --platform android --clear-cache"
