#!/usr/bin/env python
"""
Test Script for Cart to Booking Flow
Tests the complete flow: Cart → Payment → Booking → Email
"""

import os
import sys
import django
import requests
import json
from datetime import datetime, timedelta

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

BASE_URL = 'http://127.0.0.1:8001/api'
TEST_USER = {
    'email': 'asliprinceraj@gmail.com',
    'password': 'testpass123'
}

def get_access_token():
    """Login and get access token"""
    response = requests.post(f'{BASE_URL}/auth/login/', {
        'email': TEST_USER['email'],
        'password': TEST_USER['password']
    })
    
    if response.status_code == 200:
        return response.json()['access']
    else:
        print(f"Login failed: {response.text}")
        return None

def test_cart_to_booking_flow():
    """Test the complete flow"""
    print("🧪 Testing Cart to Booking Flow...")
    
    # Step 1: Get access token
    print("1. Getting access token...")
    token = get_access_token()
    if not token:
        print("❌ Failed to get access token")
        return False
    
    headers = {'Authorization': f'Bearer {token}'}
    print("✅ Got access token")
    
    # Step 2: Create cart with puja service 8 and package 2
    print("2. Creating cart...")
    cart_data = {
        'service_type': 'PUJA',
        'puja_service': 8,
        'package_id': 2,
        'selected_date': (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d'),
        'selected_time': '10:00 AM'
    }
    
    response = requests.post(f'{BASE_URL}/cart/carts/', 
                           json=cart_data, 
                           headers=headers)
    
    if response.status_code != 201:
        print(f"❌ Cart creation failed: {response.text}")
        return False
    
    cart = response.json()
    cart_id = cart['id']
    print(f"✅ Cart created with ID: {cart_id}")
    print(f"   Service: {cart.get('puja_service', {}).get('name', 'Unknown')}")
    print(f"   Total: ₹{cart.get('total_price', 0)}")
    
    # Step 3: Process payment
    print("3. Processing payment...")
    payment_data = {
        'cart_id': cart_id,
        'method': 'PHONEPE'
    }
    
    response = requests.post(f'{BASE_URL}/payments/payments/process-cart/', 
                           json=payment_data, 
                           headers=headers)
    
    if response.status_code != 201:
        print(f"❌ Payment initiation failed: {response.text}")
        return False
    
    payment_response = response.json()
    payment_id = payment_response['payment_id']
    print(f"✅ Payment initiated with ID: {payment_id}")
    print(f"   Transaction ID: {payment_response.get('transaction_id')}")
    
    # Step 4: Simulate payment success
    print("4. Simulating payment success...")
    response = requests.post(f'{BASE_URL}/payments/payments/{payment_id}/simulate-success/', 
                           headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Payment simulation failed: {response.text}")
        return False
    
    simulation_result = response.json()
    print(f"✅ Payment simulation successful")
    print(f"   Booking created: {simulation_result.get('booking_created')}")
    print(f"   Booking ID: {simulation_result.get('booking_id')}")
    
    # Step 5: Verify booking exists
    print("5. Verifying booking...")
    response = requests.get(f'{BASE_URL}/booking/bookings/', headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch bookings: {response.text}")
        return False
    
    bookings = response.json()['results'] if 'results' in response.json() else response.json()
    
    if not bookings:
        print("❌ No bookings found")
        return False
    
    latest_booking = bookings[0]
    print(f"✅ Booking verified")
    print(f"   Booking ID: {latest_booking.get('book_id')}")
    print(f"   Status: {latest_booking.get('status')}")
    print(f"   Service: {latest_booking.get('cart', {}).get('puja_service', {}).get('name')}")
    
    # Step 6: Check payment has booking linked
    print("6. Verifying payment-booking link...")
    response = requests.get(f'{BASE_URL}/payments/payments/{payment_id}/', headers=headers)
    
    if response.status_code != 200:
        print(f"❌ Failed to fetch payment: {response.text}")
        return False
    
    payment_details = response.json()
    booking_info = payment_details.get('booking')
    if booking_info:
        print("✅ Payment successfully linked to booking")
        print(f"   Payment Status: {payment_details.get('status')}")
        if isinstance(booking_info, dict):
            print(f"   Linked Booking: {booking_info.get('book_id')}")
        else:
            print(f"   Linked Booking ID: {booking_info}")
    else:
        print("❌ Payment not linked to booking")
        return False
    
    print("\n🎉 Complete flow test successful!")
    print("📧 Check email for booking confirmation")
    return True

if __name__ == "__main__":
    test_cart_to_booking_flow()
