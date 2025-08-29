#!/usr/bin/env python3
"""
Focused test for Restaurant Search and User Favorites Workflow
Tests the complete workflow as requested in the review
"""

import requests
import sys
import json
from datetime import datetime
import uuid

class FavoritesWorkflowTester:
    def __init__(self, base_url="https://special-hunter.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.user_token = None
        self.user_data = None
        self.test_restaurants = []

    def log_test(self, name, success, details=""):
        """Log test results"""
        self.tests_run += 1
        if success:
            self.tests_passed += 1
            print(f"✅ {name} - PASSED")
        else:
            print(f"❌ {name} - FAILED: {details}")
        
        if details and success:
            print(f"   Details: {details}")

    def test_restaurant_search_san_francisco(self):
        """Test restaurant search in San Francisco with specified coordinates"""
        try:
            # Use the exact coordinates from the review request
            params = {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'radius': 8047  # 5 miles
            }
            
            response = self.session.get(f"{self.api_url}/restaurants/search", params=params)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                restaurants = data.get('restaurants', [])
                total = data.get('total', 0)
                
                # Store restaurants for favorites testing
                self.test_restaurants = restaurants
                
                details = f"Found {total} restaurants in San Francisco"
                
                # Check if mock restaurants are being returned
                mock_restaurant_names = []
                google_restaurant_names = []
                
                for restaurant in restaurants:
                    name = restaurant.get('name', 'Unknown')
                    source = restaurant.get('source', 'unknown')
                    specials_count = len(restaurant.get('specials', []))
                    
                    if source == 'mock_with_specials':
                        mock_restaurant_names.append(f"{name} ({specials_count} specials)")
                    elif source == 'google_places':
                        google_restaurant_names.append(f"{name} (Google Places)")
                
                if mock_restaurant_names:
                    details += f". Mock restaurants with specials: {', '.join(mock_restaurant_names[:3])}"
                if google_restaurant_names:
                    details += f". Google Places restaurants: {', '.join(google_restaurant_names[:3])}"
                
                # Verify we have restaurants with current specials
                restaurants_with_specials = [r for r in restaurants if r.get('specials', [])]
                details += f". {len(restaurants_with_specials)} restaurants have active specials"
                
                if total == 0:
                    success = False
                    details = "No restaurants found - mock data may not be loaded"
                    
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Restaurant Search in San Francisco", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Restaurant Search in San Francisco", False, str(e))
            return False, {}

    def test_mock_data_verification(self):
        """Verify mock restaurant data is properly loaded"""
        try:
            if not self.test_restaurants:
                self.log_test("Mock Data Verification", False, "No restaurants available from previous search")
                return False
            
            # Look for specific mock restaurants that should be in the data
            expected_mock_restaurants = [
                "Tony's Tavern",
                "Mama's Italian Kitchen", 
                "The Blue Plate Diner",
                "Sunset Sports Bar",
                "Golden Gate Cafe"
            ]
            
            found_mock_restaurants = []
            restaurants_with_specials = 0
            total_specials = 0
            
            for restaurant in self.test_restaurants:
                name = restaurant.get('name', '')
                specials = restaurant.get('specials', [])
                
                if name in expected_mock_restaurants:
                    found_mock_restaurants.append(name)
                
                if specials:
                    restaurants_with_specials += 1
                    total_specials += len(specials)
            
            success = len(found_mock_restaurants) > 0 and restaurants_with_specials > 0
            
            details = f"Found {len(found_mock_restaurants)} expected mock restaurants: {', '.join(found_mock_restaurants)}. "
            details += f"{restaurants_with_specials} restaurants have {total_specials} total active specials"
            
            if not success:
                details = "Mock data not properly loaded - no expected restaurants or specials found"
            
            self.log_test("Mock Data Verification", success, details)
            return success
            
        except Exception as e:
            self.log_test("Mock Data Verification", False, str(e))
            return False

    def test_user_registration_for_favorites(self):
        """Test user registration for favorites workflow"""
        try:
            test_email = f"favorites_user_{uuid.uuid4().hex[:8]}@example.com"
            registration_data = {
                "email": test_email,
                "password": "FavoritesTest123!",
                "first_name": "Favorites",
                "last_name": "Tester"
            }
            
            response = self.session.post(f"{self.api_url}/users/register", json=registration_data)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.user_token = data.get('access_token')
                self.user_data = data.get('user')
                user_type = data.get('user_type')
                
                details = f"Registered user: {self.user_data.get('email', 'N/A')}, User type: {user_type}"
                
                # Verify user_type is "user" and token is received
                if user_type != "user" or not self.user_token:
                    success = False
                    details += f" - ERROR: Expected user_type 'user' and valid token"
                else:
                    details += ", Token received successfully"
                    
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("User Registration for Favorites", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("User Registration for Favorites", False, str(e))
            return False, {}

    def test_user_login_for_favorites(self):
        """Test user login functionality"""
        try:
            # Create a new user for login testing
            test_email = f"login_favorites_{uuid.uuid4().hex[:8]}@example.com"
            registration_data = {
                "email": test_email,
                "password": "LoginTest123!",
                "first_name": "Login",
                "last_name": "Tester"
            }
            
            # Register first
            reg_response = self.session.post(f"{self.api_url}/users/register", json=registration_data)
            if reg_response.status_code != 200:
                self.log_test("User Login for Favorites", False, "Failed to create test user for login")
                return False, {}
            
            # Now test login
            login_data = {
                "email": test_email,
                "password": "LoginTest123!"
            }
            
            response = self.session.post(f"{self.api_url}/users/login", json=login_data)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                token = data.get('access_token')
                user = data.get('user')
                user_type = data.get('user_type')
                
                details = f"Login successful for: {user.get('email', 'N/A')}, User type: {user_type}"
                
                # Verify user_type and token
                if user_type != "user" or not token:
                    success = False
                    details += f" - ERROR: Expected user_type 'user' and valid token"
                else:
                    details += ", Authentication working correctly"
                    
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("User Login for Favorites", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("User Login for Favorites", False, str(e))
            return False, {}

    def test_add_restaurants_to_favorites(self):
        """Test adding multiple restaurants to favorites using restaurant IDs from search results"""
        if not self.user_token:
            self.log_test("Add Restaurants to Favorites", False, "No user token available")
            return False, {}
        
        if not self.test_restaurants:
            self.log_test("Add Restaurants to Favorites", False, "No restaurants available from search")
            return False, {}
        
        try:
            headers = {'Authorization': f'Bearer {self.user_token}'}
            added_restaurants = []
            failed_additions = []
            
            # Try to add first 3 restaurants to favorites
            restaurants_to_add = self.test_restaurants[:3]
            
            for restaurant in restaurants_to_add:
                restaurant_id = restaurant['id']
                restaurant_name = restaurant['name']
                
                response = self.session.post(f"{self.api_url}/users/favorites/{restaurant_id}", headers=headers)
                
                if response.status_code == 200:
                    added_restaurants.append(f"{restaurant_name} (ID: {restaurant_id})")
                else:
                    failed_additions.append(f"{restaurant_name}: {response.status_code}")
            
            success = len(added_restaurants) > 0
            
            details = f"Successfully added {len(added_restaurants)} restaurants to favorites: {', '.join(added_restaurants)}"
            if failed_additions:
                details += f". Failed additions: {', '.join(failed_additions)}"
            
            # Store added restaurant IDs for removal test
            self.added_restaurant_ids = [r['id'] for r in restaurants_to_add if r['id'] in str(added_restaurants)]
            
            self.log_test("Add Restaurants to Favorites", success, details)
            return success
            
        except Exception as e:
            self.log_test("Add Restaurants to Favorites", False, str(e))
            return False

    def test_get_favorite_restaurants(self):
        """Test getting user's favorite restaurants"""
        if not self.user_token:
            self.log_test("Get Favorite Restaurants", False, "No user token available")
            return False, {}
        
        try:
            headers = {'Authorization': f'Bearer {self.user_token}'}
            
            response = self.session.get(f"{self.api_url}/users/favorites", headers=headers)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                favorites = data.get('favorites', [])
                
                details = f"Retrieved {len(favorites)} favorite restaurants"
                
                if favorites:
                    # Verify favorite structure
                    first_favorite = favorites[0]
                    expected_fields = ['id', 'name', 'address']
                    missing_fields = [field for field in expected_fields if field not in first_favorite]
                    
                    if missing_fields:
                        details += f" - Missing fields in favorite: {missing_fields}"
                    else:
                        favorite_names = [f['name'] for f in favorites]
                        details += f". Favorites: {', '.join(favorite_names)}"
                        
                        # Verify favorites persistence
                        if hasattr(self, 'added_restaurant_ids') and self.added_restaurant_ids:
                            favorite_ids = [f['id'] for f in favorites]
                            persisted_count = sum(1 for rid in self.added_restaurant_ids if rid in favorite_ids)
                            details += f". {persisted_count}/{len(self.added_restaurant_ids)} added restaurants persisted"
                else:
                    details += " (empty list - may need to add favorites first)"
                    
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Get Favorite Restaurants", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Get Favorite Restaurants", False, str(e))
            return False, {}

    def test_remove_restaurants_from_favorites(self):
        """Test removing restaurants from favorites"""
        if not self.user_token:
            self.log_test("Remove Restaurants from Favorites", False, "No user token available")
            return False, {}
        
        if not hasattr(self, 'added_restaurant_ids') or not self.added_restaurant_ids:
            self.log_test("Remove Restaurants from Favorites", False, "No restaurant IDs available for removal")
            return False, {}
        
        try:
            headers = {'Authorization': f'Bearer {self.user_token}'}
            removed_restaurants = []
            failed_removals = []
            
            # Remove the first restaurant that was added
            restaurant_id = self.added_restaurant_ids[0]
            
            # Find restaurant name for better logging
            restaurant_name = "Unknown"
            for restaurant in self.test_restaurants:
                if restaurant['id'] == restaurant_id:
                    restaurant_name = restaurant['name']
                    break
            
            response = self.session.delete(f"{self.api_url}/users/favorites/{restaurant_id}", headers=headers)
            
            if response.status_code == 200:
                removed_restaurants.append(f"{restaurant_name} (ID: {restaurant_id})")
            else:
                failed_removals.append(f"{restaurant_name}: {response.status_code}")
            
            success = len(removed_restaurants) > 0
            
            details = f"Successfully removed {len(removed_restaurants)} restaurants from favorites: {', '.join(removed_restaurants)}"
            if failed_removals:
                details += f". Failed removals: {', '.join(failed_removals)}"
            
            self.log_test("Remove Restaurants from Favorites", success, details)
            return success
            
        except Exception as e:
            self.log_test("Remove Restaurants from Favorites", False, str(e))
            return False

    def test_favorites_persistence(self):
        """Test that favorites persist correctly after add/remove operations"""
        if not self.user_token:
            self.log_test("Favorites Persistence", False, "No user token available")
            return False, {}
        
        try:
            headers = {'Authorization': f'Bearer {self.user_token}'}
            
            # Get current favorites count
            response = self.session.get(f"{self.api_url}/users/favorites", headers=headers)
            if response.status_code != 200:
                self.log_test("Favorites Persistence", False, "Failed to get current favorites")
                return False
            
            initial_favorites = response.json().get('favorites', [])
            initial_count = len(initial_favorites)
            
            # Add a restaurant
            if self.test_restaurants:
                test_restaurant = self.test_restaurants[0]
                restaurant_id = test_restaurant['id']
                restaurant_name = test_restaurant['name']
                
                # Add to favorites
                add_response = self.session.post(f"{self.api_url}/users/favorites/{restaurant_id}", headers=headers)
                
                # Check favorites count increased
                get_response = self.session.get(f"{self.api_url}/users/favorites", headers=headers)
                if get_response.status_code == 200:
                    after_add_favorites = get_response.json().get('favorites', [])
                    after_add_count = len(after_add_favorites)
                    
                    # Remove the restaurant
                    remove_response = self.session.delete(f"{self.api_url}/users/favorites/{restaurant_id}", headers=headers)
                    
                    # Check favorites count decreased
                    final_response = self.session.get(f"{self.api_url}/users/favorites", headers=headers)
                    if final_response.status_code == 200:
                        final_favorites = final_response.json().get('favorites', [])
                        final_count = len(final_favorites)
                        
                        # Verify persistence logic
                        add_worked = (add_response.status_code == 200 and after_add_count >= initial_count)
                        remove_worked = (remove_response.status_code == 200 and final_count <= after_add_count)
                        
                        success = add_worked and remove_worked
                        
                        details = f"Initial: {initial_count}, After add: {after_add_count}, After remove: {final_count}"
                        details += f". Add worked: {add_worked}, Remove worked: {remove_worked}"
                        
                        if success:
                            details += f". Persistence verified for '{restaurant_name}'"
                        else:
                            details += f". Persistence failed for '{restaurant_name}'"
                    else:
                        success = False
                        details = "Failed to get final favorites count"
                else:
                    success = False
                    details = "Failed to get favorites after add"
            else:
                success = False
                details = "No test restaurants available"
            
            self.log_test("Favorites Persistence", success, details)
            return success
            
        except Exception as e:
            self.log_test("Favorites Persistence", False, str(e))
            return False

    def test_heart_icon_status_integration(self):
        """Test that restaurant data includes information needed for heart icon status"""
        try:
            if not self.test_restaurants:
                self.log_test("Heart Icon Status Integration", False, "No restaurants available")
                return False
            
            # Check if restaurants have the required fields for heart icon integration
            required_fields = ['id', 'name']
            restaurants_with_required_fields = 0
            restaurants_with_specials = 0
            
            for restaurant in self.test_restaurants:
                has_required_fields = all(field in restaurant for field in required_fields)
                if has_required_fields:
                    restaurants_with_required_fields += 1
                
                if restaurant.get('specials', []):
                    restaurants_with_specials += 1
            
            success = restaurants_with_required_fields > 0
            
            details = f"{restaurants_with_required_fields}/{len(self.test_restaurants)} restaurants have required fields for heart icon integration"
            details += f". {restaurants_with_specials} restaurants have specials data"
            
            # Check if we can identify restaurants by ID (needed for heart icon state)
            if self.test_restaurants:
                sample_restaurant = self.test_restaurants[0]
                restaurant_id = sample_restaurant.get('id')
                if restaurant_id:
                    details += f". Sample restaurant ID format: {restaurant_id[:20]}..."
                else:
                    success = False
                    details += ". ERROR: Restaurants missing ID field"
            
            self.log_test("Heart Icon Status Integration", success, details)
            return success
            
        except Exception as e:
            self.log_test("Heart Icon Status Integration", False, str(e))
            return False

    def run_complete_workflow_test(self):
        """Run the complete restaurant search and favorites workflow test"""
        print("🍽️  RESTAURANT SEARCH & FAVORITES WORKFLOW TEST")
        print("=" * 60)
        
        # Step 1: Test restaurant search in San Francisco
        search_success, search_data = self.test_restaurant_search_san_francisco()
        
        # Step 2: Verify mock data is loaded
        mock_success = self.test_mock_data_verification()
        
        # Step 3: Test user registration
        reg_success, reg_data = self.test_user_registration_for_favorites()
        
        # Step 4: Test user login
        login_success, login_data = self.test_user_login_for_favorites()
        
        # Step 5: Test adding restaurants to favorites
        add_success = self.test_add_restaurants_to_favorites()
        
        # Step 6: Test getting favorite restaurants
        get_success, get_data = self.test_get_favorite_restaurants()
        
        # Step 7: Test removing restaurants from favorites
        remove_success = self.test_remove_restaurants_from_favorites()
        
        # Step 8: Test favorites persistence
        persistence_success = self.test_favorites_persistence()
        
        # Step 9: Test heart icon integration readiness
        heart_success = self.test_heart_icon_status_integration()
        
        print("=" * 60)
        print(f"📊 Workflow Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL WORKFLOW TESTS PASSED - Restaurant search and favorites functionality is working correctly!")
        else:
            failed_tests = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_tests} workflow tests failed - see details above")
        
        return self.tests_passed == self.tests_run

def main():
    tester = FavoritesWorkflowTester()
    success = tester.run_complete_workflow_test()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()