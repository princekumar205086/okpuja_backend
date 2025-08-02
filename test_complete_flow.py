#!/usr/bin/env python
"""
Test complete payment flow with new cart (puja id 13, package id 11)
"""

import requests
import json
import time

# Test data
BASE_URL = "http://127.0.0.1:8000/api"

# Login credentials
login_data = {
    "email": "asliprinceraj@gmail.com", 
    "password": "testpass123"
}

# Cart data - as requested
cart_data = {
    "service_type": "PUJA",
    "puja_service": 13,
    "package_id": 11,
    "selected_date": "2025-08-19",
    "selected_time": "10:00"
}

print("🚀 Starting complete payment flow test...")
print("=" * 50)

try:
    # Step 1: Login
    print("🔐 Step 1: Logging in...")
    login_response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
    login_result = login_response.json()
    
    if login_response.status_code != 200:
        print(f"❌ Login failed: {login_result}")
        exit(1)
        
    access_token = login_result.get('access')
    user_id = login_result.get('id')
    print(f"✅ Login successful - User ID: {user_id}")
    
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    # Step 2: Create Cart
    print(f"\n🛒 Step 2: Creating cart...")
    print(f"   Puja Service: {cart_data['puja_service']}")
    print(f"   Package ID: {cart_data['package_id']}")
    print(f"   Date: {cart_data['selected_date']}")
    print(f"   Time: {cart_data['selected_time']}")
    
    cart_response = requests.post(f"{BASE_URL}/cart/carts/", json=cart_data, headers=headers)
    
    if cart_response.status_code != 201:
        print(f"❌ Cart creation failed: {cart_response.json()}")
        exit(1)
        
    cart_result = cart_response.json()
    cart_id = cart_result.get('cart_id')
    cart_price = cart_result.get('total_price')
    print(f"✅ Cart created successfully!")
    print(f"   Cart ID: {cart_id}")
    print(f"   Total Price: ₹{cart_price}")
    
    # Step 3: Create Payment
    print(f"\n💳 Step 3: Creating payment...")
    payment_data = {"cart_id": cart_id}
    
    payment_response = requests.post(f"{BASE_URL}/payments/cart/", json=payment_data, headers=headers)
    
    if payment_response.status_code not in [200, 201]:
        print(f"❌ Payment creation failed: {payment_response.json()}")
        exit(1)
        
    payment_result = payment_response.json()
    order_id = payment_result.get('data', {}).get('payment_order', {}).get('merchant_order_id')
    payment_amount = payment_result.get('data', {}).get('payment_order', {}).get('amount_in_rupees')
    payment_url = payment_result.get('data', {}).get('payment_order', {}).get('phonepe_payment_url')
    
    print(f"✅ Payment created successfully!")
    print(f"   Order ID: {order_id}")
    print(f"   Amount: ₹{payment_amount}")
    print(f"   Payment URL: {payment_url[:80]}...")
    
    # Step 4: Simulate Payment Success (for testing)
    print(f"\n🧪 Step 4: Simulating successful payment...")
    print("   (In production, user would complete payment via PhonePe)")
    
    # Direct database update to simulate successful payment
    import os
    import sys
    import django
    
    sys.path.append('.')
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
    django.setup()
    
    from payments.models import PaymentOrder
    from payments.services import WebhookService
    
    payment_order = PaymentOrder.objects.get(merchant_order_id=order_id)
    payment_order.status = 'SUCCESS'
    payment_order.save()
    print(f"✅ Payment status updated to SUCCESS")
    
    # Step 5: Test Redirect Handler
    print(f"\n🔄 Step 5: Testing redirect handler...")
    redirect_response = requests.get(f"{BASE_URL}/payments/redirect/simple/", headers=headers, allow_redirects=False)
    
    if redirect_response.status_code == 302:
        redirect_url = redirect_response.headers.get('Location', '')
        print(f"✅ Redirect successful!")
        print(f"   Redirect URL: {redirect_url}")
        
        # Check if cart_id is in the redirect URL
        if cart_id in redirect_url:
            print(f"✅ Cart ID found in redirect URL")
        else:
            print(f"❌ Cart ID not found in redirect URL")
    else:
        print(f"❌ Redirect failed: {redirect_response.status_code}")
    
    # Step 6: Check Booking Creation
    print(f"\n📋 Step 6: Checking booking creation...")
    booking_response = requests.get(f"{BASE_URL}/booking/bookings/by-cart/{cart_id}/", headers=headers)
    
    if booking_response.status_code == 200:
        booking_result = booking_response.json()
        booking_id = booking_result.get('book_id')
        booking_status = booking_result.get('status')
        print(f"✅ Booking found!")
        print(f"   Booking ID: {booking_id}")
        print(f"   Status: {booking_status}")
        print(f"   Date: {booking_result.get('selected_date')}")
        print(f"   Time: {booking_result.get('selected_time')}")
    else:
        booking_result = booking_response.json()
        print(f"🔍 Booking status: {booking_result.get('message')}")
        print(f"   Payment Status: {booking_result.get('payment_status')}")
    
    # Step 7: Check Cart Status
    print(f"\n🛒 Step 7: Checking cart status after booking...")
    cart_status_response = requests.get(f"{BASE_URL}/cart/carts/active/", headers=headers)
    
    if cart_status_response.status_code == 200:
        active_cart = cart_status_response.json()
        if active_cart.get('cart_id') == cart_id:
            print(f"📋 Cart status: {active_cart.get('status')}")
        else:
            print(f"✅ Cart converted - no longer active")
    
    print(f"\n🎉 Test completed successfully!")
    print("=" * 50)
    
except Exception as e:
    print(f"❌ Error during test: {e}")
    import traceback
    traceback.print_exc()
