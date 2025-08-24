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
import googlemaps
from googlemaps import exceptions as gmaps_exceptions

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET', 'your-secret-key-change-in-production')
JWT_ALGORITHM = 'HS256'
security = HTTPBearer()

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
    password_hash: str
    business_name: str
    phone: str
    first_name: str
    last_name: str
    restaurant_ids: List[str] = []
    is_verified: bool = False
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class RestaurantOwnerCreate(BaseModel):
    email: str
    password: str
    business_name: str
    phone: str
    first_name: str
    last_name: str

class RestaurantOwnerLogin(BaseModel):
    email: str
    password: str

# Regular User Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: str
    password_hash: str
    first_name: str
    last_name: str
    favorite_restaurant_ids: List[str] = []
    search_history: List[dict] = []
    preferences: dict = {}
    is_active: bool = True
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))

class UserCreate(BaseModel):
    email: str
    password: str
    first_name: str
    last_name: str

class UserLogin(BaseModel):
    email: str
    password: str

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    preferences: Optional[dict] = None

# =================== GEOCODING MODELS ===================

class GeocodeRequest(BaseModel):
    address: str
    region: Optional[str] = None
    bounds: Optional[str] = None

class ReverseGeocodeRequest(BaseModel):
    latitude: float = Field(..., ge=-90, le=90)
    longitude: float = Field(..., ge=-180, le=180)
    result_type: Optional[List[str]] = None
    location_type: Optional[List[str]] = None

class BatchGeocodeRequest(BaseModel):
    addresses: List[str] = Field(..., max_items=10)
    region: Optional[str] = None
    max_results: Optional[int] = Field(default=10, ge=1, le=10)

class GeocodeResponse(BaseModel):
    formatted_address: str
    latitude: float
    longitude: float
    place_id: str
    address_components: List[Dict[str, Any]]
    geometry_type: str

class BatchGeocodeResponse(BaseModel):
    results: List[GeocodeResponse]
    errors: List[Dict[str, str]]

# Custom Exception for Geocoding
class GeocodingError(Exception):
    def __init__(self, message: str, error_code: str = None, retry_after: int = None):
        self.message = message
        self.error_code = error_code
        self.retry_after = retry_after
        super().__init__(self.message)

class RestaurantClaim(BaseModel):
    google_place_id: str
    business_name: str
    verification_notes: Optional[str] = None

class SpecialCreate(BaseModel):
    title: str
    description: str
    special_type: SpecialType
    price: Optional[float] = None
    original_price: Optional[float] = None
    days_available: List[str]  # ["monday", "tuesday", etc.]
    time_start: str  # "14:00"
    time_end: str    # "17:00"

class SpecialUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    special_type: Optional[SpecialType] = None
    price: Optional[float] = None
    original_price: Optional[float] = None
    days_available: Optional[List[str]] = None
    time_start: Optional[str] = None
    time_end: Optional[str] = None
    is_active: Optional[bool] = None

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

# =================== GEOCODING HELPERS ===================

def get_gmaps_client():
    """Get Google Maps client instance"""
    api_key = os.environ.get('GOOGLE_PLACES_API_KEY')
    if not api_key:
        raise HTTPException(status_code=500, detail="Google Maps API key not configured")
    return googlemaps.Client(key=api_key, timeout=10)

def handle_geocoding_error(error: Exception) -> HTTPException:
    """Convert geocoding errors to appropriate HTTP exceptions"""
    if isinstance(error, gmaps_exceptions.ApiError):
        status_code_mapping = {
            "ZERO_RESULTS": 404,
            "INVALID_REQUEST": 400,
            "OVER_QUERY_LIMIT": 429,
            "REQUEST_DENIED": 403,
            "UNKNOWN_ERROR": 500,
        }
        status_code = status_code_mapping.get(error.status, 500)
        return HTTPException(status_code=status_code, detail=f"Geocoding API error: {error.status}")
    
    elif isinstance(error, gmaps_exceptions.TransportError):
        return HTTPException(status_code=502, detail="Network communication error")
    
    elif isinstance(error, gmaps_exceptions.Timeout):
        return HTTPException(status_code=408, detail="Request timeout")
    
    else:
        return HTTPException(status_code=500, detail="Internal geocoding error")

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

