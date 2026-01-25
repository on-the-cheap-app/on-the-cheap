"""
New Orleans Restaurant Database Import
Imports enriched restaurant data into the On-the-Cheap MongoDB database.
"""

import pandas as pd
import asyncio
import os
import uuid
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

# Load environment
load_dotenv('/app/backend/.env')

INPUT_FILE = '/app/exports/nola_yelp_enriched.csv'
MONGO_URL = os.environ.get('MONGO_URL')
DB_NAME = os.environ.get('DB_NAME', 'onthecheap')

# New Orleans coordinates (center point)
NOLA_LAT = 29.9511
NOLA_LNG = -90.0715

def price_to_level(price_str):
    """Convert Yelp price string to price level (1-4)"""
    if pd.isna(price_str) or not price_str:
        return 2  # Default to moderate
    return len(str(price_str).strip())

def parse_categories(categories_str):
    """Parse Yelp categories string to list"""
    if pd.isna(categories_str) or not categories_str:
        return ["Restaurant"]
    return [c.strip() for c in str(categories_str).split(',')]

def generate_location(address, base_lat=NOLA_LAT, base_lng=NOLA_LNG):
    """Generate approximate location coordinates based on address hash"""
    # Create a deterministic but varied location based on address
    import hashlib
    if pd.isna(address) or not address:
        address = "New Orleans, LA"
    
    hash_val = int(hashlib.md5(str(address).encode()).hexdigest()[:8], 16)
    
    # Spread restaurants across ~10 mile radius of NOLA
    lat_offset = ((hash_val % 1000) - 500) / 5000  # -0.1 to +0.1 degrees
    lng_offset = (((hash_val // 1000) % 1000) - 500) / 5000
    
    return {
        "latitude": round(base_lat + lat_offset, 6),
        "longitude": round(base_lng + lng_offset, 6)
    }

def create_restaurant_doc(row):
    """Create a restaurant document from CSV row"""
    
    # Use Yelp address if available, otherwise construct from data
    address = row.get('yelp_address', '')
    if pd.isna(address) or not address:
        address = "New Orleans, LA"
    
    # Parse website
    website = row.get('website', '')
    if pd.isna(website):
        website = row.get('yelp_url', '')
    
    # Parse phone
    phone = row.get('yelp_phone', '')
    if pd.isna(phone):
        phone = None
    
    # Parse rating
    rating = row.get('yelp_rating')
    if pd.isna(rating):
        rating = None
    else:
        rating = float(rating)
    
    doc = {
        "id": str(uuid.uuid4()),
        "name": str(row['restaurant_name']),
        "address": str(address),
        "location": generate_location(address),
        "phone": phone if phone else None,
        "website": str(website) if website and not pd.isna(website) else None,
        "cuisine_type": parse_categories(row.get('yelp_categories')),
        "rating": rating,
        "price_level": price_to_level(row.get('yelp_price')),
        "specials": [],  # No specials initially - owners can add them
        "is_verified": False,  # Will need verification
        "created_at": datetime.now(timezone.utc).isoformat(),
        # Additional NOLA-specific fields
        "source": "nola_import",
        "email": str(row['email']) if not pd.isna(row.get('email')) else None,
        "yelp_url": str(row.get('yelp_url')) if not pd.isna(row.get('yelp_url')) else None,
        "yelp_review_count": int(row.get('yelp_review_count')) if not pd.isna(row.get('yelp_review_count')) else None,
        "city": "New Orleans",
        "state": "LA",
        "timezone": "America/Chicago"
    }
    
    return doc

async def import_restaurants():
    """Main import function"""
    print(f"=== New Orleans Restaurant Import ===")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Connect to MongoDB
    print(f"Connecting to MongoDB...")
    client = AsyncIOMotorClient(MONGO_URL)
    db = client[DB_NAME]
    
    # Load data
    df = pd.read_csv(INPUT_FILE)
    print(f"Loaded {len(df)} restaurants from CSV\n")
    
    # Check existing restaurants
    existing_count = await db.restaurants.count_documents({"source": "nola_import"})
    print(f"Existing NOLA imports in database: {existing_count}")
    
    # Get existing restaurant names to avoid duplicates
    existing_names = set()
    async for doc in db.restaurants.find({"source": "nola_import"}, {"name": 1}):
        existing_names.add(doc['name'].lower())
    
    # Also check for restaurants with same name regardless of source
    async for doc in db.restaurants.find({}, {"name": 1}):
        existing_names.add(doc['name'].lower())
    
    print(f"Total existing restaurant names: {len(existing_names)}")
    
    # Prepare documents
    docs_to_insert = []
    skipped = 0
    
    for _, row in df.iterrows():
        name = str(row['restaurant_name'])
        
        # Skip if already exists
        if name.lower() in existing_names:
            skipped += 1
            continue
        
        doc = create_restaurant_doc(row)
        docs_to_insert.append(doc)
        existing_names.add(name.lower())  # Prevent duplicates within import
    
    print(f"\nRestaurants to import: {len(docs_to_insert)}")
    print(f"Skipped (already exist): {skipped}")
    
    if not docs_to_insert:
        print("\nNo new restaurants to import!")
        return
    
    # Insert in batches
    batch_size = 100
    total_inserted = 0
    
    for i in range(0, len(docs_to_insert), batch_size):
        batch = docs_to_insert[i:i+batch_size]
        result = await db.restaurants.insert_many(batch)
        total_inserted += len(result.inserted_ids)
        print(f"  Inserted batch {i//batch_size + 1}: {len(batch)} restaurants")
    
    # Create index for efficient querying
    await db.restaurants.create_index([("source", 1)])
    await db.restaurants.create_index([("city", 1)])
    await db.restaurants.create_index([("name", "text")])
    
    # Final count
    final_count = await db.restaurants.count_documents({})
    nola_count = await db.restaurants.count_documents({"source": "nola_import"})
    
    print(f"\n=== IMPORT COMPLETE ===")
    print(f"Total inserted: {total_inserted}")
    print(f"Total NOLA restaurants in DB: {nola_count}")
    print(f"Total restaurants in DB: {final_count}")
    
    # Show some sample imports
    print(f"\nSample imported restaurants:")
    async for doc in db.restaurants.find({"source": "nola_import"}).limit(5):
        print(f"  • {doc['name']} - {doc.get('rating', 'N/A')}⭐ - {', '.join(doc['cuisine_type'][:2])}")
    
    client.close()

if __name__ == '__main__':
    asyncio.run(import_restaurants())
