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
} from 'react-native-paper';
import Icon from 'react-native-vector-icons/MaterialCommunityIcons';

import APIService from '../services/APIService';
import OneSignalService from '../services/OneSignalService';
import { colors, spacing } from '../theme/colors';

const ProfileScreen = ({ navigation }: any) => {
  const [user, setUser] = useState<any>(null);
  const [notificationsEnabled, setNotificationsEnabled] = useState(false);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadUserData();
    checkNotificationPermission();
  }, []);

  const loadUserData = async () => {
    try {
      const userData = await APIService.getCurrentUser();
      setUser(userData);
    } catch (error) {
      console.error('Error loading user data:', error);
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
            // Navigate to login screen or restart app
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
    return <View style={styles.container} />;
  }

  return (
    <ScrollView style={styles.container}>
      {user && (
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
      )}

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