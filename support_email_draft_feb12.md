# Support Request: Production Database Configuration Issue

**Date:** February 12, 2026
**Deployment:** menuscan-app-2 (onthecheapapp.com)
**Issue:** Login not working after redeployment

---

## Problem

After replacing the `menuscan-app-2` deployment today, users cannot login on production (onthecheapapp.com). Both customer and owner logins return "Invalid email or password" errors.

## Diagnosis

- **Preview environment:** Login works correctly ✅
- **Production:** Login fails ❌

This is the same issue that occurred previously and was resolved by Emergent Support correcting the production environment variables.

## Evidence

**Production test (FAILING):**
```
curl -X POST "https://www.onthecheapapp.com/api/users/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"sfurtwengler@gmail.com","password":"DrFurt138!"}'

Response: {"detail":"Invalid email or password"}
```

**Preview test (WORKING):**
```
curl -X POST "https://owner-mgmt.preview.emergentagent.com/api/users/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"sfurtwengler@gmail.com","password":"DrFurt138!"}'

Response: {"message":"Login successful", ...}
```

## Required Fix

Please verify/update the production environment variables for `menuscan-app-2`:

1. **MONGO_URL** - Should match the MongoDB Atlas connection string from the preview environment
2. **DB_NAME** - Should be set to `onthecheap_production`

The production deployment appears to be connecting to an empty or different database than intended.

## Previous Resolution

This same issue was resolved on approximately January 27-28, 2026 when Emergent Support corrected the database environment variables for production.

Thank you!
