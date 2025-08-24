#!/usr/bin/env python3
"""
Debug script to test the favorites functionality step by step
"""

import requests
import json
import uuid

def debug_favorites():
    base_url = "https://special-finder.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    # Create test user
    test_email = f"debug_test_{uuid.uuid4().hex[:8]}@example.com"
    registration_data = {
        "email": test_email,
        "password": "DebugTest123!",
        "first_name": "Debug",
        "last_name": "Tester"
    }
    
    print(f"🔍 Creating test user: {test_email}")
    reg_response = requests.post(f"{api_url}/users/register", json=registration_data)
    print(f"Registration response: {reg_response.status_code}")
    
    if reg_response.status_code != 200:
        print(f"Registration failed: {reg_response.text}")
        return
    
    reg_data = reg_response.json()
    token = reg_data.get('access_token')
    headers = {'Authorization': f'Bearer {token}'}
    
    print(f"✅ User created successfully, token: {token[:20]}...")
    
    # Get user info to check initial state
    user_response = requests.get(f"{api_url}/users/me", headers=headers)
    print(f"User info response: {user_response.status_code}")
    if user_response.status_code == 200:
        user_data = user_response.json()
        print(f"Initial favorite_restaurant_ids: {user_data.get('favorite_restaurant_ids', [])}")
    
    # Search for restaurants
    search_params = {
        'latitude': 37.7749,
        'longitude': -122.4194,
        'radius': 8047
    }
    
    print(f"\n🔍 Searching for restaurants...")
    search_response = requests.get(f"{api_url}/restaurants/search", params=search_params)
    print(f"Search response: {search_response.status_code}")
    
    if search_response.status_code != 200:
        print(f"Search failed: {search_response.text}")
        return
    
    search_data = search_response.json()
    restaurants = search_data.get('restaurants', [])
    google_restaurants = [r for r in restaurants if r['id'].startswith('google_')]
    
    print(f"Found {len(restaurants)} total restaurants, {len(google_restaurants)} Google Places")
    
    if not google_restaurants:
        print("No Google Places restaurants found!")
        return
    
    # Add first Google Places restaurant to favorites
    test_restaurant = google_restaurants[0]
    restaurant_id = test_restaurant['id']
    restaurant_name = test_restaurant['name']
    
    print(f"\n🔍 Adding restaurant to favorites:")
    print(f"  ID: {restaurant_id}")
    print(f"  Name: {restaurant_name}")
    
    add_response = requests.post(f"{api_url}/users/favorites/{restaurant_id}", headers=headers)
    print(f"Add favorite response: {add_response.status_code}")
    print(f"Add favorite response body: {add_response.text}")
    
    # Check user info again to see if favorite was added
    user_response2 = requests.get(f"{api_url}/users/me", headers=headers)
    print(f"\nUser info after adding favorite: {user_response2.status_code}")
    if user_response2.status_code == 200:
        user_data2 = user_response2.json()
        favorite_ids = user_data2.get('favorite_restaurant_ids', [])
        print(f"favorite_restaurant_ids after adding: {favorite_ids}")
        print(f"Restaurant ID in favorites: {restaurant_id in favorite_ids}")
    
    # Get favorites
    print(f"\n🔍 Getting favorites...")
    favorites_response = requests.get(f"{api_url}/users/favorites", headers=headers)
    print(f"Get favorites response: {favorites_response.status_code}")
    print(f"Get favorites response body: {favorites_response.text}")
    
    if favorites_response.status_code == 200:
        favorites_data = favorites_response.json()
        favorites = favorites_data.get('favorites', [])
        print(f"Number of favorites returned: {len(favorites)}")
        
        for i, favorite in enumerate(favorites):
            print(f"  Favorite {i+1}: {favorite.get('name', 'N/A')} (ID: {favorite.get('id', 'N/A')})")

if __name__ == "__main__":
    debug_favorites()