"""
New Orleans Restaurant Yelp Enrichment
Enriches restaurant data with Yelp ratings, reviews, categories, and more.
"""

import pandas as pd
import requests
import time
import json
from datetime import datetime
from urllib.parse import quote

# Configuration
YELP_API_KEY = "77aBdrn-wye5CNhNruel3YxxpQ7R21-JIYsUn4KG5kV1l_fjN6NaP07z3baLf2N3zOjox0rJeb59PUz4sxK2VFMCxUrKF4o5fUyq0gA4RtmMOeoqE_AkZu0h2FF1aXYx"
YELP_API_URL = "https://api.yelp.com/v3/businesses/search"
YELP_MATCH_URL = "https://api.yelp.com/v3/businesses/matches"

INPUT_FILE = '/app/exports/nola_all_emails_combined.csv'
OUTPUT_FILE = '/app/exports/nola_yelp_enriched.csv'
PROGRESS_FILE = '/app/exports/yelp_progress.json'
DELAY_SECONDS = 0.5  # Yelp allows 5000 calls/day, be respectful

HEADERS = {
    "Authorization": f"Bearer {YELP_API_KEY}",
    "Accept": "application/json"
}

def search_yelp_business(name, city="New Orleans", state="LA"):
    """Search for a business on Yelp by name and location"""
    try:
        params = {
            "term": name,
            "location": f"{city}, {state}",
            "limit": 3,
            "categories": "restaurants,food,bars"
        }
        
        response = requests.get(YELP_API_URL, headers=HEADERS, params=params, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            businesses = data.get("businesses", [])
            
            if businesses:
                # Try to find best match by name similarity
                name_lower = name.lower()
                for biz in businesses:
                    biz_name_lower = biz.get("name", "").lower()
                    # Check for name match (exact or partial)
                    if name_lower in biz_name_lower or biz_name_lower in name_lower:
                        return biz
                    # Check if first significant word matches
                    name_words = [w for w in name_lower.split() if len(w) > 3]
                    biz_words = [w for w in biz_name_lower.split() if len(w) > 3]
                    if name_words and biz_words and name_words[0] == biz_words[0]:
                        return biz
                
                # Return first result if no better match
                return businesses[0]
        
        elif response.status_code == 429:
            print("Rate limited - waiting 60 seconds...")
            time.sleep(60)
            return search_yelp_business(name, city, state)
        
        elif response.status_code == 401:
            print("API key invalid or expired!")
            return None
            
    except Exception as e:
        print(f"Error searching Yelp: {e}")
    
    return None

def enrich_restaurant(name):
    """Enrich a restaurant with Yelp data"""
    result = {
        'restaurant_name': name,
        'yelp_name': '',
        'yelp_rating': None,
        'yelp_review_count': None,
        'yelp_price': '',
        'yelp_categories': '',
        'yelp_phone': '',
        'yelp_address': '',
        'yelp_url': '',
        'yelp_id': '',
        'status': 'pending'
    }
    
    biz = search_yelp_business(name)
    
    if biz:
        result['yelp_name'] = biz.get('name', '')
        result['yelp_rating'] = biz.get('rating')
        result['yelp_review_count'] = biz.get('review_count')
        result['yelp_price'] = biz.get('price', '')
        result['yelp_categories'] = ', '.join([c.get('title', '') for c in biz.get('categories', [])])
        result['yelp_phone'] = biz.get('display_phone', '')
        
        location = biz.get('location', {})
        result['yelp_address'] = ', '.join(filter(None, [
            location.get('address1', ''),
            location.get('city', ''),
            location.get('state', ''),
            location.get('zip_code', '')
        ]))
        
        result['yelp_url'] = biz.get('url', '')
        result['yelp_id'] = biz.get('id', '')
        result['status'] = 'found'
    else:
        result['status'] = 'not_found'
    
    return result

def load_progress():
    """Load progress from previous run"""
    try:
        with open(PROGRESS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {'completed': [], 'results': []}

def save_progress(progress):
    """Save progress for resume capability"""
    with open(PROGRESS_FILE, 'w') as f:
        json.dump(progress, f)

def main():
    print(f"=== Yelp Restaurant Enrichment ===")
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    # Load data
    df = pd.read_csv(INPUT_FILE)
    print(f"Loaded {len(df)} restaurants to enrich\n")
    
    # Get unique restaurant names
    unique_names = df['restaurant_name'].unique()
    print(f"Unique restaurant names: {len(unique_names)}\n")
    
    # Load previous progress
    progress = load_progress()
    completed_names = set(progress['completed'])
    results = progress['results']
    
    # Filter to only unprocessed
    names_todo = [n for n in unique_names if n not in completed_names]
    print(f"Already completed: {len(completed_names)}")
    print(f"Remaining: {len(names_todo)}\n")
    
    # Process each restaurant
    for idx, name in enumerate(names_todo):
        print(f"[{len(completed_names)+1}/{len(unique_names)}] Enriching: {name[:50]}...", end=" ")
        
        result = enrich_restaurant(name)
        
        if result['status'] == 'found':
            print(f"✅ {result['yelp_rating']}⭐ ({result['yelp_review_count']} reviews)")
        else:
            print("❌ Not found on Yelp")
        
        results.append(result)
        completed_names.add(name)
        
        # Save progress every 20 restaurants
        if len(completed_names) % 20 == 0:
            progress = {'completed': list(completed_names), 'results': results}
            save_progress(progress)
            print(f"  [Progress saved: {len(completed_names)}/{len(unique_names)}]")
        
        time.sleep(DELAY_SECONDS)
    
    # Save final results
    progress = {'completed': list(completed_names), 'results': results}
    save_progress(progress)
    
    # Create output DataFrame
    results_df = pd.DataFrame(results)
    
    # Merge with original data
    enriched_df = df.merge(
        results_df[['restaurant_name', 'yelp_rating', 'yelp_review_count', 'yelp_price', 
                    'yelp_categories', 'yelp_phone', 'yelp_address', 'yelp_url']],
        on='restaurant_name',
        how='left'
    )
    
    enriched_df.to_csv(OUTPUT_FILE, index=False)
    
    # Summary
    found = sum(1 for r in results if r['status'] == 'found')
    not_found = sum(1 for r in results if r['status'] == 'not_found')
    
    print(f"\n=== ENRICHMENT COMPLETE ===")
    print(f"Total processed: {len(results)}")
    print(f"Found on Yelp: {found}")
    print(f"Not found: {not_found}")
    print(f"\nResults saved to: {OUTPUT_FILE}")

if __name__ == '__main__':
    main()
