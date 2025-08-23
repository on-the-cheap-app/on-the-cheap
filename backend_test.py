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
    def __init__(self, base_url="https://on-the-cheap.preview.emergentagent.com"):
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

if __name__ == "__main__":
    sys.exit(main())