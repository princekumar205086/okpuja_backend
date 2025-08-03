#!/usr/bin/env python
import os
import django

# Add the project root directory to the path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from cart.models import Cart
from payments.models import PaymentOrder
from booking.models import Booking
from payments.services import WebhookService

def simulate_payment_success():
    new_cart_id = '33dd806a-6989-47f5-a840-e588a73e11eb'
    
    print("🧪 SIMULATING PAYMENT SUCCESS FOR NEW CART")
    print("="*50)
    
    try:
        # Get the payment order
        payment = PaymentOrder.objects.filter(cart_id=new_cart_id).first()
        if not payment:
            print("❌ No payment found for new cart")
            return
        
        print(f"📦 Cart: {new_cart_id}")
        print(f"💳 Payment: {payment.merchant_order_id}")
        print(f"📊 Current Status: {payment.status}")
        
        # Simulate PhonePe webhook success
        print(f"\n🔔 Simulating PhonePe webhook success...")
        
        webhook_payload = {
            "event": "checkout.order.completed",
            "payload": {
                "orderId": f"OMO{payment.merchant_order_id[-15:]}",
                "merchantId": "M22G7HGSSB3SC",
                "merchantOrderId": payment.merchant_order_id,
                "state": "COMPLETED",
                "amount": int(payment.amount * 100),  # Convert to paisa
                "paymentDetails": [
                    {
                        "paymentMode": "UPI_QR",
                        "transactionId": f"TXN{payment.merchant_order_id[-8:]}",
                        "timestamp": 1724866793837,
                        "amount": int(payment.amount * 100),
                        "state": "COMPLETED"
                    }
                ]
            }
        }
        
        # Process webhook
        webhook_service = WebhookService()
        result = webhook_service.process_payment_webhook(webhook_payload)
        
        if result['success']:
            print(f"   ✅ Webhook processed successfully!")
            
            # Check results
            payment.refresh_from_db()
            cart = Cart.objects.get(cart_id=new_cart_id)
            cart.refresh_from_db()
            booking = Booking.objects.filter(cart=cart).first()
            
            print(f"\n📊 Results:")
            print(f"   💳 Payment Status: {payment.status}")
            print(f"   🛒 Cart Status: {cart.status}")
            print(f"   📋 Booking: {booking.book_id if booking else 'None'}")
            
            if booking:
                print(f"   📅 Date: {booking.selected_date}")
                print(f"   ⏰ Time: {booking.selected_time}")
                print(f"   💰 Amount: ₹{booking.total_amount}")
                print(f"   📊 Status: {booking.status}")
                
                print(f"\n🔗 Now your redirect should work!")
                print(f"URL: http://localhost:3000/confirmbooking?cart_id={new_cart_id}&order_id={payment.merchant_order_id}&redirect_source=phonepe")
            
        else:
            print(f"   ❌ Webhook failed: {result['error']}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    simulate_payment_success()
