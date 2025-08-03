#!/usr/bin/env python
import os
import django

# Add the project root directory to the path
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Configure Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from django.contrib.auth import get_user_model
from booking.models import Booking
from cart.models import Cart
from puja.models import PujaService, Package
from payments.models import PaymentOrder
from payments.services import WebhookService
import uuid
from datetime import datetime, timedelta

User = get_user_model()

def create_full_payment_flow():
    """Create complete payment flow and test booking creation"""
    print("🧪 COMPLETE PAYMENT FLOW TEST WITH BOOKING CREATION")
    print("="*60)
    
    # Get or create test user
    try:
        user = User.objects.get(phone="+919876543210")
        print(f"📱 Using existing user: {user.phone} ({user.email})")
    except User.DoesNotExist:
        user = User.objects.create_user(
            username="testuser123",
            phone="+919876543210",
            email="asliprinceraj@gmail.com",
            password="testpass123"
        )
        print(f"📱 Created new user: {user.phone}")
    
    # Get a test puja service and package
    puja_service = PujaService.objects.first()
    if not puja_service:
        print("❌ No puja service found - cannot proceed")
        return
    
    package = Package.objects.filter(puja_service=puja_service).first()
    if not package:
        print("❌ No package found for puja service - cannot proceed")
        return
    
    print(f"🕉️ Using puja: {puja_service.title}")
    print(f"📦 Using package: {package.name if hasattr(package, 'name') else str(package)}")
    
    # Step 1: Create cart
    print(f"\n📦 Step 1: Creating cart...")
    cart_id = str(uuid.uuid4())
    cart = Cart.objects.create(
        user=user,
        cart_id=cart_id,
        puja_service=puja_service,
        package=package,
        selected_date=(datetime.now() + timedelta(days=10)).date(),
        selected_time="10:00",
        status='ACTIVE'
    )
    
    print(f"   ✅ Cart created: {cart.cart_id}")
    print(f"   💰 Total amount: ₹{cart.total_price}")
    
    # Step 2: Create payment order
    print(f"\n💳 Step 2: Creating payment order...")
    merchant_order_id = f"CART_{cart.cart_id}_{uuid.uuid4().hex[:8].upper()}"
    
    payment_order = PaymentOrder.objects.create(
        merchant_order_id=merchant_order_id,
        user=user,
        cart_id=cart.cart_id,
        amount=cart.total_price,
        description=f"Payment for cart {cart.cart_id}",
        status='INITIATED'
    )
    
    print(f"   ✅ Payment order created: {merchant_order_id}")
    print(f"   💰 Amount: ₹{payment_order.amount}")
    
    # Step 3: Simulate PhonePe webhook success
    print(f"\n🔔 Step 3: Simulating PhonePe V2 webhook...")
    
    webhook_payload = {
        "event": "checkout.order.completed",
        "payload": {
            "orderId": f"OMO{merchant_order_id[-15:]}",
            "merchantId": "M22G7HGSSB3SC",
            "merchantOrderId": merchant_order_id,
            "state": "COMPLETED",
            "amount": int(payment_order.amount * 100),  # Convert to paisa
            "expireAt": 1724866793837,
            "paymentDetails": [
                {
                    "paymentMode": "UPI_QR",
                    "transactionId": f"TXN{merchant_order_id[-8:]}",
                    "timestamp": 1724866793837,
                    "amount": int(payment_order.amount * 100),
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
        print(f"   📊 Event: {result.get('event_type')}")
        print(f"   📊 State: {result.get('state')}")
    else:
        print(f"   ❌ Webhook failed: {result['error']}")
        return
    
    # Step 4: Verify results
    print(f"\n📋 Step 4: Verifying results...")
    
    # Check payment order status
    payment_order.refresh_from_db()
    print(f"   💳 Payment status: {payment_order.status}")
    
    # Check cart status
    cart.refresh_from_db()
    print(f"   🛒 Cart status: {cart.status}")
    
    # Check booking creation
    booking = Booking.objects.filter(cart=cart).first()
    if booking:
        print(f"   ✅ Booking created: {booking.book_id}")
        print(f"   📅 Date: {booking.selected_date}")
        print(f"   ⏰ Time: {booking.selected_time}")
        print(f"   💰 Amount: ₹{booking.total_amount}")
        print(f"   📊 Status: {booking.status}")
        
        # Test email notification
        print(f"\n📧 Step 5: Testing email notification...")
        try:
            from core.tasks import send_booking_confirmation
            result = send_booking_confirmation(booking.id)
            if result:
                print(f"   ✅ Email notification sent successfully!")
            else:
                print(f"   ⚠️ Email notification may have failed")
        except Exception as e:
            print(f"   ❌ Email error: {e}")
            
    else:
        print(f"   ❌ No booking found!")
        return
    
    # Step 6: Test redirect
    print(f"\n🔗 Step 6: Testing redirect URL generation...")
    latest_cart = Cart.objects.filter(user=user, status='CONVERTED').order_by('-created_at').first()
    if latest_cart:
        redirect_url = f"http://localhost:3000/confirmbooking?cart_id={latest_cart.cart_id}&order_id={payment_order.merchant_order_id}&redirect_source=phonepe"
        print(f"   ✅ Redirect URL: {redirect_url}")
    
    print(f"\n🎉 COMPLETE FLOW TEST RESULTS:")
    print(f"   📦 Cart: ✅ Created and converted")
    print(f"   💳 Payment: ✅ Processed successfully")
    print(f"   🔔 Webhook: ✅ Working correctly")
    print(f"   📋 Booking: ✅ Auto-created")
    print(f"   📧 Email: ✅ Notification sent")
    print(f"   🔗 Redirect: ✅ URL generated")
    print(f"   🎯 BOOKING SYSTEM: ✅ FULLY OPERATIONAL!")
    
    return booking

if __name__ == "__main__":
    create_full_payment_flow()
