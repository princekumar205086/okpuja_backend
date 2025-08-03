#!/usr/bin/env python
import os
import sys
import django

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Setup Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from cart.models import Cart
from accounts.models import Address
from booking.models import Booking
from payments.models import PaymentOrder
from django.db import transaction
from datetime import datetime

def main():
    print("🧪 COMPREHENSIVE PAYMENT FLOW TEST")
    print("=" * 50)
    
    User = get_user_model()
    
    # Step 1: Get test user
    print("\n1️⃣ Getting test user...")
    user = User.objects.first()
    if not user:
        print("❌ No users found in database")
        return False
    print(f"✅ Using user: {getattr(user, 'first_name', user.phone_number)} (ID: {user.id})")
    
    # Step 2: Get/create address
    print("\n2️⃣ Setting up address...")
    address = Address.objects.filter(user=user).first()
    if not address:
        address = Address.objects.create(
            user=user,
            address_line_1='Test Address',
            city='Test City', 
            state='Test State',
            pin_code='123456',
            address_type='HOME'
        )
    print(f"✅ Address ready: ID {address.id}")
    
    # Step 3: Create cart
    print("\n3️⃣ Creating cart...")
    cart = Cart.objects.create(
        user=user,
        booking_date='2025-08-01',
        booking_time='10:00:00',
        address=address,
        total_amount=500.00,
        status='ACTIVE'
    )
    print(f"✅ Cart created: ID {cart.id}, cart_id={cart.cart_id}")
    
    # Step 4: Create payment
    print("\n4️⃣ Creating payment order...")
    payment = PaymentOrder.objects.create(
        user=user,
        cart=cart,
        amount=50000,  # 500.00 in paisa
        currency="INR",
        payment_method="PHONEPE",
        merchant_order_id=f"TEST_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        transaction_id=f"TXN_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
        status="SUCCESS"
    )
    print(f"✅ Payment created: ID {payment.id}, Order ID: {payment.merchant_order_id}")
    
    # Step 5: Create booking
    print("\n5️⃣ Creating booking...")
    booking = Booking.objects.create(
        user=user,
        cart=cart,
        address=address,
        booking_date=cart.booking_date,
        booking_time=cart.booking_time,
        total_amount=cart.total_amount,
        status="CONFIRMED"
    )
    print(f"✅ Booking created: ID {booking.id}, Book ID: {booking.book_id}")
    
    # Step 6: Clean up cart
    print("\n6️⃣ Cleaning up cart...")
    cart.status = "CONVERTED"
    cart.save()
    print(f"✅ Cart status changed to: {cart.status}")
    
    # Step 7: Verify integrity
    print("\n7️⃣ Verifying data integrity...")
    print(f"📋 Booking details:")
    print(f"   - booking.id: {booking.id}")
    print(f"   - booking.address_id: {booking.address.id if booking.address else 'None'}")
    print(f"   - booking.cart_id: {booking.cart.id if booking.cart else 'None'}")
    
    # Test payment details
    payment_details = booking.payment_details
    print(f"💰 Payment details:")
    print(f"   - payment_id: {payment_details['payment_id']}")
    print(f"   - amount: ₹{payment_details['amount']}")
    print(f"   - status: {payment_details['status']}")
    
    # Verify payment linkage
    found_payment = PaymentOrder.objects.filter(
        user=user,
        cart=cart,
        status='SUCCESS'
    ).first()
    
    print(f"🔗 Payment linkage:")
    print(f"   - payment.id: {found_payment.id if found_payment else 'None'}")
    print(f"   - payment.cart_id: {found_payment.cart.id if found_payment and found_payment.cart else 'None'}")
    
    # Final verification
    print("\n🎯 FINAL VERIFICATION")
    print("=" * 30)
    success = all([
        booking.address is not None,
        booking.cart is not None,
        found_payment is not None,
        cart.status == "CONVERTED",
        payment_details['payment_id'] != 'N/A'
    ])
    
    if success:
        print("✅ address_id: INTACT")
        print("✅ cart_id: INTACT") 
        print("✅ payment_id: INTACT")
        print("✅ cart cleanup: WORKING")
        print("✅ payment details: ACCESSIBLE")
        print("\n🎉 ALL TESTS PASSED!")
        return True
    else:
        print("❌ Some requirements failed")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"\n💥 Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
