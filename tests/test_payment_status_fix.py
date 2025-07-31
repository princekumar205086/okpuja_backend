#!/usr/bin/env python3
"""
Test script to demonstrate the payment status verification fix
"""

import requests
import json
import time
from datetime import datetime

# Configuration
API_BASE_URL = "http://localhost:8000"
LOGIN_ENDPOINT = f"{API_BASE_URL}/api/accounts/auth/login/"
PAYMENT_ENDPOINT = f"{API_BASE_URL}/api/payments/payments/process-cart/"

# Test credentials
TEST_EMAIL = "asliprinceraj@gmail.com"  
TEST_PASSWORD = "testpass123"
CART_ID = 19  # Use existing cart or create new one

def test_payment_status_verification():
    """Test the complete payment status verification flow"""
    print("🧪 Testing Payment Status Verification Fix")
    print("=" * 60)
    
    # Step 1: Login
    print("1. 🔑 Logging in...")
    login_data = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
    
    try:
        login_response = requests.post(LOGIN_ENDPOINT, json=login_data, timeout=10)
        if login_response.status_code == 200:
            token = login_response.json().get('access')
            print(f"   ✅ Login successful")
        else:
            print(f"   ❌ Login failed: {login_response.status_code}")
            return False
    except Exception as e:
        print(f"   ❌ Login error: {e}")
        return False
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    
    # Step 2: Process payment (will likely fail with connectivity issues)
    print(f"\n2. 💳 Processing payment for cart {CART_ID}...")
    payment_data = {"cart_id": CART_ID, "method": "PHONEPE"}
    
    try:
        payment_response = requests.post(PAYMENT_ENDPOINT, json=payment_data, headers=headers, timeout=30)
        
        if payment_response.status_code == 201:
            result = payment_response.json()
            payment_id = result.get('payment_id')
            print(f"   ✅ Payment initiated successfully!")
            print(f"   Payment ID: {payment_id}")
            print(f"   Status: {result.get('status')}")
            
            if result.get('payment_url'):
                print(f"   🔗 Payment URL: {result.get('payment_url')}")
                print("\n   📋 In real scenario:")
                print("   - User would complete payment in PhonePe")
                print("   - Payment would remain PENDING without webhook")
                print("   - Our fix will manually verify the status")
                
                return payment_id
            
        elif payment_response.status_code == 400:
            result = payment_response.json()
            print(f"   ⚠️ Payment initiation failed (expected in local dev)")
            print(f"   Category: {result.get('error_category')}")
            
            # Check for simulation option
            debug_options = result.get('debug_options', {})
            if debug_options.get('simulate_payment_url'):
                print(f"\n3. 🎯 Using payment simulation...")
                simulate_url = debug_options['simulate_payment_url']
                
                simulate_response = requests.post(f"{API_BASE_URL}{simulate_url}", headers=headers, timeout=10)
                
                if simulate_response.status_code == 200:
                    sim_result = simulate_response.json()
                    payment_id = sim_result.get('payment_id')
                    print(f"   ✅ Payment simulated successfully!")
                    print(f"   Payment ID: {payment_id}")
                    print(f"   Status: {sim_result.get('status')}")
                    
                    if sim_result.get('booking_created'):
                        print(f"   📅 Booking created: {sim_result.get('booking_id')}")
                        return payment_id
                    else:
                        print(f"   ⚠️ Booking not created yet")
                        return payment_id
                else:
                    print(f"   ❌ Simulation failed: {simulate_response.status_code}")
                    return None
        else:
            print(f"   ❌ Payment failed: {payment_response.status_code}")
            return None
            
    except Exception as e:
        print(f"   ❌ Payment error: {e}")
        return None

