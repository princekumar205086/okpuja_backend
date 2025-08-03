#!/usr/bin/env python
"""
Test the complete flow with the latest cart
"""

import requests
import json
import os
import sys
import django

# Setup Django
sys.path.append('.')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from payments.models import PaymentOrder
from payments.services import WebhookService

BASE_URL = "http://127.0.0.1:8000/api"
LATEST_CART_ID = "3aef7e52-1f83-4067-8bdd-e6f00f6ab5b9"

print("🧪 Testing Complete Flow with Latest Cart")
print("=" * 50)
print(f"Cart ID: {LATEST_CART_ID}")

try:
    # Step 1: Login
    login_data = {"email": "asliprinceraj@gmail.com", "password": "testpass123"}
    login_response = requests.post(f"{BASE_URL}/auth/login/", json=login_data)
    
    if login_response.status_code != 200:
        print(f"❌ Login failed")
        exit(1)
        
    access_token = login_response.json().get('access')
    headers = {'Authorization': f'Bearer {access_token}', 'Content-Type': 'application/json'}
    print("✅ Logged in successfully")
    
    # Step 2: Get payment for latest cart
    payment = PaymentOrder.objects.filter(cart_id=LATEST_CART_ID).first()
    if not payment:
        print(f"❌ No payment found for cart {LATEST_CART_ID}")
        exit(1)
        
    print(f"💳 Found payment: {payment.merchant_order_id}")
    print(f"   Current status: {payment.status}")
    
    # Step 3: Simulate successful payment
    print(f"\n🎯 Simulating successful payment...")
    payment.status = 'SUCCESS'
    payment.save()
    print(f"✅ Payment status updated to SUCCESS")
    
    # Step 4: Test redirect handler with various scenarios
    print(f"\n🔄 Testing redirect handler scenarios...")
    
    # Test 1: With authenticated user
    print(f"  Test 1: Authenticated user redirect...")
    redirect_response = requests.get(f"{BASE_URL}/payments/redirect/simple/", headers=headers, allow_redirects=False)
    
    if redirect_response.status_code == 302:
        redirect_url = redirect_response.headers.get('Location', '')
        print(f"    ✅ Redirect URL: {redirect_url}")
        
        if LATEST_CART_ID in redirect_url:
            print(f"    ✅ Correct cart ID found in URL")
        else:
            print(f"    ❌ Wrong cart ID in URL")
    else:
        print(f"    ❌ Redirect failed: {redirect_response.status_code}")
    
    # Test 2: With order ID parameter (simulating PhonePe callback)
    print(f"\n  Test 2: PhonePe callback with order ID...")
    redirect_url_with_params = f"{BASE_URL}/payments/redirect/simple/?merchantOrderId={payment.merchant_order_id}"
    redirect_response2 = requests.get(redirect_url_with_params, allow_redirects=False)
    
    if redirect_response2.status_code == 302:
        redirect_url2 = redirect_response2.headers.get('Location', '')
        print(f"    ✅ Redirect URL: {redirect_url2}")
        
        if LATEST_CART_ID in redirect_url2:
            print(f"    ✅ Correct cart ID found in URL")
        else:
            print(f"    ❌ Wrong cart ID in URL")
    else:
        print(f"    ❌ Redirect failed: {redirect_response2.status_code}")
    
    # Step 5: Check booking creation
    print(f"\n📋 Checking booking for cart {LATEST_CART_ID}...")
    booking_response = requests.get(f"{BASE_URL}/booking/bookings/by-cart/{LATEST_CART_ID}/", headers=headers)
    
    print(f"   Response status: {booking_response.status_code}")
    booking_result = booking_response.json()
    
    if booking_response.status_code == 200:
        booking_data = booking_result.get('data', {})
        print(f"✅ Booking found!")
        print(f"   Booking ID: {booking_data.get('book_id')}")
        print(f"   Status: {booking_data.get('status')}")
        print(f"   Cart Status: {booking_data.get('cart', {}).get('status')}")
    else:
        print(f"🔍 Booking status: {booking_result.get('message')}")
        
    # Step 6: Test webhook processing
    print(f"\n🔔 Testing webhook processing...")
    webhook_data = {
        "merchantOrderId": payment.merchant_order_id,
        "state": "COMPLETED",
        "eventType": "PAYMENT_SUCCESS",
        "transactionId": f"T{payment.merchant_order_id[-8:]}",
        "responseCode": "SUCCESS"
    }
    
    webhook_service = WebhookService()
    webhook_result = webhook_service.process_payment_webhook(webhook_data)
    
    if webhook_result.get('success'):
        print(f"✅ Webhook processed successfully")
    else:
        print(f"❌ Webhook processing failed: {webhook_result.get('error')}")
    
    print(f"\n🎉 Test completed!")
    print("=" * 50)
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
