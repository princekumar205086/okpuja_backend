#!/usr/bin/env python
import os
import django

# Add the project root directory to the path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

def check_latest_payment_status():
    print("🔍 CHECKING LATEST PAYMENT STATUS")
    print("="*60)
    
    from payments.models import PaymentOrder
    from cart.models import Cart
    from booking.models import Booking
    from django.contrib.auth import get_user_model
    
    try:
        # Get the latest payment
        latest_payment = PaymentOrder.objects.filter(
            merchant_order_id__contains='CART_5fa44890-71a8-492c-a49e-7a40f0aa391b'
        ).first()
        
        if latest_payment:
            print(f"💳 LATEST PAYMENT DETAILS:")
            print(f"   Order ID: {latest_payment.merchant_order_id}")
            print(f"   Status: {latest_payment.status}")
            print(f"   Amount: ₹{latest_payment.amount}")
            print(f"   Cart ID: {latest_payment.cart_id}")
            print(f"   Created: {latest_payment.created_at}")
            
            # Check if cart exists
            if latest_payment.cart_id:
                try:
                    cart = Cart.objects.get(cart_id=latest_payment.cart_id)
                    print(f"\n📦 CART STATUS:")
                    print(f"   Cart ID: {cart.cart_id}")
                    print(f"   Status: {cart.status}")
                    print(f"   Total Price: ₹{cart.total_price}")
                    
                    # Check if booking exists
                    booking = Booking.objects.filter(cart=cart).first()
                    if booking:
                        print(f"\n📋 BOOKING STATUS:")
                        print(f"   Booking ID: {booking.book_id}")
                        print(f"   Status: {booking.status}")
                        print(f"   Total Amount: ₹{booking.total_amount}")
                    else:
                        print(f"\n❌ NO BOOKING FOUND")
                        print(f"   Reason: Payment status is {latest_payment.status}")
                        print(f"   Solution: Need to update payment to SUCCESS")
                        
                except Cart.DoesNotExist:
                    print(f"\n❌ CART NOT FOUND: {latest_payment.cart_id}")
            
            # Check PhonePe transaction ID
            phonepe_txn_id = "OMO2508030141519490798385"
            print(f"\n🔗 PHONEPE TRANSACTION:")
            print(f"   Transaction ID: {phonepe_txn_id}")
            print(f"   Status in PhonePe: SUCCESS (as per your screenshot)")
            print(f"   Status in our system: {latest_payment.status}")
            print(f"   ⚠️ MISMATCH: PhonePe shows SUCCESS, our system shows INITIATED")
            
        else:
            print(f"❌ No payment found with cart ID 5fa44890-71a8-492c-a49e-7a40f0aa391b")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    check_latest_payment_status()