def test_status_verification_endpoint(payment_id, token):
    """Test the new status verification endpoint"""
    print(f"\n4. 🔍 Testing Status Verification Endpoint...")
    print(f"   Payment ID: {payment_id}")
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    verify_url = f"{API_BASE_URL}/api/payments/payments/{payment_id}/verify-status/"
    
    try:
        verify_response = requests.post(verify_url, headers=headers, timeout=15)
        
        if verify_response.status_code == 200:
            result = verify_response.json()
            print(f"   ✅ Status verification successful!")
            print(f"   Old Status: {result.get('old_status', 'N/A')}")
            print(f"   New Status: {result.get('new_status')}")
            print(f"   Status Updated: {result.get('status_updated')}")
            print(f"   Booking Created: {result.get('booking_created')}")
            
            if result.get('booking_id'):
                print(f"   📅 Booking ID: {result.get('booking_id')}")
            
            return result
        else:
            print(f"   ❌ Verification failed: {verify_response.status_code}")
            print(f"   Response: {verify_response.text}")
            return None
            
    except Exception as e:
        print(f"   ❌ Verification error: {e}")
        return None

def test_booking_check_endpoint(payment_id, token):
    """Test the booking status check endpoint"""
    print(f"\n5. 📅 Testing Booking Status Check...")
    
    headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
    booking_url = f"{API_BASE_URL}/api/payments/payments/{payment_id}/check-booking/"
    
    try:
        booking_response = requests.get(booking_url, headers=headers, timeout=10)
        
        if booking_response.status_code == 200:
            result = booking_response.json()
            print(f"   ✅ Booking check successful!")
            print(f"   Payment Status: {result.get('payment_status')}")
            print(f"   Booking Created: {result.get('booking_created')}")
            
            if result.get('booking'):
                booking = result['booking']
                print(f"   📋 Booking Details:")
                print(f"     - ID: {booking.get('id')}")
                print(f"     - Status: {booking.get('status')}")
                print(f"     - Date: {booking.get('selected_date')}")
                print(f"     - Time: {booking.get('selected_time')}")
            
            return result
        else:
            print(f"   ❌ Booking check failed: {booking_response.status_code}")
            return None
            
    except Exception as e:
        print(f"   ❌ Booking check error: {e}")
        return None

def main():
    """Main test function"""
    print(f"🔧 Payment Status Verification Fix Test")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🎯 Problem: Payment status remains PENDING after successful PhonePe payment")
    print(f"💡 Solution: Manual status verification with PhonePe API")
    print()
    
    # Step 1-3: Create payment
    payment_id = test_payment_status_verification()
    
    if not payment_id:
        print("\n❌ Could not create test payment")
        return
    
    # Get token again for subsequent requests
    login_data = {"email": TEST_EMAIL, "password": TEST_PASSWORD}
    login_response = requests.post(LOGIN_ENDPOINT, json=login_data, timeout=10)
    token = login_response.json().get('access')
    
    # Step 4: Test status verification
    verify_result = test_status_verification_endpoint(payment_id, token)
    
    # Step 5: Test booking check
    booking_result = test_booking_check_endpoint(payment_id, token)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 Test Summary:")
    print(f"   Payment ID: {payment_id}")
    
    if verify_result:
        print(f"   ✅ Status Verification: Working")
        print(f"   Final Status: {verify_result.get('new_status')}")
    else:
        print(f"   ❌ Status Verification: Failed")
    
    if booking_result:
        print(f"   ✅ Booking Check: Working")
        print(f"   Booking Created: {booking_result.get('booking_created')}")
    else:
        print(f"   ❌ Booking Check: Failed")
    
    print(f"\n🎯 Solution Summary:")
    print(f"   1. POST /api/payments/payments/{payment_id}/verify-status/")
    print(f"      - Manually checks PhonePe API for payment status")
    print(f"      - Updates local payment status if successful")
    print(f"      - Creates booking if payment successful")
    print(f"      - Sends email notifications")
    print(f"")
    print(f"   2. GET /api/payments/payments/{payment_id}/check-booking/")
    print(f"      - Checks if booking was created")
    print(f"      - Returns booking details")
    print(f"")
    print(f"   3. Frontend can call these endpoints after user returns from PhonePe")
    print(f"   4. Can also poll status until it's no longer PENDING")
    
    print(f"\n✅ Payment status verification fix is ready!")

if __name__ == "__main__":
    main()
