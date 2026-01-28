from fastapi import FastAPI, APIRouter, HTTPException, Depends, Query, Request
from fastapi.responses import FileResponse
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
from foursquare_service import get_foursquare_service, FoursquareAPIError
from onesignal_service import (
    get_onesignal_service, 
    get_restaurant_notification_service, 
    NotificationPayload
)

# Import production services
from cache_service import get_cache_service, CacheType, initialize_cache_service
from database_service import get_database_service, initialize_database_service
try:
    from redis_service import get_redis_service, initialize_redis_service
except ImportError as e:
    print(f"Redis service not available: {e}")
    get_redis_service = lambda: None
    initialize_redis_service = lambda: None
from monitoring_service import get_monitoring_service, initialize_monitoring_service
from owner_service import (
    get_owner_service, 
    get_owner_admin_service,
    RestaurantOwnerCreate,
    RestaurantOwner,
    OwnerLoginRequest,
    RestaurantClaimRequest,
    OwnerSpecialCreate,
    OwnerSpecial,
    OwnerDashboardStats,
    Referral,
    ReferralStatus,
    generate_referral_code
)
from coupon_service import (
    get_coupon_service,
    CouponCreate,
    Coupon,
    CouponRedemption,
    CouponAnalytics
)

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ.get('MONGO_URL')
db_name = os.environ.get('DB_NAME', 'onthecheap_production')

if not mongo_url:
    raise ValueError("MONGO_URL environment variable is required")

print(f"[INFO] Connecting to MongoDB database: {db_name}")
client = AsyncIOMotorClient(mongo_url)
db = client[db_name]

# Production services - will be initialized on startup
cache_service = None
db_service = None
redis_service = None
monitoring_service = None

# JWT Configuration
JWT_SECRET = os.environ.get('JWT_SECRET')
if not JWT_SECRET:
    JWT_SECRET = 'on-the-cheap-super-secret-jwt-key-2024'  # Default for development
    print("[WARNING] JWT_SECRET not set, using default value")
JWT_ALGORITHM = 'HS256'
security = HTTPBearer()

# Create the main app without a prefix
app = FastAPI(title="On-the-Cheap API", description="Find local restaurant and bar specials")

# Root health endpoint for Kubernetes health checks
@app.get("/health")
async def health_check():
    """Root health check endpoint for Kubernetes"""
    return {"status": "healthy", "service": "on-the-cheap-api"}

# Production startup and shutdown events
@app.on_event("startup")
async def startup_event():
    """Initialize production services on startup"""
    global cache_service, db_service, redis_service, monitoring_service
    
    logger.info("Initializing production services...")
    
    # Initialize cache service
    cache_service = await initialize_cache_service()
    
    # Initialize database service with indexes
    db_service = await initialize_database_service()
    
    # Initialize Redis distributed caching (fallback to in-memory if Redis unavailable)
    try:
        redis_service = await initialize_redis_service()
        logger.info("Redis distributed caching enabled")
    except Exception as e:
        logger.warning(f"Redis not available, using in-memory cache: {e}")
        redis_service = None
    
    # Initialize monitoring service
    monitoring_service = initialize_monitoring_service()
    
    # Initialize mock data if needed
    await init_mock_data()
    
    logger.info("Production services initialized successfully")

@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    global db_service, redis_service, monitoring_service
    
    logger.info("Shutting down production services...")
    
    if db_service:
        await db_service.close()
    
    if redis_service:
        await redis_service.close()
    
    if monitoring_service:
        monitoring_service.stop_monitoring()
    
    logger.info("Production services shutdown complete")

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

class RestaurantOwnerCreate(BaseModel):
    first_name: str = Field(..., min_length=1, max_length=50)
    last_name: str = Field(..., min_length=1, max_length=50)
    email: str
    password: str = Field(..., min_length=8)
    phone: str = Field(..., min_length=10, max_length=20)
    business_name: Optional[str] = Field(None, max_length=100)
    business_type: str = Field(default="restaurant")  # restaurant, bar, cafe, food_truck, etc.
    referral_code: Optional[str] = Field(None, description="Referral code from another owner")

class RestaurantOwnerLogin(BaseModel):
    email: str
    password: str

# Analytics Models
class AnalyticsEventType(str, Enum):
    CARD_VIEW = "card_view"           # Restaurant card displayed in results
    CARD_CLICK = "card_click"         # User clicked on restaurant card
    SPECIAL_VIEW = "special_view"     # User viewed a specific special/deal
    SHARE_CLICK = "share_click"       # User clicked share button
    FAVORITE_ADD = "favorite_add"     # User added to favorites
    FAVORITE_REMOVE = "favorite_remove"  # User removed from favorites
    DIRECTIONS_CLICK = "directions_click"  # User clicked get directions
    CALL_CLICK = "call_click"         # User clicked phone number
    CHECKIN_ATTEMPT = "checkin_attempt"   # User attempted to check in
    CHECKIN_VERIFIED = "checkin_verified"  # Check-in verified (within geofence)
    CHECKIN_FAILED = "checkin_failed"     # Check-in failed (outside geofence)

class AnalyticsEvent(BaseModel):
    event_type: AnalyticsEventType
    restaurant_id: str
    special_id: Optional[str] = None  # For special_view events
    user_id: Optional[str] = None     # Optional - can track anonymous users
    user_latitude: Optional[float] = None  # For check-in verification
    user_longitude: Optional[float] = None
    metadata: Optional[dict] = None   # Additional context (share_type, etc.)

class CheckInRequest(BaseModel):
    restaurant_id: str
    latitude: float
    longitude: float

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
    """Get current authenticated regular user (also supports owners logged in as customers)"""
    token = credentials.credentials
    payload = verify_token(token)
    user_id = payload.get("user_id")
    user_type = payload.get("user_type")
    
    if not user_id or user_type != "user":
        raise HTTPException(status_code=401, detail="Invalid user token")
    
    # First try to find in users collection
    user = await db.users.find_one({"id": user_id})
    if user:
        return prepare_from_mongo(user)
    
    # If not found, check restaurant_owners collection (owner logged in as customer)
    owner = await db.restaurant_owners.find_one({"id": user_id})
    if owner:
        owner = prepare_from_mongo(owner)
        # Return owner data in user-like format
        return {
            'id': owner['id'],
            'email': owner['email'],
            'first_name': owner.get('first_name', ''),
            'last_name': owner.get('last_name', ''),
            'favorite_restaurant_ids': owner.get('favorite_restaurant_ids', []),
            'preferences': owner.get('preferences', {}),
            'created_at': owner.get('created_at'),
            'is_owner': True  # Flag to identify owner-as-customer
        }
    
    raise HTTPException(status_code=401, detail="User not found")

# Optional security for endpoints that can work with or without authentication
optional_security = HTTPBearer(auto_error=False)

async def get_current_user_from_token(token: str):
    """Get current user from token string"""
    payload = verify_token(token)
    user_id = payload.get("user_id")
    user_type = payload.get("user_type", "owner")  # Default to owner for backward compatibility
    
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    if user_type == "owner":
        user = await db.restaurant_owners.find_one({"id": user_id})
    else:
        user = await db.users.find_one({"id": user_id})
    
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    
    user_data = prepare_from_mongo(user)
    user_data["user_type"] = user_type
    return user_data

async def get_current_user_optional(credentials: Optional[HTTPAuthorizationCredentials] = Depends(optional_security)):
    """Get current authenticated user (optional - returns None if no valid token)"""
    if not credentials:
        return None
        
    try:
        token = credentials.credentials
        payload = verify_token(token)
        user_id = payload.get("user_id")
        user_type = payload.get("user_type", "owner")
        
        if not user_id:
            return None
        
        if user_type == "owner":
            user = await db.restaurant_owners.find_one({"id": user_id})
        else:
            user = await db.users.find_one({"id": user_id})
        
        if not user:
            return None
        
        user_data = prepare_from_mongo(user)
        user_data["user_type"] = user_type
        return user_data
        
    except:
        return None

# Google Places API Integration
async def search_google_places_real(latitude: float, longitude: float, radius: int, query: Optional[str] = None, limit: int = 20) -> List[dict]:
    """Search for real restaurants using Google Places API with caching"""
    global cache_service
    
    # Try cache first
    cache_params = {
        "latitude": round(latitude, 4),  # Round for cache key consistency
        "longitude": round(longitude, 4),
        "radius": radius,
        "query": query or "",
        "limit": limit
    }
    
    if cache_service:
        cached_data = await cache_service.get(CacheType.GOOGLE_PLACES, **cache_params)
        if cached_data:
            logger.info("Cache hit for Google Places search")
            cache_service.stats["api_calls_saved"] += 1
            cache_service.stats["cost_saved"] += 0.017  # Estimated cost per Places API call
            return cached_data
    
    google_api_key = os.environ.get('GOOGLE_PLACES_API_KEY')
    if not google_api_key:
        logger.warning("Google Places API key not found, skipping real API call")
        return []
    
    try:
        # Track API usage
        if cache_service:
            cache_service.track_api_usage("google_places", requests=1, cost=0.017)
        
        # Check if we should throttle API calls
        if cache_service and cache_service.should_throttle("google_places", threshold=0.85):
            logger.warning("Google Places API throttled due to high usage")
            return []
        
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
                        
                        # Process photos if available - temporarily using fallback only due to URL issues
                        photos = []
                        # TODO: Fix Google Places Photo URL generation - currently returning 404s
                        # Temporarily use fallback photos for all restaurants
                        restaurant_types = place.get('types', [])
                        is_mobile = any(t in ['mobile_vendor', 'food_truck'] for t in restaurant_types)
                        photos = get_fallback_photos(
                            display_name.get('text', 'Unknown Restaurant'),
                            restaurant_types,
                            is_mobile
                        )
                        
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
                            'photos': photos,  # Add photos array
                            'specials': [],  # External restaurants don't have specials in our system yet
                            'is_verified': True,
                            'source': 'google_places',
                            'distance': calculate_distance(
                                latitude, longitude,
                                location.get('latitude', latitude),
                                location.get('longitude', longitude)
                            ),
                            'created_at': datetime.now(timezone.utc).isoformat(),
                            'specials_message': 'Specials data coming soon - check back later!'
                        }
                        restaurants.append(restaurant)
                    except Exception as e:
                        logger.warning(f"Error processing Google Places result: {e}")
                        continue
                
                # Cache the results
                if cache_service:
                    await cache_service.set(CacheType.GOOGLE_PLACES, restaurants, **cache_params)
                
                logger.info(f"Found {len(restaurants)} restaurants from Google Places API")
                return restaurants
            else:
                logger.error(f"Google Places API error: {response.status_code} - {response.text}")
                return []
                
    except Exception as e:
        logger.error(f"Error calling Google Places API: {e}")
        return []

