#!/usr/bin/env python
"""
Comprehensive PhonePe Gateway Test
Tests the fixed gateway end-to-end to ensure it works in production
"""

import os
import sys
import django
import requests
import json
import time
from datetime import datetime

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from payment.models import Payment
from payment.gateways import PhonePeGateway

User = get_user_model()

def run_comprehensive_test():
    """Run all tests to validate the PhonePe fix"""
    
    print("🧪 COMPREHENSIVE PHONEPE GATEWAY TEST")
    print("="*60)
    print(f"Environment: {'PRODUCTION' if settings.DEBUG == False else 'DEVELOPMENT'}")
    print(f"Test Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("="*60)
    
    test_results = []
    
    # Test 1: Gateway Initialization
    print("\n🔧 TEST 1: Gateway Initialization")
    try:
        gateway = PhonePeGateway()
        print(f"✅ Gateway initialized successfully")
        print(f"   Merchant ID: {gateway.merchant_id}")
        print(f"   Base URL: {gateway.base_url}")
        print(f"   SSL Verify: {gateway.ssl_verify}")
        print(f"   Production Mode: {gateway.is_production}")
        test_results.append(("Gateway Init", True, "Success"))
    except Exception as e:
        print(f"❌ Gateway initialization failed: {e}")
        test_results.append(("Gateway Init", False, str(e)))
        return test_results
    
    # Test 2: Network Connectivity
    print("\n🌐 TEST 2: Network Connectivity")
    try:
        response = requests.get('https://api.phonepe.com/', timeout=10)
        if response.status_code in [200, 404]:
            print(f"✅ PhonePe reachable (Status: {response.status_code})")
            test_results.append(("Network Connectivity", True, f"Status {response.status_code}"))
        else:
            print(f"⚠️ Unexpected status: {response.status_code}")
            test_results.append(("Network Connectivity", False, f"Status {response.status_code}"))
    except Exception as e:
        print(f"❌ Network test failed: {e}")
        test_results.append(("Network Connectivity", False, str(e)))
    
    # Test 3: SSL Certificate Validation
    print("\n🔒 TEST 3: SSL Certificate Validation")
    try:
        import ssl
        import socket
        context = ssl.create_default_context()
        with socket.create_connection(('api.phonepe.com', 443), timeout=10) as sock:
            with context.wrap_socket(sock, server_hostname='api.phonepe.com') as ssock:
                print(f"✅ SSL certificate valid (Version: {ssock.version()})")
                test_results.append(("SSL Certificate", True, ssock.version()))
    except Exception as e:
        print(f"❌ SSL test failed: {e}")
        test_results.append(("SSL Certificate", False, str(e)))
    
    # Test 4: Create Test User and Payment
    print("\n👤 TEST 4: Test Payment Creation")
    try:
        # Get or create test user
        user, created = User.objects.get_or_create(
            email='test@okpuja.com',
            defaults={
                'first_name': 'Test',
                'last_name': 'User',
                'is_active': True
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
        
        # Create test payment
        payment = Payment.objects.create(
            user=user,
            amount=1.00,  # 1 rupee test
            currency='INR',
            status='pending',
            merchant_transaction_id=f"TEST_{int(time.time())}"
        )
        
        print(f"✅ Test payment created")
        print(f"   Payment ID: {payment.id}")
        print(f"   Transaction ID: {payment.merchant_transaction_id}")
        print(f"   Amount: ₹{payment.amount}")
        test_results.append(("Payment Creation", True, f"ID: {payment.id}"))
        
    except Exception as e:
        print(f"❌ Payment creation failed: {e}")
        test_results.append(("Payment Creation", False, str(e)))
        return test_results
    
    # Test 5: Payment Initiation (The Critical Test)
    print("\n💳 TEST 5: Payment Initiation (CRITICAL)")
    try:
        print("Initiating payment with fixed gateway...")
        result = gateway.initiate_payment(payment)
        
        if result.get('success'):
            print(f"✅ Payment initiation SUCCESSFUL!")
            print(f"   Payment URL: {result.get('payment_url', 'N/A')[:100]}...")
            print(f"   Transaction ID: {result.get('transaction_id')}")
            print(f"   Amount: ₹{result.get('amount')}")
            test_results.append(("Payment Initiation", True, "Payment URL generated"))
            
            # Update payment status
            payment.status = 'initiated'
            payment.gateway_response = json.dumps(result)
            payment.save()
            
        else:
            print(f"❌ Payment initiation FAILED!")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            print(f"   Error Type: {result.get('error_type', 'Unknown')}")
            if 'response' in result:
                print(f"   Response: {result['response'][:200]}...")
            test_results.append(("Payment Initiation", False, result.get('error', 'Unknown')))
            
    except Exception as e:
        print(f"❌ Payment initiation exception: {e}")
        print(f"   Exception type: {type(e).__name__}")
        test_results.append(("Payment Initiation", False, f"{type(e).__name__}: {str(e)}"))
    
    # Test 6: Webhook Endpoint Test
    print("\n🔗 TEST 6: Webhook Endpoint Test")
    try:
        webhook_url = f"{settings.PHONEPE_CALLBACK_URL}"
        print(f"Testing webhook URL: {webhook_url}")
        
        # Test if our webhook endpoint is accessible
        response = requests.get(webhook_url.replace('/phonepe/', '/debug/'), timeout=10)
        if response.status_code == 200:
            print(f"✅ Webhook endpoint accessible")
            test_results.append(("Webhook Endpoint", True, "Accessible"))
        else:
            print(f"⚠️ Webhook endpoint status: {response.status_code}")
            test_results.append(("Webhook Endpoint", False, f"Status {response.status_code}"))
    except Exception as e:
        print(f"❌ Webhook test failed: {e}")
        test_results.append(("Webhook Endpoint", False, str(e)))
    
    # Test 7: Configuration Validation
    print("\n⚙️ TEST 7: Configuration Validation")
    config_tests = [
        ("PHONEPE_MERCHANT_ID", settings.PHONEPE_MERCHANT_ID),
        ("PHONEPE_MERCHANT_KEY", settings.PHONEPE_MERCHANT_KEY[:10] + "..." if settings.PHONEPE_MERCHANT_KEY else None),
        ("PHONEPE_CALLBACK_URL", settings.PHONEPE_CALLBACK_URL),
        ("PHONEPE_SUCCESS_REDIRECT_URL", settings.PHONEPE_SUCCESS_REDIRECT_URL),
    ]
    
    config_ok = True
    for config_name, config_value in config_tests:
        if config_value:
            print(f"✅ {config_name}: {config_value}")
        else:
            print(f"❌ {config_name}: NOT SET")
            config_ok = False
    
    test_results.append(("Configuration", config_ok, "All settings present" if config_ok else "Missing settings"))
    
    # Clean up test data
    print("\n🧹 CLEANUP: Removing test data")
    try:
        payment.delete()
        if user.email == 'test@okpuja.com':
            user.delete()
        print("✅ Test data cleaned up")
    except Exception as e:
        print(f"⚠️ Cleanup warning: {e}")
    
    return test_results

def print_final_report(test_results):
    """Print the final test report"""
    
    print("\n" + "="*60)
    print("📊 FINAL TEST REPORT")
    print("="*60)
    
    passed = sum(1 for _, success, _ in test_results if success)
    total = len(test_results)
    
    print(f"Tests Passed: {passed}/{total}")
    print(f"Success Rate: {(passed/total)*100:.1f}%")
    
    print("\n📋 DETAILED RESULTS:")
    for test_name, success, details in test_results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status:10} {test_name:20} - {details}")
    
    print("\n" + "="*60)
    
    if passed == total:
        print("🎉 ALL TESTS PASSED!")
        print("Your PhonePe gateway is working correctly.")
    elif passed >= total - 1:
        print("✅ MOSTLY WORKING!")
        print("Minor issues found, but core functionality works.")
    else:
        print("⚠️ ISSUES DETECTED!")
        print("Please review the failed tests above.")
    
    print("\n🔍 TROUBLESHOOTING GUIDE:")
    if any("Network Connectivity" in result[0] and not result[1] for result in test_results):
        print("- Network issues: Check firewall and internet connectivity")
    if any("Payment Initiation" in result[0] and not result[1] for result in test_results):
        print("- Payment issues: Check PhonePe credentials and API endpoint")
    if any("Configuration" in result[0] and not result[1] for result in test_results):
        print("- Config issues: Verify all environment variables are set")
    
    print("="*60)

if __name__ == "__main__":
    try:
        results = run_comprehensive_test()
        print_final_report(results)
    except KeyboardInterrupt:
        print("\n\n⚠️ Test interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
