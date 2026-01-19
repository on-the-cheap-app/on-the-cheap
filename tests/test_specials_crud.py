"""
Test Suite for Restaurant Owner Specials CRUD Operations
Tests: Create, Read, Update, Delete specials via API endpoints
"""

import pytest
import requests
import os
from datetime import datetime, timedelta

# Get backend URL from environment
BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# Test credentials
OWNER_EMAIL = "demo@onthecheapapp.com"
OWNER_PASSWORD = "Demo123!"
RESTAURANT_ID = "6f5c2507-dd5b-4db4-8da7-4a81e95e345f"


class TestOwnerAuthentication:
    """Test owner login functionality"""
    
    def test_owner_login_success(self):
        """Test successful owner login"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        
        assert response.status_code == 200, f"Login failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "access_token" in data, "Missing access_token in response"
        assert "user" in data, "Missing user in response"
        assert data["user"]["email"] == OWNER_EMAIL
        assert data.get("user_type") == "owner"
        
        print(f"✓ Owner login successful for {OWNER_EMAIL}")
        return data["access_token"]
    
    def test_owner_login_invalid_credentials(self):
        """Test login with invalid credentials"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": "invalid@test.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401, f"Expected 401, got {response.status_code}"
        print("✓ Invalid credentials correctly rejected")


