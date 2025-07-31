#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from payment.gateways import PhonePeGateway
from payment.models import Payment, PaymentMethod, PaymentStatus
from accounts.models import User
from django.contrib.auth import get_user_model
import json
import requests

def test_phonepe_direct_api():
    """Test PhonePe API directly with minimal payload"""
    print("🧪 Testing PhonePe API Directly...")
    
    try:
        # Create test payment object
        user, created = User.objects.get_or_create(
            email='test@example.com',
            defaults={'username': 'testuser'}
        )
        
        # Create a simple test payment
        payment = Payment.objects.create(
            user=user,
            amount=500.00,
            currency='INR',
            method=PaymentMethod.PHONEPE,
            status=PaymentStatus.PENDING,
            merchant_transaction_id='TEST123456789',
            transaction_id='TEST123456789'
        )
        
        # Test gateway
        gateway = PhonePeGateway()
        
        # Minimal payload
        payload = {
            "merchantId": gateway.merchant_id,
            "merchantTransactionId": payment.merchant_transaction_id,
            "merchantUserId": f"user_{payment.user.id}",
            "amount": int(payment.amount * 100),  # Convert to paisa
            "redirectUrl": "http://127.0.0.1:8000/api/payments/webhook/phonepe/",
            "redirectMode": "POST",
            "callbackUrl": "http://127.0.0.1:8000/api/payments/webhook/phonepe/",
            "mobileNumber": "9000000000",
            "paymentInstrument": {
                "type": "PAY_PAGE"
            }
        }
        
        print(f"Payload: {json.dumps(payload, indent=2)}")
        
        # Encode and create checksum
        import base64
        data = base64.b64encode(json.dumps(payload).encode()).decode()
        checksum = gateway.generate_checksum(data)
        
        print(f"Base64 Data: {data}")
        print(f"Checksum: {checksum}")
        
        # Make direct API call
        final_payload = {"request": data}
        headers = {
            'Content-Type': 'application/json',
            'X-VERIFY': checksum,
        }
        
        api_url = f"{gateway.base_url}/pg/v1/pay"
        print(f"API URL: {api_url}")
        
        response = requests.post(api_url, headers=headers, json=final_payload)
        
        print(f"Response Status: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            response_data = response.json()
            print(f"✅ API Response: {json.dumps(response_data, indent=2)}")
        else:
            print(f"❌ API Error: {response.status_code} - {response.text}")
            
        # Cleanup
        payment.delete()
        if created:
            user.delete()
            
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_phonepe_direct_api()
