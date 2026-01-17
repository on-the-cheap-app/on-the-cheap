# On-the-Cheap - Product Requirements Document

## Original Problem Statement
A restaurant deals mobile app and web platform that helps users find restaurant specials, happy hours, and food deals near them.

## Current Status (January 17, 2026)

### Mobile App (Android)
- ✅ Core features working: Near Me, Search, Filters, Restaurant Details, Login, Favorites
- ✅ Share with Friends (Text/WhatsApp) - minor SMS formatting issue on Android
- ✅ AAB uploaded to Google Play
- ✅ Internal testing complete
- ✅ Closed testing live
- ⏳ Waiting 14 days for production access (need 12 testers opted-in)

### Web App
- ✅ Privacy Policy page: `/privacy`
- ✅ Account Deletion page: `/delete-account`
- ✅ Stripe subscription checkout (working on preview)
- ⏳ Production deployment blocked - escalated to Emergent senior support

## Pending Items

### Blocked
- Production web deployment (Emergent Support investigating)
- Production Play Store release (14-day closed testing requirement)

### Known Issues
- SMS share puts message in "To:" field instead of body on Android (minor)
- Free EAS build quota exhausted until Feb 1, 2026

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

## Test Credentials
- User: sfurtwengler@gmail.com / DrFurt138!
- Expo: onthecheapapp@gmail.com / DrFurt138!

## Technical Stack
- Frontend: React (web), React Native/Expo (mobile)
- Backend: FastAPI (Python)
- Database: MongoDB
- Payments: Stripe
