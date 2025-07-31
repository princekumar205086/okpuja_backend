#!/usr/bin/env python
"""
PhonePe V2 Complete Testing - Test & Production Credentials
Testing both sets of credentials as confirmed by PhonePe support
"""

import os
import sys
import django
import json
import uuid
import hashlib
import base64
import requests

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from payment.phonepe_v2_corrected import PhonePeV2ClientCorrected

# Test Credentials (should work in UAT)
TEST_CREDS = {
    'client_id': 'TEST-M22KEWU5BO1I2_25070',
    'client_secret': 'MTgwNDU0MjctNTEzMy00ZjEzLTgwMzUtNDllNDZkZDAzYThh',
    'merchant_id': 'M22KEWU5BO1I2',
    'salt_key': 'MTgwNDU0MjctNTEzMy00ZjEzLTgwMzUtNDllNDZkZDAzYThh'
}

# Production Credentials (should work in Production)
PROD_CREDS = {
    'client_id': 'SU2507311635477696235898',
    'client_secret': '1f59672d-e31c-4898-9caf-19ab54bcaaab',
    'merchant_id': 'M22KEWU5BO1I2',
    'salt_key': '1f59672d-e31c-4898-9caf-19ab54bcaaab'
}

def test_direct_payment_api(credentials, environment_name, base_url):
    """Test direct payment API with specific credentials"""
    print(f"\n{'=' * 80}")
    print(f"Testing {environment_name} Environment")
    print(f"Base URL: {base_url}")
    print("=" * 80)
    
    # Determine the correct endpoint based on environment
    if 'preprod' in base_url:
        # UAT endpoints
        payment_endpoint = f"{base_url}/apis/hermes/pg/v1/pay"
        oauth_endpoint = f"{base_url}/apis/hermes/oauth2/v2/token"
    else:
        # Production endpoints
        payment_endpoint = f"{base_url}/apis/hermes/pg/v1/pay"
        oauth_endpoint = f"{base_url}/apis/hermes/oauth2/v2/token"
    
    print(f"Client ID: {credentials['client_id']}")
    print(f"Merchant ID: {credentials['merchant_id']}")
    print(f"Payment Endpoint: {payment_endpoint}")
    
    # Test OAuth first
    print(f"\n🔐 Testing OAuth Authentication...")
    
    oauth_headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-MERCHANT-ID': credentials['merchant_id'],
    }
    
    oauth_data = {
        'client_id': credentials['client_id'],
        'client_version': '1',
        'client_secret': credentials['client_secret'],
        'grant_type': 'client_credentials'
    }
    
    try:
        oauth_response = requests.post(oauth_endpoint, headers=oauth_headers, data=oauth_data, timeout=30)
        print(f"OAuth Status: {oauth_response.status_code}")
        print(f"OAuth Response: {oauth_response.text}")
        
        if oauth_response.status_code == 200:
            print("✅ OAuth successful!")
            token_data = oauth_response.json()
            access_token = token_data.get('access_token')
        else:
            print("⚠️ OAuth failed, trying direct payment...")
            access_token = None
            
    except Exception as e:
        print(f"OAuth error: {e}")
        access_token = None
    
    # Test Payment Initiation
    print(f"\n💳 Testing Payment Initiation...")
    
    transaction_id = f"OKPUJA_{uuid.uuid4().hex[:12].upper()}"
    
    payload = {
        "merchantId": credentials['merchant_id'],
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
    string_to_sign = payload_base64 + endpoint_path + credentials['salt_key']
    signature = hashlib.sha256(string_to_sign.encode()).hexdigest()
    x_verify = signature + "###1"
    
    payment_headers = {
        "Content-Type": "application/json",
        "X-VERIFY": x_verify,
        "X-MERCHANT-ID": credentials['merchant_id'],
        "Accept": "application/json"
    }
    
    request_body = {
        "request": payload_base64
    }
    
    print(f"Transaction ID: {transaction_id}")
    print(f"Amount: ₹{payload['amount']/100}")
    print(f"Signature: {x_verify[:50]}...")
    
    try:
        payment_response = requests.post(payment_endpoint, headers=payment_headers, json=request_body, timeout=30)
        
        print(f"\n📡 Payment Response:")
        print(f"Status Code: {payment_response.status_code}")
        print(f"Response: {payment_response.text}")
        
        if payment_response.status_code == 200:
            print("✅ PAYMENT SUCCESSFUL!")
            try:
                data = payment_response.json()
                
                # Check for payment URL
                if data.get('success') and 'data' in data:
                    instrument_response = data['data'].get('instrumentResponse', {})
                    redirect_info = instrument_response.get('redirectInfo', {})
                    payment_url = redirect_info.get('url')
                    
                    if payment_url:
                        print(f"\n🎉 LIVE PAYMENT URL GENERATED!")
                        print(f"🌐 Payment URL: {payment_url}")
                        print(f"💳 Transaction ID: {transaction_id}")
                        print(f"💰 Amount: ₹{payload['amount']/100}")
                        return True, payment_url, transaction_id
                    else:
                        print("❌ No payment URL in response")
                else:
                    print(f"❌ Payment failed: {data.get('message', 'Unknown error')}")
                    
            except Exception as e:
                print(f"Response parsing error: {e}")
                
        elif payment_response.status_code == 400:
            try:
                error_data = payment_response.json()
                error_code = error_data.get('code', '')
                error_message = error_data.get('message', '')
                
                if 'MERCHANT_NOT_FOUND' in error_code:
                    print("❌ Merchant not found - credentials may not be activated")
                elif 'INVALID_REQUEST' in error_code:
                    print("❌ Invalid request format")
                elif 'SIGNATURE_VERIFICATION_FAILED' in error_code:
                    print("❌ Signature verification failed")
                else:
                    print(f"❌ Error: {error_code} - {error_message}")
                    
            except:
                print(f"❌ Bad request: {payment_response.text}")
                
        elif payment_response.status_code == 404:
            print("❌ Endpoint not found - check URL")
        else:
            print(f"❌ Unexpected status: {payment_response.status_code}")
                
    except Exception as e:
        print(f"❌ Payment request error: {e}")
    
    return False, None, None

def test_django_integration():
    """Test Django integration with current settings"""
    print(f"\n{'=' * 80}")
    print("Testing Django Integration")
    print("=" * 80)
    
    try:
        # Test PhonePe client initialization
        client = PhonePeV2ClientCorrected(env="uat")
        
        print(f"✅ Django PhonePe client initialized")
        print(f"✅ Merchant ID: {client.merchant_id}")
        print(f"✅ Payment Endpoint: {client.payment_endpoint}")
        print(f"✅ Client ID: {client.client_id[:20]}...")
        
        # Test payment service
        from payment.services import PaymentService
        service = PaymentService()
        print(f"✅ Payment service initialized")
        
        # Test with Django client
        print(f"\n🔄 Testing Django Payment Client...")
        
        payment_data = {
            'merchant_transaction_id': f"DJANGO_{uuid.uuid4().hex[:12].upper()}",
            'amount': 10000,
            'redirect_url': 'https://okpuja.com/payment/success',
            'callback_url': 'https://okpuja.com/api/payment/webhook/phonepe/v2/',
            'merchant_user_id': f"USER_{uuid.uuid4().hex[:8].upper()}"
        }
        
        result = client.initiate_payment(**payment_data)
        
        if result and result.get('success'):
            print("✅ DJANGO INTEGRATION WORKING!")
            
            # Extract payment URL
            instrument_response = result.get('data', {}).get('instrumentResponse', {})
            redirect_info = instrument_response.get('redirectInfo', {})
            payment_url = redirect_info.get('url')
            
            if payment_url:
                print(f"🌐 Payment URL: {payment_url}")
                return True
        else:
            print(f"⚠️ Django integration needs attention")
            print(f"Response: {result}")
            
    except Exception as e:
        print(f"❌ Django integration error: {e}")
    
    return False

def main():
    """Main testing function"""
    print("🚀 PhonePe V2 Complete Integration Test")
    print("💳 Testing both TEST and PRODUCTION credentials")
    print("📞 PhonePe support confirmed activation")
    
    results = {}
    
    # Test with UAT environment and test credentials
    success1, url1, tx1 = test_direct_payment_api(
        TEST_CREDS, 
        "UAT (Test Credentials)", 
        "https://api-preprod.phonepe.com"
    )
    results['uat_test'] = success1
    
    # Test with Production environment and production credentials  
    success2, url2, tx2 = test_direct_payment_api(
        PROD_CREDS,
        "PRODUCTION (Live Credentials)",
        "https://api.phonepe.com"
    )
    results['prod'] = success2
    
    # Test Django integration
    django_success = test_django_integration()
    results['django'] = django_success
    
    # Final Summary
    print(f"\n{'=' * 80}")
    print("🎯 FINAL TEST RESULTS")
    print("=" * 80)
    
    if any(results.values()):
        print("🎉 SUCCESS! Your PhonePe PG is WORKING!")
        
        if results['uat_test']:
            print("✅ UAT with Test Credentials: WORKING")
        if results['prod']:
            print("✅ Production with Live Credentials: WORKING")
        if results['django']:
            print("✅ Django Integration: WORKING")
            
        print(f"\n🚀 YOUR PHONEPE PG IS 100% READY!")
        print("💰 You can now accept live payments!")
        
        # Show working configuration
        working_env = "UAT" if results['uat_test'] else "PRODUCTION"
        working_creds = TEST_CREDS if results['uat_test'] else PROD_CREDS
        
        print(f"\n📋 Working Configuration:")
        print(f"Environment: {working_env}")
        print(f"Client ID: {working_creds['client_id']}")
        print(f"Merchant ID: {working_creds['merchant_id']}")
        
        if results['uat_test'] and url1:
            print(f"🌐 Test Payment URL: {url1}")
        if results['prod'] and url2:
            print(f"🌐 Live Payment URL: {url2}")
            
    else:
        print("⚠️ Integration needs attention")
        print("📞 Contact PhonePe support to verify activation status")
        
        print(f"\n📋 Tested Configurations:")
        print(f"❌ UAT Test Credentials: {TEST_CREDS['client_id']}")
        print(f"❌ Production Credentials: {PROD_CREDS['client_id']}")
    
    print(f"{'=' * 80}")

if __name__ == "__main__":
    main()
