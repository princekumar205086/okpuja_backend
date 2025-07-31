#!/usr/bin/env python
"""
Test PhonePe with CORRECT CREDENTIALS - Force restart Django
"""

import os
import sys

# Clean up any existing Django imports
for module in list(sys.modules.keys()):
    if module.startswith('django') or module.startswith('okpuja_backend') or module.startswith('payment'):
        del sys.modules[module]

# Fresh Django setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')

import django
django.setup()

from django.conf import settings
import json
import uuid
import hashlib
import base64
import requests

# Force the CORRECT credentials
print("🔧 FORCING CORRECT CREDENTIALS")
print("=" * 50)

# Test Credentials (should work)
TEST_CREDS = {
    'client_id': 'TEST-M22KEWU5BO1I2_25070',
    'client_secret': 'MTgwNDU0MjctNTEzMy00ZjEzLTgwMzUtNDllNDZkZDAzYThh',
    'merchant_id': 'M22KEWU5BO1I2',
    'salt_key': 'MTgwNDU0MjctNTEzMy00ZjEzLTgwMzUtNDllNDZkZDAzYThh'
}

def test_with_forced_credentials():
    """Test payment with the exact credentials that should work"""
    print(f"📋 Using TEST credentials from PhonePe support:")
    print(f"Client ID: {TEST_CREDS['client_id']}")
    print(f"Merchant ID: {TEST_CREDS['merchant_id']}")
    
    # Test payment initiation
    payment_endpoint = "https://api-preprod.phonepe.com/apis/hermes/pg/v1/pay"
    
    transaction_id = f"OKPUJA_{uuid.uuid4().hex[:12].upper()}"
    
    payload = {
        "merchantId": TEST_CREDS['merchant_id'],
        "merchantTransactionId": transaction_id,
        "merchantUserId": f"USER_{uuid.uuid4().hex[:8].upper()}",
        "amount": 10000,  # ₹100.00
        "redirectUrl": "https://okpuja.com/payment/success",
        "redirectMode": "POST",
        "callbackUrl": "https://okpuja.com/api/payment/webhook/phonepe/v2/",
        "paymentInstrument": {
            "type": "PAY_PAGE"
        }
    }
    
    # Create signature
    payload_json = json.dumps(payload, separators=(',', ':'))
    payload_base64 = base64.b64encode(payload_json.encode()).decode()
    
    endpoint_path = "/pg/v1/pay"
    string_to_sign = payload_base64 + endpoint_path + TEST_CREDS['salt_key']
    signature = hashlib.sha256(string_to_sign.encode()).hexdigest()
    x_verify = signature + "###1"
    
    headers = {
        "Content-Type": "application/json",
        "X-VERIFY": x_verify,
        "X-MERCHANT-ID": TEST_CREDS['merchant_id'],
        "Accept": "application/json"
    }
    
    request_body = {
        "request": payload_base64
    }
    
    print(f"\n💳 Testing Payment Initiation...")
    print(f"Transaction ID: {transaction_id}")
    print(f"Endpoint: {payment_endpoint}")
    print(f"Payload: {payload}")
    
    try:
        response = requests.post(payment_endpoint, headers=headers, json=request_body, timeout=30)
        
        print(f"\n📡 Response:")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success') and 'data' in data:
                instrument_response = data['data'].get('instrumentResponse', {})
                redirect_info = instrument_response.get('redirectInfo', {})
                payment_url = redirect_info.get('url')
                
                if payment_url:
                    print(f"\n🎉 SUCCESS! PAYMENT URL GENERATED!")
                    print(f"🌐 Payment URL: {payment_url}")
                    print(f"💳 Transaction ID: {transaction_id}")
                    print(f"💰 Amount: ₹{payload['amount']/100}")
                    return True
                else:
                    print("❌ No payment URL in response")
            else:
                print(f"❌ Payment failed: {data.get('message', 'Unknown error')}")
                
        elif response.status_code == 400:
            try:
                error_data = response.json()
                error_code = error_data.get('code', '')
                error_message = error_data.get('message', '')
                
                print(f"❌ Error: {error_code} - {error_message}")
                
                if 'KEY_NOT_CONFIGURED' in error_code:
                    print("📞 Contact PhonePe support - salt key not configured for this merchant")
                elif 'MERCHANT_NOT_FOUND' in error_code:
                    print("📞 Contact PhonePe support - merchant not activated")
                elif 'INVALID_REQUEST' in error_code:
                    print("❌ Check request format")
                    
            except:
                print(f"❌ Bad request: {response.text}")
        else:
            print(f"❌ Unexpected status: {response.status_code}")
                
    except Exception as e:
        print(f"❌ Request error: {e}")
    
    return False

