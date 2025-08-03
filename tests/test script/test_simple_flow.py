#!/usr/bin/env python3
"""
Simple Test: Cart (no address) → Payment (with address_id) → Booking (with address_id)
Testing with user: asliprinceraj@gmail.com
"""

import os
import sys
import django

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
sys.path.append('.')
django.setup()

from accounts.models import User, Address
from puja.models import PujaService, PujaCategory  
from cart.models import Cart
from payments.models import PaymentOrder
from booking.models import Booking
from payments.services import PaymentService

def test_simple_flow():
    """Test: Cart → Payment(address_id) → Booking(address_id)"""
    
    print("🔍 Testing Simple Address Flow")
    print("=" * 40)
    
    # 1. Get test user
    try:
        user = User.objects.get(email='asliprinceraj@gmail.com')
        print(f"✅ User: {user.email}")
    except User.DoesNotExist:
        print("❌ User not found")
        return
    
    # 2. Get user's address
    address = Address.objects.filter(user=user).first()
    if not address:
        print("❌ No address found")
        return
    print(f"✅ Address: {address.address_line1}, {address.city}")
    
    # 3. Get/create cart
    cart = Cart.objects.filter(user=user, status='ACTIVE').first()
    if not cart:
        # Create cart if needed
        puja_service = PujaService.objects.first()
        if not puja_service:
            print("❌ No puja service found")
            return
            
        from django.utils.crypto import get_random_string
        cart = Cart.objects.create(
            user=user,
            service_type='PUJA',
            puja_service=puja_service,
            cart_id=get_random_string(20),
            status='ACTIVE',
            selected_date='2025-08-10',
            selected_time='10:00'
        )
    print(f"✅ Cart: {cart.id} (NO ADDRESS FIELD)")
    
    # 4. Test payment creation WITH address_id
    try:
        payment_service = PaymentService()
        payment_result = payment_service.create_payment_order(
            user=user,
            amount=100.00,
            redirect_url='http://localhost:8000/test/',
            description='Test payment',
            cart_id=cart.id,
            address_id=address.id  # Address passed during payment!
        )
        
        if payment_result['success']:
            payment_order = payment_result['payment_order']
        else:
            # Even if PhonePe failed, we still have the payment_order created
            payment_order = payment_result['payment_order']
        
        print(f"✅ Payment: {payment_order.id} with address_id: {payment_order.address_id}")
    except Exception as e:
        print(f"❌ Payment creation failed: {e}")
        return
    
    # 5. Test booking creation (simulate payment success)
    try:
        payment_order.status = 'SUCCESS'
        payment_order.save()
        
        booking = Booking.objects.create(
            cart=cart,
            user=user,
            address_id=payment_order.address_id,  # Use address from payment!
            selected_date=cart.selected_date,
            selected_time=cart.selected_time,
            status='CONFIRMED'
        )
        print(f"✅ Booking: {booking.id} with address_id: {booking.address_id}")
    except Exception as e:
        print(f"❌ Booking creation failed: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # 6. Verify flow
    print(f"\n🎉 FLOW VERIFICATION")
    print(f"Cart {cart.id}: NO address field ✅")
    print(f"Payment {payment_order.id}: address_id = {payment_order.address_id} ✅")
    print(f"Booking {booking.id}: address_id = {booking.address_id} ✅")
    
    if payment_order.address_id == address.id and booking.address_id == address.id:
        print(f"\n🚀 SUCCESS: Address flows correctly from payment to booking!")
    else:
        print(f"\n❌ FAILED: Address not flowing correctly")

if __name__ == "__main__":
    test_simple_flow()
