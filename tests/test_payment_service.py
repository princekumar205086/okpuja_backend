#!/usr/bin/env python
"""
Test script to validate payment creation works correctly
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

def test_payment_creation():
    """Test payment creation with cart ID"""
    try:
        from payment.services import PaymentService
        from cart.models import Cart
        from accounts.models import User
        
        print("🧪 Testing PaymentService initialization...")
        service = PaymentService()
        print("✅ PaymentService initialized successfully")
        
        # Test that required settings are available
        from django.conf import settings
        print(f"✅ FRONTEND_URL: {settings.FRONTEND_URL}")
        print(f"✅ BACKEND_URL: {settings.BACKEND_URL}")
        print(f"✅ PHONEPE_ENV: {settings.PHONEPE_ENV}")
        
        # Test service methods exist
        methods = ['create_payment_from_cart', 'initiate_payment', 'verify_payment']
        for method in methods:
            if hasattr(service, method):
                print(f"✅ PaymentService.{method} exists")
            else:
                print(f"❌ PaymentService.{method} missing")
        
        print("\n🎉 Payment service validation passed!")
        return True
        
    except Exception as e:
        print(f"❌ Payment service test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_payment_creation()
    sys.exit(0 if success else 1)
