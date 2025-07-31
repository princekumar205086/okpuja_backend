#!/usr/bin/env python
"""
Simple PhonePe Payment Test
Tests the actual payment initiation with existing user
"""

import os
import sys
import django
import time

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.conf import settings
from django.contrib.auth import get_user_model
from payment.models import Payment
from payment.gateways import PhonePeGateway

User = get_user_model()

def test_payment_initiation():
    """Test payment initiation with existing user"""
    
    print("💳 PHONEPE PAYMENT INITIATION TEST")
    print("="*50)
    
    try:
        # Initialize gateway
        gateway = PhonePeGateway()
        print(f"✅ Gateway initialized (Merchant: {gateway.merchant_id})")
        
        # Get any existing user or create minimal test user
        try:
            user = User.objects.filter(is_active=True).first()
            if not user:
                # Create minimal user with only required fields
                user = User.objects.create(
                    email='test@okpuja.com',
                    name='Test User',
                    is_active=True
                )
                user.set_password('testpass123')
                user.save()
                print(f"✅ Created test user: {user.email}")
            else:
                print(f"✅ Using existing user: {user.email}")
        except Exception as e:
            print(f"❌ User creation failed: {e}")
            return False
        
        # Create test payment
        payment = Payment.objects.create(
            user=user,
            amount=1.00,  # 1 rupee test
            currency='INR',
            status='pending',
            merchant_transaction_id=f"TEST_{int(time.time())}"
        )
        print(f"✅ Payment created: ID={payment.id}, Amount=₹{payment.amount}")
        
        # Test payment initiation - THIS IS THE CRITICAL TEST
        print("\n🚀 INITIATING PAYMENT (Critical Test)...")
        result = gateway.initiate_payment(payment)
        
        if result.get('success'):
            print("🎉 SUCCESS! Payment initiation worked!")
            print(f"   Payment URL: {result.get('payment_url', '')[:100]}...")
            print(f"   Transaction ID: {result.get('transaction_id')}")
            
            # Clean up
            payment.delete()
            if user.email == 'test@okpuja.com':
                user.delete()
            
            print("\n✅ PhonePe payment gateway is WORKING!")
            print("You can now process real payments in your application.")
            return True
            
        else:
            print("❌ FAILED! Payment initiation failed.")
            print(f"   Error: {result.get('error', 'Unknown error')}")
            print(f"   Error Type: {result.get('error_type', 'Unknown')}")
            
            # Clean up
            payment.delete()
            if user.email == 'test@okpuja.com':
                user.delete()
            
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Testing PhonePe payment functionality...\n")
    success = test_payment_initiation()
    
    if success:
        print("\n" + "="*50)
        print("🎉 PHONEPE GATEWAY IS WORKING!")
        print("Your payment system is ready for production.")
        print("="*50)
    else:
        print("\n" + "="*50)
        print("❌ ISSUES FOUND - Please check the error above")
        print("="*50)
    
    sys.exit(0 if success else 1)
