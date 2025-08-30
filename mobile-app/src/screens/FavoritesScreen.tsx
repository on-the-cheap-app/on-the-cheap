import React, { useState, useEffect } from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  RefreshControl,
} from 'react-native';
import { Text, ActivityIndicator } from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

import APIService from '../services/APIService';
import RestaurantCard from '../components/RestaurantCard';
import { colors, spacing } from '../theme/colors';

const FavoritesScreen = ({ navigation }: any) => {
  const [favorites, setFavorites] = useState([]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);

  useEffect(() => {
    loadFavorites();
  }, []);

  const loadFavorites = async () => {
    try {
      const result = await APIService.getFavorites();
      setFavorites(result.favorites || []);
    } catch (error) {
      console.error('Error loading favorites:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleToggleFavorite = async (restaurantId: string) => {
    try {
      await APIService.toggleFavorite(restaurantId);
      // Remove from favorites list
      setFavorites(prev => prev.filter((fav: any) => fav.id !== restaurantId));
    } catch (error) {
      console.error('Error toggling favorite:', error);
    }
  };

  const onRefresh = async () => {
    setRefreshing(true);
    await loadFavorites();
    setRefreshing(false);
  };

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color={colors.primary} />
      </View>
    );
  }

  return (
    <ScrollView
      style={styles.container}
      refreshControl={
        <RefreshControl refreshing={refreshing} onRefresh={onRefresh} />
      }
    >
      {favorites.length > 0 ? (
        <View style={styles.content}>
          <Text style={styles.title}>
            Your Favorite Restaurants ({favorites.length})
          </Text>
          {favorites.map((restaurant: any) => (
            <RestaurantCard
              key={restaurant.id}
              restaurant={restaurant}
              onPress={() => navigation.navigate('RestaurantDetail', { restaurant })}
              onToggleFavorite={handleToggleFavorite}
              isFavorite={true}
            />
          ))}
        </View>
      ) : (
        <View style={styles.emptyContainer}>
          <Icon name="heart-outline" size={64} color={colors.textLight} />
          <Text style={styles.emptyTitle}>No Favorites Yet</Text>
          <Text style={styles.emptyText}>
            Add restaurants to your favorites by tapping the heart icon
          </Text>
        </View>
      )}
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
  },
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  content: {
    padding: spacing.md,
  },
  title: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.textDark,
    marginBottom: spacing.md,
  },
  emptyContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: spacing.xl,
  },
  emptyTitle: {
    fontSize: 20,
    fontWeight: 'bold',
    color: colors.textDark,
    marginTop: spacing.md,
    marginBottom: spacing.sm,
  },
  emptyText: {
    color: colors.textLight,
    textAlign: 'center',
  },
});

export default FavoritesScreen;