# On-the-Cheap - Product Requirements Document

## Original Problem Statement
A restaurant deals mobile app and web platform that helps users find restaurant specials, happy hours, and food deals near them.

## Current Status (January 25, 2026)

### Web App - PRODUCTION LIVE ✅
- ✅ Customer experience working (search, favorites, share)
- ✅ Owner login and dashboard
- ✅ **Stripe subscription checkout WORKING**
- ✅ Privacy Policy page: `/privacy`
- ✅ Account Deletion page: `/delete-account`
- ✅ WhatsApp share working
- ✅ **Create/Manage Specials feature** - Create, edit, delete specials with images
- ✅ **Image Upload for Specials** - Base64 encoding (max 1MB)
- ✅ **Timezone Support** - Restaurant-specific timezone for special filtering
- ✅ **Filter Auto-Refresh (FIXED Jan 25, 2026)** - Filters now auto-refresh results without needing to click Search again
- ✅ **New Orleans Restaurant Data** - 565 restaurants imported with Yelp enrichment

### Mobile App (Android)
- ⚠️ **BLOCKED** - Non-functional due to incorrect backend URL in APIService.js
- User has fixed the code locally but waiting for EAS build limit reset (~Feb 1, 2026)
- All mobile issues (login, search, near me) are blocked on this

### Data Enrichment Pipeline ✅ COMPLETE
- **Phase 1**: Cleaned and segmented 1,206 New Orleans restaurants
- **Phase 2**: Web scraped 305 websites, found 15 new emails
- **Phase 3**: Yelp enrichment - 552/565 matched (97.7% match rate)
- **Phase 4**: Imported 565 restaurants into database
- **Output files**: Available at `/app/exports/` - downloadable via API

## Test Accounts
- **Customer:** sfurtwengler@gmail.com / DrFurt138!
- **Owner (Preview):** demo@onthecheapapp.com / Demo123!
- **Owner (Production):** demo@onthecheapapp.com / TestPass123!

## Key URLs
- Production: https://www.onthecheapapp.com
- Preview: https://fooddeals-1.preview.emergentagent.com
- Privacy Policy: https://www.onthecheapapp.com/privacy
- Download Exports: https://fooddeals-1.preview.emergentagent.com/api/exports/list

## Pending Items

### Blocked
- Mobile App: Waiting for EAS build limit reset (~Feb 1, 2026)

### Known Issues
- SMS share on desktop web app (low priority)
- SMS share formatting on mobile app (fix ready for next build)
- Filters on "Bars" work but may return many results since most restaurants have bar-related cuisine tags

## Future Tasks (Backlog)
- P0: Mobile app debugging (once EAS build available)
- P1: Apple App Store submission (iOS build needed)
- P1: PayPal integration for owner subscriptions
- P1: Create landing page for New Orleans restaurant owner outreach
- P2: Map View for mobile app
- P2: Admin approval workflow UI
- P2: AI-driven upselling suggestions for owners

## Recent Changes

### January 25, 2026
- **Filter Auto-Refresh Bug Fix**: 
  - Added useEffect to auto-trigger search when filters change
  - Fixed stale closure issue by passing filter values explicitly to searchRestaurants()
  - Backend now supports "bar" venue_type filter (filters by cuisine keywords)
- **Data Enrichment Pipeline Complete**:
  - Phase 1: CSV cleaning and segmentation
  - Phase 2: Web scraping for emails (15 new emails found)
  - Phase 3: Yelp API enrichment (97.7% match rate)
  - Phase 4: Database import (565 restaurants)
- **Export Download API**: Added `/api/exports/list` and `/api/exports/download/{filename}` endpoints

### January 19, 2026
- Create/Manage Specials feature with image upload
- Timezone support for specials filtering
- Customer-facing specials with images
- Special preview thumbnails on restaurant cards

## Technical Stack
- Frontend: React (web), React Native/Expo (mobile)
- Backend: FastAPI (Python)
- Database: MongoDB
- Payments: Stripe
- Data: Yelp Fusion API for enrichment

## Database Stats
- Total Restaurants: 583
- New Orleans Restaurants: 565
- Top Categories: Cajun/Creole (121), Seafood (102), Breakfast & Brunch (91)
