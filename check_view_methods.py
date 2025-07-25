#!/usr/bin/env python3
"""
Check the actual view structure to find the correct payment processing method
"""

import django
import os
import sys

# Add the project directory to Python path
sys.path.append('/opt/api.okpuja.com')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

def check_payment_views():
    print("🔍 Checking Payment View Methods")
    print("=" * 35)
    
    try:
        from payment.views import PaymentViewSet
        
        # Get all methods of the PaymentViewSet
        methods = [method for method in dir(PaymentViewSet) if not method.startswith('_')]
        
        print("📋 Available methods in PaymentViewSet:")
        for method in methods:
            print(f"  - {method}")
            
        # Look for methods that might handle cart processing
        cart_methods = [m for m in methods if 'cart' in m.lower() or 'process' in m.lower()]
        print(f"\n🛒 Cart/Process related methods: {cart_methods}")
        
        # Check the URL patterns to see what method handles the endpoint
        print("\n🔍 Checking URL patterns...")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def check_urls():
    print("\n🔍 Checking Payment URLs")
    print("=" * 25)
    
    try:
        # Read the payment urls.py file
        with open("/opt/api.okpuja.com/payment/urls.py", 'r') as f:
            urls_content = f.read()
            
        print("📄 Payment URLs content:")
        lines = urls_content.split('\n')
        for i, line in enumerate(lines, 1):
            if 'process-cart' in line or 'cart' in line.lower():
                print(f"Line {i}: {line.strip()}")
                
    except Exception as e:
        print(f"❌ Error reading URLs: {e}")

def test_actual_endpoint():
    print("\n🧪 Testing Payment Processing")
    print("=" * 30)
    
    try:
        from django.test import RequestFactory
        from django.contrib.auth.models import User
        from payment.views import PaymentViewSet
        
        factory = RequestFactory()
        
        # Create a test request
        request = factory.post('/api/payments/payments/process-cart/', {
            'cart_id': 16,
            'payment_method': 'phonepe'
        }, content_type='application/json')
        
        # Try to find the right method to call
        viewset = PaymentViewSet()
        viewset.request = request
        
        # Check what methods exist
        payment_methods = [m for m in dir(viewset) if 'process' in m.lower() or 'payment' in m.lower()]
        print(f"🔧 Payment processing methods: {payment_methods}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_payment_views()
    check_urls()
    test_actual_endpoint()
    
    print("\n" + "="*50)
    print("🎯 ACTION NEEDED")
    print("="*50)
    print("1. Find the correct method name that handles process-cart")
    print("2. Ensure that method uses get_payment_gateway_v2")
    print("3. Complete the gunicorn restart process")
    print("4. Test the endpoint again")
