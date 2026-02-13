# On-the-Cheap - Product Requirements Document

## Original Problem Statement
A restaurant deals mobile app and web platform that helps users find restaurant specials, happy hours, and food deals near them.

## Current Status (January 27, 2026)

### Web App - PRODUCTION READY ✅
- ✅ Customer experience working (search, favorites, share)
- ✅ Owner login and dashboard
- ✅ **Stripe subscription checkout WORKING**
- ✅ Privacy Policy page: `/privacy`
- ✅ Account Deletion page: `/delete-account`
- ✅ **Partner Info page**: `/partner-info` - Added to header navigation
- ✅ **Referral Program** - Owners can earn rewards by referring other owners
- ✅ WhatsApp share working
- ✅ Create/Manage Specials feature with image upload
- ✅ Timezone support for specials filtering
- ✅ **Filter Auto-Refresh** - Filters update results automatically
- ✅ **Customer "Favorites" button** - Accessible in header after login
- ✅ **"Add Your Own Restaurant"** - Owners can add venues not in database
- ✅ **Owner login as customer** - Same credentials work in both portals
- ✅ **Transfer Restaurant Ownership** - Transfer restaurants to other owners
- ✅ **Delete Owner Profile** - Owners can delete their account
- ✅ **New Orleans Restaurant Data** - 565 restaurants imported with Yelp enrichment

### Referral Program Details
- **New owners get**: 10% off first 6 months when using a referral code
- **Referrers get**: 20% one-time discount after referred owner stays 6 months
- **Features**:
  - Unique referral code per owner (auto-generated)
  - Referral code validation during signup
  - Dashboard showing referral stats and status
  - Copy referral code and share message functionality

### Mobile App (Android)
- ⚠️ **BLOCKED** - Non-functional due to incorrect backend URL in APIService.js
- User has fixed the code locally but waiting for EAS build limit reset

### Data Enrichment Pipeline ✅ COMPLETE
- **Phase 1**: Cleaned and segmented 1,206 New Orleans restaurants
- **Phase 2**: Web scraped 305 websites, found 15 new emails
- **Phase 3**: Yelp enrichment - 552/565 matched (97.7% match rate)
- **Phase 4**: Imported 565 restaurants into database
- **Output files**: Available at `/app/exports/`

## Test Accounts
- **Customer:** sfurtwengler@gmail.com / DrFurt138!
- **Owner:** demo@onthecheapapp.com / Demo123!

**Note:** These credentials work on the preview environment. For production (onthecheapapp.com), ensure the production deployment environment variables are set correctly:
- `DB_NAME=onthecheap_production`
- `MONGO_URL` pointing to the correct MongoDB Atlas cluster

## Key URLs
- Production: https://www.onthecheapapp.com
- Preview: https://owner-mgmt.preview.emergentagent.com
- Privacy Policy: https://www.onthecheapapp.com/privacy
- Partner Info: https://www.onthecheapapp.com/partner-info

## Manually Added Restaurants
- Avenue Pub - 1732 St. Charles Ave, New Orleans, LA 70130
- Oh My Chives - 7332 Nolensville Rd, Suite 304, Nolensville, TN 37135

## Recent Changes (February 13, 2026)

### New Features
1. **Mobile Map View** - Toggle between list and map view on home screen
   - Custom markers showing restaurants with/without active specials
   - Restaurant preview card when tapping markers
   - Legend showing marker colors
   - Auto-fits map to show all restaurants

2. **Push Notifications System** - Full OneSignal integration
   - Mobile app: OneSignal SDK initialization
   - Mobile app: User tagging for favorites targeting
   - Mobile app: Notification preferences (new specials, starting soon, daily digest)
   - Backend: Notification endpoints for favorites' specials
   - Backend: Special starting soon notifications
   - Deep linking: Tap notification to open restaurant detail

### Files Changed
- `/app/mobile-app/src/components/RestaurantMapView.tsx` (new)
- `/app/mobile-app/src/screens/HomeScreen.tsx` (map toggle)
- `/app/mobile-app/src/services/OneSignalService.ts` (rewritten)
- `/app/mobile-app/src/services/APIService.ts` (favorite tagging)
- `/app/mobile-app/src/screens/ProfileScreen.tsx` (notification preferences)
- `/app/mobile-app/App.tsx` (OneSignal initialization)
- `/app/backend/server.py` (notification endpoints)

### Setup Required for Push Notifications
1. Create OneSignal account at https://onesignal.com
2. Create new app and get App ID
3. Configure iOS (APNs p8 certificate) and Android (FCM)
4. Add to backend `.env`: ONESIGNAL_APP_ID, ONESIGNAL_API_KEY
5. Add to mobile app build: ONESIGNAL_APP_ID environment variable
6. Add onesignal-expo-plugin to app.json plugins array
7. Rebuild mobile app with EAS