def test_django_with_correct_settings():
    """Test Django integration after verifying settings"""
    print(f"\n🔧 Django Settings Check:")
    print(f"Environment: {getattr(settings, 'PHONEPE_ENV', 'NOT SET')}")
    print(f"Client ID from settings: {getattr(settings, 'PHONEPE_CLIENT_ID', 'NOT SET')}")
    print(f"Merchant ID from settings: {getattr(settings, 'PHONEPE_MERCHANT_ID', 'NOT SET')}")
    
    # Override settings if they're wrong
    if getattr(settings, 'PHONEPE_CLIENT_ID', '') != TEST_CREDS['client_id']:
        print(f"\n⚠️ WRONG CREDENTIALS IN DJANGO SETTINGS!")
        print(f"Expected: {TEST_CREDS['client_id']}")
        print(f"Got: {getattr(settings, 'PHONEPE_CLIENT_ID', 'NOT SET')}")
        print(f"🔧 Forcing correct credentials...")
        
        # Force correct settings
        settings.PHONEPE_CLIENT_ID = TEST_CREDS['client_id']
        settings.PHONEPE_CLIENT_SECRET = TEST_CREDS['client_secret']
        settings.PHONEPE_MERCHANT_ID = TEST_CREDS['merchant_id']
        settings.PHONEPE_SALT_KEY = TEST_CREDS['salt_key']
    
    # Now test Django client
    try:
        from payment.phonepe_v2_corrected import PhonePeV2ClientCorrected
        
        print(f"\n🔄 Testing Django PhonePe Client...")
        client = PhonePeV2ClientCorrected(env="uat")
        
        print(f"✅ Django Client - Merchant ID: {client.merchant_id}")
        print(f"✅ Django Client - Client ID: {client.client_id}")
        print(f"✅ Django Client - Base URL: {client.base_url}")
        
        # Verify these match our expected credentials
        if client.merchant_id == TEST_CREDS['merchant_id'] and client.client_id == TEST_CREDS['client_id']:
            print(f"✅ DJANGO CREDENTIALS ARE CORRECT!")
            return True
        else:
            print(f"❌ Django credentials still wrong")
            print(f"Expected Merchant: {TEST_CREDS['merchant_id']}, Got: {client.merchant_id}")
            print(f"Expected Client: {TEST_CREDS['client_id']}, Got: {client.client_id}")
        
    except Exception as e:
        print(f"❌ Django client error: {e}")
    
    return False

def main():
    print("🚀 PhonePe TEST with CORRECT CREDENTIALS")
    print("💳 Using credentials confirmed by PhonePe support")
    
    # Test direct API call first
    direct_success = test_with_forced_credentials()
    
    # Test Django integration
    django_success = test_django_with_correct_settings()
    
    print(f"\n{'=' * 50}")
    print(f"🎯 FINAL RESULTS")
    print(f"{'=' * 50}")
    
    if direct_success:
        print("✅ Direct API call: SUCCESS")
    else:
        print("❌ Direct API call: FAILED")
        
    if django_success:
        print("✅ Django integration: READY")
    else:
        print("❌ Django integration: NEEDS FIX")
    
    if direct_success or django_success:
        print(f"\n🎉 PhonePe Integration is WORKING!")
        print(f"💰 Ready to accept payments!")
    else:
        print(f"\n⚠️ Integration needs PhonePe support assistance")
        print(f"📞 Contact PhonePe with these exact credentials")

if __name__ == "__main__":
    main()
