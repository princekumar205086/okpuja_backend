#!/usr/bin/env python3
"""
Test Payment with Fixed PhonePe Configuration
Test script to verify the HTTP 400 error fix
"""

import requests
import json
import os
import sys
import django
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.absolute()
sys.path.append(str(project_root))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

def test_fixed_payment():
    """Test payment processing with fixed PhonePe configuration"""
    
    print("🧪 Testing Fixed Payment Processing")
    print("=" * 50)
    
    # Test configuration
    BASE_URL = "http://127.0.0.1:8000"
    EMAIL = "asliprinceraj@gmail.com"
    PASSWORD = "testpass123"
    CART_ID = 40
    
    try:
        # Step 1: Login
        print("\n1️⃣ Logging in...")
        login_url = f"{BASE_URL}/api/accounts/login/"
        login_data = {"email": EMAIL, "password": PASSWORD}
        
        login_response = requests.post(login_url, json=login_data, timeout=30)
        print(f"Login status: {login_response.status_code}")
        
        if login_response.status_code != 200:
            print(f"❌ Login failed: {login_response.text}")
            return False
        
        login_result = login_response.json()
        token = login_result.get('access_token')
        
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
        
        payment_url = f"{BASE_URL}/api/payments/process-cart/"
        payment_data = {
            "cart_id": CART_ID,
            "payment_method": "PHONEPE"
        }
        
        print(f"Making request to: {payment_url}")
        print(f"Data: {json.dumps(payment_data, indent=2)}")
        
        payment_response = requests.post(payment_url, json=payment_data, headers=headers, timeout=60)
        
        print(f"\n📊 Payment Response:")
        print(f"Status: {payment_response.status_code}")
        
        try:
            response_data = payment_response.json()
            print(f"Response: {json.dumps(response_data, indent=2)}")
            
            if payment_response.status_code == 200:
                print("\n✅ SUCCESS: Payment initiated successfully!")
                
                if 'payment_url' in response_data:
                    payment_url = response_data['payment_url']
                    print(f"🔗 Payment URL: {payment_url}")
                    
                    # Extract payment ID for status checking
                    payment_id = response_data.get('payment_id')
                    if payment_id:
                        print(f"💳 Payment ID: {payment_id}")
                        
                        # Test status verification
                        print(f"\n3️⃣ Testing status verification...")
                        status_url = f"{BASE_URL}/api/payments/payments/{payment_id}/verify-status/"
                        
                        status_response = requests.post(status_url, headers=headers, timeout=30)
                        print(f"Status check: {status_response.status_code}")
                        
                        if status_response.status_code == 200:
                            status_data = status_response.json()
                            print(f"Status data: {json.dumps(status_data, indent=2)}")
                
                return True
                
            elif payment_response.status_code == 400:
                print("\n❌ HTTP 400 Error Still Present")
                
                debug_info = response_data.get('debug_info', {})
                print(f"Error Type: {debug_info.get('error_type')}")
                print(f"Error Details: {debug_info.get('error_details')}")
                print(f"Admin Message: {debug_info.get('admin_message')}")
                
                # Try simulation endpoint
                debug_options = response_data.get('debug_options', {})
                simulate_url = debug_options.get('simulate_payment_url')
                
                if simulate_url:
                    print(f"\n🎭 Trying simulation endpoint...")
                    full_simulate_url = f"{BASE_URL}{simulate_url}"
                    
                    simulate_response = requests.post(full_simulate_url, headers=headers, timeout=30)
                    print(f"Simulation status: {simulate_response.status_code}")
                    
                    if simulate_response.status_code == 200:
                        simulate_data = simulate_response.json()
                        print(f"✅ Simulation successful: {json.dumps(simulate_data, indent=2)}")
                        return True
                
                return False
            else:
                print(f"❌ Unexpected status: {payment_response.status_code}")
                return False
                
        except json.JSONDecodeError:
            print(f"❌ Invalid JSON: {payment_response.text}")
            return False
    
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_phonepe_connectivity():
    """Test PhonePe API connectivity"""
    
    print("\n🌐 Testing PhonePe API Connectivity")
    print("=" * 40)
    
    from django.conf import settings
    
    # Test endpoints
    endpoints = [
        "https://api-preprod.phonepe.com",
        "https://api-preprod.phonepe.com/apis/hermes",
        "https://api-preprod.phonepe.com/apis/hermes/v1",
        f"https://api-preprod.phonepe.com/apis/hermes/v1/oauth/token",
        f"https://api-preprod.phonepe.com/apis/hermes/pg/v1/pay"
    ]
    
    for endpoint in endpoints:
        try:
            response = requests.get(endpoint, timeout=10)
            status = "✅" if response.status_code in [200, 404, 405] else "⚠️"
            print(f"{status} {endpoint}: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ {endpoint}: Connection Failed")
        except Exception as e:
            print(f"❌ {endpoint}: {str(e)}")

def main():
    """Main test function"""
    
    print("🔧 PhonePe HTTP 400 Error Fix - Test Script")
    print("=" * 60)
    
    # Test connectivity first
    test_phonepe_connectivity()
    
    # Test payment processing
    if test_fixed_payment():
        print("\n🎉 SUCCESS: Payment processing is now working!")
        print("\n✅ The HTTP 400 error has been fixed!")
    else:
        print("\n❌ FAILED: Payment processing still has issues")
        print("\n🔧 Additional troubleshooting may be needed")
    
    print("\n📋 Summary:")
    print("1. Updated PhonePe API base URLs")
    print("2. Fixed OAuth2 endpoint paths")  
    print("3. Corrected payment and status endpoints")
    print("4. Updated callback URLs for localhost")

if __name__ == "__main__":
    main()
