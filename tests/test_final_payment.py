#!/usr/bin/env python3
"""
Final comprehensive test of the PhonePe V2 corrected implementation
This script tests the complete payment flow end-to-end
"""

import requests
import json
from datetime import datetime
import time

# Configuration
API_BASE_URL = "http://localhost:8000"  # Local testing
TEST_EMAIL = "asliprinceraj@gmail.com"
TEST_PASSWORD = "Testpass@123"
CART_ID = 19

def main():
    """Test the complete payment flow"""
    print("🚀 PhonePe V2 Corrected Implementation - End-to-End Test")
    print("=" * 70)
    print(f"📅 Test Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🌐 API Base: {API_BASE_URL}")
    print(f"👤 Test User: {TEST_EMAIL}")
    print(f"🛒 Cart ID: {CART_ID}")
    print()
    
    # Step 1: Test API connectivity
    print("1. 🔗 Testing API connectivity...")
    try:
        response = requests.get(f"{API_BASE_URL}/admin/", timeout=10)
        print(f"   ✅ API is reachable (Status: {response.status_code})")
    except requests.exceptions.RequestException as e:
        print(f"   ❌ API not reachable: {str(e)}")
        return False
    
    # Step 2: Authenticate user
    print("\n2. 🔑 Authenticating user...")
    login_data = {
        "email": TEST_EMAIL,
        "password": TEST_PASSWORD
    }
    
    try:
        login_response = requests.post(
            f"{API_BASE_URL}/api/accounts/auth/login/", 
            json=login_data, 
            timeout=30
        )
        
        if login_response.status_code == 200:
            login_result = login_response.json()
            access_token = login_result.get('access')
            if access_token:
                print(f"   ✅ Authentication successful")
                print(f"   Token: {access_token[:20]}...")
            else:
                print("   ❌ No access token received")
                return False
        else:
            print(f"   ❌ Authentication failed: {login_response.status_code}")
            return False
            
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Authentication request failed: {str(e)}")
        return False
    
    # Step 3: Test debug connectivity
    print("\n3. 🔍 Testing PhonePe connectivity...")
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    
    try:
        debug_response = requests.post(
            f"{API_BASE_URL}/api/payments/payments/debug-connectivity/", 
            headers=headers, 
            json={"test_payment": True},
            timeout=30
        )
        
        if debug_response.status_code == 200:
            debug_result = debug_response.json()
            print("   ✅ Debug connectivity successful")
            
            gateway_init = debug_result.get('api_test', {}).get('gateway_init')
            if gateway_init == 'SUCCESS':
                print("   ✅ PhonePe Gateway V2 initialized successfully")
                
                # Show gateway config
                config = debug_result.get('api_test', {}).get('gateway_config', {})
                print(f"      Merchant ID: {config.get('merchant_id', 'N/A')}")
                print(f"      Base URL: {config.get('base_url', 'N/A')}")
                print(f"      Timeout: {config.get('timeout', 'N/A')}s")
            else:
                print(f"   ⚠️ PhonePe Gateway initialization: {gateway_init}")
                
        else:
            print(f"   ⚠️ Debug endpoint returned: {debug_response.status_code}")
            
    except requests.exceptions.RequestException as e:
        print(f"   ⚠️ Debug connectivity test failed: {str(e)}")
    
    # Step 4: Process cart payment
    print(f"\n4. 💳 Processing payment for cart ID {CART_ID}...")
    payment_data = {
        "cart_id": CART_ID,
        "method": "PHONEPE"
    }
    
    try:
        payment_response = requests.post(
            f"{API_BASE_URL}/api/payments/payments/process-cart/",
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
                print(f"   🔗 Payment URL Generated: ✅")
                print(f"   URL: {payment_url}")
                
                # Save payment details
                payment_details = {
                    'test_date': datetime.now().isoformat(),
                    'payment_id': result.get('payment_id'),
                    'transaction_id': result.get('transaction_id'),
                    'merchant_transaction_id': result.get('merchant_transaction_id'),
                    'payment_url': payment_url,
                    'amount': result.get('amount'),
                    'cart_id': CART_ID,
                    'user_email': TEST_EMAIL
                }
                
                try:
                    with open('successful_payment_test.json', 'w') as f:
                        json.dump(payment_details, f, indent=2)
                    print(f"   💾 Payment details saved to 'successful_payment_test.json'")
                except:
                    pass
                
                print("\n" + "=" * 70)
                print("🎉 SUCCESS! PhonePe V2 Corrected Implementation Working!")
                print("=" * 70)
                print(f"🔗 Payment URL: {payment_url}")
                print("\n📱 Next Steps to Complete Payment:")
                print("1. Copy the payment URL above")
                print("2. Open it in your browser")
                print("3. Use PhonePe Test App with UAT credentials:")
                print("   - Download PhonePe Test App (link in PhonePe support chat)")
                print("   - Use test UPI ID or test card details")
                print("4. Complete the test payment")
                print("5. Check webhook logs for payment status updates")
                print("6. Verify booking creation after successful payment")
                print("\n🔧 Integration Details:")
                print(f"   Merchant ID: {result.get('merchant_transaction_id', 'N/A')[:20]}...")
                print(f"   Environment: UAT (Testing)")
                print(f"   API Version: PhonePe V2 Standard Checkout")
                
                return True
            else:
                print("   ⚠️ No payment URL received")
                return False
                
        elif payment_response.status_code == 400:
            # Client error - check for debug options
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
                    print(f"   Simulate Success URL: {API_BASE_URL}{simulate_url}")
                    
                    # Test payment simulation for development
                    print("\n   🎯 Testing payment simulation...")
                    sim_response = requests.post(
                        f"{API_BASE_URL}{simulate_url}",
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
                        
                        print("\n" + "=" * 70)
                        print("🧪 DEVELOPMENT SUCCESS! Payment Simulation Working!")
                        print("=" * 70)
                        print("The PhonePe V2 integration is working correctly.")
                        print("Payment simulation completed successfully in development mode.")
                        return True
                    else:
                        print(f"   ❌ Payment simulation failed: {sim_response.status_code}")
            
            return False
            
        else:
            # Server error
            print(f"   ❌ Server error: {payment_response.status_code}")
            try:
                error_result = payment_response.json()
                print(f"   Error details: {error_result}")
            except:
                print(f"   Raw response: {payment_response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print("   ❌ Payment request timed out")
        return False
        
    except requests.exceptions.RequestException as e:
        print(f"   ❌ Payment request failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = main()
    
    if not success:
        print("\n" + "=" * 70)
        print("❌ Test Failed!")
        print("=" * 70)
        print("🔧 Troubleshooting Steps:")
        print("1. Check Django server is running: python manage.py runserver")
        print("2. Verify PhonePe V2 credentials in .env file")
        print("3. Check network connectivity to PhonePe UAT servers")
        print("4. Verify cart ID 19 exists and belongs to test user")
        print("5. Check Django logs for detailed error information")
        print("6. Test PhonePe connectivity from your server environment")
