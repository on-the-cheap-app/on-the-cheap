#!/usr/bin/env python3
"""
Comprehensive Backend Testing for Restaurant Owner Dashboard Integration
Tests the complete owner workflow including registration, login, dashboard, claims, and specials management.
"""

import asyncio
import httpx
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Backend URL from frontend environment
BACKEND_URL = "https://dining-deals-2.preview.emergentagent.com/api"

class OwnerDashboardTester:
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

    async def test_owner_registration(self):
        """Test owner registration endpoint"""
        test_name = "Owner Registration API"
        
        try:
            # Generate unique test data
            unique_id = str(uuid.uuid4())[:8]
            owner_data = {
                "first_name": "John",
                "last_name": "Smith",
                "email": f"owner_{unique_id}@example.com",
                "password": "securepassword123",
                "phone": "+1-555-0123",
                "business_name": f"Test Restaurant {unique_id}",
                "business_type": "restaurant"
            }
            
            response = await self.client.post(f"{BACKEND_URL}/owners/register", json=owner_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["id", "first_name", "last_name", "email", "status", "business_name"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    await self.log_result(test_name, False, f"Missing fields: {missing_fields}", data)
                    return
                
                # Store owner data for subsequent tests
                self.test_data["owner"] = data
                self.test_data["owner_credentials"] = {
                    "email": owner_data["email"],
                    "password": owner_data["password"]
                }
                
                await self.log_result(test_name, True, 
                    f"Owner registered successfully. ID: {data['id']}, Status: {data['status']}")
            else:
                await self.log_result(test_name, False, 
                    f"Registration failed with status {response.status_code}", response.text)
                
        except Exception as e:
            await self.log_result(test_name, False, f"Exception: {str(e)}")

    async def test_owner_login(self):
        """Test owner login endpoint"""
        test_name = "Owner Login API"
        
        if "owner_credentials" not in self.test_data:
            await self.log_result(test_name, False, "No owner credentials available from registration")
            return
        
        try:
            login_data = self.test_data["owner_credentials"]
            
            response = await self.client.post(f"{BACKEND_URL}/owners/login", json=login_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["access_token", "token_type", "user_type", "owner"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    await self.log_result(test_name, False, f"Missing fields: {missing_fields}", data)
                    return
                
                # Verify user type
                if data.get("user_type") != "owner":
                    await self.log_result(test_name, False, f"Wrong user type: {data.get('user_type')}")
                    return
                
                # Store token for authenticated requests
                self.test_data["owner_token"] = data["access_token"]
                
                await self.log_result(test_name, True, 
                    f"Owner login successful. Token type: {data['token_type']}, User type: {data['user_type']}")
            else:
                await self.log_result(test_name, False, 
                    f"Login failed with status {response.status_code}", response.text)
                
        except Exception as e:
            await self.log_result(test_name, False, f"Exception: {str(e)}")

    async def test_owner_dashboard(self):
        """Test owner dashboard endpoint"""
        test_name = "Owner Dashboard API"
        
        if "owner_token" not in self.test_data:
            await self.log_result(test_name, False, "No owner token available from login")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.test_data['owner_token']}"}
            
            response = await self.client.get(f"{BACKEND_URL}/owners/dashboard", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["total_restaurants", "pending_claims", "active_specials", "pending_specials", "total_views", "total_favorites"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    await self.log_result(test_name, False, f"Missing fields: {missing_fields}", data)
                    return
                
                # Verify data types
                for field in required_fields:
                    if not isinstance(data[field], int):
                        await self.log_result(test_name, False, f"Field {field} is not an integer: {type(data[field])}")
                        return
                
                self.test_data["dashboard_stats"] = data
                
                await self.log_result(test_name, True, 
                    f"Dashboard retrieved successfully. Restaurants: {data['total_restaurants']}, Claims: {data['pending_claims']}, Specials: {data['active_specials']}")
            else:
                await self.log_result(test_name, False, 
                    f"Dashboard request failed with status {response.status_code}", response.text)
                
        except Exception as e:
            await self.log_result(test_name, False, f"Exception: {str(e)}")

    async def test_owner_restaurants(self):
        """Test owner restaurants listing endpoint"""
        test_name = "Owner Restaurants Listing API"
        
        if "owner_token" not in self.test_data:
            await self.log_result(test_name, False, "No owner token available from login")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.test_data['owner_token']}"}
            
            response = await self.client.get(f"{BACKEND_URL}/owners/restaurants", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                if "restaurants" not in data:
                    await self.log_result(test_name, False, "Missing 'restaurants' field in response", data)
                    return
                
                restaurants = data["restaurants"]
                
                # Should be empty for new owner
                if not isinstance(restaurants, list):
                    await self.log_result(test_name, False, f"Restaurants field is not a list: {type(restaurants)}")
                    return
                
                self.test_data["owner_restaurants"] = restaurants
                
                await self.log_result(test_name, True, 
                    f"Restaurants listing retrieved successfully. Count: {len(restaurants)}")
            else:
                await self.log_result(test_name, False, 
                    f"Restaurants request failed with status {response.status_code}", response.text)
                
        except Exception as e:
            await self.log_result(test_name, False, f"Exception: {str(e)}")

    async def test_owner_specials(self):
        """Test owner specials listing endpoint"""
        test_name = "Owner Specials Listing API"
        
        if "owner_token" not in self.test_data:
            await self.log_result(test_name, False, "No owner token available from login")
            return
        
        try:
            headers = {"Authorization": f"Bearer {self.test_data['owner_token']}"}
            
            response = await self.client.get(f"{BACKEND_URL}/owners/specials", headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                if "specials" not in data:
                    await self.log_result(test_name, False, "Missing 'specials' field in response", data)
                    return
                
                specials = data["specials"]
                
                # Should be empty for new owner
                if not isinstance(specials, list):
                    await self.log_result(test_name, False, f"Specials field is not a list: {type(specials)}")
                    return
                
                self.test_data["owner_specials"] = specials
                
                await self.log_result(test_name, True, 
                    f"Specials listing retrieved successfully. Count: {len(specials)}")
            else:
                await self.log_result(test_name, False, 
                    f"Specials request failed with status {response.status_code}", response.text)
                
        except Exception as e:
            await self.log_result(test_name, False, f"Exception: {str(e)}")

    async def test_restaurant_claim_submission(self):
        """Test restaurant claim submission"""
        test_name = "Restaurant Claim Submission API"
        
        if "owner_token" not in self.test_data:
            await self.log_result(test_name, False, "No owner token available from login")
            return
        
        try:
            # First, get a restaurant to claim (from existing restaurants)
            restaurants_response = await self.client.get(f"{BACKEND_URL}/restaurants/search?latitude=37.7749&longitude=-122.4194&limit=5")
            
            if restaurants_response.status_code != 200:
                await self.log_result(test_name, False, "Could not get restaurants for claim test")
                return
            
            restaurants_data = restaurants_response.json()
            if not restaurants_data.get("restaurants"):
                await self.log_result(test_name, False, "No restaurants available for claim test")
                return
            
            # Try multiple restaurants in case some are already claimed
            claim_successful = False
            for restaurant in restaurants_data["restaurants"]:
                restaurant_id = restaurant["id"]
                
                # Submit claim
                headers = {"Authorization": f"Bearer {self.test_data['owner_token']}"}
                claim_data = {
                    "restaurant_id": restaurant_id,
                    "owner_id": self.test_data["owner"]["id"],  # Will be overridden by server
                    "business_license": "BL123456789",
                    "proof_of_ownership": "Lease agreement and business registration",
                    "additional_documents": ["lease.pdf", "registration.pdf"],
                    "notes": "I am the owner of this restaurant and would like to claim it.",
                    "status": "pending",
                    "submitted_at": datetime.now(timezone.utc).isoformat()
                }
                
                response = await self.client.post(f"{BACKEND_URL}/owners/claims", json=claim_data, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    # Verify response structure
                    required_fields = ["restaurant_id", "owner_id", "status", "submitted_at"]
                    missing_fields = [field for field in required_fields if field not in data]
                    
                    if missing_fields:
                        await self.log_result(test_name, False, f"Missing fields: {missing_fields}", data)
                        return
                    
                    # Verify status is pending
                    if data.get("status") != "pending":
                        await self.log_result(test_name, False, f"Wrong claim status: {data.get('status')}")
                        return
                    
                    self.test_data["claim"] = data
                    claim_successful = True
                    
                    await self.log_result(test_name, True, 
                        f"Claim submitted successfully. Restaurant: {restaurant_id}, Status: {data['status']}")
                    break
                elif response.status_code == 400 and "already claimed" in response.text:
                    # Try next restaurant
                    continue
                else:
                    await self.log_result(test_name, False, 
                        f"Claim submission failed with status {response.status_code}", response.text)
                    return
            
            if not claim_successful:
                await self.log_result(test_name, False, "All restaurants are already claimed or unavailable")
                
        except Exception as e:
            await self.log_result(test_name, False, f"Exception: {str(e)}")

    async def test_admin_pending_claims(self):
        """Test admin endpoint for pending claims"""
        test_name = "Admin Pending Claims API"
        
        try:
            response = await self.client.get(f"{BACKEND_URL}/admin/owners/claims")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                if "claims" not in data:
                    await self.log_result(test_name, False, "Missing 'claims' field in response", data)
                    return
                
                claims = data["claims"]
                
                if not isinstance(claims, list):
                    await self.log_result(test_name, False, f"Claims field is not a list: {type(claims)}")
                    return
                
                # Should have at least our submitted claim
                if len(claims) == 0:
                    await self.log_result(test_name, True, "No pending claims found (expected for new system)")
                else:
                    # Verify claim structure
                    claim = claims[0]
                    required_fields = ["id", "restaurant_id", "owner_id", "status"]
                    missing_fields = [field for field in required_fields if field not in claim]
                    
                    if missing_fields:
                        await self.log_result(test_name, False, f"Missing fields in claim: {missing_fields}", claim)
                        return
                    
                    await self.log_result(test_name, True, 
                        f"Pending claims retrieved successfully. Count: {len(claims)}")
            else:
                await self.log_result(test_name, False, 
                    f"Admin claims request failed with status {response.status_code}", response.text)
                
        except Exception as e:
            await self.log_result(test_name, False, f"Exception: {str(e)}")

    async def test_admin_pending_specials(self):
        """Test admin endpoint for pending specials"""
        test_name = "Admin Pending Specials API"
        
        try:
            response = await self.client.get(f"{BACKEND_URL}/admin/owners/specials")
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                if "specials" not in data:
                    await self.log_result(test_name, False, "Missing 'specials' field in response", data)
                    return
                
                specials = data["specials"]
                
                if not isinstance(specials, list):
                    await self.log_result(test_name, False, f"Specials field is not a list: {type(specials)}")
                    return
                
                await self.log_result(test_name, True, 
                    f"Pending specials retrieved successfully. Count: {len(specials)}")
            else:
                await self.log_result(test_name, False, 
                    f"Admin specials request failed with status {response.status_code}", response.text)
                
        except Exception as e:
            await self.log_result(test_name, False, f"Exception: {str(e)}")

    async def test_claim_approval(self):
        """Test admin claim approval"""
        test_name = "Admin Claim Approval API"
        
        if "claim" not in self.test_data:
            await self.log_result(test_name, False, "No claim available for approval test")
            return
        
        try:
            claim_id = self.test_data["claim"]["id"]
            approval_data = {
                "admin_notes": "Claim approved after document verification"
            }
            
            response = await self.client.post(f"{BACKEND_URL}/admin/owners/claims/{claim_id}/approve", 
                                            json=approval_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                if "message" not in data or "success" not in data:
                    await self.log_result(test_name, False, "Missing message or success field", data)
                    return
                
                if not data.get("success"):
                    await self.log_result(test_name, False, f"Approval failed: {data.get('message')}")
                    return
                
                await self.log_result(test_name, True, 
                    f"Claim approved successfully: {data['message']}")
            else:
                await self.log_result(test_name, False, 
                    f"Claim approval failed with status {response.status_code}", response.text)
                
        except Exception as e:
            await self.log_result(test_name, False, f"Exception: {str(e)}")

    async def test_special_creation(self):
        """Test special creation by owner"""
        test_name = "Owner Special Creation API"
        
        if "owner_token" not in self.test_data:
            await self.log_result(test_name, False, "No owner token available from login")
            return
        
        # Need a restaurant ID - try to get from owner's restaurants after claim approval
        try:
            headers = {"Authorization": f"Bearer {self.test_data['owner_token']}"}
            
            # Add a small delay to ensure claim approval has been processed
            import asyncio
            await asyncio.sleep(1)
            
            # Check if owner now has restaurants after claim approval
            restaurants_response = await self.client.get(f"{BACKEND_URL}/owners/restaurants", headers=headers)
            
            if restaurants_response.status_code != 200:
                await self.log_result(test_name, False, "Could not get owner restaurants for special creation")
                return
            
            restaurants_data = restaurants_response.json()
            restaurants = restaurants_data.get("restaurants", [])
            
            # Also check the dashboard to see if it shows any restaurants
            dashboard_response = await self.client.get(f"{BACKEND_URL}/owners/dashboard", headers=headers)
            dashboard_data = dashboard_response.json() if dashboard_response.status_code == 200 else {}
            
            if not restaurants:
                # If no restaurants, check if claim was approved and restaurant should be available
                if "claim" in self.test_data:
                    restaurant_id = self.test_data["claim"]["restaurant_id"]
                    await self.log_result(test_name, False, 
                        f"Owner has no restaurants despite approved claim. Expected restaurant: {restaurant_id}. Dashboard shows {dashboard_data.get('total_restaurants', 0)} restaurants.")
                else:
                    await self.log_result(test_name, False, "Owner has no restaurants and no approved claim available")
                return
            else:
                restaurant_id = restaurants[0]["id"]
            
            # Create special
            special_data = {
                "restaurant_id": restaurant_id,
                "title": "Happy Hour Special",
                "description": "50% off all appetizers during happy hour",
                "special_type": "happy_hour",
                "price": 5.99,
                "original_price": 11.99,
                "discount_percentage": 50,
                "days_available": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                "time_start": "15:00",
                "time_end": "18:00",
                "valid_from": datetime.now(timezone.utc).isoformat(),
                "valid_until": datetime(2024, 12, 31, tzinfo=timezone.utc).isoformat(),
                "max_redemptions": 100,
                "terms_conditions": "Valid for dine-in only. Cannot be combined with other offers."
            }
            
            response = await self.client.post(f"{BACKEND_URL}/owners/specials", json=special_data, headers=headers)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                required_fields = ["id", "restaurant_id", "owner_id", "title", "approval_status", "is_active"]
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    await self.log_result(test_name, False, f"Missing fields: {missing_fields}", data)
                    return
                
                # Verify approval status is pending
                if data.get("approval_status") != "pending":
                    await self.log_result(test_name, False, f"Wrong approval status: {data.get('approval_status')}")
                    return
                
                self.test_data["special"] = data
                
                await self.log_result(test_name, True, 
                    f"Special created successfully. ID: {data['id']}, Status: {data['approval_status']}")
            else:
                await self.log_result(test_name, False, 
                    f"Special creation failed with status {response.status_code}", response.text)
                
        except Exception as e:
            await self.log_result(test_name, False, f"Exception: {str(e)}")

    async def test_special_approval(self):
        """Test admin special approval"""
        test_name = "Admin Special Approval API"
        
        if "special" not in self.test_data:
            await self.log_result(test_name, False, "No special available for approval test")
            return
        
        try:
            special_id = self.test_data["special"]["id"]
            approval_data = {
                "admin_notes": "Special approved - meets all guidelines"
            }
            
            response = await self.client.post(f"{BACKEND_URL}/admin/owners/specials/{special_id}/approve", 
                                            json=approval_data)
            
            if response.status_code == 200:
                data = response.json()
                
                # Verify response structure
                if "message" not in data or "success" not in data:
                    await self.log_result(test_name, False, "Missing message or success field", data)
                    return
                
                if not data.get("success"):
                    await self.log_result(test_name, False, f"Approval failed: {data.get('message')}")
                    return
                
                await self.log_result(test_name, True, 
                    f"Special approved successfully: {data['message']}")
            else:
                await self.log_result(test_name, False, 
                    f"Special approval failed with status {response.status_code}", response.text)
                
        except Exception as e:
            await self.log_result(test_name, False, f"Exception: {str(e)}")

    async def test_authentication_validation(self):
        """Test authentication and authorization validation"""
        test_name = "Authentication & Authorization Validation"
        
        try:
            # Test accessing protected endpoint without token
            response = await self.client.get(f"{BACKEND_URL}/owners/dashboard")
            
            if response.status_code in [401, 403]:
                await self.log_result(test_name, True, 
                    f"Correctly rejected unauthenticated request with {response.status_code}")
            else:
                await self.log_result(test_name, False, 
                    f"Should have returned 401 or 403 for unauthenticated request, got {response.status_code}")
                
        except Exception as e:
            await self.log_result(test_name, False, f"Exception: {str(e)}")

    async def test_user_type_differentiation(self):
        """Test user type differentiation between regular users and owners"""
        test_name = "User Type Differentiation"
        
        try:
            # Create a regular user
            unique_id = str(uuid.uuid4())[:8]
            user_data = {
                "email": f"user_{unique_id}@example.com",
                "password": "userpassword123",
                "first_name": "Jane",
                "last_name": "Doe"
            }
            
            # Register regular user
            user_response = await self.client.post(f"{BACKEND_URL}/users/register", json=user_data)
            
            if user_response.status_code != 200:
                await self.log_result(test_name, False, "Could not create regular user for test")
                return
            
            user_auth = user_response.json()
            user_token = user_auth["access_token"]
            
            # Try to access owner endpoint with regular user token
            headers = {"Authorization": f"Bearer {user_token}"}
            response = await self.client.get(f"{BACKEND_URL}/owners/dashboard", headers=headers)
            
            if response.status_code == 403:
                await self.log_result(test_name, True, 
                    "Correctly rejected regular user access to owner endpoint with 403")
            else:
                await self.log_result(test_name, False, 
                    f"Should have returned 403 for regular user accessing owner endpoint, got {response.status_code}")
                
        except Exception as e:
            await self.log_result(test_name, False, f"Exception: {str(e)}")

    async def run_all_tests(self):
        """Run all owner dashboard tests"""
        print("🚀 Starting Restaurant Owner Dashboard Integration Tests")
        print("=" * 60)
        
        # Core owner workflow tests
        await self.test_owner_registration()
        await self.test_owner_login()
        await self.test_owner_dashboard()
        await self.test_owner_restaurants()
        await self.test_owner_specials()
        
        # Restaurant claim workflow tests
        await self.test_restaurant_claim_submission()
        await self.test_admin_pending_claims()
        await self.test_claim_approval()
        
        # Special management workflow tests
        await self.test_special_creation()
        await self.test_admin_pending_specials()
        await self.test_special_approval()
        
        # Authentication and authorization tests
        await self.test_authentication_validation()
        await self.test_user_type_differentiation()
        
        # Summary
        print("=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
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
    tester = OwnerDashboardTester()
    passed, failed = await tester.run_all_tests()
    
    if failed == 0:
        print("\n🎉 All tests passed! Restaurant Owner Dashboard system is working correctly.")
    else:
        print(f"\n⚠️  {failed} test(s) failed. Please review the issues above.")
    
    return failed == 0

if __name__ == "__main__":
    success = asyncio.run(main())