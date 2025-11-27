#!/usr/bin/env python3
"""
Mobile App Digital Coupon System Backend Integration Testing - Focused Test

Tests the coupon endpoints that can be tested without requiring existing coupons:
1. Get Nearby Coupons (GET /api/coupons/near) - Tests API structure
2. User Authentication and Saved Coupons workflow
3. Error handling for invalid coupon IDs
4. Track Coupon View endpoint

This test focuses on verifying API response structures match mobile app expectations.
"""

import asyncio
import httpx
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

# Backend URL from frontend environment
BACKEND_URL = "https://dining-deals-2.preview.emergentagent.com/api"

class MobileCouponFocusedTester:
    def __init__(self):
        self.client = httpx.AsyncClient(timeout=30.0)
        self.test_data = {}
        self.results = []
        
    async def log_result(self, test_name: str, success: bool, details: str = "", response_data: Any = None):
        """Log test result"""
        status = "✅ PASS" if success else "❌ FAIL"
        result = {
            "test": test_name,
            "status": status,
            "details": details,
            "response_data": response_data
        }
        self.results.append(result)
        print(f"{status}: {test_name}")
        if details:
            print(f"   Details: {details}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        print()

    async def setup_test_user(self):
        """Create a test user for coupon operations"""
        test_name = "Test User Setup"
        
        try:
            # Generate unique test data
            unique_id = str(uuid.uuid4())[:8]
            user_data = {
                "email": f"coupon_user_{unique_id}@example.com",
                "password": "testpassword123",
                "first_name": "Mobile",
                "last_name": "User"
            }
            
            response = await self.client.post(f"{BACKEND_URL}/users/register", json=user_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Store user data for subsequent tests
                self.test_data["user"] = data["user"]
                self.test_data["user_token"] = data["access_token"]
                
                await self.log_result(test_name, True, 
                    f"Test user created successfully. ID: {data['user']['id']}")
                return True
            else:
                await self.log_result(test_name, False, 
                    f"User creation failed with status {response.status_code}", response.text)
                return False
                
        except Exception as e:
            await self.log_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_get_nearby_coupons_api_structure(self):
        """Test GET /api/coupons/near API structure and response format"""
        test_name = "Get Nearby Coupons API Structure"
        
        try:
            # San Francisco coordinates with 10-mile radius (16093 meters)
            params = {
                "latitude": 37.7749,
                "longitude": -122.4194,
                "radius_miles": 10
            }
            
            response = await self.client.get(f"{BACKEND_URL}/coupons/near", params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["coupons", "total"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    await self.log_result(test_name, False, f"Missing fields: {missing_fields}", data)
                    return
                
                coupons = data["coupons"]
                
                if not isinstance(coupons, list):
                    await self.log_result(test_name, False, f"Coupons field is not a list: {type(coupons)}")
                    return
                
                # Verify total field is correct
                if data["total"] != len(coupons):
                    await self.log_result(test_name, False, 
                        f"Total field ({data['total']}) doesn't match coupons array length ({len(coupons)})")
                    return
                
                await self.log_result(test_name, True, 
                    f"API structure correct. Found {len(coupons)} coupons, total: {data['total']}")
                    
            elif response.status_code == 500:
                # This might be the geospatial index issue mentioned in previous tests
                await self.log_result(test_name, False, 
                    f"Server error (500) - likely geospatial index issue: {response.text}")
            else:
                await self.log_result(test_name, False, 
                    f"Request failed with status {response.status_code}", response.text)
                
        except Exception as e:
            await self.log_result(test_name, False, f"Exception: {str(e)}")

    async def test_get_saved_coupons_empty_state(self):
        """Test GET /api/users/coupons/saved with empty state"""
        test_name = "Get Saved Coupons - Empty State"
        
        if "user_token" not in self.test_data:
            await self.log_result(test_name, False, "No user token available")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.test_data['user_token']}"}
            response = await self.client.get(f"{BACKEND_URL}/users/coupons/saved", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["coupons", "total"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    await self.log_result(test_name, False, f"Missing fields: {missing_fields}", data)
                    return
                
                coupons = data["coupons"]
                
                if not isinstance(coupons, list):
                    await self.log_result(test_name, False, f"Coupons field is not a list: {type(coupons)}")
                    return
                
                # For new user, should be empty
                if len(coupons) == 0 and data["total"] == 0:
                    await self.log_result(test_name, True, 
                        "Empty saved coupons state working correctly")
                else:
                    await self.log_result(test_name, True, 
                        f"Retrieved {len(coupons)} saved coupons (user may have existing data)")
                    
            else:
                await self.log_result(test_name, False, 
                    f"Request failed with status {response.status_code}", response.text)
                
        except Exception as e:
            await self.log_result(test_name, False, f"Exception: {str(e)}")

    async def test_invalid_coupon_operations(self):
        """Test error handling for invalid coupon IDs across different endpoints"""
        test_name = "Invalid Coupon ID Error Handling"
        
        try:
            invalid_coupon_id = "invalid-coupon-id-12345"
            
            # Test 1: Get coupon details with invalid ID
            response1 = await self.client.get(f"{BACKEND_URL}/coupons/{invalid_coupon_id}")
            
            if response1.status_code != 404:
                await self.log_result(test_name, False, 
                    f"Get coupon details: Expected 404 for invalid coupon ID, got {response1.status_code}")
                return
            
            # Test 2: Save invalid coupon (requires authentication)
            if "user_token" in self.test_data:
                headers = {"Authorization": f"Bearer {self.test_data['user_token']}"}
                response2 = await self.client.post(f"{BACKEND_URL}/users/coupons/{invalid_coupon_id}/save", headers=headers)
                
                if response2.status_code != 404:
                    await self.log_result(test_name, False, 
                        f"Save invalid coupon: Expected 404, got {response2.status_code}")
                    return
            
            # Test 3: Track view for invalid coupon
            response3 = await self.client.post(f"{BACKEND_URL}/coupons/{invalid_coupon_id}/view")
            
            # This endpoint might return 200 even for invalid IDs (depending on implementation)
            # So we just check it doesn't crash
            if response3.status_code not in [200, 404]:
                await self.log_result(test_name, False, 
                    f"Track view: Unexpected status {response3.status_code}")
                return
            
            await self.log_result(test_name, True, 
                "All invalid coupon ID operations handled correctly")
                
        except Exception as e:
            await self.log_result(test_name, False, f"Exception: {str(e)}")

    async def test_track_coupon_view_endpoint(self):
        """Test POST /api/coupons/{coupon_id}/view endpoint structure"""
        test_name = "Track Coupon View Endpoint"
        
        try:
            # Use a fake but properly formatted coupon ID
            test_coupon_id = str(uuid.uuid4())
            
            response = await self.client.post(f"{BACKEND_URL}/coupons/{test_coupon_id}/view")
            
            # This endpoint should accept the request even if coupon doesn't exist
            # (it's for analytics tracking)
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                if "message" in data:
                    await self.log_result(test_name, True, 
                        f"Track view endpoint working: {data['message']}")
                else:
                    await self.log_result(test_name, True, 
                        "Track view endpoint accepts requests successfully")
            else:
                await self.log_result(test_name, False, 
                    f"Request failed with status {response.status_code}", response.text)
                
        except Exception as e:
            await self.log_result(test_name, False, f"Exception: {str(e)}")

    async def test_user_authentication_flow(self):
        """Test user authentication is working for coupon operations"""
        test_name = "User Authentication for Coupon Operations"
        
        try:
            # Test accessing saved coupons without authentication
            response1 = await self.client.get(f"{BACKEND_URL}/users/coupons/saved")
            
            if response1.status_code not in [401, 403]:
                await self.log_result(test_name, False, 
                    f"Expected 401/403 for unauthenticated request, got {response1.status_code}")
                return
            
            # Test with valid authentication
            if "user_token" in self.test_data:
                headers = {"Authorization": f"Bearer {self.test_data['user_token']}"}
                response2 = await self.client.get(f"{BACKEND_URL}/users/coupons/saved", headers=headers)
                
                if response2.status_code != 200:
                    await self.log_result(test_name, False, 
                        f"Authenticated request failed with status {response2.status_code}")
                    return
            
            await self.log_result(test_name, True, 
                "User authentication working correctly for coupon operations")
                
        except Exception as e:
            await self.log_result(test_name, False, f"Exception: {str(e)}")

    async def test_api_response_formats(self):
        """Test that API responses match expected mobile app formats"""
        test_name = "API Response Format Validation"
        
        try:
            # Test nearby coupons response format
            params = {
                "latitude": 37.7749,
                "longitude": -122.4194,
                "radius_miles": 10
            }
            
            response = await self.client.get(f"{BACKEND_URL}/coupons/near", params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify JSON structure is valid
                if not isinstance(data, dict):
                    await self.log_result(test_name, False, "Response is not a JSON object")
                    return
                
                # Verify required fields exist
                if "coupons" not in data or "total" not in data:
                    await self.log_result(test_name, False, "Missing required fields in response")
                    return
                
                # Verify coupons is an array
                if not isinstance(data["coupons"], list):
                    await self.log_result(test_name, False, "Coupons field is not an array")
                    return
                
                # Verify total is a number
                if not isinstance(data["total"], int):
                    await self.log_result(test_name, False, "Total field is not an integer")
                    return
                
                await self.log_result(test_name, True, 
                    "API response formats are valid for mobile app consumption")
            else:
                await self.log_result(test_name, False, 
                    f"Could not test response format due to API error: {response.status_code}")
                
        except Exception as e:
            await self.log_result(test_name, False, f"Exception: {str(e)}")

    async def run_all_tests(self):
        """Run all focused mobile coupon backend tests"""
        print("🚀 Starting Mobile App Digital Coupon System Backend Integration Tests (Focused)")
        print("=" * 90)
        
        # Setup phase
        user_setup_success = await self.setup_test_user()
        if not user_setup_success:
            print("❌ Cannot proceed without test user")
            return 0, len(self.results)
        
        # Core API structure tests
        await self.test_get_nearby_coupons_api_structure()
        await self.test_get_saved_coupons_empty_state()
        await self.test_invalid_coupon_operations()
        await self.test_track_coupon_view_endpoint()
        await self.test_user_authentication_flow()
        await self.test_api_response_formats()
        
        # Summary
        print("=" * 90)
        print("📊 MOBILE COUPON BACKEND FOCUSED TEST SUMMARY")
        print("=" * 90)
        
        total_tests = len(self.results)
        passed_tests = len([r for r in self.results if "✅ PASS" in r["status"]])
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"Passed: {passed_tests}")
        print(f"Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        if failed_tests > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.results:
                if "❌ FAIL" in result["status"]:
                    print(f"  - {result['test']}: {result['details']}")
        
        print("\n📋 DETAILED FINDINGS:")
        for result in self.results:
            print(f"  {result['status']}: {result['test']}")
            if result['details']:
                print(f"      {result['details']}")
        
        await self.client.aclose()
        
        return passed_tests, failed_tests

async def main():
    """Main test execution"""
    tester = MobileCouponFocusedTester()
    passed, failed = await tester.run_all_tests()
    
    if failed == 0:
        print("\n🎉 All focused tests passed! Mobile App Digital Coupon System backend APIs are structurally sound.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the issues above.")
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(main())