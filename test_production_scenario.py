#!/usr/bin/env python
"""
Manual test to simulate the production IntegrityError scenario
"""
import requests
import json

def test_production_scenario():
    """Test the exact scenario that caused the production error"""
    print("🔍 Testing production IntegrityError scenario...")
    
    base_url = "http://127.0.0.1:8000"
    
    # First registration (should succeed)
    registration_data = {
        'email': 'test_user@example.com',
        'phone': '+919999888777',
        'password': 'testpass123',
        'password2': 'testpass123'
    }
    
    print("📝 First registration attempt...")
    response1 = requests.post(f"{base_url}/api/auth/register/", json=registration_data)
    print(f"   Status: {response1.status_code}")
    print(f"   Response: {response1.text}")
    
    if response1.status_code in [200, 201]:
        print("✅ First registration successful")
        
        # Second registration with same phone (should fail gracefully)
        print("\\n📝 Second registration with duplicate phone...")
        registration_data['email'] = 'different_user@example.com'  # Different email, same phone
        
        response2 = requests.post(f"{base_url}/api/auth/register/", json=registration_data)
        print(f"   Status: {response2.status_code}")
        print(f"   Response: {response2.text}")
        
        if response2.status_code == 400:
            try:
                response_data = response2.json()
                if 'phone' in response_data or 'field_errors' in response_data:
                    print("✅ SUCCESS: IntegrityError properly converted to user-friendly 400 error")
                else:
                    print("⚠️  WARNING: Got 400 but error format could be better")
                    print(f"   Error data: {response_data}")
            except:
                print("❌ Response is not valid JSON")
        else:
            print("❌ FAILED: Should have returned 400 for duplicate phone")
    else:
        print("❌ First registration failed, cannot continue test")
        print(f"   Error: {response1.text}")

if __name__ == "__main__":
    test_production_scenario()
