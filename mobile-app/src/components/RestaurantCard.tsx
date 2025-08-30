import React from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
} from 'react-native';
import { Card, Title, Paragraph, Chip, Button } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

import { colors, spacing, borderRadius } from '../theme/colors';

interface Restaurant {
  id: string;
  name: string;
  address: string;
  phone?: string;
  website?: string;
  rating?: number;
  specials?: any[];
  specials_message?: string;
  is_mobile_vendor?: boolean;
  vendor_type?: string;
  cuisine_type?: string[];
  distance?: number;
  latitude?: number;
  longitude?: number;
}

interface RestaurantCardProps {
  restaurant: Restaurant;
  onPress: () => void;
  onToggleFavorite?: (id: string) => void;
  isFavorite?: boolean;
}

const RestaurantCard: React.FC<RestaurantCardProps> = ({
  restaurant,
  onPress,
  onToggleFavorite,
  isFavorite = false,
}) => {
  const hasSpecials = restaurant.specials && restaurant.specials.length > 0;
  const specialsCount = restaurant.specials?.length || 0;

  return (
    <Card style={styles.card} onPress={onPress}>
      <Card.Content>
        <View style={styles.header}>
          <View style={styles.titleContainer}>
            <Title style={styles.title} numberOfLines={1}>
              {restaurant.name}
            </Title>
            
            {/* Vendor type badge */}
            {restaurant.is_mobile_vendor && (
              <Chip
                icon="truck"
                style={[styles.vendorChip, { backgroundColor: colors.foodTruck }]}
                textStyle={{ color: 'white', fontSize: 12 }}
              >
                Food Truck
              </Chip>
            )}
          </View>

          {/* Favorite button */}
          {onToggleFavorite && (
            <TouchableOpacity
              onPress={() => onToggleFavorite(restaurant.id)}
              style={styles.favoriteButton}
            >
              <Icon
                name={isFavorite ? "heart" : "heart-outline"}
                size={24}
                color={isFavorite ? colors.accent : colors.textLight}
              />
            </TouchableOpacity>
          )}
        </View>

        {/* Address */}
        <View style={styles.infoRow}>
          <Icon name="map-marker" size={16} color={colors.textLight} />
          <Paragraph style={styles.address} numberOfLines={1}>
            {restaurant.address}
          </Paragraph>
        </View>

        {/* Phone */}
        {restaurant.phone && (
          <View style={styles.infoRow}>
            <Icon name="phone" size={16} color={colors.textLight} />
            <Text style={styles.contact}>{restaurant.phone}</Text>
          </View>
        )}

        {/* Rating */}
        {restaurant.rating && (
          <View style={styles.infoRow}>
            <Icon name="star" size={16} color={colors.warning} />
            <Text style={styles.rating}>
              {restaurant.rating.toFixed(1)} / 5.0
            </Text>
          </View>
        )}

        {/* Specials info */}
        <View style={styles.specialsContainer}>
          {hasSpecials ? (
            <View style={styles.specialsInfo}>
              <Icon name="tag-multiple" size={16} color={colors.success} />
              <Text style={styles.specialsText}>
                {specialsCount} special{specialsCount !== 1 ? 's' : ''} available
              </Text>
            </View>
          ) : (
            <View style={styles.specialsInfo}>
              <Icon name="information-outline" size={16} color={colors.textLight} />
              <Text style={styles.noSpecialsText}>
                No current specials
              </Text>
            </View>
          )}
        </View>

        {/* Action buttons */}
        <View style={styles.actionContainer}>
          <Button
            mode="contained"
            onPress={onPress}
            style={styles.viewButton}
            labelStyle={styles.buttonLabel}
          >
            View Details
          </Button>

          {restaurant.phone && (
            <Button
              mode="outlined"
              onPress={() => {/* Handle call */}}
              style={styles.callButton}
              labelStyle={styles.buttonLabel}
            >
              <Icon name="phone" size={16} />
            </Button>
          )}
        </View>
      </Card.Content>
    </Card>
  );
};

const styles = StyleSheet.create({
  card: {
    marginBottom: spacing.md,
    backgroundColor: colors.surface,
    borderRadius: borderRadius.lg,
    elevation: 2,
  },
  header: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: spacing.sm,
  },
  titleContainer: {
    flex: 1,
    marginRight: spacing.sm,
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    color: colors.textDark,
    marginBottom: spacing.xs,
  },
  vendorChip: {
    alignSelf: 'flex-start',
  },
  favoriteButton: {
    padding: spacing.xs,
  },
  infoRow: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.xs,
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
  rating: {
    marginLeft: spacing.xs,
    color: colors.textDark,
    fontWeight: '500',
  },
  specialsContainer: {
    marginTop: spacing.sm,
    marginBottom: spacing.md,
  },
  specialsInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  specialsText: {
    marginLeft: spacing.xs,
    color: colors.success,
    fontWeight: '500',
  },
  noSpecialsText: {
    marginLeft: spacing.xs,
    color: colors.textLight,
    fontStyle: 'italic',
  },
  actionContainer: {
    flexDirection: 'row',
    gap: spacing.sm,
  },
  viewButton: {
    flex: 1,
  },
  callButton: {
    minWidth: 60,
  },
  buttonLabel: {
    fontSize: 14,
  },
});

export default RestaurantCard;