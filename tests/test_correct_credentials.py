#!/usr/bin/env python
"""
PhonePe V2 Test with Correct Credentials
Direct test with the credentials from your dashboard
"""

import json
import uuid
import hashlib
import base64
import requests
from datetime import datetime

# Your correct credentials from PhonePe Business Dashboard
CLIENT_ID = 'TEST-M22KEWU5BO1I2_25070'
CLIENT_SECRET = 'MTgwNDU0MjctNTEzMy00ZjEzLTgwMzUtNDllNDZkZDAzYThh'
MERCHANT_ID = 'M22KEWU5BO1I2'  # Extracted from client ID
SALT_KEY = 'b9b33b94-4a96-4b47-a7e8-21be9ec83fa4'  # UAT salt key
SALT_INDEX = '1'

def create_payment_payload():
    """Create a test payment payload"""
    
    merchant_transaction_id = f"TEST_{uuid.uuid4().hex[:12]}"
    merchant_user_id = f"USER_{uuid.uuid4().hex[:8]}"
    
    payload = {
        "merchantId": MERCHANT_ID,  
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
    string_to_sign = payload_base64 + endpoint + SALT_KEY
    
    # Create SHA256 hash
    signature = hashlib.sha256(string_to_sign.encode()).hexdigest()
    
    # Final signature format
    x_verify = signature + "###" + SALT_INDEX
    
    return payload_base64, x_verify

def test_oauth():
    """Test OAuth with correct credentials"""
    print("=" * 60)
    print("PhonePe V2 OAuth Test with Correct Credentials")
    print("=" * 60)
    
    oauth_url = "https://api-preprod.phonepe.com/apis/hermes/oauth2/v2/token"
    
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded',
        'X-MERCHANT-ID': MERCHANT_ID,
    }
    
    data = {
        'client_id': CLIENT_ID,
        'client_version': '1',
        'client_secret': CLIENT_SECRET,
        'grant_type': 'client_credentials'
    }
    
    print(f"OAuth URL: {oauth_url}")
    print(f"Client ID: {CLIENT_ID}")
    print(f"Merchant ID: {MERCHANT_ID}")
    print("Testing OAuth...")
    
    try:
        response = requests.post(oauth_url, headers=headers, data=data, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            token_data = response.json()
            access_token = token_data.get('access_token')
            if access_token:
                print(f"✅ OAuth successful! Token: {access_token[:20]}...")
                return access_token
            else:
                print("❌ No access token in response")
                return None
        else:
            print("❌ OAuth failed")
            return None
            
    except Exception as e:
        print(f"❌ OAuth error: {e}")
        return None

def test_direct_payment():
    """Test direct payment with correct credentials"""
    print(f"\n{'=' * 60}")
    print("PhonePe V2 Direct Payment Test with Correct Credentials")
    print("=" * 60)
    
    # Create payment payload
    payload, transaction_id = create_payment_payload()
    payload_base64, x_verify = create_signature(payload)
    
    print(f"\nPayment Details:")
    print(f"Merchant ID: {MERCHANT_ID}")
    print(f"Transaction ID: {transaction_id}")
    print(f"Amount: ₹{payload['amount']/100}")
    
    # Test payment endpoint
    endpoint = "https://api-preprod.phonepe.com/apis/hermes/pg/v1/pay"
    
    headers = {
        "Content-Type": "application/json",
        "X-VERIFY": x_verify,
        "X-MERCHANT-ID": MERCHANT_ID,
        "Accept": "application/json"
    }
    
    request_body = {
        "request": payload_base64
    }
    
    print(f"\nTesting Payment Endpoint: {endpoint}")
    
    try:
        response = requests.post(endpoint, headers=headers, json=request_body, timeout=30)
        
        print(f"Status Code: {response.status_code}")
        
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
                
        else:
            print(f"❌ Payment failed: {response.status_code}")
            print(f"Response: {response.text}")
                
    except Exception as e:
        print(f"❌ Request error: {e}")
    
    return False

if __name__ == "__main__":
    print("Testing PhonePe V2 with your correct credentials from dashboard...")
    
    # Test OAuth first
    access_token = test_oauth()
    
    # Test direct payment
    payment_success = test_direct_payment()
    
    print(f"\n{'=' * 60}")
    if access_token or payment_success:
        print("🎉 SUCCESS! At least one method worked.")
        if access_token:
            print("✅ OAuth working - can use V2 API with authentication")
        if payment_success:
            print("✅ Direct payment working - ready for integration")
    else:
        print("❌ Both OAuth and direct payment failed.")
        print("The merchant account may need additional configuration.")
    print(f"{'=' * 60}")
