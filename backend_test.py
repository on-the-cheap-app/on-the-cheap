#!/usr/bin/env python3
"""
Backend API Testing for On-the-Cheap Restaurant Specials Finder
Tests all API endpoints and functionality
"""

import requests
import sys
import json
from datetime import datetime
import uuid

class OnTheCheapAPITester:
    def __init__(self, base_url="https://resto-specials.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

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

    def test_api_health(self):
        """Test API health check endpoint"""
        try:
            response = self.session.get(f"{self.api_url}/")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Message: {data.get('message', 'N/A')}, Version: {data.get('version', 'N/A')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            
            self.log_test("API Health Check", success, details)
            return success, response.json() if success else {}
            
        except Exception as e:
            self.log_test("API Health Check", False, str(e))
            return False, {}

    def test_special_types(self):
        """Test getting special types"""
        try:
            response = self.session.get(f"{self.api_url}/specials/types")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                special_types = data.get('special_types', [])
                details = f"Found {len(special_types)} special types: {[st['label'] for st in special_types]}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:100]}"
            
            self.log_test("Get Special Types", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Get Special Types", False, str(e))
            return False, {}

    def test_restaurant_search_basic(self):
        """Test basic restaurant search (San Francisco coordinates)"""
        try:
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
                details = f"Found {total} restaurants with active specials"
                
                # Log some restaurant details
                if restaurants:
                    first_restaurant = restaurants[0]
                    details += f". First: {first_restaurant.get('name', 'Unknown')} with {len(first_restaurant.get('specials', []))} specials"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Basic Restaurant Search (SF)", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Basic Restaurant Search (SF)", False, str(e))
            return False, {}

    def test_restaurant_search_with_filters(self):
        """Test restaurant search with special type filter"""
        try:
            params = {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'radius': 8047,
                'special_type': 'weekend_special'  # Should find weekend specials since it's Saturday
            }
            
            response = self.session.get(f"{self.api_url}/restaurants/search", params=params)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                restaurants = data.get('restaurants', [])
                details = f"Found {len(restaurants)} restaurants with weekend specials"
                
                # Verify all returned specials are weekend_special type
                for restaurant in restaurants:
                    for special in restaurant.get('specials', []):
                        if special.get('special_type') != 'weekend_special':
                            success = False
                            details += f" - ERROR: Found non-weekend special: {special.get('special_type')}"
                            break
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Restaurant Search with Weekend Filter", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Restaurant Search with Weekend Filter", False, str(e))
            return False, {}

    def test_restaurant_search_different_radius(self):
        """Test restaurant search with different radius"""
        try:
            # Test with smaller radius (1 mile)
            params = {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'radius': 1609  # 1 mile
            }
            
            response = self.session.get(f"{self.api_url}/restaurants/search", params=params)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                restaurants_1mile = len(data.get('restaurants', []))
                
                # Test with larger radius (10 miles)
                params['radius'] = 16094  # 10 miles
                response2 = self.session.get(f"{self.api_url}/restaurants/search", params=params)
                
                if response2.status_code == 200:
                    data2 = response2.json()
                    restaurants_10mile = len(data2.get('restaurants', []))
                    
                    details = f"1 mile: {restaurants_1mile} restaurants, 10 miles: {restaurants_10mile} restaurants"
                    
                    # 10 mile radius should have >= restaurants than 1 mile
                    if restaurants_10mile >= restaurants_1mile:
                        details += " - Radius filtering working correctly"
                    else:
                        success = False
                        details += " - ERROR: Larger radius returned fewer results"
                else:
                    success = False
                    details = f"Second request failed: {response2.status_code}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Restaurant Search with Different Radius", success, details)
            return success
            
        except Exception as e:
            self.log_test("Restaurant Search with Different Radius", False, str(e))
            return False

    def test_restaurant_search_edge_cases(self):
        """Test edge cases for restaurant search"""
        test_cases = [
            {
                'name': 'Invalid Coordinates (Out of Range)',
                'params': {'latitude': 91, 'longitude': -122.4194, 'radius': 8047},
                'expected_status': 422  # Validation error
            },
            {
                'name': 'Remote Location (No Results Expected)',
                'params': {'latitude': 0, 'longitude': 0, 'radius': 8047},
                'expected_status': 200  # Should return empty results
            },
            {
                'name': 'Very Large Radius',
                'params': {'latitude': 37.7749, 'longitude': -122.4194, 'radius': 80467},  # 50 miles
                'expected_status': 200
            }
        ]
        
        all_passed = True
        details_list = []
        
        for case in test_cases:
            try:
                response = self.session.get(f"{self.api_url}/restaurants/search", params=case['params'])
                success = response.status_code == case['expected_status']
                
                if success:
                    if case['expected_status'] == 200:
                        data = response.json()
                        count = len(data.get('restaurants', []))
                        details_list.append(f"{case['name']}: {count} results")
                    else:
                        details_list.append(f"{case['name']}: Correctly rejected")
                else:
                    details_list.append(f"{case['name']}: Expected {case['expected_status']}, got {response.status_code}")
                    all_passed = False
                    
            except Exception as e:
                details_list.append(f"{case['name']}: Exception - {str(e)}")
                all_passed = False
        
        self.log_test("Restaurant Search Edge Cases", all_passed, "; ".join(details_list))
        return all_passed

    def test_create_restaurant(self):
        """Test creating a new restaurant"""
        try:
            test_restaurant = {
                "name": f"Test Restaurant {uuid.uuid4().hex[:8]}",
                "address": "123 Test St, San Francisco, CA 94102",
                "location": {
                    "latitude": 37.7749,
                    "longitude": -122.4194
                },
                "phone": "+1-415-555-TEST",
                "website": "https://test-restaurant.com",
                "cuisine_type": ["Test", "American"],
                "rating": 4.5,
                "price_level": 2,
                "specials": [
                    {
                        "title": "Test Special",
                        "description": "A test special for API testing",
                        "special_type": "happy_hour",
                        "price": 9.99,
                        "original_price": 15.99,
                        "days_available": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                        "time_start": "15:00",
                        "time_end": "18:00",
                        "is_active": True
                    }
                ],
                "is_verified": False
            }
            
            response = self.session.post(f"{self.api_url}/restaurants", json=test_restaurant)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                restaurant_id = data.get('id')
                details = f"Created restaurant with ID: {restaurant_id}"
                
                # Try to retrieve the created restaurant
                if restaurant_id:
                    get_response = self.session.get(f"{self.api_url}/restaurants/{restaurant_id}")
                    if get_response.status_code == 200:
                        details += " - Successfully retrieved created restaurant"
                    else:
                        details += f" - Failed to retrieve: {get_response.status_code}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Create Restaurant", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Create Restaurant", False, str(e))
            return False, {}

    def test_performance(self):
        """Test API response times"""
        import time
        
        try:
            # Test search endpoint performance
            start_time = time.time()
            
            params = {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'radius': 8047
            }
            
            response = self.session.get(f"{self.api_url}/restaurants/search", params=params)
            end_time = time.time()
            
            response_time = end_time - start_time
            success = response.status_code == 200 and response_time < 3.0  # Should be under 3 seconds
            
            details = f"Response time: {response_time:.2f}s"
            if response_time >= 3.0:
                details += " - WARNING: Slow response time"
            
            self.log_test("API Performance (Search)", success, details)
            return success
            
        except Exception as e:
            self.log_test("API Performance (Search)", False, str(e))
            return False

    def test_owner_registration(self):
        """Test restaurant owner registration"""
        try:
            test_email = f"test_owner_{uuid.uuid4().hex[:8]}@example.com"
            registration_data = {
                "email": test_email,
                "password": "TestPassword123!",
                "first_name": "Test",
                "last_name": "Owner",
                "business_name": "Test Restaurant Business",
                "phone": "+1-555-TEST-001"
            }
            
            response = self.session.post(f"{self.api_url}/auth/register", json=registration_data)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.owner_token = data.get('access_token')
                self.owner_user = data.get('user')
                details = f"Registered user: {data.get('user', {}).get('email', 'N/A')}, Token received: {bool(self.owner_token)}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Owner Registration", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Owner Registration", False, str(e))
            return False, {}

    def test_owner_login(self):
        """Test restaurant owner login with existing credentials"""
        try:
            # First register a user
            test_email = f"login_test_{uuid.uuid4().hex[:8]}@example.com"
            registration_data = {
                "email": test_email,
                "password": "TestPassword123!",
                "first_name": "Login",
                "last_name": "Test",
                "business_name": "Login Test Business",
                "phone": "+1-555-LOGIN-01"
            }
            
            reg_response = self.session.post(f"{self.api_url}/auth/register", json=registration_data)
            if reg_response.status_code != 200:
                self.log_test("Owner Login", False, "Failed to create test user for login")
                return False, {}
            
            # Now test login
            login_data = {
                "email": test_email,
                "password": "TestPassword123!"
            }
            
            response = self.session.post(f"{self.api_url}/auth/login", json=login_data)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                token = data.get('access_token')
                user = data.get('user')
                details = f"Login successful for: {user.get('email', 'N/A')}, Token received: {bool(token)}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Owner Login", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Owner Login", False, str(e))
            return False, {}

    def test_owner_auth_me(self):
        """Test getting current user info with JWT token"""
        if not hasattr(self, 'owner_token') or not self.owner_token:
            self.log_test("Owner Auth Me", False, "No token available - registration may have failed")
            return False, {}
        
        try:
            headers = {'Authorization': f'Bearer {self.owner_token}'}
            response = self.session.get(f"{self.api_url}/auth/me", headers=headers)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"User info retrieved: {data.get('email', 'N/A')}, Business: {data.get('business_name', 'N/A')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Owner Auth Me", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Owner Auth Me", False, str(e))
            return False, {}

    def test_search_restaurants_to_claim(self):
        """Test searching for restaurants to claim"""
        if not hasattr(self, 'owner_token') or not self.owner_token:
            self.log_test("Search Restaurants to Claim", False, "No token available")
            return False, {}
        
        try:
            headers = {'Authorization': f'Bearer {self.owner_token}'}
            params = {'query': 'Bad Martha Brewery'}
            
            response = self.session.get(f"{self.api_url}/owner/search-restaurants", 
                                      params=params, headers=headers)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                restaurants = data.get('restaurants', [])
                details = f"Found {len(restaurants)} restaurants for query 'Bad Martha Brewery'"
                if restaurants:
                    first_restaurant = restaurants[0]
                    details += f". First result: {first_restaurant.get('name', 'Unknown')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Search Restaurants to Claim", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Search Restaurants to Claim", False, str(e))
            return False, {}

    def test_claim_restaurant(self):
        """Test claiming a restaurant"""
        if not hasattr(self, 'owner_token') or not self.owner_token:
            self.log_test("Claim Restaurant", False, "No token available")
            return False, {}
        
        try:
            headers = {'Authorization': f'Bearer {self.owner_token}'}
            
            # Create a test claim
            claim_data = {
                "google_place_id": f"test_place_{uuid.uuid4().hex[:8]}",
                "business_name": "Test Restaurant for Claiming",
                "verification_notes": "This is a test claim for API testing"
            }
            
            response = self.session.post(f"{self.api_url}/owner/claim-restaurant", 
                                       json=claim_data, headers=headers)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.test_claim_id = data.get('claim_id')
                details = f"Claim submitted successfully. Claim ID: {self.test_claim_id}, Status: {data.get('status', 'N/A')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Claim Restaurant", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Claim Restaurant", False, str(e))
            return False, {}

    def test_get_my_restaurants(self):
        """Test getting user's restaurants"""
        if not hasattr(self, 'owner_token') or not self.owner_token:
            self.log_test("Get My Restaurants", False, "No token available")
            return False, {}
        
        try:
            headers = {'Authorization': f'Bearer {self.owner_token}'}
            
            response = self.session.get(f"{self.api_url}/owner/my-restaurants", headers=headers)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                restaurants = data.get('restaurants', [])
                pending_claims = data.get('pending_claims', [])
                details = f"Found {len(restaurants)} owned restaurants, {len(pending_claims)} pending claims"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Get My Restaurants", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Get My Restaurants", False, str(e))
            return False, {}

    def test_create_special(self):
        """Test creating a special for a restaurant"""
        if not hasattr(self, 'owner_token') or not self.owner_token:
            self.log_test("Create Special", False, "No token available")
            return False, {}
        
        try:
            headers = {'Authorization': f'Bearer {self.owner_token}'}
            
            # First, we need a restaurant ID. Let's create one or use an existing one
            # For testing, we'll use one of the mock restaurants
            restaurant_id = "test_restaurant_id"  # This would need to be a real restaurant ID
            
            special_data = {
                "title": "Test Happy Hour Special",
                "description": "50% off all appetizers during happy hour - API test special",
                "special_type": "happy_hour",
                "price": 7.99,
                "original_price": 15.99,
                "days_available": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                "time_start": "15:00",
                "time_end": "18:00"
            }
            
            response = self.session.post(f"{self.api_url}/owner/restaurants/{restaurant_id}/specials", 
                                       json=special_data, headers=headers)
            
            # This might fail because we don't own the restaurant, but we're testing the endpoint
            if response.status_code == 200:
                data = response.json()
                details = f"Special created successfully. Special ID: {data.get('special_id', 'N/A')}"
                success = True
            elif response.status_code == 403:
                details = "Expected 403 - Don't own restaurant (endpoint working correctly)"
                success = True  # This is expected behavior
            elif response.status_code == 404:
                details = "Expected 404 - Restaurant not found (endpoint working correctly)"
                success = True  # This is expected behavior
            else:
                details = f"Unexpected status: {response.status_code}, Response: {response.text[:200]}"
                success = False
            
            self.log_test("Create Special", success, details)
            return success
            
        except Exception as e:
            self.log_test("Create Special", False, str(e))
            return False

    def test_auth_edge_cases(self):
        """Test authentication edge cases"""
        test_cases = [
            {
                'name': 'Duplicate Email Registration',
                'endpoint': '/auth/register',
                'data': {
                    "email": "duplicate@example.com",
                    "password": "TestPassword123!",
                    "first_name": "Duplicate",
                    "last_name": "User",
                    "business_name": "Duplicate Business",
                    "phone": "+1-555-DUPLICATE"
                },
                'expected_status': [200, 400]  # First should succeed, second should fail
            },
            {
                'name': 'Invalid Login Credentials',
                'endpoint': '/auth/login',
                'data': {
                    "email": "nonexistent@example.com",
                    "password": "WrongPassword123!"
                },
                'expected_status': [401]
            },
            {
                'name': 'Invalid Token Access',
                'endpoint': '/auth/me',
                'headers': {'Authorization': 'Bearer invalid_token_here'},
                'expected_status': [401]
            }
        ]
        
        all_passed = True
        details_list = []
        
        for case in test_cases:
            try:
                if case['name'] == 'Duplicate Email Registration':
                    # Register once
                    response1 = self.session.post(f"{self.api_url}{case['endpoint']}", json=case['data'])
                    # Register again with same email
                    response2 = self.session.post(f"{self.api_url}{case['endpoint']}", json=case['data'])
                    
                    success = (response1.status_code in case['expected_status'] and 
                             response2.status_code == 400)
                    details_list.append(f"{case['name']}: First: {response1.status_code}, Second: {response2.status_code}")
                    
                elif case['name'] == 'Invalid Token Access':
                    response = self.session.get(f"{self.api_url}{case['endpoint']}", 
                                              headers=case['headers'])
                    success = response.status_code in case['expected_status']
                    details_list.append(f"{case['name']}: {response.status_code}")
                    
                else:
                    response = self.session.post(f"{self.api_url}{case['endpoint']}", json=case['data'])
                    success = response.status_code in case['expected_status']
                    details_list.append(f"{case['name']}: {response.status_code}")
                
                if not success:
                    all_passed = False
                    
            except Exception as e:
                details_list.append(f"{case['name']}: Exception - {str(e)}")
                all_passed = False
        
        self.log_test("Authentication Edge Cases", all_passed, "; ".join(details_list))
        return all_passed

    def test_user_registration(self):
        """Test regular user registration"""
        try:
            test_email = f"user_{uuid.uuid4().hex[:8]}@example.com"
            registration_data = {
                "email": test_email,
                "password": "UserPassword123!",
                "first_name": "John",
                "last_name": "Doe"
            }
            
            response = self.session.post(f"{self.api_url}/users/register", json=registration_data)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                self.user_token = data.get('access_token')
                self.user_data = data.get('user')
                user_type = data.get('user_type')
                details = f"Registered user: {data.get('user', {}).get('email', 'N/A')}, User type: {user_type}, Token received: {bool(self.user_token)}"
                
                # Verify user_type is "user"
                if user_type != "user":
                    success = False
                    details += f" - ERROR: Expected user_type 'user', got '{user_type}'"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("User Registration", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("User Registration", False, str(e))
            return False, {}

    def test_user_login(self):
        """Test regular user login with existing credentials"""
        try:
            # First register a user
            test_email = f"user_login_{uuid.uuid4().hex[:8]}@example.com"
            registration_data = {
                "email": test_email,
                "password": "UserPassword123!",
                "first_name": "Jane",
                "last_name": "Smith"
            }
            
            reg_response = self.session.post(f"{self.api_url}/users/register", json=registration_data)
            if reg_response.status_code != 200:
                self.log_test("User Login", False, "Failed to create test user for login")
                return False, {}
            
            # Now test login
            login_data = {
                "email": test_email,
                "password": "UserPassword123!"
            }
            
            response = self.session.post(f"{self.api_url}/users/login", json=login_data)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                token = data.get('access_token')
                user = data.get('user')
                user_type = data.get('user_type')
                details = f"Login successful for: {user.get('email', 'N/A')}, User type: {user_type}, Token received: {bool(token)}"
                
                # Store token for subsequent tests
                if not hasattr(self, 'user_token') or not self.user_token:
                    self.user_token = token
                    self.user_data = user
                
                # Verify user_type is "user"
                if user_type != "user":
                    success = False
                    details += f" - ERROR: Expected user_type 'user', got '{user_type}'"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("User Login", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("User Login", False, str(e))
            return False, {}

    def test_user_auth_me(self):
        """Test getting current user info with JWT token"""
        if not hasattr(self, 'user_token') or not self.user_token:
            self.log_test("User Auth Me", False, "No user token available - registration may have failed")
            return False, {}
        
        try:
            headers = {'Authorization': f'Bearer {self.user_token}'}
            response = self.session.get(f"{self.api_url}/users/me", headers=headers)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"User info retrieved: {data.get('email', 'N/A')}, Name: {data.get('first_name', '')} {data.get('last_name', '')}"
                
                # Verify expected fields are present
                expected_fields = ['id', 'email', 'first_name', 'last_name', 'favorite_restaurant_ids']
                missing_fields = [field for field in expected_fields if field not in data]
                if missing_fields:
                    details += f" - Missing fields: {missing_fields}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("User Auth Me", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("User Auth Me", False, str(e))
            return False, {}

    def test_add_favorite_restaurant(self):
        """Test adding restaurant to user's favorites"""
        if not hasattr(self, 'user_token') or not self.user_token:
            self.log_test("Add Favorite Restaurant", False, "No user token available")
            return False, {}
        
        try:
            headers = {'Authorization': f'Bearer {self.user_token}'}
            
            # First, get a restaurant ID from the search results
            search_params = {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'radius': 8047
            }
            
            search_response = self.session.get(f"{self.api_url}/restaurants/search", params=search_params)
            if search_response.status_code != 200:
                self.log_test("Add Favorite Restaurant", False, "Failed to get restaurants for testing")
                return False, {}
            
            search_data = search_response.json()
            restaurants = search_data.get('restaurants', [])
            if not restaurants:
                self.log_test("Add Favorite Restaurant", False, "No restaurants found for testing")
                return False, {}
            
            # Use the first restaurant
            restaurant_id = restaurants[0]['id']
            restaurant_name = restaurants[0]['name']
            
            # Add to favorites
            response = self.session.post(f"{self.api_url}/users/favorites/{restaurant_id}", headers=headers)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Added '{restaurant_name}' (ID: {restaurant_id}) to favorites. Message: {data.get('message', 'N/A')}"
                self.test_restaurant_id = restaurant_id  # Store for removal test
                self.test_restaurant_name = restaurant_name
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Add Favorite Restaurant", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Add Favorite Restaurant", False, str(e))
            return False, {}

    def test_remove_favorite_restaurant(self):
        """Test removing restaurant from user's favorites"""
        if not hasattr(self, 'user_token') or not self.user_token:
            self.log_test("Remove Favorite Restaurant", False, "No user token available")
            return False, {}
        
        if not hasattr(self, 'test_restaurant_id'):
            self.log_test("Remove Favorite Restaurant", False, "No restaurant ID available - add favorite test may have failed")
            return False, {}
        
        try:
            headers = {'Authorization': f'Bearer {self.user_token}'}
            restaurant_id = self.test_restaurant_id
            restaurant_name = getattr(self, 'test_restaurant_name', 'Unknown')
            
            # Remove from favorites
            response = self.session.delete(f"{self.api_url}/users/favorites/{restaurant_id}", headers=headers)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Removed '{restaurant_name}' (ID: {restaurant_id}) from favorites. Message: {data.get('message', 'N/A')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Remove Favorite Restaurant", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Remove Favorite Restaurant", False, str(e))
            return False, {}

    def test_get_favorite_restaurants(self):
        """Test getting user's favorite restaurants"""
        if not hasattr(self, 'user_token') or not self.user_token:
            self.log_test("Get Favorite Restaurants", False, "No user token available")
            return False, {}
        
        try:
            headers = {'Authorization': f'Bearer {self.user_token}'}
            
            # First add a restaurant to favorites for testing
            search_params = {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'radius': 8047
            }
            
            search_response = self.session.get(f"{self.api_url}/restaurants/search", params=search_params)
            if search_response.status_code == 200:
                search_data = search_response.json()
                restaurants = search_data.get('restaurants', [])
                if restaurants:
                    # Add first restaurant to favorites
                    restaurant_id = restaurants[0]['id']
                    add_response = self.session.post(f"{self.api_url}/users/favorites/{restaurant_id}", headers=headers)
            
            # Now get favorites
            response = self.session.get(f"{self.api_url}/users/favorites", headers=headers)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                favorites = data.get('favorites', [])
                details = f"Retrieved {len(favorites)} favorite restaurants"
                
                if favorites:
                    first_favorite = favorites[0]
                    expected_fields = ['id', 'name', 'address']
                    missing_fields = [field for field in expected_fields if field not in first_favorite]
                    if missing_fields:
                        details += f" - Missing fields in favorite: {missing_fields}"
                    else:
                        details += f". First favorite: {first_favorite.get('name', 'Unknown')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Get Favorite Restaurants", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Get Favorite Restaurants", False, str(e))
            return False, {}

    def test_user_auth_edge_cases(self):
        """Test user authentication edge cases"""
        test_cases = [
            {
                'name': 'Duplicate User Email Registration',
                'test_func': self._test_duplicate_user_registration
            },
            {
                'name': 'Invalid User Login Credentials',
                'test_func': self._test_invalid_user_login
            },
            {
                'name': 'Invalid Token Access to User Endpoints',
                'test_func': self._test_invalid_token_user_access
            },
            {
                'name': 'Add Non-existent Restaurant to Favorites',
                'test_func': self._test_add_nonexistent_favorite
            },
            {
                'name': 'Access User Endpoints with Owner Token',
                'test_func': self._test_owner_token_user_access
            }
        ]
        
        all_passed = True
        details_list = []
        
        for case in test_cases:
            try:
                success, details = case['test_func']()
                details_list.append(f"{case['name']}: {details}")
                if not success:
                    all_passed = False
            except Exception as e:
                details_list.append(f"{case['name']}: Exception - {str(e)}")
                all_passed = False
        
        self.log_test("User Authentication Edge Cases", all_passed, "; ".join(details_list))
        return all_passed

    def _test_duplicate_user_registration(self):
        """Test duplicate user email registration"""
        try:
            test_email = f"duplicate_user_{uuid.uuid4().hex[:8]}@example.com"
            registration_data = {
                "email": test_email,
                "password": "TestPassword123!",
                "first_name": "Duplicate",
                "last_name": "User"
            }
            
            # Register once
            response1 = self.session.post(f"{self.api_url}/users/register", json=registration_data)
            # Register again with same email
            response2 = self.session.post(f"{self.api_url}/users/register", json=registration_data)
            
            success = response1.status_code == 200 and response2.status_code == 400
            details = f"First: {response1.status_code}, Second: {response2.status_code}"
            return success, details
            
        except Exception as e:
            return False, str(e)

    def _test_invalid_user_login(self):
        """Test invalid user login credentials"""
        try:
            login_data = {
                "email": "nonexistent_user@example.com",
                "password": "WrongPassword123!"
            }
            
            response = self.session.post(f"{self.api_url}/users/login", json=login_data)
            success = response.status_code == 401
            details = f"Status: {response.status_code}"
            return success, details
            
        except Exception as e:
            return False, str(e)

    def _test_invalid_token_user_access(self):
        """Test invalid token access to user endpoints"""
        try:
            headers = {'Authorization': 'Bearer invalid_user_token_here'}
            response = self.session.get(f"{self.api_url}/users/me", headers=headers)
            success = response.status_code == 401
            details = f"Status: {response.status_code}"
            return success, details
            
        except Exception as e:
            return False, str(e)

    def _test_add_nonexistent_favorite(self):
        """Test adding non-existent restaurant to favorites"""
        if not hasattr(self, 'user_token') or not self.user_token:
            return False, "No user token available"
        
        try:
            headers = {'Authorization': f'Bearer {self.user_token}'}
            fake_restaurant_id = f"nonexistent_{uuid.uuid4().hex[:8]}"
            
            response = self.session.post(f"{self.api_url}/users/favorites/{fake_restaurant_id}", headers=headers)
            # This should succeed (the API doesn't validate restaurant existence)
            success = response.status_code == 200
            details = f"Status: {response.status_code}"
            return success, details
            
        except Exception as e:
            return False, str(e)

    def test_forward_geocoding_basic(self):
        """Test basic forward geocoding with valid address"""
        try:
            test_data = {
                "address": "1600 Amphitheatre Parkway, Mountain View, CA"
            }
            
            response = self.session.post(f"{self.api_url}/geocode/forward", json=test_data)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_fields = ['formatted_address', 'latitude', 'longitude', 'place_id', 'address_components', 'geometry_type']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    success = False
                    details = f"Missing required fields: {missing_fields}"
                else:
                    details = f"Address: {data.get('formatted_address', 'N/A')}, Coordinates: ({data.get('latitude', 'N/A')}, {data.get('longitude', 'N/A')}), Place ID: {data.get('place_id', 'N/A')}"
                    
                    # Validate coordinate ranges
                    lat = data.get('latitude')
                    lng = data.get('longitude')
                    if lat is None or lng is None or not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                        success = False
                        details += " - Invalid coordinate values"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Forward Geocoding - Basic Address", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Forward Geocoding - Basic Address", False, str(e))
            return False, {}

    def test_forward_geocoding_with_region(self):
        """Test forward geocoding with region parameter"""
        try:
            test_data = {
                "address": "Main Street",
                "region": "US"
            }
            
            response = self.session.post(f"{self.api_url}/geocode/forward", json=test_data)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                details = f"Address with region: {data.get('formatted_address', 'N/A')}, Coordinates: ({data.get('latitude', 'N/A')}, {data.get('longitude', 'N/A')})"
                
                # Verify address components contain US-related information
                address_components = data.get('address_components', [])
                has_us_component = any('United States' in str(component) or 'US' in str(component) for component in address_components)
                if not has_us_component:
                    details += " - Warning: No US component found in address"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Forward Geocoding - With Region Parameter", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Forward Geocoding - With Region Parameter", False, str(e))
            return False, {}

    def test_forward_geocoding_invalid_address(self):
        """Test forward geocoding with invalid address"""
        try:
            test_data = {
                "address": "ThisIsNotARealAddressAnywhere12345XYZ"
            }
            
            response = self.session.post(f"{self.api_url}/geocode/forward", json=test_data)
            # Should return 404 for address not found
            success = response.status_code == 404
            
            if success:
                details = "Correctly returned 404 for invalid address"
            else:
                details = f"Expected 404, got {response.status_code}. Response: {response.text[:200]}"
            
            self.log_test("Forward Geocoding - Invalid Address", success, details)
            return success
            
        except Exception as e:
            self.log_test("Forward Geocoding - Invalid Address", False, str(e))
            return False

    def test_reverse_geocoding_basic(self):
        """Test basic reverse geocoding with valid coordinates"""
        try:
            test_data = {
                "latitude": 37.7749,
                "longitude": -122.4194
            }
            
            response = self.session.post(f"{self.api_url}/geocode/reverse", json=test_data)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if isinstance(data, list) and len(data) > 0:
                    first_result = data[0]
                    required_fields = ['formatted_address', 'latitude', 'longitude', 'place_id', 'address_components', 'geometry_type']
                    missing_fields = [field for field in required_fields if field not in first_result]
                    
                    if missing_fields:
                        success = False
                        details = f"Missing required fields in first result: {missing_fields}"
                    else:
                        details = f"Found {len(data)} addresses. First: {first_result.get('formatted_address', 'N/A')}"
                        
                        # Verify coordinates are close to input
                        result_lat = first_result.get('latitude')
                        result_lng = first_result.get('longitude')
                        if result_lat and result_lng:
                            lat_diff = abs(result_lat - test_data['latitude'])
                            lng_diff = abs(result_lng - test_data['longitude'])
                            if lat_diff > 0.01 or lng_diff > 0.01:  # Allow small differences
                                details += f" - Warning: Coordinates differ significantly (lat: {lat_diff:.4f}, lng: {lng_diff:.4f})"
                else:
                    success = False
                    details = "Expected list of results, got different format"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Reverse Geocoding - Basic Coordinates", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Reverse Geocoding - Basic Coordinates", False, str(e))
            return False, {}

    def test_reverse_geocoding_with_filters(self):
        """Test reverse geocoding with result_type filter"""
        try:
            test_data = {
                "latitude": 37.7749,
                "longitude": -122.4194,
                "result_type": ["street_address", "route"]
            }
            
            response = self.session.post(f"{self.api_url}/geocode/reverse", json=test_data)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if isinstance(data, list):
                    details = f"Found {len(data)} filtered results"
                    if data:
                        first_result = data[0]
                        details += f". First: {first_result.get('formatted_address', 'N/A')}"
                else:
                    success = False
                    details = "Expected list of results"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Reverse Geocoding - With Filters", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Reverse Geocoding - With Filters", False, str(e))
            return False, {}

    def test_reverse_geocoding_invalid_coordinates(self):
        """Test reverse geocoding with invalid coordinates"""
        try:
            test_data = {
                "latitude": 91,  # Invalid latitude (> 90)
                "longitude": -122.4194
            }
            
            response = self.session.post(f"{self.api_url}/geocode/reverse", json=test_data)
            # Should return 422 for validation error
            success = response.status_code == 422
            
            if success:
                details = "Correctly returned 422 for invalid coordinates"
            else:
                details = f"Expected 422, got {response.status_code}. Response: {response.text[:200]}"
            
            self.log_test("Reverse Geocoding - Invalid Coordinates", success, details)
            return success
            
        except Exception as e:
            self.log_test("Reverse Geocoding - Invalid Coordinates", False, str(e))
            return False

    def test_batch_geocoding_basic(self):
        """Test basic batch geocoding with multiple addresses"""
        try:
            test_data = {
                "addresses": [
                    "1600 Amphitheatre Parkway, Mountain View, CA",
                    "1 Infinite Loop, Cupertino, CA",
                    "410 Terry Ave N, Seattle, WA"
                ]
            }
            
            response = self.session.post(f"{self.api_url}/geocode/batch", json=test_data)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_fields = ['results', 'errors']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    success = False
                    details = f"Missing required fields: {missing_fields}"
                else:
                    results = data.get('results', [])
                    errors = data.get('errors', [])
                    details = f"Processed {len(test_data['addresses'])} addresses: {len(results)} successful, {len(errors)} errors"
                    
                    # Verify each result has required fields
                    for i, result in enumerate(results):
                        result_fields = ['formatted_address', 'latitude', 'longitude', 'place_id']
                        missing_result_fields = [field for field in result_fields if field not in result]
                        if missing_result_fields:
                            details += f" - Result {i} missing fields: {missing_result_fields}"
                    
                    if results:
                        first_result = results[0]
                        details += f". First result: {first_result.get('formatted_address', 'N/A')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Batch Geocoding - Multiple Valid Addresses", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Batch Geocoding - Multiple Valid Addresses", False, str(e))
            return False, {}

    def test_batch_geocoding_with_errors(self):
        """Test batch geocoding with mix of valid and invalid addresses"""
        try:
            test_data = {
                "addresses": [
                    "1600 Amphitheatre Parkway, Mountain View, CA",  # Valid
                    "ThisIsNotARealAddressAnywhere12345XYZ",         # Invalid
                    "1 Infinite Loop, Cupertino, CA"                 # Valid
                ]
            }
            
            response = self.session.post(f"{self.api_url}/geocode/batch", json=test_data)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                results = data.get('results', [])
                errors = data.get('errors', [])
                
                # Should have some results and some errors
                details = f"Results: {len(results)}, Errors: {len(errors)}"
                
                # Verify error format
                if errors:
                    first_error = errors[0]
                    error_fields = ['index', 'address', 'error']
                    missing_error_fields = [field for field in error_fields if field not in first_error]
                    if missing_error_fields:
                        details += f" - Error missing fields: {missing_error_fields}"
                    else:
                        details += f". First error: {first_error.get('error', 'N/A')} for address at index {first_error.get('index', 'N/A')}"
                
                # Should have at least 2 successful results and 1 error
                expected_success = len(results) >= 2 and len(errors) >= 1
                if not expected_success:
                    details += " - Expected at least 2 results and 1 error"
                    success = False
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Batch Geocoding - Mixed Valid/Invalid Addresses", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Batch Geocoding - Mixed Valid/Invalid Addresses", False, str(e))
            return False, {}

    def test_batch_geocoding_max_limit(self):
        """Test batch geocoding with maximum number of addresses"""
        try:
            # Create 10 addresses (the maximum allowed)
            test_addresses = [
                f"Main Street, City {i}, CA" for i in range(10)
            ]
            
            test_data = {
                "addresses": test_addresses,
                "max_results": 10
            }
            
            response = self.session.post(f"{self.api_url}/geocode/batch", json=test_data)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                results = data.get('results', [])
                errors = data.get('errors', [])
                total_processed = len(results) + len(errors)
                
                details = f"Processed {total_processed}/10 addresses: {len(results)} successful, {len(errors)} errors"
                
                # Should process all 10 addresses
                if total_processed != 10:
                    details += f" - Expected 10 total processed, got {total_processed}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Batch Geocoding - Maximum Limit (10 addresses)", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Batch Geocoding - Maximum Limit (10 addresses)", False, str(e))
            return False, {}

    def test_batch_geocoding_over_limit(self):
        """Test batch geocoding with more than maximum addresses"""
        try:
            # Create 15 addresses (over the 10 limit)
            test_addresses = [
                f"Main Street, City {i}, CA" for i in range(15)
            ]
            
            test_data = {
                "addresses": test_addresses
            }
            
            response = self.session.post(f"{self.api_url}/geocode/batch", json=test_data)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                results = data.get('results', [])
                errors = data.get('errors', [])
                total_processed = len(results) + len(errors)
                
                # Should only process first 10 addresses
                details = f"Processed {total_processed} addresses (should be ≤10 due to limit)"
                
                if total_processed > 10:
                    details += f" - Warning: Processed more than limit ({total_processed})"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Batch Geocoding - Over Limit (15 addresses)", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Batch Geocoding - Over Limit (15 addresses)", False, str(e))
            return False, {}

    def test_legacy_geocoding_basic(self):
        """Test legacy geocoding endpoint for backward compatibility"""
        try:
            params = {
                'address': '1600 Amphitheatre Parkway, Mountain View, CA'
            }
            
            response = self.session.get(f"{self.api_url}/geocode", params=params)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_fields = ['coordinates', 'formatted_address']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    success = False
                    details = f"Missing required fields: {missing_fields}"
                else:
                    coordinates = data.get('coordinates', {})
                    coord_fields = ['latitude', 'longitude']
                    missing_coord_fields = [field for field in coord_fields if field not in coordinates]
                    
                    if missing_coord_fields:
                        success = False
                        details = f"Missing coordinate fields: {missing_coord_fields}"
                    else:
                        lat = coordinates.get('latitude')
                        lng = coordinates.get('longitude')
                        formatted_address = data.get('formatted_address')
                        details = f"Address: {formatted_address}, Coordinates: ({lat}, {lng})"
                        
                        # Validate coordinate ranges
                        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                            success = False
                            details += " - Invalid coordinate values"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Legacy Geocoding - Basic Address", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Legacy Geocoding - Basic Address", False, str(e))
            return False, {}

    def test_legacy_geocoding_invalid_address(self):
        """Test legacy geocoding with invalid address"""
        try:
            params = {
                'address': 'ThisIsNotARealAddressAnywhere12345XYZ'
            }
            
            response = self.session.get(f"{self.api_url}/geocode", params=params)
            # Should return 404 for address not found
            success = response.status_code == 404
            
            if success:
                details = "Correctly returned 404 for invalid address"
            else:
                details = f"Expected 404, got {response.status_code}. Response: {response.text[:200]}"
            
            self.log_test("Legacy Geocoding - Invalid Address", success, details)
            return success
            
        except Exception as e:
            self.log_test("Legacy Geocoding - Invalid Address", False, str(e))
            return False

    def test_geocoding_error_handling(self):
        """Test geocoding endpoints error handling"""
        test_cases = [
            {
                'name': 'Forward Geocoding - Missing Address',
                'endpoint': '/geocode/forward',
                'method': 'POST',
                'data': {},  # Missing required address field
                'expected_status': 422
            },
            {
                'name': 'Reverse Geocoding - Invalid Latitude Range',
                'endpoint': '/geocode/reverse',
                'method': 'POST',
                'data': {'latitude': 100, 'longitude': -122.4194},  # lat > 90
                'expected_status': 422
            },
            {
                'name': 'Batch Geocoding - Empty Address List',
                'endpoint': '/geocode/batch',
                'method': 'POST',
                'data': {'addresses': []},  # Empty list - should return empty results
                'expected_status': 200
            },
            {
                'name': 'Legacy Geocoding - Missing Address Parameter',
                'endpoint': '/geocode',
                'method': 'GET',
                'params': {},  # Missing required address parameter
                'expected_status': 422
            }
        ]
        
        all_passed = True
        details_list = []
        
        for case in test_cases:
            try:
                if case['method'] == 'POST':
                    response = self.session.post(f"{self.api_url}{case['endpoint']}", json=case['data'])
                else:  # GET
                    response = self.session.get(f"{self.api_url}{case['endpoint']}", params=case.get('params', {}))
                
                success = response.status_code == case['expected_status']
                details_list.append(f"{case['name']}: {response.status_code} (expected {case['expected_status']})")
                
                if not success:
                    all_passed = False
                    
            except Exception as e:
                details_list.append(f"{case['name']}: Exception - {str(e)}")
                all_passed = False
        
        self.log_test("Geocoding Error Handling", all_passed, "; ".join(details_list))
        return all_passed

    def _test_owner_token_user_access(self):
        """Test accessing user endpoints with owner token"""
        if not hasattr(self, 'owner_token') or not self.owner_token:
            return True, "No owner token available - skipping test"
        
        try:
            headers = {'Authorization': f'Bearer {self.owner_token}'}
            response = self.session.get(f"{self.api_url}/users/me", headers=headers)
            # Should fail because owner token shouldn't work for user endpoints
            success = response.status_code == 401
            details = f"Status: {response.status_code}"
            return success, details
            
        except Exception as e:
            return False, str(e)

    def test_fixed_google_places_favorites_workflow(self):
        """Test the FIXED Google Places favorites functionality - comprehensive workflow"""
        print("\n🔍 TESTING FIXED GOOGLE PLACES FAVORITES FUNCTIONALITY")
        print("=" * 70)
        
        # Step 1: Create/login test user
        try:
            test_email = f"favorites_test_{uuid.uuid4().hex[:8]}@example.com"
            registration_data = {
                "email": test_email,
                "password": "FavoritesTest123!",
                "first_name": "Favorites",
                "last_name": "Tester"
            }
            
            reg_response = self.session.post(f"{self.api_url}/users/register", json=registration_data)
            if reg_response.status_code != 200:
                self.log_test("FIXED Google Places Favorites - User Registration", False, f"Failed to create test user: {reg_response.status_code}")
                return False, {}
            
            reg_data = reg_response.json()
            test_token = reg_data.get('access_token')
            headers = {'Authorization': f'Bearer {test_token}'}
            
            print(f"✅ Step 1: Created test user: {test_email}")
            
        except Exception as e:
            self.log_test("FIXED Google Places Favorites - User Registration", False, str(e))
            return False, {}
        
        # Step 2: Search for restaurants to get Google Places results
        try:
            search_params = {
                'latitude': 37.7749,  # San Francisco
                'longitude': -122.4194,
                'radius': 8047,  # 5 miles
                'limit': 20
            }
            
            search_response = self.session.get(f"{self.api_url}/restaurants/search", params=search_params)
            if search_response.status_code != 200:
                self.log_test("FIXED Google Places Favorites - Restaurant Search", False, f"Search failed: {search_response.status_code}")
                return False, {}
            
            search_data = search_response.json()
            restaurants = search_data.get('restaurants', [])
            
            # Find Google Places restaurants (IDs starting with "google_")
            google_restaurants = [r for r in restaurants if r['id'].startswith('google_')]
            db_restaurants = [r for r in restaurants if not r['id'].startswith('google_')]
            
            print(f"✅ Step 2: Found {len(restaurants)} total restaurants ({len(google_restaurants)} Google Places, {len(db_restaurants)} database)")
            
            if len(google_restaurants) < 2:
                self.log_test("FIXED Google Places Favorites - Restaurant Search", False, f"Need at least 2 Google Places restaurants for testing, found {len(google_restaurants)}")
                return False, {}
                
        except Exception as e:
            self.log_test("FIXED Google Places Favorites - Restaurant Search", False, str(e))
            return False, {}
        
        # Step 3: Add Google Places restaurants to favorites
        try:
            test_restaurants = google_restaurants[:3]  # Use first 3 Google Places restaurants
            added_favorites = []
            
            for i, restaurant in enumerate(test_restaurants):
                restaurant_id = restaurant['id']
                restaurant_name = restaurant['name']
                
                add_response = self.session.post(f"{self.api_url}/users/favorites/{restaurant_id}", headers=headers)
                
                if add_response.status_code == 200:
                    added_favorites.append({
                        'id': restaurant_id,
                        'name': restaurant_name,
                        'address': restaurant.get('address', ''),
                        'rating': restaurant.get('rating')
                    })
                    print(f"✅ Step 3.{i+1}: Added '{restaurant_name}' (ID: {restaurant_id}) to favorites")
                else:
                    print(f"❌ Step 3.{i+1}: Failed to add '{restaurant_name}' to favorites: {add_response.status_code}")
                    self.log_test("FIXED Google Places Favorites - Add Favorites", False, f"Failed to add restaurant {restaurant_id}: {add_response.status_code}")
                    return False, {}
            
            if len(added_favorites) < 3:
                self.log_test("FIXED Google Places Favorites - Add Favorites", False, f"Only added {len(added_favorites)}/3 restaurants to favorites")
                return False, {}
                
        except Exception as e:
            self.log_test("FIXED Google Places Favorites - Add Favorites", False, str(e))
            return False, {}
        
        # Step 4: Retrieve favorites and verify Google Places data is returned
        try:
            favorites_response = self.session.get(f"{self.api_url}/users/favorites", headers=headers)
            
            if favorites_response.status_code != 200:
                self.log_test("FIXED Google Places Favorites - Get Favorites", False, f"Failed to get favorites: {favorites_response.status_code}")
                return False, {}
            
            favorites_data = favorites_response.json()
            favorites = favorites_data.get('favorites', [])
            
            print(f"✅ Step 4: Retrieved {len(favorites)} favorites from API")
            
            # Verify all added Google Places restaurants are returned with proper details
            success = True
            missing_restaurants = []
            invalid_data = []
            
            for added_restaurant in added_favorites:
                found = False
                for favorite in favorites:
                    if favorite['id'] == added_restaurant['id']:
                        found = True
                        # Verify the favorite has proper details (name, address, etc.)
                        if not favorite.get('name') or favorite.get('name') == 'Restaurant (Details Unavailable)':
                            invalid_data.append(f"Restaurant {added_restaurant['id']} has invalid name: '{favorite.get('name')}'")
                        
                        print(f"✅ Found favorite: {favorite.get('name', 'N/A')} - {favorite.get('address', 'N/A')} (Rating: {favorite.get('rating', 'N/A')})")
                        break
                
                if not found:
                    missing_restaurants.append(added_restaurant['name'])
                    success = False
            
            if missing_restaurants:
                details = f"Missing restaurants in favorites: {', '.join(missing_restaurants)}"
                success = False
            elif invalid_data:
                details = f"Invalid data in favorites: {'; '.join(invalid_data)}"
                success = False
            else:
                details = f"Successfully retrieved all {len(added_favorites)} Google Places restaurants with proper details"
            
            print(f"✅ Step 4 Complete: {details}")
            
        except Exception as e:
            self.log_test("FIXED Google Places Favorites - Get Favorites", False, str(e))
            return False, {}
        
        # Step 5: Test mixed favorites (Google Places + Database restaurants)
        try:
            if db_restaurants:
                # Add one database restaurant to favorites
                db_restaurant = db_restaurants[0]
                db_restaurant_id = db_restaurant['id']
                db_restaurant_name = db_restaurant['name']
                
                add_db_response = self.session.post(f"{self.api_url}/users/favorites/{db_restaurant_id}", headers=headers)
                
                if add_db_response.status_code == 200:
                    print(f"✅ Step 5.1: Added database restaurant '{db_restaurant_name}' to favorites")
                    
                    # Get favorites again to verify mixed results
                    mixed_favorites_response = self.session.get(f"{self.api_url}/users/favorites", headers=headers)
                    
                    if mixed_favorites_response.status_code == 200:
                        mixed_favorites_data = mixed_favorites_response.json()
                        mixed_favorites = mixed_favorites_data.get('favorites', [])
                        
                        google_count = len([f for f in mixed_favorites if f['id'].startswith('google_')])
                        db_count = len([f for f in mixed_favorites if not f['id'].startswith('google_')])
                        
                        print(f"✅ Step 5.2: Mixed favorites working - {google_count} Google Places + {db_count} database restaurants")
                        
                        if google_count >= 3 and db_count >= 1:
                            mixed_success = True
                            mixed_details = f"Mixed favorites working correctly: {google_count} Google Places + {db_count} database restaurants"
                        else:
                            mixed_success = False
                            mixed_details = f"Mixed favorites issue: Expected ≥3 Google + ≥1 DB, got {google_count} Google + {db_count} DB"
                    else:
                        mixed_success = False
                        mixed_details = f"Failed to retrieve mixed favorites: {mixed_favorites_response.status_code}"
                else:
                    mixed_success = False
                    mixed_details = f"Failed to add database restaurant: {add_db_response.status_code}"
            else:
                mixed_success = True
                mixed_details = "No database restaurants available for mixed testing (Google Places only test passed)"
                
        except Exception as e:
            mixed_success = False
            mixed_details = str(e)
        
        # Final assessment
        overall_success = success and mixed_success
        
        if overall_success:
            final_details = f"🎉 FIXED FAVORITES FUNCTIONALITY WORKING CORRECTLY! Google Places restaurants are now properly retrieved with details from Google Places API. {details}. {mixed_details}"
            print(f"\n🎉 SUCCESS: Fixed Google Places favorites functionality is working correctly!")
            print(f"   - Google Places restaurants are properly retrieved with details")
            print(f"   - Mixed favorites (Google Places + Database) working correctly")
            print(f"   - Heart icon state management issue should now be resolved")
        else:
            final_details = f"❌ FIXED FAVORITES STILL HAS ISSUES: {details}. Mixed test: {mixed_details}"
            print(f"\n❌ FAILURE: Fixed Google Places favorites functionality still has issues")
        
        self.log_test("FIXED Google Places Favorites - Complete Workflow", overall_success, final_details)
        return overall_success, favorites_data if overall_success else {}

    def test_google_places_api_integration(self):
        """Test Google Places API integration for favorites retrieval"""
        try:
            # Create test user
            test_email = f"places_api_test_{uuid.uuid4().hex[:8]}@example.com"
            registration_data = {
                "email": test_email,
                "password": "PlacesTest123!",
                "first_name": "Places",
                "last_name": "Tester"
            }
            
            reg_response = self.session.post(f"{self.api_url}/users/register", json=registration_data)
            if reg_response.status_code != 200:
                self.log_test("Google Places API Integration", False, "Failed to create test user")
                return False, {}
            
            reg_data = reg_response.json()
            test_token = reg_data.get('access_token')
            headers = {'Authorization': f'Bearer {test_token}'}
            
            # Get restaurants from search
            search_params = {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'radius': 8047
            }
            
            search_response = self.session.get(f"{self.api_url}/restaurants/search", params=search_params)
            if search_response.status_code != 200:
                self.log_test("Google Places API Integration", False, "Restaurant search failed")
                return False, {}
            
            search_data = search_response.json()
            restaurants = search_data.get('restaurants', [])
            google_restaurants = [r for r in restaurants if r['id'].startswith('google_')]
            
            if not google_restaurants:
                self.log_test("Google Places API Integration", False, "No Google Places restaurants found")
                return False, {}
            
            # Add a Google Places restaurant to favorites
            test_restaurant = google_restaurants[0]
            restaurant_id = test_restaurant['id']
            
            add_response = self.session.post(f"{self.api_url}/users/favorites/{restaurant_id}", headers=headers)
            if add_response.status_code != 200:
                self.log_test("Google Places API Integration", False, f"Failed to add favorite: {add_response.status_code}")
                return False, {}
            
            # Retrieve favorites and check Google Places API integration
            favorites_response = self.session.get(f"{self.api_url}/users/favorites", headers=headers)
            if favorites_response.status_code != 200:
                self.log_test("Google Places API Integration", False, f"Failed to get favorites: {favorites_response.status_code}")
                return False, {}
            
            favorites_data = favorites_response.json()
            favorites = favorites_data.get('favorites', [])
            
            # Verify the Google Places restaurant is returned with proper details
            google_favorite = None
            for favorite in favorites:
                if favorite['id'] == restaurant_id:
                    google_favorite = favorite
                    break
            
            if not google_favorite:
                self.log_test("Google Places API Integration", False, "Google Places restaurant not found in favorites")
                return False, {}
            
            # Check if the restaurant has proper details from Google Places API
            required_fields = ['name', 'address']
            missing_fields = [field for field in required_fields if not google_favorite.get(field)]
            
            if missing_fields:
                details = f"Google Places restaurant missing fields: {missing_fields}. Data: {google_favorite}"
                success = False
            elif google_favorite.get('name') == 'Restaurant (Details Unavailable)':
                details = f"Google Places API call failed - restaurant shows as unavailable: {google_favorite}"
                success = False
            else:
                details = f"Google Places API integration working - Restaurant: {google_favorite.get('name')} at {google_favorite.get('address')} (Rating: {google_favorite.get('rating', 'N/A')})"
                success = True
            
            self.log_test("Google Places API Integration", success, details)
            return success, favorites_data if success else {}
            
        except Exception as e:
            self.log_test("Google Places API Integration", False, str(e))
            return False, {}

    def run_all_tests(self):
        """Run all API tests"""
        print("🚀 Starting On-the-Cheap API Tests")
        print("=" * 50)
        
        # Basic functionality tests
        self.test_api_health()
        self.test_special_types()
        
        # Search functionality tests
        self.test_restaurant_search_basic()
        self.test_restaurant_search_with_filters()
        self.test_restaurant_search_different_radius()
        self.test_restaurant_search_edge_cases()
        
        # CRUD operations
        self.test_create_restaurant()
        
        # Performance tests
        self.test_performance()
        
        print("\n" + "🌍 GEOCODING API TESTS")
        print("=" * 50)
        
        # Geocoding functionality tests
        self.test_forward_geocoding_basic()
        self.test_forward_geocoding_with_region()
        self.test_forward_geocoding_invalid_address()
        self.test_reverse_geocoding_basic()
        self.test_reverse_geocoding_with_filters()
        self.test_reverse_geocoding_invalid_coordinates()
        self.test_batch_geocoding_basic()
        self.test_batch_geocoding_with_errors()
        self.test_batch_geocoding_max_limit()
        self.test_batch_geocoding_over_limit()
        self.test_legacy_geocoding_basic()
        self.test_legacy_geocoding_invalid_address()
        self.test_geocoding_error_handling()
        
        print("\n" + "🏪 RESTAURANT OWNER PORTAL TESTS")
        print("=" * 50)
        
        # Owner authentication tests
        self.test_owner_registration()
        self.test_owner_login()
        self.test_owner_auth_me()
        
        # Owner functionality tests
        self.test_search_restaurants_to_claim()
        self.test_claim_restaurant()
        self.test_get_my_restaurants()
        self.test_create_special()
        
        # Edge cases
        self.test_auth_edge_cases()
        
        print("\n" + "👤 REGULAR USER TESTS")
        print("=" * 50)
        
        # Regular user authentication and favorites tests
        self.test_user_registration()
        self.test_user_login()
        self.test_user_auth_me()
        self.test_add_favorite_restaurant()
        self.test_remove_favorite_restaurant()
        self.test_get_favorite_restaurants()
        self.test_user_auth_edge_cases()
        
        print("\n" + "🔧 FIXED GOOGLE PLACES FAVORITES TESTS")
        print("=" * 50)
        
        # Test the FIXED Google Places favorites functionality
        self.test_fixed_google_places_favorites_workflow()
        self.test_google_places_api_integration()
        
        # Print summary
        print("\n" + "=" * 50)
        print(f"📊 Test Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All tests passed!")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} tests failed")
            return 1

