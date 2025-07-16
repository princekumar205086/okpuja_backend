#!/usr/bin/env python3
"""
Quick Production Server Test for PhonePe Integration
Run this to verify the fixes are working
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from payment.gateways import PhonePeGateway
from payment.models import Payment, PaymentStatus, PaymentMethod
from cart.models import Cart
from accounts.models import User

def test_production_payment():
    """Test payment creation on production"""
    print("🚀 Testing PhonePe Payment Integration on Production")
    print("=" * 60)
    
    try:
        # Create test user if needed
        user, created = User.objects.get_or_create(
            email='test@okpuja.com',
            defaults={
                'username': 'testuser',
                'phone': '9876543210'
            }
        )
        if created:
            user.set_password('testpass123')
            user.save()
            print("✅ Test user created")
        else:
            print("✅ Using existing test user")
        
        # Get or create test cart
        cart = Cart.objects.filter(user=user, status='ACTIVE').first()
        if not cart:
            print("❌ No active cart found. Create a cart first through the API.")
            return
        
        print(f"✅ Using cart: {cart.cart_id}")
        
        # Create payment instance
        payment = Payment.objects.create(
            user=user,
            cart=cart,
            amount=cart.total_price,
            currency='INR',
            method=PaymentMethod.PHONEPE,
            status=PaymentStatus.PENDING
        )
        
        print(f"✅ Payment created: {payment.transaction_id}")
        
        # Initialize PhonePe gateway
        gateway = PhonePeGateway()
        print(f"✅ Gateway initialized")
        print(f"   Merchant ID: {gateway.merchant_id}")
        print(f"   Base URL: {gateway.base_url}")
        print(f"   Timeout: {gateway.timeout}s")
        print(f"   Max Retries: {gateway.max_retries}")
        
        # Test payment initiation
        print(f"\n📱 Testing payment initiation...")
        try:
            result = gateway.initiate_payment(payment)
            
            print(f"✅ Payment initiation successful!")
            print(f"   Payment URL: {result.get('payment_url', 'Not provided')}")
            print(f"   Transaction ID: {result.get('transaction_id')}")
            print(f"   Merchant TX ID: {result.get('merchant_transaction_id')}")
            
            return True
            
        except Exception as e:
            print(f"❌ Payment initiation failed: {str(e)}")
            print(f"   Error type: {type(e).__name__}")
            
            # Provide debugging info
            if "Connection refused" in str(e):
                print(f"\n🔍 Diagnosis: Network connectivity issue")
                print(f"   - Check firewall rules for outbound HTTPS")
                print(f"   - Verify PhonePe domains are whitelisted")
                print(f"   - Contact hosting provider")
            elif "timeout" in str(e).lower():
                print(f"\n🔍 Diagnosis: Network timeout issue")
                print(f"   - Slow network connection to PhonePe")
                print(f"   - Increase timeout settings")
            elif "SSL" in str(e):
                print(f"\n🔍 Diagnosis: SSL/Certificate issue")
                print(f"   - Check server SSL configuration")
                print(f"   - Verify certificate trust store")
            
            return False
            
    except Exception as e:
        print(f"❌ Test setup failed: {str(e)}")
        return False

def main():
    """Main test function"""
    print("🏥 Production Server Health Check")
    print("=" * 60)
    
    # Test 1: Django setup
    try:
        from django.conf import settings
        print(f"✅ Django setup successful")
        print(f"   Debug: {settings.DEBUG}")
        print(f"   PhonePe Env: {getattr(settings, 'PHONEPE_ENV', 'Not Set')}")
        print(f"   Production Server: {getattr(settings, 'PRODUCTION_SERVER', False)}")
    except Exception as e:
        print(f"❌ Django setup failed: {e}")
        return
    
    # Test 2: Database connection
    try:
        User.objects.count()
        print(f"✅ Database connection successful")
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return
    
    # Test 3: Payment integration
    success = test_production_payment()
    
    print(f"\n" + "=" * 60)
    if success:
        print(f"🎉 Production test PASSED!")
        print(f"   PhonePe integration is working correctly")
        print(f"   Ready for live payments")
    else:
        print(f"⚠️  Production test FAILED!")
        print(f"   Review the error messages above")
        print(f"   Check PRODUCTION_CONNECTIVITY_SOLUTION.md for fixes")
        print(f"   Run test_simple_connectivity.py for detailed diagnosis")

if __name__ == "__main__":
    main()
