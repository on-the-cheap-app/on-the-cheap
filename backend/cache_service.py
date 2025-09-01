"""
Production-Grade Caching Service for On-the-Cheap API

This service provides centralized caching for:
- Google Places API responses
- Geocoding API responses  
- Restaurant search results
- API quota tracking and management
"""

import json
import hashlib
import asyncio
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class CacheType(Enum):
    GOOGLE_PLACES = "google_places"
    GEOCODING = "geocoding"
    RESTAURANT_SEARCH = "restaurant_search"
    API_QUOTA = "api_quota"

@dataclass
class CacheEntry:
    key: str
    data: Any
    cache_type: CacheType
    created_at: datetime
    expires_at: datetime
    hit_count: int = 0
    last_accessed: Optional[datetime] = None

@dataclass
class ApiQuotaInfo:
    service: str  # google_places, google_geocoding, foursquare
    requests_made: int
    quota_limit: int
    reset_time: datetime
    cost_per_request: float = 0.0
    total_cost: float = 0.0

class ProductionCacheService:
    """Production-grade in-memory cache with TTL, LRU eviction, and quota tracking"""
    
    def __init__(self, max_size: int = 10000, default_ttl: int = 3600):
        self.cache: Dict[str, CacheEntry] = {}
        self.max_size = max_size
        self.default_ttl = default_ttl
        
        # Cache configuration by type
        self.cache_config = {
            CacheType.GOOGLE_PLACES: {"ttl": 7200, "max_entries": 3000},  # 2 hours, places change slowly
            CacheType.GEOCODING: {"ttl": 86400, "max_entries": 2000},     # 24 hours, addresses don't change
            CacheType.RESTAURANT_SEARCH: {"ttl": 1800, "max_entries": 4000},  # 30 minutes, search results
            CacheType.API_QUOTA: {"ttl": 3600, "max_entries": 100}       # 1 hour, quota tracking
        }
        
        # API Quota tracking
        self.api_quotas: Dict[str, ApiQuotaInfo] = {}
        
        # Performance metrics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "evictions": 0,
            "memory_usage": 0,
            "api_calls_saved": 0,
            "cost_saved": 0.0
        }
        
        logger.info("Production cache service initialized")

    def _generate_cache_key(self, cache_type: CacheType, **params) -> str:
        """Generate deterministic cache key from parameters"""
        # Sort parameters for consistent key generation
        sorted_params = sorted(params.items())
        param_string = json.dumps(sorted_params, sort_keys=True)
        key_hash = hashlib.sha256(param_string.encode()).hexdigest()[:16]
        return f"{cache_type.value}:{key_hash}"

    def _should_evict(self) -> bool:
        """Determine if cache needs eviction"""
        return len(self.cache) >= self.max_size

    def _evict_expired(self) -> int:
        """Remove expired entries"""
        now = datetime.now()
        expired_keys = [
            key for key, entry in self.cache.items() 
            if entry.expires_at < now
        ]
        
        for key in expired_keys:
            del self.cache[key]
            
        if expired_keys:
            self.stats["evictions"] += len(expired_keys)
            logger.info(f"Evicted {len(expired_keys)} expired cache entries")
            
        return len(expired_keys)

    def _evict_lru(self, count: int = 100) -> int:
        """Evict least recently used entries"""
        if not self.cache:
            return 0
            
        # Sort by last_accessed time (oldest first)
        sorted_entries = sorted(
            self.cache.items(),
            key=lambda x: x[1].last_accessed or x[1].created_at
        )
        
        evicted = 0
        for key, _ in sorted_entries[:count]:
            if key in self.cache:
                del self.cache[key]
                evicted += 1
                
        self.stats["evictions"] += evicted
        logger.info(f"LRU evicted {evicted} cache entries")
        return evicted

    def _cleanup_cache(self):
        """Cleanup expired entries and manage size"""
        # First remove expired entries
        expired_count = self._evict_expired()
        
        # If still over limit, use LRU eviction
        if self._should_evict():
            lru_count = self._evict_lru(count=max(100, len(self.cache) - self.max_size + 500))
            logger.info(f"Cache cleanup: {expired_count} expired, {lru_count} LRU evicted")

    async def get(self, cache_type: CacheType, **params) -> Optional[Any]:
        """Get cached data"""
        cache_key = self._generate_cache_key(cache_type, **params)
        
        entry = self.cache.get(cache_key)
        if not entry:
            self.stats["misses"] += 1
            return None
            
        now = datetime.now()
        if entry.expires_at < now:
            # Expired entry
            del self.cache[cache_key]
            self.stats["misses"] += 1
            return None
            
        # Update access info
        entry.hit_count += 1
        entry.last_accessed = now
        self.stats["hits"] += 1
        
        logger.debug(f"Cache hit: {cache_key[:20]}... (hits: {entry.hit_count})")
        return entry.data

    async def set(self, cache_type: CacheType, data: Any, ttl: Optional[int] = None, **params) -> None:
        """Set cached data"""
        cache_key = self._generate_cache_key(cache_type, **params)
        
        # Use type-specific TTL or provided TTL
        if ttl is None:
            ttl = self.cache_config.get(cache_type, {}).get("ttl", self.default_ttl)
            
        now = datetime.now()
        expires_at = now + timedelta(seconds=ttl)
        
        entry = CacheEntry(
            key=cache_key,
            data=data,
            cache_type=cache_type,
            created_at=now,
            expires_at=expires_at,
            last_accessed=now
        )
        
        self.cache[cache_key] = entry
        
        # Cleanup if needed
        if self._should_evict():
            self._cleanup_cache()
            
        logger.debug(f"Cache set: {cache_key[:20]}... (TTL: {ttl}s)")

    async def invalidate(self, cache_type: CacheType, **params) -> bool:
        """Invalidate specific cache entry"""
        cache_key = self._generate_cache_key(cache_type, **params)
        
        if cache_key in self.cache:
            del self.cache[cache_key]
            logger.info(f"Cache invalidated: {cache_key[:20]}...")
            return True
        return False

    async def clear_type(self, cache_type: CacheType) -> int:
        """Clear all cache entries of specific type"""
        keys_to_remove = [
            key for key, entry in self.cache.items()
            if entry.cache_type == cache_type
        ]
        
        for key in keys_to_remove:
            del self.cache[key]
            
        logger.info(f"Cleared {len(keys_to_remove)} entries of type {cache_type.value}")
        return len(keys_to_remove)

    # =================== API QUOTA MANAGEMENT ===================

    def track_api_usage(self, service: str, requests: int = 1, cost: float = 0.0):
        """Track API usage for quota management"""
        now = datetime.now()
        
        if service not in self.api_quotas:
            # Initialize quota tracking (daily limits)
            daily_limits = {
                "google_places": 100000,     # Google Places daily quota
                "google_geocoding": 40000,   # Google Geocoding daily quota  
                "foursquare": 950            # Foursquare daily quota (free tier)
            }
            
            self.api_quotas[service] = ApiQuotaInfo(
                service=service,
                requests_made=0,
                quota_limit=daily_limits.get(service, 1000),
                reset_time=now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1),
                cost_per_request=cost / requests if requests > 0 else 0.0,
                total_cost=0.0
            )
        
        quota = self.api_quotas[service]
        
        # Check if quota period has reset
        if now >= quota.reset_time:
            quota.requests_made = 0
            quota.total_cost = 0.0
            quota.reset_time = now.replace(hour=0, minute=0, second=0, microsecond=0) + timedelta(days=1)
        
        # Update usage
        quota.requests_made += requests
        quota.total_cost += cost
        
        # Log warnings for high usage
        usage_percent = (quota.requests_made / quota.quota_limit) * 100
        if usage_percent > 80:
            logger.warning(f"{service} API usage at {usage_percent:.1f}% ({quota.requests_made}/{quota.quota_limit})")
        elif usage_percent > 90:
            logger.error(f"CRITICAL: {service} API usage at {usage_percent:.1f}% - approaching limit!")

    def get_quota_status(self, service: str) -> Optional[Dict]:
        """Get current quota status for a service"""
        if service not in self.api_quotas:
            return None
            
        quota = self.api_quotas[service]
        usage_percent = (quota.requests_made / quota.quota_limit) * 100
        
        return {
            "service": service,
            "requests_made": quota.requests_made,
            "quota_limit": quota.quota_limit,
            "usage_percent": round(usage_percent, 2),
            "remaining_requests": quota.quota_limit - quota.requests_made,
            "reset_time": quota.reset_time.isoformat(),
            "total_cost": round(quota.total_cost, 4),
            "estimated_daily_cost": round(quota.total_cost, 4)
        }

    def should_throttle(self, service: str, threshold: float = 0.9) -> bool:
        """Check if API calls should be throttled"""
        if service not in self.api_quotas:
            return False
            
        quota = self.api_quotas[service]
        usage_percent = quota.requests_made / quota.quota_limit
        return usage_percent >= threshold

    # =================== PERFORMANCE METRICS ===================

    def get_cache_stats(self) -> Dict:
        """Get comprehensive cache performance statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        # Calculate memory usage estimate
        memory_usage = len(self.cache) * 1024  # Rough estimate in bytes
        
        # Cache type breakdown
        type_breakdown = {}
        for entry in self.cache.values():
            cache_type = entry.cache_type.value
            if cache_type not in type_breakdown:
                type_breakdown[cache_type] = {"count": 0, "total_hits": 0}
            type_breakdown[cache_type]["count"] += 1
            type_breakdown[cache_type]["total_hits"] += entry.hit_count
        
        return {
            "cache_entries": len(self.cache),
            "max_size": self.max_size,
            "hit_rate": round(hit_rate, 2),
            "total_hits": self.stats["hits"],
            "total_misses": self.stats["misses"],
            "total_evictions": self.stats["evictions"],
            "memory_usage_estimate": f"{memory_usage / 1024:.1f} KB",
            "api_calls_saved": self.stats["api_calls_saved"],
            "estimated_cost_saved": f"${self.stats['cost_saved']:.4f}",
            "type_breakdown": type_breakdown
        }

    def get_all_quota_status(self) -> Dict[str, Dict]:
        """Get quota status for all tracked services"""
        return {
            service: self.get_quota_status(service)
            for service in self.api_quotas.keys()
        }

# Global cache instance
_cache_service: Optional[ProductionCacheService] = None

def get_cache_service() -> ProductionCacheService:
    """Get or create global cache service instance"""
    global _cache_service
    if _cache_service is None:
        _cache_service = ProductionCacheService()
    return _cache_service

async def initialize_cache_service():
    """Initialize cache service on startup"""
    cache_service = get_cache_service()
    logger.info("Cache service initialized successfully")
    return cache_service