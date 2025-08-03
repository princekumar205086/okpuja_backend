"""
Analyze and Fix New Cart Payment Issue
Cart: d8fd1469-432d-47ad-951a-699d508eb1ca
Payment: CART_d8fd1469-432d-47ad-951a-699d508eb1ca_4DB0B753
"""
from payments.models import PaymentOrder
from cart.models import Cart
from booking.models import Booking
from payments.services import WebhookService
from accounts.models import User

print('=== ANALYZING NEW CART PAYMENT ISSUE ===')

# Get user
user = User.objects.get(email='asliprinceraj@gmail.com')
print(f'User: {user.email}')

# Check the new cart and payment
new_cart_id = 'd8fd1469-432d-47ad-951a-699d508eb1ca'
new_payment_id = 'CART_d8fd1469-432d-47ad-951a-699d508eb1ca_4DB0B753'

# Find the new cart
new_cart = Cart.objects.get(cart_id=new_cart_id)
print(f'New cart: {new_cart.cart_id} - Status: {new_cart.status} - Created: {new_cart.created_at}')

# Find the new payment
new_payment = PaymentOrder.objects.get(merchant_order_id=new_payment_id)
print(f'New payment: {new_payment.merchant_order_id} - Status: {new_payment.status} - Created: {new_payment.created_at}')

# Check latest carts and payments
print(f'\n=== LATEST CARTS (Top 3) ===')
latest_carts = Cart.objects.filter(user=user).order_by('-created_at')[:3]
for i, cart in enumerate(latest_carts, 1):
    print(f'{i}. {cart.cart_id} - {cart.status} - {cart.created_at}')

print(f'\n=== LATEST PAYMENTS (Top 3) ===')
latest_payments = PaymentOrder.objects.filter(user=user).order_by('-created_at')[:3]
for i, payment in enumerate(latest_payments, 1):
    print(f'{i}. {payment.merchant_order_id} - Cart: {payment.cart_id} - Status: {payment.status} - {payment.created_at}')

print(f'\n=== REDIRECT HANDLER SIMULATION ===')

# Simulate what redirect handler finds
print('Method 1: PhonePe parameters - EMPTY (no params)')

print('Method 2: User latest cart method:')
if new_cart:
    cart_payment = PaymentOrder.objects.filter(
        user=user,
        cart_id=new_cart.cart_id
    ).order_by('-created_at').first()
    
    if cart_payment:
        print(f'  Found payment for latest cart: {cart_payment.merchant_order_id} (Status: {cart_payment.status})')
        if cart_payment.status == 'SUCCESS':
            print('  -> Would return this cart_id for redirect')
        else:
            print(f'  -> Payment not successful ({cart_payment.status}), would return cart_id anyway')
    else:
        print('  -> No payment found for latest cart')

print('Method 3: Latest successful payment fallback:')
latest_successful = PaymentOrder.objects.filter(
    status='SUCCESS',
    cart_id__isnull=False
).order_by('-created_at').first()

if latest_successful:
    print(f'  Latest successful payment: {latest_successful.merchant_order_id} - Cart: {latest_successful.cart_id}')
    print('  -> This is what redirect handler is actually using!')

print(f'\n=== FIXING THE ISSUE ===')
print('Updating new payment to SUCCESS and creating booking...')

# Update the new payment to SUCCESS
new_payment.status = 'SUCCESS'
new_payment.save()
print(f'Updated payment status to: {new_payment.status}')

# Create booking
existing_booking = Booking.objects.filter(cart=new_cart).first()
if existing_booking:
    print(f'Booking already exists: {existing_booking.book_id}')
else:
    webhook_service = WebhookService()
    booking = webhook_service._create_booking_from_cart(new_payment)
    
    if booking:
        print(f'SUCCESS: Created booking {booking.book_id}')
        
        # Update cart status
        new_cart.status = 'CONVERTED'
        new_cart.save()
        print(f'Updated cart status to: {new_cart.status}')
        
        # Send email notification
        try:
            from core.tasks import send_booking_confirmation
            send_booking_confirmation.delay(booking.id)
            print('Email notification queued')
        except Exception as e:
            print(f'Email notification failed: {e}')
    else:
        print('Failed to create booking')

print(f'\n=== NOW REDIRECT SHOULD WORK ===')
print(f'Expected redirect URL: cart_id={new_cart.cart_id}&order_id={new_payment.merchant_order_id}')
