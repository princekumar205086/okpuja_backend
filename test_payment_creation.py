#!/usr/bin/env python
"""
Test payment creation for the cart we just created
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
        print(f"📧 User ID: {login_result.get('id')}")
        
        # Now test payment creation
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        payment_data = {
            "cart_id": CART_ID
        }
        
        print(f"\n💳 Creating payment for cart: {CART_ID}")
        payment_response = requests.post(f"{BASE_URL}/payments/cart/", json=payment_data, headers=headers)
        
        print(f"📊 Payment Response Status: {payment_response.status_code}")
        
        if payment_response.status_code == 201:
            payment_result = payment_response.json()
            print("✅ Payment created successfully!")
            print(f"🏷️  Order ID: {payment_result.get('data', {}).get('payment_order', {}).get('merchant_order_id')}")
            print(f"💰 Amount: ₹{payment_result.get('data', {}).get('payment_order', {}).get('amount')}")
            print(f"🔗 Payment URL: {payment_result.get('data', {}).get('payment_order', {}).get('payment_url')[:100]}...")
        else:
            payment_result = payment_response.json()
            print(f"❌ Payment creation failed: {payment_result}")
            
    else:
        print(f"❌ Login failed: {login_result}")
        
except Exception as e:
    print(f"❌ Error: {e}")
