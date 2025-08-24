#!/usr/bin/env python3
"""
Test the favorites fix by modifying the backend to handle Google Places restaurants
"""

import requests
import sys
import json
import uuid

class FavoritesFixTester:
    def __init__(self, base_url="https://special-finder.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.user_token = None
        
    def test_complete_workflow(self):
        """Test the complete favorites workflow after fix"""
        print("🧪 TESTING COMPLETE FAVORITES WORKFLOW")
        print("=" * 60)
        
        # Step 1: Register user
        success = self.register_test_user()
        if not success:
            return False
            
        # Step 2: Get restaurants from search
        restaurants = self.get_restaurants_from_search()
        if not restaurants:
            return False
            
        # Step 3: Add both Google Places and database restaurants to favorites
        google_restaurant = None
        db_restaurant = None
        
        for restaurant in restaurants:
            if restaurant.get('id', '').startswith('google_'):
                google_restaurant = restaurant
            elif restaurant.get('source') == 'mock_with_specials':
                db_restaurant = restaurant
            
            if google_restaurant and db_restaurant:
                break
        
        # Test adding Google Places restaurant
        if google_restaurant:
            print(f"\n🔍 Testing Google Places Restaurant: {google_restaurant['name']}")
            print(f"   ID: {google_restaurant['id']}")
            success = self.add_to_favorites(google_restaurant['id'])
            if success:
                print("   ✅ Added to favorites successfully")
            else:
                print("   ❌ Failed to add to favorites")
        
        # Test adding database restaurant
        if db_restaurant:
            print(f"\n🔍 Testing Database Restaurant: {db_restaurant['name']}")
            print(f"   ID: {db_restaurant['id']}")
            success = self.add_to_favorites(db_restaurant['id'])
            if success:
                print("   ✅ Added to favorites successfully")
            else:
                print("   ❌ Failed to add to favorites")
        
        # Step 4: Get favorites and check results
        print(f"\n📋 Retrieving Favorites:")
        favorites = self.get_favorites()
        
        print(f"   Found {len(favorites)} favorites:")
        for i, fav in enumerate(favorites):
            print(f"   {i+1}. {fav.get('name', 'Unknown')} (ID: {fav.get('id', 'No ID')})")
        
        # Analyze results
        google_found = any(fav.get('id') == google_restaurant['id'] for fav in favorites) if google_restaurant else False
        db_found = any(fav.get('id') == db_restaurant['id'] for fav in favorites) if db_restaurant else False
        
        print(f"\n📊 RESULTS:")
        if google_restaurant:
            print(f"   Google Places restaurant found in favorites: {'✅' if google_found else '❌'}")
        if db_restaurant:
            print(f"   Database restaurant found in favorites: {'✅' if db_found else '❌'}")
        
        return google_found or db_found
    
    def register_test_user(self):
        """Register a test user"""
        try:
            test_email = f"fix_test_{uuid.uuid4().hex[:8]}@example.com"
            registration_data = {
                "email": test_email,
                "password": "FixTest123!",
                "first_name": "Fix",
                "last_name": "Test"
            }
            
            response = self.session.post(f"{self.api_url}/users/register", json=registration_data)
            if response.status_code == 200:
                data = response.json()
                self.user_token = data.get('access_token')
                print(f"✅ User registered: {test_email}")
                return True
            else:
                print(f"❌ Registration failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Registration error: {e}")
            return False
    
    def get_restaurants_from_search(self):
        """Get restaurants from search API"""
        try:
            params = {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'radius': 8047
            }
            
            response = self.session.get(f"{self.api_url}/restaurants/search", params=params)
            if response.status_code == 200:
                data = response.json()
                restaurants = data.get('restaurants', [])
                print(f"✅ Found {len(restaurants)} restaurants from search")
                return restaurants
            else:
                print(f"❌ Search failed: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ Search error: {e}")
            return []
    
    def add_to_favorites(self, restaurant_id):
        """Add restaurant to favorites"""
        if not self.user_token:
            return False
            
        try:
            headers = {'Authorization': f'Bearer {self.user_token}'}
            response = self.session.post(f"{self.api_url}/users/favorites/{restaurant_id}", headers=headers)
            return response.status_code == 200
        except Exception as e:
            print(f"   Error adding to favorites: {e}")
            return False
    
    def get_favorites(self):
        """Get user's favorites"""
        if not self.user_token:
            return []
            
        try:
            headers = {'Authorization': f'Bearer {self.user_token}'}
            response = self.session.get(f"{self.api_url}/users/favorites", headers=headers)
            if response.status_code == 200:
                data = response.json()
                return data.get('favorites', [])
            else:
                print(f"   Error getting favorites: {response.status_code}")
                return []
        except Exception as e:
            print(f"   Error getting favorites: {e}")
            return []

def main():
    """Main test execution"""
    print("🚀 TESTING FAVORITES FUNCTIONALITY FIX")
    print("=" * 60)
    
    tester = FavoritesFixTester()
    success = tester.test_complete_workflow()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ FAVORITES FIX TEST PASSED")
        print("At least one type of restaurant was found in favorites.")
    else:
        print("❌ FAVORITES FIX TEST FAILED")
        print("No restaurants were found in favorites - issue still exists.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)