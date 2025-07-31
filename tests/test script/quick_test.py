#!/usr/bin/env python
"""
Quick PhonePe Gateway Test
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from payment.gateways import PhonePeGateway
from django.conf import settings

print("🚀 PhonePe Gateway Test")
print("=" * 40)

try:
    # Initialize gateway
    gateway = PhonePeGateway()
    
    print(f"✅ Gateway initialized successfully!")
    print(f"   Merchant ID: {gateway.merchant_id}")
    print(f"   Environment: {getattr(settings, 'PHONEPE_ENV', 'NOT SET')}")
    print(f"   Base URL: {gateway.base_url}")
    print(f"   Timeout: {gateway.timeout}s")
    print(f"   Max Retries: {gateway.max_retries}")
    print(f"   Production Mode: {gateway.is_production}")
    
    # Test connectivity
    print(f"\n🌐 Testing Connectivity:")
    connectivity = gateway.test_connectivity()
    
    working = [c for c in connectivity if c.get('status') == 'connected']
    failed = [c for c in connectivity if c.get('status') != 'connected']
    
    print(f"   Working endpoints: {len(working)}")
    print(f"   Failed endpoints: {len(failed)}")
    
    if working:
        print("   ✅ PhonePe connectivity is working!")
        for endpoint in working:
            print(f"      - {endpoint['endpoint']}: Status {endpoint.get('response_code', 'OK')}")
    else:
        print("   ❌ All PhonePe endpoints are unreachable")
        for endpoint in failed:
            print(f"      - {endpoint['endpoint']}: {endpoint.get('error', 'Unknown error')}")
    
    print(f"\n🎯 Status: {'READY FOR PRODUCTION' if working else 'CONNECTION ISSUES'}")
    
except Exception as e:
    print(f"❌ Error: {str(e)}")
    print(f"   Check your .env configuration")

print("=" * 40)
