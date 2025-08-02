#!/usr/bin/env python
import os
import django

# Add the project root directory to the path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

def complete_successful_phonepe_payment():
    print("🔄 COMPLETING SUCCESSFUL PHONEPE PAYMENT")
    print("="*60)
    
    from payments.services import WebhookService
    from payments.models import PaymentOrder
    
    # The payment order from your admin panel
    order_id = 'CART_5fa44890-71a8-492c-a49e-7a40f0aa391b_63B1C707'
    phonepe_txn_id = 'OMO2508030141519490798385'
    
    try:
        # Get the payment
        payment = PaymentOrder.objects.get(merchant_order_id=order_id)
        print(f"💳 Found payment: {payment.merchant_order_id}")
        print(f"   Current status: {payment.status}")
        print(f"   Cart ID: {payment.cart_id}")
        
        # Simulate PhonePe V2 webhook payload for successful payment
        webhook_data = {
            "event": "checkout.order.completed",
            "payload": {
                "transactionId": phonepe_txn_id,
                "merchantOrderId": order_id,
                "amount": payment.amount,
                "state": "COMPLETED",
                "responseCode": "SUCCESS",
                "merchantId": "TEST-M22KEWU5BO1I2"
            }
        }
        
        print(f"\n📡 Simulating webhook with PhonePe data:")
        print(f"   Event: {webhook_data['event']}")
        print(f"   Transaction ID: {webhook_data['payload']['transactionId']}")
        print(f"   Order ID: {webhook_data['payload']['merchantOrderId']}")
        print(f"   Amount: ₹{webhook_data['payload']['amount']}")
        print(f"   State: {webhook_data['payload']['state']}")
        
        # Process webhook
        webhook_service = WebhookService()
        result = webhook_service.process_payment_webhook(webhook_data)
        
        print(f"\n✅ WEBHOOK PROCESSED SUCCESSFULLY!")
        print(f"   Result: {result}")
        
        # Check updated payment status
        payment.refresh_from_db()
        print(f"\n💳 UPDATED PAYMENT STATUS:")
        print(f"   Status: {payment.status}")
        
        # Check cart status
        from cart.models import Cart
        cart = Cart.objects.get(cart_id=payment.cart_id)
        cart.refresh_from_db()
        print(f"   Cart status: {cart.status}")
        
        # Check if booking was created
        from booking.models import Booking
        booking = Booking.objects.filter(cart=cart).first()
        if booking:
            print(f"\n📋 BOOKING CREATED SUCCESSFULLY!")
            print(f"   Booking ID: {booking.book_id}")
            print(f"   Status: {booking.status}")
            print(f"   Total amount: ₹{booking.total_amount}")
            print(f"   Created at: {booking.created_at}")
        else:
            print(f"\n❌ NO BOOKING CREATED")
            
        print(f"\n🎉 PAYMENT COMPLETION SUMMARY:")
        print(f"   PhonePe Transaction: {phonepe_txn_id} ✅")
        print(f"   Payment Status: {payment.status} ✅")
        print(f"   Cart Status: {cart.status} ✅")
        print(f"   Booking Created: {booking.book_id if booking else 'No'} ✅")
        
        # Show what frontend should see now
        print(f"\n🔗 FRONTEND API RESPONSES NOW:")
        print(f"   GET /api/booking/bookings/by-cart/{payment.cart_id}/")
        print(f"   → Should return booking: {booking.book_id if booking else 'None'}")
        print(f"   GET /api/payments/cart/status/{payment.cart_id}/")
        print(f"   → Should return status: {payment.status}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    complete_successful_phonepe_payment()
