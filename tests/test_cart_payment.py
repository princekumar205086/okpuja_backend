#!/usr/bin/env python
"""
Test cart payment endpoint with real data
"""
import os
import sys
import django

# Setup Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

def test_cart_payment():
    """Test cart payment creation"""
    try:
        from django.contrib.auth import get_user_model
        from cart.models import Cart
        from payments.models import PaymentOrder
        from payments.services import PaymentService
        
        User = get_user_model()
        
        # Get test user
        user = User.objects.filter(email='asliprinceraj@gmail.com').first()
        if not user:
            print("❌ Test user not found")
            return False
        
        print(f"✅ Found user: {user.email} (ID: {user.id})")
        
        # Get the latest cart for this user
        cart = Cart.objects.filter(user=user, status=Cart.StatusChoices.ACTIVE).first()
        if not cart:
            print("❌ No active cart found")
            return False
        
        print(f"✅ Found cart: {cart.cart_id}")
        print(f"   Cart total: ₹{cart.total_price}")
        print(f"   Cart status: {cart.status}")
        
        # Test PaymentService directly
        payment_service = PaymentService()
        
        # Calculate amount in paisa
        amount_in_paisa = int(float(cart.total_price) * 100)
        print(f"   Amount in paisa: {amount_in_paisa}")
        
        # Test payment creation
        result = payment_service.create_payment_order(
            user=user,
            amount=amount_in_paisa,
            cart_id=cart.cart_id,
            redirect_url="http://localhost:3000/confirmbooking",
            description=f"Payment for cart {cart.cart_id}"
        )
        
        if result['success']:
            payment_order = result['payment_order']
            print(f"✅ Payment order created: {payment_order.merchant_order_id}")
            print(f"   Payment ID: {payment_order.id}")
            print(f"   Cart ID: {payment_order.cart_id}")
            print(f"   Status: {payment_order.status}")
            print(f"   Amount: ₹{payment_order.amount_in_rupees}")
            
            if payment_order.phonepe_payment_url:
                print(f"   PhonePe URL: {payment_order.phonepe_payment_url[:50]}...")
            else:
                print("   ⚠️  No PhonePe URL generated")
            
            return True
        else:
            print(f"❌ Payment creation failed: {result.get('error')}")
            return False
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("💳 Testing Cart Payment Creation\n")
    success = test_cart_payment()
    
    if success:
        print("\n🎉 Cart payment test passed!")
    else:
        print("\n❌ Cart payment test failed!")
