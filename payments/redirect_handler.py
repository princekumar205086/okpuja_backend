"""
Smart Payment Redirect Handler
Handles both success and failure redirects from PhonePe
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
class PaymentRedirectHandler(View):
    """
    Smart redirect handler for PhonePe payments
    Determines success/failure and redirects to appropriate frontend page
    """
    
    def get(self, request):
        """Handle payment redirect from PhonePe"""
        try:
            # Log all parameters for debugging
            logger.info(f"Redirect parameters: {dict(request.GET.items())}")
            
            # PhonePe V2 might send different parameter names
            merchant_order_id = (
                request.GET.get('merchantOrderId') or 
                request.GET.get('merchantId') or
                request.GET.get('orderId') or
                request.GET.get('order_id') or
                request.GET.get('transactionId')
            )
            
            transaction_id = (
                request.GET.get('transactionId') or
                request.GET.get('transaction_id') or
                request.GET.get('paymentId')
            )
            
            # If still no order ID, check if we can extract from any parameter
            if not merchant_order_id:
                # Log all parameters to understand what PhonePe is sending
                all_params = dict(request.GET.items())
                logger.error(f"No merchant order ID found. All parameters: {all_params}")
                
                # Check if we have any OKPUJA order ID in any parameter
                for key, value in all_params.items():
                    if isinstance(value, str) and 'OKPUJA' in value:
                        merchant_order_id = value
                        logger.info(f"Found order ID in parameter '{key}': {merchant_order_id}")
                        break
            
            if not merchant_order_id:
                logger.error("No merchant order ID in redirect - redirecting to generic success page")
                # Instead of error, redirect to a generic success page
                success_url = getattr(settings, 'PHONEPE_SUCCESS_REDIRECT_URL', f"{settings.FRONTEND_BASE_URL}/confirmbooking")
                return redirect(f"{success_url}?status=completed")
            
            # Check payment status
            payment_service = PaymentService()
            result = payment_service.check_payment_status(merchant_order_id)
            
            if result['success']:
                payment_order = result['payment_order']
                status = payment_order.status
                
                # Determine redirect based on payment status
                if status == 'SUCCESS':
                    success_url = getattr(settings, 'PHONEPE_SUCCESS_REDIRECT_URL', f"{settings.FRONTEND_BASE_URL}/confirmbooking")
                    
                    # Handle different types of payments
                    booking_id = None
                    astro_book_id = None
                    frontend_base = None
                    
                    # Check if this is an astrology booking
                    logger.info(f"🔍 Checking payment metadata for order {merchant_order_id}: {payment_order.metadata}")
                    if payment_order.metadata.get('booking_type') == 'astrology':
                        logger.info(f"✅ Detected astrology booking for order: {merchant_order_id}")
                        try:
                            from astrology.models import AstrologyBooking
                            # Find the astrology booking created by webhook
                            astrology_booking = AstrologyBooking.objects.filter(payment_id=str(payment_order.id)).first()
                            
                            if astrology_booking:
                                astro_book_id = astrology_booking.astro_book_id
                                logger.info(f"✅ Found astrology booking: {astro_book_id}")
                            else:
                                # If no booking found, try to create it now (webhook might have failed)
                                logger.info(f"⚠️ No astrology booking found for payment {merchant_order_id}, creating now...")
                                webhook_service = WebhookService()
                                astrology_booking = webhook_service._create_astrology_booking(payment_order)
                                if astrology_booking:
                                    astro_book_id = astrology_booking.astro_book_id
                                    logger.info(f"✅ Astrology booking created during redirect: {astro_book_id}")
                                else:
                                    logger.error(f"❌ Failed to create astrology booking during redirect for {merchant_order_id}")
                            
                        except Exception as e:
                            logger.warning(f"❌ Could not get/create astrology booking for payment {payment_order.id}: {e}")
                        
                        # Get the original frontend URL from metadata for astrology bookings
                        frontend_base = payment_order.metadata.get('frontend_redirect_url', 'https://www.okpuja.com')
                        if frontend_base.endswith('/'):
                            frontend_base = frontend_base.rstrip('/')
                        logger.info(f"🌐 Using frontend base URL: {frontend_base}")
                    
                    # ENSURE booking exists for cart-based payments
                    elif payment_order.cart_id:
                        logger.info(f"📦 Regular puja booking for order: {merchant_order_id}")
                        try:
                            from cart.models import Cart
                            from booking.models import Booking
                            cart = Cart.objects.get(cart_id=payment_order.cart_id)
                            booking = Booking.objects.filter(cart=cart).first()
                            
                            # If no booking exists, create it now (in case webhook failed)
                            if not booking:
                                logger.info(f"No booking found for successful payment {merchant_order_id}, creating now...")
                                webhook_service = WebhookService()
                                booking = webhook_service._create_booking_from_cart(payment_order)
                                if booking:
                                    logger.info(f"Booking created during redirect: {booking.book_id}")
                                else:
                                    logger.error(f"Failed to create booking during redirect for {merchant_order_id}")
                            
                            if booking:
                                booking_id = booking.book_id
                                
                        except Exception as e:
                            logger.warning(f"Could not get/create booking for cart {payment_order.cart_id}: {e}")
                    
                    # Build redirect URL based on booking type
                    if astro_book_id:
                        # Astrology booking - redirect to astro success page with astro_book_id parameter
                        if not frontend_base:
                            frontend_base = "https://www.okpuja.com"  # Default fallback with www
                        redirect_url = f"{frontend_base}/astro-booking-success?astro_book_id={astro_book_id}"
                        logger.info(f"🎯 ASTROLOGY REDIRECT: {redirect_url}")
                    elif booking_id:
                        # Regular puja booking - use existing URL (keep unchanged)
                        redirect_url = f"{success_url}?book_id={booking_id}&order_id={merchant_order_id}&transaction_id={transaction_id or ''}"
                        logger.info(f"Redirecting to puja success page with booking ID: {booking_id}")
                    else:
                        # No booking found - redirect to generic success
                        redirect_url = f"{success_url}?order_id={merchant_order_id}&transaction_id={transaction_id or ''}&status=no_booking"
                        logger.warning(f"Redirecting to success page WITHOUT booking ID for order: {merchant_order_id}")
                    
                    return redirect(redirect_url)
                    
                elif status in ['FAILED', 'CANCELLED']:
                    # Check if this is an astrology booking
                    if payment_order.metadata.get('booking_type') == 'astrology':
                        # Extract frontend_base from metadata for astrology bookings
                        frontend_base = payment_order.metadata.get('frontend_redirect_url', 'https://www.okpuja.com').rstrip('/')
                        
                        # Try to get astro_book_id if booking exists
                        astro_book_id = None
                        try:
                            from astrology.models import AstrologyBooking
                            astrology_booking = AstrologyBooking.objects.filter(payment_id=str(payment_order.id)).first()
                            if astrology_booking:
                                astro_book_id = astrology_booking.astro_book_id
                        except Exception as e:
                            logger.warning(f"Could not get astrology booking for failed payment: {e}")
                        
                        # Astrology booking - redirect to astro failed page with astro_book_id parameter
                        if astro_book_id:
                            redirect_url = f"{frontend_base}/astro-booking-failed?astro_book_id={astro_book_id}&reason={status.lower()}"
                        else:
                            redirect_url = f"{frontend_base}/astro-booking-failed?merchant_order_id={merchant_order_id}&reason={status.lower()}"
                        logger.info(f"Redirecting to astrology failure page: {redirect_url}")
                    else:
                        # Regular puja booking - use existing failed URL (keep unchanged)
                        failed_url = getattr(settings, 'PHONEPE_FAILED_REDIRECT_URL', f"{settings.FRONTEND_BASE_URL}/payment/failed")
                        redirect_url = f"{failed_url}?order_id={merchant_order_id}&transaction_id={transaction_id or ''}&reason={status.lower()}"
                        logger.info(f"Redirecting to puja failure page for order: {merchant_order_id}, status: {status}")
                    
                    return redirect(redirect_url)
                    
                else:
                    # Payment still pending
                    pending_url = f"{settings.FRONTEND_BASE_URL}/payment/pending"
                    redirect_url = f"{pending_url}?order_id={merchant_order_id}&transaction_id={transaction_id or ''}"
                    logger.info(f"Redirecting to pending page for order: {merchant_order_id}, status: {status}")
                    return redirect(redirect_url)
                    
            else:
                logger.error(f"Failed to check payment status for order: {merchant_order_id}")
                # Redirect to success page anyway, let frontend handle status check
                success_url = getattr(settings, 'PHONEPE_SUCCESS_REDIRECT_URL', f"{settings.FRONTEND_BASE_URL}/confirmbooking")
                return redirect(f"{success_url}?order_id={merchant_order_id}&status=unknown")
                
        except Exception as e:
            logger.error(f"Payment redirect error: {e}")
            # Redirect to success page instead of error
            success_url = getattr(settings, 'PHONEPE_SUCCESS_REDIRECT_URL', f"{settings.FRONTEND_BASE_URL}/confirmbooking")
            return redirect(f"{success_url}?status=completed")
    
    def post(self, request):
        """Handle POST redirect (if PhonePe sends POST)"""
        return self.get(request)
