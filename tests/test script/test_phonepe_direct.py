#!/usr/bin/env python
import os
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from payment.gateways import PhonePeGateway
from django.conf import settings
import json

def test_phonepe_gateway():
    """Test PhonePe gateway configuration"""
    print("🧪 Testing PhonePe Gateway Configuration...")
    
    # Print configuration
    print(f"Environment: {getattr(settings, 'PHONEPE_ENV', 'Not set')}")
    print(f"Merchant ID: {getattr(settings, 'PHONEPE_MERCHANT_ID', 'Not set')}")
    print(f"Merchant Key: {'*' * len(getattr(settings, 'PHONEPE_MERCHANT_KEY', '')) if getattr(settings, 'PHONEPE_MERCHANT_KEY', '') else 'Not set'}")
    print(f"Salt Index: {getattr(settings, 'PHONEPE_SALT_INDEX', 'Not set')}")
    print(f"Base URL: {getattr(settings, 'PHONEPE_BASE_URL', 'Not set')}")
    
    # Test checksum generation
    try:
        gateway = PhonePeGateway()
        test_data = "eyJtZXJjaGFudElkIjoiTTIyS0VXVTVCTzFJMiIsIm1lcmNoYW50VHJhbnNhY3Rpb25JZCI6IlRSWDIwMjUwMTI0MkIzMDFBMTMiLCJtZXJjaGFudFVzZXJJZCI6InVzZXJfMSIsImFtb3VudCI6NTAwMDAwLCJyZWRpcmVjdFVybCI6Imh0dHA6Ly8xMjcuMC4wLjE6ODAwMC9hcGkvcGF5bWVudHMvd2ViaG9vay9waG9uZXBlLyIsInJlZGlyZWN0TW9kZSI6IlBPU1QiLCJjYWxsYmFja1VybCI6Imh0dHA6Ly8xMjcuMC4wLjE6ODAwMC9hcGkvcGF5bWVudHMvd2ViaG9vay9waG9uZXBlLyIsIm1vYmlsZU51bWJlciI6IjkwMDAwMDAwMDAiLCJwYXltZW50SW5zdHJ1bWVudCI6eyJ0eXBlIjoiUEFZX1BBR0UifX0="
        checksum = gateway.generate_checksum(test_data)
        print(f"✅ Checksum generated: {checksum}")
        
        # Test URL construction
        api_url = f"{gateway.base_url}/pg/v1/pay"
        print(f"✅ API URL: {api_url}")
        
    except Exception as e:
        print(f"❌ Gateway test failed: {str(e)}")

if __name__ == "__main__":
    test_phonepe_gateway()
