#!/usr/bin/env python3
import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from cart.models import Cart
from payment.models import Payment
from payment.gateways import get_payment_gateway
import json

def test_payment_creation_flow():
    """Test the complete payment creation flow that production uses"""
    
    print("🧪 TESTING COMPLETE PAYMENT CREATION FLOW")
    print("=" * 50)
    
    try:
        # Get user
        User = get_user_model()
        user = User.objects.get(email='asliprinceraj@gmail.com')
        print(f"✅ Found user: {user.email}")
        
        # Get cart 28
        cart = Cart.objects.get(id=28, user=user, status='ACTIVE')
        print(f"✅ Found cart: ID={cart.id}, Total=₹{cart.total_price}")
        
        # Create payment exactly as the view does
        print("🔧 Creating payment...")
        payment = Payment.objects.create(
            cart=cart,
            user=user,
            amount=cart.total_price,
            method='PHONEPE',
            currency='INR'
        )
        print(f"✅ Payment created: ID={payment.id}, Amount=₹{payment.amount}")
        
        # Get gateway and initiate payment
        print("🔧 Getting PhonePe gateway...")
        gateway = get_payment_gateway('phonepe')
        print("✅ Gateway obtained")
        
        print("🚀 Initiating payment with gateway...")
        gateway_response = gateway.initiate_payment(payment)
        print(f"✅ Gateway response: {json.dumps(gateway_response, indent=2)}")
        
        print("🎉 COMPLETE SUCCESS! The flow works perfectly.")
        
    except Exception as e:
        print(f"❌ Error in flow: {e}")
        print(f"❌ Error type: {type(e).__name__}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_payment_creation_flow()
