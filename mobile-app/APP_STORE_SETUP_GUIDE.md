# Complete App Store Setup Guide

## ✅ COMPLETED: Phase 1 - Branding Materials

### What's Ready:
1. ✅ **Store Listing Text** - See `STORE_LISTING.md`
   - App name and descriptions
   - Feature lists
   - Keywords
   - What's New text
   
2. ✅ **Branding Guide** - See `BRANDING_GUIDE.md`
   - Color palette defined
   - Typography guidelines
   - Icon concepts
   - Reference images

3. ✅ **App Configuration** - Updated `app.json`
   - Proper bundle identifiers
   - Permission descriptions
   - Version numbers
   - iOS and Android settings

4. ✅ **Build Configuration** - Created `eas.json`
   - Development, Preview, and Production profiles
   - Android APK and AAB settings
   - iOS build configuration

### What Still Needs Creation:
- ⚠️ **App Icon** (1024x1024px) - Placeholder exists, needs professional design
- ⚠️ **Splash Screen** - Placeholder exists, needs professional design
- ⚠️ **Screenshots** (5-8 required) - Need to capture from running app
- ⚠️ **Privacy Policy** - Required by both stores

---

## 🎨 NEXT STEP: Create Visual Assets

### Option A: Quick & Free (30 minutes)

**Create Simple Icon Online:**

