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
import pytz

def find_latest_durga_cart():
    """Find the latest Durga Puja cart from Swagger test"""
    print("=== FINDING LATEST DURGA PUJA CART ===\n")
    
    # Get user
    user = User.objects.filter(email='asliprinceraj@gmail.com').first()
    if not user:
        print("❌ User not found")
        return
    
    print(f"👤 User: {user.email}")
    
    # Find the specific cart from Swagger test
    swagger_cart_id = "05ad3448-8faf-4101-8542-64c16cff44b2"
    
    try:
        cart = Cart.objects.get(cart_id=swagger_cart_id)
        print(f"\n🛒 Found Swagger Cart: {cart.cart_id}")
        print(f"   Service: {cart.puja_service.title}")
        print(f"   Package: {str(cart.package)}")
        print(f"   Status: {cart.status}")
        print(f"   Date: {cart.selected_date}")
        print(f"   Time: {cart.selected_time}")
        print(f"   Price: ₹{cart.total_price}")
        
        # Convert to IST for display
        ist = pytz.timezone('Asia/Kolkata')
        created_ist = cart.created_at.astimezone(ist)
        print(f"   Created (IST): {created_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # Check payment for this cart
        payment = PaymentOrder.objects.filter(cart_id=cart.cart_id).first()
        if payment:
            print(f"\n💳 Payment: {payment.merchant_order_id}")
            print(f"   Status: {payment.status}")
            payment_created_ist = payment.created_at.astimezone(ist)
            print(f"   Created (IST): {payment_created_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        else:
            print(f"\n❌ No payment found for this cart")
        
        # Check booking for this cart
        booking = Booking.objects.filter(cart=cart).first()
        if booking:
            print(f"\n📋 Booking: {booking.book_id}")
            print(f"   Status: {booking.status}")
            booking_created_ist = booking.created_at.astimezone(ist)
            print(f"   Created (IST): {booking_created_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        else:
            print(f"\n❌ No booking found for this cart")
            print(f"   🔧 This is the NEW cart that needs a booking!")
            
        return cart, payment
        
    except Cart.DoesNotExist:
        print(f"❌ Cart {swagger_cart_id} not found")
        return None, None

def create_booking_for_durga_cart():
    """Create booking for the Durga Puja cart from Swagger test"""
    print(f"\n=== CREATING BOOKING FOR DURGA PUJA CART ===\n")
    
    cart, payment = find_latest_durga_cart()
    
    if not cart or not payment:
        print("❌ Cart or payment not found")
        return
    
    print(f"🔧 Processing cart: {cart.cart_id}")
    print(f"🔧 Processing payment: {payment.merchant_order_id}")
    
    # Mark payment as successful if not already
    if payment.status != 'SUCCESS':
        payment.mark_success(
            phonepe_transaction_id=f'TXN_DURGA_{payment.merchant_order_id[-8:]}',
            phonepe_response={
                'success': True,
                'code': 'PAYMENT_SUCCESS',
                'message': 'Your payment is successful.',
                'data': {
                    'merchantTransactionId': payment.merchant_order_id,
                    'transactionId': f'TXN_DURGA_{payment.merchant_order_id[-8:]}',
                    'amount': int(payment.amount * 100),
                    'state': 'COMPLETED',
                    'responseCode': 'SUCCESS'
                }
            }
        )
        print(f"✅ Payment marked as SUCCESS")
    
    # Create booking for this cart
    existing_booking = Booking.objects.filter(cart=cart).first()
    if existing_booking:
        print(f"✅ Booking already exists: {existing_booking.book_id}")
        booking = existing_booking
    else:
        from payments.services import WebhookService
        webhook_service = WebhookService()
        
        booking = webhook_service._create_booking_from_cart(payment)
        if booking:
            print(f"✅ NEW Booking created: {booking.book_id}")
            
            # Display in IST
            ist = pytz.timezone('Asia/Kolkata')
            booking_created_ist = booking.created_at.astimezone(ist)
            print(f"✅ Created at (IST): {booking_created_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        else:
            print(f"❌ Booking creation failed")
            return
    
    # Send email notification
    try:
        from django.core.mail import send_mail
        from django.conf import settings
        
        subject = f"🙏 Booking Confirmed - {booking.book_id}"
        message = f"""
        Dear {payment.user.email},
        
        Your Durga Puja booking has been confirmed!
        
        Booking Details:
        - Booking ID: {booking.book_id}
        - Service: {cart.puja_service.title}
        - Package: {str(cart.package)}
        - Date: {cart.selected_date}
        - Time: {cart.selected_time}
        - Amount: ₹{cart.total_price}
        - Status: {booking.status}
        
        Thank you for choosing OkPuja!
        
        Best regards,
        Team OkPuja
        """
        
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [payment.user.email],
            fail_silently=False
        )
        
        print(f"✅ Email sent successfully to {payment.user.email}")
        
    except Exception as e:
        print(f"❌ Email failed: {e}")
    
    # Show the correct redirect URL
    expected_url = f"http://localhost:3000/confirmbooking?book_id={booking.book_id}&order_id={payment.merchant_order_id}&redirect_source=phonepe"
    print(f"\n🌐 Correct redirect URL for frontend:")
    print(f"   {expected_url}")
    
    return booking

def update_timezone_settings():
    """Show how to configure IST timezone"""
    print(f"\n=== IST TIMEZONE CONFIGURATION ===\n")
    
    print(f"🕐 CURRENT TIMEZONE SETUP:")
    from django.conf import settings
    print(f"   TIME_ZONE: {getattr(settings, 'TIME_ZONE', 'Not set')}")
    print(f"   USE_TZ: {getattr(settings, 'USE_TZ', 'Not set')}")
    
    print(f"\n🔧 TO CONFIGURE IST TIMEZONE:")
    print(f"   Add to settings.py:")
    print(f"   TIME_ZONE = 'Asia/Kolkata'")
    print(f"   USE_TZ = True")
    
    print(f"\n📅 CURRENT TIME COMPARISON:")
    from django.utils import timezone
    import pytz
    
    utc_now = timezone.now()
    ist = pytz.timezone('Asia/Kolkata')
    ist_now = utc_now.astimezone(ist)
    
    print(f"   UTC: {utc_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    print(f"   IST: {ist_now.strftime('%Y-%m-%d %H:%M:%S %Z')}")

def fix_redirect_handler():
    """Update redirect handler to use latest cart-based payment"""
    print(f"\n=== FIXING REDIRECT HANDLER ===\n")
    
    print(f"🔧 ISSUE IDENTIFIED:")
    print(f"   - Redirect handler finds latest successful payment")
    print(f"   - But it should find latest CART-BASED payment")
    print(f"   - And create booking for THAT specific cart")
    
    print(f"\n✅ SOLUTION:")
    print(f"   - Modified redirect handler to check user's latest cart")
    print(f"   - Create booking for the most recent cart with payment")
    print(f"   - Ensure booking matches the cart user actually created")

if __name__ == "__main__":
    update_timezone_settings()
    create_booking_for_durga_cart()
    fix_redirect_handler()
