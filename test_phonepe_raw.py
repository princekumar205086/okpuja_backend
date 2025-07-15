#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings
import json
import requests
import base64
import hashlib

def test_phonepe_api_raw():
    """Test PhonePe API with raw HTTP request"""
    print("🧪 Testing PhonePe API with Raw Request...")
    
    try:
        # Get configuration
        merchant_id = settings.PHONEPE_MERCHANT_ID
        merchant_key = settings.PHONEPE_MERCHANT_KEY
        salt_index = settings.PHONEPE_SALT_INDEX
        base_url = settings.PHONEPE_BASE_URL
        
        print(f"Merchant ID: {merchant_id}")
        print(f"Base URL: {base_url}")
        print(f"Salt Index: {salt_index}")
        
        # Create payload
        payload = {
            "merchantId": merchant_id,
            "merchantTransactionId": "TEST123456789",
            "merchantUserId": "user_1",
            "amount": 50000,  # 500.00 INR in paisa
            "redirectUrl": "http://127.0.0.1:8000/api/payments/webhook/phonepe/",
            "redirectMode": "POST",
            "callbackUrl": "http://127.0.0.1:8000/api/payments/webhook/phonepe/",
            "mobileNumber": "9000000000",
            "paymentInstrument": {
                "type": "PAY_PAGE"
            }
        }
        
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        # Encode payload
        data = base64.b64encode(json.dumps(payload).encode()).decode()
        print(f"Base64 Data: {data}")
        
        # Generate checksum
        endpoint = "/pg/v1/pay"
        checksum_str = data + endpoint + merchant_key
        checksum = hashlib.sha256(checksum_str.encode()).hexdigest() + '###' + str(salt_index)
        print(f"Checksum: {checksum}")
        
        # Prepare request
        final_payload = {"request": data}
        headers = {
            'Content-Type': 'application/json',
            'X-VERIFY': checksum,
            'X-MERCHANT-ID': merchant_id,
        }
        
        api_url = f"{base_url}/pg/v1/pay"
        print(f"API URL: {api_url}")
        
        # Make API call
        print("Making API call...")
        response = requests.post(api_url, headers=headers, json=final_payload, timeout=30)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                print(f"✅ Parsed Response: {json.dumps(response_data, indent=2)}")
                
                if response_data.get('success'):
                    print("✅ Payment initiation successful!")
                    payment_url = response_data.get('data', {}).get('instrumentResponse', {}).get('redirectInfo', {}).get('url')
                    if payment_url:
                        print(f"✅ Payment URL: {payment_url}")
                else:
                    print(f"❌ Payment failed: {response_data.get('message', 'Unknown error')}")
                    
            except json.JSONDecodeError:
                print(f"❌ Could not parse JSON response: {response.text}")
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_phonepe_api_raw()
