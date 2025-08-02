#!/usr/bin/env python
"""
Test the booking API response format
"""

import requests
import json

# Test data
BASE_URL = "http://127.0.0.1:8000/api"
CART_ID = "6e86ecd3-20f5-4606-b260-16938f480a6e"  # Latest cart

# Login
login_data = {"email": "asliprinceraj@gmail.com", "password": "testpass123"}

try:
    login_response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
    if login_response.status_code == 200:
        access_token = login_response.json().get('access')
        headers = {'Authorization': f'Bearer {access_token}'}
        
        print(f"🔍 Testing booking API for cart: {CART_ID}")
        
        # Get booking by cart ID
        booking_response = requests.get(f"{BASE_URL}/booking/bookings/by-cart/{CART_ID}/", headers=headers)
        
        print(f"📊 Response Status: {booking_response.status_code}")
        print(f"📋 Response Headers: {dict(booking_response.headers)}")
        
        response_json = booking_response.json()
        print(f"📄 Full Response:")
        print(json.dumps(response_json, indent=2))
        
        if booking_response.status_code == 200:
            # Extract booking data
            if 'data' in response_json:
                booking_data = response_json['data']
                print(f"\n✅ Booking Data Found:")
                print(f"   Booking ID: {booking_data.get('book_id')}")
                print(f"   Status: {booking_data.get('status')}")
                print(f"   Date: {booking_data.get('selected_date')}")
                print(f"   Time: {booking_data.get('selected_time')}")
            else:
                print(f"❌ No 'data' field in response")
        
    else:
        print(f"❌ Login failed: {login_response.json()}")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
