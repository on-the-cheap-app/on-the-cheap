# Email to Emergent Support

**To:** support@emergent.sh

**Subject:** Production Deployment Login Failure - Database Configuration Issue (Job: dealstack-5)

---

Hi Emergent Support Team,

I'm experiencing a critical issue with my production deployment where all login endpoints return **401 Unauthorized** errors, while the **preview environment works perfectly**.

## Application Details
- **Job/App Name:** dealstack-5
- **Production URL:** https://onthecheapapp.com
- **Preview URL:** https://stable-baseline.preview.emergentagent.com
- **Stack:** React (Frontend) + FastAPI (Backend) + MongoDB

## The Problem
- **Preview environment:** Login works correctly ✅
- **Production environment:** All login attempts return 401 Unauthorized ❌

Both environments use the same codebase and credentials:
- Customer: `sfurtwengler@gmail.com` / `DrFurt138!`
- Owner: `demo@onthecheapapp.com` / `Demo123!`

## What I've Verified
1. The backend `.env` file contains the correct MongoDB Atlas connection string:
   - `MONGO_URL=mongodb+srv://onthecheap_user:***@on-the-cheap-db.uwupcry.mongodb.net/...`
   - `DB_NAME=onthecheap_production`

2. The database `onthecheap_production` contains:
   - 95 users (including the test account)
   - 53 restaurant owners (including the demo account)
   - Password hashes have been verified as correct

3. API endpoints work correctly when tested against the preview backend

## Production Logs Show
```
POST /api/users/login HTTP/1.1" 401 Unauthorized
POST /api/auth/login HTTP/1.1" 401 Unauthorized
```

The database connection appears successful, but authentication fails.

## Suspected Root Cause
I believe the **production deployment is connecting to a different MongoDB database** (possibly Emergent's managed MongoDB) instead of my external MongoDB Atlas database specified in the `.env` file.

## What I Need Help With
1. Can you confirm whether the production deployment is using my external MongoDB Atlas connection string from the `.env` file, or Emergent's managed MongoDB?

2. If it's using Emergent's managed MongoDB, how can I configure it to use my external MongoDB Atlas database instead?

3. Alternatively, if production must use Emergent's managed MongoDB, how can I access it to seed the necessary user data?

## Files for Reference
- Backend .env location: `/app/backend/.env`
- Environment variables needed: `MONGO_URL`, `DB_NAME`, `JWT_SECRET`

I've spent considerable time debugging this with the AI agent, and we've confirmed the code is correct - the issue appears to be infrastructure/environment configuration related.

Thank you for your assistance!

Best regards,
[Your Name]

---

**Alternative: Discord Support**
You can also reach out via Discord: https://discord.gg/VzKfwCXC4A
