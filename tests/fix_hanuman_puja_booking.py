#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

from payments.models import PaymentOrder
from cart.models import Cart
from booking.models import Booking
from accounts.models import User
from django.utils import timezone
from datetime import timedelta

def find_hanuman_puja_cart():
    """Find the current Hanuman Puja cart that needs a booking"""
    print("=== FINDING CURRENT HANUMAN PUJA CART ===\n")
    
    # Get user
    user = User.objects.filter(email='asliprinceraj@gmail.com').first()
    if not user:
        print("❌ User not found")
        return
    
    print(f"👤 User: {user.email}")
    
    # Find active cart with Hanuman Puja
    active_carts = Cart.objects.filter(
        user=user,
        status='ACTIVE'
    ).order_by('-created_at')
    
    print(f"📦 Active carts found: {active_carts.count()}")
    
    for cart in active_carts:
        print(f"\n🛒 Cart: {cart.cart_id}")
        print(f"   Service: {cart.puja_service.title if cart.puja_service else 'N/A'}")
        print(f"   Package: {str(cart.package) if cart.package else 'N/A'}")
        print(f"   Status: {cart.status}")
        print(f"   Created: {cart.created_at}")
        print(f"   Selected Date: {cart.selected_date}")
        print(f"   Selected Time: {cart.selected_time}")
        
        # Check if this cart has a payment
        payment = PaymentOrder.objects.filter(cart_id=cart.cart_id).first()
        if payment:
            print(f"   💳 Payment: {payment.merchant_order_id} - {payment.status}")
        else:
            print(f"   ❌ No payment found for this cart")
        
        # Check if this cart has a booking
        booking = Booking.objects.filter(cart=cart).first()
        if booking:
            print(f"   📋 Booking: {booking.book_id} - {booking.status}")
        else:
            print(f"   ❌ No booking found for this cart")
            print(f"   🔧 This cart needs a booking!")
            
        print(f"   {'='*50}")

def create_payment_and_booking_for_active_cart():
    """Create payment and booking for the active Hanuman Puja cart"""
    print(f"\n=== CREATING PAYMENT AND BOOKING FOR ACTIVE CART ===\n")
    
    # Get user
    user = User.objects.filter(email='asliprinceraj@gmail.com').first()
    
    # Find the most recent active cart (should be Hanuman Puja)
    active_cart = Cart.objects.filter(
        user=user,
        status='ACTIVE'
    ).order_by('-created_at').first()
    
    if not active_cart:
        print("❌ No active cart found")
        return
    
    print(f"🛒 Found active cart: {active_cart.cart_id}")
    print(f"   Service: {active_cart.puja_service.title}")
    print(f"   Package: {str(active_cart.package)}")
    print(f"   Amount: ₹{active_cart.total_price}")
    
    # Check if payment already exists
    existing_payment = PaymentOrder.objects.filter(cart_id=active_cart.cart_id).first()
    if existing_payment:
        print(f"✅ Payment already exists: {existing_payment.merchant_order_id}")
        payment = existing_payment
    else:
        # Create new payment for this cart
        from payments.services import PaymentService
        payment_service = PaymentService()
        
        payment_data = {
            'cart_id': active_cart.cart_id,
            'amount': active_cart.total_price,
            'currency': 'INR',
            'description': f"Payment for {active_cart.puja_service.title}"
        }
        
        try:
            payment = payment_service.create_payment(user, payment_data)
            print(f"✅ Payment created: {payment.merchant_order_id}")
        except Exception as e:
            print(f"❌ Payment creation failed: {e}")
            return
    
    # Mark payment as successful
    if payment.status != 'SUCCESS':
        payment.mark_success(
            phonepe_transaction_id=f'TXN_HANUMAN_{payment.merchant_order_id[-8:]}',
            phonepe_response={
                'success': True,
                'code': 'PAYMENT_SUCCESS',
                'message': 'Your payment is successful.',
                'data': {
                    'merchantTransactionId': payment.merchant_order_id,
                    'transactionId': f'TXN_HANUMAN_{payment.merchant_order_id[-8:]}',
                    'amount': int(payment.amount * 100),
                    'state': 'COMPLETED',
                    'responseCode': 'SUCCESS'
                }
            }
        )
        print(f"✅ Payment marked as SUCCESS")
    
    # Create booking for this cart
    existing_booking = Booking.objects.filter(cart=active_cart).first()
    if existing_booking:
        print(f"✅ Booking already exists: {existing_booking.book_id}")
        booking = existing_booking
    else:
        from payments.services import WebhookService
        webhook_service = WebhookService()
        
        booking = webhook_service._create_booking_from_cart(payment)
        if booking:
            print(f"✅ Booking created: {booking.book_id}")
        else:
            print(f"❌ Booking creation failed")
            return
    
    # Send email notification
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = f"🙏 Booking Confirmed - {booking.book_id}"
        message = f"""
        Dear {user.email},
        
        Your Hanuman Puja booking has been confirmed!
        
        Booking Details:
        - Booking ID: {booking.book_id}
        - Service: {active_cart.puja_service.title}
        - Package: {str(active_cart.package)}
        - Date: {active_cart.selected_date}
        - Time: {active_cart.selected_time}
        - Amount: ₹{active_cart.total_price}
        - Status: {booking.status}
        
        Thank you for choosing OkPuja!
        
        Best regards,
        Team OkPuja
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False
        )
        
        print(f"✅ Email sent successfully to {user.email}")
        
    except Exception as e:
        print(f"❌ Email failed: {e}")
    
    # Show the correct redirect URL
    expected_url = f"http://localhost:3000/confirmbooking?book_id={booking.book_id}&order_id={payment.merchant_order_id}&redirect_source=phonepe"
    print(f"\n🌐 Correct redirect URL for frontend:")
    print(f"   {expected_url}")
    
    return booking

if __name__ == "__main__":
    find_hanuman_puja_cart()
    create_payment_and_booking_for_active_cart()
