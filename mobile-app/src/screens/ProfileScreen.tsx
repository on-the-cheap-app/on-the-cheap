import React, { useState, useEffect } from 'react';
import {
  View,
  ScrollView,
  StyleSheet,
  Alert,
} from 'react-native';
import {
  Card,
  Title,
  Paragraph,
  Button,
  Switch,
  List,
  Divider,
  ActivityIndicator,
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';
import { useFocusEffect } from '@react-navigation/native';

import APIService from '../services/APIService';
import OneSignalService from '../services/OneSignalService';
import { colors, spacing } from '../theme/colors';

const ProfileScreen = ({ navigation }: any) => {
  const [user, setUser] = useState<any>(null);
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const [loading, setLoading] = useState(true);
  const [isAuthenticated, setIsAuthenticated] = useState(false);

  useEffect(() => {
    checkAuthAndLoadUser();
    checkNotificationPermission();
  }, []);

  // Refresh user data when screen gains focus (but not auth state - it's cached)
  useFocusEffect(
    React.useCallback(() => {
      // Only refresh if already authenticated (avoid auth loop)
      if (isAuthenticated) {
        refreshUserData();
      }
    }, [isAuthenticated])
  );

  const refreshUserData = async () => {
    try {
      if (isAuthenticated) {
        const userData = await APIService.getCurrentUser();
        setUser(userData);
      }
    } catch (error) {
      console.error('Error refreshing user data:', error);
    }
  };

  const checkAuthAndLoadUser = async () => {
    try {
      const authenticated = await APIService.isAuthenticated();
      setIsAuthenticated(authenticated);
      
      if (authenticated) {
        const userData = await APIService.getCurrentUser();
        setUser(userData);
      }
    } catch (error) {
      console.error('Error checking auth status:', error);
    } finally {
      setLoading(false);
    }
  };

  const checkNotificationPermission = async () => {
    const hasPermission = await OneSignalService.hasPermission();
    setNotificationsEnabled(hasPermission);
  };

  const handleNotificationToggle = async (enabled: boolean) => {
    if (enabled) {
      const granted = await OneSignalService.requestPermission();
      setNotificationsEnabled(granted);
      
      if (granted && user) {
        // Tag user for notifications
        OneSignalService.tagUser({
          user_id: user.id,
          user_type: 'user',
          notifications_enabled: true,
        });
      }
    } else {
      setNotificationsEnabled(false);
      Alert.alert(
        'Disable Notifications',
        'To disable notifications, please go to your device settings',
        [{ text: 'OK' }]
      );
    }
  };

  const handleLogin = () => {
    navigation.navigate('Login', {
      onLoginSuccess: async (userData: any) => {
        // Update local state immediately
        setUser(userData);
        setIsAuthenticated(true);
        
        // Also refresh from server to ensure consistency
        await checkAuthAndLoadUser();
      }
    });
  };

  const handleRegister = () => {
    navigation.navigate('Register', {
      onRegistrationSuccess: async (userData: any) => {
        // Update local state immediately  
        setUser(userData);
        setIsAuthenticated(true);
        
        // Also refresh from server to ensure consistency
        await checkAuthAndLoadUser();
      }
    });
  };

  const handleLogout = () => {
    Alert.alert(
      'Logout',
      'Are you sure you want to logout?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Logout',
          style: 'destructive',
          onPress: async () => {
            await APIService.logout();
            setUser(null);
            setIsAuthenticated(false);
            setNotificationsEnabled(false);
          },
        },
      ]
    );
  };

  const sendTestNotification = async () => {
    try {
      await APIService.sendTestNotification();
      Alert.alert('Test Notification', 'Test notification sent successfully!');
    } catch (error) {
      Alert.alert('Error', 'Failed to send test notification');
    }
  };

  if (loading) {
    return (
      <View style={[styles.container, styles.centerContent]}>
        <ActivityIndicator size="large" color={colors.primary} />
        <Paragraph style={styles.loadingText}>Loading profile...</Paragraph>
      </View>
    );
  }

  // Not authenticated - show login/register options
  if (!isAuthenticated || !user) {
    return (
      <ScrollView style={styles.container}>
        <View style={styles.authPrompt}>
          <Icon name="account-circle" size={80} color={colors.textLight} />
          <Title style={styles.authTitle}>Welcome to On-the-Cheap!</Title>
          <Paragraph style={styles.authSubtitle}>
            Sign in to save your favorite restaurants and get personalized recommendations
          </Paragraph>
        </View>

        <Card style={styles.authCard}>
          <Card.Content>
            <Button 
              mode="contained" 
              onPress={handleLogin}
              style={styles.authButton}
              contentStyle={styles.buttonContent}
            >
              <Icon name="login" size={16} />
              Sign In
            </Button>
            
            <Button 
              mode="outlined" 
              onPress={handleRegister}
              style={styles.authButton}
              contentStyle={styles.buttonContent}
            >
              <Icon name="account-plus" size={16} />
              Create Account
            </Button>
          </Card.Content>
        </Card>
      </ScrollView>
    );
  }

  // Authenticated - show user profile
  return (
    <ScrollView style={styles.container}>
      <Card style={styles.userCard}>
        <Card.Content>
          <View style={styles.userInfo}>
            <Icon name="account-circle" size={64} color={colors.primary} />
            <View style={styles.userDetails}>
              <Title>{user.first_name} {user.last_name}</Title>
              <Paragraph>{user.email}</Paragraph>
            </View>
          </View>
        </Card.Content>
      </Card>

      <Card style={styles.settingsCard}>
        <Card.Content>
          <Title>Notification Settings</Title>
          
          <List.Item
            title="Push Notifications"
            description="Get notified about restaurant specials"
            left={(props) => <List.Icon {...props} icon="bell" />}
            right={() => (
              <Switch
                value={notificationsEnabled}
                onValueChange={handleNotificationToggle}
              />
            )}
          />
          
          <Divider />
          
          <List.Item
            title="Test Notification"
            description="Send a test notification"
            left={(props) => <List.Icon {...props} icon="bell-ring" />}
            onPress={sendTestNotification}
            disabled={!notificationsEnabled}
          />
        </Card.Content>
      </Card>

      <Card style={styles.actionsCard}>
        <Card.Content>
          <Title>Account Actions</Title>
          
          <Button
            mode="outlined"
            onPress={handleLogout}
            style={styles.logoutButton}
            textColor={colors.error}
            contentStyle={styles.buttonContent}
          >
            <Icon name="logout" size={16} />
            Logout
          </Button>
        </Card.Content>
      </Card>

      <View style={styles.appInfo}>
        <Paragraph style={styles.appVersion}>
          On-the-Cheap v1.0.0
        </Paragraph>
      </View>
    </ScrollView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: colors.background,
    padding: spacing.md,
  },
  centerContent: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    marginTop: spacing.md,
    color: colors.textLight,
  },
  authPrompt: {
    alignItems: 'center',
    padding: spacing.xl,
    marginBottom: spacing.lg,
  },
  authTitle: {
    fontSize: 24,
    fontWeight: 'bold',
    color: colors.textDark,
    marginTop: spacing.md,
    textAlign: 'center',
  },
  authSubtitle: {
    fontSize: 16,
    color: colors.textLight,
    textAlign: 'center',
    marginTop: spacing.sm,
    lineHeight: 22,
  },
  authCard: {
    marginBottom: spacing.md,
  },
  authButton: {
    marginBottom: spacing.md,
  },
  buttonContent: {
    paddingVertical: spacing.sm,
  },
  userCard: {
    marginBottom: spacing.md,
  },
  userInfo: {
    flexDirection: 'row',
    alignItems: 'center',
  },
  userDetails: {
    marginLeft: spacing.md,
    flex: 1,
  },
  settingsCard: {
    marginBottom: spacing.md,
  },
  actionsCard: {
    marginBottom: spacing.md,
  },
  logoutButton: {
    marginTop: spacing.sm,
    borderColor: colors.error,
  },
  appInfo: {
    alignItems: 'center',
    padding: spacing.lg,
  },
  appVersion: {
    color: colors.textLight,
    fontSize: 12,
  },
});

export default ProfileScreen;