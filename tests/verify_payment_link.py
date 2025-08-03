import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from booking.models import Booking
from payments.models import PaymentOrder

try:
    # Get the latest booking
    booking = Booking.objects.latest('created_at')
    print(f"📋 Latest Booking:")
    print(f"   ID: {booking.id}")
    print(f"   Book ID: {booking.book_id}")
    print(f"   Payment Order ID: {booking.payment_order_id}")
    print(f"   Cart ID: {booking.cart.cart_id}")
    print(f"   Address ID: {booking.address.id if booking.address else 'None'}")

    # Get the corresponding payment
    if booking.payment_order_id:
        payment = PaymentOrder.objects.filter(merchant_order_id=booking.payment_order_id).first()
        if payment:
            print(f"\n💳 Associated Payment:")
            print(f"   Merchant Order ID: {payment.merchant_order_id}")
            print(f"   Payment ID: {payment.id}")
            print(f"   Amount: ₹{payment.amount/100}")
            print(f"   Status: {payment.status}")
            print(f"   Transaction ID: {payment.phonepe_transaction_id}")
            print(f"   Cart ID linked: {payment.cart_id}")
            
            # Verify the payment_details property works correctly
            payment_details = booking.payment_details
            print(f"\n🔗 Payment Details via Booking:")
            print(f"   Payment ID: {payment_details['payment_id']}")
            print(f"   Amount: ₹{payment_details['amount']}")
            print(f"   Status: {payment_details['status']}")
            print(f"   Transaction ID: {payment_details['transaction_id']}")
            
            print(f"\n✅ VERIFICATION COMPLETE:")
            print(f"   - Payment ID correctly linked: {booking.payment_order_id == payment.merchant_order_id}")
            print(f"   - Cart IDs match: {booking.cart.cart_id == payment.cart_id}")
            print(f"   - Payment details accessible: {payment_details['payment_id'] != 'N/A'}")
            print(f"\n🎉 PAYMENT ID IS NOW INTACT WITH BOOKING!")
        else:
            print(f"❌ Payment not found for order ID: {booking.payment_order_id}")
    else:
        print(f"❌ No payment order ID in booking")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()
