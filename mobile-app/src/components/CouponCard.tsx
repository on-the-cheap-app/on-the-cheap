import React, { useState } from 'react';
import { View, Text, StyleSheet, TouchableOpacity, Image } from 'react-native';
import { Card, IconButton, Chip } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { Coupon, CouponType } from '../types/restaurant';
import { colors, spacing } from '../theme/colors';

interface CouponCardProps {
  coupon: Coupon;
  onPress: () => void;
  onSaveToggle?: (couponId: string, isSaved: boolean) => void;
  isSaved?: boolean;
}

const CouponCard: React.FC<CouponCardProps> = ({ 
  coupon, 
  onPress, 
  onSaveToggle,
  isSaved = false 
}) => {
  const [savedState, setSavedState] = useState(isSaved);

  const handleSaveToggle = () => {
    const newState = !savedState;
    setSavedState(newState);
    if (onSaveToggle) {
      onSaveToggle(coupon.id, newState);
    }
  };

  const getDiscountDisplay = () => {
    switch (coupon.coupon_type) {
      case CouponType.PERCENTAGE:
        return `${coupon.discount_percentage}% OFF`;
      case CouponType.FIXED_AMOUNT:
        return `$${coupon.discount_amount} OFF`;
      case CouponType.BOGO:
        return 'BUY 1 GET 1';
      case CouponType.FREE_ITEM:
        return `FREE ${coupon.free_item?.toUpperCase()}`;
      case CouponType.COMBO_DEAL:
        return `$${coupon.combo_price} DEAL`;
      default:
        return 'SPECIAL OFFER';
    }
  };

  const getCouponTypeColor = () => {
    switch (coupon.coupon_type) {
      case CouponType.PERCENTAGE:
        return '#FF6B35';
      case CouponType.FIXED_AMOUNT:
        return '#00A878';
      case CouponType.BOGO:
        return '#9B59B6';
      case CouponType.FREE_ITEM:
        return '#E74C3C';
      case CouponType.COMBO_DEAL:
        return '#3498DB';
      default:
        return colors.primary;
    }
  };

  const formatExpiryDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffTime = date.getTime() - now.getTime();
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays < 0) {
      return 'Expired';
    } else if (diffDays === 0) {
      return 'Expires today';
    } else if (diffDays === 1) {
      return 'Expires tomorrow';
    } else if (diffDays < 7) {
      return `Expires in ${diffDays} days`;
    } else {
      return date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' });
    }
  };

  const isExpiringSoon = () => {
    const date = new Date(coupon.valid_until);
    const now = new Date();
    const diffDays = Math.ceil((date.getTime() - now.getTime()) / (1000 * 60 * 60 * 24));
    return diffDays <= 3 && diffDays >= 0;
  };

  const restaurantPhoto = coupon.restaurant?.photos?.[0]?.url;

  return (
    <TouchableOpacity onPress={onPress} activeOpacity={0.7}>
      <Card style={styles.card}>
        <View style={styles.cardContent}>
          {/* Restaurant Image */}
          {restaurantPhoto && (
            <Image
              source={{ uri: restaurantPhoto }}
              style={styles.restaurantImage}
              resizeMode="cover"
            />
          )}
          
          {/* Discount Badge */}
          <View style={[styles.discountBadge, { backgroundColor: getCouponTypeColor() }]}>
            <Text style={styles.discountText}>{getDiscountDisplay()}</Text>
          </View>

          {/* Save Button */}
          {onSaveToggle && (
            <IconButton
              icon={savedState ? 'bookmark' : 'bookmark-outline'}
              iconColor={savedState ? colors.primary : '#fff'}
              size={24}
              onPress={handleSaveToggle}
              style={styles.saveButton}
            />
          )}

          {/* Content Section */}
          <View style={styles.contentSection}>
            <View style={styles.headerRow}>
              <View style={styles.titleContainer}>
                <Text style={styles.title} numberOfLines={1}>
                  {coupon.title}
                </Text>
                <Text style={styles.restaurantName} numberOfLines={1}>
                  📍 {coupon.restaurant?.name || 'Restaurant'}
                </Text>
              </View>
            </View>

            <Text style={styles.description} numberOfLines={2}>
              {coupon.description}
            </Text>

            {/* Footer Info */}
            <View style={styles.footer}>
              <View style={styles.expiryContainer}>
                <Icon 
                  name="clock-outline" 
                  size={14} 
                  color={isExpiringSoon() ? '#E74C3C' : colors.textLight} 
                />
                <Text 
                  style={[
                    styles.expiryText,
                    isExpiringSoon() && styles.expiryWarning
                  ]}
                >
                  {formatExpiryDate(coupon.valid_until)}
                </Text>
              </View>

              {coupon.minimum_purchase && (
                <Chip
                  icon="currency-usd"
                  style={styles.minPurchaseChip}
                  textStyle={styles.chipText}
                >
                  Min: ${coupon.minimum_purchase}
                </Chip>
              )}

              {coupon.total_redemptions > 0 && (
                <View style={styles.redemptionBadge}>
                  <Icon name="account-check" size={12} color={colors.textLight} />
                  <Text style={styles.redemptionText}>
                    {coupon.total_redemptions} redeemed
                  </Text>
                </View>
              )}
            </View>
          </View>
        </View>
      </Card>
    </TouchableOpacity>
  );
};

const styles = StyleSheet.create({
  card: {
    marginBottom: spacing.md,
    elevation: 3,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
    borderRadius: 12,
    overflow: 'hidden',
  },
  cardContent: {
    position: 'relative',
  },
  restaurantImage: {
    width: '100%',
    height: 160,
    backgroundColor: colors.border,
  },
  discountBadge: {
    position: 'absolute',
    top: 12,
    left: 12,
    paddingHorizontal: 16,
    paddingVertical: 8,
    borderRadius: 8,
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.25,
    shadowRadius: 4,
  },
  discountText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    letterSpacing: 0.5,
  },
  saveButton: {
    position: 'absolute',
    top: 4,
    right: 4,
    backgroundColor: 'rgba(0, 0, 0, 0.5)',
    margin: 0,
  },
  contentSection: {
    padding: spacing.md,
  },
  headerRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'flex-start',
    marginBottom: spacing.sm,
  },
  titleContainer: {
    flex: 1,
  },
  title: {
    fontSize: 18,
    fontWeight: 'bold',
    color: colors.textDark,
    marginBottom: 4,
  },
  restaurantName: {
    fontSize: 14,
    color: colors.textLight,
    fontWeight: '500',
  },
  description: {
    fontSize: 14,
    color: colors.textDark,
    lineHeight: 20,
    marginBottom: spacing.md,
  },
  footer: {
    flexDirection: 'row',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: spacing.sm,
  },
  expiryContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: colors.background,
    paddingHorizontal: 8,
    paddingVertical: 4,
    borderRadius: 4,
  },
  expiryText: {
    fontSize: 12,
    color: colors.textLight,
    marginLeft: 4,
    fontWeight: '500',
  },
  expiryWarning: {
    color: '#E74C3C',
    fontWeight: 'bold',
  },
  minPurchaseChip: {
    height: 24,
    backgroundColor: colors.background,
  },
  chipText: {
    fontSize: 11,
    marginVertical: 0,
  },
  redemptionBadge: {
    flexDirection: 'row',
    alignItems: 'center',
    paddingHorizontal: 8,
    paddingVertical: 4,
    backgroundColor: colors.background,
    borderRadius: 4,
  },
  redemptionText: {
    fontSize: 11,
    color: colors.textLight,
    marginLeft: 4,
  },
});

export default CouponCard;
