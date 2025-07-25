#!/usr/bin/env python
"""
PhonePe API Endpoint and Credentials Tester
Tests the correct API endpoints and credential configuration
"""

import os
import django
import requests
import json
import base64
import hashlib

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings
from payment.gateways import get_payment_gateway

def test_phonepe_endpoints():
    """Test different PhonePe API endpoints"""
    print("🌐 TESTING PHONEPE API ENDPOINTS")
    print("=" * 50)
    
    endpoints = [
        "https://api.phonepe.com/apis/hermes",
        "https://api.phonepe.com/apis/hermes/pg/v1/pay",
        "https://mercury-t2.phonepe.com/apis/hermes/pg/v1/pay",
        "https://api-preprod.phonepe.com/apis/hermes/pg/v1/pay"
    ]
    
    for endpoint in endpoints:
        try:
            print(f"\n🔍 Testing: {endpoint}")
            response = requests.get(endpoint, timeout=10)
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:100]}...")
            
            if response.status_code in [200, 400]:
                print(f"   ✅ Endpoint reachable")
            else:
                print(f"   ⚠️ Unexpected status code")
                
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")

def test_gateway_settings():
    """Test gateway settings and configuration"""
    print("\n⚙️ TESTING GATEWAY SETTINGS")
    print("=" * 50)
    
    try:
        gateway = get_payment_gateway('phonepe')
        
        print(f"✅ Gateway loaded: {type(gateway).__name__}")
        print(f"🏢 Merchant ID: {gateway.merchant_id}")
        print(f"🔑 Merchant Key: {'*' * 20}{gateway.merchant_key[-10:]}")
        print(f"🧂 Salt Index: {gateway.salt_index}")
        print(f"🌐 Base URL: {gateway.base_url}")
        print(f"⏰ Timeout: {gateway.timeout}s")
        print(f"🔄 Max Retries: {gateway.max_retries}")
        print(f"🏭 Production: {gateway.is_production}")
        
        # Check if settings are being read correctly
        expected_timeout = int(getattr(settings, 'PHONEPE_TIMEOUT', 180))
        expected_retries = int(getattr(settings, 'PHONEPE_MAX_RETRIES', 7))
        
        if gateway.timeout == expected_timeout:
            print(f"✅ Timeout setting correct: {gateway.timeout}s")
        else:
            print(f"❌ Timeout mismatch: got {gateway.timeout}s, expected {expected_timeout}s")
            
        if gateway.max_retries == expected_retries:
            print(f"✅ Retry setting correct: {gateway.max_retries}")
        else:
            print(f"❌ Retry mismatch: got {gateway.max_retries}, expected {expected_retries}")
            
        return gateway
        
    except Exception as e:
        print(f"❌ Gateway loading failed: {str(e)}")
        return None

def test_api_call_with_test_credentials():
    """Test API call with test credentials"""
    print("\n🧪 TESTING WITH TEST CREDENTIALS")
    print("=" * 50)
    
    # Test credentials from your message
    test_merchant_id = "TEST-M22KEWU5BO1I2_25070"
    test_merchant_key = "MTgwNDU0MjctNTEzMy00ZjEzLTgwMzUtNDllNDZkZDAzYThh"  # This might need to be decoded
    test_salt_index = 1
    
    # Try to decode the test merchant key if it's base64
    try:
        decoded_key = base64.b64decode(test_merchant_key).decode('utf-8')
        print(f"🔑 Decoded test key: {decoded_key}")
        test_key_to_use = decoded_key
    except:
        print(f"🔑 Using test key as-is: {test_merchant_key}")
        test_key_to_use = test_merchant_key
    
    # Create test payload
    payload = {
        "merchantId": test_merchant_id,
        "merchantTransactionId": f"TEST_API_{int(__import__('time').time())}",
        "merchantUserId": "TEST_USER_123",
        "amount": 100,  # 1 rupee
        "redirectUrl": "https://backend.okpuja.com/test-success",
        "redirectMode": "POST",
        "callbackUrl": "https://backend.okpuja.com/api/payments/webhook/phonepe/",
        "mobileNumber": "9999999999",
        "paymentInstrument": {
            "type": "PAY_PAGE"
        }
    }
    
    # Encode and sign
    data = base64.b64encode(json.dumps(payload).encode()).decode()
    string_to_hash = data + "/pg/v1/pay" + test_key_to_use
    checksum = hashlib.sha256(string_to_hash.encode()).hexdigest()
    final_checksum = f"{checksum}###{test_salt_index}"
    
    final_payload = {"request": data}
    headers = {
        'Content-Type': 'application/json',
        'X-VERIFY': final_checksum,
        'User-Agent': 'okpuja-backend/1.0'
    }
    
    # Test endpoints
    test_endpoints = [
        "https://api.phonepe.com/apis/hermes/pg/v1/pay",
        "https://api-preprod.phonepe.com/apis/hermes/pg/v1/pay"
    ]
    
    for endpoint in test_endpoints:
        print(f"\n🎯 Testing endpoint: {endpoint}")
        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json=final_payload,
                timeout=30
            )
            
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    if data.get('success'):
                        print(f"   ✅ API call successful!")
                        return True
                    else:
                        print(f"   ⚠️ API call failed: {data.get('message', 'Unknown error')}")
                except:
                    print(f"   ⚠️ Non-JSON response")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
    
    return False

