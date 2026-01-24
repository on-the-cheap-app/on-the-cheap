#!/usr/bin/env python3
"""
Mobile App Enhanced Search Features Backend API Testing
Tests the enhanced mobile app search features integration with backend APIs
"""

import requests
import sys
import json
from datetime import datetime
import uuid

class MobileAppAPITester:
    def __init__(self, base_url="https://fooddeals-1.preview.emergentagent.com"):
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

    def test_forward_geocoding_mobile_format(self):
        """Test forward geocoding API for mobile app AddressInput component"""
        try:
            # Test various address formats that mobile app might use
            test_addresses = [
                "San Francisco, CA",
                "1600 Amphitheatre Parkway, Mountain View, CA",
                "New York",
                "Chicago, IL",
                "Main Street, Boston"
            ]
            
            all_passed = True
            results = []
            
            for address in test_addresses:
                test_data = {"address": address}
                response = self.session.post(f"{self.api_url}/geocode/forward", json=test_data)
                
                if response.status_code == 200:
                    data = response.json()
                    # Verify mobile app expected fields
                    required_fields = ['formatted_address', 'latitude', 'longitude', 'place_id']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        all_passed = False
                        results.append(f"{address}: Missing fields {missing_fields}")
                    else:
                        # Validate coordinate ranges for mobile app
                        lat = data.get('latitude')
                        lng = data.get('longitude')
                        if not (-90 <= lat <= 90) or not (-180 <= lng <= 180):
                            all_passed = False
                            results.append(f"{address}: Invalid coordinates ({lat}, {lng})")
                        else:
                            results.append(f"{address}: ✓ ({lat:.4f}, {lng:.4f})")
                elif response.status_code == 404:
                    # Some generic addresses might not be found - this is acceptable
                    results.append(f"{address}: Not found (acceptable)")
                else:
                    all_passed = False
                    results.append(f"{address}: Error {response.status_code}")
            
            details = "; ".join(results)
            self.log_test("Forward Geocoding - Mobile App Format", all_passed, details)
            return all_passed
            
        except Exception as e:
            self.log_test("Forward Geocoding - Mobile App Format", False, str(e))
            return False

    def test_restaurant_search_enhanced_radius(self):
        """Test restaurant search with enhanced radius parameters for mobile app"""
        try:
            # Test different radius values that mobile app uses
            radius_tests = [
                {"radius": 1609, "name": "1 mile"},
                {"radius": 8047, "name": "5 miles"},
                {"radius": 25000, "name": "15.5 miles"},
                {"radius": 40234, "name": "25 miles"}
            ]
            
            base_params = {
                'latitude': 37.7749,
                'longitude': -122.4194
            }
            
            all_passed = True
            results = []
            
            for radius_test in radius_tests:
                params = {**base_params, 'radius': radius_test['radius']}
                response = self.session.get(f"{self.api_url}/restaurants/search", params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    restaurants = data.get('restaurants', [])
                    total = len(restaurants)
                    
                    # Verify response includes specials_message field for mobile display
                    if restaurants:
                        first_restaurant = restaurants[0]
                        if 'specials_message' not in first_restaurant:
                            all_passed = False
                            results.append(f"{radius_test['name']}: Missing specials_message field")
                        else:
                            results.append(f"{radius_test['name']}: {total} restaurants with specials_message")
                    else:
                        results.append(f"{radius_test['name']}: 0 restaurants")
                else:
                    all_passed = False
                    results.append(f"{radius_test['name']}: Error {response.status_code}")
            
            details = "; ".join(results)
            self.log_test("Restaurant Search - Enhanced Radius Selection", all_passed, details)
            return all_passed
            
        except Exception as e:
            self.log_test("Restaurant Search - Enhanced Radius Selection", False, str(e))
            return False

    def test_restaurant_search_special_type_filtering(self):
        """Test restaurant search with special_type filtering for mobile app dropdown"""
        try:
            # Get available special types first
            types_response = self.session.get(f"{self.api_url}/specials/types")
            if types_response.status_code != 200:
                self.log_test("Restaurant Search - Special Type Filtering", False, "Could not get special types")
                return False
            
            special_types_data = types_response.json()
            special_types = special_types_data.get('special_types', [])
            
            if not special_types:
                self.log_test("Restaurant Search - Special Type Filtering", False, "No special types available")
                return False
            
            base_params = {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'radius': 8047
            }
            
            all_passed = True
            results = []
            
            # Test each special type
            for special_type in special_types[:3]:  # Test first 3 types
                params = {**base_params, 'special_type': special_type['value']}
                response = self.session.get(f"{self.api_url}/restaurants/search", params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    restaurants = data.get('restaurants', [])
                    
                    # Verify filtering works correctly
                    filtered_correctly = True
                    for restaurant in restaurants:
                        specials = restaurant.get('specials', [])
                        if specials:  # Only check restaurants with specials
                            for special in specials:
                                if special.get('special_type') != special_type['value']:
                                    filtered_correctly = False
                                    break
                    
                    if filtered_correctly:
                        results.append(f"{special_type['label']}: {len(restaurants)} restaurants (filtered correctly)")
                    else:
                        all_passed = False
                        results.append(f"{special_type['label']}: Filtering failed")
                else:
                    all_passed = False
                    results.append(f"{special_type['label']}: Error {response.status_code}")
            
            details = "; ".join(results)
            self.log_test("Restaurant Search - Special Type Filtering", all_passed, details)
            return all_passed
            
        except Exception as e:
            self.log_test("Restaurant Search - Special Type Filtering", False, str(e))
            return False

    def test_restaurant_search_vendor_type_filtering(self):
        """Test restaurant search with vendor_type filtering (all, permanent, mobile)"""
        try:
            base_params = {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'radius': 8047
            }
            
            vendor_types = ['all', 'permanent', 'mobile']
            all_passed = True
            results = []
            
            for vendor_type in vendor_types:
                params = {**base_params, 'vendor_type': vendor_type}
                response = self.session.get(f"{self.api_url}/restaurants/search", params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    restaurants = data.get('restaurants', [])
                    
                    # Verify vendor type filtering
                    if vendor_type == 'mobile':
                        # Should only return mobile vendors
                        mobile_count = sum(1 for r in restaurants if r.get('is_mobile_vendor', False) or r.get('vendor_type') == 'mobile')
                        if mobile_count == len(restaurants) or len(restaurants) == 0:
                            results.append(f"Mobile: {len(restaurants)} restaurants (all mobile or none found)")
                        else:
                            all_passed = False
                            results.append(f"Mobile: {mobile_count}/{len(restaurants)} are mobile (filtering failed)")
                    
                    elif vendor_type == 'permanent':
                        # Should only return permanent vendors
                        permanent_count = sum(1 for r in restaurants if not r.get('is_mobile_vendor', False) and r.get('vendor_type') != 'mobile')
                        if permanent_count == len(restaurants):
                            results.append(f"Permanent: {len(restaurants)} restaurants (all permanent)")
                        else:
                            all_passed = False
                            results.append(f"Permanent: {permanent_count}/{len(restaurants)} are permanent (filtering failed)")
                    
                    else:  # 'all'
                        results.append(f"All: {len(restaurants)} restaurants")
                else:
                    all_passed = False
                    results.append(f"{vendor_type}: Error {response.status_code}")
            
            details = "; ".join(results)
            self.log_test("Restaurant Search - Vendor Type Filtering", all_passed, details)
            return all_passed
            
        except Exception as e:
            self.log_test("Restaurant Search - Vendor Type Filtering", False, str(e))
            return False

    def test_special_types_api_mobile_format(self):
        """Test Special Types API for mobile app dropdown"""
        try:
            response = self.session.get(f"{self.api_url}/specials/types")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                special_types = data.get('special_types', [])
                
                if not special_types:
                    success = False
                    details = "No special types returned"
                else:
                    # Verify mobile app expected format (value and label fields)
                    all_have_required_fields = True
                    for special_type in special_types:
                        if 'value' not in special_type or 'label' not in special_type:
                            all_have_required_fields = False
                            break
                    
                    if all_have_required_fields:
                        details = f"Found {len(special_types)} special types with proper mobile format: {[st['label'] for st in special_types]}"
                    else:
                        success = False
                        details = "Special types missing required 'value' or 'label' fields for mobile app"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Special Types API - Mobile App Format", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Special Types API - Mobile App Format", False, str(e))
            return False, {}

    def test_enhanced_restaurant_data_fields(self):
        """Test that restaurant objects include all fields needed for mobile app"""
        try:
            params = {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'radius': 8047
            }
            
            response = self.session.get(f"{self.api_url}/restaurants/search", params=params)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                restaurants = data.get('restaurants', [])
                
                if not restaurants:
                    success = False
                    details = "No restaurants returned for testing"
                else:
                    # Check required fields for mobile app
                    required_fields = [
                        'id', 'name', 'address', 'location', 'specials_message', 
                        'cuisine_type', 'distance', 'rating'
                    ]
                    
                    all_restaurants_valid = True
                    missing_fields_summary = {}
                    
                    for restaurant in restaurants[:5]:  # Check first 5 restaurants
                        missing_fields = [field for field in required_fields if field not in restaurant]
                        if missing_fields:
                            all_restaurants_valid = False
                            for field in missing_fields:
                                missing_fields_summary[field] = missing_fields_summary.get(field, 0) + 1
                    
                    if all_restaurants_valid:
                        # Check for mobile vendor detection
                        mobile_vendors = [r for r in restaurants if r.get('is_mobile_vendor', False)]
                        details = f"All {len(restaurants)} restaurants have required mobile app fields. Mobile vendors detected: {len(mobile_vendors)}"
                    else:
                        success = False
                        details = f"Missing fields in restaurants: {dict(missing_fields_summary)}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Enhanced Restaurant Data - Mobile App Fields", success, details)
            return success
            
        except Exception as e:
            self.log_test("Enhanced Restaurant Data - Mobile App Fields", False, str(e))
            return False

    def test_mobile_search_parameter_combinations(self):
        """Test search with various mobile app parameter combinations"""
        try:
            # Test different combinations of parameters
            test_combinations = [
                {
                    'name': 'Radius + Special Type',
                    'params': {
                        'latitude': 37.7749,
                        'longitude': -122.4194,
                        'radius': 1609,
                        'special_type': 'happy_hour'
                    }
                },
                {
                    'name': 'Radius + Vendor Type',
                    'params': {
                        'latitude': 37.7749,
                        'longitude': -122.4194,
                        'radius': 8047,
                        'vendor_type': 'permanent'
                    }
                },
                {
                    'name': 'All Filters Combined',
                    'params': {
                        'latitude': 37.7749,
                        'longitude': -122.4194,
                        'radius': 25000,
                        'special_type': 'lunch_special',
                        'vendor_type': 'all'
                    }
                },
                {
                    'name': 'Large Radius Mobile Search',
                    'params': {
                        'latitude': 37.7749,
                        'longitude': -122.4194,
                        'radius': 40234,
                        'vendor_type': 'mobile'
                    }
                }
            ]
            
            all_passed = True
            results = []
            
            for test_case in test_combinations:
                response = self.session.get(f"{self.api_url}/restaurants/search", params=test_case['params'])
                
                if response.status_code == 200:
                    data = response.json()
                    restaurants = data.get('restaurants', [])
                    
                    # Verify response structure for mobile app
                    required_response_fields = ['restaurants', 'total', 'search_location', 'radius_meters']
                    missing_response_fields = [field for field in required_response_fields if field not in data]
                    
                    if missing_response_fields:
                        all_passed = False
                        results.append(f"{test_case['name']}: Missing response fields {missing_response_fields}")
                    else:
                        results.append(f"{test_case['name']}: {len(restaurants)} restaurants found")
                else:
                    all_passed = False
                    results.append(f"{test_case['name']}: Error {response.status_code}")
            
            details = "; ".join(results)
            self.log_test("Mobile Search Parameter Combinations", all_passed, details)
            return all_passed
            
        except Exception as e:
            self.log_test("Mobile Search Parameter Combinations", False, str(e))
            return False

    def test_mobile_search_edge_cases(self):
        """Test edge cases for mobile app search"""
        try:
            edge_cases = [
                {
                    'name': 'Minimum Radius',
                    'params': {
                        'latitude': 37.7749,
                        'longitude': -122.4194,
                        'radius': 100  # Minimum allowed
                    },
                    'expected_status': 200
                },
                {
                    'name': 'Maximum Radius',
                    'params': {
                        'latitude': 37.7749,
                        'longitude': -122.4194,
                        'radius': 80467  # Maximum allowed
                    },
                    'expected_status': 200
                },
                {
                    'name': 'Invalid Vendor Type',
                    'params': {
                        'latitude': 37.7749,
                        'longitude': -122.4194,
                        'radius': 8047,
                        'vendor_type': 'invalid_type'
                    },
                    'expected_status': 422  # Validation error
                },
                {
                    'name': 'Invalid Special Type',
                    'params': {
                        'latitude': 37.7749,
                        'longitude': -122.4194,
                        'radius': 8047,
                        'special_type': 'invalid_special'
                    },
                    'expected_status': 422  # Validation error
                }
            ]
            
            all_passed = True
            results = []
            
            for case in edge_cases:
                response = self.session.get(f"{self.api_url}/restaurants/search", params=case['params'])
                
                if response.status_code == case['expected_status']:
                    if case['expected_status'] == 200:
                        data = response.json()
                        count = len(data.get('restaurants', []))
                        results.append(f"{case['name']}: {count} results (✓)")
                    else:
                        results.append(f"{case['name']}: Correctly rejected (✓)")
                else:
                    all_passed = False
                    results.append(f"{case['name']}: Expected {case['expected_status']}, got {response.status_code}")
            
            details = "; ".join(results)
            self.log_test("Mobile Search Edge Cases", all_passed, details)
            return all_passed
            
        except Exception as e:
            self.log_test("Mobile Search Edge Cases", False, str(e))
            return False

    def test_specials_information_in_search_results(self):
        """Test that specials information is properly included in restaurant search results"""
        try:
            params = {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'radius': 8047
            }
            
            response = self.session.get(f"{self.api_url}/restaurants/search", params=params)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                restaurants = data.get('restaurants', [])
                
                if not restaurants:
                    success = False
                    details = "No restaurants returned for testing"
                else:
                    # Check specials information
                    restaurants_with_specials = 0
                    restaurants_with_specials_message = 0
                    specials_message_types = set()
                    
                    for restaurant in restaurants:
                        if restaurant.get('specials'):
                            restaurants_with_specials += 1
                        
                        specials_message = restaurant.get('specials_message')
                        if specials_message:
                            restaurants_with_specials_message += 1
                            specials_message_types.add(specials_message)
                    
                    # Verify specials summary data
                    specials_summary = data.get('specials_summary', {})
                    summary_fields = ['with_specials', 'no_specials', 'external_restaurants']
                    missing_summary_fields = [field for field in summary_fields if field not in specials_summary]
                    
                    if missing_summary_fields:
                        success = False
                        details = f"Missing specials_summary fields: {missing_summary_fields}"
                    else:
                        details = f"Found {len(restaurants)} restaurants: {restaurants_with_specials} with specials, {restaurants_with_specials_message} with specials_message. Summary: {specials_summary}. Message types: {list(specials_message_types)}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Specials Information in Search Results", success, details)
            return success
            
        except Exception as e:
            self.log_test("Specials Information in Search Results", False, str(e))
            return False

    def run_all_tests(self):
        """Run all mobile app enhancement tests"""
        print("🚀 Starting Mobile App Enhanced Search Features Backend API Tests")
        print(f"Testing against: {self.base_url}")
        print("=" * 80)
        
        # Run all tests
        test_methods = [
            self.test_forward_geocoding_mobile_format,
            self.test_restaurant_search_enhanced_radius,
            self.test_restaurant_search_special_type_filtering,
            self.test_restaurant_search_vendor_type_filtering,
            self.test_special_types_api_mobile_format,
            self.test_enhanced_restaurant_data_fields,
            self.test_mobile_search_parameter_combinations,
            self.test_mobile_search_edge_cases,
            self.test_specials_information_in_search_results
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"❌ {test_method.__name__} - EXCEPTION: {str(e)}")
                self.tests_run += 1
        
        # Print summary
        print("=" * 80)
        print(f"📊 Mobile App Enhancement Tests Summary:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "No tests run")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All mobile app enhancement tests passed!")
            return True
        else:
            print("⚠️  Some mobile app enhancement tests failed. Check the details above.")
            return False

def main():
    """Main function to run the mobile app enhancement tests"""
    tester = MobileAppAPITester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()