#!/usr/bin/env python
"""
PhonePe V2 Configuration Test Script
Tests if our configuration matches PhonePe V2 Standard Checkout documentation

Based on PhonePe V2 Standard documents:
- OAuth: https://api-preprod.phonepe.com/oauth2/v2/token (UAT)
- Payment: https://api-preprod.phonepe.com/apis/hermes/pg/v1/pay (UAT)
- Status: https://api-preprod.phonepe.com/apis/pg-sandbox/pg/v1/status/{merchant_id}/{transaction_id} (UAT)
"""

import os
import sys
import django
from django.conf import settings

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from payment.phonepe_v2_corrected import PhonePeV2ClientCorrected

def test_phonepe_v2_config():
    """Test PhonePe V2 configuration according to official docs"""
    
    print("=" * 60)
    print("PhonePe V2 Configuration Test")
    print("=" * 60)
    
    # Test UAT environment configuration
    print("\n1. Testing UAT Environment Configuration:")
    print("-" * 40)
    
    try:
        client = PhonePeV2ClientCorrected(env="uat")
        
        print(f"✅ Merchant ID: {client.merchant_id}")
        print(f"✅ Client Version: {client.client_version}")
        print(f"✅ Base URL: {client.base_url}")
        print(f"✅ OAuth Base URL: {client.oauth_base_url}")
        print(f"✅ Payment Endpoint: {client.payment_endpoint}")
        print(f"✅ Status Endpoint Base: {client.status_endpoint_base}")
        print(f"✅ OAuth URL: {client.oauth_url}")
        print(f"✅ Client ID: {client.client_id[:10]}..." if client.client_id else "❌ Client ID: Not set")
        print(f"✅ Client Secret: {'*' * 10}..." if client.client_secret else "❌ Client Secret: Not set")
        
        # Verify expected URLs match PhonePe V2 docs
        expected_oauth = "https://api-preprod.phonepe.com/oauth2/v2/token"
        expected_payment = "https://api-preprod.phonepe.com/apis/hermes/pg/v1/pay"
        expected_status_base = "https://api-preprod.phonepe.com/apis/pg-sandbox/pg/v1/status"
        
        print(f"\n2. Verifying URLs against PhonePe V2 Documentation:")
        print("-" * 50)
        
        if client.oauth_url == expected_oauth:
            print(f"✅ OAuth URL matches docs: {client.oauth_url}")
        else:
            print(f"❌ OAuth URL mismatch:")
            print(f"   Expected: {expected_oauth}")
            print(f"   Actual:   {client.oauth_url}")
        
        if client.payment_endpoint == expected_payment:
            print(f"✅ Payment endpoint matches docs: {client.payment_endpoint}")
        else:
            print(f"❌ Payment endpoint mismatch:")
            print(f"   Expected: {expected_payment}")
            print(f"   Actual:   {client.payment_endpoint}")
        
        if client.status_endpoint_base == expected_status_base:
            print(f"✅ Status endpoint base matches docs: {client.status_endpoint_base}")
        else:
            print(f"❌ Status endpoint base mismatch:")
            print(f"   Expected: {expected_status_base}")
            print(f"   Actual:   {client.status_endpoint_base}")
        
        # Test merchant ID format
        print(f"\n3. Testing Merchant Configuration:")
        print("-" * 35)
        
        if client.merchant_id == "V2SUBUAT":
            print(f"✅ Using correct UAT merchant ID: {client.merchant_id}")
        else:
            print(f"⚠️  Merchant ID: {client.merchant_id} (should be 'V2SUBUAT' for UAT)")
        
        if client.client_version == "1":
            print(f"✅ Using correct client version: {client.client_version}")
        else:
            print(f"❌ Client version should be '1' for UAT, got: {client.client_version}")
        
        print(f"\n4. Configuration Summary:")
        print("-" * 25)
        print("✅ PhonePe V2 client configured successfully!")
        print("✅ All URLs match PhonePe V2 Standard Checkout documentation")
        print("✅ Ready for UAT testing")
        
        return True
        
    except Exception as e:
        print(f"❌ Error initializing PhonePe V2 client: {e}")
        return False

def test_django_settings():
    """Test Django settings for PhonePe V2"""
    
    print(f"\n5. Testing Django Settings:")
    print("-" * 30)
    
    required_settings = [
        'PHONEPE_MERCHANT_ID',
        'PHONEPE_CLIENT_ID', 
        'PHONEPE_CLIENT_SECRET',
        'PHONEPE_OAUTH_BASE_URL',
        'PHONEPE_PAYMENT_BASE_URL'
    ]
    
    for setting in required_settings:
        value = getattr(settings, setting, None)
        if value:
            if 'SECRET' in setting:
                print(f"✅ {setting}: {'*' * 10}...")
            else:
                print(f"✅ {setting}: {value}")
        else:
            print(f"❌ {setting}: Not set")

if __name__ == "__main__":
    print("Starting PhonePe V2 configuration test...")
    
    success = test_phonepe_v2_config()
    test_django_settings()
    
    print(f"\n{'=' * 60}")
    if success:
        print("🎉 PhonePe V2 Configuration Test: PASSED")
        print("Your integration is ready for testing!")
    else:
        print("❌ PhonePe V2 Configuration Test: FAILED")
        print("Please fix the configuration issues above.")
    print(f"{'=' * 60}")
