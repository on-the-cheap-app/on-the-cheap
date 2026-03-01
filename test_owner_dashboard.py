#!/usr/bin/env python3
"""
Restaurant Owner Dashboard Testing Script
Tests the newly implemented Restaurant Owner Dashboard system
"""

import requests
import sys
import json
from datetime import datetime
import uuid

class OwnerDashboardTester:
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

    def test_owner_service_integration(self):
        """Test that owner service is properly initialized and integrated"""
        try:
            # Test a simple endpoint to verify service integration
            response = self.session.get(f"{self.api_url}/admin/owners/claims")
            success = response.status_code in [200, 401, 403]  # Service should respond, auth may be required
            
            if success:
                details = f"Owner service responding correctly (status: {response.status_code})"
            else:
                details = f"Owner service not responding properly (status: {response.status_code})"
            
            self.log_test("Owner Service Integration", success, details)
            return success
            
        except Exception as e:
            self.log_test("Owner Service Integration", False, str(e))
            return False

    def test_owner_registration(self):
        """Test restaurant owner registration"""
        try:
            # Generate unique email for testing
            unique_id = str(uuid.uuid4())[:8]
            test_data = {
                "first_name": "John",
                "last_name": "Smith",
                "email": f"owner_{unique_id}@restaurant.com",
                "password": "securepassword123",
                "phone": "+1-555-0123",
                "business_name": "Smith's Bistro",
                "business_type": "restaurant"
            }
            
            response = self.session.post(f"{self.api_url}/owners/register", json=test_data)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_fields = ['id', 'first_name', 'last_name', 'email', 'business_name', 'status']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    success = False
                    details = f"Missing required fields: {missing_fields}"
                else:
                    details = f"Owner registered: {data.get('email')}, Status: {data.get('status')}, ID: {data.get('id')}"
                    # Store owner data for subsequent tests
                    self.test_owner_data = {
                        'id': data.get('id'),
                        'email': data.get('email'),
                        'password': test_data['password']
                    }
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Owner Registration", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Owner Registration", False, str(e))
            return False, {}

    def test_owner_login(self):
        """Test restaurant owner login and JWT token generation"""
        try:
            if not hasattr(self, 'test_owner_data'):
                # Create a test owner first
                success, owner_data = self.test_owner_registration()
                if not success:
                    self.log_test("Owner Login", False, "Failed to create test owner for login test")
                    return False, {}
            
            login_data = {
                "email": self.test_owner_data['email'],
                "password": self.test_owner_data['password']
            }
            
            response = self.session.post(f"{self.api_url}/owners/login", json=login_data)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_fields = ['access_token', 'token_type', 'user_type', 'user']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    success = False
                    details = f"Missing required fields: {missing_fields}"
                elif data.get('user_type') != 'owner':
                    success = False
                    details = f"Expected user_type 'owner', got '{data.get('user_type')}'"
                else:
                    details = f"Owner logged in successfully, Token type: {data.get('token_type')}, User type: {data.get('user_type')}"
                    # Store token for authenticated requests
                    self.owner_token = data.get('access_token')
                    self.session.headers.update({'Authorization': f"Bearer {self.owner_token}"})
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Owner Login & JWT Authentication", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Owner Login & JWT Authentication", False, str(e))
            return False, {}

    def test_restaurant_claim_submission(self):
        """Test restaurant claim submission workflow"""
        try:
            if not hasattr(self, 'owner_token'):
                # Login first
                success, _ = self.test_owner_login()
                if not success:
                    self.log_test("Restaurant Claim Submission", False, "Failed to authenticate owner")
                    return False, {}
            
            # First, get a restaurant ID from the database
            restaurants_response = self.session.get(f"{self.api_url}/restaurants/search?latitude=37.7749&longitude=-122.4194&limit=1")
            if restaurants_response.status_code != 200:
                self.log_test("Restaurant Claim Submission", False, "Failed to get restaurant for claim test")
                return False, {}
            
            restaurants_data = restaurants_response.json()
            if not restaurants_data.get('restaurants'):
                self.log_test("Restaurant Claim Submission", False, "No restaurants available for claim test")
                return False, {}
            
            restaurant_id = restaurants_data['restaurants'][0]['id']
            
            claim_data = {
                "restaurant_id": restaurant_id,
                "owner_id": self.test_owner_data['id'],  # Will be overridden by server
                "business_license": "BL123456789",
                "proof_of_ownership": "Lease agreement and business registration",
                "additional_documents": ["tax_id.pdf", "insurance.pdf"],
                "notes": "I am the owner of this restaurant and would like to claim it to manage specials.",
                "status": "pending",
                "submitted_at": datetime.now().isoformat()
            }
            
            response = self.session.post(f"{self.api_url}/owners/claims", json=claim_data)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_fields = ['restaurant_id', 'owner_id', 'status', 'submitted_at']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    success = False
                    details = f"Missing required fields: {missing_fields}"
                elif data.get('status') != 'pending':
                    success = False
                    details = f"Expected status 'pending', got '{data.get('status')}'"
                else:
                    details = f"Claim submitted for restaurant {data.get('restaurant_id')}, Status: {data.get('status')}"
                    self.test_claim_id = data.get('id') or data.get('restaurant_id')  # Store for admin tests
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Restaurant Claim Submission", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Restaurant Claim Submission", False, str(e))
            return False, {}

    def test_special_creation_pending_approval(self):
        """Test special creation with pending approval workflow"""
        try:
            if not hasattr(self, 'owner_token'):
                # Login first
                success, _ = self.test_owner_login()
                if not success:
                    self.log_test("Special Creation (Pending Approval)", False, "Failed to authenticate owner")
                    return False, {}
            
            # Get a restaurant ID for the special
            restaurants_response = self.session.get(f"{self.api_url}/restaurants/search?latitude=37.7749&longitude=-122.4194&limit=1")
            if restaurants_response.status_code != 200:
                self.log_test("Special Creation (Pending Approval)", False, "Failed to get restaurant for special test")
                return False, {}
            
            restaurants_data = restaurants_response.json()
            if not restaurants_data.get('restaurants'):
                self.log_test("Special Creation (Pending Approval)", False, "No restaurants available for special test")
                return False, {}
            
            restaurant_id = restaurants_data['restaurants'][0]['id']
            
            special_data = {
                "restaurant_id": restaurant_id,
                "title": "Happy Hour Special",
                "description": "50% off all appetizers and $5 craft cocktails during happy hour",
                "special_type": "happy_hour",
                "price": 5.00,
                "original_price": 10.00,
                "discount_percentage": 50,
                "days_available": ["monday", "tuesday", "wednesday", "thursday", "friday"],
                "time_start": "16:00",
                "time_end": "19:00",
                "valid_from": datetime.now().isoformat(),
                "valid_until": "2024-12-31T23:59:59",
                "max_redemptions": 100,
                "terms_conditions": "Cannot be combined with other offers. Valid for dine-in only."
            }
            
            response = self.session.post(f"{self.api_url}/owners/specials", json=special_data)
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_fields = ['id', 'restaurant_id', 'title', 'approval_status', 'is_active']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    success = False
                    details = f"Missing required fields: {missing_fields}"
                elif data.get('approval_status') != 'pending':
                    success = False
                    details = f"Expected approval_status 'pending', got '{data.get('approval_status')}'"
                elif data.get('is_active') != False:
                    success = False
                    details = f"Expected is_active False (pending approval), got {data.get('is_active')}"
                else:
                    details = f"Special created: {data.get('title')}, Status: {data.get('approval_status')}, Active: {data.get('is_active')}"
                    self.test_special_id = data.get('id')  # Store for admin tests
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Special Creation (Pending Approval)", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Special Creation (Pending Approval)", False, str(e))
            return False, {}

    def test_owner_dashboard_stats(self):
        """Test owner dashboard statistics endpoint"""
        try:
            if not hasattr(self, 'owner_token'):
                # Login first
                success, _ = self.test_owner_login()
                if not success:
                    self.log_test("Owner Dashboard Statistics", False, "Failed to authenticate owner")
                    return False, {}
            
            response = self.session.get(f"{self.api_url}/owners/dashboard")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                required_fields = ['total_restaurants', 'pending_claims', 'active_specials', 'pending_specials', 'total_views', 'total_favorites']
                missing_fields = [field for field in required_fields if field not in data]
                
                if missing_fields:
                    success = False
                    details = f"Missing required fields: {missing_fields}"
                else:
                    details = f"Dashboard stats - Restaurants: {data.get('total_restaurants')}, Pending Claims: {data.get('pending_claims')}, Active Specials: {data.get('active_specials')}, Pending Specials: {data.get('pending_specials')}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Owner Dashboard Statistics", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Owner Dashboard Statistics", False, str(e))
            return False, {}

    def test_owner_specials_list(self):
        """Test getting owner's specials list"""
        try:
            if not hasattr(self, 'owner_token'):
                # Login first
                success, _ = self.test_owner_login()
                if not success:
                    self.log_test("Owner Specials List", False, "Failed to authenticate owner")
                    return False, {}
            
            response = self.session.get(f"{self.api_url}/owners/specials")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if 'specials' not in data:
                    success = False
                    details = "Missing 'specials' field in response"
                else:
                    specials = data['specials']
                    details = f"Found {len(specials)} specials for owner"
                    
                    # Validate special structure if any exist
                    if specials:
                        first_special = specials[0]
                        required_fields = ['id', 'restaurant_id', 'title', 'approval_status']
                        missing_fields = [field for field in required_fields if field not in first_special]
                        if missing_fields:
                            success = False
                            details += f" - Missing fields in special: {missing_fields}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Owner Specials List", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Owner Specials List", False, str(e))
            return False, {}

    def test_owner_restaurants_list(self):
        """Test getting owner's restaurants list"""
        try:
            if not hasattr(self, 'owner_token'):
                # Login first
                success, _ = self.test_owner_login()
                if not success:
                    self.log_test("Owner Restaurants List", False, "Failed to authenticate owner")
                    return False, {}
            
            response = self.session.get(f"{self.api_url}/owners/restaurants")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if 'restaurants' not in data:
                    success = False
                    details = "Missing 'restaurants' field in response"
                else:
                    restaurants = data['restaurants']
                    details = f"Found {len(restaurants)} restaurants for owner"
                    
                    # Validate restaurant structure if any exist
                    if restaurants:
                        first_restaurant = restaurants[0]
                        required_fields = ['id', 'name', 'address']
                        missing_fields = [field for field in required_fields if field not in first_restaurant]
                        if missing_fields:
                            success = False
                            details += f" - Missing fields in restaurant: {missing_fields}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Owner Restaurants List", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Owner Restaurants List", False, str(e))
            return False, {}

    def test_admin_pending_claims(self):
        """Test admin endpoint for viewing pending claims"""
        try:
            # Remove owner auth header for admin test
            if 'Authorization' in self.session.headers:
                del self.session.headers['Authorization']
            
            response = self.session.get(f"{self.api_url}/admin/owners/claims")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if 'claims' not in data:
                    success = False
                    details = "Missing 'claims' field in response"
                else:
                    claims = data['claims']
                    details = f"Found {len(claims)} pending claims"
                    
                    # Validate claim structure if any exist
                    if claims:
                        first_claim = claims[0]
                        required_fields = ['restaurant_id', 'owner_id', 'status']
                        missing_fields = [field for field in required_fields if field not in first_claim]
                        if missing_fields:
                            success = False
                            details += f" - Missing fields in claim: {missing_fields}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Admin Pending Claims View", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Admin Pending Claims View", False, str(e))
            return False, {}

    def test_admin_pending_specials(self):
        """Test admin endpoint for viewing pending specials"""
        try:
            # Remove owner auth header for admin test
            if 'Authorization' in self.session.headers:
                del self.session.headers['Authorization']
            
            response = self.session.get(f"{self.api_url}/admin/owners/specials")
            success = response.status_code == 200
            
            if success:
                data = response.json()
                if 'specials' not in data:
                    success = False
                    details = "Missing 'specials' field in response"
                else:
                    specials = data['specials']
                    details = f"Found {len(specials)} pending specials"
                    
                    # Validate special structure if any exist
                    if specials:
                        first_special = specials[0]
                        required_fields = ['id', 'restaurant_id', 'title', 'approval_status']
                        missing_fields = [field for field in required_fields if field not in first_special]
                        if missing_fields:
                            success = False
                            details += f" - Missing fields in special: {missing_fields}"
            else:
                details = f"Status: {response.status_code}, Response: {response.text[:200]}"
            
            self.log_test("Admin Pending Specials View", success, details)
            return success, data if success else {}
            
        except Exception as e:
            self.log_test("Admin Pending Specials View", False, str(e))
            return False, {}

    def test_database_integration_owners(self):
        """Test database integration for owner data"""
        try:
            # Test that owner registration creates proper database records
            unique_id = str(uuid.uuid4())[:8]
            test_data = {
                "first_name": "Database",
                "last_name": "Test",
                "email": f"dbtest_{unique_id}@restaurant.com",
                "password": "testpassword123",
                "phone": "+1-555-9999",
                "business_name": "DB Test Restaurant",
                "business_type": "restaurant"
            }
            
            # Register owner
            response = self.session.post(f"{self.api_url}/owners/register", json=test_data)
            success = response.status_code == 200
            
            if success:
                owner_data = response.json()
                owner_id = owner_data.get('id')
                
                # Login to get token
                login_response = self.session.post(f"{self.api_url}/owners/login", json={
                    "email": test_data['email'],
                    "password": test_data['password']
                })
                
                if login_response.status_code == 200:
                    login_data = login_response.json()
                    token = login_data.get('access_token')
                    
                    # Test authenticated endpoint to verify database persistence
                    self.session.headers.update({'Authorization': f"Bearer {token}"})
                    dashboard_response = self.session.get(f"{self.api_url}/owners/dashboard")
                    
                    if dashboard_response.status_code == 200:
                        dashboard_data = dashboard_response.json()
                        details = f"Database integration working - Owner ID: {owner_id}, Dashboard accessible with stats: {dashboard_data}"
                    else:
                        success = False
                        details = f"Database integration issue - Dashboard not accessible after registration"
                else:
                    success = False
                    details = f"Database integration issue - Login failed after registration"
            else:
                details = f"Database integration issue - Registration failed: {response.text[:200]}"
            
            self.log_test("Database Integration (Owners)", success, details)
            return success
            
        except Exception as e:
            self.log_test("Database Integration (Owners)", False, str(e))
            return False

    def run_all_tests(self):
        """Run all owner dashboard tests"""
        print("🏪 TESTING RESTAURANT OWNER DASHBOARD SYSTEM")
        print("=" * 70)
        print("Testing the newly implemented Restaurant Owner Dashboard system including:")
        print("- Owner Service Integration")
        print("- Owner Registration & Authentication")
        print("- Restaurant Claiming System")
        print("- Special Management System")
        print("- Owner Dashboard Functionality")
        print("- Admin Approval Workflows")
        print("- Database Integration")
        print("=" * 70)
        
        # Run owner dashboard system tests
        print("\n📋 Running Restaurant Owner Dashboard tests...")
        
        # 1. Owner Service Integration
        self.test_owner_service_integration()
        
        # 2. Owner Registration & Authentication
        self.test_owner_registration()
        self.test_owner_login()
        
        # 3. Restaurant Claiming System
        self.test_restaurant_claim_submission()
        
        # 4. Special Management System
        self.test_special_creation_pending_approval()
        self.test_owner_specials_list()
        
        # 5. Owner Dashboard
        self.test_owner_dashboard_stats()
        self.test_owner_restaurants_list()
        
        # 6. Admin Endpoints
        self.test_admin_pending_claims()
        self.test_admin_pending_specials()
        
        # 7. Database Integration
        self.test_database_integration_owners()
        
        # Print summary
        print("\n" + "=" * 70)
        print(f"📊 RESTAURANT OWNER DASHBOARD Results: {self.tests_passed}/{self.tests_run} tests passed")
        
        if self.tests_passed == self.tests_run:
            print("🎉 All Restaurant Owner Dashboard tests passed!")
            print("✅ Owner Dashboard system is working correctly")
            return 0
        else:
            print(f"⚠️  {self.tests_run - self.tests_passed} Owner Dashboard tests failed")
            return 1

if __name__ == "__main__":
    tester = OwnerDashboardTester()
    sys.exit(tester.run_all_tests())