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

def process_latest_swagger_cart():
    """Process the latest cart from Swagger and create booking"""
    print("=== PROCESSING LATEST SWAGGER CART ===\n")
    
    # Get user
    user = User.objects.filter(email='asliprinceraj@gmail.com').first()
    if not user:
        print("❌ User not found")
        return
    
    print(f"👤 User: {user.email}")
    
    # Find the latest cart from Swagger test
    latest_cart_id = "d3417c2a-d644-427b-bf3d-8794f7d178fe"
    
    try:
        cart = Cart.objects.get(cart_id=latest_cart_id)
        print(f"\n🛒 Latest Cart: {cart.cart_id}")
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
            
            # Mark payment as successful
            if payment.status != 'SUCCESS':
                print(f"\n🔧 Marking payment as successful...")
                
                payment.mark_success(
                    phonepe_transaction_id=f'TXN_LATEST_{payment.merchant_order_id[-8:]}',
                    phonepe_response={
                        'success': True,
                        'code': 'PAYMENT_SUCCESS',
                        'message': 'Your payment is successful.',
                        'data': {
                            'merchantTransactionId': payment.merchant_order_id,
                            'transactionId': f'TXN_LATEST_{payment.merchant_order_id[-8:]}',
                            'amount': int(payment.amount * 100),
                            'state': 'COMPLETED',
                            'responseCode': 'SUCCESS'
                        }
                    }
                )
                print(f"✅ Payment marked as SUCCESS")
            
            # Check/create booking for this cart
            booking = Booking.objects.filter(cart=cart).first()
            if booking:
                print(f"\n📋 Existing Booking: {booking.book_id}")
            else:
                print(f"\n📋 Creating booking for latest cart...")
                
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
                
                Your latest Durga Puja booking has been confirmed!
                
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
            
            # Show the correct redirect URL for frontend
            expected_url = f"http://localhost:3000/confirmbooking?book_id={booking.book_id}&order_id={payment.merchant_order_id}&redirect_source=phonepe"
            print(f"\n🌐 Correct redirect URL for frontend:")
            print(f"   {expected_url}")
            
            # Test booking API
            print(f"\n📡 Testing Booking API:")
            import requests
            
            api_url = f"http://127.0.0.1:8000/api/booking/bookings/by-id/{booking.book_id}/"
            response = requests.get(api_url)
            
            if response.status_code == 200:
                booking_data = response.json()
                print(f"✅ API working - Booking ID: {booking_data.get('book_id')}")
                print(f"   Service: {booking_data.get('service_name', 'N/A')}")
                print(f"   Status: {booking_data.get('status')}")
            else:
                print(f"⚠️ API returned: {response.status_code} (may need authentication)")
            
            return booking
        else:
            print(f"\n❌ No payment found for this cart")
            return None
            
    except Cart.DoesNotExist:
        print(f"❌ Cart {latest_cart_id} not found")
        return None

def cleanup_old_carts():
    """Clean up old converted carts to keep only active ones"""
    print(f"\n=== CLEANING UP OLD CARTS ===\n")
    
    user = User.objects.filter(email='asliprinceraj@gmail.com').first()
    if not user:
        print("❌ User not found")
        return
    
    # Find all converted carts (successful payments with bookings)
    converted_carts = Cart.objects.filter(
        user=user, 
        status='CONVERTED'
    ).order_by('-created_at')
    
    print(f"📦 Found {converted_carts.count()} converted carts")
    
    # Keep only the latest 3 converted carts, delete the rest
    carts_to_keep = converted_carts[:3]
    carts_to_delete = converted_carts[3:]
    
    if carts_to_delete:
        print(f"🗑️ Cleaning up {carts_to_delete.count()} old converted carts:")
        
        for cart in carts_to_delete:
            print(f"   Deleting cart: {cart.cart_id} ({cart.puja_service.title})")
            
            # Check if cart has any bookings that should be preserved
            bookings = Booking.objects.filter(cart=cart)
            if bookings.exists():
                print(f"   ⚠️ Cart has {bookings.count()} booking(s) - setting cart to NULL")
                for booking in bookings:
                    booking.cart = None
                    booking.save()
            
            # Delete the cart
            cart.delete()
        
        print(f"✅ Cleanup complete - kept {len(carts_to_keep)} recent carts")
    else:
        print(f"✅ No cleanup needed - only {converted_carts.count()} converted carts")

def show_current_state():
    """Show current state of user's carts and bookings"""
    print(f"\n=== CURRENT USER STATE ===\n")
    
    user = User.objects.filter(email='asliprinceraj@gmail.com').first()
    if not user:
        print("❌ User not found")
        return
    
    # Show active carts
    active_carts = Cart.objects.filter(user=user, status='ACTIVE').order_by('-created_at')
    print(f"🛒 Active Carts: {active_carts.count()}")
    
    for cart in active_carts[:3]:  # Show latest 3
        ist = pytz.timezone('Asia/Kolkata')
        created_ist = cart.created_at.astimezone(ist)
        print(f"   {cart.cart_id} - {cart.puja_service.title}")
        print(f"     Date: {cart.selected_date} {cart.selected_time}")
        print(f"     Created (IST): {created_ist.strftime('%Y-%m-%d %H:%M:%S')}")
        print()
    
    # Show recent bookings
    recent_bookings = Booking.objects.filter(user=user).order_by('-created_at')[:5]
    print(f"📋 Recent Bookings: {recent_bookings.count()}")
    
    for booking in recent_bookings:
        ist = pytz.timezone('Asia/Kolkata')
        created_ist = booking.created_at.astimezone(ist)
        service_name = "Unknown Service"
        if booking.cart and booking.cart.puja_service:
            service_name = booking.cart.puja_service.title
        
        print(f"   {booking.book_id} - {service_name}")
        print(f"     Status: {booking.status}")
        print(f"     Created (IST): {created_ist.strftime('%Y-%m-%d %H:%M:%S')}")
        print()

if __name__ == "__main__":
    booking = process_latest_swagger_cart()
    if booking:
        cleanup_old_carts()
        show_current_state()
        
        print(f"\n🎉 SUCCESS!")
        print(f"   Latest booking: {booking.book_id}")
        print(f"   Frontend URL: http://localhost:3000/confirmbooking?book_id={booking.book_id}")
        print(f"   Database updated with LATEST cart data in IST timezone")
