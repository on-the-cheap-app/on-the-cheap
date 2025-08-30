import React from 'react';
import {
  SafeAreaProvider,
  SafeAreaView,
} from 'react-native-safe-area-context';
import {
  StatusBar,
  StyleSheet,
} from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { Provider as PaperProvider } from 'react-native-paper';

import AppNavigator from './src/navigation/AppNavigator';
import { theme } from './src/theme/colors';
import OneSignalService from './src/services/OneSignalService';

// Initialize OneSignal
OneSignalService.initialize();

const App = (): JSX.Element => {
  return (
    <SafeAreaProvider>
      <PaperProvider theme={theme}>
        <StatusBar
          barStyle="light-content"
          backgroundColor={theme.colors.primary}
        />
        <NavigationContainer>
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