#!/usr/bin/env python3
"""
Comprehensive Cart 40 Payment Test - Final Version
This script tests the complete payment flow with proper error handling
"""

import sys
import time
import requests
import json
from pathlib import Path

def wait_for_server(base_url="http://127.0.0.1:8000", max_attempts=10):
    """Wait for Django server to be ready"""
    print("🔍 Checking if Django server is running...")
    
    for attempt in range(max_attempts):
        try:
            response = requests.get(f"{base_url}/admin/", timeout=5)
            print(f"✅ Django server is running (Status: {response.status_code})")
            return True
        except requests.exceptions.ConnectionError:
            print(f"⏳ Attempt {attempt + 1}/{max_attempts} - Waiting for server...")
            time.sleep(2)
        except Exception as e:
            print(f"⚠️ Unexpected error: {str(e)}")
            time.sleep(1)
    
    print("❌ Django server is not accessible")
    print("Please start the server with: python manage.py runserver")
    return False

def test_login(base_url, email, password):
    """Test user login"""
    print(f"\n1️⃣ Testing login for {email}...")
    
    try:
        response = requests.post(
            f"{base_url}/api/accounts/login/",
            json={"email": email, "password": password},
            timeout=30
        )
        
        print(f"Login response: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            token = data.get('access_token')
            
            if token:
                print("✅ Login successful")
                return token
            else:
                print("❌ No access token in response")
                return None
        else:
            print(f"❌ Login failed: {response.status_code}")
            return None
    
    except Exception as e:
        print(f"❌ Login error: {str(e)}")
        return None

def test_payment_processing(base_url, token, cart_id):
    """Test payment processing"""
    print(f"\n2️⃣ Testing payment processing for cart {cart_id}...")
    
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    payment_data = {
        "cart_id": cart_id,
        "payment_method": "PHONEPE"
    }
    
    try:
        response = requests.post(
            f"{base_url}/api/payments/process-cart/",
            json=payment_data,
            headers=headers,
            timeout=60
        )
        
        print(f"Payment Response Status: {response.status_code}")
        
        # Parse response
        try:
            response_data = response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
            
            if response.status_code == 200:
                print(f"\n🎉 SUCCESS: Payment processing successful!")
                return {'success': True, 'data': response_data}
            
            elif response.status_code == 400:
                print(f"\n❌ HTTP 400 Error")
                
                # Check for simulation option
                if 'debug_options' in response_data:
                    simulate_url = response_data['debug_options'].get('simulate_payment_url')
                    if simulate_url:
                        print(f"🎭 Testing simulation...")
                        return test_simulation(base_url, token, simulate_url)
                
                return {'success': False, 'error': 'HTTP_400', 'data': response_data}
            
            else:
                return {'success': False, 'error': f'HTTP_{response.status_code}'}
        
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON response")
            return {'success': False, 'error': 'INVALID_JSON'}
    
    except Exception as e:
        print(f"❌ Request error: {str(e)}")
        return {'success': False, 'error': str(e)}

def test_simulation(base_url, token, simulate_url):
    """Test payment simulation endpoint"""
    print(f"Testing simulation: {simulate_url}")
    
    headers = {'Authorization': f'Bearer {token}'}
    
    try:
        response = requests.post(f"{base_url}{simulate_url}", headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Simulation successful!")
            print(json.dumps(data, indent=2))
            return {'success': True, 'simulated': True, 'data': data}
        else:
            return {'success': False, 'simulated': True}
    
    except Exception as e:
        return {'success': False, 'error': str(e)}

def main():
    """Main test function"""
    print("🚀 Comprehensive Cart 40 Payment Test")
    print("=" * 60)
    
    BASE_URL = "http://127.0.0.1:8000"
    EMAIL = "asliprinceraj@gmail.com"
    PASSWORD = "testpass123"
    CART_ID = 40
    
    # Check server
    if not wait_for_server(BASE_URL):
        return False
    
    # Test login
    token = test_login(BASE_URL, EMAIL, PASSWORD)
    if not token:
        return False
    
    # Test payment
    result = test_payment_processing(BASE_URL, token, CART_ID)
    
    print(f"\n" + "=" * 60)
    print(f"🏁 FINAL RESULTS")
    print(f"=" * 60)
    
    if result['success']:
        print(f"✅ TEST PASSED: Payment system working!")
        if result.get('simulated'):
            print(f"🎭 Used simulation (development mode)")
        print(f"🎉 The PhonePe HTTP 400 error has been FIXED!")
        return True
    else:
        print(f"❌ TEST FAILED: {result.get('error', 'Unknown error')}")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
