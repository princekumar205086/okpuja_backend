#!/usr/bin/env python
"""
Test payment views after fixing duplicate methods
"""
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

print("🧪 Testing Payment Views Import")
print("=" * 40)

try:
    from payment.views import PaymentViewSet
    print("✅ PaymentViewSet imported successfully!")
    
    # Check methods
    methods = [method for method in dir(PaymentViewSet) if not method.startswith('_')]
    print(f"📊 Total methods: {len(methods)}")
    
    # Check for our specific methods
    target_methods = ['simulate_payment_success', 'debug_connectivity', 'process_cart_payment']
    
    for method in target_methods:
        if hasattr(PaymentViewSet, method):
            print(f"✅ {method}: Found")
        else:
            print(f"❌ {method}: Missing")
    
    # Check for duplicates by examining the method's actual implementation
    if hasattr(PaymentViewSet, 'simulate_payment_success'):
        method_obj = getattr(PaymentViewSet, 'simulate_payment_success')
        doc = method_obj.__doc__ or ""
        if "DEVELOPMENT ONLY" in doc:
            print("✅ simulate_payment_success: Correct version (enhanced)")
        else:
            print("⚠️  simulate_payment_success: Old version detected")
    
    print("\n🎯 Import test completed successfully!")
    
except ImportError as e:
    print(f"❌ Import failed: {str(e)}")
except Exception as e:
    print(f"❌ Unexpected error: {str(e)}")

print("=" * 40)
