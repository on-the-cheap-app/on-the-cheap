"""
Advanced Redis Distributed Caching Service

This service provides:
- Distributed caching with Redis
- Advanced cache strategies (cache-aside, write-through)
- Automatic failover and connection pooling
- Performance monitoring and analytics
- Cache warming and invalidation strategies
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union
import aioredis
from aioredis import Redis
import os
from contextlib import asynccontextmanager
from enum import Enum

logger = logging.getLogger(__name__)

class CacheStrategy(Enum):
    CACHE_ASIDE = "cache_aside"
    WRITE_THROUGH = "write_through"
    WRITE_BEHIND = "write_behind"

class RedisCacheService:
    """Advanced Redis caching service with production features"""
    
    def __init__(self):
        self.redis: Optional[Redis] = None
        self.connection_pool = None
        self.is_connected = False
        
        # Configuration
        self.redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/0')
        self.max_connections = int(os.environ.get('REDIS_MAX_CONNECTIONS', '50'))
        self.socket_timeout = int(os.environ.get('REDIS_SOCKET_TIMEOUT', '5'))
        self.socket_connect_timeout = int(os.environ.get('REDIS_CONNECT_TIMEOUT', '10'))
        self.retry_on_timeout = True
        self.health_check_interval = 60  # seconds
        
        # Performance tracking
        self.stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "errors": 0,
            "connection_errors": 0,
            "total_operations": 0,
            "avg_response_time": 0.0,
            "last_health_check": None
        }
        
        # Cache configuration by pattern
        self.cache_configs = {
            "google_places:*": {"ttl": 7200, "strategy": CacheStrategy.CACHE_ASIDE},
            "geocoding:*": {"ttl": 86400, "strategy": CacheStrategy.CACHE_ASIDE},
            "restaurant:*": {"ttl": 3600, "strategy": CacheStrategy.WRITE_THROUGH},
            "user:*": {"ttl": 1800, "strategy": CacheStrategy.CACHE_ASIDE},
            "owner:*": {"ttl": 1800, "strategy": CacheStrategy.WRITE_THROUGH},
            "session:*": {"ttl": 3600, "strategy": CacheStrategy.CACHE_ASIDE},
            "analytics:*": {"ttl": 300, "strategy": CacheStrategy.WRITE_BEHIND}
        }

    async def initialize(self) -> bool:
        """Initialize Redis connection with production settings"""
        try:
            # Create connection pool with production settings
            self.connection_pool = aioredis.ConnectionPool.from_url(
                self.redis_url,
                max_connections=self.max_connections,
                socket_timeout=self.socket_timeout,
                socket_connect_timeout=self.socket_connect_timeout,
                retry_on_timeout=self.retry_on_timeout,
                decode_responses=True,
                encoding='utf-8'
            )
            
            # Create Redis client
            self.redis = aioredis.Redis(connection_pool=self.connection_pool)
            
            # Test connection
            await self.redis.ping()
            self.is_connected = True
            
            # Start health check background task
            asyncio.create_task(self._health_check_loop())
            
            logger.info(f"Redis service initialized successfully: {self.redis_url}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to initialize Redis service: {e}")
            self.is_connected = False
            return False

    async def _health_check_loop(self):
        """Background health check for Redis connection"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                if self.redis:
                    start_time = datetime.now()
                    await self.redis.ping()
                    response_time = (datetime.now() - start_time).total_seconds() * 1000
                    
                    self.stats["last_health_check"] = datetime.now(timezone.utc).isoformat()
                    
                    if response_time > 100:  # Log slow responses
                        logger.warning(f"Slow Redis response: {response_time:.2f}ms")
                        
            except Exception as e:
                logger.error(f"Redis health check failed: {e}")
                self.is_connected = False
                self.stats["connection_errors"] += 1
                
                # Attempt to reconnect
                await self._attempt_reconnect()

    async def _attempt_reconnect(self):
        """Attempt to reconnect to Redis"""
        try:
            if self.connection_pool:
                await self.connection_pool.disconnect()
            
            await self.initialize()
            logger.info("Redis reconnection successful")
            
        except Exception as e:
            logger.error(f"Redis reconnection failed: {e}")

    def _get_cache_config(self, key: str) -> Dict[str, Any]:
        """Get cache configuration for a key pattern"""
        for pattern, config in self.cache_configs.items():
            if pattern.endswith('*'):
                prefix = pattern[:-1]
                if key.startswith(prefix):
                    return config
            elif pattern == key:
                return config
        
        # Default configuration
        return {"ttl": 3600, "strategy": CacheStrategy.CACHE_ASIDE}

    async def get(self, key: str, default: Any = None) -> Any:
        """Get value from cache with performance tracking"""
        if not self.is_connected:
            self.stats["misses"] += 1
            return default
            
        start_time = datetime.now()
        
        try:
            value = await self.redis.get(key)
            
            # Update performance stats
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_response_time(response_time)
            self.stats["total_operations"] += 1
            
            if value is not None:
                self.stats["hits"] += 1
                try:
                    return json.loads(value)
                except json.JSONDecodeError:
                    return value  # Return as string if not JSON
            else:
                self.stats["misses"] += 1
                return default
                
        except Exception as e:
            logger.error(f"Redis GET error for key '{key}': {e}")
            self.stats["errors"] += 1
            self.stats["misses"] += 1
            return default

    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set value in cache with automatic TTL and strategy handling"""
        if not self.is_connected:
            return False
            
        start_time = datetime.now()
        
        try:
            # Get cache configuration
            config = self._get_cache_config(key)
            cache_ttl = ttl or config["ttl"]
            
            # Serialize value
            if isinstance(value, (dict, list)):
                serialized_value = json.dumps(value, default=str)
            else:
                serialized_value = str(value)
            
            # Set with TTL
            success = await self.redis.setex(key, cache_ttl, serialized_value)
            
            # Update performance stats
            response_time = (datetime.now() - start_time).total_seconds() * 1000
            self._update_response_time(response_time)
            self.stats["total_operations"] += 1
            self.stats["sets"] += 1
            
            return bool(success)
            
        except Exception as e:
            logger.error(f"Redis SET error for key '{key}': {e}")
            self.stats["errors"] += 1
            return False

    async def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.is_connected:
            return False
            
        try:
            result = await self.redis.delete(key)
            self.stats["deletes"] += 1
            self.stats["total_operations"] += 1
            return bool(result)
            
        except Exception as e:
            logger.error(f"Redis DELETE error for key '{key}': {e}")
            self.stats["errors"] += 1
            return False

    async def invalidate_pattern(self, pattern: str) -> int:
        """Invalidate all keys matching a pattern"""
        if not self.is_connected:
            return 0
            
        try:
            keys = await self.redis.keys(pattern)
            if keys:
                result = await self.redis.delete(*keys)
                self.stats["deletes"] += len(keys)
                self.stats["total_operations"] += 1
                logger.info(f"Invalidated {result} keys matching pattern: {pattern}")
                return result
            return 0
            
        except Exception as e:
            logger.error(f"Redis pattern invalidation error for '{pattern}': {e}")
            self.stats["errors"] += 1
            return 0

    async def exists(self, key: str) -> bool:
        """Check if key exists in cache"""
        if not self.is_connected:
            return False
            
        try:
            result = await self.redis.exists(key)
            self.stats["total_operations"] += 1
            return bool(result)
            
        except Exception as e:
            logger.error(f"Redis EXISTS error for key '{key}': {e}")
            self.stats["errors"] += 1
            return False

    async def ttl(self, key: str) -> int:
        """Get time-to-live for a key"""
        if not self.is_connected:
            return -1
            
        try:
            result = await self.redis.ttl(key)
            self.stats["total_operations"] += 1
            return result
            
        except Exception as e:
            logger.error(f"Redis TTL error for key '{key}': {e}")
            self.stats["errors"] += 1
            return -1

    async def increment(self, key: str, amount: int = 1, ttl: Optional[int] = None) -> int:
        """Increment a counter with optional TTL"""
        if not self.is_connected:
            return 0
            
        try:
            async with self.redis.pipeline() as pipe:
                await pipe.incr(key, amount)
                if ttl:
                    await pipe.expire(key, ttl)
                results = await pipe.execute()
                
            self.stats["total_operations"] += 1
            return results[0]
            
        except Exception as e:
            logger.error(f"Redis INCR error for key '{key}': {e}")
            self.stats["errors"] += 1
            return 0

    async def cache_warming(self, warm_data: Dict[str, Any]) -> int:
        """Warm cache with predefined data"""
        if not self.is_connected:
            return 0
            
        warmed_count = 0
        
        try:
            async with self.redis.pipeline() as pipe:
                for key, value in warm_data.items():
                    config = self._get_cache_config(key)
                    
                    if isinstance(value, (dict, list)):
                        serialized_value = json.dumps(value, default=str)
                    else:
                        serialized_value = str(value)
                    
                    await pipe.setex(key, config["ttl"], serialized_value)
                    warmed_count += 1
                    
                await pipe.execute()
                
            logger.info(f"Cache warming completed: {warmed_count} keys loaded")
            return warmed_count
            
        except Exception as e:
            logger.error(f"Cache warming error: {e}")
            self.stats["errors"] += 1
            return 0

    def _update_response_time(self, response_time: float):
        """Update average response time"""
        if self.stats["avg_response_time"] == 0:
            self.stats["avg_response_time"] = response_time
        else:
            # Exponential moving average
            alpha = 0.1
            self.stats["avg_response_time"] = (
                alpha * response_time + 
                (1 - alpha) * self.stats["avg_response_time"]
            )

    async def get_performance_stats(self) -> Dict[str, Any]:
        """Get comprehensive performance statistics"""
        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (self.stats["hits"] / total_requests * 100) if total_requests > 0 else 0
        
        # Get Redis server info if connected
        server_info = {}
        if self.is_connected and self.redis:
            try:
                info = await self.redis.info()
                server_info = {
                    "used_memory": info.get("used_memory_human", "N/A"),
                    "connected_clients": info.get("connected_clients", 0),
                    "total_commands_processed": info.get("total_commands_processed", 0),
                    "keyspace_hits": info.get("keyspace_hits", 0),
                    "keyspace_misses": info.get("keyspace_misses", 0),
                    "used_cpu_sys": info.get("used_cpu_sys", 0),
                    "used_cpu_user": info.get("used_cpu_user", 0)
                }
            except Exception as e:
                logger.warning(f"Could not get Redis server info: {e}")
        
        return {
            "connection_status": "connected" if self.is_connected else "disconnected",
            "hit_rate": round(hit_rate, 2),
            "total_hits": self.stats["hits"],
            "total_misses": self.stats["misses"],
            "total_sets": self.stats["sets"],
            "total_deletes": self.stats["deletes"],
            "total_errors": self.stats["errors"],
            "connection_errors": self.stats["connection_errors"],
            "total_operations": self.stats["total_operations"],
            "avg_response_time_ms": round(self.stats["avg_response_time"], 2),
            "last_health_check": self.stats["last_health_check"],
            "redis_server": server_info,
            "cache_configs": {k: v for k, v in self.cache_configs.items()}
        }

    async def close(self):
        """Close Redis connections"""
        try:
            if self.connection_pool:
                await self.connection_pool.disconnect()
            self.is_connected = False
            logger.info("Redis service connections closed")
        except Exception as e:
            logger.error(f"Error closing Redis connections: {e}")

# Global Redis service instance
_redis_service: Optional[RedisCacheService] = None

async def get_redis_service() -> RedisCacheService:
    """Get or create global Redis service instance"""
    global _redis_service
    if _redis_service is None:
        _redis_service = RedisCacheService()
        await _redis_service.initialize()
    return _redis_service

async def initialize_redis_service() -> RedisCacheService:
    """Initialize Redis service on startup"""
    redis_service = await get_redis_service()
    logger.info("Redis distributed caching service initialized")
    return redis_service