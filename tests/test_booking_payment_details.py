import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from booking.models import Booking
from payments.models import PaymentOrder
from booking.serializers import BookingSerializer

try:
    # Get the specific booking mentioned (BK-AE8348BC)
    booking = Booking.objects.get(book_id='BK-AE8348BC')
    print(f"📋 Booking Found:")
    print(f"   ID: {booking.id}")
    print(f"   Book ID: {booking.book_id}")
    print(f"   Payment Order ID: {booking.payment_order_id}")
    print(f"   Cart ID: {booking.cart.cart_id}")
    print(f"   User: {booking.user.email}")
    
    # Check payment_details property
    payment_details = booking.payment_details
    print(f"\n💳 Payment Details Property:")
    for key, value in payment_details.items():
        print(f"   {key}: {value}")
    
    # Check if payment exists
    if booking.payment_order_id:
        payment = PaymentOrder.objects.filter(merchant_order_id=booking.payment_order_id).first()
        if payment:
            print(f"\n✅ Payment Found: {payment.merchant_order_id}")
            print(f"   Status: {payment.status}")
            print(f"   Amount: ₹{payment.amount/100}")
        else:
            print(f"\n❌ No payment found for order ID: {booking.payment_order_id}")
    else:
        print(f"\n❌ No payment_order_id in booking")
    
    # Test serializer output
    print(f"\n🔧 Testing Serializer:")
    serializer = BookingSerializer(booking)
    serialized_data = serializer.data
    
    if 'payment_details' in serialized_data:
        print(f"✅ Payment details in serializer:")
        for key, value in serialized_data['payment_details'].items():
            print(f"   {key}: {value}")
    else:
        print(f"❌ Payment details NOT in serializer output")
        print(f"Available keys: {list(serialized_data.keys())}")
        
except Booking.DoesNotExist:
    print("❌ Booking BK-AE8348BC not found")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
