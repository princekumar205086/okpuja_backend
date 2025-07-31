#!/usr/bin/env python
"""
PhonePe V2 Production Test with Correct Standard Checkout Endpoints
Testing with the official Standard Checkout API endpoints
"""

import json
import uuid
import hashlib
import base64
import requests

# Your PRODUCTION credentials
CLIENT_ID = 'SU2507311635477696235898'
CLIENT_SECRET = '1f59672d-e31c-4898-9caf-19ab54bcaaab'  # API Key
MERCHANT_ID = 'M22KEWU5BO1I2'
SALT_KEY = '1f59672d-e31c-4898-9caf-19ab54bcaaab'  # API Key as salt
SALT_INDEX = '1'

# Correct Standard Checkout Production endpoints
PAYMENT_URL = "https://api.phonepe.com/apis/hermes/pg/v1/pay"
STATUS_URL_BASE = "https://api.phonepe.com/apis/hermes/pg/v1/status"

# Alternative endpoints to try
ALTERNATIVE_ENDPOINTS = [
    "https://api.phonepe.com/apis/pg-sandbox/pg/v1/pay",  # Sandbox style
    "https://api.phonepe.com/pg/v1/pay",  # Direct path
    "https://mercury.phonepe.com/v1/charge",  # Mercury gateway
    "https://api.phonepe.com/v1/pay",  # Simple path
]

def create_payment_payload():
    """Create a production payment payload"""
    
    merchant_transaction_id = f"OKPUJA_{uuid.uuid4().hex[:12].upper()}"
    merchant_user_id = f"USER_{uuid.uuid4().hex[:8].upper()}"
    
    payload = {
        "merchantId": MERCHANT_ID,  
        "merchantTransactionId": merchant_transaction_id,
        "merchantUserId": merchant_user_id,
        "amount": 10000,  # ₹100.00 in paise
        "redirectUrl": "https://okpuja.com/payment/success",
        "redirectMode": "POST", 
        "callbackUrl": "https://okpuja.com/api/payment/webhook/phonepe/v2/",
        "paymentInstrument": {
            "type": "PAY_PAGE"
        }
    }
    
    return payload, merchant_transaction_id

def create_signature(payload, endpoint="/pg/v1/pay"):
    """Create X-VERIFY signature"""
    
    # Convert payload to base64
    payload_json = json.dumps(payload, separators=(',', ':'))
    payload_base64 = base64.b64encode(payload_json.encode()).decode()
    
    # Create string to sign: base64Payload + endpoint + saltKey  
    string_to_sign = payload_base64 + endpoint + SALT_KEY
    
    # Create SHA256 hash
    signature = hashlib.sha256(string_to_sign.encode()).hexdigest()
    
    # Final signature format
    x_verify = signature + "###" + SALT_INDEX
    
    return payload_base64, x_verify