async def search_external_restaurants(latitude: float, longitude: float, radius: int, query: Optional[str] = None, limit: int = 20, include_mobile_vendors: bool = True) -> List[dict]:
    """Search for restaurants and mobile vendors using external APIs (Foursquare) as fallback"""
    try:
        # Try Foursquare first
        foursquare_service = get_foursquare_service()
        if not foursquare_service:
            logger.warning("Foursquare service not available, skipping external search")
            return []
            
        foursquare_venues = await foursquare_service.search_restaurants(
            latitude=latitude,
            longitude=longitude,
            radius_meters=radius,
            query=query,
            limit=limit,
            include_mobile_vendors=include_mobile_vendors
        )
        
        # Convert Foursquare format to our standard format
        restaurants = []
        for venue in foursquare_venues:
            try:
                restaurant = {
                    'id': venue.id,  # Already prefixed with 'foursquare_'
                    'name': venue.name,
                    'address': venue.address or '',
                    'location': {
                        'latitude': venue.latitude or latitude,
                        'longitude': venue.longitude or longitude
                    },
                    'phone': venue.phone,
                    'website': venue.website,
                    'cuisine_type': venue.categories,
                    'rating': venue.rating,
                    'price_level': venue.price,
                    'specials': [],  # External restaurants don't have specials in our system yet
                    'is_verified': True,
                    'source': 'foursquare',
                    'is_mobile_vendor': getattr(venue, 'is_mobile_vendor', False),
                    'vendor_type': 'mobile' if getattr(venue, 'is_mobile_vendor', False) else 'permanent',
                    'distance': calculate_distance(
                        latitude, longitude,
                        venue.latitude or latitude,
                        venue.longitude or longitude
                    ),
                    'created_at': datetime.now(timezone.utc).isoformat(),
                    'specials_message': 'Specials data coming soon - check back later!'
                }
                restaurants.append(restaurant)
            except Exception as e:
                logger.warning(f"Error processing Foursquare venue: {e}")
                continue
        
        logger.info(f"Found {len(restaurants)} restaurants from Foursquare")
        return restaurants
        
    except FoursquareAPIError as e:
        logger.error(f"Foursquare API error: {e}")
        return []
    except Exception as e:
        logger.error(f"Error calling external restaurant APIs: {e}")
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

def get_fallback_photos(restaurant_name: str, venue_types: List[str], is_mobile_vendor: bool = False) -> List[dict]:
    """Generate fallback photos for restaurants without images"""
    
    # Determine primary venue type
    venue_type = "restaurant"  # default
    if is_mobile_vendor:
        venue_type = "food_truck"
    elif any(t in ['bar', 'night_club', 'liquor_store'] for t in venue_types):
        venue_type = "bar"
    elif any(t in ['cafe', 'bakery', 'coffee_shop'] for t in venue_types):
        venue_type = "cafe"
    elif any(t in ['fast_food', 'meal_takeaway'] for t in venue_types):
        venue_type = "fast_food"
    
    # Generate fallback image URLs (using placeholder service or default images)
    fallback_images = {
        "restaurant": f"https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=400&h=300&fit=crop&crop=center",
        "bar": f"https://images.unsplash.com/photo-1514933651103-005eec06c04b?w=400&h=300&fit=crop&crop=center", 
        "cafe": f"https://images.unsplash.com/photo-1501339847302-ac426a4a7cbb?w=400&h=300&fit=crop&crop=center",
        "fast_food": f"https://images.unsplash.com/photo-1571091718767-18b5b1457add?w=400&h=300&fit=crop&crop=center",
        "food_truck": f"https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400&h=300&fit=crop&crop=center"
    }
    
    return [{
        'url': fallback_images.get(venue_type, fallback_images["restaurant"]),
        'width': 400,
        'height': 300,
        'is_fallback': True
    }]

