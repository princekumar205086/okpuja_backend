#!/usr/bin/env python
"""
Simple PhonePe Production Test
"""
import os
import django
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings

print("🚀 PhonePe Production Configuration Test")
print("=" * 50)

# Check configuration
print("📋 Configuration:")
print(f"   PHONEPE_ENV: {getattr(settings, 'PHONEPE_ENV', 'NOT SET')}")
print(f"   PHONEPE_MERCHANT_ID: {'SET' if getattr(settings, 'PHONEPE_MERCHANT_ID', None) else 'NOT SET'}")
print(f"   PHONEPE_BASE_URL: {getattr(settings, 'PHONEPE_BASE_URL', 'NOT SET')}")
print(f"   PRODUCTION_SERVER: {getattr(settings, 'PRODUCTION_SERVER', False)}")
print(f"   DEBUG: {getattr(settings, 'DEBUG', True)}")

# Test basic connectivity
print(f"\n🌐 Testing Basic Connectivity:")
test_urls = [
    'https://api.phonepe.com',
    'https://www.okpuja.com'
]

for url in test_urls:
    try:
        print(f"   Testing {url}...", end=" ")
        response = requests.get(url, timeout=10)
        print(f"✅ OK (Status: {response.status_code})")
    except Exception as e:
        print(f"❌ FAILED: {str(e)}")

print(f"\n🎯 Ready for Payment Testing!")
print("   Use the /api/payments/payments/process-cart/ endpoint")
print("   to test actual payment processing")
print("=" * 50)
