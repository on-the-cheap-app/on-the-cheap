#!/usr/bin/env python3
"""
Database Debug Test - Check what's actually stored in the restaurants collection
"""

import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent / 'backend'
load_dotenv(ROOT_DIR / '.env')

async def debug_database():
    """Debug what's in the database"""
    print("🔍 DATABASE DEBUG - Checking restaurants collection")
    print("=" * 60)
    
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ['DB_NAME']]
    
    try:
        # Check restaurants collection
        restaurants_cursor = db.restaurants.find({})
        restaurants = await restaurants_cursor.to_list(length=None)
        
        print(f"📊 Found {len(restaurants)} restaurants in database:")
        print()
        
        for i, restaurant in enumerate(restaurants):
            print(f"Restaurant {i+1}:")
            print(f"   ID: {restaurant.get('id', 'NO_ID')}")
            print(f"   Name: {restaurant.get('name', 'NO_NAME')}")
            print(f"   Source: {restaurant.get('source', 'NO_SOURCE')}")
            print(f"   Google Place ID: {restaurant.get('google_place_id', 'NO_GOOGLE_ID')}")
            print(f"   Specials: {len(restaurant.get('specials', []))}")
            print()
        
        # Check users collection for favorites
        print("👤 Checking users with favorites:")
        users_cursor = db.users.find({"favorite_restaurant_ids": {"$exists": True, "$ne": []}})
        users_with_favorites = await users_cursor.to_list(length=None)
        
        print(f"Found {len(users_with_favorites)} users with favorites:")
        for user in users_with_favorites:
            favorite_ids = user.get('favorite_restaurant_ids', [])
            print(f"   User: {user.get('email', 'NO_EMAIL')}")
            print(f"   Favorite IDs: {favorite_ids}")
            print()
        
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(debug_database())