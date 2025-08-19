#!/usr/bin/env python
"""
Simple test to investigate the logout issue during booking
"""
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"

def test_login_and_session():
    print("🔍 TESTING LOGIN AND SESSION PERSISTENCE")
    print("=" * 50)
    
    # Test credentials
    login_data = {
        "email": "asliprinceraj@gmail.com",
        "password": "testpass123"
    }
    
    print("\n1️⃣ Testing Login...")
    try:
        response = requests.post(f"{BASE_URL}/api/auth/login/", json=login_data, timeout=10)
        print(f"Status: {response.status_code}")
        
        if response.status_code == 200:
            auth_data = response.json()
            access_token = auth_data.get('access')
            print(f"✅ Login successful!")
            print(f"   Access token (first 30 chars): {access_token[:30]}...")
            
            headers = {
                'Authorization': f'Bearer {access_token}',
                'Content-Type': 'application/json'
            }
            
            # Test session persistence
            print("\n2️⃣ Testing Session Persistence...")
            test_profile_access(headers)
            
            # Test booking creation
            print("\n3️⃣ Testing Cart Creation (Puja Booking)...")
            test_cart_creation(headers)
            
            # Test session after cart creation
            print("\n4️⃣ Testing Session After Cart Creation...")
            test_profile_access(headers)
            
        else:
            print(f"❌ Login failed: {response.status_code}")
            if response.content:
                error_data = response.json()
                print(f"   Error: {error_data}")
            
            # Try production credentials
            print("\n   Trying production credentials...")
            login_data["password"] = "Testpass@123"
            response = requests.post(f"{BASE_URL}/api/auth/login/", json=login_data, timeout=10)
            
            if response.status_code == 200:
                auth_data = response.json()
                access_token = auth_data.get('access')
                print(f"✅ Login successful with production credentials!")
                
                headers = {
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json'
                }
                
                # Test session persistence with production creds
                print("\n2️⃣ Testing Session Persistence (Prod)...")
                test_profile_access(headers)
                
            else:
                print(f"❌ Production login also failed: {response.status_code}")
    
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to server. Is Django running on port 8000?")
    except Exception as e:
        print(f"❌ Error: {e}")

def test_profile_access(headers):
    """Test access to user profile to check session validity"""
    try:
        response = requests.get(f"{BASE_URL}/api/auth/profile/", headers=headers, timeout=10)
        
        if response.status_code == 200:
            profile_data = response.json()
            print(f"   ✅ Profile access successful - User: {profile_data.get('email', 'Unknown')}")
        elif response.status_code == 401:
            print(f"   ❌ AUTHENTICATION FAILED - Session expired/invalid!")
            print(f"      Response: {response.json() if response.content else 'No content'}")
        else:
            print(f"   ⚠️ Unexpected response: {response.status_code}")
            
    except Exception as e:
        print(f"   ❌ Error accessing profile: {e}")

def test_cart_creation(headers):
    """Test cart creation which is part of the booking flow"""
    try:
        # Simple cart data
        cart_data = {
            "puja_service": 1,  # Assuming service ID 1 exists
            "selected_date": "2024-12-25",
            "selected_time": "10:00 AM",
            "special_instructions": "Test booking"
        }
        
        response = requests.post(f"{BASE_URL}/api/cart/carts/", json=cart_data, headers=headers, timeout=10)
        
        if response.status_code == 201:
            cart_response = response.json()
            print(f"   ✅ Cart created successfully!")
            print(f"      Cart ID: {cart_response.get('cart_id', 'Unknown')}")
            
        elif response.status_code == 401:
            print(f"   ❌ AUTHENTICATION FAILED DURING CART CREATION!")
            print(f"      This could be the logout issue!")
            print(f"      Response: {response.json() if response.content else 'No content'}")
            
        else:
            print(f"   ❌ Cart creation failed: {response.status_code}")
            if response.content:
                error_data = response.json()
                print(f"      Error: {error_data}")
                
    except Exception as e:
        print(f"   ❌ Error creating cart: {e}")

if __name__ == "__main__":
    test_login_and_session()
