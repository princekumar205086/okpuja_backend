#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

def create_booking_for_swagger_cart():
    """Create booking for the Swagger cart that was paid"""
    print("=== 🚀 CREATING BOOKING FOR SWAGGER CART ===\n")
    
    from booking.models import Booking
    from accounts.models import User
    from cart.models import Cart
    from payments.models import PaymentOrder
    from payments.services import WebhookService
    
    # Get the user
    user = User.objects.filter(email='asliprinceraj@gmail.com').first()
    
    # Get the Swagger cart
    swagger_cart_id = "ee52ccd4-31ca-4f4d-b436-33b649c1ef49"
    swagger_cart = Cart.objects.filter(cart_id=swagger_cart_id).first()
    
    if not swagger_cart:
        print(f"❌ Swagger cart {swagger_cart_id} not found!")
        return
    
    print(f"🛒 Swagger Cart: {swagger_cart.cart_id}")
    print(f"   Service: {swagger_cart.puja_service.title}")
    print(f"   Status: {swagger_cart.status}")
    print(f"   Date: {swagger_cart.selected_date}")
    print(f"   Time: {swagger_cart.selected_time}")
    
    # Check payment
    payment = PaymentOrder.objects.filter(cart_id=swagger_cart_id).first()
    if payment:
        print(f"💳 Payment: {payment.merchant_order_id} ({payment.status})")
    else:
        print(f"❌ No payment found for cart!")
        return
    
    # Check if booking already exists
    existing_booking = Booking.objects.filter(cart=swagger_cart).first()
    if existing_booking:
        print(f"📋 Booking already exists: {existing_booking.book_id}")
        return
    
    # Create booking
    print(f"\n🔧 Creating booking for Swagger cart...")
    
    try:
        webhook_service = WebhookService()
        booking = webhook_service._create_booking_from_cart(swagger_cart)
        
        if booking:
            print(f"✅ Created booking: {booking.book_id}")
            print(f"   Status: {booking.status}")
            print(f"   User: {booking.user.email}")
            print(f"   Cart: {booking.cart.cart_id}")
            
            # Send email
            from django.core.mail import send_mail
            from django.conf import settings
            
            try:
                send_mail(
                    subject=f'🙏 Booking Confirmed - {booking.book_id}',
                    message=f'Your booking {booking.book_id} has been confirmed for {swagger_cart.puja_service.title} on {swagger_cart.selected_date} at {swagger_cart.selected_time}.',
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                print(f"📧 Email sent to {user.email}")
            except Exception as e:
                print(f"⚠️  Email sending failed: {e}")
            
            # Update cart status
            swagger_cart.status = 'CONVERTED'
            swagger_cart.save()
            print(f"🛒 Cart marked as CONVERTED")
            
            # Test redirect URL
            redirect_url = f"http://localhost:3000/confirmbooking?book_id={booking.book_id}&order_id={payment.merchant_order_id}&redirect_source=phonepe"
            print(f"\n🌐 Redirect URL:")
            print(f"   {redirect_url}")
            
            print(f"\n🎉 SUCCESS! Redirect handler will now return the NEW booking:")
            print(f"   OLD: BK-9DCB7B55 (from old cart)")
            print(f"   NEW: {booking.book_id} (from Swagger cart)")
            
        else:
            print(f"❌ Failed to create booking")
            
    except Exception as e:
        print(f"❌ Error creating booking: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_booking_for_swagger_cart()
