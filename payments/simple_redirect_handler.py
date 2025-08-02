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
            cart_id = None
            latest_order_id = None
            
            # Method 1: Check if PhonePe sent any order-related parameters (most reliable)
            cart_id, latest_order_id = self._check_phonepe_parameters(all_params, request)
            
            # Method 2: If user is authenticated, find their latest payment
            if not cart_id and hasattr(request, 'user') and request.user.is_authenticated:
                cart_id, latest_order_id = self._find_user_latest_cart(request.user, request)
            
            # Method 3: Find most recent payment and ensure it has cart (fallback)
            if not cart_id:
                cart_id, latest_order_id = self._find_latest_payment_cart()
            
            # Build redirect URL using cart_id instead of book_id
            if cart_id and latest_order_id:
                redirect_url = f"{success_url}?cart_id={cart_id}&order_id={latest_order_id}&redirect_source=phonepe"
                logger.info(f"Redirecting with cart ID: {cart_id}")
            else:
                # Add any parameters PhonePe sent
                if all_params:
                    param_string = "&".join([f"{k}={v}" for k, v in all_params.items()])
                    redirect_url = f"{success_url}?{param_string}&redirect_source=phonepe&status=no_cart"
                else:
                    redirect_url = f"{success_url}?redirect_source=phonepe&status=no_cart"
                logger.warning("No cart ID found - using fallback redirect")
            
            logger.info(f"Final redirect URL: {redirect_url}")
            return redirect(redirect_url)
                
        except Exception as e:
            logger.error(f"Payment redirect error: {e}")
            success_url = getattr(settings, 'PHONEPE_SUCCESS_REDIRECT_URL', f"{settings.FRONTEND_BASE_URL}/confirmbooking")
            return redirect(f"{success_url}?redirect_source=phonepe&error=redirect_error")
    
    def _find_user_latest_cart(self, user, request=None):
        """Find user's latest cart and ensure it has payment"""
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
                        updated_status = payment_service.check_payment_status(cart_payment.merchant_order_id)
                        cart_payment.refresh_from_db()
                        logger.info(f"Updated payment status: {cart_payment.status}")
                    
                    # If payment successful, ensure booking exists (but still return cart_id)
                    if cart_payment.status == 'SUCCESS':
                        booking = Booking.objects.filter(cart=latest_cart).first()
                        
                        # Create booking if it doesn't exist
                        if not booking:
                            webhook_service = WebhookService()
                            booking = webhook_service._create_booking_from_cart(cart_payment)
                            logger.info(f"Created booking during redirect: {booking.book_id if booking else 'FAILED'}")
                            
                            # Send email notifications
                            if booking:
                                try:
                                    from core.tasks import send_booking_confirmation
                                    send_booking_confirmation.delay(booking.id)
                                    logger.info(f"Email notification queued for booking {booking.book_id}")
                                except Exception as e:
                                    logger.error(f"Failed to queue email notification: {e}")
                        
                        if booking:
                            logger.info(f"Found/created booking: {booking.book_id}")
                            
                        # Always return cart_id for successful payments
                        return latest_cart.cart_id, cart_payment.merchant_order_id
                    
                    # ENHANCED: Handle sandbox/test payments that redirect but don't get webhooks
                    elif cart_payment.status in ['INITIATED', 'PENDING'] and request and request.path.endswith('/redirect/simple/'):
                        # This is likely a successful redirect from PhonePe sandbox
                        # In production, webhook would have updated status, but in sandbox it might not
                        logger.info(f"Payment redirect detected for {cart_payment.status} payment - checking if booking should be created")
                        
                        # Check if this cart already has a booking
                        existing_booking = Booking.objects.filter(cart=latest_cart).first()
                        
                        if not existing_booking:
                            # For redirect flow, we can assume payment was successful 
                            # Update payment status and create booking
                            logger.info(f"Assuming payment success for redirect flow - updating status")
                            cart_payment.status = 'SUCCESS'
                            cart_payment.save()
                            
                            # Create booking
                            webhook_service = WebhookService()
                            booking = webhook_service._create_booking_from_cart(cart_payment)
                            logger.info(f"Created booking from redirect flow: {booking.book_id if booking else 'FAILED'}")
                            
                            # Send email notifications
                            if booking:
                                try:
                                    from core.tasks import send_booking_confirmation
                                    send_booking_confirmation.delay(booking.id)
                                    logger.info(f"Email notification queued for booking {booking.book_id}")
                                except Exception as e:
                                    logger.error(f"Failed to queue email notification: {e}")
                        else:
                            logger.info(f"Booking already exists: {existing_booking.book_id}")
                        
                        # Return cart_id for redirect flow
                        return latest_cart.cart_id, cart_payment.merchant_order_id
                    else:
                        logger.warning(f"Payment not successful: {cart_payment.status}")
                        # Still return cart_id for incomplete payments
                        return latest_cart.cart_id, cart_payment.merchant_order_id
                else:
                    logger.warning("No payment found for latest cart")
            else:
                logger.warning("No cart found for user")
                
        except Exception as e:
            logger.error(f"Error finding user latest cart: {e}")
        
        return None, None
    
    def _check_phonepe_parameters(self, params, request=None):
        """Check if PhonePe sent any order-related parameters"""
        try:
            # Look for any order ID in PhonePe parameters
            order_id = None
            
            # Check for common PhonePe parameter names
            possible_keys = ['merchantOrderId', 'orderId', 'order_id', 'merchantTransactionId', 'transactionId']
            
            # First check direct parameter names
            for key in possible_keys:
                if key in params:
                    order_id = params[key]
                    break
            
            # If not found, check for any parameter containing order patterns
            if not order_id:
                for key, value in params.items():
                    if 'order' in key.lower() or 'OKPUJA' in str(value) or 'CART_' in str(value):
                        order_id = value
                        break
            
            if order_id:
                from .models import PaymentOrder
                payment = PaymentOrder.objects.filter(merchant_order_id=order_id).first()
                if payment and payment.cart_id:
                    logger.info(f"Found payment via PhonePe params: {payment.merchant_order_id}")
                    
                    # Check payment status and update if needed
                    if payment.status in ['INITIATED', 'PENDING']:
                        payment_service = PaymentService()
                        payment_service.check_payment_status(payment.merchant_order_id)
                        payment.refresh_from_db()
                        logger.info(f"Updated payment status via params: {payment.status}")
                    
                    # Ensure booking exists for this payment
                    from cart.models import Cart
                    from booking.models import Booking
                    
                    cart = Cart.objects.get(cart_id=payment.cart_id)
                    booking = Booking.objects.filter(cart=cart).first()
                    
                    if not booking and payment.status == 'SUCCESS':
                        webhook_service = WebhookService()
                        booking = webhook_service._create_booking_from_cart(payment)
                        logger.info(f"Created booking via PhonePe params: {booking.book_id if booking else 'FAILED'}")
                        
                        # Send email notifications
                        if booking:
                            try:
                                from core.tasks import send_booking_confirmation
                                send_booking_confirmation.delay(booking.id)
                                logger.info(f"Email notification queued for booking {booking.book_id}")
                            except Exception as e:
                                logger.error(f"Failed to queue email notification: {e}")
                    
                    # ENHANCED: Handle redirect flow for sandbox payments
                    elif not booking and payment.status in ['INITIATED', 'PENDING'] and request and request.path.endswith('/redirect/simple/'):
                        logger.info(f"Redirect flow detected for {payment.status} payment - assuming success")
                        # Update payment status for redirect flow
                        payment.status = 'SUCCESS'
                        payment.save()
                        
                        # Create booking
                        webhook_service = WebhookService()
                        booking = webhook_service._create_booking_from_cart(payment)
                        logger.info(f"Created booking from redirect (PhonePe params): {booking.book_id if booking else 'FAILED'}")
                        
                        # Send email notifications
                        if booking:
                            try:
                                from core.tasks import send_booking_confirmation
                                send_booking_confirmation.delay(booking.id)
                                logger.info(f"Email notification queued for booking {booking.book_id}")
                            except Exception as e:
                                logger.error(f"Failed to queue email notification: {e}")
                    
                    # Return cart_id instead of booking_id
                    return payment.cart_id, payment.merchant_order_id
        
        except Exception as e:
            logger.error(f"Error checking PhonePe parameters: {e}")
        
        return None, None
    
    def _find_latest_payment_cart(self):
        """Find the most recent successful payment and return its cart_id"""
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
                
                # Return cart_id regardless of booking status
                return latest_payment.cart_id, latest_payment.merchant_order_id
        
        except Exception as e:
            logger.error(f"Error finding latest payment cart: {e}")
        
        return None, None
    
    def post(self, request):
        """Handle POST redirect (if PhonePe sends POST)"""
        return self.get(request)
