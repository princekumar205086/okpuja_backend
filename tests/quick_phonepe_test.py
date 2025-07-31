#!/usr/bin/env python3
"""
Quick PhonePe Test Script
"""

import os
import sys
import django

# Add current directory to path
sys.path.insert(0, '.')

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

def test_phonepe():
    from django.conf import settings
    
    print("=== PHONEPE CREDENTIALS TEST ===")
    print(f"Environment: {getattr(settings, 'PHONEPE_ENV', 'Not set')}")
    print(f"Client ID: {getattr(settings, 'PHONEPE_CLIENT_ID', 'Not set')[:25]}...")
    print(f"Merchant ID: {getattr(settings, 'PHONEPE_MERCHANT_ID', 'Not set')}")
    
    try:
        from payments.phonepe_client import PhonePePaymentClient
        
        client = PhonePePaymentClient()
        print("\n=== CLIENT TEST ===")
        print("✓ Client initialized")
        print(f"Environment: {client.environment}")
        print(f"Base URL: {client.base_url}")
        
        # Test OAuth
        print("\n=== OAUTH TEST ===")
        token = client.get_access_token()
        if token:
            print("✓ OAuth successful")
            print(f"Token: {token[:40]}...")
            
            # Test payment URL creation
            print("\n=== PAYMENT URL TEST ===")
            import time
            merchant_order_id = f'OKPUJA_TEST_{int(time.time())}'
            
            response = client.create_payment_url(
                merchant_order_id=merchant_order_id,
                amount=10000,  # Rs 100 in paisa
                redirect_url='https://okpuja.com/payment-success'
            )
            
            if response.get('success'):
                print("✓ Payment URL creation successful")
                if response.get('payment_url'):
                    print(f"✓ Payment URL: {response['payment_url'][:60]}...")
                    print("\n🎉 PHONEPE INTEGRATION WORKING!")
                    print("✅ You can get payment URLs from PhonePe UAT")
                else:
                    print("⚠ Payment successful but no URL returned")
                    print("Response:", response)
            else:
                print(f"✗ Payment URL creation failed: {response.get('error')}")
        else:
            print("✗ OAuth failed")
            
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_phonepe()
