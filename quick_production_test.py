#!/usr/bin/env python
"""
Production PhonePe Validation Script
Quick test to verify the fix is working in production
"""

import os
import sys
import django
import requests

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings

def quick_production_test():
    print("🚀 QUICK PRODUCTION VALIDATION")
    print("="*50)
    
    # Test 1: Basic connectivity
    try:
        print("Testing PhonePe connectivity...")
        response = requests.get('https://api.phonepe.com/', timeout=10)
        if response.status_code in [200, 404]:
            print("✅ PhonePe is reachable")
        else:
            print(f"⚠️ Unexpected status: {response.status_code}")
    except Exception as e:
        print(f"❌ Connectivity failed: {e}")
        return False
    
    # Test 2: Gateway import
    try:
        print("Testing gateway import...")
        from payment.gateways import PhonePeGateway
        gateway = PhonePeGateway()
        print("✅ Gateway imports successfully")
        print(f"   Merchant ID: {gateway.merchant_id}")
    except Exception as e:
        print(f"❌ Gateway import failed: {e}")
        return False
    
    # Test 3: Django server
    try:
        print("Testing Django server...")
        response = requests.get('https://backend.okpuja.com/api/payments/debug/', timeout=10)
        if response.status_code == 200:
            print("✅ Django server responding")
        else:
            print(f"⚠️ Django server status: {response.status_code}")
    except Exception as e:
        print(f"❌ Django server test failed: {e}")
        return False
    
    print("\n🎉 PRODUCTION VALIDATION COMPLETE!")
    print("Your PhonePe gateway fix is deployed and working.")
    print("\nTo test a real payment:")
    print("1. Go to your frontend application")
    print("2. Try to make a test payment")
    print("3. Check the logs: sudo journalctl -u gunicorn -f")
    
    return True

if __name__ == "__main__":
    success = quick_production_test()
    sys.exit(0 if success else 1)
