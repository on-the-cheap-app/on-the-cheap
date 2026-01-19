# On-the-Cheap - Product Requirements Document

## Original Problem Statement
A restaurant deals mobile app and web platform that helps users find restaurant specials, happy hours, and food deals near them.

## Current Status (January 19, 2026)

### Web App - PRODUCTION LIVE ✅
- ✅ Customer experience working (search, favorites, share)
- ✅ Owner login and dashboard
- ✅ **Stripe subscription checkout WORKING**
- ✅ Pricing modal scrolling fixed
- ✅ Privacy Policy page: `/privacy`
- ✅ Account Deletion page: `/delete-account`
- ✅ WhatsApp share working
- ✅ **Create/Manage Specials feature (Jan 19, 2026)**
  - Create new specials with full form (title, description, type, pricing, schedule)
  - Edit existing specials via modal
  - Delete specials
  - View specials list with status badges
  - Auto-approval enabled (specials go live immediately)
  - Backend API endpoints: POST/GET/PUT/DELETE `/api/owners/specials`
- ✅ **Image Upload for Specials (NEW - Jan 19, 2026)**
  - Base64 image encoding (max 1MB)
  - Upload via Choose Image button in modal
  - Images displayed in specials list
  - Edit preserves existing images
- ⚠️ SMS share on desktop (low priority)

### Mobile App (Android)
- ✅ Core features working: Near Me, Search, Filters, Restaurant Details, Login, Favorites
- ✅ WhatsApp share working
- ⚠️ SMS share formatting issue (fix ready, waiting for build)
- ✅ AAB uploaded to Google Play
- ✅ Internal testing complete
- ✅ Closed testing live
- ⏳ Waiting 14 days for production access (need 12 testers opted-in)

## Test Accounts
- **Customer:** sfurtwengler@gmail.com / DrFurt138!
- **Owner (Preview):** demo@onthecheapapp.com / Demo123!
- **Owner (Production):** demo@onthecheapapp.com / TestPass123!
- **Expo:** onthecheapapp@gmail.com / DrFurt138!
- **Test Restaurant (Preview):** Demo Bistro & Bar (ID: 6f5c2507-dd5b-4db4-8da7-4a81e95e345f)
- **Test Restaurant (Production):** Demo Bistro & Bar (Test) (ID: test-demo-bistro-prod-001)

## Pending Items

### Waiting On
- Google Play: 14-day closed testing period (need 12 testers)
- EAS builds reset: Feb 1, 2026

### Known Issues (Low Priority)
- SMS share on desktop web app
- SMS share on mobile app (fix ready for next build)

## Future Tasks (Backlog)
- P1: Apple App Store submission (iOS build needed)
- P1: PayPal integration for owner subscriptions
- P2: Map View for mobile app
- P2: Admin approval workflow (if needed later)
- P2: AI-driven upselling suggestions for owners

## Recent Changes

### January 19, 2026 - Session 2
- **Customer-facing Specials with Images**: Updated restaurant search and detail views to show owner-created specials with images
- Backend merges specials from `owner_specials` collection with restaurant's built-in specials
- Images display as 80x80 thumbnails alongside special details

### January 19, 2026 - Session 1
- **Create/Manage Specials Feature**: Full CRUD for owner specials with form, scheduling, pricing
- **Image Upload for Specials**: Base64 image upload (max 1MB), preview, display in dashboard
- **Auto-approval**: Specials go live immediately without manual approval
- **Test restaurant linked**: Demo Bistro & Bar linked to demo owner account
- P1: Apple App Store submission (iOS)
- P1: PayPal integration
- P2: Map View for mobile app
- P2: Owner Dashboard AI enhancements
- P2: Admin Approval Workflow for specials

## Key URLs
- Production: https://www.onthecheapapp.com
- Preview: https://eatsaver.preview.emergentagent.com
- Privacy Policy: https://www.onthecheapapp.com/privacy
- Account Deletion: https://www.onthecheapapp.com/delete-account

## Technical Stack
- Frontend: React (web), React Native/Expo (mobile)
- Backend: FastAPI (Python)
- Database: MongoDB
- Payments: Stripe

## Recent Changes (Jan 19, 2026)
### Create/Manage Specials Feature
- **SpecialCreator.js**: Modal component for creating/editing specials
- **OwnerDashboard.js**: Updated with Specials tab, CRUD handlers
- **server.py**: Added PUT/DELETE endpoints for `/api/owners/specials`
- **owner_service.py**: Added `update_special()` and `delete_special()` methods
- **Tests**: `/app/tests/test_specials_crud.py` - 13 tests all passing
