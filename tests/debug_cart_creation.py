#!/usr/bin/env python
"""
Debug Cart Creation API
"""

import os
import sys
import django
import requests
import json

# Add the project root to Python path
sys.path.append('.')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

# Test credentials
TEST_EMAIL = "asliprinceraj@gmail.com"
TEST_PASSWORD = "Testpass@123"
PUJA_SERVICE_ID = 109
PACKAGE_ID = 309
ADDRESS_ID = 1

# Production API Base URL
BASE_URL = "https://api.okpuja.com/api"

def test_cart_creation():
    print("🔐 Authenticating...")
    
    # Login
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    session = requests.Session()
    response = session.post(f"{BASE_URL}/auth/login/", json=login_data)
    
    if response.status_code != 200:
        print(f"❌ Login failed: {response.status_code}")
        return
    
    result = response.json()
    access_token = result.get('access')
    
    session.headers.update({
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    })
    
    print("✅ Login successful")
    
    # Test different cart creation payloads
    cart_payloads = [
        {
            "name": "Direct field names",
            "data": {
                "puja_service": PUJA_SERVICE_ID,
                "package": PACKAGE_ID,
                "selected_date": "2025-08-15",
                "selected_time": "10:00 AM",
                "address": ADDRESS_ID
            }
        },
        {
            "name": "With _id suffix",
            "data": {
                "puja_service_id": PUJA_SERVICE_ID,
                "package_id": PACKAGE_ID,
                "selected_date": "2025-08-15",
                "selected_time": "10:00 AM",
                "address_id": ADDRESS_ID
            }
        },
        {
            "name": "Minimal payload",
            "data": {
                "puja_service": PUJA_SERVICE_ID,
                "selected_date": "2025-08-15",
                "selected_time": "10:00 AM"
            }
        }
    ]
    
    for test_case in cart_payloads:
        print(f"\n🧪 Testing: {test_case['name']}")
        print(f"Payload: {json.dumps(test_case['data'], indent=2)}")
        
        response = session.post(f"{BASE_URL}/cart/carts/", json=test_case['data'])
        
        print(f"Status: {response.status_code}")
        
        try:
            result = response.json()
            print(f"Response: {json.dumps(result, indent=2)}")
        except:
            print(f"Raw response: {response.text[:500]}...")
        
        if response.status_code == 201:
            print("✅ Cart creation successful!")
            break
        else:
            print("❌ Cart creation failed")

if __name__ == "__main__":
    test_cart_creation()
