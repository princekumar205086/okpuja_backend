#!/usr/bin/env python
"""
FINAL CREDENTIAL VERIFICATION - Using exact credentials you provided
Testing both sets exactly as PhonePe support gave them
"""

import json
import uuid
import hashlib
import base64
import requests

def test_exact_credentials():
    """Test with the exact credentials provided by PhonePe support"""
    print("🚀 FINAL CREDENTIAL TEST")
    print("💳 Using EXACT credentials from PhonePe support")
    print("=" * 60)
    
    # TEST 1: Your TEST credentials
    print(f"\n1️⃣ Testing TEST Credentials (UAT)")
    print("-" * 40)
    
    test_creds = {
        'client_id': 'TEST-M22KEWU5BO1I2_25070',
        'client_secret': 'MTgwNDU0MjctNTEzMy00ZjEzLTgwMzUtNDllNDZkZDAzYThh',
        'merchant_id': 'M22KEWU5BO1I2',
        'salt_key': 'MTgwNDU0MjctNTEzMy00ZjEzLTgwMzUtNDllNDZkZDAzYThh'
    }
    
    result1 = test_payment_endpoint(
        creds=test_creds,
        endpoint="https://api-preprod.phonepe.com/apis/hermes/pg/v1/pay",
        name="TEST on UAT"
    )
    
    # TEST 2: Your PRODUCTION credentials on UAT
    print(f"\n2️⃣ Testing PRODUCTION Credentials (UAT)")
    print("-" * 40)
    
    prod_creds = {
        'client_id': 'SU2507311635477696235898',
        'client_secret': '1f59672d-e31c-4898-9caf-19ab54bcaaab',
        'merchant_id': 'M22KEWU5BO1I2',
        'salt_key': '1f59672d-e31c-4898-9caf-19ab54bcaaab'
    }
    
    result2 = test_payment_endpoint(
        creds=prod_creds,
        endpoint="https://api-preprod.phonepe.com/apis/hermes/pg/v1/pay",
        name="PRODUCTION on UAT"
    )
    
    # TEST 3: Your PRODUCTION credentials on PRODUCTION
    print(f"\n3️⃣ Testing PRODUCTION Credentials (LIVE)")
    print("-" * 40)
    
    result3 = test_payment_endpoint(
        creds=prod_creds,
        endpoint="https://api.phonepe.com/apis/hermes/pg/v1/pay",
        name="PRODUCTION on LIVE"
    )
    
    # FINAL SUMMARY
    print(f"\n{'=' * 60}")
    print(f"🎯 FINAL VERIFICATION RESULTS")
    print(f"{'=' * 60}")
    
    working_configs = []
    
    if result1['success']:
        working_configs.append("✅ TEST credentials on UAT")
        print(f"✅ TEST credentials on UAT: WORKING")
        print(f"   🌐 Payment URL: {result1['url']}")
    else:
        print(f"❌ TEST credentials on UAT: {result1['error']}")
    
    if result2['success']:
        working_configs.append("✅ PRODUCTION credentials on UAT")
        print(f"✅ PRODUCTION credentials on UAT: WORKING")
        print(f"   🌐 Payment URL: {result2['url']}")
    else:
        print(f"❌ PRODUCTION credentials on UAT: {result2['error']}")
    
    if result3['success']:
        working_configs.append("✅ PRODUCTION credentials on LIVE")
        print(f"✅ PRODUCTION credentials on LIVE: WORKING")
        print(f"   🌐 Payment URL: {result3['url']}")
    else:
        print(f"❌ PRODUCTION credentials on LIVE: {result3['error']}")
    
    if working_configs:
        print(f"\n🎉 SUCCESS! Working configurations:")
        for config in working_configs:
            print(f"   {config}")
            
        print(f"\n🚀 YOUR PHONEPE PG IS READY!")
        print(f"💰 You can start accepting payments!")
        
        if result3['success']:
            print(f"\n🔥 PRODUCTION IS LIVE! Use these settings:")
            print(f"   - Environment: PRODUCTION")
            print(f"   - Client ID: {prod_creds['client_id']}")
            print(f"   - Merchant ID: {prod_creds['merchant_id']}")
        elif result2['success']:
            print(f"\n🧪 Use UAT for testing, contact PhonePe for production activation:")
            print(f"   - Environment: UAT") 
            print(f"   - Use production credentials on UAT endpoint")
        elif result1['success']:
            print(f"\n🧪 Use test credentials for safe testing:")
            print(f"   - Environment: UAT")
            print(f"   - Use test credentials")
            
    else:
        print(f"\n⚠️ All configurations need PhonePe support attention")
        print(f"📞 Contact PhonePe support immediately with:")
        print(f"   - Merchant ID: M22KEWU5BO1I2") 
        print(f"   - All credentials getting errors")
        print(f"   - Request immediate activation for Standard Checkout API")
    
    print(f"{'=' * 60}")

def test_payment_endpoint(creds, endpoint, name):
    """Test a specific endpoint with specific credentials"""
    print(f"🔄 Testing {name}...")
    print(f"   Client ID: {creds['client_id']}")
    print(f"   Merchant ID: {creds['merchant_id']}")
    print(f"   Endpoint: {endpoint}")
    
    transaction_id = f"OKPUJA_{uuid.uuid4().hex[:12].upper()}"
    
    payload = {
        "merchantId": creds['merchant_id'],
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
    string_to_sign = payload_base64 + endpoint_path + creds['salt_key']
    signature = hashlib.sha256(string_to_sign.encode()).hexdigest()
    x_verify = signature + "###1"
    
    headers = {
        "Content-Type": "application/json",
        "X-VERIFY": x_verify,
        "X-MERCHANT-ID": creds['merchant_id'],
        "Accept": "application/json"
    }
    
    request_body = {
        "request": payload_base64
    }
    
    try:
        response = requests.post(endpoint, headers=headers, json=request_body, timeout=30)
        
        print(f"   📡 Status: {response.status_code}")
        print(f"   📡 Response: {response.text[:100]}...")
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success') and 'data' in data:
                instrument_response = data['data'].get('instrumentResponse', {})
                redirect_info = instrument_response.get('redirectInfo', {})
                payment_url = redirect_info.get('url')
                
                if payment_url:
                    print(f"   ✅ SUCCESS! Payment URL generated")
                    return {
                        'success': True,
                        'url': payment_url,
                        'transaction_id': transaction_id
                    }
                else:
                    print(f"   ❌ No payment URL in response")
                    return {'success': False, 'error': 'No payment URL'}
            else:
                error_msg = data.get('message', 'Unknown error')
                print(f"   ❌ Payment failed: {error_msg}")
                return {'success': False, 'error': error_msg}
                
        elif response.status_code == 400:
            try:
                error_data = response.json()
                error_code = error_data.get('code', '')
                error_message = error_data.get('message', '')
                print(f"   ❌ Error: {error_code} - {error_message}")
                return {'success': False, 'error': f"{error_code} - {error_message}"}
            except:
                print(f"   ❌ Bad request: {response.text}")
                return {'success': False, 'error': f"Bad request: {response.status_code}"}
        else:
            print(f"   ❌ HTTP {response.status_code}")
            return {'success': False, 'error': f"HTTP {response.status_code}"}
                
    except Exception as e:
        print(f"   ❌ Request error: {e}")
        return {'success': False, 'error': str(e)}

if __name__ == "__main__":
    test_exact_credentials()
