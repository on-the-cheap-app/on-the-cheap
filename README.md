# On-the-Cheap 🍽️

**Find the best restaurant specials near you!**

A full-stack restaurant discovery platform that helps users find active specials, happy hours, and daily deals at local restaurants. Built with React, FastAPI, and MongoDB, integrated with Google Places API for real restaurant data.

## ✨ Features

### For Customers:
- 🔍 **Real-time Restaurant Search** - Find restaurants worldwide via Google Places API
- ⏰ **Time-based Special Filtering** - Only see currently active specials
- 📍 **Location-based Search** - GPS "near me" or city/address search
- 🏷️ **Special Categories** - Happy Hour, Lunch Specials, Blue Plate, Daily Deals
- ⭐ **Real Business Data** - Ratings, photos, contact info, hours

### For Restaurant Owners:
- 🏢 **Restaurant Portal** - Claim and manage restaurants
- 📋 **Specials Management** - Create, edit, delete daily specials
- 🕐 **Automatic Scheduling** - Set times and days for special activation
- ✅ **Ownership Verification** - Secure restaurant claiming process

## 🛠️ Tech Stack

- **Frontend**: React 19, Tailwind CSS, shadcn/ui components
- **Backend**: FastAPI (Python), JWT authentication
- **Database**: MongoDB Atlas
- **APIs**: Google Places API for restaurant data
- **Deployment**: Railway (backend), Vercel (frontend)

## 🚀 Live Demo

- **Main App**: [Find Restaurant Specials](https://owner-mgmt.preview.emergentagent.com)
- **Owner Portal**: Click "Restaurant Owner" in the app header

## 🏗️ Project Structure

```
on-the-cheap-app/
├── frontend/           # React application
│   ├── src/
│   │   ├── App.js     # Main app component
│   │   ├── OwnerPortal.js  # Restaurant owner dashboard
│   │   └── components/ # shadcn/ui components
│   ├── public/
│   └── package.json
├── backend/           # FastAPI server
│   ├── server.py     # Main API server
│   ├── requirements.txt
│   └── .env          # Environment variables
├── railway.json      # Railway deployment config
├── Procfile         # Process file for deployment
└── README.md
```

## 🔧 Environment Variables

### Backend:
```
MONGO_URL=mongodb+srv://...
JWT_SECRET=your-jwt-secret
GOOGLE_PLACES_API_KEY=your-google-api-key
CORS_ORIGINS=*
```

### Frontend:
```
REACT_APP_BACKEND_URL=your-backend-url
```

## 📱 API Endpoints

### Public:
- `GET /api/restaurants/search` - Search restaurants with specials
- `GET /api/restaurants/{id}` - Get restaurant details
- `GET /api/specials/types` - Get special types

### Owner Portal:
- `POST /api/auth/register` - Restaurant owner registration
- `POST /api/auth/login` - Owner login
- `GET /api/owner/my-restaurants` - Get owned restaurants
- `POST /api/owner/claim-restaurant` - Claim restaurant
- `POST /api/owner/restaurants/{id}/specials` - Create special

---

**Built with ❤️ for restaurant owners and food lovers!** 🍽️✨