class TestOwnerDashboard:
    """Test owner dashboard endpoints"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed - skipping authenticated tests")
    
    def test_get_dashboard_stats(self, auth_token):
        """Test getting dashboard statistics"""
        response = requests.get(
            f"{BASE_URL}/api/owners/dashboard",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Dashboard request failed: {response.text}"
        data = response.json()
        
        # Verify dashboard stats structure
        assert "total_restaurants" in data
        assert "pending_claims" in data
        assert "active_specials" in data
        assert "pending_specials" in data
        
        print(f"✓ Dashboard stats retrieved: {data}")
    
    def test_get_owner_restaurants(self, auth_token):
        """Test getting owner's restaurants"""
        response = requests.get(
            f"{BASE_URL}/api/owners/restaurants",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        
        assert response.status_code == 200, f"Restaurants request failed: {response.text}"
        data = response.json()
        
        assert "restaurants" in data
        assert isinstance(data["restaurants"], list)
        
        # Verify at least one restaurant exists (Demo Bistro & Bar)
        assert len(data["restaurants"]) > 0, "Owner should have at least one restaurant"
        
        print(f"✓ Owner has {len(data['restaurants'])} restaurant(s)")
        return data["restaurants"]


class TestSpecialsCRUD:
    """Test Specials CRUD operations"""
    
    @pytest.fixture
    def auth_token(self):
        """Get authentication token"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        if response.status_code == 200:
            return response.json().get("access_token")
        pytest.skip("Authentication failed - skipping authenticated tests")
    
    @pytest.fixture
    def auth_headers(self, auth_token):
        """Get auth headers"""
        return {
            "Authorization": f"Bearer {auth_token}",
            "Content-Type": "application/json"
        }
    
    def test_get_specials_list(self, auth_headers):
        """Test getting list of specials"""
        response = requests.get(
            f"{BASE_URL}/api/owners/specials",
            headers=auth_headers
        )
        
        assert response.status_code == 200, f"Get specials failed: {response.text}"
        data = response.json()
        
        assert "specials" in data
        assert isinstance(data["specials"], list)
        
        print(f"✓ Retrieved {len(data['specials'])} special(s)")
        return data["specials"]
    
    def test_create_special(self, auth_headers):
        """Test creating a new special"""
        # Create special data
        valid_from = datetime.now().strftime("%Y-%m-%d")
        valid_until = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        special_data = {
            "restaurant_id": RESTAURANT_ID,
            "title": "TEST_Happy Hour Special",
            "description": "Test special created by automated testing",
            "special_type": "happy_hour",
            "price": 9.99,
            "original_price": 14.99,
            "discount_percentage": 33,
            "days_available": ["monday", "tuesday", "wednesday"],
            "time_start": "16:00",
            "time_end": "19:00",
            "valid_from": valid_from,
            "valid_until": valid_until,
            "max_redemptions": 100,
            "terms_conditions": "Test terms and conditions"
        }
        
        response = requests.post(
            f"{BASE_URL}/api/owners/specials",
            headers=auth_headers,
            json=special_data
        )
        
        assert response.status_code == 200, f"Create special failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "id" in data, "Missing id in response"
        assert data["title"] == special_data["title"]
        assert data["description"] == special_data["description"]
        assert data["special_type"] == special_data["special_type"]
        assert data["approval_status"] == "pending"  # New specials should be pending
        
        print(f"✓ Special created with ID: {data['id']}")
        return data
    
    def test_create_special_and_verify_persistence(self, auth_headers):
        """Test creating a special and verifying it persists in the list"""
        # Create special
        valid_from = datetime.now().strftime("%Y-%m-%d")
        valid_until = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        special_data = {
            "restaurant_id": RESTAURANT_ID,
            "title": "TEST_Persistence Check Special",
            "description": "Testing data persistence",
            "special_type": "daily_special",
            "price": 12.99,
            "days_available": ["thursday", "friday"],
            "time_start": "11:00",
            "time_end": "14:00",
            "valid_from": valid_from,
            "valid_until": valid_until
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/owners/specials",
            headers=auth_headers,
            json=special_data
        )
        
        assert create_response.status_code == 200, f"Create failed: {create_response.text}"
        created_special = create_response.json()
        special_id = created_special["id"]
        
        # Verify by getting the list
        list_response = requests.get(
            f"{BASE_URL}/api/owners/specials",
            headers=auth_headers
        )
        
        assert list_response.status_code == 200
        specials = list_response.json()["specials"]
        
        # Find the created special in the list
        found = False
        for special in specials:
            if special["id"] == special_id:
                found = True
                assert special["title"] == special_data["title"]
                break
        
        assert found, f"Created special {special_id} not found in list"
        print(f"✓ Special {special_id} persisted and verified in list")
        
        return special_id
    
    def test_update_special(self, auth_headers):
        """Test updating an existing special"""
        # First create a special to update
        valid_from = datetime.now().strftime("%Y-%m-%d")
        valid_until = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        create_data = {
            "restaurant_id": RESTAURANT_ID,
            "title": "TEST_Special to Update",
            "description": "Original description",
            "special_type": "lunch_special",
            "price": 8.99,
            "days_available": ["monday"],
            "time_start": "11:00",
            "time_end": "14:00",
            "valid_from": valid_from,
            "valid_until": valid_until
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/owners/specials",
            headers=auth_headers,
            json=create_data
        )
        
        assert create_response.status_code == 200
        special_id = create_response.json()["id"]
        
        # Update the special
        update_data = {
            "restaurant_id": RESTAURANT_ID,
            "title": "TEST_Updated Special Title",
            "description": "Updated description",
            "special_type": "dinner_special",
            "price": 15.99,
            "days_available": ["monday", "tuesday", "wednesday"],
            "time_start": "17:00",
            "time_end": "21:00",
            "valid_from": valid_from,
            "valid_until": valid_until
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/owners/specials/{special_id}",
            headers=auth_headers,
            json=update_data
        )
        
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        updated_special = update_response.json()
        
        # Verify updates
        assert updated_special["title"] == update_data["title"]
        assert updated_special["description"] == update_data["description"]
        assert updated_special["special_type"] == update_data["special_type"]
        assert updated_special["price"] == update_data["price"]
        
        print(f"✓ Special {special_id} updated successfully")
        return special_id
    
    def test_delete_special(self, auth_headers):
        """Test deleting a special"""
        # First create a special to delete
        valid_from = datetime.now().strftime("%Y-%m-%d")
        valid_until = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        create_data = {
            "restaurant_id": RESTAURANT_ID,
            "title": "TEST_Special to Delete",
            "description": "This will be deleted",
            "special_type": "happy_hour",
            "price": 5.99,
            "days_available": ["friday"],
            "time_start": "16:00",
            "time_end": "19:00",
            "valid_from": valid_from,
            "valid_until": valid_until
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/owners/specials",
            headers=auth_headers,
            json=create_data
        )
        
        assert create_response.status_code == 200
        special_id = create_response.json()["id"]
        
        # Delete the special
        delete_response = requests.delete(
            f"{BASE_URL}/api/owners/specials/{special_id}",
            headers=auth_headers
        )
        
        assert delete_response.status_code == 200, f"Delete failed: {delete_response.text}"
        
        # Verify deletion by checking the list
        list_response = requests.get(
            f"{BASE_URL}/api/owners/specials",
            headers=auth_headers
        )
        
        assert list_response.status_code == 200
        specials = list_response.json()["specials"]
        
        # Verify the special is no longer in the list
        for special in specials:
            assert special["id"] != special_id, f"Deleted special {special_id} still in list"
        
        print(f"✓ Special {special_id} deleted and verified removed from list")
    
    def test_create_special_missing_required_fields(self, auth_headers):
        """Test creating a special with missing required fields"""
        # Missing required fields
        invalid_data = {
            "restaurant_id": RESTAURANT_ID,
            "title": "Incomplete Special"
            # Missing: description, special_type, days_available, time_start, time_end, valid_from, valid_until
        }
        
        response = requests.post(
            f"{BASE_URL}/api/owners/specials",
            headers=auth_headers,
            json=invalid_data
        )
        
        # Should fail with 422 (validation error)
        assert response.status_code == 422, f"Expected 422, got {response.status_code}"
        print("✓ Missing required fields correctly rejected with 422")
    
    def test_unauthorized_access(self):
        """Test accessing specials without authentication"""
        response = requests.get(f"{BASE_URL}/api/owners/specials")
        
        # Should fail with 401 or 403
        assert response.status_code in [401, 403], f"Expected 401/403, got {response.status_code}"
        print("✓ Unauthorized access correctly rejected")


class TestSpecialTypes:
    """Test special type selection"""
    
    def test_get_special_types(self):
        """Test getting available special types"""
        response = requests.get(f"{BASE_URL}/api/specials/types")
        
        assert response.status_code == 200, f"Get special types failed: {response.text}"
        data = response.json()
        
        assert "special_types" in data
        assert isinstance(data["special_types"], list)
        assert len(data["special_types"]) > 0
        
        # Verify structure of special types
        for special_type in data["special_types"]:
            assert "value" in special_type
            assert "label" in special_type
        
        print(f"✓ Retrieved {len(data['special_types'])} special types")


class TestCleanup:
    """Cleanup test data"""
    
    @pytest.fixture
    def auth_headers(self):
        """Get auth headers"""
        response = requests.post(f"{BASE_URL}/api/auth/login", json={
            "email": OWNER_EMAIL,
            "password": OWNER_PASSWORD
        })
        if response.status_code == 200:
            token = response.json().get("access_token")
            return {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json"
            }
        pytest.skip("Authentication failed")
    
    def test_cleanup_test_specials(self, auth_headers):
        """Clean up TEST_ prefixed specials"""
        # Get all specials
        response = requests.get(
            f"{BASE_URL}/api/owners/specials",
            headers=auth_headers
        )
        
        if response.status_code != 200:
            print("Could not get specials for cleanup")
            return
        
        specials = response.json().get("specials", [])
        deleted_count = 0
        
        for special in specials:
            if special.get("title", "").startswith("TEST_"):
                delete_response = requests.delete(
                    f"{BASE_URL}/api/owners/specials/{special['id']}",
                    headers=auth_headers
                )
                if delete_response.status_code == 200:
                    deleted_count += 1
        
        print(f"✓ Cleaned up {deleted_count} test special(s)")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
