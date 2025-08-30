import React, { useState } from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  Linking,
  Alert,
} from 'react-native';
import {
  Card,
  Title,
  Paragraph,
  Button,
  Chip,
  List,
  Divider,
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import Share from 'react-native-share';

import { colors, spacing, borderRadius } from '../theme/colors';

const RestaurantDetailScreen = ({ route, navigation }: any) => {
  const { restaurant } = route.params;
  const [isFavorite, setIsFavorite] = useState(false);

  const handleCall = () => {
    if (restaurant.phone) {
      Linking.openURL(`tel:${restaurant.phone}`);
    }
  };

  const handleWebsite = () => {
    if (restaurant.website) {
      Linking.openURL(restaurant.website);
    }
  };

  const handleShare = async () => {
    try {
      const shareOptions = {
        title: restaurant.name,
        message: `Check out ${restaurant.name} on On-the-Cheap! ${restaurant.address}`,
        url: restaurant.website || '',
      };
      await Share.open(shareOptions);
    } catch (error) {
      console.error('Share error:', error);
    }
  };

  const handleRide = (service: 'uber' | 'lyft') => {
    if (restaurant.latitude && restaurant.longitude) {
      const destination = `${restaurant.latitude},${restaurant.longitude}`;
      const url = service === 'uber' 
        ? `uber://?action=setPickup&pickup=my_location&dropoff[latitude]=${restaurant.latitude}&dropoff[longitude]=${restaurant.longitude}`
        : `lyft://ridetype?id=lyft&destination[latitude]=${restaurant.latitude}&destination[longitude]=${restaurant.longitude}`;
      
      Linking.openURL(url).catch(() => {
        Alert.alert('App not found', `${service} app is not installed`);
      });
    }
  };

  const hasSpecials = restaurant.specials && restaurant.specials.length > 0;

  return (
    <ScrollView style={styles.container}>
      {/* Restaurant Header */}
      <Card style={styles.headerCard}>
        <Card.Content>
          <View style={styles.headerContent}>
            <View style={styles.titleSection}>
              <Title style={styles.restaurantName}>{restaurant.name}</Title>
              {restaurant.is_mobile_vendor && (
                <Chip
                  icon="truck"
                  style={styles.vendorChip}
                  textStyle={{ color: 'white' }}
                >
                  Food Truck
                </Chip>
              )}
            </View>
            
            <View style={styles.ratingSection}>
              {restaurant.rating && (
                <View style={styles.rating}>
                  <Icon name="star" size={20} color={colors.warning} />
                  <Paragraph style={styles.ratingText}>
                    {restaurant.rating.toFixed(1)} / 5.0
                  </Paragraph>
                </View>
              )}
            </View>
          </View>

          <View style={styles.contactInfo}>
            <View style={styles.addressRow}>
              <Icon name="map-marker" size={16} color={colors.textLight} />
              <Paragraph style={styles.address}>{restaurant.address}</Paragraph>
            </View>
            
            {restaurant.phone && (
              <View style={styles.contactRow}>
                <Icon name="phone" size={16} color={colors.textLight} />
                <Paragraph style={styles.contact}>{restaurant.phone}</Paragraph>
              </View>
            )}
          </View>
        </Card.Content>
      </Card>

      {/* Action Buttons */}
      <Card style={styles.actionsCard}>
        <Card.Content>
          <View style={styles.actionButtons}>
            {restaurant.phone && (
              <Button
                mode="contained"
                onPress={handleCall}
                style={styles.actionButton}
              >
                <Icon name="phone" size={16} />
                Call
              </Button>
            )}
            
            {restaurant.website && (
              <Button
                mode="outlined"
                onPress={handleWebsite}
                style={styles.actionButton}
              >
                <Icon name="web" size={16} />
                Website
              </Button>
            )}
            
            <Button
              mode="outlined"
              onPress={handleShare}
              style={styles.actionButton}
            >
              <Icon name="share" size={16} />
              Share
            </Button>
          </View>

          <Divider style={styles.divider} />

          <Paragraph style={styles.sectionTitle}>Get a Ride</Paragraph>
          <View style={styles.rideButtons}>
            <Button
              mode="outlined"
              onPress={() => handleRide('uber')}
              style={styles.rideButton}
            >
              🚗 Uber
            </Button>
            <Button
              mode="outlined"
              onPress={() => handleRide('lyft')}
              style={styles.rideButton}
            >
              🚕 Lyft
            </Button>
          </View>
        </Card.Content>
      </Card>

      {/* Specials Section */}
      <Card style={styles.specialsCard}>
        <Card.Content>
          <Title>Current Specials</Title>
          
          {hasSpecials ? (
            <View style={styles.specialsList}>
              {restaurant.specials.map((special: any, index: number) => (
                <List.Item
                  key={index}
                  title={special.name || 'Special Offer'}
                  description={special.description || 'Details not available'}
                  left={(props) => <List.Icon {...props} icon="tag" color={colors.success} />}
                  style={styles.specialItem}
                />
              ))}
            </View>
          ) : (
            <View style={styles.noSpecials}>
              <Icon name="information-outline" size={32} color={colors.textLight} />
              <Paragraph style={styles.noSpecialsText}>
                No current specials available
              </Paragraph>
              <Paragraph style={styles.noSpecialsSubtext}>
                Check back later or call the restaurant for current offers
              </Paragraph>
            </View>
          )}
        </Card.Content>
      </Card>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  headerCard: {
    margin: spacing.md,
    marginBottom: spacing.sm,
  },
  headerContent: {
    marginBottom: spacing.md,
  },
  titleSection: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: spacing.sm,
  },
  restaurantName: {
    flex: 1,
    fontSize: 22,
    fontWeight: 'bold',
    color: colors.textDark,
  },
  vendorChip: {
    backgroundColor: colors.foodTruck,
    marginLeft: spacing.sm,
  },
  ratingSection: {
    alignItems: 'flex-end',
  },
  rating: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  ratingText: {
    marginLeft: spacing.xs,
    fontWeight: '500',
    color: colors.textDark,
  },
  contactInfo: {
    gap: spacing.xs,
  },
  addressRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
  },
  contactRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  address: {
    marginLeft: spacing.xs,
    color: colors.textLight,
    flex: 1,
  },
  contact: {
    marginLeft: spacing.xs,
    color: colors.textLight,
  },
  actionsCard: {
    margin: spacing.md,
    marginTop: spacing.sm,
    marginBottom: spacing.sm,
  },
  actionButtons: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  actionButton: {
    flex: 1,
  },
  divider: {
    marginVertical: spacing.md,
  },
  sectionTitle: {
    fontWeight: '600',
    color: colors.textDark,
    marginBottom: spacing.sm,
  },
  rideButtons: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  rideButton: {
    flex: 1,
  },
  specialsCard: {
    margin: spacing.md,
    marginTop: spacing.sm,
  },
  specialsList: {
    marginTop: spacing.sm,
  },
  specialItem: {
    backgroundColor: colors.backgroundLight,
    borderRadius: borderRadius.md,
    marginBottom: spacing.xs,
  },
  noSpecials: {
    alignItems: 'center',
    padding: spacing.lg,
  },
  noSpecialsText: {
    marginTop: spacing.sm,
    color: colors.textDark,
    fontWeight: '500',
  },
  noSpecialsSubtext: {
    marginTop: spacing.xs,
    color: colors.textLight,
    textAlign: 'center',
  },
});

export default RestaurantDetailScreen;