# Authentication Helper Functions
def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash"""
    return hash_password(password) == password_hash

def create_access_token(data: dict) -> str:
    """Create JWT access token"""
    to_encode = data.copy()
    expire = datetime.now(timezone.utc).timestamp() + 86400  # 24 hours
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def verify_token(token: str) -> dict:
    """Verify JWT token"""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token has expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated user (restaurant owner)"""
    token = credentials.credentials
    payload = verify_token(token)
    user_id = payload.get("user_id")
    user_type = payload.get("user_type", "owner")  # Default to owner for backward compatibility
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    if user_type == "owner":
        user = await db.restaurant_owners.find_one({"id": user_id})
        collection = "restaurant_owners"
    else:
        user = await db.users.find_one({"id": user_id})
        collection = "users"
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    user_data = prepare_from_mongo(user)
    user_data["user_type"] = user_type
    return user_data

async def get_current_regular_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    """Get current authenticated regular user"""
    token = credentials.credentials
    payload = verify_token(token)
    user_id = payload.get("user_id")
    user_type = payload.get("user_type")
    
    if not user_id or user_type != "user":
        raise HTTPException(status_code=401, detail="Invalid user token")
    
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    return prepare_from_mongo(user)

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

# =================== ENHANCED GEOCODING ENDPOINTS ===================

