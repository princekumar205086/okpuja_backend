#!/usr/bin/env python
"""
Test booking retrieval by cart ID
"""

import requests
import json

# Test data
BASE_URL = "http://127.0.0.1:8000/api"
CART_ID = "44ae14e5-bf66-4ecc-8530-b2ad4ef064e7"  # From your Swagger test

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
        
        # Now test booking retrieval by cart ID
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        print(f"\n📋 Getting booking for cart: {CART_ID}")
        booking_response = requests.get(f"{BASE_URL}/booking/bookings/by-cart/{CART_ID}/", headers=headers)
        
        print(f"📊 Booking Response Status: {booking_response.status_code}")
        booking_result = booking_response.json()
        
        if booking_response.status_code == 200:
            print("✅ Booking found!")
            print(f"🏷️  Booking ID: {booking_result.get('book_id')}")
            print(f"📅 Selected Date: {booking_result.get('selected_date')}")
            print(f"🕐 Selected Time: {booking_result.get('selected_time')}")
            print(f"📊 Status: {booking_result.get('status')}")
        elif booking_response.status_code == 404:
            print(f"🔍 No booking found yet: {booking_result.get('message')}")
            print(f"💳 Payment Status: {booking_result.get('payment_status')}")
        else:
            print(f"❌ Booking retrieval failed: {booking_result}")
            
    else:
        print(f"❌ Login failed: {login_result}")
        
except Exception as e:
    print(f"❌ Error: {e}")
