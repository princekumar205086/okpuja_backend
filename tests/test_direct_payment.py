#!/usr/bin/env python
"""
PhonePe V2 Direct Payment Test (without OAuth)
Some PhonePe V2 implementations might use direct payment without OAuth
"""

import os
import sys
import django
import json
import uuid
import hashlib
import base64
from datetime import datetime

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings
import requests

def create_payment_payload():
    """Create a test payment payload according to PhonePe V2 docs"""
    
    merchant_transaction_id = f"TEST_{uuid.uuid4().hex[:12]}"
    merchant_user_id = f"USER_{uuid.uuid4().hex[:8]}"
    
    payload = {
        "merchantId": settings.PHONEPE_MERCHANT_ID,  
        "merchantTransactionId": merchant_transaction_id,
        "merchantUserId": merchant_user_id,
        "amount": 10000,  # ₹100.00 in paise
        "redirectUrl": "https://webhook.site/redirect",
        "redirectMode": "POST",
        "callbackUrl": "https://webhook.site/callback",
        "paymentInstrument": {
            "type": "PAY_PAGE"
        }
    }
    
    return payload, merchant_transaction_id

def create_signature(payload, endpoint="/pg/v1/pay"):
    """Create X-VERIFY signature for PhonePe V2"""
    
    # Convert payload to base64
    payload_json = json.dumps(payload)
    payload_base64 = base64.b64encode(payload_json.encode()).decode()
    
    # Create string to sign: base64Payload + endpoint + saltKey  
    # Note: For UAT, salt key might be different or not required
    salt_key = getattr(settings, 'PHONEPE_SALT_KEY', '')  # Usually empty for UAT
    string_to_sign = payload_base64 + endpoint + salt_key
    
    # Create SHA256 hash
    signature = hashlib.sha256(string_to_sign.encode()).hexdigest()
    
    # Final signature format
    x_verify = signature + "###" + str(getattr(settings, 'PHONEPE_SALT_INDEX', '1'))
    
    return payload_base64, x_verify

def test_direct_payment():
    """Test direct payment call to PhonePe V2 without OAuth"""
    
    print("=" * 60)
    print("PhonePe V2 Direct Payment Test (No OAuth)")
    print("=" * 60)
    
    # Create payment payload
    payload, transaction_id = create_payment_payload()
    payload_base64, x_verify = create_signature(payload)
    
    print(f"\n1. Payment Request Details:")
    print("-" * 30)
    print(f"Merchant ID: {payload['merchantId']}")
    print(f"Transaction ID: {transaction_id}")
    print(f"Amount: ₹{payload['amount']/100}")
    print(f"Payload: {json.dumps(payload, indent=2)}")
    
    # Test different payment endpoints
    endpoints = [
        "https://api-preprod.phonepe.com/apis/hermes/pg/v1/pay",
        "https://api-preprod.phonepe.com/apis/pg-sandbox/pg/v1/pay", 
        "https://api-preprod.phonepe.com/v1/pay"
    ]
    
    headers = {
        "Content-Type": "application/json",
        "X-VERIFY": x_verify,
        "X-MERCHANT-ID": settings.PHONEPE_MERCHANT_ID,
        "Accept": "application/json"
    }
    
    request_body = {
        "request": payload_base64
    }
    
    for endpoint in endpoints:
        print(f"\n2. Testing Endpoint: {endpoint}")
        print("-" * (25 + len(endpoint)))
        
        try:
            response = requests.post(
                endpoint,
                headers=headers,
                json=request_body,
                timeout=30
            )
            
            print(f"Status Code: {response.status_code}")
            print(f"Headers: {dict(response.headers)}")
            
            if response.status_code == 200:
                print("✅ Payment request successful!")
                try:
                    data = response.json()
                    print(f"Response: {json.dumps(data, indent=2)}")
                    
                    # Check if we got a payment URL
                    if 'data' in data and 'instrumentResponse' in data['data']:
                        payment_url = data['data']['instrumentResponse'].get('redirectInfo', {}).get('url')
                        if payment_url:
                            print(f"✅ Payment URL: {payment_url}")
                            return True
                            
                except Exception as e:
                    print(f"Response parsing error: {e}")
                    print(f"Raw response: {response.text}")
                    
            elif response.status_code == 400:
                print("⚠️  Bad Request - check payload format")
                print(f"Response: {response.text}")
            elif response.status_code == 401:
                print("⚠️  Unauthorized - check credentials/signature")
                print(f"Response: {response.text}")
            elif response.status_code == 404:
                print("❌ Endpoint not found")
            else:
                print(f"⚠️  Unexpected status: {response.status_code}")
                print(f"Response: {response.text}")
                
        except Exception as e:
            print(f"❌ Request error: {e}")
    
    return False

if __name__ == "__main__":
    success = test_direct_payment()
    
    print(f"\n{'=' * 60}")
    if success:
        print("🎉 Direct payment test successful!")
        print("PhonePe V2 might not require OAuth for basic operations.")
    else:
        print("❌ Direct payment test failed.")
        print("Check credentials, endpoints, and signature generation.")
    print(f"{'=' * 60}")
