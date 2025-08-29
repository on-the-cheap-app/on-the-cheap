#!/usr/bin/env python3
"""
Favorites Functionality Debug Test
Specifically designed to debug the user favorites workflow and identify data format issues
"""

import requests
import sys
import json
from datetime import datetime
import uuid

class FavoritesDebugTester:
    def __init__(self, base_url="https://resto-specials.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.user_token = None
        self.user_data = None
        
    def log_test(self, name, success, details=""):
        """Log test results"""
        if success:
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        if details and success:
            print(f"   Details: {details}")

    def debug_favorites_workflow(self):
        """Complete favorites workflow debugging as requested"""
        print("🔍 DEBUGGING FAVORITES FUNCTIONALITY - COMPLETE WORKFLOW")
        print("=" * 80)
        
        # Step 1: Create/login a test user
        print("\n📝 STEP 1: User Registration and Login")
        success = self.test_user_registration_and_login()
        if not success:
            print("❌ Cannot proceed without user authentication")
            return False
            
        # Step 2: Search for restaurants and examine ID format
        print("\n🔍 STEP 2: Restaurant Search - Examining ID Format")
        restaurants = self.test_restaurant_search_and_examine_ids()
        if not restaurants:
            print("❌ Cannot proceed without restaurant data")
            return False
            
        # Step 3: Add 2-3 restaurants to favorites
        print("\n❤️ STEP 3: Adding Restaurants to Favorites")
        added_restaurants = self.test_add_multiple_favorites(restaurants[:3])
        
        # Step 4: Retrieve favorites and examine data format
        print("\n📋 STEP 4: Retrieving Favorites - Data Format Analysis")
        favorites_data = self.test_get_favorites_and_analyze_format()
        
        # Step 5: Compare ID formats and identify mismatches
        print("\n🔍 STEP 5: ID Format Comparison and Mismatch Analysis")
        self.analyze_id_format_mismatches(restaurants, favorites_data, added_restaurants)
        
        print("\n" + "=" * 80)
        print("🏁 FAVORITES DEBUGGING COMPLETE")
        return True

    def test_user_registration_and_login(self):
        """Test user registration and login"""
        try:
            # Register a new user
            test_email = f"favorites_debug_{uuid.uuid4().hex[:8]}@example.com"
            registration_data = {
                "email": test_email,
                "password": "DebugPassword123!",
                "first_name": "Debug",
                "last_name": "User"
            }
            
            response = self.session.post(f"{self.api_url}/users/register", json=registration_data)
            if response.status_code == 200:
                data = response.json()
                self.user_token = data.get('access_token')
                self.user_data = data.get('user')
                user_type = data.get('user_type')
                
                self.log_test("User Registration", True, 
                    f"Email: {test_email}, User Type: {user_type}, Token: {'✓' if self.user_token else '✗'}")
                
                # Test login with same credentials
                login_data = {
                    "email": test_email,
                    "password": "DebugPassword123!"
                }
                
                login_response = self.session.post(f"{self.api_url}/users/login", json=login_data)
                if login_response.status_code == 200:
                    login_data_resp = login_response.json()
                    self.log_test("User Login", True, 
                        f"Login successful, Token: {'✓' if login_data_resp.get('access_token') else '✗'}")
                    return True
                else:
                    self.log_test("User Login", False, f"Status: {login_response.status_code}")
                    return False
            else:
                self.log_test("User Registration", False, f"Status: {response.status_code}, Response: {response.text[:200]}")
                return False
                
        except Exception as e:
            self.log_test("User Registration and Login", False, str(e))
            return False

    def test_restaurant_search_and_examine_ids(self):
        """Search for restaurants and examine ID formats"""
        try:
            # Search in San Francisco
            params = {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'radius': 8047  # 5 miles
            }
            
            response = self.session.get(f"{self.api_url}/restaurants/search", params=params)
            if response.status_code == 200:
                data = response.json()
                restaurants = data.get('restaurants', [])
                
                print(f"   Found {len(restaurants)} restaurants")
                
                # Examine ID formats
                id_formats = {}
                for i, restaurant in enumerate(restaurants[:5]):  # Examine first 5
                    restaurant_id = restaurant.get('id', 'NO_ID')
                    restaurant_name = restaurant.get('name', 'Unknown')
                    source = restaurant.get('source', 'unknown')
                    
                    # Categorize ID format
                    if restaurant_id.startswith('google_'):
                        id_type = 'Google Places ID'
                    elif len(restaurant_id) == 36 and '-' in restaurant_id:  # UUID format
                        id_type = 'UUID'
                    else:
                        id_type = 'Other'
                    
                    if id_type not in id_formats:
                        id_formats[id_type] = []
                    id_formats[id_type].append({
                        'id': restaurant_id,
                        'name': restaurant_name,
                        'source': source
                    })
                    
                    print(f"   Restaurant {i+1}: {restaurant_name}")
                    print(f"      ID: {restaurant_id}")
                    print(f"      ID Type: {id_type}")
                    print(f"      Source: {source}")
                    print()
                
                # Summary of ID formats
                print("   📊 ID FORMAT SUMMARY:")
                for id_type, examples in id_formats.items():
                    print(f"      {id_type}: {len(examples)} restaurants")
                    if examples:
                        print(f"         Example: {examples[0]['id']}")
                
                self.log_test("Restaurant Search and ID Examination", True, 
                    f"Found {len(restaurants)} restaurants with {len(id_formats)} different ID formats")
                return restaurants
            else:
                self.log_test("Restaurant Search", False, f"Status: {response.status_code}")
                return []
                
        except Exception as e:
            self.log_test("Restaurant Search and ID Examination", False, str(e))
            return []

    def test_add_multiple_favorites(self, restaurants):
        """Add multiple restaurants to favorites and track the process"""
        if not self.user_token:
            print("   ❌ No user token available")
            return []
        
        headers = {'Authorization': f'Bearer {self.user_token}'}
        added_restaurants = []
        
        for i, restaurant in enumerate(restaurants):
            try:
                restaurant_id = restaurant.get('id')
                restaurant_name = restaurant.get('name', 'Unknown')
                
                print(f"   Adding Restaurant {i+1}: {restaurant_name}")
                print(f"      ID: {restaurant_id}")
                
                # Add to favorites
                response = self.session.post(f"{self.api_url}/users/favorites/{restaurant_id}", headers=headers)
                
                if response.status_code == 200:
                    response_data = response.json()
                    message = response_data.get('message', 'No message')
                    print(f"      ✅ Added successfully: {message}")
                    added_restaurants.append({
                        'id': restaurant_id,
                        'name': restaurant_name,
                        'original_data': restaurant
                    })
                else:
                    print(f"      ❌ Failed to add: Status {response.status_code}")
                    print(f"         Response: {response.text[:200]}")
                
                print()
                
            except Exception as e:
                print(f"      ❌ Exception adding restaurant: {str(e)}")
        
        self.log_test("Add Multiple Favorites", len(added_restaurants) > 0, 
            f"Successfully added {len(added_restaurants)}/{len(restaurants)} restaurants to favorites")
        
        return added_restaurants

    def test_get_favorites_and_analyze_format(self):
        """Retrieve favorites and analyze the data format"""
        if not self.user_token:
            print("   ❌ No user token available")
            return {}
        
        try:
            headers = {'Authorization': f'Bearer {self.user_token}'}
            
            response = self.session.get(f"{self.api_url}/users/favorites", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                favorites = data.get('favorites', [])
                
                print(f"   Retrieved {len(favorites)} favorites from API")
                
                # Analyze each favorite's data structure
                for i, favorite in enumerate(favorites):
                    print(f"   Favorite {i+1}:")
                    print(f"      ID: {favorite.get('id', 'NO_ID')}")
                    print(f"      Name: {favorite.get('name', 'NO_NAME')}")
                    print(f"      Address: {favorite.get('address', 'NO_ADDRESS')}")
                    print(f"      Rating: {favorite.get('rating', 'NO_RATING')}")
                    print(f"      Cuisine: {favorite.get('cuisine_type', 'NO_CUISINE')}")
                    print(f"      Specials Count: {favorite.get('specials_count', 'NO_COUNT')}")
                    
                    # Check for any additional fields
                    expected_fields = {'id', 'name', 'address', 'rating', 'cuisine_type', 'specials_count'}
                    actual_fields = set(favorite.keys())
                    extra_fields = actual_fields - expected_fields
                    missing_fields = expected_fields - actual_fields
                    
                    if extra_fields:
                        print(f"      Extra fields: {list(extra_fields)}")
                    if missing_fields:
                        print(f"      Missing fields: {list(missing_fields)}")
                    print()
                
                # Raw JSON structure analysis
                print("   📋 RAW FAVORITES API RESPONSE STRUCTURE:")
                print(f"      Response keys: {list(data.keys())}")
                if favorites:
                    print(f"      First favorite keys: {list(favorites[0].keys())}")
                    print(f"      First favorite raw data: {json.dumps(favorites[0], indent=8)}")
                
                self.log_test("Get Favorites and Analyze Format", True, 
                    f"Retrieved {len(favorites)} favorites with detailed format analysis")
                
                return data
            else:
                print(f"   ❌ Failed to retrieve favorites: Status {response.status_code}")
                print(f"      Response: {response.text[:200]}")
                self.log_test("Get Favorites", False, f"Status: {response.status_code}")
                return {}
                
        except Exception as e:
            self.log_test("Get Favorites and Analyze Format", False, str(e))
            return {}

    def analyze_id_format_mismatches(self, search_restaurants, favorites_data, added_restaurants):
        """Analyze ID format mismatches between search results and favorites"""
        print("   🔍 DETAILED ID FORMAT MISMATCH ANALYSIS")
        print("   " + "-" * 60)
        
        favorites = favorites_data.get('favorites', [])
        
        # Create lookup maps
        search_ids = {r.get('id'): r for r in search_restaurants}
        favorite_ids = {f.get('id'): f for f in favorites}
        added_ids = {a.get('id'): a for a in added_restaurants}
        
        print(f"   📊 SUMMARY:")
        print(f"      Restaurants from search: {len(search_restaurants)}")
        print(f"      Restaurants added to favorites: {len(added_restaurants)}")
        print(f"      Favorites retrieved from API: {len(favorites)}")
        print()
        
        # Check if added restaurants appear in favorites
        print("   🔍 MATCHING ANALYSIS:")
        matches_found = 0
        mismatches = []
        
        for added_restaurant in added_restaurants:
            added_id = added_restaurant.get('id')
            added_name = added_restaurant.get('name')
            
            # Check if this ID exists in favorites
            if added_id in favorite_ids:
                favorite = favorite_ids[added_id]
                matches_found += 1
                print(f"      ✅ MATCH FOUND:")
                print(f"         Added ID: {added_id}")
                print(f"         Found in favorites: {favorite.get('id')}")
                print(f"         Name match: {added_name} == {favorite.get('name')}")
            else:
                mismatches.append({
                    'added_id': added_id,
                    'added_name': added_name,
                    'found_in_favorites': False
                })
                print(f"      ❌ MISMATCH:")
                print(f"         Added ID: {added_id}")
                print(f"         Added Name: {added_name}")
                print(f"         Found in favorites: NO")
        
        print()
        print(f"   📈 RESULTS:")
        print(f"      Matches found: {matches_found}/{len(added_restaurants)}")
        print(f"      Mismatches: {len(mismatches)}")
        
        if mismatches:
            print(f"   ❌ CRITICAL ISSUE IDENTIFIED:")
            print(f"      {len(mismatches)} restaurants were added to favorites but don't appear in the favorites list!")
            print(f"      This suggests a data format or storage issue.")
            
            # Check if favorites contain different IDs
            if favorites:
                print(f"   🔍 FAVORITES CONTAIN DIFFERENT IDS:")
                for fav in favorites:
                    fav_id = fav.get('id')
                    if fav_id not in added_ids:
                        print(f"      Unexpected favorite ID: {fav_id} (Name: {fav.get('name')})")
        
        # Analyze ID format patterns
        print(f"   🔍 ID FORMAT PATTERN ANALYSIS:")
        
        search_id_patterns = self.analyze_id_patterns([r.get('id') for r in search_restaurants])
        favorite_id_patterns = self.analyze_id_patterns([f.get('id') for f in favorites])
        
        print(f"      Search Results ID Patterns: {search_id_patterns}")
        print(f"      Favorites ID Patterns: {favorite_id_patterns}")
        
        # Check for format conversion issues
        if search_id_patterns != favorite_id_patterns:
            print(f"   ⚠️ ID FORMAT MISMATCH DETECTED:")
            print(f"      Search results use: {search_id_patterns}")
            print(f"      Favorites use: {favorite_id_patterns}")
            print(f"      This could be the root cause of the favorites issue!")
        
        return {
            'matches_found': matches_found,
            'total_added': len(added_restaurants),
            'mismatches': mismatches,
            'search_patterns': search_id_patterns,
            'favorite_patterns': favorite_id_patterns
        }

    def analyze_id_patterns(self, ids):
        """Analyze ID patterns to identify format types"""
        patterns = {}
        
        for id_val in ids:
            if not id_val:
                pattern = 'null'
            elif id_val.startswith('google_'):
                pattern = 'google_prefixed'
            elif len(id_val) == 36 and id_val.count('-') == 4:
                pattern = 'uuid'
            elif len(id_val) > 20 and '_' in id_val:
                pattern = 'compound_id'
            else:
                pattern = 'other'
            
            patterns[pattern] = patterns.get(pattern, 0) + 1
        
        return patterns

    def test_api_response_formats(self):
        """Test and compare API response formats for debugging"""
        print("\n🔍 API RESPONSE FORMAT TESTING")
        print("=" * 50)
        
        # Test restaurant search response format
        print("📋 Restaurant Search API Response Format:")
        try:
            params = {'latitude': 37.7749, 'longitude': -122.4194, 'radius': 8047}
            response = self.session.get(f"{self.api_url}/restaurants/search", params=params)
            
            if response.status_code == 200:
                data = response.json()
                restaurants = data.get('restaurants', [])
                if restaurants:
                    first_restaurant = restaurants[0]
                    print(f"   Sample restaurant object keys: {list(first_restaurant.keys())}")
                    print(f"   Sample restaurant ID: {first_restaurant.get('id')}")
                    print(f"   Sample restaurant ID type: {type(first_restaurant.get('id'))}")
                    print(f"   Full sample restaurant: {json.dumps(first_restaurant, indent=4)}")
        except Exception as e:
            print(f"   Error testing search API: {e}")
        
        print()
        
        # Test favorites API response format
        if self.user_token:
            print("❤️ Favorites API Response Format:")
            try:
                headers = {'Authorization': f'Bearer {self.user_token}'}
                response = self.session.get(f"{self.api_url}/users/favorites", headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    favorites = data.get('favorites', [])
                    print(f"   Favorites response keys: {list(data.keys())}")
                    if favorites:
                        first_favorite = favorites[0]
                        print(f"   Sample favorite object keys: {list(first_favorite.keys())}")
                        print(f"   Sample favorite ID: {first_favorite.get('id')}")
                        print(f"   Sample favorite ID type: {type(first_favorite.get('id'))}")
                        print(f"   Full sample favorite: {json.dumps(first_favorite, indent=4)}")
                    else:
                        print("   No favorites found in response")
                else:
                    print(f"   Favorites API error: {response.status_code}")
            except Exception as e:
                print(f"   Error testing favorites API: {e}")

def main():
    """Main test execution"""
    print("🚀 STARTING FAVORITES FUNCTIONALITY DEBUG TEST")
    print("=" * 80)
    
    tester = FavoritesDebugTester()
    
    # Run the complete debugging workflow
    success = tester.debug_favorites_workflow()
    
    # Additional API format testing
    tester.test_api_response_formats()
    
    print("\n" + "=" * 80)
    if success:
        print("✅ FAVORITES DEBUG TEST COMPLETED")
        print("Check the detailed output above for ID format mismatches and data issues.")
    else:
        print("❌ FAVORITES DEBUG TEST FAILED")
        print("Unable to complete the full debugging workflow.")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)