from fastapi import FastAPI, APIRouter, HTTPException, Depends, Query
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uuid
from datetime import datetime, timezone, time
import httpx
import asyncio
from enum import Enum
import json
import jwt
import hashlib
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Union

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# Create the main app without a prefix
app = FastAPI(title="On-the-Cheap API", description="Find local restaurant and bar specials")

# Create a router with the /api prefix
api_router = APIRouter(prefix="/api")

# Models
class SpecialType(str, Enum):
    HAPPY_HOUR = "happy_hour"
    LUNCH_SPECIAL = "lunch_special"
    DINNER_SPECIAL = "dinner_special"
    BLUE_PLATE = "blue_plate"
    DAILY_SPECIAL = "daily_special"
    WEEKEND_SPECIAL = "weekend_special"

class LocationCoordinates(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)

class RestaurantSpecial(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str
    description: str
    special_type: SpecialType
    price: Optional[float] = None
    original_price: Optional[float] = None
    days_available: List[str]  # ["monday", "tuesday", etc.]
    time_start: str  # "14:00"
    time_end: str    # "17:00"
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class Restaurant(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    address: str
    location: LocationCoordinates
    phone: Optional[str] = None
    website: Optional[str] = None
    cuisine_type: List[str] = []
    rating: Optional[float] = None
    price_level: Optional[int] = Field(None, ge=1, le=4)  # 1-4 ($-$$$$)
    specials: List[RestaurantSpecial] = []
    is_verified: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RestaurantSearch(BaseModel):
    query: Optional[str] = None
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    radius: int = Field(default=8047, ge=100, le=80467)  # Default 5 miles in meters
    special_type: Optional[SpecialType] = None
    limit: int = Field(default=20, ge=1, le=50)

class RestaurantOwner(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    business_name: str
    phone: str
    restaurant_ids: List[str] = []
    is_verified: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

# Mock data setup
def prepare_for_mongo(data):
    """Convert data for MongoDB storage"""
    if isinstance(data, dict):
        return {k: prepare_for_mongo(v) for k, v in data.items()}
    elif isinstance(data, list):
        return [prepare_for_mongo(item) for item in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    else:
        return data

def prepare_from_mongo(data):
    """Convert data from MongoDB to dict (removes ObjectId)"""
    if isinstance(data, dict):
        result = {}
        for k, v in data.items():
            if k == '_id':
                continue  # Skip MongoDB's _id field
            result[k] = prepare_from_mongo(v)
        return result
    elif isinstance(data, list):
        return [prepare_from_mongo(item) for item in data]
    else:
        return data

async def init_mock_data():
    """Initialize mock restaurant data"""
    existing_restaurants = await db.restaurants.count_documents({})
    if existing_restaurants > 0:
        return
    
    mock_restaurants = [
        {
            "id": str(uuid.uuid4()),
            "name": "Tony's Tavern",
            "address": "123 Main St, San Francisco, CA 94102",
            "location": {"latitude": 37.7749, "longitude": -122.4194},
            "phone": "+1-415-555-0101",
            "website": "https://tonystaveran.com",
            "cuisine_type": ["American", "Bar"],
            "rating": 4.5,
            "price_level": 2,
            "specials": [
                {
                    "id": str(uuid.uuid4()),
                    "title": "Happy Hour - Half Price Appetizers",
                    "description": "All appetizers 50% off during happy hour",
                    "special_type": "happy_hour",
                    "price": 5.99,
                    "original_price": 11.99,
                    "days_available": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    "time_start": "15:00",
                    "time_end": "18:00",
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc).isoformat()
                },
                {
                    "id": str(uuid.uuid4()),
                    "title": "$2 Draft Beers",
                    "description": "Local craft beer drafts for just $2",
                    "special_type": "happy_hour",
                    "price": 2.00,
                    "original_price": 6.00,
                    "days_available": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    "time_start": "15:00",
                    "time_end": "19:00",
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            ],
            "is_verified": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Mama's Italian Kitchen",
            "address": "456 North Beach, San Francisco, CA 94133",
            "location": {"latitude": 37.8067, "longitude": -122.4158},
            "phone": "+1-415-555-0202",
            "website": "https://mamasitalian.com",
            "cuisine_type": ["Italian", "Family"],
            "rating": 4.7,
            "price_level": 2,
            "specials": [
                {
                    "id": str(uuid.uuid4()),
                    "title": "Lunch Special - Pasta & Salad",
                    "description": "Choice of pasta with house salad and bread",
                    "special_type": "lunch_special",
                    "price": 12.99,
                    "original_price": 18.99,
                    "days_available": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    "time_start": "11:30",
                    "time_end": "15:00",
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            ],
            "is_verified": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "The Blue Plate Diner",
            "address": "789 Mission St, San Francisco, CA 94103",
            "location": {"latitude": 37.7853, "longitude": -122.4056},
            "phone": "+1-415-555-0303",
            "cuisine_type": ["American", "Diner"],
            "rating": 4.2,
            "price_level": 1,
            "specials": [
                {
                    "id": str(uuid.uuid4()),
                    "title": "Blue Plate Special",
                    "description": "Meatloaf, mashed potatoes, green beans, and cornbread",
                    "special_type": "blue_plate",
                    "price": 8.99,
                    "original_price": 14.99,
                    "days_available": ["monday", "tuesday", "wednesday"],
                    "time_start": "11:00",
                    "time_end": "21:00",
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc).isoformat()
                },
                {
                    "id": str(uuid.uuid4()),
                    "title": "Tuesday Taco Special",
                    "description": "Three tacos with rice and beans",
                    "special_type": "daily_special",
                    "price": 6.99,
                    "original_price": 12.99,
                    "days_available": ["tuesday"],
                    "time_start": "11:00",
                    "time_end": "21:00",
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            ],
            "is_verified": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Sunset Sports Bar",
            "address": "321 Sunset Blvd, San Francisco, CA 94116",
            "location": {"latitude": 37.7449, "longitude": -122.4804},
            "phone": "+1-415-555-0404",
            "cuisine_type": ["American", "Sports Bar"],
            "rating": 4.0,
            "price_level": 2,
            "specials": [
                {
                    "id": str(uuid.uuid4()),
                    "title": "Wing Wednesday",
                    "description": "50¢ wings all day long",
                    "special_type": "daily_special",
                    "price": 0.50,
                    "original_price": 1.25,
                    "days_available": ["wednesday"],
                    "time_start": "11:00",
                    "time_end": "23:00",
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc).isoformat()
                },
                {
                    "id": str(uuid.uuid4()),
                    "title": "Happy Hour Drinks",
                    "description": "$3 well drinks and $4 craft beers",
                    "special_type": "happy_hour",
                    "price": 3.00,
                    "original_price": 8.00,
                    "days_available": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                    "time_start": "16:00",
                    "time_end": "19:00",
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            ],
            "is_verified": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Golden Gate Cafe",
            "address": "654 Market St, San Francisco, CA 94104",
            "location": {"latitude": 37.7892, "longitude": -122.4013},
            "phone": "+1-415-555-0505",
            "cuisine_type": ["Cafe", "Breakfast"],
            "rating": 4.3,
            "price_level": 2,
            "specials": [
                {
                    "id": str(uuid.uuid4()),
                    "title": "Weekend Brunch Special",
                    "description": "Eggs Benedict with fresh fruit and coffee",
                    "special_type": "weekend_special",
                    "price": 14.99,
                    "original_price": 19.99,
                    "days_available": ["saturday", "sunday"],
                    "time_start": "09:00",
                    "time_end": "14:00",
                    "is_active": True,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
            ],
            "is_verified": True,
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    prepared_restaurants = [prepare_for_mongo(restaurant) for restaurant in mock_restaurants]
    await db.restaurants.insert_many(prepared_restaurants)
    logger.info(f"Inserted {len(mock_restaurants)} mock restaurants")

# Google Places API Integration
async def search_google_places_real(latitude: float, longitude: float, radius: int, query: Optional[str] = None, limit: int = 20) -> List[dict]:
    """Search for real restaurants using Google Places API"""
    google_api_key = os.environ.get('GOOGLE_PLACES_API_KEY')
    if not google_api_key:
        logger.warning("Google Places API key not found, skipping real API call")
        return []
    
    try:
        headers = {
            "Content-Type": "application/json",
            "X-Goog-Api-Key": google_api_key,
            "X-Goog-FieldMask": "places.id,places.displayName,places.types,places.rating,places.priceLevel,places.location,places.formattedAddress,places.nationalPhoneNumber,places.websiteUri,places.regularOpeningHours,places.photos"
        }
        
        # Build request payload for Google Places API (New)
        included_types = ["restaurant", "bar", "cafe", "meal_takeaway"]
        
        payload = {
            "includedTypes": included_types,
            "maxResultCount": min(limit, 20),
            "locationRestriction": {
                "circle": {
                    "center": {
                        "latitude": latitude,
                        "longitude": longitude
                    },
                    "radius": float(min(radius, 50000))  # Google Places max radius
                }
            }
        }
        
        # Add text query if provided
        if query:
            payload["textQuery"] = query
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(
                "https://places.googleapis.com/v1/places:searchNearby",
                json=payload,
                headers=headers
            )
            
            if response.status_code == 200:
                data = response.json()
                places = data.get('places', [])
                
                # Convert Google Places format to our format
                restaurants = []
                for place in places:
                    try:
                        location = place.get('location', {})
                        display_name = place.get('displayName', {})
                        
                        restaurant = {
                            'id': f"google_{place.get('id', str(uuid.uuid4()))}",
                            'name': display_name.get('text', 'Unknown Restaurant'),
                            'address': place.get('formattedAddress', ''),
                            'location': {
                                'latitude': location.get('latitude', latitude),
                                'longitude': location.get('longitude', longitude)
                            },
                            'phone': place.get('nationalPhoneNumber'),
                            'website': place.get('websiteUri'),
                            'cuisine_type': [t.replace('_', ' ').title() for t in place.get('types', []) if t in ['restaurant', 'bar', 'cafe', 'meal_takeaway']],
                            'rating': place.get('rating'),
                            'price_level': place.get('priceLevel'),
                            'specials': [],  # Real restaurants don't have specials in our system yet
                            'is_verified': True,
                            'source': 'google_places',
                            'distance': calculate_distance(
                                latitude, longitude,
                                location.get('latitude', latitude),
                                location.get('longitude', longitude)
                            ),
                            'created_at': datetime.now(timezone.utc).isoformat()
                        }
                        restaurants.append(restaurant)
                    except Exception as e:
                        logger.warning(f"Error processing Google Places result: {e}")
                        continue
                
                logger.info(f"Found {len(restaurants)} restaurants from Google Places API")
                return restaurants
            else:
                logger.error(f"Google Places API error: {response.status_code} - {response.text}")
                return []
                
    except Exception as e:
        logger.error(f"Error calling Google Places API: {e}")
        return []

# Helper functions
def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in meters (Haversine formula)"""
    import math
    
    # Convert latitude and longitude from degrees to radians
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat/2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    
    # Radius of earth in meters
    r = 6371000
    return c * r

def is_special_active_now(special_data: dict) -> bool:
    """Check if special is currently active based on time and day"""
    now = datetime.now()
    current_day = now.strftime("%A").lower()
    current_time = now.time()
    
    if current_day not in special_data.get('days_available', []):
        return False
    
    try:
        start_time = datetime.strptime(special_data['time_start'], "%H:%M").time()
        end_time = datetime.strptime(special_data['time_end'], "%H:%M").time()
        
        return start_time <= current_time <= end_time
    except:
        return True  # If time parsing fails, assume it's active

# API Routes
@api_router.get("/restaurants/search")
async def search_restaurants(
    latitude: float = Query(..., ge=-90, le=90),
    longitude: float = Query(..., ge=-180, le=180),
    radius: int = Query(default=8047, ge=100, le=80467),  # 5 miles default
    query: Optional[str] = Query(None),
    special_type: Optional[SpecialType] = Query(None),
    limit: int = Query(default=20, ge=1, le=50)
):
    """Search for restaurants with specials near a location"""
    try:
        # Get real restaurants from Google Places API
        google_restaurants = await search_google_places_real(latitude, longitude, radius, query, limit)
        
        # Get mock restaurants from database (with specials)
        restaurants_cursor = db.restaurants.find({})
        all_restaurants_raw = await restaurants_cursor.to_list(length=None)
        mock_restaurants = [prepare_from_mongo(restaurant) for restaurant in all_restaurants_raw]

        # Combine real restaurants with mock specials data
        all_restaurants = []
        
        # First, add mock restaurants (they have specials)
        for restaurant in mock_restaurants:
            location = restaurant.get('location', {})
            rest_lat = location.get('latitude', 0)
            rest_lon = location.get('longitude', 0)
            
            distance = calculate_distance(latitude, longitude, rest_lat, rest_lon)
            
            if distance <= radius:
                restaurant['distance'] = round(distance)
                restaurant['source'] = 'mock_with_specials'
                
                # Filter specials by type if specified
                if special_type:
                    restaurant['specials'] = [
                        special for special in restaurant.get('specials', [])
                        if special.get('special_type') == special_type and special.get('is_active', True)
                    ]
                else:
                    # Filter out inactive specials and check if currently active
                    active_specials = []
                    for special in restaurant.get('specials', []):
                        if special.get('is_active', True) and is_special_active_now(special):
                            active_specials.append(special)
                    restaurant['specials'] = active_specials
                
                # Only include restaurants with active specials
                if restaurant['specials']:
                    all_restaurants.append(restaurant)
        
        # Then add Google Places restaurants (they don't have specials yet)
        # We'll show them only if no special_type filter is applied
        if not special_type:
            for restaurant in google_restaurants:
                if restaurant.get('distance', 0) <= radius:
                    # Add a note that these are real restaurants without specials data
                    restaurant['specials'] = []
                    restaurant['note'] = 'Real restaurant - specials data coming soon!'
                    all_restaurants.append(restaurant)

        nearby_restaurants = all_restaurants
        
        # Filter by query if provided
        if query:
            query_lower = query.lower()
            nearby_restaurants = [
                r for r in nearby_restaurants 
                if query_lower in r.get('name', '').lower() or 
                   any(query_lower in cuisine.lower() for cuisine in r.get('cuisine_type', []))
            ]
        
        # Sort by distance
        nearby_restaurants.sort(key=lambda x: x.get('distance', float('inf')))
        
        # Limit results
        nearby_restaurants = nearby_restaurants[:limit]
        
        return {
            "restaurants": nearby_restaurants,
            "total": len(nearby_restaurants),
            "search_location": {"latitude": latitude, "longitude": longitude},
            "radius_meters": radius
        }
        
    except Exception as e:
        logger.error(f"Error searching restaurants: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.get("/restaurants/{restaurant_id}")
async def get_restaurant(restaurant_id: str):
    """Get details for a specific restaurant"""
    restaurant_raw = await db.restaurants.find_one({"id": restaurant_id})
    if not restaurant_raw:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    restaurant = prepare_from_mongo(restaurant_raw)
    
    # Filter only active specials that are currently running
    active_specials = []
    for special in restaurant.get('specials', []):
        if special.get('is_active', True) and is_special_active_now(special):
            active_specials.append(special)
    
    restaurant['specials'] = active_specials
    return restaurant

@api_router.post("/restaurants", response_model=dict)
async def create_restaurant(restaurant: Restaurant):
    """Create a new restaurant (for restaurant owners)"""
    restaurant_dict = restaurant.dict()
    restaurant_dict['created_at'] = datetime.now(timezone.utc).isoformat()
    
    result = await db.restaurants.insert_one(restaurant_dict)
    return {"id": restaurant.id, "message": "Restaurant created successfully"}

@api_router.post("/restaurants/{restaurant_id}/specials")
async def add_special(restaurant_id: str, special: RestaurantSpecial):
    """Add a special to a restaurant"""
    # Check if restaurant exists
    restaurant = await db.restaurants.find_one({"id": restaurant_id})
    if not restaurant:
        raise HTTPException(status_code=404, detail="Restaurant not found")
    
    # Add special to restaurant
    special_dict = special.dict()
    special_dict['created_at'] = datetime.now(timezone.utc).isoformat()
    
    await db.restaurants.update_one(
        {"id": restaurant_id},
        {"$push": {"specials": special_dict}}
    )
    
    return {"message": "Special added successfully", "special_id": special.id}

@api_router.get("/specials/types")
async def get_special_types():
    """Get all available special types"""
    return {
        "special_types": [
            {"value": "happy_hour", "label": "Happy Hour"},
            {"value": "lunch_special", "label": "Lunch Special"},
            {"value": "dinner_special", "label": "Dinner Special"},
            {"value": "blue_plate", "label": "Blue Plate Special"},
            {"value": "daily_special", "label": "Daily Special"},
            {"value": "weekend_special", "label": "Weekend Special"}
        ]
    }

# Original status check endpoints (keeping for compatibility)
class StatusCheck(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    client_name: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class StatusCheckCreate(BaseModel):
    client_name: str

@api_router.get("/")
async def root():
    return {"message": "On-the-Cheap API - Find the best restaurant specials!", "version": "1.0.0"}

@api_router.post("/status", response_model=StatusCheck)
async def create_status_check(input: StatusCheckCreate):
    status_dict = input.dict()
    status_obj = StatusCheck(**status_dict)
    _ = await db.status_checks.insert_one(status_obj.dict())
    return status_obj

@api_router.get("/status", response_model=List[StatusCheck])
async def get_status_checks():
    status_checks = await db.status_checks.find().to_list(1000)
    return [StatusCheck(**status_check) for status_check in status_checks]

# Include the router in the main app
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("startup")
async def startup_event():
    """Initialize mock data on startup"""
    await init_mock_data()
    logger.info("On-the-Cheap API started successfully")

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()