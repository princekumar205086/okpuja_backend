#!/usr/bin/env python
"""
Verify Django Settings - Check what credentials Django is loading
"""

import os
import sys
import django

# Set up Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings

def main():
    print("🔍 Django Settings Verification")
    print("=" * 50)
    
    print(f"📋 Current PhonePe Configuration:")
    print(f"Environment: {getattr(settings, 'PHONEPE_ENV', 'NOT SET')}")
    print(f"Merchant ID: {getattr(settings, 'PHONEPE_MERCHANT_ID', 'NOT SET')}")
    print(f"Client ID: {getattr(settings, 'PHONEPE_CLIENT_ID', 'NOT SET')}")
    print(f"Client Secret: {getattr(settings, 'PHONEPE_CLIENT_SECRET', 'NOT SET')[:20]}...")
    print(f"Salt Key: {getattr(settings, 'PHONEPE_SALT_KEY', 'NOT SET')[:20]}...")
    
    print(f"\n📋 Production Credentials Available:")
    print(f"Prod Client ID: {getattr(settings, 'PHONEPE_PROD_CLIENT_ID', 'NOT SET')}")
    print(f"Prod Client Secret: {getattr(settings, 'PHONEPE_PROD_CLIENT_SECRET', 'NOT SET')[:20]}...")
    
    print(f"\n📋 URLs:")
    print(f"Payment Base URL: {getattr(settings, 'PHONEPE_PAYMENT_BASE_URL', 'NOT SET')}")
    print(f"OAuth Base URL: {getattr(settings, 'PHONEPE_OAUTH_BASE_URL', 'NOT SET')}")
    
    # Test PhonePe client initialization
    try:
        from payment.phonepe_v2_corrected import PhonePeV2ClientCorrected
        
        print(f"\n🔧 Testing PhonePe Client Initialization:")
        
        # Test UAT
        client_uat = PhonePeV2ClientCorrected(env="uat")
        print(f"UAT Client - Merchant ID: {client_uat.merchant_id}")
        print(f"UAT Client - Client ID: {client_uat.client_id}")
        print(f"UAT Client - Base URL: {client_uat.base_url}")
        
        # Test Production
        client_prod = PhonePeV2ClientCorrected(env="production")
        print(f"Production Client - Merchant ID: {client_prod.merchant_id}")
        print(f"Production Client - Client ID: {client_prod.client_id}")
        print(f"Production Client - Base URL: {client_prod.base_url}")
        
    except Exception as e:
        print(f"❌ Error initializing PhonePe client: {e}")

if __name__ == "__main__":
    main()
