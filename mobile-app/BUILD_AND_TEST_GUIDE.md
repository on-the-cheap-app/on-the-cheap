# Build and Test Guide - On the Cheap Mobile App

## Latest Features to Test (February 2026)

### 🗺️ Map View
- Toggle between List/Map view on home screen
- Custom markers (orange = has specials, gray = no specials)
- Tap marker to see restaurant preview card
- Tap preview card to open restaurant detail

### 🔔 Push Notifications
- OneSignal App ID: `e841b137-33e1-439c-8284-7cebb747fde7`
- Notification preferences in Profile screen
- Receives notifications for favorites' new specials

---

## Prerequisites

Before building, you need:
- [ ] EAS CLI installed (`npm install -g eas-cli`)
- [ ] Expo account (create at https://expo.dev)
- [ ] Android device or iOS device for testing

---

## Step 1: Login to EAS

```bash
cd /app/mobile-app
eas login
```

Enter your Expo account credentials.

---

## Step 2: Configure EAS Project

```bash
eas build:configure
```

This will link your project to your Expo account.

---

## Step 3: Build Preview/Test Version

### For Android (APK - easiest to test):

```bash
eas build --profile preview --platform android
```

This will:
- Upload your code to EAS servers
- Build an APK file
- Provide a download link when complete (~15-20 minutes)

### For iOS (requires Apple Developer account):

```bash
eas build --profile preview --platform ios
```

---

## Step 4: Install on Your Device

### Android:
1. Wait for build to complete
2. Click the download link from EAS
3. Download APK to your Android device
4. Enable "Install from Unknown Sources" in settings
5. Tap the APK file to install
6. Open "On the Cheap" app

### iOS:
1. Wait for build to complete
2. Open the link on your iOS device
3. Follow instructions to install via TestFlight or Ad-Hoc

---

## Step 5: Test Key Features

### Customer/Diner Flow:
- [ ] Open app - splash screen appears
- [ ] Allow location permission
- [ ] View list of nearby restaurant specials
- [ ] Tap on a special to see details
- [ ] Filter specials by cuisine/price
- [ ] Save a special to favorites
- [ ] View coupons tab
- [ ] Tap on a coupon to see QR code
- [ ] Search for specific restaurants
- [ ] View restaurant details (hours, menu, directions)

### Owner Flow (if accessible via mobile):
- [ ] Login as restaurant owner
- [ ] View owner dashboard
- [ ] Add/edit restaurant
- [ ] Create special
- [ ] Manage coupons

---

## Step 6: Take Screenshots

While testing, take screenshots of:

### Must-Have Screens (5-8 screenshots):

1. **Home/Special List** - Shows nearby restaurant specials
2. **Special Detail** - Shows a specific deal with restaurant info
3. **Coupons List** - Browse digital coupons
4. **Coupon Detail** - Shows QR code for redemption
5. **Filters** - Search/filter by cuisine, price, distance
6. **Restaurant Detail** - Restaurant profile with info
7. **Favorites** - Saved specials
8. **Map View** - Specials shown on map (optional)

### How to Take Screenshots:

**Android:**
- Press Power + Volume Down simultaneously
- Screenshots saved to Photos/Screenshots folder

**iOS:**
- iPhone with Face ID: Press Side + Volume Up
- iPhone with Home button: Press Home + Side button
- Screenshots saved to Photos app

---

## Step 7: Transfer Screenshots to Computer

### Android:
1. Connect phone to computer via USB
2. Enable "File Transfer" mode
3. Navigate to DCIM/Screenshots
4. Copy screenshot files

### iOS:
1. AirDrop to Mac, OR
2. Email screenshots to yourself, OR
3. Use iCloud Photos sync

---

## Screenshot Requirements

### Android (Google Play):
- **Minimum:** 2 screenshots
- **Maximum:** 8 screenshots
- **Size:** 1080 x 1920 pixels (9:16 aspect ratio)
- **Format:** PNG or JPEG

### iOS (App Store):
- **6.7" iPhone:** 1290 x 2796 pixels (iPhone 14 Pro Max, 15 Pro Max)
- **5.5" iPhone:** 1242 x 2208 pixels (iPhone 8 Plus)
- **Minimum:** 3 screenshots
- **Maximum:** 10 screenshots

---

## Troubleshooting

### Build Fails:
- Check EAS CLI is up to date: `npm install -g eas-cli@latest`
- Verify you're logged in: `eas whoami`
- Check build logs in EAS dashboard

### App Won't Install (Android):
- Enable "Install from Unknown Sources"
- Try downloading APK again
- Clear browser cache and re-download

### App Crashes on Launch:
- Check if location permission is granted
- Verify API_URL is set correctly in eas.json
- Check device logs in Android Studio or Xcode

### Location Not Working:
- Ensure location permissions are granted
- Try enabling "High Accuracy" location mode
- Check if GPS is enabled on device

---

## Production Build (When Ready for Store Submission)

### Android (App Bundle for Google Play):

```bash
eas build --profile production --platform android
```

This creates an .aab file (Android App Bundle) required by Google Play.

### iOS (For App Store):

```bash
eas build --profile production --platform ios
```

This creates an .ipa file for App Store submission.

---

## Next Steps After Testing

1. ✅ Confirm all features work correctly
2. ✅ Collect 5-8 high-quality screenshots
3. ✅ Note any bugs or issues to fix
4. ✅ Get screenshots to me for formatting
5. ✅ Create feature graphic from screenshots
6. ✅ Build production version
7. ✅ Submit to stores!

---

## Need Help?

If you encounter any issues:
- Share error messages
- Send build logs
- Describe what's not working

I'll help troubleshoot and get your app ready for submission!

---

## Testing New Features (February 2026)

### Map View Testing Checklist

1. **Search for restaurants:**
   - Enter a location (e.g., "New Orleans, LA")
   - Click "Near Me" or enter an address

2. **Toggle to Map View:**
   - Look for "Found X restaurants" section
   - Tap the "Map" toggle button (next to "List")
   - Map should appear with restaurant markers

3. **Verify Markers:**
   - Orange markers = restaurants with active specials
   - Gray markers = restaurants without specials
   - Truck icon = food trucks
   - Fork & knife icon = regular restaurants

4. **Test Interactions:**
   - Tap a marker → preview card should appear
   - Tap preview card → should navigate to restaurant detail
   - Tap X button → should close preview card
   - Pinch to zoom, drag to pan the map

5. **Check Legend:**
   - Top-right corner should show legend explaining marker colors

### Push Notifications Testing Checklist

1. **Enable Notifications:**
   - Go to Profile tab
   - Sign in if not already
   - Toggle "Push Notifications" ON
   - Accept system permission prompt

2. **Configure Preferences:**
   - "New Specials" - notifications for favorites' new deals
   - "Specials Starting Soon" - 30 min reminder
   - "Daily Digest" - morning summary

3. **Test Notification Flow:**
   - Add a restaurant to favorites (heart icon)
   - Have an owner create a new special for that restaurant
   - You should receive a push notification

4. **Test Deep Linking:**
   - When you tap the notification, app should open to that restaurant's detail page

### Test Accounts
- **Customer:** sfurtwengler@gmail.com / DrFurt138!
- **Owner (web):** demo@onthecheapapp.com / Demo123!

### Backend API for Manual Testing
```bash
# Test notification endpoint (replace IDs)
curl -X POST "https://deals-alert-staging.preview.emergentagent.com/api/notifications/favorite-special?restaurant_id=YOUR_RESTAURANT_ID&special_title=Test%20Special&special_description=50%25%20off%20lunch"
```

---

## Quick Commands

```bash
# Build preview APK
eas build --profile preview --platform android

# Check build status
eas build:list

# Update over-the-air (after first build)
eas update --branch preview --message "Map and notifications update"
```
