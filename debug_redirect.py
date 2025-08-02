"""
Debug Cart and Payment Analysis
"""
from payments.models import PaymentOrder
from cart.models import Cart
from accounts.models import User

print('=== LATEST CART AND PAYMENT ANALYSIS ===')

# Get user
user = User.objects.get(email='asliprinceraj@gmail.com')
print(f'User: {user.email} (ID: {user.id})')

# Check latest carts
latest_carts = Cart.objects.filter(user=user).order_by('-created_at')[:3]
print(f'\nLatest 3 carts:')
for i, cart in enumerate(latest_carts, 1):
    print(f'{i}. {cart.cart_id} - {cart.status} - {cart.created_at}')

# Check latest payments
latest_payments = PaymentOrder.objects.filter(user=user).order_by('-created_at')[:3]
print(f'\nLatest 3 payments:')
for i, payment in enumerate(latest_payments, 1):
    print(f'{i}. {payment.merchant_order_id} - Cart: {payment.cart_id} - Status: {payment.status} - {payment.created_at}')

# Check if latest cart has payment
latest_cart = latest_carts[0] if latest_carts else None
if latest_cart:
    cart_payment = PaymentOrder.objects.filter(cart_id=latest_cart.cart_id).first()
    if cart_payment:
        print(f'\nLatest cart payment: {cart_payment.merchant_order_id} - Status: {cart_payment.status}')
    else:
        print(f'\nLatest cart has NO PAYMENT')

# Check what redirect handler would find
print(f'\n=== REDIRECT HANDLER ANALYSIS ===')

# Method 1: PhonePe parameters (empty in this case)
print('Method 1: PhonePe parameters - EMPTY')

# Method 2: User's latest cart
if latest_cart:
    cart_payment = PaymentOrder.objects.filter(
        user=user,
        cart_id=latest_cart.cart_id
    ).order_by('-created_at').first()
    
    if cart_payment:
        print(f'Method 2: Found payment for latest cart: {cart_payment.merchant_order_id} (Status: {cart_payment.status})')
        if cart_payment.status == 'SUCCESS':
            print('  -> Would check for booking and create if missing')
        else:
            print(f'  -> Payment not successful: {cart_payment.status}')
    else:
        print('Method 2: NO payment found for latest cart')

# Method 3: Latest successful payment
latest_successful = PaymentOrder.objects.filter(
    status='SUCCESS',
    cart_id__isnull=False
).order_by('-created_at').first()

if latest_successful:
    print(f'Method 3: Latest successful payment: {latest_successful.merchant_order_id} - Cart: {latest_successful.cart_id}')
else:
    print('Method 3: NO successful payments found')
