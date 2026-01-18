# On-the-Cheap - Product Requirements Document

## Original Problem Statement
A restaurant deals mobile app and web platform that helps users find restaurant specials, happy hours, and food deals near them.

## Current Status (January 17, 2026)

### Web App - PRODUCTION LIVE ✅
- ✅ Customer experience working (search, favorites, share)
- ✅ Owner login and dashboard
- ✅ **Stripe subscription checkout WORKING**
- ✅ Pricing modal scrolling fixed
- ✅ Privacy Policy page: `/privacy`
- ✅ Account Deletion page: `/delete-account`
- ✅ WhatsApp share working
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
- **Owner:** demo@onthecheapapp.com / Demo123!
- **Expo:** onthecheapapp@gmail.com / DrFurt138!

## Pending Items

### Waiting On
- Google Play: 14-day closed testing period (need 12 testers)
- EAS builds reset: Feb 1, 2026

### Known Issues (Low Priority)
- SMS share on desktop web app
- SMS share on mobile app (fix ready for next build)

## Future Tasks (Backlog)
- P1: Apple App Store submission (iOS)
- P1: PayPal integration
- P2: Owner Dashboard AI enhancements
- P2: Admin Approval Workflow

## Key URLs
- Production: https://www.onthecheapapp.com
- Preview: https://eatdeals-mobile.preview.emergentagent.com
- Privacy Policy: https://www.onthecheapapp.com/privacy
- Account Deletion: https://www.onthecheapapp.com/delete-account

## Technical Stack
- Frontend: React (web), React Native/Expo (mobile)
- Backend: FastAPI (Python)
- Database: MongoDB
- Payments: Stripe
