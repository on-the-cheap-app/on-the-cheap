import React, { useState, useEffect } from 'react';
import {
  View,
  Text,
  ScrollView,
  StyleSheet,
  Image,
  Share,
  Alert,
  TouchableOpacity,
} from 'react-native';
import {
  Button,
  Card,
  Title,
  Paragraph,
  Chip,
  Divider,
  ActivityIndicator,
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { Coupon, CouponType } from '../types/restaurant';
import { colors, spacing } from '../theme/colors';
import APIService from '../services/APIService';

const CouponDetailScreen = ({ route, navigation }: any) => {
  const { coupon: initialCoupon } = route.params;
  const [coupon, setCoupon] = useState<Coupon>(initialCoupon);
  const [isSaved, setIsSaved] = useState(false);
  const [loading, setLoading] = useState(false);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    checkAuthentication();
    loadCouponDetails();
  }, []);

  const checkAuthentication = async () => {
    const authenticated = await APIService.isAuthenticated();
    setIsAuthenticated(authenticated);
  };

  const loadCouponDetails = async () => {
    try {
      const result = await APIService.getCouponDetails(initialCoupon.id);
      setCoupon(result);
    } catch (error) {
      console.error('Error loading coupon details:', error);
    }
  };

  const getDiscountDisplay = () => {
    switch (coupon.coupon_type) {
      case CouponType.PERCENTAGE:
        return `${coupon.discount_percentage}% OFF`;
      case CouponType.FIXED_AMOUNT:
        return `$${coupon.discount_amount} OFF`;
      case CouponType.BOGO:
        return 'BUY 1 GET 1 FREE';
      case CouponType.FREE_ITEM:
        return `FREE ${coupon.free_item?.toUpperCase()}`;
      case CouponType.COMBO_DEAL:
        return `$${coupon.combo_price} COMBO DEAL`;
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

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'long',
      day: 'numeric',
      year: 'numeric',
    });
  };

  const formatDaysOfWeek = (days: string[]) => {
    if (days.length === 7) return 'Every day';
    return days.map(d => d.charAt(0).toUpperCase() + d.slice(1, 3)).join(', ');
  };

  const handleSaveToggle = async () => {
    if (!isAuthenticated) {
      Alert.alert('Login Required', 'Please login to save coupons', [
        { text: 'Cancel', style: 'cancel' },
        { text: 'Login', onPress: () => navigation.navigate('Login') }
      ]);
      return;
    }

    setLoading(true);
    try {
      if (isSaved) {
        await APIService.removeSavedCoupon(coupon.id);
        setIsSaved(false);
        Alert.alert('Removed', 'Coupon removed from your saved collection');
      } else {
        await APIService.saveCoupon(coupon.id);
        setIsSaved(true);
        Alert.alert('Saved!', 'Coupon saved to your collection');
      }
    } catch (error) {
      console.error('Error toggling save:', error);
      Alert.alert('Error', 'Could not save coupon. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const handleShare = async () => {
    try {
      await Share.share({
        message: `Check out this deal at ${coupon.restaurant?.name}: ${coupon.title} - ${getDiscountDisplay()}`,
        title: coupon.title,
      });
    } catch (error) {
      console.error('Error sharing:', error);
    }
  };

  const restaurantPhoto = coupon.restaurant?.photos?.[0]?.url;

  return (
    <ScrollView style={styles.container}>
      {/* Header Image */}
      {restaurantPhoto && (
        <Image
          source={{ uri: restaurantPhoto }}
          style={styles.headerImage}
          resizeMode="cover"
        />
      )}

      {/* Discount Badge */}
      <View style={[styles.discountBanner, { backgroundColor: getCouponTypeColor() }]}>
        <Text style={styles.discountText}>{getDiscountDisplay()}</Text>
      </View>

      {/* Main Content */}
      <View style={styles.content}>
        {/* Title Section */}
        <View style={styles.titleSection}>
          <Title style={styles.title}>{coupon.title}</Title>
          <View style={styles.restaurantInfo}>
            <Icon name="store" size={20} color={colors.primary} />
            <Text style={styles.restaurantName}>{coupon.restaurant?.name}</Text>
          </View>
          <Text style={styles.address}>{coupon.restaurant?.address}</Text>
        </View>

        {/* Action Buttons */}
        <View style={styles.actionButtons}>
          <Button
            mode="contained"
            onPress={handleSaveToggle}
            icon={isSaved ? 'bookmark' : 'bookmark-outline'}
            style={[styles.actionButton, styles.saveButton]}
            loading={loading}
            disabled={loading}
          >
            {isSaved ? 'Saved' : 'Save'}
          </Button>
          <Button
            mode="outlined"
            onPress={handleShare}
            icon="share-variant"
            style={styles.actionButton}
          >
            Share
          </Button>
        </View>

        <Divider style={styles.divider} />

        {/* Description */}
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>About This Offer</Text>
            <Text style={styles.description}>{coupon.description}</Text>

            {coupon.promotional_message && (
              <View style={styles.promoContainer}>
                <Icon name="star" size={16} color={colors.primary} />
                <Text style={styles.promoMessage}>{coupon.promotional_message}</Text>
              </View>
            )}
          </Card.Content>
        </Card>

        {/* QR Code Section */}
        {coupon.qr_code && (
          <Card style={styles.card}>
            <Card.Content style={styles.qrSection}>
              <Text style={styles.sectionTitle}>Redeem at Restaurant</Text>
              <Text style={styles.qrInstructions}>
                Show this QR code to the staff to redeem your coupon
              </Text>
              <View style={styles.qrCodeContainer}>
                <Image
                  source={{ uri: coupon.qr_code }}
                  style={styles.qrCode}
                  resizeMode="contain"
                />
              </View>
              <View style={styles.redemptionCodeContainer}>
                <Text style={styles.redemptionCodeLabel}>Redemption Code:</Text>
                <Text style={styles.redemptionCode}>{coupon.redemption_code}</Text>
              </View>
            </Card.Content>
          </Card>
        )}

        {/* Coupon Details */}
        <Card style={styles.card}>
          <Card.Content>
            <Text style={styles.sectionTitle}>Coupon Details</Text>

            <View style={styles.detailRow}>
              <Icon name="calendar-range" size={20} color={colors.textLight} />
              <View style={styles.detailText}>
                <Text style={styles.detailLabel}>Valid Period</Text>
                <Text style={styles.detailValue}>
                  {formatDate(coupon.valid_from)} - {formatDate(coupon.valid_until)}
                </Text>
              </View>
            </View>

            <View style={styles.detailRow}>
              <Icon name="calendar-week" size={20} color={colors.textLight} />
              <View style={styles.detailText}>
                <Text style={styles.detailLabel}>Available Days</Text>
                <Text style={styles.detailValue}>{formatDaysOfWeek(coupon.days_of_week)}</Text>
              </View>
            </View>

            {coupon.time_restrictions && (
              <View style={styles.detailRow}>
                <Icon name="clock-outline" size={20} color={colors.textLight} />
                <View style={styles.detailText}>
                  <Text style={styles.detailLabel}>Time Restrictions</Text>
                  <Text style={styles.detailValue}>
                    {coupon.time_restrictions.start} - {coupon.time_restrictions.end}
                  </Text>
                </View>
              </View>
            )}

            {coupon.minimum_purchase && (
              <View style={styles.detailRow}>
                <Icon name="currency-usd" size={20} color={colors.textLight} />
                <View style={styles.detailText}>
                  <Text style={styles.detailLabel}>Minimum Purchase</Text>
                  <Text style={styles.detailValue}>${coupon.minimum_purchase}</Text>
                </View>
              </View>
            )}

            <View style={styles.detailRow}>
              <Icon name="account-check" size={20} color={colors.textLight} />
              <View style={styles.detailText}>
                <Text style={styles.detailLabel}>Max Uses Per Customer</Text>
                <Text style={styles.detailValue}>{coupon.max_per_customer}</Text>
              </View>
            </View>

            {coupon.max_redemptions && (
              <View style={styles.detailRow}>
                <Icon name="ticket-percent" size={20} color={colors.textLight} />
                <View style={styles.detailText}>
                  <Text style={styles.detailLabel}>Total Available</Text>
                  <Text style={styles.detailValue}>
                    {coupon.max_redemptions - coupon.total_redemptions} remaining
                  </Text>
                </View>
              </View>
            )}
          </Card.Content>
        </Card>

        {/* Terms & Conditions */}
        {coupon.terms_conditions && (
          <Card style={styles.card}>
            <Card.Content>
              <Text style={styles.sectionTitle}>Terms & Conditions</Text>
              <Text style={styles.termsText}>{coupon.terms_conditions}</Text>
            </Card.Content>
          </Card>
        )}

        {/* Stats */}
        {coupon.total_redemptions > 0 && (
          <View style={styles.statsContainer}>
            <View style={styles.statItem}>
              <Icon name="account-check" size={24} color={colors.primary} />
              <Text style={styles.statValue}>{coupon.total_redemptions}</Text>
              <Text style={styles.statLabel}>Redeemed</Text>
            </View>
            <View style={styles.statItem}>
              <Icon name="eye" size={24} color={colors.primary} />
              <Text style={styles.statValue}>{coupon.views}</Text>
              <Text style={styles.statLabel}>Views</Text>
            </View>
            <View style={styles.statItem}>
              <Icon name="bookmark" size={24} color={colors.primary} />
              <Text style={styles.statValue}>{coupon.saves}</Text>
              <Text style={styles.statLabel}>Saves</Text>
            </View>
          </View>
        )}
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  headerImage: {
    width: '100%',
    height: 200,
    backgroundColor: colors.border,
  },
  discountBanner: {
    paddingVertical: spacing.lg,
    alignItems: 'center',
  },
  discountText: {
    color: '#fff',
    fontSize: 28,
    fontWeight: 'bold',
    letterSpacing: 1,
  },
  content: {
    padding: spacing.md,
  },
  titleSection: {
    marginBottom: spacing.md,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: colors.textDark,
    marginBottom: spacing.sm,
  },
  restaurantInfo: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: spacing.xs,
  },
  restaurantName: {
    fontSize: 18,
    fontWeight: '600',
    color: colors.textDark,
    marginLeft: spacing.sm,
  },
  address: {
    fontSize: 14,
    color: colors.textLight,
    marginLeft: 28,
  },
  actionButtons: {
    flexDirection: 'row',
    gap: spacing.sm,
    marginBottom: spacing.md,
  },
  actionButton: {
    flex: 1,
  },
  saveButton: {
    backgroundColor: colors.primary,
  },
  divider: {
    marginVertical: spacing.md,
  },
  card: {
    marginBottom: spacing.md,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  sectionTitle: {
    fontSize: 18,
    fontWeight: 'bold',
    color: colors.textDark,
    marginBottom: spacing.md,
  },
  description: {
    fontSize: 16,
    color: colors.textDark,
    lineHeight: 24,
  },
  promoContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginTop: spacing.md,
    padding: spacing.sm,
    backgroundColor: '#FFF3E0',
    borderRadius: 8,
  },
  promoMessage: {
    fontSize: 14,
    fontWeight: '600',
    color: '#E65100',
    marginLeft: spacing.sm,
    flex: 1,
  },
  qrSection: {
    alignItems: 'center',
  },
  qrInstructions: {
    fontSize: 14,
    color: colors.textLight,
    textAlign: 'center',
    marginBottom: spacing.lg,
  },
  qrCodeContainer: {
    padding: spacing.lg,
    backgroundColor: '#fff',
    borderRadius: 12,
    elevation: 4,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.15,
    shadowRadius: 4,
  },
  qrCode: {
    width: 200,
    height: 200,
  },
  redemptionCodeContainer: {
    marginTop: spacing.lg,
    padding: spacing.md,
    backgroundColor: colors.background,
    borderRadius: 8,
    alignItems: 'center',
  },
  redemptionCodeLabel: {
    fontSize: 12,
    color: colors.textLight,
    marginBottom: spacing.xs,
  },
  redemptionCode: {
    fontSize: 24,
    fontWeight: 'bold',
    color: colors.textDark,
    letterSpacing: 2,
  },
  detailRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: spacing.md,
  },
  detailText: {
    marginLeft: spacing.md,
    flex: 1,
  },
  detailLabel: {
    fontSize: 12,
    color: colors.textLight,
    marginBottom: 2,
  },
  detailValue: {
    fontSize: 16,
    color: colors.textDark,
    fontWeight: '500',
  },
  termsText: {
    fontSize: 14,
    color: colors.textDark,
    lineHeight: 20,
  },
  statsContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    padding: spacing.lg,
    backgroundColor: '#fff',
    borderRadius: 12,
    elevation: 2,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.1,
    shadowRadius: 2,
  },
  statItem: {
    alignItems: 'center',
  },
  statValue: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.textDark,
    marginTop: spacing.xs,
  },
  statLabel: {
    fontSize: 12,
    color: colors.textLight,
    marginTop: 2,
  },
});

export default CouponDetailScreen;
