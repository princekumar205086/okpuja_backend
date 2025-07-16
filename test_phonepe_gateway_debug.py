#!/usr/bin/env python3
import os
import django
import json
import hashlib
import base64
import requests
import uuid
import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings
from payment.gateways import PhonePeGateway

def test_phonepe_gateway_direct():
    """Test PhonePe gateway directly with same parameters as production payment"""
    
    print("🧪 TESTING PHONEPE GATEWAY DIRECTLY")
    print("=" * 50)
    
    # Create a mock payment object with the same data
    class MockUser:
        id = 2
        phone_number = "9000000000"
    
    class MockPayment:
        def __init__(self):
            self.id = 999
            self.user = MockUser()
            self.amount = 4990.00  # ₹4990 as found in cart 28
            self.merchant_transaction_id = f"TRX{datetime.datetime.now().strftime('%Y%m%d')}{str(uuid.uuid4()).split('-')[0].upper()}"
            self.transaction_id = self.merchant_transaction_id
            self.gateway_response = None
        
        def save(self):
            print(f"Mock save called with gateway_response: {self.gateway_response}")
    
    # Create gateway and mock payment
    gateway = PhonePeGateway()
    payment = MockPayment()
    
    print(f"Payment details:")
    print(f"  Amount: ₹{payment.amount}")
    print(f"  Transaction ID: {payment.merchant_transaction_id}")
    print(f"  User ID: {payment.user.id}")
    print(f"  Phone: {payment.user.phone_number}")
    
    print(f"\nPhonePe Gateway settings:")
    print(f"  Merchant ID: {gateway.merchant_id}")
    print(f"  Base URL: {gateway.base_url}")
    print(f"  Salt Index: {gateway.salt_index}")
    
    try:
        print(f"\n🚀 Calling PhonePe gateway...")
        result = gateway.initiate_payment(payment)
        print(f"✅ Success! Result: {json.dumps(result, indent=2)}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        print(f"❌ Type: {type(e).__name__}")
        
        # Let's also test the raw API call
        print(f"\n🔧 Testing raw PhonePe API call...")
        test_raw_phonepe_api(gateway, payment)

def test_raw_phonepe_api(gateway, payment):
    """Test the raw PhonePe API call to see exact response"""
    
    try:
        # Prepare payload exactly as gateway does
        callback_url = f"{settings.PHONEPE_CALLBACK_URL}"
        redirect_url = f"{settings.PHONEPE_SUCCESS_REDIRECT_URL}?payment_id={payment.id}"
        
        payload = {
            "merchantId": gateway.merchant_id,
            "merchantTransactionId": payment.merchant_transaction_id,
            "merchantUserId": f"USR{payment.user.id}",
            "amount": int(payment.amount * 100),  # Convert to paisa
            "redirectUrl": redirect_url,
            "redirectMode": "POST",
            "callbackUrl": callback_url,
            "mobileNumber": getattr(payment.user, 'phone_number', None) or "9000000000",
            "paymentInstrument": {
                "type": "PAY_PAGE"
            }
        }
        
        print(f"Raw payload: {json.dumps(payload, indent=2)}")
        
        # Encode payload
        data = base64.b64encode(json.dumps(payload).encode()).decode()
        checksum = gateway.generate_checksum(data)
        
        final_payload = {"request": data}
        
        headers = {
            'Content-Type': 'application/json',
            'X-VERIFY': checksum,
            'X-MERCHANT-ID': gateway.merchant_id,
        }
        
        print(f"Headers: {json.dumps(headers, indent=2)}")
        print(f"Final payload: {json.dumps(final_payload, indent=2)}")
        
        # Make API call
        api_url = f"{gateway.base_url}/pg/v1/pay"
        print(f"API URL: {api_url}")
        
        response = requests.post(api_url, headers=headers, json=final_payload, timeout=30)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            try:
                response_data = response.json()
                print(f"Response JSON: {json.dumps(response_data, indent=2)}")
            except:
                print("Could not parse response as JSON")
        
    except Exception as e:
        print(f"Raw API test failed: {e}")

if __name__ == "__main__":
    test_phonepe_gateway_direct()
