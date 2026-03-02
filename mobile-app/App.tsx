import React, { useEffect, useRef } from 'react';
import {
  SafeAreaProvider,
  SafeAreaView,
} from 'react-native-safe-area-context';
import {
  StatusBar,
  StyleSheet,
} from 'react-native';
import { NavigationContainer, NavigationContainerRef } from '@react-navigation/native';
import { Provider as PaperProvider } from 'react-native-paper';

import AppNavigator from './src/navigation/AppNavigator';
import { theme } from './src/theme/colors';
import OneSignalService from './src/services/OneSignalService';

// OneSignal App ID
const ONESIGNAL_APP_ID = 'e841b137-33e1-439c-8284-7cebb747fde7';

const App = (): React.JSX.Element => {
  const navigationRef = useRef<NavigationContainerRef<any>>(null);

  useEffect(() => {
    // Initialize OneSignal
    if (ONESIGNAL_APP_ID) {
      OneSignalService.initialize(ONESIGNAL_APP_ID);
      
      // Request notification permission
      OneSignalService.requestPermission();
      
      // Set up notification click handler for deep linking
      OneSignalService.onNotificationClick((data) => {
        if (data.restaurantId && navigationRef.current) {
          // Navigate to restaurant detail when notification is tapped
          navigationRef.current.navigate('RestaurantDetail', { 
            restaurantId: data.restaurantId 
          });
        }
      });
    } else {
      // OneSignal not configured - push notifications disabled
    }
  }, []);

  return (
    <SafeAreaProvider>
      <PaperProvider theme={theme}>
        <StatusBar
          barStyle="light-content"
          backgroundColor={theme.colors.primary}
        />
        <NavigationContainer ref={navigationRef}>
          <SafeAreaView style={styles.container}>
            <AppNavigator />
          </SafeAreaView>
        </NavigationContainer>
      </PaperProvider>
    </SafeAreaProvider>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#fef3c7', // Light orange background
  },
});

export default App;