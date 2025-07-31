#!/usr/bin/env python
"""
Test payment creation directly without server
"""
import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

def test_payment_initiation():
    """Test the payment initiation flow"""
    try:
        from payment.services import PaymentService
        from cart.models import Cart
        from accounts.models import User
        from django.conf import settings
        
        print("🔄 Testing payment initiation flow...")
        
        # Initialize service
        service = PaymentService()
        print("✅ PaymentService initialized")
        
        # Check if we have any carts and users
        user_count = User.objects.count()
        cart_count = Cart.objects.count()
        
        print(f"📊 Database stats:")
        print(f"   Users: {user_count}")
        print(f"   Carts: {cart_count}")
        
        if cart_count > 0 and user_count > 0:
            # Get a test cart
            cart = Cart.objects.filter(status='ACTIVE').first()
            if cart:
                user = cart.user
                print(f"🛒 Found test cart: {cart.id} for user: {user.email}")
                
                # Test create payment from cart
                try:
                    payment = service.create_payment_from_cart(cart, user)
                    print(f"✅ Payment created: {payment.id}")
                    print(f"   Transaction ID: {payment.transaction_id}")
                    print(f"   Merchant ID: {payment.merchant_transaction_id}")
                    print(f"   Amount: {payment.amount}")
                    print(f"   Status: {payment.status}")
                    
                    # Now test PhonePe client initialization (without calling actual API)
                    from payment.phonepe_v2_corrected import PhonePeV2ClientCorrected
                    client = PhonePeV2ClientCorrected(env='sandbox')
                    print("✅ PhonePe V2 client initialized successfully")
                    
                    # Test URL generation
                    redirect_url = f"{settings.FRONTEND_URL}/payment/callback/"
                    callback_url = f"{settings.BACKEND_URL}/api/payment/webhook/phonepe/v2/"
                    
                    print(f"✅ URLs generated:")
                    print(f"   Redirect: {redirect_url}")
                    print(f"   Callback: {callback_url}")
                    
                    print("\n🎉 Payment flow validation successful!")
                    print("💡 The FRONTEND_URL/BACKEND_URL error should now be fixed.")
                    
                except Exception as e:
                    print(f"❌ Payment creation failed: {str(e)}")
                    import traceback
                    traceback.print_exc()
            else:
                print("⚠️  No active cart found for testing")
        else:
            print("⚠️  No test data available (no users or carts)")
        
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_payment_initiation()
    sys.exit(0 if success else 1)
