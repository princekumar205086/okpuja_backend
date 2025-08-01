"""
Smart Payment Redirect Handler for PhonePe V2

Since PhonePe V2 Standard Checkout doesn't send order ID in redirect URL,
this handler finds the user's latest payment and ensures booking exists.
"""

import logging
from django.shortcuts import redirect
from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from .services import PaymentService, WebhookService

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class SimplePaymentRedirectHandler(View):
    """
    Smart redirect handler for PhonePe V2 payments
    Finds user's latest payment and includes booking ID in redirect
    """
    
    def get(self, request):
        """Handle payment redirect from PhonePe - find latest payment and redirect with booking ID"""
        try:
            # Log what PhonePe is sending
            all_params = dict(request.GET.items())
            logger.info(f"PhonePe redirect parameters: {all_params}")
            
            success_url = getattr(settings, 'PHONEPE_SUCCESS_REDIRECT_URL', f"{settings.FRONTEND_BASE_URL}/confirmbooking")
            
            # Try to find user's latest payment and ensure booking exists
            booking_id = None
            latest_order_id = None
            
            # Method 1: If user is authenticated, find their latest payment
            if hasattr(request, 'user') and request.user.is_authenticated:
                booking_id, latest_order_id = self._find_user_latest_booking(request.user)
            
            # Method 2: Check if PhonePe sent any order-related parameters
            if not booking_id:
                booking_id, latest_order_id = self._check_phonepe_parameters(all_params)
            
            # Method 3: Find most recent payment and ensure it has booking
            if not booking_id:
                booking_id, latest_order_id = self._find_latest_payment_booking()
            
            # Build redirect URL
            if booking_id and latest_order_id:
                redirect_url = f"{success_url}?book_id={booking_id}&order_id={latest_order_id}&redirect_source=phonepe"
                logger.info(f"Redirecting with booking ID: {booking_id}")
            else:
                # Add any parameters PhonePe sent
                if all_params:
                    param_string = "&".join([f"{k}={v}" for k, v in all_params.items()])
                    redirect_url = f"{success_url}?{param_string}&redirect_source=phonepe&status=no_booking"
                else:
                    redirect_url = f"{success_url}?redirect_source=phonepe&status=no_booking"
                logger.warning("No booking ID found - using fallback redirect")
            
            logger.info(f"Final redirect URL: {redirect_url}")
            return redirect(redirect_url)
                
        except Exception as e:
            logger.error(f"Payment redirect error: {e}")
            success_url = getattr(settings, 'PHONEPE_SUCCESS_REDIRECT_URL', f"{settings.FRONTEND_BASE_URL}/confirmbooking")
            return redirect(f"{success_url}?redirect_source=phonepe&error=redirect_error")
    
    def _find_user_latest_booking(self, user):
        """Find user's latest cart and ensure it has payment and booking"""
        try:
            from .models import PaymentOrder
            from cart.models import Cart
            from booking.models import Booking
            
            # First, find user's most recent cart (regardless of payment status)
            latest_cart = Cart.objects.filter(user=user).order_by('-created_at').first()
            
            if latest_cart:
                logger.info(f"Found user's latest cart: {latest_cart.cart_id}")
                
                # Check if this cart has a payment
                cart_payment = PaymentOrder.objects.filter(
                    user=user,
                    cart_id=latest_cart.cart_id
                ).order_by('-created_at').first()
                
                if cart_payment:
                    logger.info(f"Found payment for latest cart: {cart_payment.merchant_order_id} (status: {cart_payment.status})")
                    
                    # Check payment status and update if needed
                    if cart_payment.status in ['INITIATED', 'PENDING']:
                        payment_service = PaymentService()
                        payment_service.check_payment_status(cart_payment.merchant_order_id)
                        cart_payment.refresh_from_db()
                        logger.info(f"Updated payment status: {cart_payment.status}")
                    
                    # If payment successful, ensure booking exists
                    if cart_payment.status == 'SUCCESS':
                        booking = Booking.objects.filter(cart=latest_cart).first()
                        
                        # Create booking if it doesn't exist
                        if not booking:
                            webhook_service = WebhookService()
                            booking = webhook_service._create_booking_from_cart(cart_payment)
                            logger.info(f"Created booking during redirect: {booking.book_id if booking else 'FAILED'}")
                        
                        if booking:
                            logger.info(f"Found/created booking: {booking.book_id}")
                            return booking.book_id, cart_payment.merchant_order_id
                        else:
                            logger.warning("Failed to create booking for successful payment")
                    else:
                        logger.warning(f"Payment not successful: {cart_payment.status}")
                else:
                    logger.warning("No payment found for latest cart")
            else:
                logger.warning("No cart found for user")
                
        except Exception as e:
            logger.error(f"Error finding user latest booking: {e}")
        
        return None, None
    
    def _check_phonepe_parameters(self, params):
        """Check if PhonePe sent any order-related parameters"""
        try:
            # Look for any order ID in PhonePe parameters
            order_id = None
            for key, value in params.items():
                if 'order' in key.lower() or 'OKPUJA' in str(value) or 'CART_' in str(value):
                    order_id = value
                    break
            
            if order_id:
                from .models import PaymentOrder
                payment = PaymentOrder.objects.filter(merchant_order_id=order_id).first()
                if payment and payment.cart_id:
                    # Ensure booking exists for this payment
                    from cart.models import Cart
                    from booking.models import Booking
                    
                    cart = Cart.objects.get(cart_id=payment.cart_id)
                    booking = Booking.objects.filter(cart=cart).first()
                    
                    if not booking and payment.status == 'SUCCESS':
                        webhook_service = WebhookService()
                        booking = webhook_service._create_booking_from_cart(payment)
                    
                    if booking:
                        return booking.book_id, payment.merchant_order_id
        
        except Exception as e:
            logger.error(f"Error checking PhonePe parameters: {e}")
        
        return None, None
    
    def _find_latest_payment_booking(self):
        """Find the most recent successful payment and ensure it has booking"""
        try:
            from .models import PaymentOrder
            from cart.models import Cart
            from booking.models import Booking
            
            # Find most recent successful cart-based payment
            latest_payment = PaymentOrder.objects.filter(
                status='SUCCESS',
                cart_id__isnull=False
            ).order_by('-created_at').first()
            
            if latest_payment and latest_payment.cart_id:
                cart = Cart.objects.get(cart_id=latest_payment.cart_id)
                booking = Booking.objects.filter(cart=cart).first()
                
                # Create booking if it doesn't exist
                if not booking:
                    webhook_service = WebhookService()
                    booking = webhook_service._create_booking_from_cart(latest_payment)
                    logger.info(f"Created booking for latest payment: {booking.book_id if booking else 'FAILED'}")
                
                if booking:
                    return booking.book_id, latest_payment.merchant_order_id
        
        except Exception as e:
            logger.error(f"Error finding latest payment booking: {e}")
        
        return None, None
    
    def post(self, request):
        """Handle POST redirect (if PhonePe sends POST)"""
        return self.get(request)
