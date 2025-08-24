#!/usr/bin/env python3
"""
Focused test for user registration API
"""

import requests
import uuid
import json

def test_user_registration():
    """Test user registration endpoint"""
    base_url = "https://special-finder.preview.emergentagent.com"
    api_url = f"{base_url}/api"
    
    test_email = f"focused_test_{uuid.uuid4().hex[:8]}@example.com"
    registration_data = {
        "email": test_email,
        "password": "TestPassword123!",
        "first_name": "Focused",
        "last_name": "Test"
    }
    
    try:
        session = requests.Session()
        session.headers.update({'Content-Type': 'application/json'})
        
        print(f"Testing user registration with email: {test_email}")
        response = session.post(f"{api_url}/users/register", json=registration_data)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print("✅ User registration successful!")
            print(f"User ID: {data.get('user', {}).get('id', 'N/A')}")
            print(f"User Type: {data.get('user_type', 'N/A')}")
            print(f"Token received: {bool(data.get('access_token'))}")
            return True
        else:
            print("❌ User registration failed!")
            return False
            
    except Exception as e:
        print(f"❌ Exception during test: {e}")
        return False

if __name__ == "__main__":
    test_user_registration()