#!/usr/bin/env python3
"""
Detailed Mobile App Backend API Testing
Focused tests for specific mobile app requirements from the review request
"""

import requests
import sys
import json
from datetime import datetime

class DetailedMobileAppTester:
    def __init__(self, base_url="https://stable-baseline.preview.emergentagent.com"):
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

    def test_forward_geocoding_address_input_component(self):
        """Test forward geocoding specifically for AddressInput component expectations"""
        try:
            # Test address formats that AddressInput component would send
            test_cases = [
                {
                    'address': 'San Francisco, CA',
                    'description': 'City search'
                },
                {
                    'address': '123 Market Street, San Francisco, CA',
                    'description': 'Full address'
                },
                {
                    'address': 'Market Street',
                    'description': 'Partial address',
                    'region': 'US'
                }
            ]
            
            all_passed = True
            results = []
            
            for case in test_cases:
                test_data = {'address': case['address']}
                if 'region' in case:
                    test_data['region'] = case['region']
                
                response = self.session.post(f"{self.api_url}/geocode/forward", json=test_data)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verify exact format expected by mobile AddressInput
                    required_fields = ['formatted_address', 'latitude', 'longitude', 'place_id']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        all_passed = False
                        results.append(f"{case['description']}: Missing {missing_fields}")
                    else:
                        # Verify data types for mobile app
                        lat = data['latitude']
                        lng = data['longitude']
                        if not isinstance(lat, (int, float)) or not isinstance(lng, (int, float)):
                            all_passed = False
                            results.append(f"{case['description']}: Invalid coordinate types")
                        else:
                            results.append(f"{case['description']}: ✓ {data['formatted_address']}")
                
                elif response.status_code == 404:
                    # Acceptable for some partial addresses
                    results.append(f"{case['description']}: Not found (acceptable)")
                else:
                    all_passed = False
                    results.append(f"{case['description']}: Error {response.status_code}")
            
            details = "; ".join(results)
            self.log_test("Forward Geocoding - AddressInput Component Format", all_passed, details)
            return all_passed
            
        except Exception as e:
            self.log_test("Forward Geocoding - AddressInput Component Format", False, str(e))
            return False

    def test_restaurant_search_radius_meters_specific(self):
        """Test specific radius values mentioned in review request"""
        try:
            # Test exact radius values from review request
            radius_values = [
                {'meters': 1609, 'description': '1mi'},
                {'meters': 8047, 'description': '5mi'},
                {'meters': 25000, 'description': '15.5mi'},
                {'meters': 40234, 'description': '25mi'}
            ]
            
            base_params = {
                'latitude': 37.7749,
                'longitude': -122.4194
            }
            
            all_passed = True
            results = []
            previous_count = 0
            
            for radius in radius_values:
                params = {**base_params, 'radius': radius['meters']}
                response = self.session.get(f"{self.api_url}/restaurants/search", params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    restaurants = data.get('restaurants', [])
                    count = len(restaurants)
                    
                    # Verify radius_meters field in response
                    if data.get('radius_meters') != radius['meters']:
                        all_passed = False
                        results.append(f"{radius['description']}: Radius mismatch in response")
                    else:
                        results.append(f"{radius['description']}: {count} restaurants")
                        
                        # Verify distance calculation for mobile app
                        for restaurant in restaurants[:3]:  # Check first 3
                            distance = restaurant.get('distance')
                            if distance is None or distance > radius['meters']:
                                all_passed = False
                                results.append(f"{radius['description']}: Restaurant outside radius")
                                break
                    
                    previous_count = count
                else:
                    all_passed = False
                    results.append(f"{radius['description']}: Error {response.status_code}")
            
            details = "; ".join(results)
            self.log_test("Restaurant Search - Specific Radius Values", all_passed, details)
            return all_passed
            
        except Exception as e:
            self.log_test("Restaurant Search - Specific Radius Values", False, str(e))
            return False

    def test_special_types_dropdown_format(self):
        """Test special types API format for mobile app dropdown"""
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
                    # Verify exact format for mobile dropdown
                    all_valid = True
                    dropdown_items = []
                    
                    for item in special_types:
                        # Must have 'value' and 'label' fields for dropdown
                        if 'value' not in item or 'label' not in item:
                            all_valid = False
                            break
                        
                        # Verify data types
                        if not isinstance(item['value'], str) or not isinstance(item['label'], str):
                            all_valid = False
                            break
                        
                        dropdown_items.append(f"{item['label']} ({item['value']})")
                    
                    if all_valid:
                        details = f"Found {len(special_types)} dropdown items: {', '.join(dropdown_items)}"
                    else:
                        success = False
                        details = "Invalid format for mobile dropdown"
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test("Special Types - Mobile Dropdown Format", success, details)
            return success
            
        except Exception as e:
            self.log_test("Special Types - Mobile Dropdown Format", False, str(e))
            return False

    def test_restaurant_data_mobile_card_fields(self):
        """Test restaurant data includes all fields for mobile RestaurantCard"""
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
                    details = "No restaurants for testing"
                else:
                    # Check fields needed for mobile RestaurantCard
                    required_fields = [
                        'id', 'name', 'address', 'location', 'specials_message',
                        'cuisine_type', 'distance', 'rating', 'is_mobile_vendor'
                    ]
                    
                    all_valid = True
                    field_coverage = {}
                    
                    for restaurant in restaurants[:5]:  # Check first 5
                        for field in required_fields:
                            if field in restaurant:
                                field_coverage[field] = field_coverage.get(field, 0) + 1
                            else:
                                all_valid = False
                    
                    if all_valid:
                        # Check specific mobile card requirements
                        mobile_vendors = sum(1 for r in restaurants if r.get('is_mobile_vendor', False))
                        has_specials_msg = sum(1 for r in restaurants if r.get('specials_message'))
                        
                        details = f"All restaurants have required fields. Mobile vendors: {mobile_vendors}, With specials_message: {has_specials_msg}"
                    else:
                        missing_fields = [f for f in required_fields if field_coverage.get(f, 0) < 5]
                        success = False
                        details = f"Missing fields in some restaurants: {missing_fields}"
            else:
                details = f"Status: {response.status_code}"
            
            self.log_test("Restaurant Data - Mobile Card Fields", success, details)
            return success
            
        except Exception as e:
            self.log_test("Restaurant Data - Mobile Card Fields", False, str(e))
            return False

    def test_vendor_type_filtering_combinations(self):
        """Test vendor_type filtering with all combinations"""
        try:
            base_params = {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'radius': 8047
            }
            
            # Test all vendor type combinations
            test_cases = [
                {'vendor_type': 'all', 'description': 'All venues'},
                {'vendor_type': 'permanent', 'description': 'Restaurants only'},
                {'vendor_type': 'mobile', 'description': 'Food trucks & pop-ups'}
            ]
            
            all_passed = True
            results = []
            all_count = 0
            
            for case in test_cases:
                params = {**base_params, 'vendor_type': case['vendor_type']}
                response = self.session.get(f"{self.api_url}/restaurants/search", params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    restaurants = data.get('restaurants', [])
                    count = len(restaurants)
                    
                    if case['vendor_type'] == 'all':
                        all_count = count
                        results.append(f"{case['description']}: {count} total")
                    
                    elif case['vendor_type'] == 'mobile':
                        # Verify all returned are mobile vendors
                        mobile_count = sum(1 for r in restaurants if r.get('is_mobile_vendor', False) or r.get('vendor_type') == 'mobile')
                        if mobile_count == count or count == 0:
                            results.append(f"{case['description']}: {count} mobile vendors")
                        else:
                            all_passed = False
                            results.append(f"{case['description']}: {mobile_count}/{count} are mobile (filtering failed)")
                    
                    elif case['vendor_type'] == 'permanent':
                        # Verify all returned are permanent venues
                        permanent_count = sum(1 for r in restaurants if not r.get('is_mobile_vendor', False) and r.get('vendor_type') != 'mobile')
                        if permanent_count == count:
                            results.append(f"{case['description']}: {count} permanent venues")
                        else:
                            all_passed = False
                            results.append(f"{case['description']}: {permanent_count}/{count} are permanent (filtering failed)")
                else:
                    all_passed = False
                    results.append(f"{case['description']}: Error {response.status_code}")
            
            details = "; ".join(results)
            self.log_test("Vendor Type Filtering - All Combinations", all_passed, details)
            return all_passed
            
        except Exception as e:
            self.log_test("Vendor Type Filtering - All Combinations", False, str(e))
            return False

    def test_coordinate_search_parameters(self):
        """Test search with coordinate parameters for mobile app"""
        try:
            # Test different coordinate locations
            test_locations = [
                {'lat': 37.7749, 'lng': -122.4194, 'name': 'San Francisco'},
                {'lat': 40.7128, 'lng': -74.0060, 'name': 'New York'},
                {'lat': 41.8781, 'lng': -87.6298, 'name': 'Chicago'},
                {'lat': 34.0522, 'lng': -118.2437, 'name': 'Los Angeles'}
            ]
            
            all_passed = True
            results = []
            
            for location in test_locations:
                params = {
                    'latitude': location['lat'],
                    'longitude': location['lng'],
                    'radius': 8047  # 5 miles
                }
                
                response = self.session.get(f"{self.api_url}/restaurants/search", params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    restaurants = data.get('restaurants', [])
                    
                    # Verify search_location in response
                    search_location = data.get('search_location', {})
                    if (search_location.get('latitude') != location['lat'] or 
                        search_location.get('longitude') != location['lng']):
                        all_passed = False
                        results.append(f"{location['name']}: Search location mismatch")
                    else:
                        results.append(f"{location['name']}: {len(restaurants)} restaurants")
                else:
                    all_passed = False
                    results.append(f"{location['name']}: Error {response.status_code}")
            
            details = "; ".join(results)
            self.log_test("Coordinate Search Parameters", all_passed, details)
            return all_passed
            
        except Exception as e:
            self.log_test("Coordinate Search Parameters", False, str(e))
            return False

    def test_filtering_combinations_edge_cases(self):
        """Test edge cases with various radius and filter combinations"""
        try:
            # Test complex filtering combinations
            test_cases = [
                {
                    'name': 'Small radius + Special type',
                    'params': {
                        'latitude': 37.7749,
                        'longitude': -122.4194,
                        'radius': 1609,  # 1 mile
                        'special_type': 'happy_hour'
                    }
                },
                {
                    'name': 'Large radius + Mobile vendors',
                    'params': {
                        'latitude': 37.7749,
                        'longitude': -122.4194,
                        'radius': 40234,  # 25 miles
                        'vendor_type': 'mobile'
                    }
                },
                {
                    'name': 'Medium radius + All filters',
                    'params': {
                        'latitude': 37.7749,
                        'longitude': -122.4194,
                        'radius': 25000,  # 15.5 miles
                        'special_type': 'weekend_special',
                        'vendor_type': 'permanent'
                    }
                }
            ]
            
            all_passed = True
            results = []
            
            for case in test_cases:
                response = self.session.get(f"{self.api_url}/restaurants/search", params=case['params'])
                
                if response.status_code == 200:
                    data = response.json()
                    restaurants = data.get('restaurants', [])
                    
                    # Verify response structure
                    required_fields = ['restaurants', 'total', 'search_location', 'radius_meters', 'specials_summary']
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        all_passed = False
                        results.append(f"{case['name']}: Missing {missing_fields}")
                    else:
                        results.append(f"{case['name']}: {len(restaurants)} results")
                else:
                    all_passed = False
                    results.append(f"{case['name']}: Error {response.status_code}")
            
            details = "; ".join(results)
            self.log_test("Filtering Combinations - Edge Cases", all_passed, details)
            return all_passed
            
        except Exception as e:
            self.log_test("Filtering Combinations - Edge Cases", False, str(e))
            return False

    def run_all_tests(self):
        """Run all detailed mobile app tests"""
        print("🔍 Starting Detailed Mobile App Backend API Tests")
        print(f"Testing against: {self.base_url}")
        print("=" * 80)
        
        # Run all tests
        test_methods = [
            self.test_forward_geocoding_address_input_component,
            self.test_restaurant_search_radius_meters_specific,
            self.test_special_types_dropdown_format,
            self.test_restaurant_data_mobile_card_fields,
            self.test_vendor_type_filtering_combinations,
            self.test_coordinate_search_parameters,
            self.test_filtering_combinations_edge_cases
        ]
        
        for test_method in test_methods:
            try:
                test_method()
            except Exception as e:
                print(f"❌ {test_method.__name__} - EXCEPTION: {str(e)}")
                self.tests_run += 1
        
        # Print summary
        print("=" * 80)
        print(f"📊 Detailed Mobile App Tests Summary:")
        print(f"   Tests Run: {self.tests_run}")
        print(f"   Tests Passed: {self.tests_passed}")
        print(f"   Tests Failed: {self.tests_run - self.tests_passed}")
        print(f"   Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%" if self.tests_run > 0 else "No tests run")
        
        return self.tests_passed == self.tests_run

def main():
    """Main function to run the detailed mobile app tests"""
    tester = DetailedMobileAppTester()
    success = tester.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()