## Recent Changes (February 12, 2026)

### New Features
1. **Admin Restaurant Ownership Endpoints** - Added for internal management
   - `GET /api/admin/search-restaurants` - Search restaurants by name
   - `GET /api/admin/restaurant-owner/{restaurant_id}` - Find who owns a restaurant
   - `DELETE /api/admin/release-restaurant/{restaurant_id}` - Release restaurant from owner
   - Works with both MongoDB ObjectId and string IDs
   - Returns detailed owner information or "no owner" status

2. **Mobile App Favorites Photos** - Added real photos to favorites
   - Google Places favorites now show actual venue photos
   - Database restaurants get fallback stock photos
   - Fixed empty favorites display issue

### Bug Fixes
1. **"Already Claimed" Bug** - Fixed restaurants incorrectly showing as claimed
   - Backend now only sets `source: 'owner_managed'` when restaurant has actual owner
   - Frontend checks both `owner_id` and `source` before disabling claim button
   - Added client-side filtering to claim modal

### Pending
1. **New App Icon/Logo/Splash** - Waiting on design firm to deliver assets
   - App Icon: 1024x1024 PNG
   - Splash Screen: 1284x2778 PNG
   - Web Logo: ~200px wide PNG/SVG
   - Favicon: 32x32 ICO/PNG

## Recent Changes (January 27, 2026)

### New Features
1. **Referral Program** - Complete owner referral system
   - Unique referral codes per owner
   - 10% discount for new owners using referral code
   - 20% one-time discount for referrers after 6 months
   - Dashboard with referral stats and tracking
   - Referral code validation during signup
2. **Partner Info Page** - Static page at `/partner-info` with orange-themed styling

### Bug Fixes
- Fixed stale closure issue in filter useEffect
- Fixed userType not being set on session restore
- Fixed collection name (restaurant_owners vs owners)

## Technical Stack
- Frontend: React (web), React Native/Expo (mobile)
- Backend: FastAPI (Python)
- Database: MongoDB
- Payments: Stripe

## New API Endpoints (Admin - Internal Use)
- `GET /api/admin/search-restaurants?name=X&has_owner=true/false&limit=N` - Search restaurants by name
- `GET /api/admin/restaurant-owner/{restaurant_id}` - Get owner info for a restaurant
- `DELETE /api/admin/release-restaurant/{restaurant_id}` - Release restaurant from ownership

## New API Endpoints (Referral Program)
- `GET /api/owners/referral-code` - Get owner's referral code
- `GET /api/owners/referrals` - Get referral history and stats
- `GET /api/referral/validate/{code}` - Validate a referral code (public)

## Pending Items

### Blocked
- Mobile App: Waiting for EAS build limit reset

## Future Tasks (Backlog)
- P0: Mobile app debugging (once EAS build available)
- P1: Apple App Store submission
- P1: PayPal integration for owner subscriptions
- P1: Landing page for New Orleans restaurant owner outreach
- P2: Map View for mobile app
- P2: Admin approval workflow UI
- P2: Stripe integration for referral discounts (automated discount application)

## Planned Features (Post-Deployment Fix)

### Owner Analytics Dashboard (Tier 1 - Engagement Metrics) ✅ IMPLEMENTED
**Status:** Complete
**Implementation Date:** January 28, 2026

**Metrics Tracked:**
- ✅ Card Views (restaurant displayed in search results)
- ✅ Card Clicks (user opens restaurant details)
- ✅ Special Views (views of specific deals)
- ✅ Share Actions (WhatsApp/SMS shares)
- ✅ Favorites Added/Removed
- ✅ Direction Requests ("Get Directions" / Uber/Lyft clicks)
- ✅ Call Button Clicks
- ✅ Check-ins (geofence-verified visits)

**Dashboard Features:**
- Period selector (7/30/90 days)
- Stats cards with color-coded metrics
- Views Over Time chart
- Peak Hours distribution chart
- Click-through rate calculation
- Engagement insights section
- Recent check-ins list

**Check-In Feature:**
- "I'm Here" button on restaurant detail page
- Geofence verification (200m radius)
- Location permission request
- Success/failure feedback

**API Endpoints:**
- POST /api/analytics/event - Record tracking events
- POST /api/analytics/checkin - Verify customer check-in
- GET /api/owners/analytics - Get owner's analytics data

**Future Tiers (Backlog):**
- Tier 2: Conversion tracking (redemptions, return visits)
- Tier 3: Purchase analytics (POS integration for ticket size, items purchased, loyalty sign-ups)
