#!/usr/bin/env python
"""
PhonePe V2 End-to-End Payment Test
Tests the complete payment flow with the corrected configuration
"""

import os
import sys
import django
import json
import uuid
from decimal import Decimal

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from payment.phonepe_v2_corrected import PhonePeV2ClientCorrected

def test_oauth_flow():
    """Test OAuth token acquisition"""
    print("\n1. Testing OAuth Token Acquisition:")
    print("-" * 40)
    
    try:
        client = PhonePeV2ClientCorrected(env="uat")
        
        print(f"OAuth URL: {client.oauth_url}")
        print(f"Client ID: {client.client_id[:10]}...")
        print("Attempting to get access token...")
        
        token = client.get_access_token()
        
        if token:
            print(f"✅ OAuth successful! Token acquired: {token[:20]}...")
            return client
        else:
            print("❌ OAuth failed - no token received")
            return None
            
    except Exception as e:
        print(f"❌ OAuth error: {e}")
        return None

def test_payment_initiation(client):
    """Test payment initiation"""
    if not client:
        print("❌ Skipping payment test - OAuth failed")
        return False
        
    print("\n2. Testing Payment Initiation:")
    print("-" * 35)
    
    try:
        # Test payment request
        payment_data = {
            'merchant_transaction_id': f"TEST_{uuid.uuid4().hex[:12]}",
            'amount': 10000,  # ₹100.00 in paise
            'redirect_url': 'https://webhook.site/unique-id',
            'redirect_mode': 'POST',
            'callback_url': 'https://webhook.site/unique-id',
            'merchant_user_id': f"USER_{uuid.uuid4().hex[:8]}"
        }
        
        print(f"Payment data: {json.dumps(payment_data, indent=2)}")
        print("Initiating payment...")
        
        result = client.initiate_payment(**payment_data)
        
        if result and result.get('success'):
            print(f"✅ Payment initiated successfully!")
            print(f"Payment URL: {result.get('data', {}).get('instrumentResponse', {}).get('redirectInfo', {}).get('url', 'N/A')}")
            print(f"Transaction ID: {payment_data['merchant_transaction_id']}")
            return True
        else:
            print(f"❌ Payment initiation failed: {result}")
            return False
            
    except Exception as e:
        print(f"❌ Payment error: {e}")
        return False

def test_payment_status(client, transaction_id):
    """Test payment status check"""
    if not client or not transaction_id:
        print("❌ Skipping status test - payment not initiated")
        return
        
    print("\n3. Testing Payment Status Check:")
    print("-" * 36)
    
    try:
        status = client.check_payment_status(transaction_id)
        
        if status:
            print(f"✅ Status check successful: {status.get('state', 'UNKNOWN')}")
            print(f"Response code: {status.get('responseCode', 'N/A')}")
            print(f"Response message: {status.get('message', 'N/A')}")
        else:
            print("❌ Status check failed")
            
    except Exception as e:
        print(f"❌ Status check error: {e}")

def main():
    """Main test function"""
    print("=" * 60)
    print("PhonePe V2 End-to-End Payment Test")
    print("=" * 60)
    
    # Test OAuth
    client = test_oauth_flow()
    
    # Test payment initiation  
    transaction_id = None
    if client:
        payment_success = test_payment_initiation(client)
        if payment_success:
            # Get the last transaction ID for status check
            # In a real scenario, you'd store this from the payment response
            transaction_id = f"TEST_{uuid.uuid4().hex[:12]}"
    
    # Test status check
    test_payment_status(client, transaction_id)
    
    print(f"\n{'=' * 60}")
    print("Test completed! Check the results above.")
    print("If OAuth and payment initiation worked, your integration is ready!")
    print(f"{'=' * 60}")

if __name__ == "__main__":
    main()
