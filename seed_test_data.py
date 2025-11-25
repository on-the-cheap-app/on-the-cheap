#!/usr/bin/env python3
"""
Seed database with test restaurants and coupons for mobile app testing
"""

import asyncio
import os
from motor.motor_asyncio import AsyncIOMotorClient
from datetime import datetime, timezone, timedelta
import uuid

async def seed_database():
    # Connect to MongoDB
    mongo_url = os.environ.get('MONGO_URL', 'mongodb://localhost:27017')
    client = AsyncIOMotorClient(mongo_url)
    db = client.restaurant_db
    
    print("Connected to MongoDB")
    
    # Create test restaurants in San Francisco
    test_restaurants = [
        {
            "id": str(uuid.uuid4()),
            "name": "The Golden Spoon",
            "address": "123 Market Street, San Francisco, CA 94105",
            "location": {"latitude": 37.7749, "longitude": -122.4194},
            "phone": "+1-415-555-0101",
            "website": "https://goldenspoonsf.com",
            "cuisine_type": ["American", "Fine Dining"],
            "rating": 4.5,
            "price_level": 3,
            "photos": [{
                "url": "https://images.unsplash.com/photo-1517248135467-4c7edcad34c4?w=400&h=300",
                "width": 400,
                "height": 300,
                "is_fallback": True
            }],
            "specials": [],
            "is_verified": True,
            "source": "owner_managed",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Pizza Paradise",
            "address": "456 Mission Street, San Francisco, CA 94105",
            "location": {"latitude": 37.7879, "longitude": -122.3987},
            "phone": "+1-415-555-0202",
            "website": "https://pizzaparadise.com",
            "cuisine_type": ["Italian", "Pizza"],
            "rating": 4.2,
            "price_level": 2,
            "photos": [{
                "url": "https://images.unsplash.com/photo-1513104890138-7c749659a591?w=400&h=300",
                "width": 400,
                "height": 300,
                "is_fallback": True
            }],
            "specials": [],
            "is_verified": True,
            "source": "owner_managed",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Sushi Central",
            "address": "789 Embarcadero, San Francisco, CA 94111",
            "location": {"latitude": 37.7994, "longitude": -122.3988},
            "phone": "+1-415-555-0303",
            "website": "https://sushicentral.com",
            "cuisine_type": ["Japanese", "Sushi"],
            "rating": 4.7,
            "price_level": 3,
            "photos": [{
                "url": "https://images.unsplash.com/photo-1579584425555-c3ce17fd4351?w=400&h=300",
                "width": 400,
                "height": 300,
                "is_fallback": True
            }],
            "specials": [],
            "is_verified": True,
            "source": "owner_managed",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Taco Fiesta",
            "address": "321 Valencia Street, San Francisco, CA 94103",
            "location": {"latitude": 37.7619, "longitude": -122.4211},
            "phone": "+1-415-555-0404",
            "website": "https://tacofiesta.com",
            "cuisine_type": ["Mexican", "Tacos"],
            "rating": 4.3,
            "price_level": 1,
            "photos": [{
                "url": "https://images.unsplash.com/photo-1565299585323-38d6b0865b47?w=400&h=300",
                "width": 400,
                "height": 300,
                "is_fallback": True
            }],
            "specials": [],
            "is_verified": True,
            "source": "owner_managed",
            "created_at": datetime.now(timezone.utc).isoformat()
        },
        {
            "id": str(uuid.uuid4()),
            "name": "Burger Barn",
            "address": "654 Haight Street, San Francisco, CA 94117",
            "location": {"latitude": 37.7694, "longitude": -122.4480},
            "phone": "+1-415-555-0505",
            "website": "https://burgerbarn.com",
            "cuisine_type": ["American", "Burgers"],
            "rating": 4.0,
            "price_level": 2,
            "photos": [{
                "url": "https://images.unsplash.com/photo-1568901346375-23c9450c58cd?w=400&h=300",
                "width": 400,
                "height": 300,
                "is_fallback": True
            }],
            "specials": [],
            "is_verified": True,
            "source": "owner_managed",
            "created_at": datetime.now(timezone.utc).isoformat()
        }
    ]
    
    # Insert restaurants
    await db.restaurants.insert_many(test_restaurants)
    print(f"✅ Created {len(test_restaurants)} test restaurants")
    
    # Create coupons for each restaurant
    coupons_list = []
    
    coupon_templates = [
        {
            "type": "percentage",
            "title_template": "{}% Off",
            "description_template": "Get {}% off your entire order! Valid for dine-in and takeout.",
            "discount_percentage": 20,
            "days": 30
        },
        {
            "type": "bogo",
            "title_template": "BOGO Deal",
            "description_template": "Buy one entree, get one free! Perfect for dining with a friend.",
            "days": 14
        },
        {
            "type": "fixed_amount",
            "title_template": "${} Off",
            "description_template": "Save ${} on your order of $50 or more!",
            "discount_amount": 10.0,
            "days": 21
        }
    ]
    
    for restaurant in test_restaurants:
        # Create 2 coupons per restaurant
        for i, template in enumerate(coupon_templates[:2]):
            if template["type"] == "percentage":
                title = template["title_template"].format(template["discount_percentage"])
                description = template["description_template"].format(template["discount_percentage"])
                coupon = {
                    "id": str(uuid.uuid4()),
                    "restaurant_id": restaurant["id"],
                    "owner_id": "test_owner_mobile",
                    "title": f"{title} at {restaurant['name']}",
                    "description": description,
                    "coupon_type": "percentage",
                    "discount_percentage": template["discount_percentage"],
                    "discount_amount": None,
                    "free_item": None,
                    "combo_price": None,
                    "minimum_purchase": 25.0,
                }
            elif template["type"] == "bogo":
                title = template["title_template"]
                description = template["description_template"]
                coupon = {
                    "id": str(uuid.uuid4()),
                    "restaurant_id": restaurant["id"],
                    "owner_id": "test_owner_mobile",
                    "title": f"{title} at {restaurant['name']}",
                    "description": description,
                    "coupon_type": "bogo",
                    "discount_percentage": None,
                    "discount_amount": None,
                    "free_item": None,
                    "combo_price": None,
                    "minimum_purchase": None,
                }
            else:
                title = template["title_template"].format(template["discount_amount"])
                description = template["description_template"].format(template["discount_amount"])
                coupon = {
                    "id": str(uuid.uuid4()),
                    "restaurant_id": restaurant["id"],
                    "owner_id": "test_owner_mobile",
                    "title": f"{title} at {restaurant['name']}",
                    "description": description,
                    "coupon_type": "fixed_amount",
                    "discount_percentage": None,
                    "discount_amount": template["discount_amount"],
                    "free_item": None,
                    "combo_price": None,
                    "minimum_purchase": 50.0,
                }
            
            # Add common fields
            coupon.update({
                "valid_from": datetime.now(timezone.utc).isoformat(),
                "valid_until": (datetime.now(timezone.utc) + timedelta(days=template["days"])).isoformat(),
                "max_redemptions": 100,
                "max_per_customer": 1,
                "total_redemptions": i * 3,
                "total_revenue_impact": i * 45.0,
                "unique_customers": i * 3,
                "target_audience": "all_customers",
                "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
                "time_restrictions": None,
                "terms_conditions": "Cannot be combined with other offers. One use per customer.",
                "promotional_message": "Limited time offer! Don't miss out!",
                "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==",
                "redemption_code": f"SAVE{str(uuid.uuid4())[:6].upper()}",
                "status": "active",
                "created_at": datetime.now(timezone.utc).isoformat(),
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "views": 10 + (i * 5),
                "saves": 3 + i,
                "click_rate": 0.30,
                "conversion_rate": 0.15
            })
            
            coupons_list.append(coupon)
    
    # Insert coupons
    await db.coupons.insert_many(coupons_list)
    print(f"✅ Created {len(coupons_list)} test coupons")
    
    # Verify
    rest_count = await db.restaurants.count_documents({})
    coupon_count = await db.coupons.count_documents({})
    
    print(f"\n🎉 Database seeded successfully!")
    print(f"  - Restaurants: {rest_count}")
    print(f"  - Coupons: {coupon_count}")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_database())
