#!/usr/bin/env python
"""
Test script to verify cart and payments integration
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

def test_cart_payments_integration():
    """Test that cart and payments work together"""
    try:
        # Test imports
        from cart.models import Cart
        from payments.models import PaymentOrder
        print("✅ Both Cart and PaymentOrder models imported successfully")
        
        # Test cart methods
        from django.contrib.auth import get_user_model
        from datetime import date
        
        User = get_user_model()
        user = User.objects.first()
        
        if not user:
            print("❌ No users found for testing")
            return False
        
        # Create a test cart
        cart = Cart(
            user=user,
            selected_date=date.today(),
            selected_time="10:00 AM",
            cart_id="TEST-CART-123",
            status=Cart.StatusChoices.ACTIVE
        )
        
        print("✅ Cart instance created successfully")
        
        # Test cart methods
        can_delete = cart.can_be_deleted()
        print(f"✅ can_be_deleted() works: {can_delete}")
        
        deletion_info = cart.get_deletion_info()
        print(f"✅ get_deletion_info() works: {deletion_info}")
        
        cleanup_result = cart.auto_cleanup_old_payments()
        print(f"✅ auto_cleanup_old_payments() works: {cleanup_result}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_payment_order_cart_integration():
    """Test PaymentOrder cart_id field"""
    try:
        from payments.models import PaymentOrder
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        user = User.objects.first()
        
        if not user:
            print("❌ No users found for testing")
            return False
        
        # Create a test payment order
        payment = PaymentOrder(
            merchant_order_id="TEST-ORDER-123",
            user=user,
            cart_id="TEST-CART-123",
            amount=100000,  # ₹1000 in paisa
            redirect_url="http://localhost:3000/success"
        )
        
        print("✅ PaymentOrder with cart_id created successfully")
        print(f"✅ cart_id field accessible: {payment.cart_id}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error creating PaymentOrder: {e}")
        return False

if __name__ == "__main__":
    print("Testing cart and payments integration...")
    
    success1 = test_cart_payments_integration()
    success2 = test_payment_order_cart_integration()
    
    if success1 and success2:
        print("\n🎉 All integration tests passed!")
        print("Cart and payments apps are properly integrated.")
    else:
        print("\n❌ Integration tests failed!")
        
    sys.exit(0 if (success1 and success2) else 1)