def is_special_active_now(special_data: dict, restaurant_timezone: str = None) -> bool:
    """Check if special is currently active based on time and day in the restaurant's timezone"""
    try:
        from zoneinfo import ZoneInfo
    except ImportError:
        from backports.zoneinfo import ZoneInfo
    
    # Default to America/Chicago (Central Time) if no timezone specified
    tz_name = restaurant_timezone or special_data.get('timezone') or 'America/Chicago'
    
    try:
        tz = ZoneInfo(tz_name)
        now = datetime.now(tz)
    except Exception:
        # Fallback to UTC if timezone is invalid
        now = datetime.now(timezone.utc)
    
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
    vendor_type: Optional[str] = Query(None, regex="^(all|permanent|mobile|bar)$"),  # Filter for venue type
    limit: int = Query(default=20, ge=1, le=50)
):
    """Search for restaurants with specials near a location using fallback system"""
    try:
        all_restaurants = []
        
        # STEP 1: Get restaurants with owner-managed specials (highest priority)
        # Limit query to prevent memory issues - use geospatial query for better performance
        restaurants_cursor = db.restaurants.find({}).limit(5000)  # Reasonable limit
        all_restaurants_raw = await restaurants_cursor.to_list(length=5000)
        owner_restaurants = [prepare_from_mongo(restaurant) for restaurant in all_restaurants_raw]

        # Filter owner restaurants by location and add active specials
        for restaurant in owner_restaurants:
            location = restaurant.get('location', {})
            rest_lat = location.get('latitude', 0)
            rest_lon = location.get('longitude', 0)
            
            distance = calculate_distance(latitude, longitude, rest_lat, rest_lon)
            
            if distance <= radius:
                restaurant['distance'] = round(distance)
                restaurant['source'] = 'owner_managed'
                
                # Add photos (from database or fallback)
                if 'photos' not in restaurant or not restaurant['photos']:
                    restaurant['photos'] = get_fallback_photos(
                        restaurant.get('name', ''),
                        restaurant.get('cuisine_type', []),
                        restaurant.get('is_mobile_vendor', False)
                    )
                
                # Filter specials by type if specified
                if special_type:
                    restaurant['specials'] = [
                        special for special in restaurant.get('specials', [])
                        if special.get('special_type') == special_type and special.get('is_active', True)
                    ]
                else:
                    # Filter out inactive specials and check if currently active
                    active_specials = []
                    restaurant_tz = restaurant.get('timezone', 'America/Chicago')
                    for special in restaurant.get('specials', []):
                        if special.get('is_active', True) and is_special_active_now(special, restaurant_tz):
                            active_specials.append(special)
                    restaurant['specials'] = active_specials
                
                # Also fetch owner-created specials from owner_specials collection
                owner_specials_cursor = db.owner_specials.find({
                    "restaurant_id": restaurant.get('id'),
                    "is_active": True,
                    "approval_status": "approved"
                }, {"_id": 0})
                owner_specials = await owner_specials_cursor.to_list(length=None)
                
                # Add owner specials that are currently active
                for special in owner_specials:
                    if is_special_active_now(special, restaurant_tz):
                        # Apply special_type filter if specified
                        if special_type and special.get('special_type') != special_type:
                            continue
                        # Avoid duplicates by checking IDs
                        if not any(s.get('id') == special.get('id') for s in restaurant['specials']):
                            restaurant['specials'].append(special)
                
                # Include restaurants with active specials (or all if no special_type filter)
                if restaurant['specials'] or not special_type:
                    all_restaurants.append(restaurant)
        
        # STEP 2: If we need more restaurants, try Google Places API
        google_restaurants = []
        if len(all_restaurants) < limit:
            remaining_limit = limit - len(all_restaurants)
            google_restaurants = await search_google_places_real(latitude, longitude, radius, query, remaining_limit)
            
            # Add Google Places restaurants (no specials data yet)
            if not special_type:  # Only show when not filtering by special type
                for restaurant in google_restaurants:
                    if restaurant.get('distance', 0) <= radius:
                        restaurant['specials'] = []
                        if 'specials_message' not in restaurant:
                            restaurant['specials_message'] = 'Specials data coming soon - check back later!'
                        all_restaurants.append(restaurant)
        
        # STEP 3: If we still need more restaurants, try external APIs (Foursquare)
        if len(all_restaurants) < limit:
            remaining_limit = limit - len(all_restaurants)
            
            # Determine if we should include mobile vendors based on vendor_type filter
            include_mobile_vendors = vendor_type != 'permanent'
            
            external_restaurants = await search_external_restaurants(
                latitude, longitude, radius, query, remaining_limit, include_mobile_vendors
            )
            
            # Add external restaurants (no specials data yet)
            if not special_type:  # Only show when not filtering by special type
                for restaurant in external_restaurants:
                    if restaurant.get('distance', 0) <= radius:
                        # Avoid duplicates by checking if we already have this restaurant from other sources
                        existing_names = [r.get('name', '').lower() for r in all_restaurants]
                        if restaurant.get('name', '').lower() not in existing_names:
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
        
        # Filter by vendor type if provided
        if vendor_type and vendor_type != 'all':
            if vendor_type == 'mobile':
                nearby_restaurants = [
                    r for r in nearby_restaurants 
                    if r.get('is_mobile_vendor', False) or r.get('vendor_type') == 'mobile'
                ]
            elif vendor_type == 'permanent':
                nearby_restaurants = [
                    r for r in nearby_restaurants 
                    if not r.get('is_mobile_vendor', False) and r.get('vendor_type') != 'mobile'
                ]
            elif vendor_type == 'bar':
                # Filter for bars based on cuisine_type
                bar_keywords = ['bar', 'bars', 'pub', 'tavern', 'lounge', 'cocktail', 'brewery', 'wine bar', 'sports bar', 'night club']
                nearby_restaurants = [
                    r for r in nearby_restaurants 
                    if any(
                        any(keyword in cuisine.lower() for keyword in bar_keywords)
                        for cuisine in r.get('cuisine_type', [])
                    )
                ]
        
        # Sort by priority: owner-managed first, then by distance
        def sort_key(restaurant):
            source_priority = {
                'owner_managed': 0,  # Highest priority
                'google_places': 1,
                'foursquare': 2
            }
            source = restaurant.get('source', 'unknown')
            priority = source_priority.get(source, 999)
            distance = restaurant.get('distance', float('inf'))
            return (priority, distance)
        
        nearby_restaurants.sort(key=sort_key)
        
        # Limit results
        nearby_restaurants = nearby_restaurants[:limit]
        
        # Add proper specials messaging and mobile vendor flag for each restaurant
        for restaurant in nearby_restaurants:
            specials = restaurant.get('specials', [])
            source = restaurant.get('source', 'unknown')
            
            # Ensure is_mobile_vendor field exists for mobile app compatibility
            if 'is_mobile_vendor' not in restaurant:
                restaurant['is_mobile_vendor'] = False
            
            # Ensure photos field exists - add fallback if needed
            if 'photos' not in restaurant or not restaurant['photos']:
                restaurant['photos'] = get_fallback_photos(
                    restaurant.get('name', ''),
                    restaurant.get('cuisine_type', []),
                    restaurant.get('is_mobile_vendor', False)
                )
            
            if source == 'owner_managed':
                # Restaurants with registered owners
                if not specials:
                    restaurant['specials_message'] = "No current specials at this time"
                else:
                    restaurant['specials_message'] = f"{len(specials)} special{'s' if len(specials) != 1 else ''} available now"
            else:
                # External API restaurants (Google Places, Foursquare)
                restaurant['specials_message'] = "Specials data coming soon - check back later!"
        
        # Add source summary for debugging
        source_summary = {}
        specials_summary = {'with_specials': 0, 'no_specials': 0, 'external_restaurants': 0}
        
        for restaurant in nearby_restaurants:
            source = restaurant.get('source', 'unknown')
            source_summary[source] = source_summary.get(source, 0) + 1
            
            # Count specials availability
            if source == 'owner_managed':
                if restaurant.get('specials', []):
                    specials_summary['with_specials'] += 1
                else:
                    specials_summary['no_specials'] += 1
            else:
                specials_summary['external_restaurants'] += 1
        
        return {
            "restaurants": nearby_restaurants,
            "total": len(nearby_restaurants),
            "search_location": {"latitude": latitude, "longitude": longitude},
            "radius_meters": radius,
            "source_summary": source_summary,
            "specials_summary": specials_summary,
            "fallback_system_used": True
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
    restaurant_tz = restaurant.get('timezone', 'America/Chicago')
    
    # Filter only active specials that are currently running (from restaurant.specials array)
    active_specials = []
    for special in restaurant.get('specials', []):
        if special.get('is_active', True) and is_special_active_now(special, restaurant_tz):
            active_specials.append(special)
    
    # Also fetch owner-created specials from owner_specials collection
    owner_specials_cursor = db.owner_specials.find({
        "restaurant_id": restaurant_id,
        "is_active": True,
        "approval_status": "approved"
    }, {"_id": 0})
    owner_specials = await owner_specials_cursor.to_list(length=None)
    
    # Filter owner specials that are currently active
    for special in owner_specials:
        if is_special_active_now(special, restaurant_tz):
            # Avoid duplicates by checking IDs
            if not any(s.get('id') == special.get('id') for s in active_specials):
                active_specials.append(special)
    
    restaurant['specials'] = active_specials
    
    # Add specials messaging
    if active_specials:
        restaurant['specials_message'] = f"{len(active_specials)} special{'s' if len(active_specials) != 1 else ''} available now"
        restaurant['has_current_specials'] = True
    else:
        restaurant['specials_message'] = "No current specials at this time"
        restaurant['has_current_specials'] = False
    
    return restaurant

@api_router.post("/restaurants", response_model=dict)
async def create_restaurant(restaurant: Restaurant):
    """Create a new restaurant (for restaurant owners)"""
    restaurant_dict = restaurant.dict()
    restaurant_dict['created_at'] = datetime.now(timezone.utc).isoformat()
    
    result = await db.restaurants.insert_one(restaurant_dict)
    return {"id": restaurant.id, "message": "Restaurant created successfully"}

@api_router.patch("/restaurants/{restaurant_id}/timezone")
async def update_restaurant_timezone(
    restaurant_id: str, 
    timezone_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update a restaurant's timezone (owner only)"""
    try:
        if current_user.get("user_type") != "owner":
            raise HTTPException(status_code=403, detail="Owner access required")
        
        # Verify the owner has access to this restaurant
        owner = await db.restaurant_owners.find_one({"id": current_user["id"]})
        if not owner:
            raise HTTPException(status_code=404, detail="Owner not found")
        
        # Check if restaurant belongs to owner (by ID or email)
        restaurant = await db.restaurants.find_one({"id": restaurant_id})
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        owner_restaurant_ids = owner.get("restaurant_ids", [])
        if restaurant_id not in owner_restaurant_ids and restaurant.get("owner_email") != owner.get("email"):
            raise HTTPException(status_code=403, detail="You don't have access to this restaurant")
        
        # Validate timezone
        new_timezone = timezone_data.get("timezone", "America/Chicago")
        try:
            from zoneinfo import ZoneInfo
            ZoneInfo(new_timezone)  # Validate timezone exists
        except Exception:
            raise HTTPException(status_code=400, detail=f"Invalid timezone: {new_timezone}")
        
        # Update the timezone
        await db.restaurants.update_one(
            {"id": restaurant_id},
            {"$set": {"timezone": new_timezone}}
        )
        
        return {"message": "Timezone updated successfully", "timezone": new_timezone}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating timezone: {e}")
        raise HTTPException(status_code=500, detail="Failed to update timezone")

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
    """Convert address to coordinates using Google Geocoding API with free fallback"""
    global cache_service
    
    # Try cache first
    cache_params = {
        "address": request.address.lower().strip(),
        "region": request.region or "",
        "bounds": request.bounds or ""
    }
    
    if cache_service:
        cached_data = await cache_service.get(CacheType.GEOCODING, **cache_params)
        if cached_data:
            logger.info("Cache hit for geocoding request")
            cache_service.stats["api_calls_saved"] += 1
            cache_service.stats["cost_saved"] += 0.005  # Estimated cost per geocoding call
            return GeocodeResponse(**cached_data)
    
    # Try Google Maps API first
    try:
        # Track API usage
        if cache_service:
            cache_service.track_api_usage("google_geocoding", requests=1, cost=0.005)
        
        # Check if we should throttle API calls
        if cache_service and cache_service.should_throttle("google_geocoding", threshold=0.85):
            logger.warning("Google Geocoding API throttled due to high usage")
            raise HTTPException(status_code=429, detail="API rate limit approached, please try again later")
        
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
        
        response_data = {
            "formatted_address": result["formatted_address"],
            "latitude": location["lat"],
            "longitude": location["lng"],
            "place_id": result["place_id"],
            "address_components": result["address_components"],
            "geometry_type": result["geometry"]["location_type"]
        }
        
        # Cache the result
        if cache_service:
            await cache_service.set(CacheType.GEOCODING, response_data, ttl=86400, **cache_params)  # 24 hour cache
        
        return GeocodeResponse(**response_data)
        
    except (gmaps_exceptions.ApiError, gmaps_exceptions.TransportError, gmaps_exceptions.Timeout) as e:
        logger.warning(f"Google Maps API error: {e}, falling back to Nominatim")
        # Fall back to free Nominatim geocoding
        pass
    except HTTPException as e:
        if e.status_code != 404:
            raise
        # Fall back to free Nominatim for 404
        pass
    except Exception as e:
        logger.error(f"Unexpected error in Google geocoding: {e}")
        # Fall back to free service
        pass
    
    # Fallback: Use free Nominatim (OpenStreetMap) geocoding
    try:
        import httpx
        logger.info(f"Using Nominatim fallback for address: {request.address}")
        
        async with httpx.AsyncClient() as client:
            params = {
                "q": request.address,
                "format": "json",
                "limit": 1,
                "addressdetails": 1
            }
            if request.region:
                params["countrycodes"] = request.region.lower()
            
            response = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params=params,
                headers={"User-Agent": "OnTheCheap/1.0"}
            )
            
            if response.status_code != 200:
                raise HTTPException(status_code=500, detail="Geocoding service unavailable")
            
            results = response.json()
            
            if not results:
                raise HTTPException(status_code=404, detail="Address not found")
            
            result = results[0]
            
            # Convert Nominatim format to our format
            response_data = {
                "formatted_address": result.get("display_name", request.address),
                "latitude": float(result["lat"]),
                "longitude": float(result["lon"]),
                "place_id": result.get("place_id", "nominatim_" + result["osm_id"]),
                "address_components": [],  # Nominatim doesn't provide this in same format
                "geometry_type": "APPROXIMATE"
            }
            
            # Cache the fallback result
            if cache_service:
                await cache_service.set(CacheType.GEOCODING, response_data, ttl=86400, **cache_params)
            
            logger.info(f"Successfully geocoded using Nominatim: {response_data['formatted_address']}")
            return GeocodeResponse(**response_data)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Nominatim geocoding also failed: {e}")
        raise HTTPException(status_code=500, detail="All geocoding services failed")

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
    except HTTPException:
        raise
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
                    errors.append({"index": str(i), "address": address, "error": "Address not found"})
                    
            except gmaps_exceptions.ApiError as e:
                errors.append({"index": str(i), "address": address, "error": str(e)})
            except Exception as e:
                errors.append({"index": str(i), "address": address, "error": "Processing error"})
                
        return BatchGeocodeResponse(results=results, errors=errors)
        
    except HTTPException:
        raise
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
        
        # Handle referral code if provided
        referrer_id = None
        if owner_data.referral_code:
            referrer = await db.restaurant_owners.find_one({"referral_code": owner_data.referral_code.upper()})
            if referrer:
                referrer_id = referrer.get("id")
            else:
                # Invalid referral code - log but don't block registration
                logger.warning(f"Invalid referral code used: {owner_data.referral_code}")
        
        # Generate unique referral code for this new owner
        new_referral_code = generate_referral_code(owner_data.business_name)
        # Ensure uniqueness
        while await db.restaurant_owners.find_one({"referral_code": new_referral_code}):
            new_referral_code = generate_referral_code(owner_data.business_name)
        
        # Create owner dict directly (RestaurantOwner model has different fields)
        owner_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc).isoformat()
        
        owner_dict = {
            "id": owner_id,
            "email": owner_data.email,
            "password_hash": hash_password(owner_data.password),
            "business_name": owner_data.business_name,
            "business_type": owner_data.business_type or "restaurant",
            "phone": owner_data.phone,
            "first_name": owner_data.first_name,
            "last_name": owner_data.last_name,
            "status": "pending",
            "restaurant_ids": [],
            "verification_documents": [],
            "is_verified": False,
            "referral_code": new_referral_code,
            "referred_by": referrer_id,
            "referral_discount_applied": False,
            "created_at": now,
            "updated_at": now
        }
        
        result = await db.restaurant_owners.insert_one(owner_dict)
        
        # If referred, create a referral record
        if referrer_id:
            referral_record = {
                "id": str(uuid.uuid4()),
                "referrer_id": referrer_id,
                "referred_owner_id": owner_id,
                "referral_code_used": owner_data.referral_code.upper(),
                "status": "pending",
                "referred_owner_subscription_start": None,
                "qualification_date": None,
                "reward_applied_date": None,
                "created_at": now,
                "updated_at": now
            }
            await db.referrals.insert_one(referral_record)
            logger.info(f"Created referral record: {referrer_id} -> {owner_id}")
        
        # Create access token
        token = create_access_token({"user_id": owner_id, "email": owner_data.email, "user_type": "owner"})
        
        return {
            "message": "Registration successful",
            "access_token": token,
            "token_type": "bearer",
            "user_type": "owner",
            "user": {
                "id": owner_id,
                "email": owner_data.email,
                "business_name": owner_data.business_name,
                "first_name": owner_data.first_name,
                "last_name": owner_data.last_name,
                "referral_code": new_referral_code,
                "was_referred": referrer_id is not None
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
                "restaurant_ids": user.get('restaurant_ids', []),
                "referral_code": user.get('referral_code')
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

@api_router.patch("/owners/profile")
async def update_owner_profile(
    profile_update: dict,
    current_user: dict = Depends(get_current_user)
):
    """Update owner profile information"""
    try:
        if current_user.get("user_type") != "owner":
            raise HTTPException(status_code=403, detail="Owner access required")
        
        # Only allow updating specific fields
        allowed_fields = ['first_name', 'last_name', 'business_name', 'phone']
        update_data = {k: v for k, v in profile_update.items() if k in allowed_fields}
        
        if not update_data:
            raise HTTPException(status_code=400, detail="No valid fields to update")
        
        # Update in database
        update_data['updated_at'] = datetime.now(timezone.utc).isoformat()
        
        result = await db.restaurant_owners.update_one(
            {"id": current_user['id']},
            {"$set": update_data}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Owner not found")
        
        return {"message": "Profile updated successfully", "updated_fields": list(update_data.keys())}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating owner profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to update profile")

# =================== REFERRAL PROGRAM ===================

@api_router.get("/owners/referral-code")
async def get_owner_referral_code(current_user: dict = Depends(get_current_user)):
    """Get the current owner's referral code"""
    try:
        owner = await db.restaurant_owners.find_one({"id": current_user["id"]})
        if not owner:
            raise HTTPException(status_code=404, detail="Owner not found")
        
        referral_code = owner.get("referral_code")
        
        # Generate one if it doesn't exist (for existing owners before the feature)
        if not referral_code:
            referral_code = generate_referral_code(owner.get("business_name"))
            while await db.restaurant_owners.find_one({"referral_code": referral_code}):
                referral_code = generate_referral_code(owner.get("business_name"))
            
            await db.restaurant_owners.update_one(
                {"id": current_user["id"]},
                {"$set": {"referral_code": referral_code, "updated_at": datetime.now(timezone.utc).isoformat()}}
            )
        
        return {
            "referral_code": referral_code,
            "share_message": f"Join On-the-Cheap and get 10% off your first 6 months! Use my referral code: {referral_code}"
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting referral code: {e}")
        raise HTTPException(status_code=500, detail="Failed to get referral code")


@api_router.get("/owners/referrals")
async def get_owner_referrals(current_user: dict = Depends(get_current_user)):
    """Get the owner's referral history and stats"""
    try:
        owner_id = current_user["id"]
        
        # Get all referrals made by this owner
        referrals_cursor = db.referrals.find({"referrer_id": owner_id})
        referrals = await referrals_cursor.to_list(length=100)
        
        # Enrich referral data with referred owner info
        enriched_referrals = []
        for ref in referrals:
            if '_id' in ref:
                del ref['_id']
            
            # Get referred owner's basic info
            referred_owner = await db.restaurant_owners.find_one({"id": ref["referred_owner_id"]})
            if referred_owner:
                ref["referred_owner_name"] = f"{referred_owner.get('first_name', '')} {referred_owner.get('last_name', '')}".strip()
                ref["referred_owner_business"] = referred_owner.get("business_name", "N/A")
            else:
                ref["referred_owner_name"] = "Unknown"
                ref["referred_owner_business"] = "N/A"
            
            enriched_referrals.append(ref)
        
        # Calculate stats
        total_referrals = len(referrals)
        pending_referrals = sum(1 for r in referrals if r.get("status") == "pending")
        qualified_referrals = sum(1 for r in referrals if r.get("status") == "qualified")
        rewarded_referrals = sum(1 for r in referrals if r.get("status") == "rewarded")
        
        # Get owner's referral code
        owner = await db.restaurant_owners.find_one({"id": owner_id})
        referral_code = owner.get("referral_code") if owner else None
        
        return {
            "referral_code": referral_code,
            "stats": {
                "total_referrals": total_referrals,
                "pending": pending_referrals,
                "qualified": qualified_referrals,
                "rewarded": rewarded_referrals,
                "potential_savings": qualified_referrals * 20  # 20% discount per qualified referral
            },
            "referrals": enriched_referrals
        }
    except Exception as e:
        logger.error(f"Error getting referrals: {e}")
        raise HTTPException(status_code=500, detail="Failed to get referrals")


@api_router.get("/referral/validate/{code}")
async def validate_referral_code(code: str):
    """Validate a referral code (public endpoint for signup form)"""
    try:
        owner = await db.restaurant_owners.find_one({"referral_code": code.upper()})
        if owner:
            return {
                "valid": True,
                "referrer_name": f"{owner.get('first_name', '')} {owner.get('last_name', '')}".strip() or "A fellow restaurant owner",
                "discount": "10% off your first 6 months!"
            }
        return {"valid": False}
    except Exception as e:
        logger.error(f"Error validating referral code: {e}")
        return {"valid": False}


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
    """Login regular user (also allows owners to login as customers)"""
    try:
        # First, try to find user in regular users collection
        user = await db.users.find_one({"email": login_data.email})
        is_owner_as_customer = False
        
        if user:
            user = prepare_from_mongo(user)
            
            # Verify password
            if not verify_password(login_data.password, user['password_hash']):
                raise HTTPException(status_code=401, detail="Invalid email or password")
        else:
            # If not found in users, check restaurant_owners collection
            owner = await db.restaurant_owners.find_one({"email": login_data.email})
            if not owner:
                raise HTTPException(status_code=401, detail="Invalid email or password")
            
            owner = prepare_from_mongo(owner)
            
            # Verify owner password
            if not verify_password(login_data.password, owner['password_hash']):
                raise HTTPException(status_code=401, detail="Invalid email or password")
            
            # Owner logging in as customer - create a user-like object
            is_owner_as_customer = True
            user = {
                'id': owner['id'],
                'email': owner['email'],
                'first_name': owner.get('first_name', ''),
                'last_name': owner.get('last_name', ''),
                'favorite_restaurant_ids': owner.get('favorite_restaurant_ids', [])
            }
        
        # Create access token
        token = create_access_token({"user_id": user['id'], "email": user['email'], "user_type": "user"})
        
        return {
            "message": "Login successful",
            "access_token": token,
            "token_type": "bearer",
            "user_type": "user",
            "is_owner_as_customer": is_owner_as_customer,
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
        
        # Determine which collection to update
        collection = db.restaurant_owners if current_user.get('is_owner') else db.users
        
        # Add to favorites
        await collection.update_one(
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
        # Determine which collection to update
        collection = db.restaurant_owners if current_user.get('is_owner') else db.users
        
        # Remove from favorites
        await collection.update_one(
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
        
        favorites = []
        
        # Separate Google Places IDs from database IDs
        google_ids = [fid for fid in favorite_ids if fid.startswith('google_')]
        db_ids = [fid for fid in favorite_ids if not fid.startswith('google_')]
        
        # Get database restaurants (mock restaurants)
        if db_ids:
            restaurants_cursor = db.restaurants.find({"id": {"$in": db_ids}})
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
        
        # Get Google Places restaurants
        if google_ids:
            google_api_key = os.environ.get('GOOGLE_PLACES_API_KEY')
            
            if google_api_key:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    for google_id in google_ids:
                        try:
                            # Extract the Google Place ID from our format (google_PLACE_ID)
                            place_id = google_id.replace('google_', '')
                            
                            # Use the new Places API (same as restaurant search)
                            headers = {
                                "Content-Type": "application/json",
                                "X-Goog-Api-Key": google_api_key,
                                "X-Goog-FieldMask": "id,displayName,types,rating,priceLevel,location,formattedAddress,nationalPhoneNumber,websiteUri"
                            }
                            
                            # Get place details using the new Places API
                            response = await client.get(
                                f"https://places.googleapis.com/v1/places/{place_id}",
                                headers=headers
                            )
                            
                            if response.status_code == 200:
                                place = response.json()
                                
                                # Extract data from new API format
                                display_name = place.get('displayName', {})
                                name = display_name.get('text', 'Unknown Restaurant') if display_name else 'Unknown Restaurant'
                                
                                favorites.append({
                                    "id": google_id,  # Keep our format
                                    "name": name,
                                    "address": place.get('formattedAddress', ''),
                                    "rating": place.get('rating'),
                                    "cuisine_type": place.get('types', []),
                                    "specials_count": 0  # Google Places restaurants don't have our specials
                                })
                            else:
                                logger.warning(f"Failed to get Google Place details for {google_id}: HTTP {response.status_code}")
                                # Add placeholder for failed API call
                                favorites.append({
                                    "id": google_id,
                                    "name": "Restaurant (Details Unavailable)",
                                    "address": "",
                                    "rating": None,
                                    "cuisine_type": [],
                                    "specials_count": 0
                                })
                                
                        except Exception as e:
                            logger.warning(f"Failed to get Google Place details for {google_id}: {e}")
                            # Add a placeholder for failed lookups so user knows it exists
                            favorites.append({
                                "id": google_id,
                                "name": "Restaurant (Details Unavailable)",
                                "address": "",
                                "rating": None,
                                "cuisine_type": [],
                                "specials_count": 0
                            })
        
        return {"favorites": favorites}
        
    except Exception as e:
        logger.error(f"Get favorites error: {e}")
        raise HTTPException(status_code=500, detail="Failed to get favorites")

# =================== ACCOUNT DELETION ===================

class AccountDeletionRequest(BaseModel):
    email: str
    reason: Optional[str] = None

@api_router.post("/users/request-deletion")
async def request_account_deletion(request: AccountDeletionRequest):
    """Request account and data deletion"""
    try:
        # Check if user exists
        user = await db.users.find_one({"email": request.email})
        owner = await db.restaurant_owners.find_one({"email": request.email})
        
        if not user and not owner:
            # Don't reveal if account exists or not for privacy
            return {"message": "If an account exists with this email, a deletion request has been submitted. You will receive confirmation within 7 business days."}
        
        # Store deletion request
        deletion_request = {
            "email": request.email,
            "reason": request.reason,
            "user_type": "owner" if owner else "user",
            "status": "pending",
            "requested_at": datetime.now(timezone.utc),
            "user_id": owner.get("id") if owner else user.get("id") if user else None
        }
        
        await db.deletion_requests.insert_one(deletion_request)
        
        logger.info(f"Account deletion requested for: {request.email}")
        
        return {"message": "Your account deletion request has been submitted. Your account and all associated data will be deleted within 7 business days. You will receive a confirmation email once complete."}
        
    except Exception as e:
        logger.error(f"Account deletion request error: {e}")
        raise HTTPException(status_code=500, detail="Failed to submit deletion request")

@api_router.delete("/users/delete-account")
async def delete_own_account(current_user: dict = Depends(get_current_regular_user)):
    """Immediately delete own account and all associated data"""
    try:
        user_id = current_user.get("id")
        email = current_user.get("email")
        
        # Delete user's favorites, saved coupons, etc.
        await db.users.delete_one({"id": user_id})
        
        # Log the deletion
        await db.deletion_requests.insert_one({
            "email": email,
            "user_type": "user",
            "status": "completed",
            "requested_at": datetime.now(timezone.utc),
            "completed_at": datetime.now(timezone.utc),
            "user_id": user_id
        })
        
        logger.info(f"Account deleted for user: {email}")
        
        return {"message": "Your account and all associated data have been permanently deleted."}
        
    except Exception as e:
        logger.error(f"Account deletion error: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete account")

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

# =============================================================================
# PUSH NOTIFICATIONS ENDPOINTS
# =============================================================================

class NotificationRequest(BaseModel):
    title: str
    message: str
    url: Optional[str] = None
    image_url: Optional[str] = None
    segments: Optional[List[str]] = None
    user_ids: Optional[List[str]] = None
    tags: Optional[Dict[str, str]] = None

class SendNotificationRequest(BaseModel):
    type: str  # 'daily_special', 'limited_offer', 'favorite_update', etc.
    data: Dict[str, Any]  # Notification-specific data
    target_users: Optional[List[str]] = None

@api_router.post("/notifications/send")
async def send_notification(
    request: NotificationRequest,
    current_user: dict = Depends(get_current_user_optional)
):
    """Send a push notification"""
    try:
        onesignal_service = get_onesignal_service()
        
        payload = NotificationPayload(
            title=request.title,
            message=request.message,
            url=request.url,
            image_url=request.image_url,
            segments=request.segments,
            user_ids=request.user_ids,
            tags=request.tags
        )
        
        result = await onesignal_service.send_notification(payload)
        
        if result:
            return {
                "success": True,
                "notification_id": result.get("id"),
                "recipients": result.get("recipients", 0),
                "message": "Notification sent successfully"
            }
        else:
            return {
                "success": False,
                "message": "Failed to send notification"
            }
    
    except Exception as e:
        logging.error(f"Error sending notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/notifications/restaurant")
async def send_restaurant_notification(
    request: SendNotificationRequest,
    current_user: dict = Depends(get_current_user_optional)
):
    """Send restaurant-specific notifications (daily specials, offers, etc.)"""
    try:
        restaurant_service = get_restaurant_notification_service()
        result = None
        
        if request.type == "daily_special":
            result = await restaurant_service.send_daily_special_notification(
                request.data, 
                request.target_users
            )
        elif request.type == "limited_offer":
            result = await restaurant_service.send_limited_time_offer(
                request.data, 
                request.target_users
            )
        elif request.type == "favorite_update" and request.target_users:
            result = await restaurant_service.send_favorite_restaurant_update(
                request.data, 
                request.target_users
            )
        elif request.type == "daily_digest":
            result = await restaurant_service.send_daily_digest(request.data)
        elif request.type == "location_special":
            result = await restaurant_service.send_location_based_special(
                request.data, 
                request.data.get("location", "")
            )
        else:
            raise HTTPException(
                status_code=400, 
                detail=f"Unknown notification type: {request.type}"
            )
        
        if result:
            return {
                "success": True,
                "notification_id": result.get("id"),
                "recipients": result.get("recipients", 0),
                "message": f"{request.type} notification sent successfully"
            }
        else:
            return {
                "success": False,
                "message": "Failed to send notification"
            }
    
    except Exception as e:
        logging.error(f"Error sending restaurant notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/notifications/{notification_id}/status")
async def get_notification_status(
    notification_id: str,
    current_user: dict = Depends(get_current_user_optional)
):
    """Get notification delivery status and analytics"""
    try:
        onesignal_service = get_onesignal_service()
        status = await onesignal_service.get_notification_status(notification_id)
        
        if status:
            return {
                "success": True,
                "status": status
            }
        else:
            return {
                "success": False,
                "message": "Could not retrieve notification status"
            }
    
    except Exception as e:
        logging.error(f"Error getting notification status: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/notifications/test")
async def send_test_notification(
    current_user: dict = Depends(get_current_user_optional)
):
    """Send a test notification for debugging"""
    try:
        onesignal_service = get_onesignal_service()
        
        payload = NotificationPayload(
            title="🧪 Test Notification",
            message="This is a test notification from On-the-Cheap app!",
            url="/",
            segments=["All"]
        )
        
        result = await onesignal_service.send_notification(payload)
        
        if result:
            return {
                "success": True,
                "notification_id": result.get("id"),
                "recipients": result.get("recipients", 0),
                "message": "Test notification sent successfully"
            }
        else:
            return {
                "success": False,
                "message": "Failed to send test notification"
            }
    
    except Exception as e:
        logging.error(f"Error sending test notification: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# =============================================================================
# STATUS CHECK ENDPOINTS
# =============================================================================

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

# =================== PRODUCTION MONITORING & ADMIN ENDPOINTS ===================

@api_router.get("/admin/performance")
async def get_performance_stats():
    """Get comprehensive performance statistics (admin only)"""
    global cache_service, db_service
    
    try:
        stats = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {
                "cache": "available" if cache_service else "unavailable",
                "database": "available" if db_service else "unavailable"
            }
        }
        
        # Cache statistics
        if cache_service:
            stats["cache"] = cache_service.get_cache_stats()
            stats["api_quotas"] = cache_service.get_all_quota_status()
        
        # Database statistics
        if db_service:
            stats["database"] = await db_service.get_db_stats()
        
        return stats
        
    except Exception as e:
        logger.error(f"Error getting performance stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get performance statistics")

@api_router.get("/admin/health")
async def comprehensive_health_check():
    """Comprehensive system health check"""
    global cache_service, db_service
    
    health_status = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_status": "healthy",
        "services": {}
    }
    
    # Database health
    if db_service:
        db_health = await db_service.health_check()
        health_status["services"]["database"] = db_health
        if db_health["status"] != "healthy":
            health_status["overall_status"] = "degraded"
    else:
        health_status["services"]["database"] = {"status": "unavailable"}
        health_status["overall_status"] = "degraded"
    
    # Cache service health
    if cache_service:
        cache_stats = cache_service.get_cache_stats()
        health_status["services"]["cache"] = {
            "status": "healthy",
            "entries": cache_stats["cache_entries"],
            "hit_rate": cache_stats["hit_rate"],
            "memory_usage": cache_stats["memory_usage_estimate"]
        }
    else:
        health_status["services"]["cache"] = {"status": "unavailable"}
    
    # API quota health
    if cache_service:
        quotas = cache_service.get_all_quota_status()
        health_status["services"]["api_quotas"] = {}
        
        for service, quota in quotas.items():
            if quota and quota["usage_percent"] > 90:
                health_status["services"]["api_quotas"][service] = {
                    "status": "critical",
                    "usage_percent": quota["usage_percent"]
                }
                health_status["overall_status"] = "critical"
            elif quota and quota["usage_percent"] > 75:
                health_status["services"]["api_quotas"][service] = {
                    "status": "warning", 
                    "usage_percent": quota["usage_percent"]
                }
                if health_status["overall_status"] == "healthy":
                    health_status["overall_status"] = "warning"
            else:
                health_status["services"]["api_quotas"][service] = {
                    "status": "healthy",
                    "usage_percent": quota["usage_percent"] if quota else 0
                }
    
    return health_status

@api_router.post("/admin/cache/clear")
async def clear_cache(cache_type: Optional[str] = None):
    """Clear cache entries (admin only)"""
    global cache_service
    
    if not cache_service:
        raise HTTPException(status_code=503, detail="Cache service not available")
    
    try:
        if cache_type:
            # Clear specific cache type
            cache_type_enum = CacheType(cache_type)
            cleared_count = await cache_service.clear_type(cache_type_enum)
            return {
                "message": f"Cleared {cleared_count} entries of type {cache_type}",
                "cache_type": cache_type,
                "cleared_entries": cleared_count
            }
        else:
            # Clear all cache
            total_entries = len(cache_service.cache)
            cache_service.cache.clear()
            return {
                "message": f"Cleared all cache entries",
                "cleared_entries": total_entries
            }
            
    except ValueError:
        raise HTTPException(status_code=400, detail=f"Invalid cache type: {cache_type}")
    except Exception as e:
        logger.error(f"Error clearing cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to clear cache")

@api_router.post("/admin/database/optimize")
async def optimize_database():
    """Optimize database collections (admin only)"""
    global db_service
    
    if not db_service:
        raise HTTPException(status_code=503, detail="Database service not available")
    
    try:
        results = {}
        collections = ["restaurants", "users", "restaurant_owners"]
        
        for collection in collections:
            result = await db_service.optimize_collection(collection)
            results[collection] = result
        
        return {
            "message": "Database optimization completed",
            "results": results,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error optimizing database: {e}")
        raise HTTPException(status_code=500, detail="Failed to optimize database")

@api_router.get("/admin/quota-status")
async def get_quota_status():
    """Get current API quota status for all services"""
    global cache_service
    
    if not cache_service:
        return {"message": "Cache service not available", "quotas": {}}
    
    quotas = cache_service.get_all_quota_status()
    
    # Add recommendations based on usage
    for service, quota in quotas.items():
        if quota:
            usage_percent = quota["usage_percent"]
            if usage_percent > 90:
                quota["recommendation"] = "CRITICAL - Consider upgrading quota or implementing stronger throttling"
            elif usage_percent > 75:
                quota["recommendation"] = "WARNING - Monitor usage closely"
            elif usage_percent > 50:
                quota["recommendation"] = "MODERATE - Usage within normal range"
            else:
                quota["recommendation"] = "LOW - Usage well within limits"
    
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "quotas": quotas,
        "cache_performance": cache_service.get_cache_stats() if cache_service else None
    }

# =================== RESTAURANT OWNER ENDPOINTS ===================

@api_router.post("/owners/register", response_model=RestaurantOwner)
async def register_owner(owner_data: RestaurantOwnerCreate):
    """Register a new restaurant owner"""
    try:
        owner_service = get_owner_service(db)
        owner = await owner_service.create_owner(owner_data)
        return owner
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error registering owner: {e}")
        raise HTTPException(status_code=500, detail="Registration failed")

@api_router.post("/owners/login")
async def login_owner(login_data: OwnerLoginRequest):
    """Authenticate restaurant owner"""
    try:
        owner_service = get_owner_service(db)
        auth_result = await owner_service.authenticate_owner(login_data)
        return auth_result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error authenticating owner: {e}")
        raise HTTPException(status_code=500, detail="Authentication failed")

@api_router.post("/owners/claims", response_model=RestaurantClaimRequest)
async def submit_restaurant_claim(claim_data: RestaurantClaimRequest, current_user: dict = Depends(get_current_user)):
    """Submit a restaurant claim request"""
    try:
        if current_user.get("user_type") != "owner":
            raise HTTPException(status_code=403, detail="Only owners can submit claims")
        
        # Set owner_id from authenticated user
        claim_data.owner_id = current_user["id"]
        
        owner_service = get_owner_service(db)
        claim = await owner_service.claim_restaurant(claim_data)
        return claim
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error submitting claim: {e}")
        raise HTTPException(status_code=500, detail="Claim submission failed")

@api_router.post("/owners/specials", response_model=OwnerSpecial)
async def create_owner_special(special_data: OwnerSpecialCreate, current_user: dict = Depends(get_current_user)):
    """Create a new special (pending approval)"""
    try:
        if current_user.get("user_type") != "owner":
            raise HTTPException(status_code=403, detail="Only owners can create specials")
        
        owner_service = get_owner_service(db)
        special = await owner_service.create_special(special_data, current_user["id"])
        return special
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating special: {e}")
        raise HTTPException(status_code=500, detail="Special creation failed")

@api_router.get("/owners/dashboard", response_model=OwnerDashboardStats)
async def get_owner_dashboard(current_user: dict = Depends(get_current_user)):
    """Get owner dashboard statistics"""
    try:
        if current_user.get("user_type") != "owner":
            raise HTTPException(status_code=403, detail="Owner access required")
        
        owner_service = get_owner_service(db)
        stats = await owner_service.get_owner_dashboard(current_user["id"])
        return stats
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting dashboard: {e}")
        raise HTTPException(status_code=500, detail="Dashboard retrieval failed")

@api_router.get("/owners/specials")
async def get_owner_specials(restaurant_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get all specials for the authenticated owner"""
    try:
        if current_user.get("user_type") != "owner":
            raise HTTPException(status_code=403, detail="Owner access required")
        
        owner_service = get_owner_service(db)
        specials = await owner_service.get_owner_specials(current_user["id"], restaurant_id)
        return {"specials": specials}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting specials: {e}")
        raise HTTPException(status_code=500, detail="Specials retrieval failed")

@api_router.put("/owners/specials/{special_id}", response_model=OwnerSpecial)
async def update_owner_special(special_id: str, special_data: OwnerSpecialCreate, current_user: dict = Depends(get_current_user)):
    """Update an existing special"""
    try:
        if current_user.get("user_type") != "owner":
            raise HTTPException(status_code=403, detail="Owner access required")
        
        owner_service = get_owner_service(db)
        # Use exclude_unset=True to only include fields that were explicitly set
        # This allows preserving existing values for fields not provided in the update
        updated_special = await owner_service.update_special(
            special_id, 
            current_user["id"], 
            special_data.dict(exclude_unset=True)
        )
        return updated_special
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating special: {e}")
        raise HTTPException(status_code=500, detail="Special update failed")

@api_router.delete("/owners/specials/{special_id}")
async def delete_owner_special(special_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a special"""
    try:
        if current_user.get("user_type") != "owner":
            raise HTTPException(status_code=403, detail="Owner access required")
        
        owner_service = get_owner_service(db)
        success = await owner_service.delete_special(special_id, current_user["id"])
        
        if success:
            return {"message": "Special deleted successfully"}
        else:
            raise HTTPException(status_code=500, detail="Failed to delete special")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting special: {e}")
        raise HTTPException(status_code=500, detail="Special deletion failed")

@api_router.get("/owners/restaurants")
async def get_owner_restaurants(current_user: dict = Depends(get_current_user)):
    """Get all restaurants owned by the authenticated owner"""
    try:
        if current_user.get("user_type") != "owner":
            raise HTTPException(status_code=403, detail="Owner access required")
        
        owner_service = get_owner_service(db)
        restaurants = await owner_service.get_owner_restaurants(current_user["id"])
        return {"restaurants": restaurants}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting restaurants: {e}")
        raise HTTPException(status_code=500, detail="Restaurants retrieval failed")

class CreateRestaurantRequest(BaseModel):
    name: str
    address: str
    phone: Optional[str] = None
    website: Optional[str] = None
    cuisine_type: List[str] = []
    latitude: float
    longitude: float

@api_router.post("/owners/restaurants")
async def create_owner_restaurant(request: CreateRestaurantRequest, current_user: dict = Depends(get_current_user)):
    """Create a new restaurant and automatically claim it for the owner"""
    try:
        if current_user.get("user_type") != "owner":
            raise HTTPException(status_code=403, detail="Owner access required")
        
        # Create the restaurant document
        restaurant_id = str(uuid.uuid4())
        restaurant = {
            "id": restaurant_id,
            "name": request.name,
            "address": request.address,
            "location": {
                "latitude": request.latitude,
                "longitude": request.longitude
            },
            "phone": request.phone,
            "website": request.website,
            "cuisine_type": request.cuisine_type if request.cuisine_type else ["Restaurant"],
            "rating": None,
            "price_level": 2,
            "specials": [],
            "is_verified": False,
            "created_at": datetime.now(timezone.utc).isoformat(),
            "source": "owner_managed",
            "owner_id": current_user["id"],
            "city": "",  # Will be extracted from address
            "state": "",
            "timezone": "America/Chicago"  # Default to Central Time
        }
        
        # Try to extract city and state from address
        address_parts = request.address.split(',')
        if len(address_parts) >= 2:
            restaurant["city"] = address_parts[-2].strip() if len(address_parts) >= 2 else ""
            state_zip = address_parts[-1].strip().split()
            restaurant["state"] = state_zip[0] if state_zip else ""
        
        # Insert the restaurant
        await db.restaurants.insert_one(restaurant)
        
        # Link it to the owner
        owner_service = get_owner_service(db)
        await owner_service.link_restaurant_to_owner(current_user["id"], restaurant_id)
        
        logger.info(f"Owner {current_user['id']} created and claimed restaurant: {request.name}")
        
        return {
            "message": f"Restaurant '{request.name}' created and claimed successfully!",
            "restaurant": serialize_doc(restaurant)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating restaurant: {e}")
        raise HTTPException(status_code=500, detail="Failed to create restaurant")

@api_router.post("/owners/restaurants/{restaurant_id}/link")
async def link_restaurant_to_owner(restaurant_id: str, current_user: dict = Depends(get_current_user)):
    """Link a restaurant to the authenticated owner"""
    try:
        if current_user.get("user_type") != "owner":
            raise HTTPException(status_code=403, detail="Owner access required")
        
        # Verify restaurant exists
        restaurant = await db.restaurants.find_one({"id": restaurant_id})
        if not restaurant:
            raise HTTPException(status_code=404, detail="Restaurant not found")
        
        owner_service = get_owner_service(db)
        success = await owner_service.link_restaurant_to_owner(current_user["id"], restaurant_id)
        
        if success:
            return {"message": "Restaurant linked successfully", "restaurant_id": restaurant_id}
        else:
            raise HTTPException(status_code=500, detail="Failed to link restaurant")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error linking restaurant: {e}")
        raise HTTPException(status_code=500, detail="Restaurant linking failed")

# =================== OWNER PROFILE MANAGEMENT ===================

class TransferRestaurantRequest(BaseModel):
    new_owner_email: str

@api_router.post("/owners/restaurants/{restaurant_id}/transfer")
async def transfer_restaurant(restaurant_id: str, request: TransferRestaurantRequest, current_user: dict = Depends(get_current_user)):
    """Transfer restaurant management to another owner"""
    try:
        if current_user.get("user_type") != "owner":
            raise HTTPException(status_code=403, detail="Owner access required")
        
        # Verify current owner owns this restaurant
        owner_service = get_owner_service(db)
        owner_restaurants = await owner_service.get_owner_restaurants(current_user["id"])
        restaurant_ids = [r.get('id') for r in owner_restaurants]
        
        if restaurant_id not in restaurant_ids:
            raise HTTPException(status_code=403, detail="You don't own this restaurant")
        
        # Find the new owner by email
        new_owner = await db.restaurant_owners.find_one({"email": request.new_owner_email.lower()})
        if not new_owner:
            raise HTTPException(status_code=404, detail=f"No owner account found with email: {request.new_owner_email}")
        
        new_owner = prepare_from_mongo(new_owner)
        
        if new_owner['id'] == current_user['id']:
            raise HTTPException(status_code=400, detail="Cannot transfer to yourself")
        
        # Get restaurant details for the response
        restaurant = await db.restaurants.find_one({"id": restaurant_id})
        restaurant_name = restaurant.get('name', 'Restaurant') if restaurant else 'Restaurant'
        
        # Remove restaurant from current owner's linked restaurants
        await db.restaurant_owners.update_one(
            {"id": current_user["id"]},
            {"$pull": {"restaurant_ids": restaurant_id}}
        )
        
        # Add restaurant to new owner's linked restaurants
        await db.restaurant_owners.update_one(
            {"id": new_owner['id']},
            {"$addToSet": {"restaurant_ids": restaurant_id}}
        )
        
        # Update restaurant's owner_id
        await db.restaurants.update_one(
            {"id": restaurant_id},
            {"$set": {"owner_id": new_owner['id']}}
        )
        
        logger.info(f"Restaurant {restaurant_id} transferred from {current_user['email']} to {request.new_owner_email}")
        
        return {
            "message": f"'{restaurant_name}' has been transferred to {request.new_owner_email}",
            "restaurant_id": restaurant_id,
            "new_owner_email": request.new_owner_email
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error transferring restaurant: {e}")
        raise HTTPException(status_code=500, detail="Failed to transfer restaurant")

class DeleteOwnerProfileRequest(BaseModel):
    confirm_email: str
    password: str

@api_router.delete("/owners/profile")
async def delete_owner_profile(request: DeleteOwnerProfileRequest, current_user: dict = Depends(get_current_user)):
    """Delete owner profile and unlink all restaurants"""
    try:
        if current_user.get("user_type") != "owner":
            raise HTTPException(status_code=403, detail="Owner access required")
        
        # Verify email matches
        if request.confirm_email.lower() != current_user['email'].lower():
            raise HTTPException(status_code=400, detail="Email confirmation does not match your account email")
        
        # Verify password
        owner = await db.restaurant_owners.find_one({"id": current_user['id']})
        if not owner:
            raise HTTPException(status_code=404, detail="Owner not found")
        
        owner = prepare_from_mongo(owner)
        if not verify_password(request.password, owner['password_hash']):
            raise HTTPException(status_code=401, detail="Invalid password")
        
        # Get owner's restaurants before deletion
        owner_service = get_owner_service(db)
        owner_restaurants = await owner_service.get_owner_restaurants(current_user["id"])
        
        # Unlink all restaurants (set them as unclaimed but keep them in database)
        for restaurant in owner_restaurants:
            await db.restaurants.update_one(
                {"id": restaurant['id']},
                {
                    "$set": {"owner_id": None, "source": "unclaimed"},
                    "$unset": {"owner_email": ""}
                }
            )
        
        # Delete owner's specials
        await db.owner_specials.delete_many({"owner_id": current_user['id']})
        
        # Delete any pending claims
        await db.owner_claims.delete_many({"owner_id": current_user['id']})
        
        # Delete the owner profile
        await db.restaurant_owners.delete_one({"id": current_user['id']})
        
        logger.info(f"Owner profile deleted: {current_user['email']} - {len(owner_restaurants)} restaurants unlinked")
        
        return {
            "message": "Your owner profile has been deleted successfully",
            "restaurants_unlinked": len(owner_restaurants)
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting owner profile: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete profile")

# =================== ADMIN OWNER ENDPOINTS ===================

@api_router.get("/admin/owners/claims")
async def get_pending_claims():
    """Get all pending restaurant claims (admin only)"""
    try:
        admin_service = get_owner_admin_service(db)
        claims = await admin_service.get_pending_claims()
        return {"claims": claims}
    except Exception as e:
        logger.error(f"Error getting pending claims: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pending claims")

@api_router.post("/admin/owners/claims/{claim_id}/approve")
async def approve_claim(claim_id: str, admin_notes: Optional[str] = None):
    """Approve a restaurant claim (admin only)"""
    try:
        admin_service = get_owner_admin_service(db)
        success = await admin_service.approve_claim(claim_id, admin_notes)
        return {"message": "Claim approved successfully", "success": success}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving claim: {e}")
        raise HTTPException(status_code=500, detail="Claim approval failed")

@api_router.get("/admin/owners/specials")
async def get_pending_specials():
    """Get all pending specials (admin only)"""
    try:
        admin_service = get_owner_admin_service(db)
        specials = await admin_service.get_pending_specials()
        return {"specials": specials}
    except Exception as e:
        logger.error(f"Error getting pending specials: {e}")
        raise HTTPException(status_code=500, detail="Failed to get pending specials")

@api_router.post("/admin/owners/specials/{special_id}/approve")
async def approve_special(special_id: str, admin_notes: Optional[str] = None):
    """Approve a special (admin only)"""
    try:
        admin_service = get_owner_admin_service(db)
        success = await admin_service.approve_special(special_id, admin_notes)
        return {"message": "Special approved successfully", "success": success}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error approving special: {e}")
        raise HTTPException(status_code=500, detail="Special approval failed")

# =================== ADVANCED PRODUCTION MONITORING ENDPOINTS ===================

@api_router.get("/admin/analytics/api")
async def get_api_analytics(hours: int = Query(24, ge=1, le=168)):
    """Get comprehensive API usage analytics"""
    global monitoring_service
    
    if not monitoring_service:
        raise HTTPException(status_code=503, detail="Monitoring service not available")
    
    try:
        analytics = await monitoring_service.get_api_analytics(hours)
        return analytics
    except Exception as e:
        logger.error(f"Error getting API analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get API analytics")

@api_router.get("/admin/analytics/system")
async def get_system_analytics(hours: int = Query(24, ge=1, le=168)):
    """Get comprehensive system performance analytics"""
    global monitoring_service
    
    if not monitoring_service:
        raise HTTPException(status_code=503, detail="Monitoring service not available")
    
    try:
        analytics = await monitoring_service.get_system_analytics(hours)
        return analytics
    except Exception as e:
        logger.error(f"Error getting system analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get system analytics")

@api_router.get("/admin/analytics/business")
async def get_business_analytics(metric_name: Optional[str] = None, hours: int = Query(24, ge=1, le=168)):
    """Get business metrics analytics"""
    global monitoring_service
    
    if not monitoring_service:
        raise HTTPException(status_code=503, detail="Monitoring service not available")
    
    try:
        analytics = await monitoring_service.get_business_analytics(metric_name, hours)
        return analytics
    except Exception as e:
        logger.error(f"Error getting business analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get business analytics")

@api_router.get("/admin/analytics/errors")
async def get_error_analytics(hours: int = Query(24, ge=1, le=168)):
    """Get comprehensive error analytics"""
    global monitoring_service
    
    if not monitoring_service:
        raise HTTPException(status_code=503, detail="Monitoring service not available")
    
    try:
        analytics = await monitoring_service.get_error_analytics(hours)
        return analytics
    except Exception as e:
        logger.error(f"Error getting error analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get error analytics")

@api_router.get("/admin/redis/stats")
async def get_redis_stats():
    """Get Redis performance statistics"""
    global redis_service
    
    if not redis_service:
        return {"message": "Redis service not available", "status": "disabled"}
    
    try:
        stats = await redis_service.get_performance_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting Redis stats: {e}")
        raise HTTPException(status_code=500, detail="Failed to get Redis statistics")

@api_router.post("/admin/redis/invalidate")
async def invalidate_redis_cache(pattern: str = Query(..., description="Cache key pattern to invalidate")):
    """Invalidate Redis cache by pattern"""
    global redis_service
    
    if not redis_service:
        raise HTTPException(status_code=503, detail="Redis service not available")
    
    try:
        invalidated_count = await redis_service.invalidate_pattern(pattern)
        return {
            "message": f"Invalidated {invalidated_count} cache entries",
            "pattern": pattern,
            "invalidated_count": invalidated_count
        }
    except Exception as e:
        logger.error(f"Error invalidating Redis cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to invalidate cache")

@api_router.post("/admin/cache/warm")
async def warm_cache():
    """Warm up cache with frequently accessed data"""
    global redis_service, cache_service
    
    try:
        # Prepare warm data for frequently accessed endpoints
        warm_data = {
            "special_types": await get_special_types(),
            # Add more frequently accessed data as needed
        }
        
        warmed_count = 0
        if redis_service:
            warmed_count += await redis_service.cache_warming(warm_data)
        
        return {
            "message": f"Cache warming completed",
            "warmed_entries": warmed_count,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    except Exception as e:
        logger.error(f"Error warming cache: {e}")
        raise HTTPException(status_code=500, detail="Failed to warm cache")

# =================== PRODUCTION HEALTH & STATUS ENDPOINTS ===================

@api_router.get("/admin/status/comprehensive")
async def comprehensive_status():
    """Get comprehensive production system status"""
    global cache_service, db_service, redis_service, monitoring_service
    
    status = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_status": "healthy",
        "services": {}
    }
    
    # Cache service status
    if cache_service:
        cache_stats = cache_service.get_cache_stats()
        status["services"]["cache"] = {
            "status": "healthy",
            "hit_rate": cache_stats["hit_rate"],
            "entries": cache_stats["cache_entries"]
        }
    
    # Database service status
    if db_service:
        db_health = await db_service.health_check()
        status["services"]["database"] = db_health
        if db_health["status"] != "healthy":
            status["overall_status"] = "degraded"
    
    # Redis service status
    if redis_service:
        redis_stats = await redis_service.get_performance_stats()
        status["services"]["redis"] = {
            "status": redis_stats["connection_status"],
            "hit_rate": redis_stats["hit_rate"],
            "avg_response_time": redis_stats["avg_response_time_ms"]
        }
        if redis_stats["connection_status"] != "connected":
            status["overall_status"] = "degraded"
    else:
        status["services"]["redis"] = {"status": "disabled"}
    
    # Monitoring service status
    if monitoring_service:
        status["services"]["monitoring"] = {
            "status": "active" if monitoring_service.monitoring_enabled else "inactive",
            "api_calls_tracked": len(monitoring_service.api_metrics),
            "system_metrics_tracked": len(monitoring_service.system_metrics)
        }
    
    return status

# Enhanced health endpoint with monitoring integration
@api_router.get("/admin/health/enhanced")
async def enhanced_health_check():
    """Enhanced health check with monitoring integration"""
    # Record this API call for monitoring
    start_time = datetime.now()
    
    try:
        health_data = await comprehensive_health_check()
        
        # Record monitoring data
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        if monitoring_service:
            await monitoring_service.record_api_call(
                endpoint="/admin/health/enhanced",
                method="GET",
                status_code=200,
                response_time=response_time
            )
        
        return health_data
        
    except Exception as e:
        response_time = (datetime.now() - start_time).total_seconds() * 1000
        if monitoring_service:
            await monitoring_service.record_api_call(
                endpoint="/admin/health/enhanced",
                method="GET",
                status_code=500,
                response_time=response_time,
                error_message=str(e)
            )
        raise

# =================== DIGITAL COUPON ENDPOINTS ===================

@api_router.post("/owners/coupons", response_model=Coupon)
async def create_coupon(coupon_data: CouponCreate, restaurant_id: str, current_user: dict = Depends(get_current_user)):
    """Create a new digital coupon for a restaurant"""
    try:
        if current_user.get("user_type") != "owner":
            raise HTTPException(status_code=403, detail="Only owners can create coupons")
        
        coupon_service = get_coupon_service(db)
        coupon = await coupon_service.create_coupon(coupon_data, current_user["id"], restaurant_id)
        return coupon
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating coupon: {e}")
        raise HTTPException(status_code=500, detail="Coupon creation failed")

@api_router.get("/owners/coupons")
async def get_owner_coupons(restaurant_id: Optional[str] = None, current_user: dict = Depends(get_current_user)):
    """Get all coupons for the authenticated owner"""
    try:
        if current_user.get("user_type") != "owner":
            raise HTTPException(status_code=403, detail="Owner access required")
        
        coupon_service = get_coupon_service(db)
        # Use 'id' instead of 'user_id' to match the token payload
        owner_id = current_user.get("id") or current_user.get("user_id")
        coupons = await coupon_service.get_owner_coupons(owner_id, restaurant_id)
        return {"coupons": coupons}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting owner coupons: {e}")
        raise HTTPException(status_code=500, detail="Failed to get coupons")

@api_router.get("/coupons/near")
async def get_coupons_near_location(
    latitude: float = Query(..., description="Latitude"),
    longitude: float = Query(..., description="Longitude"), 
    radius: float = Query(default=10, description="Search radius in miles")
):
    """Get active coupons near a location"""
    try:
        coupon_service = get_coupon_service(db)
        coupons = await coupon_service.get_active_coupons_by_location(latitude, longitude, radius)
        return {"coupons": coupons, "total": len(coupons)}
    except Exception as e:
        logger.error(f"Error getting coupons near location: {e}")
        raise HTTPException(status_code=500, detail="Failed to get nearby coupons")

@api_router.post("/coupons/{coupon_id}/redeem")
async def redeem_coupon(
    coupon_id: str, 
    order_total: Optional[float] = None,
    current_user: Optional[dict] = Depends(get_current_user_optional)
):
    """Redeem a coupon"""
    try:
        coupon_service = get_coupon_service(db)
        customer_id = current_user.get("user_id") if current_user else None
        
        result = await coupon_service.redeem_coupon(
            coupon_id=coupon_id,
            customer_id=customer_id,
            order_total=order_total
        )
        
        # Record business metric for monitoring
        if monitoring_service:
            await monitoring_service.record_business_metric(
                "coupon_redemption", 
                result["discount_applied"],
                {"coupon_id": coupon_id, "customer_type": "registered" if customer_id else "guest"}
            )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error redeeming coupon: {e}")
        raise HTTPException(status_code=500, detail="Coupon redemption failed")

@api_router.get("/owners/coupons/{coupon_id}/analytics", response_model=CouponAnalytics)
async def get_coupon_analytics(
    coupon_id: str, 
    days: int = Query(default=30, ge=1, le=365),
    current_user: dict = Depends(get_current_user)
):
    """Get detailed analytics for a coupon"""
    try:
        if current_user.get("user_type") != "owner":
            raise HTTPException(status_code=403, detail="Owner access required")
        
        coupon_service = get_coupon_service(db)
        analytics = await coupon_service.get_coupon_analytics(coupon_id, days)
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting coupon analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get coupon analytics")

@api_router.get("/coupons/{coupon_id}/analytics")
async def get_coupon_analytics_public(coupon_id: str, days: int = Query(default=30), current_user: dict = Depends(get_current_user)):
    """Get analytics for a coupon"""
    try:
        if current_user.get("user_type") != "owner":
            raise HTTPException(status_code=403, detail="Owner access required")
        
        coupon_service = get_coupon_service(db)
        analytics = await coupon_service.get_coupon_analytics(coupon_id, days)
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting coupon analytics: {e}")
        raise HTTPException(status_code=500, detail="Failed to get analytics")

@api_router.get("/coupons/{coupon_id}")
async def get_coupon_detail(coupon_id: str):
    """Get detailed information about a specific coupon"""
    try:
        coupon_service = get_coupon_service(db)
        coupon_doc = await db.coupons.find_one({"id": coupon_id})
        
        if not coupon_doc:
            raise HTTPException(status_code=404, detail="Coupon not found")
        
        # Get restaurant info
        restaurant = await db.restaurants.find_one({"id": coupon_doc["restaurant_id"]})
        if restaurant:
            coupon_doc["restaurant"] = {
                "name": restaurant["name"],
                "address": restaurant["address"],
                "cuisine_type": restaurant.get("cuisine_type", []),
                "photos": restaurant.get("photos", [])
            }
        
        return Coupon(**coupon_doc)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting coupon detail: {e}")
        raise HTTPException(status_code=500, detail="Failed to get coupon")

@api_router.patch("/coupons/{coupon_id}/status")
async def update_coupon_status(coupon_id: str, status: str, current_user: dict = Depends(get_current_user)):
    """Update coupon status (active, paused, expired)"""
    try:
        if current_user.get("user_type") != "owner":
            raise HTTPException(status_code=403, detail="Owner access required")
        
        # Verify ownership
        coupon = await db.coupons.find_one({"id": coupon_id})
        if not coupon:
            raise HTTPException(status_code=404, detail="Coupon not found")
        
        if coupon["owner_id"] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorized to modify this coupon")
        
        # Update status
        await db.coupons.update_one(
            {"id": coupon_id},
            {"$set": {"status": status, "updated_at": datetime.now(timezone.utc).isoformat()}}
        )
        
        return {"message": f"Coupon status updated to {status}"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating coupon status: {e}")
        raise HTTPException(status_code=500, detail="Failed to update coupon status")

@api_router.delete("/coupons/{coupon_id}")
async def delete_coupon(coupon_id: str, current_user: dict = Depends(get_current_user)):
    """Delete a coupon"""
    try:
        if current_user.get("user_type") != "owner":
            raise HTTPException(status_code=403, detail="Owner access required")
        
        # Verify ownership
        coupon = await db.coupons.find_one({"id": coupon_id})
        if not coupon:
            raise HTTPException(status_code=404, detail="Coupon not found")
        
        if coupon["owner_id"] != current_user["user_id"]:
            raise HTTPException(status_code=403, detail="Not authorized to delete this coupon")
        
        # Delete coupon
        await db.coupons.delete_one({"id": coupon_id})
        
        return {"message": "Coupon deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting coupon: {e}")
        raise HTTPException(status_code=500, detail="Failed to delete coupon")

# Customer coupon endpoints
@api_router.post("/users/coupons/{coupon_id}/save")
async def save_coupon(coupon_id: str, current_user: dict = Depends(get_current_regular_user)):
    """Save a coupon to user's saved coupons"""
    try:
        # Verify coupon exists
        coupon = await db.coupons.find_one({"id": coupon_id})
        if not coupon:
            raise HTTPException(status_code=404, detail="Coupon not found")
        
        # Add to saved coupons
        user = await db.users.find_one({"id": current_user["id"]})
        saved_coupons = user.get("saved_coupon_ids", [])
        
        if coupon_id in saved_coupons:
            return {"message": "Coupon already saved"}
        
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$push": {"saved_coupon_ids": coupon_id}}
        )
        
        # Increment coupon saves count
        await db.coupons.update_one(
            {"id": coupon_id},
            {"$inc": {"saves": 1}}
        )
        
        return {"message": "Coupon saved successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving coupon: {e}")
        raise HTTPException(status_code=500, detail="Failed to save coupon")

@api_router.delete("/users/coupons/{coupon_id}/save")
async def unsave_coupon(coupon_id: str, current_user: dict = Depends(get_current_regular_user)):
    """Remove a coupon from user's saved coupons"""
    try:
        await db.users.update_one(
            {"id": current_user["id"]},
            {"$pull": {"saved_coupon_ids": coupon_id}}
        )
        
        # Decrement coupon saves count
        await db.coupons.update_one(
            {"id": coupon_id},
            {"$inc": {"saves": -1}}
        )
        
        return {"message": "Coupon removed from saved"}
    except Exception as e:
        logger.error(f"Error unsaving coupon: {e}")
        raise HTTPException(status_code=500, detail="Failed to unsave coupon")

@api_router.get("/users/coupons/saved")
async def get_saved_coupons(current_user: dict = Depends(get_current_regular_user)):
    """Get user's saved coupons"""
    try:
        user = await db.users.find_one({"id": current_user["id"]})
        saved_coupon_ids = user.get("saved_coupon_ids", [])
        
        if not saved_coupon_ids:
            return {"coupons": [], "total": 0}
        
        # Get coupons with restaurant info
        coupons = await db.coupons.find({"id": {"$in": saved_coupon_ids}}).to_list(length=None)
        
        enriched_coupons = []
        for coupon in coupons:
            restaurant = await db.restaurants.find_one({"id": coupon["restaurant_id"]})
            if restaurant:
                coupon["restaurant"] = {
                    "name": restaurant["name"],
                    "address": restaurant["address"],
                    "cuisine_type": restaurant.get("cuisine_type", []),
                    "photos": restaurant.get("photos", [])
                }
            enriched_coupons.append(coupon)
        
        return {"coupons": enriched_coupons, "total": len(enriched_coupons)}
    except Exception as e:
        logger.error(f"Error getting saved coupons: {e}")
        raise HTTPException(status_code=500, detail="Failed to get saved coupons")

@api_router.post("/coupons/{coupon_id}/view")
async def track_coupon_view(coupon_id: str):
    """Track when a coupon is viewed"""
    try:
        await db.coupons.update_one(
            {"id": coupon_id},
            {"$inc": {"views": 1}}
        )
        return {"message": "View tracked"}
    except Exception as e:
        logger.error(f"Error tracking coupon view: {e}")
        return {"message": "View tracking failed"}

@api_router.post("/coupons/{coupon_id}/save")
async def track_coupon_save(coupon_id: str, current_user: Optional[dict] = Depends(get_current_user_optional)):
    """Track when a coupon is saved by a customer"""
    try:
        # Update save count
        result = await db.coupons.update_one(
            {"id": coupon_id},
            {"$inc": {"saves": 1}}
        )
        
        if result.matched_count == 0:
            raise HTTPException(status_code=404, detail="Coupon not found")
        
        # TODO: Add to user's saved coupons if user is logged in
        
        return {"success": True, "message": "Save tracked"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error tracking coupon save: {e}")
        raise HTTPException(status_code=500, detail="Failed to track save")

# Helper function for optional authentication
async def get_current_user_optional(authorization: Optional[HTTPAuthorizationCredentials] = Depends(optional_security)):
    """Get current user if authenticated, otherwise return None"""
    try:
        if not authorization:
            return None
        return await get_current_user_from_token(authorization.credentials)
    except:
        return None

# ====================================================================================
# SUBSCRIPTION MANAGEMENT ENDPOINTS
# ====================================================================================

from subscription_service import SubscriptionService, SubscriptionTier, FeatureLimits

# Initialize subscription service
subscription_service = SubscriptionService(
    db_client=db,
    stripe_api_key=os.environ.get('STRIPE_SECRET_KEY', 'sk_test_emergent'),
    webhook_url=f"{os.environ.get('FRONTEND_URL', 'http://localhost:8001')}/api/webhook/stripe"
)

@api_router.get("/owners/subscription/status")
async def get_subscription_status(
    current_user: dict = Depends(get_current_user)
):
    """Get owner's current subscription status and analytics"""
    try:
        if current_user.get("user_type") != "owner":
            raise HTTPException(status_code=403, detail="Owner access required")
            
        analytics = await subscription_service.get_subscription_analytics(current_user["id"])
        return analytics
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting subscription status: {e}")
        raise HTTPException(status_code=500, detail="Failed to get subscription status")

class SubscriptionCheckoutRequest(BaseModel):
    tier: str
    billing: str = "monthly"  # "monthly" or "annual"

# Stripe Price IDs - configure these in your Stripe dashboard
STRIPE_PRICE_IDS = {
    "pro_monthly": os.environ.get("STRIPE_PRO_MONTHLY_PRICE_ID", ""),
    "pro_annual": os.environ.get("STRIPE_PRO_ANNUAL_PRICE_ID", ""),
    "enterprise_monthly": os.environ.get("STRIPE_ENTERPRISE_MONTHLY_PRICE_ID", ""),
    "enterprise_annual": os.environ.get("STRIPE_ENTERPRISE_ANNUAL_PRICE_ID", "")
}

@api_router.post("/owners/subscription/checkout")
async def create_subscription_checkout(
    request: SubscriptionCheckoutRequest,
    current_user: dict = Depends(get_current_user)
):
    """
    Create Stripe checkout session for subscription
    
    Args:
        tier: Subscription tier (pro or enterprise)
        billing: Billing period (monthly or annual)
    """
    try:
        if current_user.get("user_type") != "owner":
            raise HTTPException(status_code=403, detail="Owner access required")
        
        tier = request.tier.lower()
        billing = request.billing.lower()
        
        if tier not in ["pro", "enterprise"]:
            raise HTTPException(status_code=400, detail=f"Invalid subscription tier: {tier}")
        
        if billing not in ["monthly", "annual"]:
            raise HTTPException(status_code=400, detail=f"Invalid billing period: {billing}")
        
        price_key = f"{tier}_{billing}"
        price_id = STRIPE_PRICE_IDS.get(price_key)
        
        if not price_id:
            raise HTTPException(
                status_code=500, 
                detail=f"Stripe price not configured for {tier} {billing}. Please contact support."
            )
        
        origin_url = os.environ.get("FRONTEND_URL", "https://www.onthecheapapp.com")
        success_url = f"{origin_url}/owner/billing?session_id={{CHECKOUT_SESSION_ID}}"
        cancel_url = f"{origin_url}/owner/pricing"
        
        result = await subscription_service.create_subscription_checkout(
            owner_id=current_user["id"],
            price_id=price_id,
            success_url=success_url,
            cancel_url=cancel_url,
            metadata={"owner_email": current_user["email"], "tier": tier, "billing": billing}
        )
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating checkout: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/owners/subscription/checkout/{session_id}/status")
async def check_subscription_checkout_status(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    """Check the status of a checkout session"""
    try:
        if current_user.get("user_type") != "owner":
            raise HTTPException(status_code=403, detail="Owner access required")
            
        status = await subscription_service.check_checkout_status(session_id)
        
        # If payment succeeded, handle subscription activation
        if status.payment_status == "paid":
            # Extract metadata to determine tier and billing period
            metadata = status.metadata
            
            # Update subscription based on Stripe data
            # This is a simplified version - webhook will handle the full update
            logger.info(f"Checkout session {session_id} completed for owner {current_user['id']}")
        
        return {
            "status": status.status,
            "payment_status": status.payment_status,
            "amount_total": status.amount_total / 100,  # Convert from cents
            "currency": status.currency
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking checkout status: {e}")
        raise HTTPException(status_code=500, detail="Failed to check checkout status")

@api_router.post("/owners/subscription/cancel")
async def cancel_subscription(
    immediate: bool = False,
    current_user: dict = Depends(get_current_user)
):
    """Cancel owner's subscription"""
    try:
        if current_user.get("user_type") != "owner":
            raise HTTPException(status_code=403, detail="Owner access required")
            
        result = await subscription_service.cancel_subscription(
            owner_id=current_user["id"],
            immediate=immediate
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error canceling subscription: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/owners/features/check/{feature}")
async def check_feature_access(
    feature: str,
    current_user: dict = Depends(get_current_user)
):
    """Check if owner has access to a specific feature"""
    try:
        if current_user.get("user_type") != "owner":
            raise HTTPException(status_code=403, detail="Owner access required")
            
        has_access = await subscription_service.check_feature_access(current_user["id"], feature)
        tier = await subscription_service.get_owner_tier(current_user["id"])
        
        return {
            "has_access": has_access,
            "current_tier": tier,
            "feature": feature
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error checking feature access: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.post("/webhook/stripe")
async def stripe_webhook(request: Request):
    """Handle Stripe webhook events"""
    try:
        body = await request.body()
        signature = request.headers.get("Stripe-Signature")
        
        # Handle webhook using emergentintegrations
        webhook_response = await subscription_service.stripe_checkout.handle_webhook(
            body,
            signature
        )
        
        event_type = webhook_response.event_type
        session_id = webhook_response.session_id
        payment_status = webhook_response.payment_status
        metadata = webhook_response.metadata
        
        logger.info(f"Stripe webhook received: {event_type}, session: {session_id}, status: {payment_status}")
        
        # Handle subscription events
        if event_type == "checkout.session.completed" and payment_status == "paid":
            # Extract subscription info from metadata or Stripe
            owner_id = metadata.get("owner_id")
            if owner_id:
                # For now, mark as successful - full implementation would extract tier info
                logger.info(f"Subscription payment successful for owner {owner_id}")
                
                # Update transaction status
                await subscription_service.transactions.update_one(
                    {"transaction_id": session_id},
                    {
                        "$set": {
                            "status": "succeeded",
                            "payment_status": payment_status,
                            "updated_at": datetime.now(timezone.utc)
                        }
                    }
                )
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Stripe webhook error: {e}")
        raise HTTPException(status_code=400, detail=str(e))

# ===========================================
# Export Files Download Endpoints
# ===========================================

EXPORTS_DIR = Path(__file__).parent.parent / "exports"

@api_router.get("/exports/list")
async def list_export_files():
    """List all available export files"""
    try:
        if not EXPORTS_DIR.exists():
            return {"files": []}
        
        files = []
        for f in EXPORTS_DIR.iterdir():
            if f.is_file() and f.suffix in ['.csv', '.html', '.txt']:
                files.append({
                    "name": f.name,
                    "size_kb": round(f.stat().st_size / 1024, 1),
                    "download_url": f"/api/exports/download/{f.name}"
                })
        
        return {"files": sorted(files, key=lambda x: x["name"])}
    except Exception as e:
        logger.error(f"Error listing export files: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@api_router.get("/exports/download/{filename}")
async def download_export_file(filename: str):
    """Download a specific export file"""
    try:
        # Security: only allow specific file extensions
        allowed_extensions = ['.csv', '.html', '.txt']
        file_path = EXPORTS_DIR / filename
        
        # Prevent directory traversal
        if ".." in filename or "/" in filename or "\\" in filename:
            raise HTTPException(status_code=400, detail="Invalid filename")
        
        if not any(filename.endswith(ext) for ext in allowed_extensions):
            raise HTTPException(status_code=400, detail="File type not allowed")
        
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type="application/octet-stream"
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading export file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

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