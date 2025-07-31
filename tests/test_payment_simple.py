#!/usr/bin/env python3
"""
Simple Payment Test for Cart 40 - Fixed Version
"""

import requests
import json

def test_payment_simple():
    """Simple test for payment processing with cart 40"""
    
    print("🧪 Simple Payment Test - Cart 40")
    print("=" * 40)
    
    # Configuration
    BASE_URL = "http://127.0.0.1:8000"
    EMAIL = "asliprinceraj@gmail.com"
    PASSWORD = "testpass123"
    CART_ID = 40
    
    try:
        # Step 1: Login
        print("1️⃣ Logging in...")
        login_response = requests.post(
            f"{BASE_URL}/api/accounts/login/",
            json={"email": EMAIL, "password": PASSWORD},
            timeout=30
        )
        
        print(f"Login status: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text[:200]}")
            return False
        
        token = login_response.json().get('access_token')
        if not token:
            print("❌ No access token received")
            return False
            
        print("✅ Login successful")
        
        # Step 2: Process payment
        print(f"\n2️⃣ Processing payment for cart {CART_ID}...")
        
        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json'
        }
        
        payment_data = {
            "cart_id": CART_ID,
            "payment_method": "PHONEPE"
        }
        
        print(f"Request: POST {BASE_URL}/api/payments/process-cart/")
        print(f"Data: {json.dumps(payment_data, indent=2)}")
        
        payment_response = requests.post(
            f"{BASE_URL}/api/payments/process-cart/",
            json=payment_data,
            headers=headers,
            timeout=60
        )
        
        print(f"\n📊 Response Status: {payment_response.status_code}")
        print(f"Response Headers: Content-Type = {payment_response.headers.get('content-type')}")
        
        # Parse response
        try:
            response_data = payment_response.json()
            print(f"\n📋 Response Data:")
            print(json.dumps(response_data, indent=2))
            
            if payment_response.status_code == 200:
                print(f"\n🎉 SUCCESS!")
                print(f"✅ Payment processing successful")
                
                if 'payment_url' in response_data:
                    print(f"🔗 Payment URL: {response_data['payment_url']}")
                
                if 'transaction_id' in response_data:
                    print(f"💳 Transaction ID: {response_data['transaction_id']}")
                
                return True
                
            elif payment_response.status_code == 400:
                print(f"\n❌ HTTP 400 Error")
                
                # Check for debug info
                if 'debug_info' in response_data:
                    debug = response_data['debug_info']
                    print(f"Error Type: {debug.get('error_type')}")
                    print(f"Error Details: {debug.get('error_details')}")
                    print(f"Admin Message: {debug.get('admin_message')}")
                
                # Check for simulation option
                if 'debug_options' in response_data:
                    debug_options = response_data['debug_options']
                    simulate_url = debug_options.get('simulate_payment_url')
                    
                    if simulate_url:
                        print(f"\n🎭 Simulation endpoint available: {simulate_url}")
                        print(f"Use: POST {BASE_URL}{simulate_url}")
                
                return False
            else:
                print(f"\n❌ Unexpected status code: {payment_response.status_code}")
                return False
                
        except json.JSONDecodeError as e:
            print(f"❌ JSON decode error: {str(e)}")
            print(f"Raw response: {payment_response.text[:500]}")
            return False
        
    except requests.exceptions.ConnectionError as e:
        print(f"❌ Connection error: {str(e)}")
        print("Make sure Django server is running: python manage.py runserver")
        return False
        
    except requests.exceptions.Timeout as e:
        print(f"❌ Timeout error: {str(e)}")
        return False
        
    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Simple Payment Test")
    print("Make sure Django server is running on http://127.0.0.1:8000")
    print("=" * 60)
    
    success = test_payment_simple()
    
    if success:
        print(f"\n✅ Test completed successfully!")
        print(f"The PhonePe HTTP 400 error has been fixed!")
    else:
        print(f"\n❌ Test failed")
        print(f"Check the error details above")
    
    print(f"\n📋 Test Summary:")
    print(f"- Email: asliprinceraj@gmail.com")
    print(f"- Cart ID: 40") 
    print(f"- Payment Method: PHONEPE")
    print(f"- Expected: Payment URL generation")
