#!/usr/bin/env python
"""
Check the current payment status and attempt booking creation
"""

import requests
import json

# Test data
BASE_URL = "http://127.0.0.1:8000/api"
CART_ID = "44ae14e5-bf66-4ecc-8530-b2ad4ef064e7"

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
        
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Check payment status for this cart
        print(f"\n💳 Checking payment status for cart: {CART_ID}")
        payment_status_response = requests.get(f"{BASE_URL}/payments/cart/status/{CART_ID}/", headers=headers)
        
        print(f"📊 Payment Status Response: {payment_status_response.status_code}")
        if payment_status_response.status_code == 200:
            payment_result = payment_status_response.json()
            print(f"💰 Payment Status: {payment_result.get('status')}")
            print(f"🏷️  Order ID: {payment_result.get('merchant_order_id')}")
            print(f"💵 Amount: {payment_result.get('amount')}")
        else:
            payment_result = payment_status_response.json()
            print(f"❌ Payment status check failed: {payment_result}")
        
        # Now try to get booking by cart ID
        print(f"\n📋 Attempting to get booking for cart: {CART_ID}")
        booking_response = requests.get(f"{BASE_URL}/booking/bookings/by-cart/{CART_ID}/", headers=headers)
        
        print(f"📊 Booking Response Status: {booking_response.status_code}")
        booking_result = booking_response.json()
        
        if booking_response.status_code == 200:
            print("✅ Booking found!")
            print(f"🏷️  Booking ID: {booking_result.get('book_id')}")
            print(f"📊 Status: {booking_result.get('status')}")
        elif booking_response.status_code == 404:
            print(f"🔍 No booking found: {booking_result.get('message')}")
            print(f"💳 Payment Status in booking check: {booking_result.get('payment_status')}")
        else:
            print(f"❌ Booking retrieval failed: {booking_result}")
            
    else:
        print(f"❌ Login failed: {login_result}")
        
except Exception as e:
    print(f"❌ Error: {e}")
