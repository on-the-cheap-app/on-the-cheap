"""
Production Database Service with Indexing and Optimization

This service provides:
- Database connection management
- Index creation and optimization
- Query performance monitoring
- Connection pooling
- Database health checks
"""

import asyncio
import logging
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
import os
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

class DatabaseService:
    """Production database service with optimizations"""
    
    def __init__(self):
        self.client: Optional[AsyncIOMotorClient] = None
        self.db: Optional[AsyncIOMotorDatabase] = None
        self.indexes_created = False
        
        # Performance monitoring
        self.query_stats = {
            "total_queries": 0,
            "slow_queries": 0,
            "connection_errors": 0,
            "index_usage": {}
        }

    async def initialize(self):
        """Initialize database connection and create indexes"""
        try:
            mongo_url = os.environ['MONGO_URL']
            db_name = os.environ['DB_NAME']
            
            # Configure connection with production settings
            self.client = AsyncIOMotorClient(
                mongo_url,
                maxPoolSize=50,          # Maximum connections in pool
                minPoolSize=10,          # Minimum connections in pool
                maxIdleTimeMS=30000,     # 30 seconds max idle time
                connectTimeoutMS=5000,   # 5 second connection timeout
                serverSelectionTimeoutMS=5000,  # 5 second server selection timeout
                retryWrites=True,        # Enable retry writes for resilience
                w="majority"             # Write concern for data safety
            )
            
            self.db = self.client[db_name]
            
            # Verify connection
            await self.client.admin.command('ping')
            logger.info("Database connection established successfully")
            
            # Create indexes for performance
            await self.create_indexes()
            
            return True
            
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise

    async def create_indexes(self):
        """Create database indexes for optimal query performance"""
        if self.indexes_created:
            return
            
        try:
            # Restaurants collection indexes
            restaurants = self.db.restaurants
            
            # Location-based search (most important for restaurant discovery)
            await restaurants.create_index([
                ("location.latitude", 1),
                ("location.longitude", 1)
            ], name="location_2d")
            
            # Skip 2dsphere index for now due to existing data format incompatibility
            # The existing location format {latitude: X, longitude: Y} is not compatible with 2dsphere
            # We'll use the 2d index above which works with the current format
            
            # Restaurant lookup by ID (primary key)
            await restaurants.create_index("id", unique=True, name="restaurant_id_unique")
            
            # Search by name and cuisine
            await restaurants.create_index([
                ("name", "text"),
                ("cuisine_type", "text")
            ], name="text_search")
            
            # Verified restaurants filter
            await restaurants.create_index("is_verified", name="verified_filter")
            
            # Creation date for analytics
            await restaurants.create_index("created_at", name="created_at_idx")

            # =================== USERS COLLECTION ===================
            users = self.db.users
            
            # User login (email lookup)
            await users.create_index("email", unique=True, name="user_email_unique")
            
            # User ID lookup
            await users.create_index("id", unique=True, name="user_id_unique")
            
            # Favorites queries
            await users.create_index("favorite_restaurant_ids", name="favorites_idx")
            
            # Active users filter
            await users.create_index("is_active", name="active_users_idx")

            # =================== RESTAURANT OWNERS COLLECTION ===================
            owners = self.db.restaurant_owners
            
            # Owner login (email lookup)
            await owners.create_index("email", unique=True, name="owner_email_unique")
            
            # Owner ID lookup
            await owners.create_index("id", unique=True, name="owner_id_unique")
            
            # Restaurant ownership queries
            await owners.create_index("restaurant_ids", name="owner_restaurants_idx")
            
            # Verified owners filter
            await owners.create_index("is_verified", name="verified_owners_idx")

            # =================== PERFORMANCE INDEXES ===================
            
            # Compound index for restaurant search with filters
            await restaurants.create_index([
                ("location.latitude", 1),
                ("location.longitude", 1),
                ("is_verified", 1),
                ("cuisine_type", 1)
            ], name="location_verified_cuisine")
            
            # Index for special type filtering
            await restaurants.create_index("specials.special_type", name="specials_type_idx")
            
            # Index for active specials
            await restaurants.create_index([
                ("specials.is_active", 1),
                ("specials.days_available", 1)
            ], name="active_specials_idx")

            logger.info("All database indexes created successfully")
            self.indexes_created = True
            
            # Log index information
            await self.log_index_info()
            
        except Exception as e:
            logger.error(f"Failed to create database indexes: {e}")
            raise

    async def log_index_info(self):
        """Log information about created indexes"""
        try:
            collections = ["restaurants", "users", "restaurant_owners"]
            
            for collection_name in collections:
                collection = self.db[collection_name]
                indexes = await collection.list_indexes().to_list(length=None)
                
                index_names = [idx["name"] for idx in indexes]
                logger.info(f"Collection '{collection_name}' indexes: {', '.join(index_names)}")
                
        except Exception as e:
            logger.warning(f"Could not log index information: {e}")

    async def get_db_stats(self) -> Dict:
        """Get database performance statistics"""
        try:
            # Database stats
            db_stats = await self.db.command("dbStats")
            
            # Collection stats
            collections_stats = {}
            collections = ["restaurants", "users", "restaurant_owners"]
            
            for collection_name in collections:
                try:
                    stats = await self.db.command("collStats", collection_name)
                    collections_stats[collection_name] = {
                        "documents": stats.get("count", 0),
                        "size": stats.get("size", 0),
                        "storage_size": stats.get("storageSize", 0),
                        "indexes": stats.get("nindexes", 0),
                        "index_size": stats.get("totalIndexSize", 0)
                    }
                except Exception as e:
                    logger.warning(f"Could not get stats for collection {collection_name}: {e}")
                    collections_stats[collection_name] = {"error": str(e)}
            
            return {
                "database": {
                    "name": self.db.name,
                    "collections": db_stats.get("collections", 0),
                    "objects": db_stats.get("objects", 0),
                    "data_size": db_stats.get("dataSize", 0),
                    "storage_size": db_stats.get("storageSize", 0),
                    "index_size": db_stats.get("indexSize", 0),
                    "file_size": db_stats.get("fileSize", 0)
                },
                "collections": collections_stats,
                "query_performance": self.query_stats,
                "indexes_created": self.indexes_created
            }
            
        except Exception as e:
            logger.error(f"Failed to get database stats: {e}")
            return {"error": str(e)}

    async def health_check(self) -> Dict:
        """Perform database health check"""
        try:
            start_time = datetime.now()
            
            # Test basic connectivity
            await self.client.admin.command('ping')
            ping_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Test read operation
            start_time = datetime.now()
            await self.db.restaurants.count_documents({})
            read_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Test write operation (lightweight)
            start_time = datetime.now()
            health_doc = {
                "type": "health_check",
                "timestamp": datetime.now(timezone.utc),
                "test": True
            }
            await self.db.health_checks.insert_one(health_doc)
            write_time = (datetime.now() - start_time).total_seconds() * 1000
            
            # Clean up test document
            await self.db.health_checks.delete_one({"_id": health_doc["_id"]})
            
            return {
                "status": "healthy",
                "ping_time_ms": round(ping_time, 2),
                "read_time_ms": round(read_time, 2),
                "write_time_ms": round(write_time, 2),
                "total_time_ms": round(ping_time + read_time + write_time, 2),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.now(timezone.utc).isoformat()
            }

    async def optimize_collection(self, collection_name: str) -> Dict:
        """Optimize a specific collection"""
        try:
            collection = self.db[collection_name]
            
            # Analyze collection
            stats_before = await self.db.command("collStats", collection_name)
            
            # Reindex collection (rebuilds all indexes)
            await collection.reindex()
            
            # Get stats after optimization
            stats_after = await self.db.command("collStats", collection_name)
            
            logger.info(f"Optimized collection: {collection_name}")
            
            return {
                "collection": collection_name,
                "status": "optimized",
                "before": {
                    "size": stats_before.get("size", 0),
                    "storage_size": stats_before.get("storageSize", 0)
                },
                "after": {
                    "size": stats_after.get("size", 0),
                    "storage_size": stats_after.get("storageSize", 0)
                },
                "improvement": {
                    "size_reduction": stats_before.get("size", 0) - stats_after.get("size", 0),
                    "storage_reduction": stats_before.get("storageSize", 0) - stats_after.get("storageSize", 0)
                }
            }
            
        except Exception as e:
            logger.error(f"Failed to optimize collection {collection_name}: {e}")
            return {
                "collection": collection_name,
                "status": "failed",
                "error": str(e)
            }

    @asynccontextmanager
    async def transaction(self):
        """Database transaction context manager"""
        async with await self.client.start_session() as session:
            async with session.start_transaction():
                try:
                    yield session
                    await session.commit_transaction()
                except Exception:
                    await session.abort_transaction()
                    raise

    async def close(self):
        """Close database connections"""
        if self.client:
            self.client.close()
            logger.info("Database connections closed")

# Global database service instance
_db_service: Optional[DatabaseService] = None

def get_database_service() -> DatabaseService:
    """Get or create global database service instance"""
    global _db_service
    if _db_service is None:
        _db_service = DatabaseService()
    return _db_service

async def initialize_database_service():
    """Initialize database service on startup"""
    db_service = get_database_service()
    await db_service.initialize()
    logger.info("Database service initialized successfully")
    return db_service