def test_production_credentials():
    """Test with production credentials from .env"""
    print("\n🏭 TESTING WITH PRODUCTION CREDENTIALS")
    print("=" * 50)
    
    try:
        gateway = get_payment_gateway('phonepe')
        if not gateway:
            print("❌ Could not load gateway")
            return False
        
        # Create test payload
        payload = {
            "merchantId": gateway.merchant_id,
            "merchantTransactionId": f"PROD_TEST_{int(__import__('time').time())}",
            "merchantUserId": "PROD_USER_123",
            "amount": 100,  # 1 rupee
            "redirectUrl": "https://backend.okpuja.com/test-success",
            "redirectMode": "POST", 
            "callbackUrl": settings.PHONEPE_CALLBACK_URL,
            "mobileNumber": "9999999999",
            "paymentInstrument": {
                "type": "PAY_PAGE"
            }
        }
        
        # Encode and sign
        data = base64.b64encode(json.dumps(payload).encode()).decode()
        string_to_hash = data + "/pg/v1/pay" + gateway.merchant_key
        checksum = hashlib.sha256(string_to_hash.encode()).hexdigest()
        final_checksum = f"{checksum}###{gateway.salt_index}"
        
        final_payload = {"request": data}
        headers = {
            'Content-Type': 'application/json',
            'X-VERIFY': final_checksum,
            'User-Agent': 'okpuja-backend/1.0'
        }
        
        # Test production endpoint
        endpoint = "https://api.phonepe.com/apis/hermes/pg/v1/pay"
        
        print(f"🎯 Testing production endpoint: {endpoint}")
        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json=final_payload,
                timeout=30
            )
            
            print(f"   Status: {response.status_code}")
            print(f"   Response: {response.text[:200]}...")
            
            if response.status_code == 200:
                try:
                    response_data = response.json()
                    if response_data.get('success'):
                        print(f"   ✅ Production API call successful!")
                        return True
                    else:
                        print(f"   ⚠️ Production API call failed: {response_data.get('message', 'Unknown error')}")
                        print(f"   📋 Error code: {response_data.get('code', 'Unknown')}")
                except:
                    print(f"   ⚠️ Non-JSON response")
            else:
                print(f"   ❌ HTTP Error: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ Request failed: {str(e)}")
            
    except Exception as e:
        print(f"❌ Production test failed: {str(e)}")
        
    return False

def main():
    print("🔧 PHONEPE API ENDPOINT & CREDENTIALS TESTER")
    print("=" * 60)
    
    # Test endpoints
    test_phonepe_endpoints()
    
    # Test gateway settings
    gateway = test_gateway_settings()
    
    # Test with test credentials
    test_success = test_api_call_with_test_credentials()
    
    # Test with production credentials
    prod_success = test_production_credentials()
    
    print("\n" + "=" * 60)
    print("📋 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    if gateway:
        print("✅ Gateway configuration loaded")
        if gateway.timeout == 180:
            print("✅ Timeout settings correct (180s)")
        else:
            print(f"⚠️ Timeout settings: {gateway.timeout}s (expected 180s)")
    else:
        print("❌ Gateway configuration issues")
    
    if test_success:
        print("✅ Test credentials API call successful")
    else:
        print("❌ Test credentials API call failed")
        
    if prod_success:
        print("✅ Production credentials API call successful")
    else:
        print("❌ Production credentials API call failed")
    
    print("\n🎯 NEXT STEPS:")
    if not test_success and not prod_success:
        print("1. Check PhonePe merchant dashboard for correct API endpoints")
        print("2. Verify merchant credentials are active")
        print("3. Check if IP whitelisting is required")
        print("4. Contact PhonePe support for API access verification")
    elif test_success and not prod_success:
        print("1. Test credentials work - check production merchant setup")
        print("2. Verify production merchant is activated")
        print("3. Check production merchant key format")
    else:
        print("✅ API connectivity is working!")
        print("Your connection refused error should now be resolved")

if __name__ == "__main__":
    main()
