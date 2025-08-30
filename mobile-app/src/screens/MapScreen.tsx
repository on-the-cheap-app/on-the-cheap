import React, { useState, useEffect } from 'react';
import { View, StyleSheet, Alert } from 'react-native';
import MapView, { Marker, PROVIDER_GOOGLE } from 'react-native-maps';
import { FAB, Portal } from 'react-native-paper';
import Geolocation from 'react-native-geolocation-service';

import APIService from '../services/APIService';
import { colors, spacing } from '../theme/colors';

interface Restaurant {
  id: string;
  name: string;
  latitude?: number;
  longitude?: number;
  is_mobile_vendor?: boolean;
  specials?: any[];
}

const MapScreen = ({ navigation }: any) => {
  const [restaurants, setRestaurants] = useState<Restaurant[]>([]);
  const [region, setRegion] = useState({
    latitude: 37.7749,
    longitude: -122.4194,
    latitudeDelta: 0.05,
    longitudeDelta: 0.05,
  });
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    getCurrentLocation();
  }, []);

  const getCurrentLocation = () => {
    Geolocation.getCurrentPosition(
      (position) => {
        const { latitude, longitude } = position.coords;
        setRegion({
          latitude,
          longitude,
          latitudeDelta: 0.05,
          longitudeDelta: 0.05,
        });
        searchNearbyRestaurants(latitude, longitude);
      },
      (error) => {
        console.error('Location error:', error);
        Alert.alert('Location Error', 'Could not get your current location');
      },
      { enableHighAccuracy: true, timeout: 15000, maximumAge: 10000 }
    );
  };

  const searchNearbyRestaurants = async (lat: number, lng: number) => {
    setLoading(true);
    try {
      const result = await APIService.searchRestaurants({
        latitude: lat,
        longitude: lng,
        radius: 25,
      });
      
      const restaurantsWithCoords = (result.restaurants || []).filter(
        (r: Restaurant) => r.latitude && r.longitude
      );
      setRestaurants(restaurantsWithCoords);
    } catch (error) {
      console.error('Map search error:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <View style={styles.container}>
      <MapView
        provider={PROVIDER_GOOGLE}
        style={styles.map}
        region={region}
        onRegionChangeComplete={setRegion}
        showsUserLocation={true}
        showsMyLocationButton={false}
      >
        {restaurants.map((restaurant) => (
          <Marker
            key={restaurant.id}
            coordinate={{
              latitude: restaurant.latitude!,
              longitude: restaurant.longitude!,
            }}
            title={restaurant.name}
            description={`${restaurant.specials?.length || 0} specials`}
            pinColor={restaurant.is_mobile_vendor ? colors.foodTruck : colors.primary}
            onCalloutPress={() => 
              navigation.navigate('RestaurantDetail', { restaurant })
            }
          />
        ))}
      </MapView>

      <Portal>
        <FAB
          icon="crosshairs-gps"
          style={styles.fab}
          onPress={getCurrentLocation}
          loading={loading}
        />
      </Portal>
    </View>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  map: {
    flex: 1,
  },
  fab: {
    position: 'absolute',
    margin: spacing.md,
    right: 0,
    bottom: 0,
    backgroundColor: colors.primary,
  },
});

export default MapScreen;