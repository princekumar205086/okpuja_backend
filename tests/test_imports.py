#!/usr/bin/env python
"""
Test script to verify that all payment imports work correctly
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

def test_imports():
    """Test all payment-related imports"""
    try:
        # Test model imports
        from payment.models import Payment, PaymentStatus, PaymentMethod, Refund
        print("✅ Model imports successful")
        
        # Test service imports
        from payment.services import PaymentService
        print("✅ Service imports successful")
        
        # Test client imports
        from payment.phonepe_v2_corrected import PhonePeV2ClientCorrected, PhonePeV2Exception
        print("✅ PhonePe client imports successful")
        
        # Test webhook handler imports
        from payment.webhook_handler_v2 import PhonePeV2WebhookView
        print("✅ Webhook handler imports successful")
        
        # Test status values
        print(f"✅ Payment statuses: {list(PaymentStatus.choices)}")
        print(f"✅ Payment methods: {list(PaymentMethod.choices)}")
        
        # Test service initialization
        service = PaymentService()
        print("✅ PaymentService initialization successful")
        
        print("\n🎉 All imports and initialization tests passed!")
        return True
        
    except Exception as e:
        print(f"❌ Import test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_imports()
    sys.exit(0 if success else 1)
