#!/usr/bin/env python
"""
Simple PhonePe Connection Test
"""
import os
import sys
import django
import requests
import socket
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings

print("=" * 60)
print("SIMPLE PHONEPE CONNECTION TEST")
print("=" * 60)

# Step 1: Check basic config
print("\n1. Configuration Check:")
print(f"   PHONEPE_MERCHANT_ID: {getattr(settings, 'PHONEPE_MERCHANT_ID', 'NOT SET')}")
print(f"   PHONEPE_ENV: {getattr(settings, 'PHONEPE_ENV', 'NOT SET')}")
print(f"   PHONEPE_BASE_URL: {getattr(settings, 'PHONEPE_BASE_URL', 'NOT SET')}")
print(f"   PRODUCTION_SERVER: {getattr(settings, 'PRODUCTION_SERVER', False)}")

# Step 2: Basic connectivity test
print("\n2. Basic Connectivity Test:")
test_urls = [
    'https://google.com',
    'https://api.phonepe.com',
]

for url in test_urls:
    try:
        print(f"   Testing {url}...", end=" ")
        response = requests.get(url, timeout=10)
        print(f"✅ OK (Status: {response.status_code})")
    except requests.exceptions.ConnectionError:
        print("❌ CONNECTION REFUSED")
    except requests.exceptions.Timeout:
        print("❌ TIMEOUT")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")

# Step 3: DNS Resolution
print("\n3. DNS Resolution Test:")
try:
    ip = socket.gethostbyname('api.phonepe.com')
    print(f"   api.phonepe.com resolves to: {ip}")
except Exception as e:
    print(f"   DNS Error: {e}")

print("\n" + "=" * 60)
print("Test completed!")
print("=" * 60)
