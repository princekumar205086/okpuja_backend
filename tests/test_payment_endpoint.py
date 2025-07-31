#!/usr/bin/env python3
"""
Test script for payment endpoint with cart ID 19
Tests the PhonePe payment integration with the updated V2 API
"""

import requests
import json
import os
from datetime import datetime

# Configuration
API_BASE_URL = "https://api.okpuja.com"
LOGIN_ENDPOINT = f"{API_BASE_URL}/api/accounts/auth/login/"
PAYMENT_ENDPOINT = f"{API_BASE_URL}/api/payments/payments/process-cart/"
DEBUG_ENDPOINT = f"{API_BASE_URL}/api/payments/payments/debug-connectivity/"

# Test credentials
TEST_EMAIL = "asliprinceraj@gmail.com"
TEST_PASSWORD = "Testpass@123"
CART_ID = 19

def test_payment_endpoint():
    """Test the payment endpoint with proper authentication and error handling"""
    print("🚀 Testing Payment Endpoint")
    print("=" * 50)
    
    # Step 1: Login to get authentication token
    print("1. 🔑 Authenticating user...")
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        login_response = requests.post(LOGIN_ENDPOINT, json=login_data, timeout=30)
        print(f"   Status Code: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            access_token = login_result.get('access')
            
            if not access_token:
                print("   ❌ No access token in response")
                print(f"   Response: {login_result}")
                return False
                
            print("   ✅ Login successful")
            print(f"   Token: {access_token[:20]}...")
            
        else:
            print(f"   ❌ Login failed: {login_response.status_code}")
            print(f"   Response: {login_response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Login request failed: {str(e)}")
        return False
    
    # Step 2: Test debug connectivity first
    print("\n2. 🔍 Testing PhonePe connectivity...")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        debug_response = requests.get(DEBUG_ENDPOINT, headers=headers, timeout=30)
        print(f"   Status Code: {debug_response.status_code}")
        
        if debug_response.status_code == 200:
            debug_result = debug_response.json()
            print("   ✅ Debug connectivity successful")
            
            # Check network connectivity
            network_tests = debug_result.get('network_tests', {})
            phonepe_reachable = any(
                test.get('reachable', False) 
                for url, test in network_tests.items() 
                if 'phonepe.com' in url
            )
            
            if phonepe_reachable:
                print("   ✅ PhonePe API is reachable")
            else:
                print("   ⚠️ PhonePe API may not be reachable")
                
            # Check gateway initialization
            if debug_result.get('api_test', {}).get('gateway_init') == 'SUCCESS':
                print("   ✅ PhonePe Gateway initialized successfully")
            else:
                print("   ⚠️ PhonePe Gateway initialization issues")
                
        else:
            print(f"   ⚠️ Debug endpoint issue: {debug_response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ⚠️ Debug request failed: {str(e)}")
    
    # Step 3: Process cart payment
    print(f"\n3. 💳 Processing payment for cart ID {CART_ID}...")
    payment_data = {
        "cart_id": CART_ID,
        "method": "PHONEPE"
    }
    
    try:
        payment_response = requests.post(
            PAYMENT_ENDPOINT, 
            json=payment_data, 
            headers=headers, 
            timeout=60
        )
        
        print(f"   Status Code: {payment_response.status_code}")
        
        if payment_response.status_code == 201:
            # Success response
            result = payment_response.json()
            print("   ✅ Payment processing successful!")
            print(f"   Payment ID: {result.get('payment_id')}")
            print(f"   Transaction ID: {result.get('transaction_id')}")
            print(f"   Amount: ₹{result.get('amount')}")
            print(f"   Status: {result.get('status')}")
            
            payment_url = result.get('payment_url') or result.get('checkout_url')
            if payment_url:
                print(f"   🔗 Payment URL: {payment_url}")
                print("\n   📋 Test Steps:")
                print("   1. Copy the payment URL above")
                print("   2. Open it in your browser")
                print("   3. Complete the test payment using PhonePe Test App")
                print("   4. Check webhook status on your server")
            else:
                print("   ⚠️ No payment URL received")
                
            return True
            
        elif payment_response.status_code == 400:
            # Client error - detailed error response
            result = payment_response.json()
            error_category = result.get('error_category', 'UNKNOWN')
            user_message = result.get('user_message', 'Payment failed')
            
            print(f"   ❌ Payment failed: {error_category}")
            print(f"   Message: {user_message}")
            
            # Check for debug options
            debug_options = result.get('debug_options', {})
            if debug_options:
                print("\n   🔧 Debug Options Available:")
                simulate_url = debug_options.get('simulate_payment_url')
                if simulate_url:
                    print(f"   Simulate Success: {API_BASE_URL}{simulate_url}")
                    
                    # Offer to simulate payment success
                    print("\n   🎯 Testing payment simulation...")
                    simulate_response = requests.post(
                        f"{API_BASE_URL}{simulate_url}",
                        headers=headers,
                        timeout=30
                    )
                    
                    if simulate_response.status_code == 200:
                        sim_result = simulate_response.json()
                        print("   ✅ Payment simulation successful!")
                        print(f"   Payment ID: {sim_result.get('payment_id')}")
                        print(f"   Status: {sim_result.get('status')}")
                        if sim_result.get('booking_created'):
                            print(f"   Booking Created: {sim_result.get('booking_id')}")
                        return True
                    else:
                        print(f"   ❌ Payment simulation failed: {simulate_response.status_code}")
                        print(f"   Response: {simulate_response.text}")
            
            return False
            
        else:
            # Other error
            print(f"   ❌ Unexpected error: {payment_response.status_code}")
            try:
                error_result = payment_response.json()
                print(f"   Error details: {error_result}")
            except:
                print(f"   Raw response: {payment_response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("   ❌ Payment request timed out")
        print("   This might indicate PhonePe API connectivity issues")
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Payment request failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print(f"🧪 Payment Endpoint Test")
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 API Base URL: {API_BASE_URL}")
    print(f"👤 Test User: {TEST_EMAIL}")
    print(f"🛒 Cart ID: {CART_ID}")
    print()
    
    success = test_payment_endpoint()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ Test completed successfully!")
        print("\n📋 Next Steps:")
        print("1. If you received a payment URL, test the actual payment flow")
        print("2. Check webhook logs for payment status updates")
        print("3. Verify booking creation after successful payment")
    else:
        print("❌ Test failed!")
        print("\n🔧 Troubleshooting:")
        print("1. Check server logs for detailed error information")
        print("2. Verify PhonePe API credentials in .env file")
        print("3. Test network connectivity to PhonePe servers")
        print("4. Check if cart ID 19 exists and is active")

if __name__ == "__main__":
    main()