1. Go to https://www.canva.com/create/app-icons/
2. Sign up for free
3. Select "App Icon" template (1024x1024)
4. Choose orange background (#f97316)
5. Add elements:
   - Large white % symbol in center
   - Or fork/knife icon
   - Or "OTC" text
6. Keep it simple and clean
7. Download as PNG (1024x1024)
8. Save to `/app/mobile-app/assets/icon.png`

**Create Splash Screen:**

1. Use same Canva account
2. Create 1080x1920 design
3. Orange gradient background
4. Add your icon in center
5. Add "On-the-Cheap" text below
6. Download as PNG
7. Save to `/app/mobile-app/assets/splash.png`

### Option B: Professional Design (1-3 days, $20-50)

**Hire Designer on Fiverr:**

1. Go to https://www.fiverr.com/
2. Search "app icon design"
3. Choose designer with good reviews (5 stars, 100+ reviews)
4. Look for packages $20-50
5. Provide them:
   - `BRANDING_GUIDE.md`
   - `STORE_LISTING.md`
   - Reference images URLs from branding guide
6. Request:
   - App icon 1024x1024
   - Splash screen 1080x1920 and 2048x2732
   - Adaptive icon layers for Android
   - 2-3 design variations
7. Timeline: 1-3 days

**Brief for Designer:**
```
I need an app icon for my restaurant deals mobile app called "On-the-Cheap".

Requirements:
- Size: 1024x1024px
- Format: PNG with transparency
- Style: Modern, clean, flat design
- Colors: Orange (#f97316) as primary
- Elements: Food/restaurant themed with discount/deals indication
- Must be recognizable at small sizes (40px)

Also need:
- Splash screen (1080x1920 and 2048x2732)
- Android adaptive icon (foreground + background layers)

Brand info and reference images attached.
Deliver: All required sizes + source files (PSD/AI)
```

---

## 📱 STEP-BY-STEP: Taking Screenshots

### Prerequisites:
- Icon and splash screen created
- App running on your Mac

### On iOS Simulator (Mac):

1. **Start Simulator:**
```bash
cd /app/mobile-app
npm run ios
# Or: npx expo start --ios
```

2. **Select Device:**
   - Use iPhone 14 Pro or iPhone 15 Pro
   - Cmd+Shift+H to go home
   - Open your app

3. **Capture Screenshots:**
   - Navigate to key screens (see list below)
   - Press Cmd+S to save screenshot
   - Screenshots saved to Desktop
   - Resize to store requirements

4. **Required Screenshots (minimum 5):**
   - Home screen with restaurant list
   - Coupons discovery screen
   - Coupon detail with QR code
   - Map view with markers
   - Favorites/Profile screen

### On Android Emulator:

1. **Start Emulator:**
```bash
cd /app/mobile-app
npm run android
# Or: npx expo start --android
```

2. **Capture:**
   - Use Android Studio
   - Tools → AVD Manager → Camera icon
   - Or Cmd+S on Mac

### Professional Screenshot Tools:

**Add Device Frames:**
- https://mockuphone.com/ - Upload screenshot, add iPhone/Android frame
- https://www.appstorescreenshot.com/ - Create professional store screenshots
- https://placeit.net/ - Premium tool with text overlays

---

## 📄 Privacy Policy & Support Pages

### Required URLs:
- Privacy Policy: https://onthecheapapp.com/privacy-policy
- Support/Help: https://onthecheapapp.com/support
- Terms of Service: https://onthecheapapp.com/terms

### Quick Privacy Policy Generator:
1. Go to https://www.termsfeed.com/privacy-policy-generator/
2. Fill in:
   - App name: On-the-Cheap
   - Type: Mobile app
   - Collects: Location, email, preferences
   - Uses: Push notifications, analytics
3. Generate and download
4. Host on your website

---

## 🏪 Store Account Setup

### Google Play Console ($25 one-time)

**Create Account:**
1. Go to https://play.google.com/console/signup
2. Sign in with Google account
3. Accept Developer Distribution Agreement
4. Pay $25 registration fee (one-time)
5. Complete account details:
   - Developer name: "On-the-Cheap" or your company name
   - Email: Support email
   - Phone: Contact number
   - Website: https://onthecheapapp.com
6. Verification: 1-2 business days

**After Approval:**
- You can create app listing
- Upload app bundle (.aab file)
- Fill in store listing details
- Submit for review

### Apple Developer Program ($99/year)

**Create Account:**
1. Go to https://developer.apple.com/programs/enroll/
2. Sign in with Apple ID
3. Choose account type:
   - Individual: Use personal info
   - Organization: Need D-U-N-S number
4. Pay $99 annual fee
5. Agree to terms
6. Verification: 1-2 business days

**After Approval:**
- Access to App Store Connect
- Can create app listing
- Generate certificates
- Submit builds

---

## 🚀 Build & Publish Workflow

### Phase 1: Prepare Assets (Current Phase)
- ✅ Store listing text done
- ✅ App configuration done
- ⚠️ Create app icon
- ⚠️ Create splash screen
- ⚠️ Take screenshots
- ⚠️ Create privacy policy

### Phase 2: Test Build (After assets ready)
1. Install EAS CLI: `npm install -g eas-cli`
2. Login to Expo: `eas login`
3. Configure: `eas build:configure`
4. Build preview: `eas build --platform android --profile preview`
5. Test on device

### Phase 3: Production Build
1. Build Android: `eas build --platform android --profile production`
2. Download .aab file
3. Test thoroughly
4. Build iOS: `eas build --platform ios --profile production`
5. Download .ipa file

### Phase 4: Submit to Stores
1. Google Play: Upload .aab, complete listing, submit
2. App Store: Upload .ipa via Xcode or EAS submit
3. Wait for review (1-7 days)
4. App goes live!

---

## 📋 Pre-Launch Checklist

### Assets:
- [ ] App icon 1024x1024 created
- [ ] Splash screen created
- [ ] 5-8 screenshots captured
- [ ] Privacy policy written and hosted
- [ ] Support page created

### Accounts:
- [ ] Google Play Console account created ($25 paid)
- [ ] Apple Developer account created ($99 paid)
- [ ] Both accounts verified

### Configuration:
- [ ] app.json updated with correct bundle IDs
- [ ] eas.json configured
- [ ] Privacy policy URL added
- [ ] Support URL added
- [ ] All permissions justified

### Testing:
- [ ] App builds successfully
- [ ] All features work in production build
- [ ] Location permission works
- [ ] Push notifications work
- [ ] QR code scanning works
- [ ] Coupons save/load correctly
- [ ] Maps display correctly

### Store Listings:
- [ ] App name finalized
- [ ] Description written
- [ ] Keywords researched
- [ ] Category selected (Food & Drink)
- [ ] Content rating obtained
- [ ] Screenshots uploaded
- [ ] App icon uploaded

---

## 💡 Pro Tips

1. **Start with Android** - Faster approval, easier process
2. **Use TestFlight** - Beta test iOS before public release
3. **Internal Testing** - Use Google Play's internal testing first
4. **ASO (App Store Optimization)** - Research keywords before submission
5. **Respond to Reviews** - Engage with users after launch
6. **Update Regularly** - Keep app fresh with updates
7. **Monitor Crashes** - Set up crash reporting (Firebase/Sentry)
8. **Analytics** - Track user behavior to improve app

---

## 🆘 Common Issues & Solutions

**Problem: Build fails**
- Solution: Check eas.json configuration, ensure all dependencies installed

**Problem: App rejected by Apple**
- Solution: Usually permissions or privacy policy issues - read rejection carefully

**Problem: Can't generate iOS certificate**
- Solution: Need Apple Developer account first, use EAS credentials helper

**Problem: App crashes on real device**
- Solution: Test production build, not development - production is optimized differently

**Problem: Screenshots wrong size**
- Solution: Use exact device (iPhone 14 Pro, Pixel 6) for captures

---

## 📞 Support Resources

- **Expo Docs**: https://docs.expo.dev/
- **EAS Build**: https://docs.expo.dev/build/introduction/
- **Google Play Help**: https://support.google.com/googleplay/android-developer/
- **App Store Connect**: https://developer.apple.com/app-store-connect/
- **This Project**: support@onthecheapapp.com

---

## ⏱️ Current Status

**COMPLETED TODAY:**
✅ Store listing content created
✅ Branding guidelines documented
✅ App configuration updated
✅ Build configuration created
✅ Documentation complete

**NEXT ACTIONS:**
1. Create or commission app icon (1-3 days)
2. Create splash screen (same day as icon)
3. Capture 5-8 screenshots (1-2 hours)
4. Create privacy policy (1 hour)
5. Register developer accounts (if not done)

**ESTIMATED TIME TO LAUNCH:**
- If DIY assets: 1-2 weeks
- If commissioned assets: 2-3 weeks
- Android typically faster than iOS

You're now ready to create your visual assets!
