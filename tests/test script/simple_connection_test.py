#!/usr/bin/env python
"""
Simple PhonePe Connection Test
"""

import os
import sys
import django
import requests
import socket
import json
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings

def test_basic_connectivity():
    print("="*60)
    print("PHONEPE CONNECTION TEST")
    print("="*60)
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # Test basic internet
    print("Testing basic internet connectivity...")
    try:
        response = requests.get('https://google.com', timeout=10)
        print(f"✅ Google: {response.status_code}")
    except Exception as e:
        print(f"❌ Google: {str(e)}")
    
    # Test PhonePe domain
    print("\nTesting PhonePe domain...")
    try:
        response = requests.get('https://api.phonepe.com', timeout=15)
        print(f"✅ PhonePe domain: {response.status_code}")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ PhonePe domain: CONNECTION REFUSED - {str(e)}")
    except Exception as e:
        print(f"❌ PhonePe domain: {str(e)}")
    
    # Test DNS resolution
    print("\nTesting DNS resolution...")
    try:
        ip = socket.gethostbyname('api.phonepe.com')
        print(f"✅ api.phonepe.com resolves to: {ip}")
    except Exception as e:
        print(f"❌ DNS resolution failed: {str(e)}")
    
    # Test PhonePe API endpoint
    print("\nTesting PhonePe API endpoint...")
    try:
        response = requests.get('https://api.phonepe.com/apis/hermes/pg/v1/pay', timeout=20)
        print(f"✅ PhonePe API endpoint: {response.status_code}")
    except requests.exceptions.ConnectionError as e:
        print(f"❌ PhonePe API endpoint: CONNECTION REFUSED - {str(e)}")
    except Exception as e:
        print(f"❌ PhonePe API endpoint: {str(e)}")
    
    # Test with different user agents
    print("\nTesting with different user agents...")
    user_agents = [
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'OkPuja-Backend/1.0',
        'curl/7.68.0'
    ]
    
    for ua in user_agents:
        try:
            response = requests.get(
                'https://api.phonepe.com', 
                headers={'User-Agent': ua},
                timeout=10
            )
            print(f"✅ User-Agent {ua[:20]}...: {response.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"❌ User-Agent {ua[:20]}...: CONNECTION REFUSED")
        except Exception as e:
            print(f"❌ User-Agent {ua[:20]}...: {str(e)[:50]}")
    
    # Check environment settings
    print(f"\nEnvironment Settings:")
    print(f"PHONEPE_MERCHANT_ID: {getattr(settings, 'PHONEPE_MERCHANT_ID', 'NOT_SET')[:10]}...")
    print(f"PHONEPE_ENV: {getattr(settings, 'PHONEPE_ENV', 'NOT_SET')}")
    print(f"PRODUCTION_SERVER: {getattr(settings, 'PRODUCTION_SERVER', False)}")
    print(f"DEBUG: {getattr(settings, 'DEBUG', True)}")
    
    print("\n" + "="*60)
    print("TEST COMPLETED")
    print("="*60)

if __name__ == "__main__":
    test_basic_connectivity()
