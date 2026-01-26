# On-the-Cheap - Product Requirements Document

## Original Problem Statement
A restaurant deals mobile app and web platform that helps users find restaurant specials, happy hours, and food deals near them.

## Current Status (January 26, 2026)

### Web App - PRODUCTION READY ✅
- ✅ Customer experience working (search, favorites, share)
- ✅ Owner login and dashboard
- ✅ **Stripe subscription checkout WORKING**
- ✅ Privacy Policy page: `/privacy`
- ✅ Account Deletion page: `/delete-account`
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
- **Owner (Preview):** demo@onthecheapapp.com / Demo123!
- **Owner (Production):** demo@onthecheapapp.com / TestPass123!

## Key URLs
- Production: https://www.onthecheapapp.com
- Preview: https://dealstack-5.preview.emergentagent.com
- Privacy Policy: https://www.onthecheapapp.com/privacy

## Manually Added Restaurants
- Avenue Pub - 1732 St. Charles Ave, New Orleans, LA 70130
- Oh My Chives - 7332 Nolensville Rd, Suite 304, Nolensville, TN 37135

## Recent Changes (January 26, 2026)

### New Features
1. **Filter Auto-Refresh** - Search results update automatically when filters change
2. **Customer Favorites Button** - Heart icon button in header for logged-in customers
3. **Add Your Own Restaurant** - Owners can add venues not found in database
4. **Owner Login as Customer** - Owners can use customer Sign In with same credentials
5. **Transfer Restaurant Ownership** - Transfer restaurants to another owner's email
6. **Delete Owner Profile** - Owners can delete their account (restaurants become unclaimed)

### Bug Fixes
- Fixed stale closure issue in filter useEffect
- Fixed userType not being set on session restore
- Fixed collection name (restaurant_owners vs owners)

## Technical Stack
- Frontend: React (web), React Native/Expo (mobile)
- Backend: FastAPI (Python)
- Database: MongoDB
- Payments: Stripe

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
