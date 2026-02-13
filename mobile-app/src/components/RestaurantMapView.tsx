import React, { useRef, useEffect, useState } from 'react';
import { View, StyleSheet, Dimensions, TouchableOpacity, Image } from 'react-native';
import { Text, Card, Chip } from 'react-native-paper';
import MapView, { Marker, Callout, PROVIDER_GOOGLE } from 'react-native-maps';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { colors, spacing, borderRadius } from '../theme/colors';
import { Restaurant } from '../types/restaurant';

interface RestaurantMapViewProps {
  restaurants: Restaurant[];
  userLocation: { latitude: number; longitude: number } | null;
  onRestaurantPress: (restaurant: Restaurant) => void;
  onToggleFavorite?: (restaurantId: string, isFavorite: boolean) => void;
}

const { width, height } = Dimensions.get('window');
const ASPECT_RATIO = width / height;
const LATITUDE_DELTA = 0.0922;
const LONGITUDE_DELTA = LATITUDE_DELTA * ASPECT_RATIO;

const RestaurantMapView: React.FC<RestaurantMapViewProps> = ({
  restaurants,
  userLocation,
  onRestaurantPress,
  onToggleFavorite,
}) => {
  const mapRef = useRef<MapView>(null);
  const [selectedRestaurant, setSelectedRestaurant] = useState<Restaurant | null>(null);

  // Helper to get coordinates from restaurant (handles both formats)
  const getCoordinates = (restaurant: Restaurant): { latitude: number; longitude: number } | null => {
    if (restaurant.latitude && restaurant.longitude) {
      return { latitude: restaurant.latitude, longitude: restaurant.longitude };
    }
    if (restaurant.location?.latitude && restaurant.location?.longitude) {
      return { latitude: restaurant.location.latitude, longitude: restaurant.location.longitude };
    }
    return null;
  };

  // Sort restaurants: those with active specials first
  const sortedRestaurants = [...restaurants].sort((a, b) => {
    const aHasSpecials = (a.specials?.length || 0) > 0;
    const bHasSpecials = (b.specials?.length || 0) > 0;
    if (aHasSpecials && !bHasSpecials) return -1;
    if (!aHasSpecials && bHasSpecials) return 1;
    return 0;
  });

  // Fit map to show all markers
  useEffect(() => {
    if (mapRef.current && restaurants.length > 0) {
      const coordinates = restaurants
        .map(r => getCoordinates(r))
        .filter((c): c is { latitude: number; longitude: number } => c !== null);
      
      if (userLocation) {
        coordinates.push(userLocation);
      }

      if (coordinates.length > 0) {
        mapRef.current.fitToCoordinates(coordinates, {
          edgePadding: { top: 50, right: 50, bottom: 150, left: 50 },
          animated: true,
        });
      }
    }
  }, [restaurants, userLocation]);

  const getMarkerColor = (restaurant: Restaurant) => {
    const hasSpecials = (restaurant.specials?.length || 0) > 0;
    if (hasSpecials) return colors.primary; // Orange for specials
    return colors.textLight; // Gray for no specials
  };

  const handleMarkerPress = (restaurant: Restaurant) => {
    setSelectedRestaurant(restaurant);
  };

  const getPhotoUrl = (restaurant: Restaurant): string | null => {
    if (restaurant.photos && restaurant.photos.length > 0) {
      return restaurant.photos[0].url;
    }
    return null;
  };

  const initialRegion = userLocation
    ? {
        latitude: userLocation.latitude,
        longitude: userLocation.longitude,
        latitudeDelta: LATITUDE_DELTA,
        longitudeDelta: LONGITUDE_DELTA,
      }
    : {
        latitude: 36.1627, // Default to Nashville
        longitude: -86.7816,
        latitudeDelta: LATITUDE_DELTA,
        longitudeDelta: LONGITUDE_DELTA,
      };

  return (
    <View style={styles.container}>
      <MapView
        ref={mapRef}
        style={styles.map}
        initialRegion={initialRegion}
        showsUserLocation={true}
        showsMyLocationButton={true}
        showsCompass={true}
        onPress={() => setSelectedRestaurant(null)}
      >
        {sortedRestaurants.map((restaurant) => {
          if (!restaurant.latitude || !restaurant.longitude) return null;
          
          const hasSpecials = (restaurant.specials?.length || 0) > 0;
          
          return (
            <Marker
              key={restaurant.id}
              coordinate={{
                latitude: restaurant.latitude,
                longitude: restaurant.longitude,
              }}
              onPress={() => handleMarkerPress(restaurant)}
              pinColor={getMarkerColor(restaurant)}
            >
              <View style={[
                styles.markerContainer,
                hasSpecials ? styles.markerWithSpecials : styles.markerNoSpecials
              ]}>
                <Icon
                  name={restaurant.is_mobile_vendor ? 'truck' : 'silverware-fork-knife'}
                  size={16}
                  color={hasSpecials ? '#fff' : colors.textLight}
                />
              </View>
            </Marker>
          );
        })}
      </MapView>

      {/* Selected Restaurant Card */}
      {selectedRestaurant && (
        <View style={styles.selectedCardContainer}>
          <Card style={styles.selectedCard} onPress={() => onRestaurantPress(selectedRestaurant)}>
            <View style={styles.cardContent}>
              {/* Photo */}
              <View style={styles.photoContainer}>
                {getPhotoUrl(selectedRestaurant) ? (
                  <Image
                    source={{ uri: getPhotoUrl(selectedRestaurant)! }}
                    style={styles.photo}
                    resizeMode="cover"
                  />
                ) : (
                  <View style={styles.photoPlaceholder}>
                    <Icon name="silverware-fork-knife" size={24} color={colors.textLight} />
                  </View>
                )}
              </View>

              {/* Info */}
              <View style={styles.infoContainer}>
                <View style={styles.headerRow}>
                  <Text style={styles.restaurantName} numberOfLines={1}>
                    {selectedRestaurant.name}
                  </Text>
                  {selectedRestaurant.is_mobile_vendor && (
                    <Chip style={styles.foodTruckChip} textStyle={styles.foodTruckText}>
                      Food Truck
                    </Chip>
                  )}
                </View>

                <View style={styles.ratingRow}>
                  {selectedRestaurant.rating && (
                    <View style={styles.rating}>
                      <Icon name="star" size={14} color={colors.warning} />
                      <Text style={styles.ratingText}>{selectedRestaurant.rating.toFixed(1)}</Text>
                    </View>
                  )}
                  {selectedRestaurant.distance && (
                    <Text style={styles.distance}>
                      {selectedRestaurant.distance < 1000
                        ? `${selectedRestaurant.distance}m`
                        : `${(selectedRestaurant.distance / 1609).toFixed(1)}mi`}
                    </Text>
                  )}
                </View>

                {/* Specials Count */}
                {(selectedRestaurant.specials?.length || 0) > 0 ? (
                  <View style={styles.specialsBadge}>
                    <Icon name="tag" size={12} color="#fff" />
                    <Text style={styles.specialsText}>
                      {selectedRestaurant.specials!.length} Active Special{selectedRestaurant.specials!.length !== 1 ? 's' : ''}
                    </Text>
                  </View>
                ) : (
                  <Text style={styles.noSpecials}>No active specials</Text>
                )}
              </View>

              {/* Arrow */}
              <View style={styles.arrowContainer}>
                <Icon name="chevron-right" size={24} color={colors.textLight} />
              </View>
            </View>
          </Card>

          {/* Close button */}
          <TouchableOpacity
            style={styles.closeButton}
            onPress={() => setSelectedRestaurant(null)}
          >
            <Icon name="close" size={20} color={colors.textDark} />
          </TouchableOpacity>
        </View>
      )}

      {/* Map Legend */}
      <View style={styles.legend}>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: colors.primary }]} />
          <Text style={styles.legendText}>With Specials</Text>
        </View>
        <View style={styles.legendItem}>
          <View style={[styles.legendDot, { backgroundColor: colors.textLight }]} />
          <Text style={styles.legendText}>No Specials</Text>
        </View>
      </View>
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
  markerContainer: {
    width: 32,
    height: 32,
    borderRadius: 16,
    justifyContent: 'center',
    alignItems: 'center',
    borderWidth: 2,
    borderColor: '#fff',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
    elevation: 5,
  },
  markerWithSpecials: {
    backgroundColor: colors.primary,
  },
  markerNoSpecials: {
    backgroundColor: '#f3f4f6',
  },
  selectedCardContainer: {
    position: 'absolute',
    bottom: spacing.lg,
    left: spacing.md,
    right: spacing.md,
  },
  selectedCard: {
    borderRadius: borderRadius.lg,
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.2,
    shadowRadius: 4,
  },
  cardContent: {
    flexDirection: 'row',
    padding: spacing.sm,
    alignItems: 'center',
  },
  photoContainer: {
    width: 70,
    height: 70,
    borderRadius: borderRadius.md,
    overflow: 'hidden',
    marginRight: spacing.sm,
  },
  photo: {
    width: '100%',
    height: '100%',
  },
  photoPlaceholder: {
    width: '100%',
    height: '100%',
    backgroundColor: colors.background,
    justifyContent: 'center',
    alignItems: 'center',
  },
  infoContainer: {
    flex: 1,
  },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  restaurantName: {
    fontSize: 16,
    fontWeight: 'bold',
    color: colors.textDark,
    flex: 1,
  },
  foodTruckChip: {
    height: 20,
    backgroundColor: colors.foodTruck,
    marginLeft: spacing.xs,
  },
  foodTruckText: {
    fontSize: 10,
    color: '#fff',
  },
  ratingRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  rating: {
    flexDirection: 'row',
    alignItems: 'center',
    marginRight: spacing.sm,
  },
  ratingText: {
    fontSize: 12,
    color: colors.textDark,
    marginLeft: 2,
  },
  distance: {
    fontSize: 12,
    color: colors.textLight,
  },
  specialsBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.primary,
    paddingHorizontal: spacing.sm,
    paddingVertical: 2,
    borderRadius: borderRadius.sm,
    alignSelf: 'flex-start',
  },
  specialsText: {
    fontSize: 11,
    color: '#fff',
    marginLeft: 4,
    fontWeight: '600',
  },
  noSpecials: {
    fontSize: 12,
    color: colors.textLight,
    fontStyle: 'italic',
  },
  arrowContainer: {
    paddingLeft: spacing.sm,
  },
  closeButton: {
    position: 'absolute',
    top: -10,
    right: -5,
    backgroundColor: '#fff',
    borderRadius: 15,
    width: 30,
    height: 30,
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.2,
    shadowRadius: 2,
    elevation: 3,
  },
  legend: {
    position: 'absolute',
    top: spacing.md,
    right: spacing.md,
    backgroundColor: 'rgba(255, 255, 255, 0.95)',
    borderRadius: borderRadius.md,
    padding: spacing.sm,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.15,
    shadowRadius: 2,
    elevation: 2,
  },
  legendItem: {
    flexDirection: 'row',
    alignItems: 'center',
    marginVertical: 2,
  },
  legendDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: spacing.xs,
  },
  legendText: {
    fontSize: 11,
    color: colors.textDark,
  },
});

export default RestaurantMapView;
