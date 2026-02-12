#!/usr/bin/env python3
"""
Mobile App Digital Coupon System Backend Integration Testing

Tests the complete coupon workflow for mobile app including:
1. Get Nearby Coupons (GET /api/coupons/near)
2. Get Coupon Details (GET /api/coupons/{coupon_id})
3. Save Coupon (POST /api/users/coupons/{coupon_id}/save)
4. Get Saved Coupons (GET /api/users/coupons/saved)
5. Remove Saved Coupon (DELETE /api/users/coupons/{coupon_id}/save)
6. Track Coupon View (POST /api/coupons/{coupon_id}/view)

Focus: Verify API response structure matches mobile app expectations with restaurant information
"""

import asyncio
import httpx
import json
import uuid
from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Optional, List

# Backend URL from frontend environment
BACKEND_URL = "https://owner-mgmt.preview.emergentagent.com/api"

class MobileCouponTester:
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
                self.test_data["user_credentials"] = {
                    "email": user_data["email"],
                    "password": user_data["password"]
                }
                
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

    async def setup_test_owner_and_coupon(self):
        """Create test owner and coupon for testing"""
        test_name = "Test Owner and Coupon Setup"
        
        try:
            # Create test owner using correct auth endpoint
            unique_id = str(uuid.uuid4())[:8]
            owner_data = {
                "first_name": "Test",
                "last_name": "Owner",
                "email": f"coupon_owner_{unique_id}@example.com",
                "password": "ownerpassword123",
                "phone": "+1-555-0199",
                "business_name": f"Test Coupon Restaurant {unique_id}",
                "business_type": "restaurant"
            }
            
            # Register owner using auth endpoint
            owner_response = await self.client.post(f"{BACKEND_URL}/auth/register", json=owner_data)
            
            if owner_response.status_code != 200:
                await self.log_result(test_name, False, 
                    f"Could not create test owner: {owner_response.status_code} - {owner_response.text}")
                return False
            
            owner_auth = owner_response.json()
            owner_token = owner_auth.get("access_token")
            
            if not owner_token:
                await self.log_result(test_name, False, 
                    f"No owner token received. Response: {owner_auth}")
                return False
            
            # Get a restaurant to associate with coupon
            restaurants_response = await self.client.get(
                f"{BACKEND_URL}/restaurants/search?latitude=37.7749&longitude=-122.4194&limit=1"
            )
            
            if restaurants_response.status_code != 200:
                await self.log_result(test_name, False, "Could not get restaurants for coupon test")
                return False
            
            restaurants_data = restaurants_response.json()
            restaurants = restaurants_data.get("restaurants", [])
            
            if not restaurants:
                await self.log_result(test_name, False, "No restaurants available for coupon test")
                return False
            
            restaurant_id = restaurants[0]["id"]
            
            # Create test coupon
            coupon_data = {
                "title": "Mobile App Test Coupon",
                "description": "20% off your entire order - Mobile app testing coupon",
                "coupon_type": "percentage",
                "discount_percentage": 20,
                "valid_from": datetime.now(timezone.utc).isoformat(),
                "valid_until": (datetime.now(timezone.utc) + timedelta(days=30)).isoformat(),
                "max_redemptions": 100,
                "max_per_customer": 1,
                "minimum_purchase": 10.0,
                "target_audience": "all_customers",
                "days_of_week": ["monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday"],
                "terms_conditions": "Valid for dine-in and takeout. Cannot be combined with other offers.",
                "promotional_message": "Save 20% on your next visit!"
            }
            
            headers = {"Authorization": f"Bearer {owner_token}"}
            coupon_response = await self.client.post(
                f"{BACKEND_URL}/owners/coupons?restaurant_id={restaurant_id}", 
                json=coupon_data, 
                headers=headers
            )
            
            if coupon_response.status_code == 200:
                coupon = coupon_response.json()
                self.test_data["test_coupon"] = coupon
                self.test_data["test_restaurant_id"] = restaurant_id
                self.test_data["owner_token"] = owner_token
                
                await self.log_result(test_name, True, 
                    f"Test coupon created successfully. ID: {coupon['id']}")
                return True
            else:
                await self.log_result(test_name, False, 
                    f"Coupon creation failed with status {coupon_response.status_code}", coupon_response.text)
                return False
                
        except Exception as e:
            await self.log_result(test_name, False, f"Exception: {str(e)}")
            return False

    async def test_get_nearby_coupons(self):
        """Test GET /api/coupons/near with San Francisco coordinates"""
        test_name = "Get Nearby Coupons API"
        
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
                
                # Check if we have coupons and verify structure
                if len(coupons) > 0:
                    coupon = coupons[0]
                    
                    # Verify coupon has restaurant info
                    if "restaurant" not in coupon:
                        await self.log_result(test_name, False, "Coupon missing restaurant information")
                        return
                    
                    restaurant = coupon["restaurant"]
                    required_restaurant_fields = ["name", "address"]
                    missing_restaurant_fields = [field for field in required_restaurant_fields if field not in restaurant]
                    
                    if missing_restaurant_fields:
                        await self.log_result(test_name, False, 
                            f"Restaurant missing fields: {missing_restaurant_fields}")
                        return
                    
                    # Store first coupon for subsequent tests
                    self.test_data["nearby_coupon"] = coupon
                    
                    await self.log_result(test_name, True, 
                        f"Found {len(coupons)} nearby coupons with proper restaurant info")
                else:
                    await self.log_result(test_name, True, 
                        "No coupons found in area (expected if no test coupons created)")
                    
            else:
                await self.log_result(test_name, False, 
                    f"Request failed with status {response.status_code}", response.text)
                
        except Exception as e:
            await self.log_result(test_name, False, f"Exception: {str(e)}")

    async def test_get_coupon_details(self):
        """Test GET /api/coupons/{coupon_id}"""
        test_name = "Get Coupon Details API"
        
        # Use test coupon if available, otherwise try nearby coupon
        coupon_id = None
        if "test_coupon" in self.test_data:
            coupon_id = self.test_data["test_coupon"]["id"]
        elif "nearby_coupon" in self.test_data:
            coupon_id = self.test_data["nearby_coupon"]["id"]
        
        if not coupon_id:
            await self.log_result(test_name, False, "No coupon ID available for testing")
            return
        
        try:
            response = await self.client.get(f"{BACKEND_URL}/coupons/{coupon_id}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response has all required fields
                required_fields = ["id", "title", "description", "coupon_type", "qr_code", "redemption_code"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    await self.log_result(test_name, False, f"Missing fields: {missing_fields}", data)
                    return
                
                # Verify QR code is base64 encoded
                qr_code = data.get("qr_code", "")
                if not qr_code.startswith("data:image/png;base64,"):
                    await self.log_result(test_name, False, "QR code not in expected base64 format")
                    return
                
                # Store coupon details for subsequent tests
                self.test_data["coupon_details"] = data
                
                await self.log_result(test_name, True, 
                    f"Coupon details retrieved successfully. Title: {data['title']}, Type: {data['coupon_type']}")
                    
            else:
                await self.log_result(test_name, False, 
                    f"Request failed with status {response.status_code}", response.text)
                
        except Exception as e:
            await self.log_result(test_name, False, f"Exception: {str(e)}")

    async def test_save_coupon(self):
        """Test POST /api/users/coupons/{coupon_id}/save"""
        test_name = "Save Coupon API"
        
        if "user_token" not in self.test_data:
            await self.log_result(test_name, False, "No user token available")
            return
        
        # Use test coupon if available, otherwise try coupon details
        coupon_id = None
        if "test_coupon" in self.test_data:
            coupon_id = self.test_data["test_coupon"]["id"]
        elif "coupon_details" in self.test_data:
            coupon_id = self.test_data["coupon_details"]["id"]
        
        if not coupon_id:
            await self.log_result(test_name, False, "No coupon ID available for testing")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.test_data['user_token']}"}
            response = await self.client.post(f"{BACKEND_URL}/users/coupons/{coupon_id}/save", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                if "message" not in data:
                    await self.log_result(test_name, False, "Missing message field in response", data)
                    return
                
                self.test_data["saved_coupon_id"] = coupon_id
                
                await self.log_result(test_name, True, 
                    f"Coupon saved successfully: {data['message']}")
                    
            else:
                await self.log_result(test_name, False, 
                    f"Request failed with status {response.status_code}", response.text)
                
        except Exception as e:
            await self.log_result(test_name, False, f"Exception: {str(e)}")

    async def test_get_saved_coupons(self):
        """Test GET /api/users/coupons/saved"""
        test_name = "Get Saved Coupons API"
        
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
                
                # Verify saved coupon is in the list
                if "saved_coupon_id" in self.test_data:
                    saved_coupon_id = self.test_data["saved_coupon_id"]
                    found_saved_coupon = any(c.get("id") == saved_coupon_id for c in coupons)
                    
                    if not found_saved_coupon:
                        await self.log_result(test_name, False, 
                            f"Previously saved coupon {saved_coupon_id} not found in saved list")
                        return
                
                # Verify coupons have enriched restaurant data
                if len(coupons) > 0:
                    coupon = coupons[0]
                    if "restaurant" not in coupon:
                        await self.log_result(test_name, False, "Saved coupon missing restaurant information")
                        return
                    
                    restaurant = coupon["restaurant"]
                    required_restaurant_fields = ["name", "address"]
                    missing_restaurant_fields = [field for field in required_restaurant_fields if field not in restaurant]
                    
                    if missing_restaurant_fields:
                        await self.log_result(test_name, False, 
                            f"Restaurant missing fields: {missing_restaurant_fields}")
                        return
                
                await self.log_result(test_name, True, 
                    f"Retrieved {len(coupons)} saved coupons with enriched restaurant data")
                    
            else:
                await self.log_result(test_name, False, 
                    f"Request failed with status {response.status_code}", response.text)
                
        except Exception as e:
            await self.log_result(test_name, False, f"Exception: {str(e)}")

    async def test_remove_saved_coupon(self):
        """Test DELETE /api/users/coupons/{coupon_id}/save"""
        test_name = "Remove Saved Coupon API"
        
        if "user_token" not in self.test_data:
            await self.log_result(test_name, False, "No user token available")
            return
        
        if "saved_coupon_id" not in self.test_data:
            await self.log_result(test_name, False, "No saved coupon ID available")
            return
        
        try:
            coupon_id = self.test_data["saved_coupon_id"]
            headers = {"Authorization": f"Bearer {self.test_data['user_token']}"}
            response = await self.client.delete(f"{BACKEND_URL}/users/coupons/{coupon_id}/save", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                if "message" not in data:
                    await self.log_result(test_name, False, "Missing message field in response", data)
                    return
                
                await self.log_result(test_name, True, 
                    f"Coupon removed successfully: {data['message']}")
                    
            else:
                await self.log_result(test_name, False, 
                    f"Request failed with status {response.status_code}", response.text)
                
        except Exception as e:
            await self.log_result(test_name, False, f"Exception: {str(e)}")

    async def test_verify_coupon_removed(self):
        """Verify coupon was removed from saved list"""
        test_name = "Verify Coupon Removed from Saved List"
        
        if "user_token" not in self.test_data:
            await self.log_result(test_name, False, "No user token available")
            return
        
        if "saved_coupon_id" not in self.test_data:
            await self.log_result(test_name, False, "No saved coupon ID available")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.test_data['user_token']}"}
            response = await self.client.get(f"{BACKEND_URL}/users/coupons/saved", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                coupons = data.get("coupons", [])
                
                # Verify removed coupon is not in the list
                saved_coupon_id = self.test_data["saved_coupon_id"]
                found_removed_coupon = any(c.get("id") == saved_coupon_id for c in coupons)
                
                if found_removed_coupon:
                    await self.log_result(test_name, False, 
                        f"Removed coupon {saved_coupon_id} still found in saved list")
                    return
                
                await self.log_result(test_name, True, 
                    "Coupon successfully removed from saved list")
                    
            else:
                await self.log_result(test_name, False, 
                    f"Request failed with status {response.status_code}", response.text)
                
        except Exception as e:
            await self.log_result(test_name, False, f"Exception: {str(e)}")

    async def test_track_coupon_view(self):
        """Test POST /api/coupons/{coupon_id}/view"""
        test_name = "Track Coupon View API"
        
        # Use test coupon if available, otherwise try coupon details
        coupon_id = None
        if "test_coupon" in self.test_data:
            coupon_id = self.test_data["test_coupon"]["id"]
        elif "coupon_details" in self.test_data:
            coupon_id = self.test_data["coupon_details"]["id"]
        
        if not coupon_id:
            await self.log_result(test_name, False, "No coupon ID available for testing")
            return
        
        try:
            response = await self.client.post(f"{BACKEND_URL}/coupons/{coupon_id}/view")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                if "message" not in data:
                    await self.log_result(test_name, False, "Missing message field in response", data)
                    return
                
                await self.log_result(test_name, True, 
                    f"Coupon view tracked successfully: {data['message']}")
                    
            else:
                await self.log_result(test_name, False, 
                    f"Request failed with status {response.status_code}", response.text)
                
        except Exception as e:
            await self.log_result(test_name, False, f"Exception: {str(e)}")

    async def test_invalid_coupon_id_handling(self):
        """Test error handling for invalid coupon IDs"""
        test_name = "Invalid Coupon ID Error Handling"
        
        try:
            invalid_coupon_id = "invalid-coupon-id-12345"
            
            # Test get coupon details with invalid ID
            response = await self.client.get(f"{BACKEND_URL}/coupons/{invalid_coupon_id}")
            
            if response.status_code == 404:
                await self.log_result(test_name, True, 
                    "Correctly returned 404 for invalid coupon ID")
            else:
                await self.log_result(test_name, False, 
                    f"Expected 404 for invalid coupon ID, got {response.status_code}")
                
        except Exception as e:
            await self.log_result(test_name, False, f"Exception: {str(e)}")

    async def run_all_tests(self):
        """Run all mobile coupon backend tests"""
        print("🚀 Starting Mobile App Digital Coupon System Backend Integration Tests")
        print("=" * 80)
        
        # Setup phase
        user_setup_success = await self.setup_test_user()
        if not user_setup_success:
            print("❌ Cannot proceed without test user")
            return 0, len(self.results)
        
        # Try to create test coupon (may fail due to known issues)
        await self.setup_test_owner_and_coupon()
        
        # Core coupon API tests
        await self.test_get_nearby_coupons()
        await self.test_get_coupon_details()
        await self.test_save_coupon()
        await self.test_get_saved_coupons()
        await self.test_remove_saved_coupon()
        await self.test_verify_coupon_removed()
        await self.test_track_coupon_view()
        
        # Error handling tests
        await self.test_invalid_coupon_id_handling()
        
        # Summary
        print("=" * 80)
        print("📊 MOBILE COUPON BACKEND TEST SUMMARY")
        print("=" * 80)
        
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
        
        await self.client.aclose()
        
        return passed_tests, failed_tests

async def main():
    """Main test execution"""
    tester = MobileCouponTester()
    passed, failed = await tester.run_all_tests()
    
    if failed == 0:
        print("\n🎉 All tests passed! Mobile App Digital Coupon System backend is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the issues above.")
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(main())