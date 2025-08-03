"""
Simulate PhonePe Payment Success and Webhook Processing
This will update the payment status and create the booking
"""
from payments.models import PaymentOrder
from payments.services import WebhookService
from cart.models import Cart
from booking.models import Booking

print('=== SIMULATING PHONEPE PAYMENT SUCCESS ===')

# Find the latest payment
latest_payment = PaymentOrder.objects.filter(
    merchant_order_id='CART_0e36bb21-03ee-4ead-8e2d-6c08df506bf0_6E33C403'
).first()

if latest_payment:
    print(f'Found payment: {latest_payment.merchant_order_id}')
    print(f'Current status: {latest_payment.status}')
    print(f'Cart ID: {latest_payment.cart_id}')
    
    # Update payment status to SUCCESS (simulating PhonePe success)
    latest_payment.status = 'SUCCESS'
    latest_payment.save()
    print(f'Updated payment status to: {latest_payment.status}')
    
    # Check if booking already exists
    cart = Cart.objects.get(cart_id=latest_payment.cart_id)
    existing_booking = Booking.objects.filter(cart=cart).first()
    
    if existing_booking:
        print(f'Booking already exists: {existing_booking.book_id}')
    else:
        print('No booking found - creating new booking...')
        
        # Create booking using webhook service
        webhook_service = WebhookService()
        booking = webhook_service._create_booking_from_cart(latest_payment)
        
        if booking:
            print(f'SUCCESS: Created booking {booking.book_id}')
            print(f'Booking status: {booking.status}')
            print(f'Total amount: Rs.{booking.total_amount}')
            
            # Update cart status
            cart.status = 'CONVERTED'
            cart.save()
            print(f'Updated cart status to: {cart.status}')
            
            # Send email notification
            try:
                from core.tasks import send_booking_confirmation
                send_booking_confirmation.delay(booking.id)
                print('Email notification queued')
            except Exception as e:
                print(f'Email notification failed: {e}')
        else:
            print('Failed to create booking')
    
    print(f'\n=== TESTING REDIRECT NOW ===')
    print(f'Expected redirect URL should now use cart_id: {latest_payment.cart_id}')
    print(f'Booking should exist and be found')
    
else:
    print('Payment not found!')