def test_multiple_endpoints():
    """Test multiple possible production endpoints"""
    print("=" * 80)
    print("PhonePe V2 Production Endpoint Testing")
    print("🔍 Trying multiple endpoint formats to find the working one")
    print("=" * 80)
    
    # Create payment payload
    payload, transaction_id = create_payment_payload()
    
    all_endpoints = [PAYMENT_URL] + ALTERNATIVE_ENDPOINTS
    
    for i, endpoint_url in enumerate(all_endpoints, 1):
        print(f"\n{i}. Testing Endpoint: {endpoint_url}")
        print("-" * (len(endpoint_url) + 20))
        
        # Create signature based on endpoint path
        if "/pg/v1/pay" in endpoint_url:
            endpoint_path = "/pg/v1/pay"
        elif "/v1/pay" in endpoint_url:
            endpoint_path = "/v1/pay"
        elif "/v1/charge" in endpoint_url:
            endpoint_path = "/v1/charge"
        else:
            endpoint_path = "/pg/v1/pay"  # Default
        
        payload_base64, x_verify = create_signature(payload, endpoint_path)
        
        headers = {
            "Content-Type": "application/json",
            "X-VERIFY": x_verify,
            "X-MERCHANT-ID": MERCHANT_ID,
            "Accept": "application/json"
        }
        
        request_body = {
            "request": payload_base64
        }
        
        try:
            response = requests.post(endpoint_url, headers=headers, json=request_body, timeout=30)
            
            print(f"Status Code: {response.status_code}")
            
            if response.status_code == 200:
                print("✅ SUCCESS! This endpoint works!")
                try:
                    data = response.json()
                    print(f"Response: {json.dumps(data, indent=2)}")
                    
                    # Check for payment URL
                    if data.get('success') and 'data' in data:
                        instrument_response = data['data'].get('instrumentResponse', {})
                        redirect_info = instrument_response.get('redirectInfo', {})
                        payment_url = redirect_info.get('url')
                        
                        if payment_url:
                            print(f"\n🎉 LIVE PAYMENT URL GENERATED:")
                            print(f"🌐 URL: {payment_url}")
                            print(f"💳 Transaction ID: {transaction_id}")
                            print(f"\n✅ WORKING ENDPOINT: {endpoint_url}")
                            return True, endpoint_url, transaction_id
                            
                except Exception as e:
                    print(f"Response parsing error: {e}")
                    print(f"Raw response: {response.text}")
                    
            elif response.status_code == 400:
                print("⚠️  Bad Request - endpoint exists but request format issue")
                try:
                    error_data = response.json()
                    print(f"Error: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"Raw response: {response.text}")
                    
            elif response.status_code == 404:
                print("❌ Endpoint not found")
                
            elif response.status_code == 401:
                print("⚠️  Unauthorized - endpoint exists but auth issue")
                print(f"Response: {response.text}")
                
            else:
                print(f"⚠️  Status {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Request error: {e}")
    
    return False, None, None

def test_with_different_payload_formats():
    """Test with different payload formats that PhonePe might accept"""
    print(f"\n{'=' * 80}")
    print("Testing Different Payload Formats")
    print("=" * 80)
    
    merchant_transaction_id = f"OKPUJA_{uuid.uuid4().hex[:12].upper()}"
    
    # Try different payload formats
    payload_formats = [
        # Standard format
        {
            "merchantId": MERCHANT_ID,
            "merchantTransactionId": merchant_transaction_id,
            "merchantUserId": f"USER_{uuid.uuid4().hex[:8].upper()}",
            "amount": 10000,
            "redirectUrl": "https://okpuja.com/payment/success",
            "redirectMode": "POST",
            "callbackUrl": "https://okpuja.com/api/payment/webhook/phonepe/v2/",
            "paymentInstrument": {
                "type": "PAY_PAGE"
            }
        },
        # Alternative format with merchant_id instead of merchantId
        {
            "merchant_id": MERCHANT_ID,
            "merchant_transaction_id": merchant_transaction_id,
            "merchant_user_id": f"USER_{uuid.uuid4().hex[:8].upper()}",
            "amount": 10000,
            "redirect_url": "https://okpuja.com/payment/success",
            "redirect_mode": "POST",
            "callback_url": "https://okpuja.com/api/payment/webhook/phonepe/v2/",
            "payment_instrument": {
                "type": "PAY_PAGE"
            }
        }
    ]
    
    for i, payload in enumerate(payload_formats, 1):
        print(f"\n{i}. Testing Payload Format {i}")
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        payload_base64, x_verify = create_signature(payload)
        
        headers = {
            "Content-Type": "application/json",
            "X-VERIFY": x_verify,
            "X-MERCHANT-ID": MERCHANT_ID,
            "Accept": "application/json"
        }
        
        request_body = {
            "request": payload_base64
        }
        
        try:
            response = requests.post(PAYMENT_URL, headers=headers, json=request_body, timeout=30)
            print(f"Status: {response.status_code}")
            print(f"Response: {response.text}")
            
            if response.status_code == 200:
                print("✅ This payload format works!")
                return True
                
        except Exception as e:
            print(f"Error: {e}")
    
    return False

if __name__ == "__main__":
    print("🚀 PhonePe V2 Production Integration - Comprehensive Test")
    print("💳 Finding the correct endpoint and format for your credentials")
    
    # Test multiple endpoints
    success, working_endpoint, transaction_id = test_multiple_endpoints()
    
    if not success:
        # Try different payload formats
        print("\n🔄 Trying different payload formats...")
        format_success = test_with_different_payload_formats()
    
    print(f"\n{'=' * 80}")
    if success:
        print("🎉 CONGRATULATIONS! Found a working endpoint!")
        print(f"✅ Working Endpoint: {working_endpoint}")
        print(f"💳 Transaction ID: {transaction_id}")
        print("🚀 Your PhonePe PG is ready!")
        
    else:
        print("⚠️  No working endpoint found with current configuration")
        print("\n📋 Possible issues:")
        print("1. 🔑 Merchant credentials need activation by PhonePe")
        print("2. 🌐 Production endpoints might be different")
        print("3. 📝 Payload format might need adjustment")
        print("4. 🔒 Additional authentication might be required")
        
        print("\n📞 Next Steps:")
        print("1. Contact PhonePe support to verify merchant activation")
        print("2. Ask for correct production API endpoints")
        print("3. Verify if additional setup is needed")
        
    print(f"{'=' * 80}")
