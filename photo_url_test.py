#!/usr/bin/env python3
"""
Photo URL Testing for On-the-Cheap Restaurant Specials Finder
Tests that restaurant search API returns working photo URLs after fixing Google Places photo URL issues
"""

import requests
import sys
import json
from datetime import datetime
import time

class PhotoURLTester:
    def __init__(self, base_url="https://eatdeals-mobile.preview.emergentagent.com"):
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

    def test_photo_url_accessibility(self, url, timeout=10):
        """Test if a photo URL is accessible and returns HTTP 200"""
        try:
            response = requests.head(url, timeout=timeout, allow_redirects=True)
            return response.status_code == 200
        except Exception as e:
            print(f"   Error accessing {url}: {str(e)}")
            return False

    def test_restaurant_search_photos_san_francisco(self):
        """Test restaurant search returns working photos in San Francisco"""
        try:
            params = {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'radius': 8047,  # 5 miles
                'limit': 20
            }
            
            response = self.session.get(f"{self.api_url}/restaurants/search", params=params)
            success = response.status_code == 200
            
            if not success:
                self.log_test("San Francisco Restaurant Search Photos", False, f"API call failed: {response.status_code}")
                return False
            
            data = response.json()
            restaurants = data.get('restaurants', [])
            
            if not restaurants:
                self.log_test("San Francisco Restaurant Search Photos", False, "No restaurants returned")
                return False
            
            # Check photos for all restaurants
            restaurants_with_photos = 0
            total_photos = 0
            accessible_photos = 0
            broken_photos = []
            
            for restaurant in restaurants:
                photos = restaurant.get('photos', [])
                if photos:
                    restaurants_with_photos += 1
                    total_photos += len(photos)
                    
                    # Test accessibility of each photo URL
                    for photo in photos:
                        url = photo.get('url')
                        if url:
                            if self.test_photo_url_accessibility(url):
                                accessible_photos += 1
                            else:
                                broken_photos.append(f"{restaurant.get('name', 'Unknown')}: {url}")
            
            # All restaurants should have photos
            all_have_photos = restaurants_with_photos == len(restaurants)
            # All photos should be accessible
            all_photos_accessible = accessible_photos == total_photos and len(broken_photos) == 0
            
            success = all_have_photos and all_photos_accessible
            
            details = f"Restaurants: {len(restaurants)}, With photos: {restaurants_with_photos}, Total photos: {total_photos}, Accessible: {accessible_photos}"
            if broken_photos:
                details += f", Broken URLs: {len(broken_photos)}"
            
            self.log_test("San Francisco Restaurant Search Photos", success, details)
            
            if broken_photos:
                print("   Broken photo URLs:")
                for broken in broken_photos[:5]:  # Show first 5 broken URLs
                    print(f"     {broken}")
            
            return success
            
        except Exception as e:
            self.log_test("San Francisco Restaurant Search Photos", False, str(e))
            return False

    def test_restaurant_search_photos_new_york(self):
        """Test restaurant search returns working photos in New York"""
        try:
            params = {
                'latitude': 40.7128,
                'longitude': -74.0060,
                'radius': 8047,  # 5 miles
                'limit': 20
            }
            
            response = self.session.get(f"{self.api_url}/restaurants/search", params=params)
            success = response.status_code == 200
            
            if not success:
                self.log_test("New York Restaurant Search Photos", False, f"API call failed: {response.status_code}")
                return False
            
            data = response.json()
            restaurants = data.get('restaurants', [])
            
            if not restaurants:
                self.log_test("New York Restaurant Search Photos", False, "No restaurants returned")
                return False
            
            # Check photos for all restaurants
            restaurants_with_photos = 0
            total_photos = 0
            accessible_photos = 0
            broken_photos = []
            
            for restaurant in restaurants:
                photos = restaurant.get('photos', [])
                if photos:
                    restaurants_with_photos += 1
                    total_photos += len(photos)
                    
                    # Test accessibility of each photo URL
                    for photo in photos:
                        url = photo.get('url')
                        if url:
                            if self.test_photo_url_accessibility(url):
                                accessible_photos += 1
                            else:
                                broken_photos.append(f"{restaurant.get('name', 'Unknown')}: {url}")
            
            # All restaurants should have photos
            all_have_photos = restaurants_with_photos == len(restaurants)
            # All photos should be accessible
            all_photos_accessible = accessible_photos == total_photos and len(broken_photos) == 0
            
            success = all_have_photos and all_photos_accessible
            
            details = f"Restaurants: {len(restaurants)}, With photos: {restaurants_with_photos}, Total photos: {total_photos}, Accessible: {accessible_photos}"
            if broken_photos:
                details += f", Broken URLs: {len(broken_photos)}"
            
            self.log_test("New York Restaurant Search Photos", success, details)
            
            if broken_photos:
                print("   Broken photo URLs:")
                for broken in broken_photos[:5]:  # Show first 5 broken URLs
                    print(f"     {broken}")
            
            return success
            
        except Exception as e:
            self.log_test("New York Restaurant Search Photos", False, str(e))
            return False

    def test_photo_data_structure(self):
        """Test that photos array contains proper structure (url, width, height, is_fallback)"""
        try:
            params = {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'radius': 8047,
                'limit': 10
            }
            
            response = self.session.get(f"{self.api_url}/restaurants/search", params=params)
            success = response.status_code == 200
            
            if not success:
                self.log_test("Photo Data Structure", False, f"API call failed: {response.status_code}")
                return False
            
            data = response.json()
            restaurants = data.get('restaurants', [])
            
            if not restaurants:
                self.log_test("Photo Data Structure", False, "No restaurants returned")
                return False
            
            structure_valid = True
            invalid_photos = []
            total_photos_checked = 0
            
            required_fields = ['url', 'width', 'height', 'is_fallback']
            
            for restaurant in restaurants:
                photos = restaurant.get('photos', [])
                for photo in photos:
                    total_photos_checked += 1
                    
                    # Check if all required fields are present
                    missing_fields = [field for field in required_fields if field not in photo]
                    if missing_fields:
                        structure_valid = False
                        invalid_photos.append(f"{restaurant.get('name', 'Unknown')}: Missing {missing_fields}")
                    
                    # Check data types
                    if 'url' in photo and not isinstance(photo['url'], str):
                        structure_valid = False
                        invalid_photos.append(f"{restaurant.get('name', 'Unknown')}: URL not string")
                    
                    if 'width' in photo and not isinstance(photo['width'], int):
                        structure_valid = False
                        invalid_photos.append(f"{restaurant.get('name', 'Unknown')}: Width not integer")
                    
                    if 'height' in photo and not isinstance(photo['height'], int):
                        structure_valid = False
                        invalid_photos.append(f"{restaurant.get('name', 'Unknown')}: Height not integer")
                    
                    if 'is_fallback' in photo and not isinstance(photo['is_fallback'], bool):
                        structure_valid = False
                        invalid_photos.append(f"{restaurant.get('name', 'Unknown')}: is_fallback not boolean")
            
            details = f"Photos checked: {total_photos_checked}, Structure valid: {structure_valid}"
            if invalid_photos:
                details += f", Invalid: {len(invalid_photos)}"
            
            self.log_test("Photo Data Structure", structure_valid, details)
            
            if invalid_photos:
                print("   Invalid photo structures:")
                for invalid in invalid_photos[:5]:  # Show first 5 invalid structures
                    print(f"     {invalid}")
            
            return structure_valid
            
        except Exception as e:
            self.log_test("Photo Data Structure", False, str(e))
            return False

    def test_primary_photo_exists(self):
        """Test that primary photo (photos[0]) exists for all restaurants"""
        try:
            params = {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'radius': 8047,
                'limit': 20
            }
            
            response = self.session.get(f"{self.api_url}/restaurants/search", params=params)
            success = response.status_code == 200
            
            if not success:
                self.log_test("Primary Photo Exists", False, f"API call failed: {response.status_code}")
                return False
            
            data = response.json()
            restaurants = data.get('restaurants', [])
            
            if not restaurants:
                self.log_test("Primary Photo Exists", False, "No restaurants returned")
                return False
            
            restaurants_with_primary_photo = 0
            restaurants_without_primary_photo = []
            
            for restaurant in restaurants:
                photos = restaurant.get('photos', [])
                if photos and len(photos) > 0:
                    restaurants_with_primary_photo += 1
                else:
                    restaurants_without_primary_photo.append(restaurant.get('name', 'Unknown'))
            
            all_have_primary = restaurants_with_primary_photo == len(restaurants)
            
            details = f"Restaurants: {len(restaurants)}, With primary photo: {restaurants_with_primary_photo}"
            if restaurants_without_primary_photo:
                details += f", Without primary: {len(restaurants_without_primary_photo)}"
            
            self.log_test("Primary Photo Exists", all_have_primary, details)
            
            if restaurants_without_primary_photo:
                print("   Restaurants without primary photo:")
                for name in restaurants_without_primary_photo[:5]:  # Show first 5
                    print(f"     {name}")
            
            return all_have_primary
            
        except Exception as e:
            self.log_test("Primary Photo Exists", False, str(e))
            return False

    def test_unsplash_fallback_urls(self):
        """Test that Unsplash fallback URLs work correctly"""
        try:
            params = {
                'latitude': 37.7749,
                'longitude': -122.4194,
                'radius': 8047,
                'limit': 10
            }
            
            response = self.session.get(f"{self.api_url}/restaurants/search", params=params)
            success = response.status_code == 200
            
            if not success:
                self.log_test("Unsplash Fallback URLs", False, f"API call failed: {response.status_code}")
                return False
            
            data = response.json()
            restaurants = data.get('restaurants', [])
            
            if not restaurants:
                self.log_test("Unsplash Fallback URLs", False, "No restaurants returned")
                return False
            
            unsplash_photos = []
            accessible_unsplash = 0
            broken_unsplash = []
            
            for restaurant in restaurants:
                photos = restaurant.get('photos', [])
                for photo in photos:
                    url = photo.get('url', '')
                    is_fallback = photo.get('is_fallback', False)
                    
                    # Check if it's an Unsplash URL
                    if 'unsplash.com' in url and is_fallback:
                        unsplash_photos.append(url)
                        
                        # Test accessibility
                        if self.test_photo_url_accessibility(url):
                            accessible_unsplash += 1
                        else:
                            broken_unsplash.append(f"{restaurant.get('name', 'Unknown')}: {url}")
            
            all_unsplash_accessible = len(broken_unsplash) == 0 and len(unsplash_photos) > 0
            
            details = f"Unsplash photos found: {len(unsplash_photos)}, Accessible: {accessible_unsplash}"
            if broken_unsplash:
                details += f", Broken: {len(broken_unsplash)}"
            
            self.log_test("Unsplash Fallback URLs", all_unsplash_accessible, details)
            
            if broken_unsplash:
                print("   Broken Unsplash URLs:")
                for broken in broken_unsplash[:3]:  # Show first 3 broken URLs
                    print(f"     {broken}")
            
            return all_unsplash_accessible
            
        except Exception as e:
            self.log_test("Unsplash Fallback URLs", False, str(e))
            return False

    def test_no_404_photo_urls(self):
        """Test that no 404 photo URLs are returned"""
        try:
            # Test multiple locations to get diverse photo sources
            locations = [
                {'latitude': 37.7749, 'longitude': -122.4194, 'name': 'San Francisco'},
                {'latitude': 40.7128, 'longitude': -74.0060, 'name': 'New York'},
            ]
            
            all_photos_valid = True
            total_photos_tested = 0
            broken_urls = []
            
            for location in locations:
                params = {
                    'latitude': location['latitude'],
                    'longitude': location['longitude'],
                    'radius': 8047,
                    'limit': 10
                }
                
                response = self.session.get(f"{self.api_url}/restaurants/search", params=params)
                
                if response.status_code != 200:
                    continue
                
                data = response.json()
                restaurants = data.get('restaurants', [])
                
                for restaurant in restaurants:
                    photos = restaurant.get('photos', [])
                    for photo in photos:
                        url = photo.get('url')
                        if url:
                            total_photos_tested += 1
                            
                            # Test if URL returns 404
                            try:
                                response = requests.head(url, timeout=10, allow_redirects=True)
                                if response.status_code == 404:
                                    all_photos_valid = False
                                    broken_urls.append(f"{restaurant.get('name', 'Unknown')} ({location['name']}): {url}")
                            except Exception as e:
                                # Network errors are different from 404s, but still problematic
                                all_photos_valid = False
                                broken_urls.append(f"{restaurant.get('name', 'Unknown')} ({location['name']}): {url} - {str(e)}")
            
            details = f"Photos tested: {total_photos_tested}, 404 errors: {len(broken_urls)}"
            
            self.log_test("No 404 Photo URLs", all_photos_valid, details)
            
            if broken_urls:
                print("   URLs returning 404 or errors:")
                for broken in broken_urls[:5]:  # Show first 5 broken URLs
                    print(f"     {broken}")
            
            return all_photos_valid
            
        except Exception as e:
            self.log_test("No 404 Photo URLs", False, str(e))
            return False

    def run_all_photo_tests(self):
        """Run all photo URL tests"""
        print("🔍 URGENT IMAGE DISPLAY FIX TESTING")
        print("=" * 60)
        print("Testing that restaurant search API returns working photo URLs")
        print("after fixing Google Places photo URL issues")
        print("=" * 60)
        
        # Run all photo-related tests
        tests = [
            self.test_restaurant_search_photos_san_francisco,
            self.test_restaurant_search_photos_new_york,
            self.test_photo_data_structure,
            self.test_primary_photo_exists,
            self.test_unsplash_fallback_urls,
            self.test_no_404_photo_urls
        ]
        
        for test in tests:
            test()
            print()  # Add spacing between tests
        
        # Summary
        print("=" * 60)
        print(f"PHOTO URL TESTING SUMMARY")
        print(f"Tests Run: {self.tests_run}")
        print(f"Tests Passed: {self.tests_passed}")
        print(f"Success Rate: {(self.tests_passed/self.tests_run*100):.1f}%")
        
        if self.tests_passed == self.tests_run:
            print("🎉 ALL PHOTO URL TESTS PASSED - Images should display correctly!")
        else:
            print("❌ SOME PHOTO URL TESTS FAILED - Image display issues may persist")
        
        print("=" * 60)
        
        return self.tests_passed == self.tests_run

if __name__ == "__main__":
    tester = PhotoURLTester()
    success = tester.run_all_photo_tests()
    sys.exit(0 if success else 1)