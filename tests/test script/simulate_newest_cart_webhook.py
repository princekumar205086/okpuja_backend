#!/usr/bin/env python
import os
import django

# Add the project root directory to the path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

def simulate_webhook_for_newest_cart():
    print("🔄 SIMULATING WEBHOOK FOR NEWEST CART")
    print("="*60)
    
    from payments.services import WebhookService
    from payments.models import PaymentOrder
    
    # Your newest cart
    newest_cart_id = 'd7a594ac-9333-4213-985f-67942a3b638b'
    order_id = 'CART_d7a594ac-9333-4213-985f-67942a3b638b_260E14E5'
    
    try:
        # Get the payment
        payment = PaymentOrder.objects.get(merchant_order_id=order_id)
        print(f"💳 Found payment: {payment.merchant_order_id}")
        print(f"   Current status: {payment.status}")
        print(f"   Cart ID: {payment.cart_id}")
        
        # Simulate PhonePe V2 webhook payload
        webhook_data = {
            "event": "checkout.order.completed",
            "payload": {
                "transactionId": f"T{order_id}",
                "merchantOrderId": order_id,
                "amount": payment.amount,
                "state": "COMPLETED",
                "responseCode": "SUCCESS",
                "merchantId": "TEST-M22KEWU5BO1I2"
            }
        }
        
        print(f"\n📡 Simulating webhook with payload:")
        print(f"   Event: {webhook_data['event']}")
        print(f"   Order ID: {webhook_data['payload']['merchantOrderId']}")
        print(f"   Amount: ₹{webhook_data['payload']['amount']}")
        
        # Process webhook
        webhook_service = WebhookService()
        result = webhook_service.process_payment_webhook(webhook_data)
        
        print(f"\n✅ Webhook processed successfully!")
        print(f"   Result: {result}")
        
        # Check updated payment status
        payment.refresh_from_db()
        print(f"\n💳 UPDATED PAYMENT STATUS:")
        print(f"   Status: {payment.status}")
        
        # Check if booking was created
        from booking.models import Booking
        from cart.models import Cart
        
        cart = Cart.objects.get(cart_id=newest_cart_id)
        cart.refresh_from_db()
        print(f"   Cart status: {cart.status}")
        
        booking = Booking.objects.filter(cart=cart).first()
        if booking:
            print(f"   Booking created: {booking.book_id}")
            print(f"   Booking status: {booking.status}")
            print(f"   Total amount: ₹{booking.total_amount}")
        else:
            print(f"   ❌ No booking created")
            
        print(f"\n🔗 NOW TRY THE REDIRECT AGAIN!")
        print(f"   Visit: http://127.0.0.1:8000/api/payments/redirect/simple/")
        print(f"   Expected redirect to: cart_id={newest_cart_id}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    simulate_webhook_for_newest_cart()
