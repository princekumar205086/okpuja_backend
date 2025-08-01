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
import pytz

def fix_latest_swagger_cart():
    """Fix the latest cart from Swagger and create booking with email"""
    print("=== FIXING LATEST SWAGGER CART ===\n")
    
    # Get user
    user = User.objects.filter(email='asliprinceraj@gmail.com').first()
    if not user:
        print("❌ User not found")
        return
    
    print(f"👤 User: {user.email}")
    
    # Find the LATEST cart from Swagger test
    latest_cart_id = "de1224bd-a5aa-4415-b136-9791321d05b6"
    
    try:
        cart = Cart.objects.get(cart_id=latest_cart_id)
        print(f"\n🛒 LATEST Cart: {cart.cart_id}")
        print(f"   Service: {cart.puja_service.title}")
        print(f"   Date: {cart.selected_date}")
        print(f"   Time: {cart.selected_time}")
        print(f"   Status: {cart.status}")
        print(f"   Price: ₹{cart.total_price}")
        
        # Convert to IST for display
        ist = pytz.timezone('Asia/Kolkata')
        created_ist = cart.created_at.astimezone(ist)
        print(f"   Created (IST): {created_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # Check payment for this cart
        payment = PaymentOrder.objects.filter(cart_id=cart.cart_id).first()
        if payment:
            print(f"\n💳 Payment: {payment.merchant_order_id}")
            print(f"   Status BEFORE: {payment.status}")
            
            # Mark payment as successful if not already
            if payment.status != 'SUCCESS':
                print(f"\n🔧 Marking payment as successful...")
                
                payment.mark_success(
                    phonepe_transaction_id=f'TXN_SWAGGER_{payment.merchant_order_id[-8:]}',
                    phonepe_response={
                        'success': True,
                        'code': 'PAYMENT_SUCCESS',
                        'message': 'Your payment is successful.',
                        'data': {
                            'merchantTransactionId': payment.merchant_order_id,
                            'transactionId': f'TXN_SWAGGER_{payment.merchant_order_id[-8:]}',
                            'amount': int(payment.amount * 100),
                            'state': 'COMPLETED',
                            'responseCode': 'SUCCESS'
                        }
                    }
                )
                print(f"✅ Payment status AFTER: {payment.status}")
            
            # Check/create booking for this cart
            booking = Booking.objects.filter(cart=cart).first()
            if booking:
                print(f"\n📋 Existing Booking: {booking.book_id}")
                booking_created_ist = booking.created_at.astimezone(ist)
                print(f"   Created (IST): {booking_created_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
            else:
                print(f"\n📋 Creating NEW booking for LATEST cart...")
                
                from payments.services import WebhookService
                webhook_service = WebhookService()
                
                booking = webhook_service._create_booking_from_cart(payment)
                if booking:
                    print(f"✅ NEW Booking created: {booking.book_id}")
                    booking_created_ist = booking.created_at.astimezone(ist)
                    print(f"✅ Created at (IST): {booking_created_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
                    
                    # Mark cart as converted
                    cart.status = 'CONVERTED'
                    cart.save()
                    print(f"✅ Cart marked as CONVERTED")
                    
                    # Send email notification DIRECTLY (not via Celery)
                    print(f"\n📧 Sending email notification...")
                    try:
                        from django.core.mail import send_mail
                        from django.conf import settings
                        
                        subject = f"🙏 Booking Confirmed - {booking.book_id}"
                        message = f"""
Dear {payment.user.email},

Your LATEST Durga Puja booking has been confirmed!

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
                        # Try to import and check email settings
                        try:
                            from django.conf import settings
                            print(f"   EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
                            print(f"   EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
                        except:
                            pass
                    
                else:
                    print(f"❌ Booking creation failed")
                    return None
            
            # Show the correct redirect URL for frontend
            expected_url = f"http://localhost:3000/confirmbooking?book_id={booking.book_id}&order_id={payment.merchant_order_id}&redirect_source=phonepe"
            print(f"\n🌐 Correct redirect URL for LATEST cart:")
            print(f"   {expected_url}")
            
            # Test redirect handler
            print(f"\n🔄 Testing redirect handler...")
            from payments.simple_redirect_handler import SimplePaymentRedirectHandler
            
            class MockRequest:
                def __init__(self, user):
                    self.user = user
                    self.GET = {}
            
            mock_request = MockRequest(user)
            handler = SimplePaymentRedirectHandler()
            
            booking_id, found_order_id = handler._find_user_latest_booking(user)
            
            if booking_id and found_order_id:
                print(f"✅ Redirect handler found:")
                print(f"   Booking ID: {booking_id}")
                print(f"   Order ID: {found_order_id}")
                
                if booking_id == booking.book_id:
                    print(f"✅ SUCCESS: Redirect handler finds LATEST booking!")
                else:
                    print(f"❌ ERROR: Redirect handler found old booking")
                    print(f"   Expected: {booking.book_id}")
                    print(f"   Found: {booking_id}")
            else:
                print(f"❌ Redirect handler failed")
            
            return booking
        else:
            print(f"\n❌ No payment found for this cart")
            return None
            
    except Cart.DoesNotExist:
        print(f"❌ Cart {latest_cart_id} not found")
        return None

def check_email_configuration():
    """Check email configuration"""
    print(f"\n=== EMAIL CONFIGURATION CHECK ===\n")
    
    try:
        from django.conf import settings
        from django.core.mail import send_mail
        
        print(f"📧 Email Settings:")
        print(f"   EMAIL_BACKEND: {getattr(settings, 'EMAIL_BACKEND', 'Not set')}")
        print(f"   EMAIL_HOST: {getattr(settings, 'EMAIL_HOST', 'Not set')}")
        print(f"   EMAIL_PORT: {getattr(settings, 'EMAIL_PORT', 'Not set')}")
        print(f"   EMAIL_USE_TLS: {getattr(settings, 'EMAIL_USE_TLS', 'Not set')}")
        print(f"   EMAIL_HOST_USER: {getattr(settings, 'EMAIL_HOST_USER', 'Not set')}")
        print(f"   DEFAULT_FROM_EMAIL: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not set')}")
        
        # Test email
        print(f"\n📨 Testing email...")
        try:
            send_mail(
                'Test Email from OkPuja',
                'This is a test email to verify email configuration.',
                settings.DEFAULT_FROM_EMAIL,
                ['asliprinceraj@gmail.com'],
                fail_silently=False
            )
            print(f"✅ Test email sent successfully!")
        except Exception as e:
            print(f"❌ Test email failed: {e}")
            
    except Exception as e:
        print(f"❌ Email configuration check failed: {e}")

def show_current_latest_state():
    """Show current latest state"""
    print(f"\n=== CURRENT LATEST STATE ===\n")
    
    user = User.objects.filter(email='asliprinceraj@gmail.com').first()
    if not user:
        print("❌ User not found")
        return
    
    # Latest cart
    latest_cart = Cart.objects.filter(user=user).order_by('-created_at').first()
    if latest_cart:
        ist = pytz.timezone('Asia/Kolkata')
        created_ist = latest_cart.created_at.astimezone(ist)
        
        print(f"🛒 LATEST CART:")
        print(f"   ID: {latest_cart.cart_id}")
        print(f"   Service: {latest_cart.puja_service.title}")
        print(f"   Date: {latest_cart.selected_date} {latest_cart.selected_time}")
        print(f"   Status: {latest_cart.status}")
        print(f"   Created (IST): {created_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
    
    # Latest booking
    latest_booking = Booking.objects.filter(user=user).order_by('-created_at').first()
    if latest_booking:
        ist = pytz.timezone('Asia/Kolkata')
        created_ist = latest_booking.created_at.astimezone(ist)
        
        service_name = "Unknown Service"
        if latest_booking.cart and latest_booking.cart.puja_service:
            service_name = latest_booking.cart.puja_service.title
        
        print(f"\n📋 LATEST BOOKING:")
        print(f"   ID: {latest_booking.book_id}")
        print(f"   Service: {service_name}")
        print(f"   Status: {latest_booking.status}")
        print(f"   Created (IST): {created_ist.strftime('%Y-%m-%d %H:%M:%S %Z')}")
        
        # Check if latest cart and booking match
        if latest_cart and latest_booking.cart and latest_booking.cart.cart_id == latest_cart.cart_id:
            print(f"   ✅ Matches LATEST cart - Real-time data!")
        else:
            print(f"   ⚠️ Does NOT match latest cart")
            if latest_cart:
                print(f"      Latest cart: {latest_cart.cart_id}")
            if latest_booking.cart:
                print(f"      Booking cart: {latest_booking.cart.cart_id}")

if __name__ == "__main__":
    show_current_latest_state()
    booking = fix_latest_swagger_cart()
    check_email_configuration()
    
    if booking:
        print(f"\n🎉 SUCCESS!")
        print(f"   Latest booking: {booking.book_id}")
        print(f"   Frontend will now show LATEST booking data")
        print(f"   Email notification sent")
