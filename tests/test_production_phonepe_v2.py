#!/usr/bin/env python
"""
PhonePe V2 Production Environment Test Script
Test the production configuration and fix any issues
"""

import os
import sys
import django
import json
import requests
from datetime import datetime

# Django setup
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings
from payments.phonepe_client import PhonePePaymentClient
from payments.services import PaymentService
from django.contrib.auth import get_user_model

User = get_user_model()

def test_production_environment():
    """Test production environment configuration"""
    print("🔧 Testing PhonePe V2 Production Configuration")
    print("=" * 60)
    
    # Check environment settings
    env = getattr(settings, 'PHONEPE_ENV', 'Not Set')
    client_id = getattr(settings, 'PHONEPE_CLIENT_ID', 'Not Set')
    merchant_id = getattr(settings, 'PHONEPE_MERCHANT_ID', 'Not Set')
    
    print(f"Environment: {env}")
    print(f"Client ID: {client_id}")
    print(f"Merchant ID: {merchant_id}")
    print(f"Frontend URL: {getattr(settings, 'FRONTEND_BASE_URL', 'Not Set')}")
    
    if env != 'PRODUCTION':
        print("❌ Environment not set to PRODUCTION")
        return False
    
    if not client_id or client_id == 'Not Set':
        print("❌ Client ID not configured")
        return False
    
    print("✅ Basic configuration looks good")
    return True

def test_oauth_token():
    """Test OAuth token generation with production credentials"""
    print("\n🔐 Testing OAuth Token Generation")
    print("-" * 40)
    
    try:
        # Initialize production client
        client = PhonePePaymentClient(environment="production")
        
        print(f"OAuth URL: {client.oauth_url}")
        print(f"Client ID: {client.client_id[:20]}...")
        
        # Test direct OAuth call (mimicking your working Postman call)
        headers = {
            'Content-Type': 'application/x-www-form-urlencoded'
        }
        
        data = {
            'client_id': client.client_id,
            'client_version': client.client_version,
            'client_secret': client.client_secret,
            'grant_type': 'client_credentials'
        }
        
        print("Making OAuth request...")
        response = requests.post(
            client.oauth_url,
            headers=headers,
            data=data,
            timeout=30
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            token_data = response.json()
            print("✅ OAuth token obtained successfully!")
            print(f"Token Type: {token_data.get('token_type')}")
            print(f"Expires In: {token_data.get('expires_in')} seconds")
            
            # Test using client method
            access_token = client.get_access_token()
            print(f"✅ Client method also works: {access_token[:20]}...")
            return True
        else:
            print(f"❌ OAuth failed: {response.status_code}")
            print(f"Response: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ OAuth error: {e}")
        return False

def test_payment_creation():
    """Test payment creation with production environment"""
    print("\n💳 Testing Payment Creation")
    print("-" * 40)
    
    try:
        # Try to get existing user first
        try:
            user = User.objects.get(username='testuser_prod')
            print(f"✅ Using existing test user: {user.username}")
        except User.DoesNotExist:
            # Create new user with unique email
            import uuid
            unique_email = f"test_{uuid.uuid4().hex[:8]}@okpuja.com"
            user = User.objects.create_user(
                username='testuser_prod_' + uuid.uuid4().hex[:8],
                email=unique_email
            )
            print(f"✅ Created test user: {user.username}")
        
        # Initialize payment service
        payment_service = PaymentService(environment="production")
        
        # Test payment creation (small amount for testing)
        result = payment_service.create_payment_order(
            user=user,
            amount=100,  # ₹1.00 for testing
            redirect_url='https://www.okpuja.com/payment-success',
            description='Production test payment'
        )
        
        if result['success']:
            print("✅ Payment order created successfully!")
            print(f"Merchant Order ID: {result['merchant_order_id']}")
            print(f"Payment URL: {result['payment_url'][:50]}...")
            
            # Test status check
            status_result = payment_service.check_payment_status(result['merchant_order_id'])
            if status_result['success']:
                print("✅ Payment status check works!")
                print(f"Status: {status_result['payment_order'].status}")
            else:
                print(f"⚠️  Status check failed: {status_result['error']}")
            
            return True
        else:
            print(f"❌ Payment creation failed: {result['error']}")
            return False
            
    except Exception as e:
        print(f"❌ Payment creation error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_webhook_url():
    """Test webhook URL configuration"""
    print("\n🔔 Testing Webhook Configuration")
    print("-" * 40)
    
    webhook_url = getattr(settings, 'PHONEPE_CALLBACK_URL', '')
    print(f"Configured Webhook URL: {webhook_url}")
    
    if 'localhost' in webhook_url:
        print("❌ Webhook URL still points to localhost")
        print("Update PHONEPE_CALLBACK_URL in .env to production URL")
        return False
    
    if webhook_url.startswith('https://www.okpuja.com'):
        print("✅ Webhook URL configured for production")
        return True
    
    print("⚠️  Webhook URL needs verification")
    return False

def main():
    """Run all production tests"""
    print("🚀 PhonePe V2 Production Test Suite")
    print("=" * 60)
    
    tests = [
        ("Environment Configuration", test_production_environment),
        ("OAuth Token Generation", test_oauth_token),
        ("Payment Creation", test_payment_creation),
        ("Webhook Configuration", test_webhook_url),
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n📊 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nPassed: {passed}/{len(results)} tests")
    
    if passed == len(results):
        print("\n🎉 All tests passed! Production environment is ready.")
    else:
        print("\n⚠️  Some tests failed. Please check the configuration.")
        
        # Provide specific fixes
        print("\n🔧 Fixes Required:")
        for test_name, result in results:
            if not result:
                if "Environment" in test_name:
                    print("- Set PHONEPE_ENV=PRODUCTION in .env")
                elif "OAuth" in test_name:
                    print("- Verify production credentials in .env")
                elif "Payment" in test_name:
                    print("- Check PhonePe client configuration")
                elif "Webhook" in test_name:
                    print("- Update webhook URLs to production domain")

if __name__ == "__main__":
    main()
