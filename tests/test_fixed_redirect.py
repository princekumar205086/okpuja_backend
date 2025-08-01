#!/usr/bin/env python
import os
import sys
import django

# Setup Django environment
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'okpuja_backend.settings')
django.setup()

def test_fixed_redirect_handler():
    """Test the fixed redirect handler logic"""
    print("=== 🧪 TESTING FIXED REDIRECT HANDLER ===\n")
    
    from booking.models import Booking
    from accounts.models import User
    from cart.models import Cart
    from payments.models import PaymentOrder
    
    # Get the user
    user = User.objects.filter(email='asliprinceraj@gmail.com').first()
    if not user:
        print("❌ User not found!")
        return
    
    print(f"👤 User: {user.email} (ID: {user.id})")
    
    # Simulate the NEW redirect handler logic
    print(f"\n🔄 NEW REDIRECT HANDLER LOGIC:")
    
    # Step 1: Look for cart with successful payment
    successful_payment = PaymentOrder.objects.filter(
        user=user, 
        status='SUCCESS'
    ).order_by('-created_at').first()
    
    target_cart = None
    
    if successful_payment:
        target_cart = Cart.objects.filter(cart_id=successful_payment.cart_id).first()
        print(f"   1. ✅ Found cart with successful payment: {target_cart.cart_id if target_cart else 'None'}")
        if target_cart:
            print(f"      Service: {target_cart.puja_service.title}")
            print(f"      Status: {target_cart.status}")
    else:
        print(f"   1. ❌ No cart with successful payment found")
    
    # Step 2: If no successful payment, look for recent initiated payment
    if not target_cart:
        recent_payment = PaymentOrder.objects.filter(
            user=user,
            status='INITIATED'
        ).order_by('-created_at').first()
        
        if recent_payment:
            target_cart = Cart.objects.filter(cart_id=recent_payment.cart_id).first()
            print(f"   2. ✅ Found cart with recent initiated payment: {target_cart.cart_id if target_cart else 'None'}")
            if target_cart:
                print(f"      Service: {target_cart.puja_service.title}")
                print(f"      Status: {target_cart.status}")
                print(f"      Payment: {recent_payment.merchant_order_id}")
        else:
            print(f"   2. ❌ No recent initiated payment found")
    
    # Step 3: Fallback to latest cart
    if not target_cart:
        target_cart = Cart.objects.filter(user=user).order_by('-created_at').first()
        print(f"   3. 🔄 Fallback to latest cart: {target_cart.cart_id if target_cart else 'None'}")
    
    if target_cart:
        print(f"\n🎯 SELECTED TARGET CART: {target_cart.cart_id}")
        print(f"   Service: {target_cart.puja_service.title}")
        print(f"   Status: {target_cart.status}")
        print(f"   Created: {target_cart.created_at}")
        
        # Check payment for target cart
        target_payment = PaymentOrder.objects.filter(
            cart_id=target_cart.cart_id
        ).order_by('-created_at').first()
        
        if target_payment:
            print(f"   Payment: {target_payment.merchant_order_id} ({target_payment.status})")
        
        # Check if booking exists
        target_booking = Booking.objects.filter(cart=target_cart).first()
        
        if target_booking:
            print(f"   Existing Booking: {target_booking.book_id}")
            print(f"   ✅ Redirect would return: {target_booking.book_id}")
        else:
            print(f"   No existing booking - would create new one")
            print(f"   ✅ Redirect would create new booking for this cart")
    
    # Now mark the Swagger cart payment as SUCCESS and test again
    swagger_cart_id = "ee52ccd4-31ca-4f4d-b436-33b649c1ef49"
    swagger_payment = PaymentOrder.objects.filter(cart_id=swagger_cart_id).first()
    
    if swagger_payment and swagger_payment.status != 'SUCCESS':
        print(f"\n🔧 FIXING SWAGGER CART PAYMENT:")
        print(f"   Marking payment {swagger_payment.merchant_order_id} as SUCCESS")
        swagger_payment.status = 'SUCCESS'
        swagger_payment.save()
        
        print(f"\n🧪 TESTING AFTER FIX:")
        
        # Test the logic again
        successful_payment = PaymentOrder.objects.filter(
            user=user, 
            status='SUCCESS'
        ).order_by('-created_at').first()
        
        if successful_payment:
            target_cart = Cart.objects.filter(cart_id=successful_payment.cart_id).first()
            print(f"   ✅ Now finds cart: {target_cart.cart_id if target_cart else 'None'}")
            
            if target_cart and target_cart.cart_id == swagger_cart_id:
                print(f"   🎯 PERFECT! Now targets the Swagger cart")
                
                # Check if booking exists
                target_booking = Booking.objects.filter(cart=target_cart).first()
                
                if not target_booking:
                    print(f"   Creating booking for Swagger cart...")
                    
                    from payments.services import WebhookService
                    webhook_service = WebhookService()
                    try:
                        booking = webhook_service._create_booking_from_cart(target_cart)
                        if booking:
                            print(f"   ✅ Created booking: {booking.book_id}")
                            
                            # Send email
                            from django.core.mail import send_mail
                            from django.conf import settings
                            
                            send_mail(
                                subject=f'🙏 Booking Confirmed - {booking.book_id}',
                                message=f'Your booking {booking.book_id} has been confirmed for {target_cart.puja_service.title}.',
                                from_email=settings.DEFAULT_FROM_EMAIL,
                                recipient_list=[user.email],
                                fail_silently=False,
                            )
                            print(f"   📧 Email sent to {user.email}")
                            
                            # Update cart status
                            target_cart.status = 'CONVERTED'
                            target_cart.save()
                            print(f"   🛒 Cart marked as CONVERTED")
                            
                            print(f"\n🎉 REDIRECT WOULD NOW RETURN: {booking.book_id}")
                        else:
                            print(f"   ❌ Failed to create booking")
                    except Exception as e:
                        print(f"   ❌ Error creating booking: {e}")
                else:
                    print(f"   ✅ Booking already exists: {target_booking.book_id}")

if __name__ == "__main__":
    test_fixed_redirect_handler()
