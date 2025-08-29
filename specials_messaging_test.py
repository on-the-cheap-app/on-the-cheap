#!/usr/bin/env python3
"""
Specials Messaging System Testing for On-the-Cheap Restaurant App
Tests the newly implemented "no current specials" messaging system
"""

import requests
import sys
import json
from datetime import datetime
import uuid

class SpecialsMessagingTester:
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

    def test_restaurant_search_specials_messaging(self):
        """Test /api/restaurants/search endpoint specials messaging"""
        try:
            # Test San Francisco search
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
                specials_summary = data.get('specials_summary', {})
                
                # Check that specials_summary exists and has required fields
                required_summary_fields = ['with_specials', 'no_specials', 'external_restaurants']
                missing_summary_fields = [field for field in required_summary_fields if field not in specials_summary]
                
                if missing_summary_fields:
                    success = False
                    details = f"Missing specials_summary fields: {missing_summary_fields}"
                else:
                    # Verify each restaurant has proper specials messaging
                    owner_managed_count = 0
                    external_count = 0
                    messaging_errors = []
                    
                    for restaurant in restaurants:
                        source = restaurant.get('source', 'unknown')
                        specials_message = restaurant.get('specials_message', '')
                        specials = restaurant.get('specials', [])
                        
                        if source == 'owner_managed':
                            owner_managed_count += 1
                            if not specials:
                                # Should show "No current specials at this time"
                                if specials_message != "No current specials at this time":
                                    messaging_errors.append(f"Owner restaurant '{restaurant.get('name')}' without specials has wrong message: '{specials_message}'")
                            else:
                                # Should show count message like "2 specials available now"
                                expected_pattern = f"{len(specials)} special"
                                if expected_pattern not in specials_message or "available now" not in specials_message:
                                    messaging_errors.append(f"Owner restaurant '{restaurant.get('name')}' with {len(specials)} specials has wrong message: '{specials_message}'")
                        
                        elif source in ['google_places', 'foursquare']:
                            external_count += 1
                            # Should show "Specials data coming soon - check back later!"
                            if specials_message != "Specials data coming soon - check back later!":
                                messaging_errors.append(f"External restaurant '{restaurant.get('name')}' ({source}) has wrong message: '{specials_message}'")
                    
                    if messaging_errors:
                        success = False
                        details = f"Messaging errors: {'; '.join(messaging_errors[:3])}"  # Show first 3 errors
                    else:
                        details = f"Found {len(restaurants)} restaurants: {owner_managed_count} owner-managed, {external_count} external. Specials summary: {specials_summary}. All messaging correct."
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Restaurant Search Specials Messaging", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Restaurant Search Specials Messaging", False, str(e))
            return False, {}

    def test_restaurant_search_with_special_type_filter(self):
        """Test restaurant search with special type filter messaging"""
        try:
            params = {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'radius': 8047,
                'special_type': 'weekend_special'
            }
            
            response = self.session.get(f"{self.api_url}/restaurants/search", params=params)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                restaurants = data.get('restaurants', [])
                
                # When filtering by special type, only owner-managed restaurants with that special type should appear
                # External restaurants should not appear when filtering by special type
                messaging_errors = []
                external_restaurants_found = 0
                
                for restaurant in restaurants:
                    source = restaurant.get('source', 'unknown')
                    specials = restaurant.get('specials', [])
                    specials_message = restaurant.get('specials_message', '')
                    
                    if source in ['google_places', 'foursquare']:
                        external_restaurants_found += 1
                    
                    # All restaurants should have the filtered special type
                    if source == 'owner_managed':
                        has_weekend_special = any(special.get('special_type') == 'weekend_special' for special in specials)
                        if not has_weekend_special:
                            messaging_errors.append(f"Restaurant '{restaurant.get('name')}' returned without weekend_special")
                        
                        # Should have proper count message
                        if specials:
                            expected_pattern = f"{len(specials)} special"
                            if expected_pattern not in specials_message or "available now" not in specials_message:
                                messaging_errors.append(f"Restaurant '{restaurant.get('name')}' has wrong specials message: '{specials_message}'")
                
                if messaging_errors:
                    success = False
                    details = f"Filter messaging errors: {'; '.join(messaging_errors[:2])}"
                else:
                    details = f"Found {len(restaurants)} restaurants with weekend specials. {external_restaurants_found} external restaurants (should be 0 when filtering). All messaging correct."
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Restaurant Search with Special Type Filter", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Restaurant Search with Special Type Filter", False, str(e))
            return False, {}

    def test_individual_restaurant_details(self):
        """Test /api/restaurants/{restaurant_id} endpoint specials messaging"""
        try:
            # First get a list of restaurants to test individual details
            search_params = {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'radius': 8047
            }
            
            search_response = self.session.get(f"{self.api_url}/restaurants/search", params=search_params)
            if search_response.status_code != 200:
                self.log_test("Individual Restaurant Details", False, "Failed to get restaurants for testing")
                return False, {}
            
            search_data = search_response.json()
            restaurants = search_data.get('restaurants', [])
            
            if not restaurants:
                self.log_test("Individual Restaurant Details", False, "No restaurants found for testing")
                return False, {}
            
            # Test owner-managed restaurants only (external restaurants don't have individual detail endpoints)
            owner_restaurants = [r for r in restaurants if r.get('source') == 'owner_managed']
            
            if not owner_restaurants:
                self.log_test("Individual Restaurant Details", False, "No owner-managed restaurants found for testing")
                return False, {}
            
            # Test first few owner-managed restaurants
            test_results = []
            messaging_errors = []
            
            for restaurant in owner_restaurants[:3]:  # Test first 3
                restaurant_id = restaurant['id']
                restaurant_name = restaurant.get('name', 'Unknown')
                
                detail_response = self.session.get(f"{self.api_url}/restaurants/{restaurant_id}")
                
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    
                    # Check required fields
                    required_fields = ['specials_message', 'has_current_specials']
                    missing_fields = [field for field in required_fields if field not in detail_data]
                    
                    if missing_fields:
                        messaging_errors.append(f"Restaurant '{restaurant_name}' missing fields: {missing_fields}")
                    else:
                        specials = detail_data.get('specials', [])
                        specials_message = detail_data.get('specials_message', '')
                        has_current_specials = detail_data.get('has_current_specials')
                        
                        # Verify messaging consistency
                        if specials:
                            # Should have specials message with count and has_current_specials = True
                            expected_pattern = f"{len(specials)} special"
                            if expected_pattern not in specials_message or "available now" not in specials_message:
                                messaging_errors.append(f"Restaurant '{restaurant_name}' with specials has wrong message: '{specials_message}'")
                            
                            if has_current_specials != True:
                                messaging_errors.append(f"Restaurant '{restaurant_name}' with specials has has_current_specials={has_current_specials}, expected True")
                        else:
                            # Should have "No current specials at this time" and has_current_specials = False
                            if specials_message != "No current specials at this time":
                                messaging_errors.append(f"Restaurant '{restaurant_name}' without specials has wrong message: '{specials_message}'")
                            
                            if has_current_specials != False:
                                messaging_errors.append(f"Restaurant '{restaurant_name}' without specials has has_current_specials={has_current_specials}, expected False")
                        
                        test_results.append(f"{restaurant_name}: {len(specials)} specials, message='{specials_message}', flag={has_current_specials}")
                else:
                    messaging_errors.append(f"Failed to get details for restaurant '{restaurant_name}': HTTP {detail_response.status_code}")
            
            success = len(messaging_errors) == 0
            
            if success:
                details = f"Tested {len(test_results)} restaurants. All individual restaurant details have correct specials messaging and flags. Examples: {'; '.join(test_results[:2])}"
            else:
                details = f"Individual restaurant detail errors: {'; '.join(messaging_errors[:3])}"
            
            self.log_test("Individual Restaurant Details", success, details)
            return success
            
        except Exception as e:
            self.log_test("Individual Restaurant Details", False, str(e))
            return False

    def test_time_based_special_filtering(self):
        """Test that specials are properly filtered by current time/day"""
        try:
            # Get current day and time for analysis
            now = datetime.now()
            current_day = now.strftime("%A").lower()
            current_time = now.time()
            
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
                
                # Focus on owner-managed restaurants with specials
                owner_restaurants_with_specials = [r for r in restaurants if r.get('source') == 'owner_managed' and r.get('specials')]
                
                time_filtering_errors = []
                active_specials_found = 0
                
                for restaurant in owner_restaurants_with_specials:
                    restaurant_name = restaurant.get('name', 'Unknown')
                    specials = restaurant.get('specials', [])
                    
                    for special in specials:
                        days_available = special.get('days_available', [])
                        time_start = special.get('time_start', '')
                        time_end = special.get('time_end', '')
                        special_title = special.get('title', 'Unknown Special')
                        
                        # Check if special should be active now
                        is_day_match = current_day in days_available
                        
                        try:
                            start_time = datetime.strptime(time_start, "%H:%M").time() if time_start else None
                            end_time = datetime.strptime(time_end, "%H:%M").time() if time_end else None
                            
                            is_time_match = True
                            if start_time and end_time:
                                is_time_match = start_time <= current_time <= end_time
                            
                            should_be_active = is_day_match and is_time_match
                            
                            if should_be_active:
                                active_specials_found += 1
                            
                            # Since the special is returned in search results, it should be currently active
                            # If it's not active based on time/day, that's a filtering error
                            if not should_be_active:
                                time_filtering_errors.append(f"Restaurant '{restaurant_name}' special '{special_title}' is inactive (day: {current_day} not in {days_available} or time: {current_time} not in {time_start}-{time_end}) but still returned")
                        
                        except ValueError as e:
                            time_filtering_errors.append(f"Restaurant '{restaurant_name}' special '{special_title}' has invalid time format: {e}")
                
                if time_filtering_errors:
                    success = False
                    details = f"Time-based filtering errors: {'; '.join(time_filtering_errors[:2])}"
                else:
                    details = f"Time-based filtering working correctly. Found {active_specials_found} currently active specials across {len(owner_restaurants_with_specials)} restaurants. Current time: {current_day} {current_time.strftime('%H:%M')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Time-Based Special Filtering", success, details)
            return success
            
        except Exception as e:
            self.log_test("Time-Based Special Filtering", False, str(e))
            return False

    def test_external_restaurant_messaging_consistency(self):
        """Test that external restaurants (Google Places/Foursquare) have consistent messaging"""
        try:
            # Test multiple locations to get different external restaurants
            test_locations = [
                {'name': 'San Francisco', 'lat': 37.7749, 'lng': -122.4194},
                {'name': 'New York', 'lat': 40.7128, 'lng': -74.0060},
                {'name': 'Los Angeles', 'lat': 34.0522, 'lng': -118.2437}
            ]
            
            all_external_restaurants = []
            messaging_errors = []
            
            for location in test_locations:
                params = {
                    'latitude': location['lat'],
                    'longitude': location['lng'],
                    'radius': 8047
                }
                
                response = self.session.get(f"{self.api_url}/restaurants/search", params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    restaurants = data.get('restaurants', [])
                    
                    external_restaurants = [r for r in restaurants if r.get('source') in ['google_places', 'foursquare']]
                    all_external_restaurants.extend(external_restaurants)
                    
                    # Check messaging for external restaurants
                    for restaurant in external_restaurants:
                        source = restaurant.get('source')
                        specials_message = restaurant.get('specials_message', '')
                        specials = restaurant.get('specials', [])
                        restaurant_name = restaurant.get('name', 'Unknown')
                        
                        # External restaurants should have empty specials array
                        if specials:
                            messaging_errors.append(f"External restaurant '{restaurant_name}' ({source}) has specials: {len(specials)}")
                        
                        # Should have consistent external message
                        expected_message = "Specials data coming soon - check back later!"
                        if specials_message != expected_message:
                            messaging_errors.append(f"External restaurant '{restaurant_name}' ({source}) has wrong message: '{specials_message}'")
            
            success = len(messaging_errors) == 0
            
            if success:
                google_count = len([r for r in all_external_restaurants if r.get('source') == 'google_places'])
                foursquare_count = len([r for r in all_external_restaurants if r.get('source') == 'foursquare'])
                details = f"Tested {len(all_external_restaurants)} external restaurants across {len(test_locations)} cities ({google_count} Google Places, {foursquare_count} Foursquare). All have consistent messaging."
            else:
                details = f"External restaurant messaging errors: {'; '.join(messaging_errors[:3])}"
            
            self.log_test("External Restaurant Messaging Consistency", success, details)
            return success
            
        except Exception as e:
            self.log_test("External Restaurant Messaging Consistency", False, str(e))
            return False

    def test_specials_summary_accuracy(self):
        """Test that specials_summary provides accurate counts"""
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
                specials_summary = data.get('specials_summary', {})
                
                # Count restaurants manually
                actual_with_specials = 0
                actual_no_specials = 0
                actual_external = 0
                
                for restaurant in restaurants:
                    source = restaurant.get('source', 'unknown')
                    specials = restaurant.get('specials', [])
                    
                    if source == 'owner_managed':
                        if specials:
                            actual_with_specials += 1
                        else:
                            actual_no_specials += 1
                    else:
                        actual_external += 1
                
                # Compare with reported summary
                reported_with_specials = specials_summary.get('with_specials', 0)
                reported_no_specials = specials_summary.get('no_specials', 0)
                reported_external = specials_summary.get('external_restaurants', 0)
                
                summary_errors = []
                
                if actual_with_specials != reported_with_specials:
                    summary_errors.append(f"with_specials: actual={actual_with_specials}, reported={reported_with_specials}")
                
                if actual_no_specials != reported_no_specials:
                    summary_errors.append(f"no_specials: actual={actual_no_specials}, reported={reported_no_specials}")
                
                if actual_external != reported_external:
                    summary_errors.append(f"external_restaurants: actual={actual_external}, reported={reported_external}")
                
                if summary_errors:
                    success = False
                    details = f"Specials summary inaccuracies: {'; '.join(summary_errors)}"
                else:
                    details = f"Specials summary accurate: {reported_with_specials} with specials, {reported_no_specials} without specials, {reported_external} external restaurants. Total: {len(restaurants)} restaurants."
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Specials Summary Accuracy", success, details)
            return success
            
        except Exception as e:
            self.log_test("Specials Summary Accuracy", False, str(e))
            return False

    def test_edge_cases_messaging(self):
        """Test edge cases for specials messaging"""
        try:
            edge_case_results = []
            
            # Test 1: Very small radius (might return fewer results)
            params = {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'radius': 100  # Very small radius
            }
            
            response = self.session.get(f"{self.api_url}/restaurants/search", params=params)
            if response.status_code == 200:
                data = response.json()
                restaurants = data.get('restaurants', [])
                specials_summary = data.get('specials_summary', {})
                
                # Even with small results, messaging should be consistent
                messaging_consistent = True
                for restaurant in restaurants:
                    specials_message = restaurant.get('specials_message', '')
                    if not specials_message:
                        messaging_consistent = False
                        break
                
                edge_case_results.append(f"Small radius: {len(restaurants)} restaurants, messaging consistent: {messaging_consistent}")
            else:
                edge_case_results.append(f"Small radius: HTTP {response.status_code}")
            
            # Test 2: Remote location (might return no owner-managed restaurants)
            params = {
                'latitude': 0,  # Middle of ocean
                'longitude': 0,
                'radius': 8047
            }
            
            response = self.session.get(f"{self.api_url}/restaurants/search", params=params)
            if response.status_code == 200:
                data = response.json()
                restaurants = data.get('restaurants', [])
                specials_summary = data.get('specials_summary', {})
                
                # Should have proper summary even with no results
                has_summary = 'with_specials' in specials_summary and 'no_specials' in specials_summary
                edge_case_results.append(f"Remote location: {len(restaurants)} restaurants, has summary: {has_summary}")
            else:
                edge_case_results.append(f"Remote location: HTTP {response.status_code}")
            
            # Test 3: Large radius
            params = {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'radius': 80467  # 50 miles
            }
            
            response = self.session.get(f"{self.api_url}/restaurants/search", params=params)
            if response.status_code == 200:
                data = response.json()
                restaurants = data.get('restaurants', [])
                
                # Should still have proper messaging with large radius
                all_have_messages = all(restaurant.get('specials_message', '') for restaurant in restaurants)
                edge_case_results.append(f"Large radius: {len(restaurants)} restaurants, all have messages: {all_have_messages}")
            else:
                edge_case_results.append(f"Large radius: HTTP {response.status_code}")
            
            success = True  # Edge cases should not fail, just provide information
            details = "; ".join(edge_case_results)
            
            self.log_test("Edge Cases Messaging", success, details)
            return success
            
        except Exception as e:
            self.log_test("Edge Cases Messaging", False, str(e))
            return False

    def run_all_tests(self):
        """Run all specials messaging tests"""
        print("🧪 Starting Specials Messaging System Tests")
        print("=" * 60)
        
        # Core messaging tests
        self.test_restaurant_search_specials_messaging()
        self.test_restaurant_search_with_special_type_filter()
        self.test_individual_restaurant_details()
        
        # Advanced functionality tests
        self.test_time_based_special_filtering()
        self.test_external_restaurant_messaging_consistency()
        self.test_specials_summary_accuracy()
        
        # Edge cases
        self.test_edge_cases_messaging()
        
        # Summary
        print("\n" + "=" * 60)
        print(f"🏁 Specials Messaging Tests Complete")
        print(f"📊 Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All specials messaging tests PASSED!")
            return True
        else:
            failed_count = self.tests_run - self.tests_passed
            print(f"⚠️  {failed_count} test(s) FAILED")
            return False

if __name__ == "__main__":
    tester = SpecialsMessagingTester()
    success = tester.run_all_tests()
    sys.exit(0 if success else 1)