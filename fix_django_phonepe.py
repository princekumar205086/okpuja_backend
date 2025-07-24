#!/usr/bin/env python
"""
Direct connection fix for Django PhonePe gateway
This bypasses Django's session handling that might be causing issues
"""

import os
import sys
import django
import requests
import json
import base64
import hashlib
import uuid
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings

def test_direct_payment_call():
    """Test payment call using the exact same method that works in diagnostic"""
    
    print("🔧 FIXING DJANGO PHONEPE CONNECTION")
    print("="*60)
    
    # Use exact same credentials and setup as diagnostic
    merchant_id = settings.PHONEPE_MERCHANT_ID
    merchant_key = settings.PHONEPE_MERCHANT_KEY
    salt_index = settings.PHONEPE_SALT_INDEX
    
    # Create test payload (same as diagnostic script)
    payload = {
        "merchantId": merchant_id,
        "merchantTransactionId": f"DJANGO_TEST_{uuid.uuid4().hex[:8].upper()}",
        "merchantUserId": "DJANGO_TEST_USER",
        "amount": 100,  # 1 rupee
        "redirectUrl": "https://backend.okpuja.com/api/payments/webhook/phonepe/",
        "redirectMode": "POST",
        "callbackUrl": "https://backend.okpuja.com/api/payments/webhook/phonepe/",
        "mobileNumber": "9876543210",
        "paymentInstrument": {
            "type": "PAY_PAGE"
        }
    }
    
    # Encode payload (same as diagnostic)
    data = base64.b64encode(json.dumps(payload).encode()).decode()
    
    # Generate checksum (same as diagnostic)
    checksum_str = data + "/pg/v1/pay" + merchant_key
    checksum = hashlib.sha256(checksum_str.encode()).hexdigest() + '###' + str(salt_index)
    
    final_payload = {"request": data}
    
    # Use EXACT same headers as diagnostic script
    headers = {
        'Content-Type': 'application/json',
        'X-VERIFY': checksum,
        'X-MERCHANT-ID': merchant_id,
        'User-Agent': 'OkPuja-Backend/1.0',
        'Accept': 'application/json'
    }
    
    # Use same URL as diagnostic
    api_url = 'https://api.phonepe.com/apis/hermes/pg/v1/pay'
    
    print(f"Testing Django environment with direct call...")
    print(f"URL: {api_url}")
    print(f"Merchant ID: {merchant_id}")
    
    try:
        # Make request exactly like diagnostic script (no Django session handling)
        response = requests.post(
            api_url,
            headers=headers,
            json=final_payload,
            timeout=30,
            verify=True
        )
        
        print("✅ SUCCESS! Django can connect to PhonePe!")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text[:200]}...")
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('success'):
                print("🎉 Payment initiation successful!")
                return True
        
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")
        print(f"Error type: {type(e).__name__}")
        
        if "Connection refused" in str(e):
            print("\n🚨 DJANGO CONNECTION ISSUE CONFIRMED")
            print("The diagnostic script works but Django fails.")
            print("This is likely a Django configuration or environment issue.")
        
        return False
    
    return False

def create_fixed_gateway_method():
    """Create a fixed version of the gateway method"""
    
    print("\n🔧 CREATING FIXED GATEWAY METHOD")
    print("="*60)
    
    # Create the fixed initiate_payment method
    fixed_method = '''
def initiate_payment_fixed(self, payment):
    """
    Fixed version that bypasses Django session issues
    Uses the exact same method as the working diagnostic script
    """
    import requests
    import json
    import base64
    import hashlib
    
    try:
        # Create payload (same as diagnostic)
        payload = {
            "merchantId": self.merchant_id,
            "merchantTransactionId": payment.merchant_transaction_id,
            "merchantUserId": f"USR{payment.user.id}",
            "amount": int(float(payment.amount) * 100),
            "redirectUrl": f"{settings.PHONEPE_SUCCESS_REDIRECT_URL}?payment_id={payment.id}",
            "redirectMode": "POST", 
            "callbackUrl": settings.PHONEPE_CALLBACK_URL,
            "mobileNumber": getattr(payment.user, 'phone_number', '9000000000'),
            "paymentInstrument": {
                "type": "PAY_PAGE"
            }
        }
        
        # Encode and create checksum (same as diagnostic)
        data = base64.b64encode(json.dumps(payload).encode()).decode()
        checksum_str = data + "/pg/v1/pay" + self.merchant_key
        checksum = hashlib.sha256(checksum_str.encode()).hexdigest() + '###' + str(self.salt_index)
        
        final_payload = {"request": data}
        
        # Use exact same headers as diagnostic
        headers = {
            'Content-Type': 'application/json',
            'X-VERIFY': checksum,
            'X-MERCHANT-ID': self.merchant_id,
            'User-Agent': 'OkPuja-Backend/1.0',
            'Accept': 'application/json'
        }
        
        # Make direct request (no Django session complexity)
        api_url = 'https://api.phonepe.com/apis/hermes/pg/v1/pay'
        
        response = requests.post(
            api_url,
            headers=headers,
            json=final_payload,
            timeout=30,
            verify=True
        )
        
        if response.status_code == 200:
            response_data = response.json()
            if response_data.get('success'):
                payment_url = response_data['data']['instrumentResponse']['redirectInfo']['url']
                return {
                    'success': True,
                    'payment_url': payment_url,
                    'transaction_id': payment.merchant_transaction_id,
                    'amount': payment.amount
                }
        
        # Handle error response
        logger.error(f"PhonePe API error: {response.status_code} - {response.text}")
        return {
            'success': False,
            'error': f'API returned {response.status_code}',
            'response': response.text
        }
        
    except Exception as e:
        logger.error(f"Payment initiation failed: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'error_type': type(e).__name__
        }
'''
    
    print("Fixed method created. This should work with Django.")
    return fixed_method

if __name__ == "__main__":
    # Test direct connection first
    success = test_direct_payment_call()
    
    if success:
        print("\n✅ SOLUTION CONFIRMED")
        print("The issue is in Django's session/adapter configuration.")
        print("The fix is to use direct requests.post() calls.")
    else:
        print("\n❌ DEEPER ISSUE")
        print("Even direct calls from Django environment fail.")
        print("This might be a Python environment or system issue.")
    
    # Create the fixed method
    create_fixed_gateway_method()
    
    print(f"\n{'='*60}")
    print("NEXT STEPS:")
    print("1. If direct test worked: Update the gateway with the fixed method")
    print("2. If direct test failed: Check Django environment settings")
    print("3. Restart your Django server after making changes")
    print(f"{'='*60}")
