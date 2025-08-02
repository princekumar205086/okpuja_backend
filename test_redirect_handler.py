#!/usr/bin/env python
"""
Test the redirect handler directly
"""

import requests
import json

# Test data
BASE_URL = "http://127.0.0.1:8000/api"

# First login to get token
login_data = {
    "email": "asliprinceraj@gmail.com", 
    "password": "testpass123"
}

print("🔐 Logging in...")
try:
    login_response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
    login_result = login_response.json()
    
    if login_response.status_code == 200:
        access_token = login_result.get('access')
        print(f"✅ Login successful")
        
        # Now test the redirect handler directly 
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        print(f"\n🔄 Testing redirect handler...")
        # Simulate what PhonePe might send (usually no params)
        redirect_response = requests.get(f"{BASE_URL}/payments/redirect/simple/", headers=headers, allow_redirects=False)
        
        print(f"📊 Redirect Response Status: {redirect_response.status_code}")
        
        if redirect_response.status_code == 302:
            redirect_location = redirect_response.headers.get('Location', 'No location header')
            print(f"✅ Redirect successful!")
            print(f"🔗 Redirect URL: {redirect_location}")
            
            # Parse the redirect URL to see what parameters we get
            if 'cart_id=' in redirect_location:
                print("✅ cart_id found in redirect URL")
            if 'order_id=' in redirect_location:
                print("✅ order_id found in redirect URL")
            if 'error=' in redirect_location:
                print("❌ Error parameter found in redirect URL")
        else:
            print(f"❌ Unexpected redirect status: {redirect_response.status_code}")
            print(f"Response: {redirect_response.text}")
            
    else:
        print(f"❌ Login failed: {login_result}")
        
except Exception as e:
    print(f"❌ Error: {e}")
