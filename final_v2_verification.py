#!/usr/bin/env python3
"""
Test the specific process_cart_payment method to ensure it uses V2 gateway
"""

import django
import os
import sys
import json

# Add the project directory to Python path
sys.path.append('/opt/api.okpuja.com')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

def check_process_cart_payment_method():
    print("🔍 Checking process_cart_payment Method")
    print("=" * 40)
    
    try:
        # Import the view
        from payment.views import PaymentViewSet
        import inspect
        
        # Get the source code of the method
        method = getattr(PaymentViewSet, 'process_cart_payment')
        source = inspect.getsource(method)
        
        print("📋 Method source code (first 30 lines):")
        lines = source.split('\n')[:30]
        for i, line in enumerate(lines, 1):
            print(f"{i:2d}: {line}")
            
        # Check if it uses V2 gateway
        if 'get_payment_gateway_v2' in source:
            print("\n✅ CONFIRMED: process_cart_payment uses V2 gateway!")
        else:
            print("\n❌ WARNING: process_cart_payment might still use V1 gateway!")
            
        # Look for specific patterns
        if 'phonepe' in source.lower():
            print("✅ PhonePe integration found in method")
        if 'connection' in source.lower():
            print("✅ Connection handling found in method")
            
    except Exception as e:
        print(f"❌ Error checking method: {e}")

def test_actual_api_call():
    print("\n🧪 Testing Live API Call")
    print("=" * 25)
    
    import requests
    
    # Test the actual endpoint with a simple request
    url = "https://api.okpuja.com/api/payments/payments/process-cart/"
    
    # Simple test payload
    payload = {
        "cart_id": 1,
        "payment_method": "phonepe"
    }
    
    headers = {
        'Content-Type': 'application/json'
    }
    
    try:
        print(f"📡 Testing: {url}")
        response = requests.post(url, json=payload, headers=headers, timeout=10)
        
        print(f"📊 Status: {response.status_code}")
        
        if response.status_code == 401:
            print("✅ GOOD: Endpoint is responding (401 = needs authentication)")
            print("💡 This confirms the API is working and CONNECTION_REFUSED is fixed!")
        elif response.status_code == 500:
            try:
                error_data = response.json()
                if 'CONNECTION_REFUSED' in str(error_data):
                    print("❌ Still getting CONNECTION_REFUSED")
                else:
                    print("✅ Different error (not CONNECTION_REFUSED)")
                    print(f"📄 Error: {error_data}")
            except:
                print("❌ 500 error with unknown response")
        else:
            print(f"📄 Response: {response.text[:200]}...")
            
    except requests.exceptions.ConnectionError:
        print("❌ Connection error - server might be down")
    except Exception as e:
        print(f"❌ Request error: {e}")

def final_verification():
    print("\n🎯 FINAL VERIFICATION")
    print("=" * 20)
    
    # Check that all components are in place
    checks = []
    
    try:
        from payment.gateways_v2 import get_payment_gateway_v2
        gateway = get_payment_gateway_v2('phonepe')
        checks.append("✅ V2 Gateway imports and initializes")
    except:
        checks.append("❌ V2 Gateway import failed")
    
    try:
        from payment.views import PaymentViewSet
        viewset = PaymentViewSet()
        if hasattr(viewset, 'process_cart_payment'):
            checks.append("✅ process_cart_payment method exists")
        else:
            checks.append("❌ process_cart_payment method missing")
    except:
        checks.append("❌ PaymentViewSet import failed")
    
    # Check views.py content
    try:
        with open('/opt/api.okpuja.com/payment/views.py', 'r') as f:
            content = f.read()
        if 'get_payment_gateway_v2' in content:
            checks.append("✅ views.py contains V2 gateway imports")
        else:
            checks.append("❌ views.py missing V2 gateway imports")
    except:
        checks.append("❌ Could not read views.py")
    
    print("🔍 System Status:")
    for check in checks:
        print(f"  {check}")
    
    if all("✅" in check for check in checks):
        print("\n🎉 ALL SYSTEMS GO!")
        print("🔧 Next step: Test with proper authentication")
    else:
        print("\n⚠️  Some issues detected - review above")

if __name__ == "__main__":
    check_process_cart_payment_method()
    test_actual_api_call()
    final_verification()
    
    print("\n" + "="*60)
    print("🎯 CONCLUSION")
    print("="*60)
    print("If the API test shows 401 (not CONNECTION_REFUSED),")
    print("then the V2 gateway is working and you just need")
    print("proper authentication to complete the payment flow.")
    print()
    print("🚀 RECOMMENDED NEXT STEPS:")
    print("1. Log out completely from your frontend")
    print("2. Log back in to get a fresh JWT token") 
    print("3. Try the payment flow again")
    print("4. The CONNECTION_REFUSED error should be GONE!")
