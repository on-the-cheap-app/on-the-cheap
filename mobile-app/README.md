# On-the-Cheap Mobile App

React Native mobile application for finding restaurant specials and deals.

## Features

- 🍽️ **Restaurant Discovery**: Search for restaurants and food trucks by location
- 🗺️ **Interactive Map**: View restaurant locations with real-time data
- ❤️ **Favorites**: Save and manage favorite restaurants
- 📱 **Push Notifications**: Get notified about new specials (OneSignal integration)
- 🚗 **Ride Integration**: Direct links to Uber and Lyft
- 📞 **Contact Integration**: Call restaurants directly from the app

## Tech Stack

- **React Native 0.73**
- **React Navigation** for navigation
- **React Native Paper** for UI components
- **React Native Maps** for map functionality
- **OneSignal** for push notifications
- **AsyncStorage** for local data persistence
- **Axios** for API communication

## Getting Started

### Prerequisites

1. **React Native Development Environment**:
   - Node.js (v18+)
   - React Native CLI
   - Android Studio (for Android development)
   - Xcode (for iOS development, Mac only)

2. **Device Setup**:
   - Android: USB debugging enabled
   - iOS: Development provisioning profile

### Installation

1. **Install dependencies**:
```bash
cd mobile-app
npm install
# or
yarn install
```

2. **iOS Setup** (Mac only):
```bash
cd ios && pod install
```

3. **Android Setup**:
   - Ensure Android Studio and SDK are properly configured
   - Create AVD or connect physical device

### Configuration

1. **Backend API**: Already configured to use the production backend at `https://bargaineats.preview.emergentagent.com/api`

2. **OneSignal**: Already configured with App ID `4ca64e1c-b430-436d-8037-ffc9d4176b62`

3. **Google Maps API** (Android):
   - Add your Google Maps API key to `android/app/src/main/res/values/strings.xml`

### Running the App

1. **Start Metro Bundler**:
```bash
npm start
# or
yarn start
```

2. **Run on Android**:
```bash
npm run android
# or
yarn android
```

3. **Run on iOS** (Mac only):
```bash
npm run ios
# or
yarn ios
```

## Project Structure

```
mobile-app/
├── src/
│   ├── components/          # Reusable UI components
│   │   └── RestaurantCard.tsx
│   ├── navigation/          # Navigation configuration
│   │   └── AppNavigator.tsx
│   ├── screens/            # Screen components
│   │   ├── HomeScreen.tsx
│   │   ├── MapScreen.tsx
│   │   ├── FavoritesScreen.tsx
│   │   ├── ProfileScreen.tsx
│   │   └── RestaurantDetailScreen.tsx
│   ├── services/           # API and external services
│   │   ├── APIService.ts
│   │   └── OneSignalService.ts
│   ├── theme/              # App theming
│   │   └── colors.ts
│   └── utils/              # Utility functions
├── android/                # Android-specific code
├── ios/                    # iOS-specific code
├── App.tsx                 # Root component
├── index.js               # Entry point
└── package.json           # Dependencies
```

## API Integration

The app integrates with the existing On-the-Cheap backend:
- **Restaurant Search**: `/api/restaurants/search`
- **Geocoding**: `/api/geocode`
- **User Auth**: `/api/auth/login`, `/api/auth/register`
- **Favorites**: `/api/users/favorites`
- **Notifications**: `/api/notifications`

## Build for Release

### Android

1. **Generate signed APK**:
```bash
cd android
./gradlew assembleRelease
```

2. **Generated APK location**: `android/app/build/outputs/apk/release/app-release.apk`

### iOS

1. **Build for release**:
```bash
npm run build-ios
```

2. **Archive in Xcode** for App Store submission

## Deployment

### Google Play Store
1. Create Google Play Console account
2. Upload signed APK
3. Complete store listing
4. Submit for review

### Apple App Store  
1. Create Apple Developer account ($99/year)
2. Configure app in App Store Connect
3. Upload build via Xcode
4. Submit for review

## Features Compared to PWA

| Feature | PWA | React Native |
|---------|-----|-------------|
| Installation | Browser-based | App Store |
| Performance | Good | Excellent |
| Native APIs | Limited | Full access |
| Offline | Service Worker | AsyncStorage |
| Push Notifications | Web Push | Native Push |
| Camera/GPS | Limited | Full access |
| App Store Presence | No | Yes |

## Next Steps

1. **Test on physical devices**
2. **Add authentication UI**
3. **Implement Google Maps API key**
4. **Configure app icons and splash screens**
5. **Set up continuous integration**
6. **Prepare for app store submission**