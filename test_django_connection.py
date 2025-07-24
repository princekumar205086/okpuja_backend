#!/usr/bin/env python
"""
Test Django Application Connection Issue
This script tests the exact same way Django makes the connection
"""

import os
import sys
import django
import json
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings
from payment.gateways import PhonePeGateway

def test_django_connectivity():
    print("="*60)
    print("DJANGO APPLICATION CONNECTION TEST")
    print("="*60)
    print(f"Timestamp: {datetime.now()}")
    print()
    
    # Test 1: Initialize Gateway (same as Django app does)
    print("1. Testing PhonePe Gateway Initialization...")
    try:
        gateway = PhonePeGateway()
        print("✅ Gateway initialized successfully")
        print(f"   Base URL: {gateway.base_url}")
        print(f"   Timeout: {gateway.timeout}s")
        print(f"   Retries: {gateway.max_retries}")
        print(f"   SSL Verify: {gateway.ssl_verify}")
    except Exception as e:
        print(f"❌ Gateway initialization failed: {str(e)}")
        return
    
    # Test 2: Test connectivity method
    print("\n2. Testing Gateway Connectivity Method...")
    try:
        connectivity_results = gateway.test_connectivity()
        print("✅ Connectivity test completed")
        for result in connectivity_results:
            status = "✅" if result.get('reachable') else "❌"
            print(f"   {status} {result.get('endpoint')}: {result.get('status_code', 'N/A')}")
    except Exception as e:
        print(f"❌ Connectivity test failed: {str(e)}")
    
    # Test 3: Test actual payment initiation (same as app does)
    print("\n3. Testing Actual Payment Initiation...")
    try:
        test_payload = {
            'amount': 100,  # 1 rupee
            'user_id': 'test_user_django',
            'mobile': '9876543210'
        }
        
        # This calls the same method your Django app calls
        result = gateway.initiate_payment(
            amount=test_payload['amount'],
            mobile_number=test_payload['mobile'],
            user_id=test_payload['user_id'],
            booking_id=999,  # Test booking ID
            cart_id=999      # Test cart ID
        )
        
        print("✅ Payment initiation successful!")
        print(f"   Payment URL: {result.get('payment_url', 'Not found')[:50]}...")
        print(f"   Transaction ID: {result.get('transaction_id', 'Not found')}")
        print(f"   Status: {result.get('success', False)}")
        
    except Exception as e:
        print(f"❌ Payment initiation failed: {str(e)}")
        print(f"   Error type: {type(e).__name__}")
        
        # Check if it's the same Connection refused error
        if "Connection refused" in str(e):
            print("🚨 FOUND THE ISSUE: Django app gets Connection refused")
            print("   But diagnostic script works fine!")
            print("   This suggests a Django configuration or import issue")
    
    print(f"\n{'='*60}")
    print("TEST COMPLETED")
    print("="*60)

if __name__ == "__main__":
    test_django_connectivity()
