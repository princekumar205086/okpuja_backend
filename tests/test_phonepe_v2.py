#!/usr/bin/env python3
"""
Comprehensive test script for PhonePe V2 Standard Checkout API
Tests authentication, cart processing, and payment initiation
"""

import requests
import json
from datetime import datetime
import time

# Configuration
API_BASE_URL = "https://api.okpuja.com"
LOCAL_API_URL = "http://localhost:8000"  # Try local first
LOGIN_ENDPOINT = "/api/accounts/auth/login/"
PAYMENT_ENDPOINT = "/api/payments/payments/process-cart/"
DEBUG_ENDPOINT = "/api/payments/payments/debug-connectivity/"

# Test credentials
TEST_EMAIL = "asliprinceraj@gmail.com"
TEST_PASSWORD = "Testpass@123"
CART_ID = 19

def test_api_connectivity():
    """Test which API endpoint is available"""
    endpoints_to_test = [LOCAL_API_URL, API_BASE_URL]
    
    for base_url in endpoints_to_test:
        try:
            print(f"🔍 Testing connectivity to {base_url}...")
            response = requests.get(f"{base_url}/admin/", timeout=10)
            print(f"   ✅ {base_url} is reachable (Status: {response.status_code})")
            return base_url
        except requests.exceptions.RequestException as e:
            print(f"   ❌ {base_url} not reachable: {str(e)}")
            continue
    
    print("❌ No API endpoints are reachable")
    return None

def authenticate_user(api_base):
    """Authenticate user and return access token"""
    print("🔑 Authenticating user...")
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        login_response = requests.post(
            f"{api_base}{LOGIN_ENDPOINT}", 
            json=login_data, 
            timeout=30
        )
        
        print(f"   Status Code: {login_response.status_code}")
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            access_token = login_result.get('access')
            
            if access_token:
                print("   ✅ Authentication successful")
                print(f"   Token: {access_token[:20]}...")
                return access_token
            else:
                print("   ❌ No access token received")
                print(f"   Response: {login_result}")
                return None
        else:
            print(f"   ❌ Authentication failed: {login_response.status_code}")
            try:
                error_data = login_response.json()
                print(f"   Error: {error_data}")
            except:
                print(f"   Raw response: {login_response.text}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Authentication request failed: {str(e)}")
        return None

def test_phonepe_connectivity(api_base, access_token):
    """Test PhonePe API connectivity"""
    print("🔍 Testing PhonePe connectivity...")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        debug_response = requests.post(
            f"{api_base}{DEBUG_ENDPOINT}", 
            headers=headers, 
            json={"test_payment": True},
            timeout=30
        )
        
        print(f"   Status Code: {debug_response.status_code}")
        
        if debug_response.status_code == 200:
            debug_result = debug_response.json()
            print("   ✅ Debug connectivity successful")
            
            # Check network tests
            network_tests = debug_result.get('network_tests', {})
            phonepe_reachable = any(
                test.get('reachable', False) 
                for url, test in network_tests.items() 
                if 'phonepe.com' in url or 'preprod' in url
            )
            
            if phonepe_reachable:
                print("   ✅ PhonePe API endpoints are reachable")
            else:
                print("   ⚠️ PhonePe API endpoints may not be reachable")
                
            # Check gateway initialization
            gateway_init = debug_result.get('api_test', {}).get('gateway_init')
            if gateway_init == 'SUCCESS':
                print("   ✅ PhonePe Gateway V2 initialized successfully")
            else:
                print(f"   ⚠️ PhonePe Gateway initialization: {gateway_init}")
                
            # Check payment simulation if available
            payment_sim = debug_result.get('payment_simulation', {})
            if payment_sim.get('status') == 'SUCCESS':
                print("   ✅ Payment simulation successful")
                print(f"   Test payment URL: {payment_sim.get('payment_url', 'N/A')}")
            elif payment_sim.get('status') == 'FAILED':
                print(f"   ⚠️ Payment simulation failed: {payment_sim.get('error', 'Unknown error')}")
                
            return True
        else:
            print(f"   ⚠️ Debug endpoint returned: {debug_response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ⚠️ Debug connectivity test failed: {str(e)}")
        return False

