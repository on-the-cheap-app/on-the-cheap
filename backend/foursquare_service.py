"""
Foursquare API Integration Service
Provides restaurant data as a fallback source for On-the-Cheap app
"""

import httpx
import asyncio
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from pydantic import BaseModel
import os

logger = logging.getLogger(__name__)

class VenueSearchParams(BaseModel):
    ll: Optional[str] = None  # latitude,longitude
    near: Optional[str] = None  # address or location name
    query: Optional[str] = None  # search term
    categories: Optional[str] = None  # category IDs for restaurants
    radius: Optional[int] = None  # search radius in meters
    limit: Optional[int] = 50  # max results (default 50)

class FoursquareVenue(BaseModel):
    id: str
    name: str
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    categories: List[str] = []
    rating: Optional[float] = None
    price: Optional[int] = None
    photos: List[str] = []
    source: str = "foursquare"

class FoursquareAPIError(Exception):
    """Base exception for Foursquare API errors"""
    def __init__(self, message: str, status_code: Optional[int] = None):
        super().__init__(message)
        self.status_code = status_code

class RateLimitError(FoursquareAPIError):
    """Raised when API rate limits are exceeded"""
    def __init__(self, message: str, retry_after: Optional[int] = None):
        super().__init__(message, 429)
        self.retry_after = retry_after

class VenueNotFoundError(FoursquareAPIError):
    """Raised when requested venue is not found"""
    def __init__(self, message: str = "Venue not found"):
        super().__init__(message, 404)