@api_router.post("/geocode/forward", response_model=GeocodeResponse)
async def forward_geocode(request: GeocodeRequest):
    """Convert address to coordinates using Google Geocoding API"""
    try:
        gmaps_client = get_gmaps_client()
        
        # Prepare geocoding parameters
        geocoding_params = {"address": request.address}
        if request.region:
            geocoding_params["region"] = request.region
        if request.bounds:
            geocoding_params["bounds"] = request.bounds
            
        # Perform geocoding
        geocode_result = gmaps_client.geocode(**geocoding_params)
        
        if not geocode_result:
            raise HTTPException(status_code=404, detail="Address not found")
            
        result = geocode_result[0]
        location = result["geometry"]["location"]
        
        return GeocodeResponse(
            formatted_address=result["formatted_address"],
            latitude=location["lat"],
            longitude=location["lng"],
            place_id=result["place_id"],
            address_components=result["address_components"],
            geometry_type=result["geometry"]["location_type"]
        )
        
    except (gmaps_exceptions.ApiError, gmaps_exceptions.TransportError, gmaps_exceptions.Timeout) as e:
        logging.error(f"Google Maps API error: {e}")
        raise handle_geocoding_error(e)
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Unexpected error in forward geocoding: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.post("/geocode/reverse", response_model=List[GeocodeResponse])
async def reverse_geocode(request: ReverseGeocodeRequest):
    """Convert coordinates to addresses using Google Geocoding API"""
    try:
        gmaps_client = get_gmaps_client()
        
        latlng = (request.latitude, request.longitude)
        
        # Prepare reverse geocoding parameters
        reverse_params = {"latlng": latlng}
        if request.result_type:
            reverse_params["result_type"] = request.result_type
        if request.location_type:
            reverse_params["location_type"] = request.location_type
            
        # Perform reverse geocoding
        reverse_result = gmaps_client.reverse_geocode(**reverse_params)
        
        if not reverse_result:
            raise HTTPException(status_code=404, detail="No address found for coordinates")
            
        results = []
        for result in reverse_result[:5]:  # Limit to top 5 results
            location = result["geometry"]["location"]
            results.append(GeocodeResponse(
                formatted_address=result["formatted_address"],
                latitude=location["lat"],
                longitude=location["lng"],
                place_id=result["place_id"],
                address_components=result["address_components"],
                geometry_type=result["geometry"]["location_type"]
            ))
            
        return results
        
    except (gmaps_exceptions.ApiError, gmaps_exceptions.TransportError, gmaps_exceptions.Timeout) as e:
        logging.error(f"Google Maps API error: {e}")
        raise handle_geocoding_error(e)
    except Exception as e:
        logging.error(f"Unexpected error in reverse geocoding: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.post("/geocode/batch", response_model=BatchGeocodeResponse)
async def batch_geocode(request: BatchGeocodeRequest):
    """Batch geocode multiple addresses"""
    try:
        gmaps_client = get_gmaps_client()
        
        results = []
        errors = []
        
        # Limit batch size to prevent excessive API usage
        addresses = request.addresses[:request.max_results or 10]
        
        for i, address in enumerate(addresses):
            try:
                geocoding_params = {"address": address}
                if request.region:
                    geocoding_params["region"] = request.region
                    
                geocode_result = gmaps_client.geocode(**geocoding_params)
                
                if geocode_result:
                    result = geocode_result[0]
                    location = result["geometry"]["location"]
                    results.append(GeocodeResponse(
                        formatted_address=result["formatted_address"],
                        latitude=location["lat"],
                        longitude=location["lng"],
                        place_id=result["place_id"],
                        address_components=result["address_components"],
                        geometry_type=result["geometry"]["location_type"]
                    ))
                else:
                    errors.append({"index": i, "address": address, "error": "Address not found"})
                    
            except gmaps_exceptions.ApiError as e:
                errors.append({"index": i, "address": address, "error": str(e)})
            except Exception as e:
                errors.append({"index": i, "address": address, "error": "Processing error"})
                
        return BatchGeocodeResponse(results=results, errors=errors)
        
    except Exception as e:
        logging.error(f"Unexpected error in batch geocoding: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@api_router.get("/geocode")
async def geocode_address(address: str = Query(...)):
    """Legacy geocode endpoint - converts address to coordinates"""
    try:
        # Use the new forward geocoding functionality
        request = GeocodeRequest(address=address)
        result = await forward_geocode(request)
        
        # Return in legacy format for backward compatibility
        return {
            "coordinates": {
                "latitude": result.latitude,
                "longitude": result.longitude
            },
            "formatted_address": result.formatted_address
        }
    except HTTPException:
        raise
    except Exception as e:
        logging.error(f"Error in legacy geocode endpoint: {e}")
        raise HTTPException(status_code=500, detail="Geocoding failed")

# =================== RESTAURANT OWNER AUTHENTICATION ===================

@api_router.post("/auth/register")
async def register_owner(owner_data: RestaurantOwnerCreate):
    """Register a new restaurant owner"""
    try:
        # Check if email already exists
        existing_owner = await db.restaurant_owners.find_one({"email": owner_data.email})
        if existing_owner:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create new owner
        owner = RestaurantOwner(
            email=owner_data.email,
            password_hash=hash_password(owner_data.password),
            business_name=owner_data.business_name,
            phone=owner_data.phone,
            first_name=owner_data.first_name,
            last_name=owner_data.last_name
        )
        
        owner_dict = prepare_for_mongo(owner.dict())
        result = await db.restaurant_owners.insert_one(owner_dict)
        
        # Create access token
        token = create_access_token({"user_id": owner.id, "email": owner.email, "user_type": "owner"})
        
        return {
            "message": "Registration successful",
            "access_token": token,
            "token_type": "bearer",
            "user_type": "owner",
            "user": {
                "id": owner.id,
                "email": owner.email,
                "business_name": owner.business_name,
                "first_name": owner.first_name,
                "last_name": owner.last_name
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@api_router.post("/auth/login")
async def login_owner(login_data: RestaurantOwnerLogin):
    """Login restaurant owner"""
    try:
        # Find user by email
        user = await db.restaurant_owners.find_one({"email": login_data.email})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        user = prepare_from_mongo(user)
        
        # Verify password
        if not verify_password(login_data.password, user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Create access token
        token = create_access_token({"user_id": user['id'], "email": user['email'], "user_type": "owner"})
        
        return {
            "message": "Login successful",
            "access_token": token,
            "token_type": "bearer",
            "user_type": "owner",
            "user": {
                "id": user['id'],
                "email": user['email'],
                "business_name": user['business_name'],
                "first_name": user['first_name'],
                "last_name": user['last_name'],
                "restaurant_ids": user.get('restaurant_ids', [])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@api_router.get("/auth/me")
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
    """Get current user information"""
    return {
        "id": current_user['id'],
        "email": current_user['email'],
        "business_name": current_user['business_name'],
        "first_name": current_user['first_name'],
        "last_name": current_user['last_name'],
        "phone": current_user['phone'],
        "restaurant_ids": current_user.get('restaurant_ids', []),
        "is_verified": current_user.get('is_verified', False)
    }

# =================== REGULAR USER AUTHENTICATION ===================

@api_router.post("/users/register")
async def register_user(user_data: UserCreate):
    """Register a new regular user"""
    try:
        # Check if email already exists in users or restaurant owners
        existing_user = await db.users.find_one({"email": user_data.email})
        existing_owner = await db.restaurant_owners.find_one({"email": user_data.email})
        
        if existing_user or existing_owner:
            raise HTTPException(status_code=400, detail="Email already registered")
        
        # Create new user
        user = User(
            email=user_data.email,
            password_hash=hash_password(user_data.password),
            first_name=user_data.first_name,
            last_name=user_data.last_name
        )
        
        user_dict = prepare_for_mongo(user.dict())
        result = await db.users.insert_one(user_dict)
        
        # Create access token
        token = create_access_token({"user_id": user.id, "email": user.email, "user_type": "user"})
        
        return {
            "message": "Registration successful",
            "access_token": token,
            "token_type": "bearer",
            "user_type": "user",
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "favorite_restaurants": []
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User registration error: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@api_router.post("/users/login")
async def login_user(login_data: UserLogin):
    """Login regular user"""
    try:
        # Find user by email
        user = await db.users.find_one({"email": login_data.email})
        if not user:
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        user = prepare_from_mongo(user)
        
        # Verify password
        if not verify_password(login_data.password, user['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid email or password")
        
        # Create access token
        token = create_access_token({"user_id": user['id'], "email": user['email'], "user_type": "user"})
        
        return {
            "message": "Login successful",
            "access_token": token,
            "token_type": "bearer",
            "user_type": "user",
            "user": {
                "id": user['id'],
                "email": user['email'],
                "first_name": user['first_name'],
                "last_name": user['last_name'],
                "favorite_restaurant_ids": user.get('favorite_restaurant_ids', [])
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"User login error: {e}")
        raise HTTPException(status_code=500, detail="Login failed")

@api_router.get("/users/me")
async def get_current_user_info(current_user: dict = Depends(get_current_regular_user)):
    """Get current regular user information"""
    return {
        "id": current_user['id'],
        "email": current_user['email'],
        "first_name": current_user['first_name'],
        "last_name": current_user['last_name'],
        "favorite_restaurant_ids": current_user.get('favorite_restaurant_ids', []),
        "preferences": current_user.get('preferences', {}),
        "created_at": current_user.get('created_at')
    }

@api_router.post("/users/favorites/{restaurant_id}")
async def add_favorite_restaurant(
    restaurant_id: str,
    current_user: dict = Depends(get_current_regular_user)
):
    """Add restaurant to user's favorites"""
    try:
        # Check if already in favorites
        current_favorites = current_user.get('favorite_restaurant_ids', [])
        if restaurant_id in current_favorites:
            return {"message": "Restaurant already in favorites"}
        
        # Add to favorites
        await db.users.update_one(
            {"id": current_user['id']},
            {"$push": {"favorite_restaurant_ids": restaurant_id}}
        )
        
        return {"message": "Restaurant added to favorites"}
        
    except Exception as e:
        logger.error(f"Add favorite error: {e}")
        raise HTTPException(status_code=500, detail="Failed to add favorite")

@api_router.delete("/users/favorites/{restaurant_id}")
async def remove_favorite_restaurant(
    restaurant_id: str,
    current_user: dict = Depends(get_current_regular_user)
):
    """Remove restaurant from user's favorites"""
    try:
        # Remove from favorites
        await db.users.update_one(
            {"id": current_user['id']},
            {"$pull": {"favorite_restaurant_ids": restaurant_id}}
        )
        
        return {"message": "Restaurant removed from favorites"}
        
    except Exception as e:
        logger.error(f"Remove favorite error: {e}")
        raise HTTPException(status_code=500, detail="Failed to remove favorite")

@api_router.get("/users/favorites")
async def get_favorite_restaurants(current_user: dict = Depends(get_current_regular_user)):
    """Get user's favorite restaurants with details"""
    try:
        favorite_ids = current_user.get('favorite_restaurant_ids', [])
        
        if not favorite_ids:
            return {"favorites": []}
        
        # Get restaurant details for favorites (from mock database)
        favorites = []
        restaurants_cursor = db.restaurants.find({"id": {"$in": favorite_ids}})
        restaurants = await restaurants_cursor.to_list(length=None)
        
        for restaurant in restaurants:
            restaurant = prepare_from_mongo(restaurant)
            favorites.append({
                "id": restaurant['id'],
                "name": restaurant['name'],
                "address": restaurant.get('address', ''),
                "rating": restaurant.get('rating'),
                "cuisine_type": restaurant.get('cuisine_type', []),
                "specials_count": len(restaurant.get('specials', []))
            })
        
        return {"favorites": favorites}
        
    except Exception as e:
        logger.error(f"Get favorites error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get favorites")

# =================== RESTAURANT CLAIMING & MANAGEMENT ===================

@api_router.get("/owner/search-restaurants")
async def search_restaurants_to_claim(
    query: str = Query(..., min_length=2),
    latitude: Optional[float] = Query(None),
    longitude: Optional[float] = Query(None),
    current_user: dict = Depends(get_current_user)
):
    """Search Google Places restaurants for claiming"""
    try:
        # If no coordinates provided, use a default (San Francisco)
        if not latitude or not longitude:
            latitude, longitude = 37.7749, -122.4194
        
        # Search Google Places
        restaurants = await search_google_places_real(
            latitude=latitude,
            longitude=longitude,
            radius=50000,  # 50km radius
            query=query,
            limit=20
        )
        
        # Add claiming status for each restaurant
        for restaurant in restaurants:
            # Check if already claimed
            claimed_restaurant = await db.restaurant_claims.find_one({
                "google_place_id": restaurant['id'].replace('google_', ''),
                "status": {"$in": ["approved", "pending"]}
            })
            restaurant['is_claimed'] = bool(claimed_restaurant)
            restaurant['claim_status'] = claimed_restaurant.get('status') if claimed_restaurant else None
        
        return {"restaurants": restaurants}
        
    except Exception as e:
        logger.error(f"Search restaurants error: {e}")
        raise HTTPException(status_code=500, detail="Search failed")

@api_router.post("/owner/claim-restaurant")
async def claim_restaurant(
    claim_data: RestaurantClaim,
    current_user: dict = Depends(get_current_user)
):
    """Claim a restaurant from Google Places"""
    try:
        # Check if restaurant is already claimed
        existing_claim = await db.restaurant_claims.find_one({
            "google_place_id": claim_data.google_place_id,
            "status": {"$in": ["approved", "pending"]}
        })
        
        if existing_claim:
            raise HTTPException(status_code=400, detail="Restaurant is already claimed or pending approval")
        
        # Create claim record
        claim_record = {
            "id": str(uuid.uuid4()),
            "owner_id": current_user['id'],
            "google_place_id": claim_data.google_place_id,
            "business_name": claim_data.business_name,
            "verification_notes": claim_data.verification_notes,
            "status": "pending",  # pending, approved, rejected
            "created_at": datetime.now(timezone.utc).isoformat(),
            "reviewed_at": None,
            "reviewed_by": None
        }
        
        await db.restaurant_claims.insert_one(claim_record)
        
        return {
            "message": "Restaurant claim submitted successfully",
            "claim_id": claim_record['id'],
            "status": "pending"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Claim restaurant error: {e}")
        raise HTTPException(status_code=500, detail="Claim submission failed")

@api_router.get("/owner/my-restaurants")
async def get_my_restaurants(current_user: dict = Depends(get_current_user)):
    """Get restaurants owned by current user"""
    try:
        # Get approved claims for this user
        claims_cursor = db.restaurant_claims.find({
            "owner_id": current_user['id'],
            "status": "approved"
        })
        approved_claims = await claims_cursor.to_list(length=None)
        
        # Get pending claims
        pending_claims_cursor = db.restaurant_claims.find({
            "owner_id": current_user['id'],
            "status": "pending"
        })
        pending_claims = await pending_claims_cursor.to_list(length=None)
        
        # Get restaurant details for approved claims
        restaurants = []
        for claim in approved_claims:
            # Find restaurant in our database or get from Google Places
            restaurant = await db.restaurants.find_one({"google_place_id": claim['google_place_id']})
            
            if restaurant:
                restaurant = prepare_from_mongo(restaurant)
            else:
                # Create restaurant record from Google Places data if it doesn't exist
                # For now, create a basic record
                restaurant = {
                    "id": f"google_{claim['google_place_id']}",
                    "google_place_id": claim['google_place_id'],
                    "name": claim['business_name'],
                    "owner_id": current_user['id'],
                    "specials": [],
                    "is_verified": True,
                    "created_at": datetime.now(timezone.utc).isoformat()
                }
                
                # Insert into database
                await db.restaurants.insert_one(prepare_for_mongo(restaurant))
            
            restaurants.append(restaurant)
        
        return {
            "restaurants": restaurants,
            "pending_claims": [prepare_from_mongo(claim) for claim in pending_claims]
        }
        
    except Exception as e:
        logger.error(f"Get my restaurants error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get restaurants")

# =================== SPECIALS MANAGEMENT ===================

@api_router.post("/owner/restaurants/{restaurant_id}/specials")
async def create_special(
    restaurant_id: str,
    special_data: SpecialCreate,
    current_user: dict = Depends(get_current_user)
):
    """Create a new special for restaurant"""
    try:
        # Verify restaurant ownership
        restaurant = await db.restaurants.find_one({"id": restaurant_id})
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        restaurant = prepare_from_mongo(restaurant)
        
        # Check if user owns this restaurant (via claims)
        claim = await db.restaurant_claims.find_one({
            "owner_id": current_user['id'],
            "google_place_id": restaurant.get('google_place_id', ''),
            "status": "approved"
        })
        
        if not claim and restaurant.get('owner_id') != current_user['id']:
            raise HTTPException(status_code=403, detail="You don't own this restaurant")
        
        # Create new special
        special = RestaurantSpecial(
            title=special_data.title,
            description=special_data.description,
            special_type=special_data.special_type,
            price=special_data.price,
            original_price=special_data.original_price,
            days_available=special_data.days_available,
            time_start=special_data.time_start,
            time_end=special_data.time_end
        )
        
        special_dict = prepare_for_mongo(special.dict())
        
        # Add special to restaurant
        await db.restaurants.update_one(
            {"id": restaurant_id},
            {"$push": {"specials": special_dict}}
        )
        
        return {
            "message": "Special created successfully",
            "special_id": special.id,
            "special": special_dict
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Create special error: {e}")
        raise HTTPException(status_code=500, detail="Failed to create special")

@api_router.get("/owner/restaurants/{restaurant_id}/specials")
async def get_restaurant_specials(
    restaurant_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Get all specials for a restaurant"""
    try:
        # Verify restaurant ownership
        restaurant = await db.restaurants.find_one({"id": restaurant_id})
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        restaurant = prepare_from_mongo(restaurant)
        
        # Check ownership
        claim = await db.restaurant_claims.find_one({
            "owner_id": current_user['id'],
            "google_place_id": restaurant.get('google_place_id', ''),
            "status": "approved"
        })
        
        if not claim and restaurant.get('owner_id') != current_user['id']:
            raise HTTPException(status_code=403, detail="You don't own this restaurant")
        
        return {
            "specials": restaurant.get('specials', []),
            "restaurant_name": restaurant.get('name', '')
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get specials error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get specials")

@api_router.put("/owner/restaurants/{restaurant_id}/specials/{special_id}")
async def update_special(
    restaurant_id: str,
    special_id: str,
    special_update: SpecialUpdate,
    current_user: dict = Depends(get_current_user)
):
    """Update a special"""
    try:
        # Verify restaurant ownership
        restaurant = await db.restaurants.find_one({"id": restaurant_id})
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        restaurant = prepare_from_mongo(restaurant)
        
        # Check ownership
        claim = await db.restaurant_claims.find_one({
            "owner_id": current_user['id'],
            "google_place_id": restaurant.get('google_place_id', ''),
            "status": "approved"
        })
        
        if not claim and restaurant.get('owner_id') != current_user['id']:
            raise HTTPException(status_code=403, detail="You don't own this restaurant")
        
        # Find and update the special
        specials = restaurant.get('specials', [])
        special_found = False
        
        for i, special in enumerate(specials):
            if special.get('id') == special_id:
                # Update fields that are provided
                update_data = special_update.dict(exclude_unset=True)
                for key, value in update_data.items():
                    specials[i][key] = value
                special_found = True
                break
        
        if not special_found:
            raise HTTPException(status_code=404, detail="Special not found")
        
        # Update restaurant in database
        await db.restaurants.update_one(
            {"id": restaurant_id},
            {"$set": {"specials": specials}}
        )
        
        return {"message": "Special updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Update special error: {e}")
        raise HTTPException(status_code=500, detail="Failed to update special")

@api_router.delete("/owner/restaurants/{restaurant_id}/specials/{special_id}")
async def delete_special(
    restaurant_id: str,
    special_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Delete a special"""
    try:
        # Verify restaurant ownership
        restaurant = await db.restaurants.find_one({"id": restaurant_id})
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        restaurant = prepare_from_mongo(restaurant)
        
        # Check ownership
        claim = await db.restaurant_claims.find_one({
            "owner_id": current_user['id'],
            "google_place_id": restaurant.get('google_place_id', ''),
            "status": "approved"
        })
        
        if not claim and restaurant.get('owner_id') != current_user['id']:
            raise HTTPException(status_code=403, detail="You don't own this restaurant")
        
        # Remove the special
        await db.restaurants.update_one(
            {"id": restaurant_id},
            {"$pull": {"specials": {"id": special_id}}}
        )
        
        return {"message": "Special deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Delete special error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete special")

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