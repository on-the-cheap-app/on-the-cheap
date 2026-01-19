"""
Test Suite for Restaurant Special Image Upload Feature
Tests: Create/Update specials with Base64 image encoding
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

# Small 1x1 pixel base64 image for testing
TEST_IMAGE_BASE64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="


class TestImageUploadFeature:
    """Test image upload functionality for specials"""
    
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
    
    def test_create_special_with_image(self, auth_headers):
        """Test creating a special with base64 image"""
        valid_from = datetime.now().strftime("%Y-%m-%d")
        valid_until = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        special_data = {
            "restaurant_id": RESTAURANT_ID,
            "title": "TEST_Special With Image",
            "description": "Test special with image upload",
            "special_type": "daily_special",
            "price": 12.99,
            "days_available": ["monday", "tuesday", "wednesday"],
            "time_start": "11:00",
            "time_end": "21:00",
            "valid_from": valid_from,
            "valid_until": valid_until,
            "image": TEST_IMAGE_BASE64  # Include base64 image
        }
        
        response = requests.post(
            f"{BASE_URL}/api/owners/specials",
            headers=auth_headers,
            json=special_data
        )
        
        assert response.status_code == 200, f"Create special with image failed: {response.text}"
        data = response.json()
        
        # Verify response structure
        assert "id" in data, "Missing id in response"
        assert data["title"] == special_data["title"]
        assert data["image"] == TEST_IMAGE_BASE64, "Image not saved correctly"
        
        print(f"✓ Special with image created with ID: {data['id']}")
        return data
    
    def test_create_special_without_image(self, auth_headers):
        """Test creating a special without image (should work)"""
        valid_from = datetime.now().strftime("%Y-%m-%d")
        valid_until = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        special_data = {
            "restaurant_id": RESTAURANT_ID,
            "title": "TEST_Special Without Image",
            "description": "Test special without image",
            "special_type": "happy_hour",
            "price": 8.99,
            "days_available": ["friday", "saturday"],
            "time_start": "16:00",
            "time_end": "19:00",
            "valid_from": valid_from,
            "valid_until": valid_until
            # No image field
        }
        
        response = requests.post(
            f"{BASE_URL}/api/owners/specials",
            headers=auth_headers,
            json=special_data
        )
        
        assert response.status_code == 200, f"Create special without image failed: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert data.get("image") is None, "Image should be None when not provided"
        
        print(f"✓ Special without image created with ID: {data['id']}")
        return data
    
    def test_create_special_with_null_image(self, auth_headers):
        """Test creating a special with explicit null image"""
        valid_from = datetime.now().strftime("%Y-%m-%d")
        valid_until = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        special_data = {
            "restaurant_id": RESTAURANT_ID,
            "title": "TEST_Special Null Image",
            "description": "Test special with null image",
            "special_type": "lunch_special",
            "price": 10.99,
            "days_available": ["monday"],
            "time_start": "11:00",
            "time_end": "14:00",
            "valid_from": valid_from,
            "valid_until": valid_until,
            "image": None  # Explicit null
        }
        
        response = requests.post(
            f"{BASE_URL}/api/owners/specials",
            headers=auth_headers,
            json=special_data
        )
        
        assert response.status_code == 200, f"Create special with null image failed: {response.text}"
        data = response.json()
        
        assert "id" in data
        assert data.get("image") is None
        
        print(f"✓ Special with null image created with ID: {data['id']}")
        return data
    
    def test_update_special_add_image(self, auth_headers):
        """Test updating a special to add an image"""
        valid_from = datetime.now().strftime("%Y-%m-%d")
        valid_until = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        # First create a special without image
        create_data = {
            "restaurant_id": RESTAURANT_ID,
            "title": "TEST_Special Add Image Later",
            "description": "Will add image via update",
            "special_type": "daily_special",
            "price": 9.99,
            "days_available": ["tuesday"],
            "time_start": "11:00",
            "time_end": "21:00",
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
        
        # Update to add image
        update_data = {
            "restaurant_id": RESTAURANT_ID,
            "title": "TEST_Special Add Image Later",
            "description": "Image added via update",
            "special_type": "daily_special",
            "price": 9.99,
            "days_available": ["tuesday"],
            "time_start": "11:00",
            "time_end": "21:00",
            "valid_from": valid_from,
            "valid_until": valid_until,
            "image": TEST_IMAGE_BASE64  # Add image
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/owners/specials/{special_id}",
            headers=auth_headers,
            json=update_data
        )
        
        assert update_response.status_code == 200, f"Update to add image failed: {update_response.text}"
        updated_special = update_response.json()
        
        assert updated_special["image"] == TEST_IMAGE_BASE64, "Image not added via update"
        
        print(f"✓ Image added to special {special_id} via update")
        return special_id
    
    def test_update_special_preserve_image(self, auth_headers):
        """Test updating a special preserves existing image when not provided"""
        valid_from = datetime.now().strftime("%Y-%m-%d")
        valid_until = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Create special with image
        create_data = {
            "restaurant_id": RESTAURANT_ID,
            "title": "TEST_Special Preserve Image",
            "description": "Original description",
            "special_type": "daily_special",
            "price": 11.99,
            "days_available": ["wednesday"],
            "time_start": "11:00",
            "time_end": "21:00",
            "valid_from": valid_from,
            "valid_until": valid_until,
            "image": TEST_IMAGE_BASE64
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/owners/specials",
            headers=auth_headers,
            json=create_data
        )
        
        assert create_response.status_code == 200
        special_id = create_response.json()["id"]
        
        # Update without image field - should preserve existing image
        update_data = {
            "restaurant_id": RESTAURANT_ID,
            "title": "TEST_Special Preserve Image Updated",
            "description": "Updated description",
            "special_type": "daily_special",
            "price": 13.99,
            "days_available": ["wednesday", "thursday"],
            "time_start": "11:00",
            "time_end": "21:00",
            "valid_from": valid_from,
            "valid_until": valid_until
            # No image field - should preserve existing
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/owners/specials/{special_id}",
            headers=auth_headers,
            json=update_data
        )
        
        assert update_response.status_code == 200, f"Update failed: {update_response.text}"
        updated_special = update_response.json()
        
        # Image should be preserved
        assert updated_special["image"] == TEST_IMAGE_BASE64, "Image was not preserved during update"
        assert updated_special["title"] == update_data["title"]
        assert updated_special["price"] == update_data["price"]
        
        print(f"✓ Image preserved during update of special {special_id}")
        return special_id
    
    def test_update_special_remove_image(self, auth_headers):
        """Test updating a special to remove image by setting to null"""
        valid_from = datetime.now().strftime("%Y-%m-%d")
        valid_until = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Create special with image
        create_data = {
            "restaurant_id": RESTAURANT_ID,
            "title": "TEST_Special Remove Image",
            "description": "Will remove image",
            "special_type": "daily_special",
            "price": 14.99,
            "days_available": ["thursday"],
            "time_start": "11:00",
            "time_end": "21:00",
            "valid_from": valid_from,
            "valid_until": valid_until,
            "image": TEST_IMAGE_BASE64
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/owners/specials",
            headers=auth_headers,
            json=create_data
        )
        
        assert create_response.status_code == 200
        special_id = create_response.json()["id"]
        
        # Update with null image to remove it
        update_data = {
            "restaurant_id": RESTAURANT_ID,
            "title": "TEST_Special Remove Image",
            "description": "Image removed",
            "special_type": "daily_special",
            "price": 14.99,
            "days_available": ["thursday"],
            "time_start": "11:00",
            "time_end": "21:00",
            "valid_from": valid_from,
            "valid_until": valid_until,
            "image": None  # Explicitly remove image
        }
        
        update_response = requests.put(
            f"{BASE_URL}/api/owners/specials/{special_id}",
            headers=auth_headers,
            json=update_data
        )
        
        assert update_response.status_code == 200, f"Update to remove image failed: {update_response.text}"
        updated_special = update_response.json()
        
        assert updated_special.get("image") is None, "Image was not removed"
        
        print(f"✓ Image removed from special {special_id}")
        return special_id
    
    def test_get_specials_returns_image(self, auth_headers):
        """Test that GET specials returns image field"""
        valid_from = datetime.now().strftime("%Y-%m-%d")
        valid_until = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        
        # Create special with image
        create_data = {
            "restaurant_id": RESTAURANT_ID,
            "title": "TEST_Special Get Image",
            "description": "Test getting image in list",
            "special_type": "daily_special",
            "price": 15.99,
            "days_available": ["friday"],
            "time_start": "11:00",
            "time_end": "21:00",
            "valid_from": valid_from,
            "valid_until": valid_until,
            "image": TEST_IMAGE_BASE64
        }
        
        create_response = requests.post(
            f"{BASE_URL}/api/owners/specials",
            headers=auth_headers,
            json=create_data
        )
        
        assert create_response.status_code == 200
        special_id = create_response.json()["id"]
        
        # Get specials list
        list_response = requests.get(
            f"{BASE_URL}/api/owners/specials",
            headers=auth_headers
        )
        
        assert list_response.status_code == 200
        specials = list_response.json()["specials"]
        
        # Find our special and verify image is returned
        found = False
        for special in specials:
            if special["id"] == special_id:
                found = True
                assert special.get("image") == TEST_IMAGE_BASE64, "Image not returned in GET specials"
                break
        
        assert found, f"Created special {special_id} not found in list"
        print(f"✓ Image correctly returned in GET specials for {special_id}")
        return special_id


class TestImageUploadCleanup:
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