class FoursquareService:
    def __init__(self):
        self.client_id = os.environ.get('FOURSQUARE_CLIENT_ID')
        self.client_secret = os.environ.get('FOURSQUARE_CLIENT_SECRET')
        
        if not self.client_id or not self.client_secret:
            raise ValueError("Foursquare credentials not found in environment variables")
        
        self.base_url = "https://api.foursquare.com/v3"
        self.headers = {
            "Authorization": f"Bearer {self.client_secret}",
            "Accept": "application/json"
        }
        
        # Cache for API responses (simple in-memory cache)
        self.cache = {}
        self.cache_ttl = 3600  # 1 hour cache
    
    def _get_cache_key(self, endpoint: str, params: Dict) -> str:
        """Generate cache key for API requests"""
        import hashlib
        key_data = f"{endpoint}_{str(sorted(params.items()))}"
        return hashlib.md5(key_data.encode()).hexdigest()
    
    def _is_cache_valid(self, cache_entry: Dict) -> bool:
        """Check if cache entry is still valid"""
        if not cache_entry:
            return False
        cached_time = cache_entry.get('cached_at')
        if not cached_time:
            return False
        return (datetime.now() - cached_time).seconds < self.cache_ttl
    
    def _cache_response(self, key: str, data: Any) -> None:
        """Cache API response"""
        self.cache[key] = {
            'data': data,
            'cached_at': datetime.now()
        }
    
    def _get_cached_data(self, key: str) -> Optional[Any]:
        """Retrieve cached data if valid"""
        cache_entry = self.cache.get(key)
        if self._is_cache_valid(cache_entry):
            logger.info(f"Cache hit for key: {key[:10]}...")
            return cache_entry['data']
        return None
    
    async def _make_request(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make HTTP request to Foursquare API with caching and error handling"""
        if params is None:
            params = {}
        
        # Check cache first
        cache_key = self._get_cache_key(endpoint, params)
        cached_data = self._get_cached_data(cache_key)
        if cached_data:
            return cached_data
        
        url = f"{self.base_url}/{endpoint}"
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(url, headers=self.headers, params=params, timeout=30.0)
                
                if response.status_code == 200:
                    data = response.json()
                    self._cache_response(cache_key, data)
                    logger.info(f"Foursquare API call successful: {endpoint}")
                    return data
                elif response.status_code == 401:
                    raise FoursquareAPIError("Invalid API credentials", 401)
                elif response.status_code == 429:
                    retry_after = response.headers.get('Retry-After')
                    raise RateLimitError("Rate limit exceeded", int(retry_after) if retry_after else None)
                elif response.status_code == 404:
                    raise VenueNotFoundError("Venue not found")
                else:
                    error_text = await response.aread() if hasattr(response, 'aread') else 'Unknown error'
                    logger.error(f"Foursquare API error {response.status_code}: {error_text}")
                    raise FoursquareAPIError(f"API request failed: {response.status_code}", response.status_code)
        
        except httpx.TimeoutException:
            logger.error(f"Foursquare API timeout for endpoint: {endpoint}")
            raise FoursquareAPIError("API request timeout")
        except httpx.RequestError as e:
            logger.error(f"Network error during Foursquare API request: {str(e)}")
            raise FoursquareAPIError(f"Network error: {str(e)}")
    
    async def search_restaurants(self, latitude: float, longitude: float, radius_meters: int = 5000, 
                               query: Optional[str] = None, limit: int = 20) -> List[FoursquareVenue]:
        """Search for restaurants using Foursquare Places API"""
        
        # Restaurant categories in Foursquare (some common ones)
        restaurant_categories = "13065"  # General restaurant category
        
        params = {
            "ll": f"{latitude},{longitude}",
            "radius": radius_meters,
            "categories": restaurant_categories,
            "limit": limit,
            "fields": "fsq_id,name,location,categories,rating,price,photos,website,tel"
        }
        
        if query:
            params["query"] = query
        
        try:
            response = await self._make_request("places/search", params)
            venues = response.get('results', [])
            
            processed_venues = []
            for venue_data in venues:
                try:
                    venue = self._transform_venue_data(venue_data)
                    processed_venues.append(venue)
                except Exception as e:
                    logger.warning(f"Error processing venue {venue_data.get('fsq_id', 'unknown')}: {str(e)}")
                    continue
            
            logger.info(f"Found {len(processed_venues)} restaurants from Foursquare")
            return processed_venues
        
        except Exception as e:
            logger.error(f"Error searching restaurants: {str(e)}")
            raise
    
    async def get_venue_details(self, venue_id: str) -> FoursquareVenue:
        """Get detailed information for a specific venue"""
        params = {
            "fields": "fsq_id,name,location,categories,rating,price,photos,website,tel,hours"
        }
        
        try:
            response = await self._make_request(f"places/{venue_id}", params)
            return self._transform_venue_data(response)
        except Exception as e:
            logger.error(f"Error getting venue details for {venue_id}: {str(e)}")
            raise
    
    def _transform_venue_data(self, venue_data: Dict[str, Any]) -> FoursquareVenue:
        """Transform Foursquare venue data into our standard format"""
        location = venue_data.get('location', {})
        
        # Extract coordinates
        latitude = None
        longitude = None
        if 'geocodes' in venue_data:
            main_geocode = venue_data['geocodes'].get('main', {})
            latitude = main_geocode.get('latitude')
            longitude = main_geocode.get('longitude')
        
        # Extract address
        address = None
        if location.get('formatted_address'):
            address = location['formatted_address']
        elif location.get('address'):
            address = location['address']
        
        # Extract categories
        categories = []
        for cat in venue_data.get('categories', []):
            categories.append(cat.get('name', ''))
        
        # Extract photos
        photos = []
        if 'photos' in venue_data:
            for photo in venue_data['photos']:
                if 'prefix' in photo and 'suffix' in photo:
                    photo_url = f"{photo['prefix']}300x300{photo['suffix']}"
                    photos.append(photo_url)
        
        # Extract price tier (convert to our format)
        price = None
        if 'price' in venue_data:
            price = venue_data['price']
        
        return FoursquareVenue(
            id=f"foursquare_{venue_data.get('fsq_id', '')}",
            name=venue_data.get('name', ''),
            address=address,
            latitude=latitude,
            longitude=longitude,
            phone=venue_data.get('tel'),
            website=venue_data.get('website'),
            categories=categories,
            rating=venue_data.get('rating'),
            price=price,
            photos=photos,
            source="foursquare"
        )
    
    async def search_venues_near_address(self, address: str, radius_meters: int = 5000, 
                                       query: Optional[str] = None, limit: int = 20) -> List[FoursquareVenue]:
        """Search for restaurants near an address (using Foursquare's address resolution)"""
        
        restaurant_categories = "13065"  # General restaurant category
        
        params = {
            "near": address,
            "radius": radius_meters,
            "categories": restaurant_categories,
            "limit": limit,
            "fields": "fsq_id,name,location,categories,rating,price,photos,website,tel"
        }
        
        if query:
            params["query"] = query
        
        try:
            response = await self._make_request("places/search", params)
            venues = response.get('results', [])
            
            processed_venues = []
            for venue_data in venues:
                try:
                    venue = self._transform_venue_data(venue_data)
                    processed_venues.append(venue)
                except Exception as e:
                    logger.warning(f"Error processing venue {venue_data.get('fsq_id', 'unknown')}: {str(e)}")
                    continue
            
            logger.info(f"Found {len(processed_venues)} restaurants near '{address}' from Foursquare")
            return processed_venues
        
        except Exception as e:
            logger.error(f"Error searching restaurants near address: {str(e)}")
            raise

# Global service instance
foursquare_service = FoursquareService()