def process_cart_payment(api_base, access_token):
    """Process cart payment using V2 API"""
    print(f"💳 Processing payment for cart ID {CART_ID}...")
    
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    payment_data = {
        "cart_id": CART_ID,
        "method": "PHONEPE"
    }
    
    try:
        payment_response = requests.post(
            f"{api_base}{PAYMENT_ENDPOINT}",
            json=payment_data,
            headers=headers,
            timeout=60
        )
        
        print(f"   Status Code: {payment_response.status_code}")
        
        if payment_response.status_code == 201:
            # Success
            result = payment_response.json()
            print("   ✅ Payment processing successful!")
            print(f"   Payment ID: {result.get('payment_id')}")
            print(f"   Transaction ID: {result.get('transaction_id')}")
            print(f"   Merchant Transaction ID: {result.get('merchant_transaction_id')}")
            print(f"   Amount: ₹{result.get('amount')}")
            print(f"   Status: {result.get('status')}")
            
            payment_url = result.get('payment_url') or result.get('checkout_url')
            if payment_url:
                print(f"   🔗 Payment URL: {payment_url}")
                print("\n   📋 Next Steps:")
                print("   1. Copy the payment URL above")
                print("   2. Open it in your browser")
                print("   3. Complete payment using PhonePe Test App")
                print("   4. Check webhook status on your server")
                
                # Save payment details for later reference
                payment_details = {
                    'payment_id': result.get('payment_id'),
                    'transaction_id': result.get('transaction_id'),
                    'merchant_transaction_id': result.get('merchant_transaction_id'),
                    'payment_url': payment_url,
                    'amount': result.get('amount'),
                    'timestamp': datetime.now().isoformat()
                }
                
                with open('payment_test_result.json', 'w') as f:
                    json.dump(payment_details, f, indent=2)
                
                print(f"   💾 Payment details saved to 'payment_test_result.json'")
                
            return result
            
        elif payment_response.status_code == 400:
            # Client error
            result = payment_response.json()
            error_category = result.get('error_category', 'UNKNOWN')
            user_message = result.get('user_message', 'Payment failed')
            
            print(f"   ❌ Payment failed: {error_category}")
            print(f"   Message: {user_message}")
            
            # Check for debug options (development mode)
            debug_options = result.get('debug_options', {})
            if debug_options:
                print("\n   🔧 Debug Options Available (Development Mode):")
                simulate_url = debug_options.get('simulate_payment_url')
                if simulate_url:
                    print(f"   Simulate Success URL: {api_base}{simulate_url}")
                    
                    # Offer to simulate payment success for testing
                    user_input = input("\n   🎯 Would you like to simulate payment success for testing? (y/N): ")
                    if user_input.lower().startswith('y'):
                        print("   Testing payment simulation...")
                        sim_response = requests.post(
                            f"{api_base}{simulate_url}",
                            headers=headers,
                            timeout=30
                        )
                        
                        if sim_response.status_code == 200:
                            sim_result = sim_response.json()
                            print("   ✅ Payment simulation successful!")
                            print(f"   Payment ID: {sim_result.get('payment_id')}")
                            print(f"   Status: {sim_result.get('status')}")
                            if sim_result.get('booking_created'):
                                print(f"   Booking Created: {sim_result.get('booking_id')}")
                            return sim_result
                        else:
                            print(f"   ❌ Payment simulation failed: {sim_response.status_code}")
                            try:
                                error = sim_response.json()
                                print(f"   Error: {error}")
                            except:
                                print(f"   Raw response: {sim_response.text}")
            
            return None
            
        else:
            # Server error
            print(f"   ❌ Server error: {payment_response.status_code}")
            try:
                error_result = payment_response.json()
                print(f"   Error details: {error_result}")
            except:
                print(f"   Raw response: {payment_response.text}")
            return None
            
    except requests.exceptions.Timeout:
        print("   ❌ Payment request timed out")
        print("   This might indicate PhonePe API connectivity issues")
        return None
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Payment request failed: {str(e)}")
        return None

def main():
    """Main test function"""
    print("🧪 PhonePe V2 Standard Checkout API Test")
    print("=" * 60)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"👤 Test User: {TEST_EMAIL}")
    print(f"🛒 Cart ID: {CART_ID}")
    print()
    
    # Step 1: Test API connectivity
    api_base = test_api_connectivity()
    if not api_base:
        print("❌ Cannot reach any API endpoints. Please check your connection.")
        return
    
    print(f"🌐 Using API base: {api_base}")
    print()
    
    # Step 2: Authenticate user
    access_token = authenticate_user(api_base)
    if not access_token:
        print("❌ Authentication failed. Cannot proceed with payment testing.")
        return
    
    print()
    
    # Step 3: Test PhonePe connectivity
    phonepe_ok = test_phonepe_connectivity(api_base, access_token)
    print()
    
    # Step 4: Process cart payment
    payment_result = process_cart_payment(api_base, access_token)
    
    print("\n" + "=" * 60)
    
    if payment_result:
        print("✅ Payment processing test completed successfully!")
        print("\n📋 Summary:")
        print(f"   API Base: {api_base}")
        print(f"   Cart ID: {CART_ID}")
        print(f"   Payment ID: {payment_result.get('payment_id', 'N/A')}")
        print(f"   Transaction ID: {payment_result.get('transaction_id', 'N/A')}")
        
        payment_url = payment_result.get('payment_url')
        if payment_url:
            print(f"\n🔗 Payment URL: {payment_url}")
            print("\n📱 To complete the test:")
            print("1. Open the payment URL in your browser")
            print("2. Use PhonePe Test App credentials:")
            print("   - Download PhonePe Test App from the link in PhonePe chat")
            print("   - Use test UPI ID or test card details")
            print("3. Complete the test payment")
            print("4. Check your webhook endpoint for payment status updates")
            print("5. Verify booking creation after successful payment")
        else:
            print("\n✅ Payment simulation completed (Development Mode)")
            
    else:
        print("❌ Payment processing test failed!")
        print("\n🔧 Troubleshooting Steps:")
        print("1. Check server logs for detailed error information")
        print("2. Verify PhonePe V2 API credentials in .env file:")
        print("   - PHONEPE_CLIENT_ID=TAJFOOTWEARUAT_2503031838273556894438")
        print("   - PHONEPE_CLIENT_SECRET=NTY5NjExODAtZTlkNy00ZWM3LThlZWEtYWQ0NGJkMGMzMjkz")
        print("   - PHONEPE_CLIENT_VERSION=1")
        print("3. Check network connectivity to PhonePe preprod servers")
        print("4. Verify cart ID 19 exists and belongs to the test user")
        print("5. Check if Django server is running and accessible")

if __name__ == "__main__":
    main()
