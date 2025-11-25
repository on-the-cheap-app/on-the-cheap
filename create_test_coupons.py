#!/usr/bin/env python3
"""
Create test coupons in the database for mobile app testing
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
import uuid
import sys

# Add backend to path
sys.path.append('/app/backend')

async def create_test_coupons():
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client.restaurant_db
    
    print("Connected to MongoDB")
    
    # Get some restaurants from the database
    restaurants = await db.restaurants.find({}).limit(5).to_list(length=None)
    
    if not restaurants:
        print("❌ No restaurants found in database!")
        return
    
    print(f"Found {len(restaurants)} restaurants")
    
    # Create test coupons for each restaurant
    coupons_created = 0
    
    for restaurant in restaurants:
        # Create a percentage off coupon
        coupon1 = {
            "id": str(uuid.uuid4()),
            "restaurant_id": restaurant["id"],
            "owner_id": "test_owner_123",  # Mock owner ID
            "title": f"20% Off at {restaurant['name']}",
            "description": "Get 20% off your entire order! Valid for dine-in and takeout.",
            "coupon_type": "percentage",
            "discount_percentage": 20,
            "discount_amount": None,
            "free_item": None,
            "combo_price": None,
            "valid_from": datetime.now(timezone.utc).isoformat(),
            "valid_until": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
            "max_redemptions": 100,
            "max_per_customer": 1,
            "minimum_purchase": 25.0,
            "total_redemptions": 5,
            "total_revenue_impact": 150.0,
            "unique_customers": 5,
            "target_audience": "all_customers",
            "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
            "time_restrictions": None,
            "terms_conditions": "Cannot be combined with other offers. Valid for one use per customer.",
            "promotional_message": "Limited time offer! Save big on your next visit!",
            "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            "redemption_code": f"SAVE{str(uuid.uuid4())[:6].upper()}",
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "views": 25,
            "saves": 8,
            "click_rate": 0.32,
            "conversion_rate": 0.20
        }
        
        # Create a BOGO coupon
        coupon2 = {
            "id": str(uuid.uuid4()),
            "restaurant_id": restaurant["id"],
            "owner_id": "test_owner_123",
            "title": f"BOGO Deal at {restaurant['name']}",
            "description": "Buy one entree, get one free! Perfect for dining with a friend.",
            "coupon_type": "bogo",
            "discount_percentage": None,
            "discount_amount": None,
            "free_item": None,
            "combo_price": None,
            "valid_from": datetime.now(timezone.utc).isoformat(),
            "valid_until": (datetime.now(timezone.utc) + timedelta(days=14)).isoformat(),
            "max_redemptions": 50,
            "max_per_customer": 1,
            "minimum_purchase": None,
            "total_redemptions": 12,
            "total_revenue_impact": 240.0,
            "unique_customers": 12,
            "target_audience": "all_customers",
            "days_of_week": ["monday", "tuesday", "wednesday", "thursday"],
            "time_restrictions": {"start": "17:00", "end": "21:00"},
            "terms_conditions": "Valid for entrees only. Dine-in only. Equal or lesser value.",
            "promotional_message": "Bring a friend and save!",
            "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
            "redemption_code": f"BOGO{str(uuid.uuid4())[:6].upper()}",
            "status": "active",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
            "views": 42,
            "saves": 15,
            "click_rate": 0.36,
            "conversion_rate": 0.29
        }
        
        # Insert coupons
        await db.coupons.insert_one(coupon1)
        await db.coupons.insert_one(coupon2)
        coupons_created += 2
        
        print(f"✅ Created 2 coupons for {restaurant['name']}")
    
    print(f"\n🎉 Successfully created {coupons_created} test coupons!")
    
    # Verify
    total_coupons = await db.coupons.count_documents({})
    print(f"Total coupons in database: {total_coupons}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(create_test_coupons())