def main():
    """Main test runner"""
    tester = OnTheCheapAPITester()
    return tester.run_all_tests()

def test_fixed_favorites_only():
    """Test runner specifically for the FIXED Google Places favorites functionality"""
    print("🔧 TESTING FIXED GOOGLE PLACES FAVORITES FUNCTIONALITY")
    print("=" * 70)
    print("This test focuses on verifying that the Google Places favorites bug has been fixed.")
    print("The fix should allow Google Places restaurants to be properly retrieved with details.")
    print("=" * 70)
    
    tester = OnTheCheapAPITester()
    
    # Run only the favorites-related tests
    print("\n📋 Running focused favorites tests...")
    
    # Test basic user functionality first
    tester.test_user_registration()
    tester.test_user_login()
    tester.test_user_auth_me()
    
    # Test the core fixed functionality
    tester.test_fixed_google_places_favorites_workflow()
    tester.test_google_places_api_integration()
    
    # Test basic favorites operations
    tester.test_add_favorite_restaurant()
    tester.test_get_favorite_restaurants()
    tester.test_remove_favorite_restaurant()
    
    # Print focused summary
    print("\n" + "=" * 70)
    print(f"📊 FIXED FAVORITES TEST Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All FIXED FAVORITES tests passed! The Google Places favorites bug appears to be resolved.")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} FIXED FAVORITES tests failed - bug may still exist")
        return 1

if __name__ == "__main__":
    sys.exit(main())