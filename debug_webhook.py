#!/usr/bin/env python
"""
Debug PhonePe Webhook Issue
This script helps debug the webhook by sending test requests
"""

import os
import django
import requests
import json

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings

def test_webhook_empty_body():
    """Test webhook with empty body (current issue)"""
    print("🔍 Testing webhook with empty body...")
    
    webhook_url = "http://127.0.0.1:8000/api/payments/webhook/phonepe/"
    
    # Test 1: Completely empty body
    print("\n1. Testing with completely empty body:")
    try:
        response = requests.post(webhook_url, data="", headers={'Content-Type': 'application/json'})
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 2: Empty JSON object
    print("\n2. Testing with empty JSON object:")
    try:
        response = requests.post(webhook_url, json={}, headers={'Content-Type': 'application/json'})
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")
    
    # Test 3: Invalid JSON
    print("\n3. Testing with invalid JSON:")
    try:
        response = requests.post(webhook_url, data="invalid json", headers={'Content-Type': 'application/json'})
        print(f"Status: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def test_webhook_valid_payload():
    """Test webhook with valid PhonePe-like payload"""
    print("\n🔍 Testing webhook with valid payload...")
    
    webhook_url = "http://127.0.0.1:8000/api/payments/webhook/phonepe/"
    
    # Sample PhonePe webhook payload structure
    sample_payload = {
        "response": "eyJzdWNjZXNzIjp0cnVlLCJjb2RlIjoiUEFZTUVOVF9TVUNDRVNTIiwibWVzc2FnZSI6IlBheW1lbnQgc3VjY2Vzc2Z1bCIsImRhdGEiOnsibWVyY2hhbnRJZCI6Ik9LUFVKQSIsIm1lcmNoYW50VHJhbnNhY3Rpb25JZCI6IlRYTjEyMzQ1Njc4OTAiLCJzdGF0ZSI6IkNPTVBMRVRFRCJ9fQ==",
        "merchantId": "OKPUJA",
        "merchantTransactionId": "TXN1234567890"
    }
    
    headers = {
        'Content-Type': 'application/json',
        'X-VERIFY': 'test_signature_here'
    }
    
    print("Sample payload:")
    print(json.dumps(sample_payload, indent=2))
    
    try:
        response = requests.post(webhook_url, json=sample_payload, headers=headers)
        print(f"\nStatus: {response.status_code}")
        print(f"Response: {response.text}")
    except Exception as e:
        print(f"Error: {e}")

def check_webhook_endpoint():
    """Check if webhook endpoint is accessible"""
    print("🔍 Checking webhook endpoint accessibility...")
    
    webhook_url = "http://127.0.0.1:8000/api/payments/webhook/phonepe/"
    
    try:
        response = requests.get(webhook_url)
        print(f"GET Status: {response.status_code}")
        print(f"GET Response: {response.text}")
    except Exception as e:
        print(f"GET Error: {e}")

if __name__ == "__main__":
    print("🚀 PhonePe Webhook Debug Script")
    print("=" * 50)
    
    # Check if server is running
    try:
        response = requests.get("http://127.0.0.1:8000/api/")
        print("✅ Django server is accessible")
    except Exception as e:
        print(f"❌ Django server not accessible: {e}")
        print("Please start the server with: python manage.py runserver")
        exit(1)
    
    check_webhook_endpoint()
    test_webhook_empty_body() 
    test_webhook_valid_payload()
    
    print("\n" + "=" * 50)
    print("🎯 RECOMMENDATIONS:")
    print("1. If webhook receives empty body, check PhonePe dashboard webhook configuration")
    print("2. Ensure webhook URL is publicly accessible (not localhost for production)")
    print("3. Check PhonePe webhook authentication settings")
    print("4. Verify Content-Type headers in PhonePe webhook configuration")
