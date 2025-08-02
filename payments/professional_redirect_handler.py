"""
PROFESSIONAL Real-Time Payment Verification Handler

This handler immediately verifies payments with PhonePe API when user returns,
creates bookings in real-time, and only shows success page when everything is complete.
"""

import logging
import time
from django.shortcuts import redirect
from django.http import JsonResponse, HttpResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings
from django.utils import timezone
from .services import PaymentService, WebhookService
from .models import PaymentOrder
from cart.models import Cart
from booking.models import Booking

logger = logging.getLogger(__name__)


@method_decorator(csrf_exempt, name='dispatch')
class ProfessionalPaymentRedirectHandler(View):
    """
    Professional real-time payment verification and booking creation
    """
    
    def get(self, request):
        """Handle payment redirect with IMMEDIATE verification and booking creation"""
        try:
            # Log redirect parameters
            all_params = dict(request.GET.items())
            logger.info(f"🔍 Payment redirect received: {all_params}")
            
            # Find the user's latest payment
            latest_payment = self._find_latest_payment(request)
            
            if not latest_payment:
                logger.error("❌ No payment found for redirect")
                return self._redirect_with_error("No payment found")
            
            logger.info(f"📋 Found payment: {latest_payment.merchant_order_id} (Status: {latest_payment.status})")
            
            # IMMEDIATELY verify payment status with PhonePe
            if latest_payment.status in ['INITIATED', 'PENDING']:
                logger.info(f"⚡ IMMEDIATE verification for {latest_payment.merchant_order_id}")
                
                # Real-time verification
                verification_result = self._verify_payment_immediately(latest_payment)
                
                if verification_result['success']:
                    latest_payment = verification_result['payment']
                    logger.info(f"✅ Payment verified as: {latest_payment.status}")
                else:
                    logger.error(f"❌ Payment verification failed: {verification_result['error']}")
            
            # Handle based on final payment status
            if latest_payment.status == 'SUCCESS':
                # IMMEDIATELY create booking if needed
                booking = self._ensure_booking_exists(latest_payment)
                
                if booking:
                    logger.info(f"✅ Booking ready: {booking.book_id}")
                    return self._redirect_to_success(booking.book_id)
                else:
                    logger.error(f"❌ Failed to create booking for {latest_payment.merchant_order_id}")
                    return self._redirect_with_error("Booking creation failed")
                    
            elif latest_payment.status in ['FAILED', 'CANCELLED']:
                logger.info(f"❌ Payment failed: {latest_payment.status}")
                return self._redirect_to_failure("Payment was not successful")
                
            else:
                logger.warning(f"⏳ Payment still pending: {latest_payment.status}")
                return self._redirect_to_pending(latest_payment.merchant_order_id)
                
        except Exception as e:
            logger.error(f"❌ Redirect handler error: {str(e)}")
            return self._redirect_with_error(f"System error: {str(e)}")
    
    def _find_latest_payment(self, request):
        """Find the user's most recent payment"""
        try:
            # If user is authenticated, find their latest payment
            if hasattr(request, 'user') and request.user.is_authenticated:
                payment = PaymentOrder.objects.filter(
                    user=request.user
                ).order_by('-created_at').first()
                
                if payment:
                    return payment
            
            # Fallback: Find most recent payment (within last 30 minutes)
            recent_cutoff = timezone.now() - timezone.timedelta(minutes=30)
            payment = PaymentOrder.objects.filter(
                created_at__gte=recent_cutoff
            ).order_by('-created_at').first()
            
            return payment
            
        except Exception as e:
            logger.error(f"Error finding latest payment: {e}")
            return None
    
    def _verify_payment_immediately(self, payment, max_retries=3):
        """Immediately verify payment with PhonePe - with retries for reliability"""
        for attempt in range(max_retries):
            try:
                logger.info(f"🔍 Verification attempt {attempt + 1}/{max_retries} for {payment.merchant_order_id}")
                
                payment_service = PaymentService()
                result = payment_service.check_payment_status(payment.merchant_order_id)
                
                if result and result.get('success'):
                    updated_payment = result['payment_order']
                    logger.info(f"✅ PhonePe verification successful: {updated_payment.status}")
                    
                    return {
                        'success': True,
                        'payment': updated_payment
                    }
                else:
                    logger.warning(f"⚠️ Verification attempt {attempt + 1} failed: {result}")
                    
                # Wait before retry (except last attempt)
                if attempt < max_retries - 1:
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"❌ Verification attempt {attempt + 1} error: {str(e)}")
                
                # Wait before retry (except last attempt)
                if attempt < max_retries - 1:
                    time.sleep(1)
        
        return {
            'success': False,
            'error': 'Payment verification failed after multiple attempts'
        }
    
    def _ensure_booking_exists(self, payment):
        """Ensure booking exists for successful payment - create if needed"""
        try:
            # Get cart
            cart = Cart.objects.get(cart_id=payment.cart_id)
            
            # Check if booking already exists
            existing_booking = Booking.objects.filter(cart=cart).first()
            
            if existing_booking:
                logger.info(f"📋 Booking already exists: {existing_booking.book_id}")
                return existing_booking
            
            # Create booking immediately
            logger.info(f"🏗️ Creating booking for payment {payment.merchant_order_id}")
            
            webhook_service = WebhookService()
            booking = webhook_service._create_booking_from_cart(payment)
            
            if booking:
                logger.info(f"✅ Booking created successfully: {booking.book_id}")
                
                # Send email notification asynchronously
                try:
                    from core.tasks import send_booking_confirmation
                    send_booking_confirmation.delay(booking.id)
                    logger.info(f"📧 Email notification queued for {booking.book_id}")
                except Exception as e:
                    logger.warning(f"Email notification failed: {e}")
                
                return booking
            else:
                logger.error("❌ Booking creation returned None")
                return None
                
        except Cart.DoesNotExist:
            logger.error(f"❌ Cart not found: {payment.cart_id}")
            return None
        except Exception as e:
            logger.error(f"❌ Booking creation error: {str(e)}")
            return None
    
    def _redirect_to_success(self, booking_id):
        """Redirect to success page with booking ID"""
        success_url = getattr(settings, 'PHONEPE_SUCCESS_REDIRECT_URL', f"{settings.FRONTEND_BASE_URL}/confirmbooking")
        
        # Add booking ID to URL
        if '?' in success_url:
            final_url = f"{success_url}&booking_id={booking_id}"
        else:
            final_url = f"{success_url}?booking_id={booking_id}"
        
        logger.info(f"✅ Redirecting to success: {final_url}")
        return redirect(final_url)
    
    def _redirect_to_failure(self, reason):
        """Redirect to failure page"""
        failure_url = getattr(settings, 'PHONEPE_FAILURE_REDIRECT_URL', f"{settings.FRONTEND_BASE_URL}/payment-failed")
        
        # Add error reason
        if '?' in failure_url:
            final_url = f"{failure_url}&reason={reason}"
        else:
            final_url = f"{failure_url}?reason={reason}"
        
        logger.info(f"❌ Redirecting to failure: {final_url}")
        return redirect(final_url)
    
    def _redirect_to_pending(self, merchant_order_id):
        """Redirect to pending page for verification"""
        pending_url = getattr(settings, 'PHONEPE_PENDING_REDIRECT_URL', f"{settings.FRONTEND_BASE_URL}/payment-pending")
        
        # Add order ID for frontend to poll
        if '?' in pending_url:
            final_url = f"{pending_url}&order_id={merchant_order_id}"
        else:
            final_url = f"{pending_url}?order_id={merchant_order_id}"
        
        logger.info(f"⏳ Redirecting to pending: {final_url}")
        return redirect(final_url)
    
    def _redirect_with_error(self, error_message):
        """Redirect with error message"""
        error_url = getattr(settings, 'PHONEPE_ERROR_REDIRECT_URL', f"{settings.FRONTEND_BASE_URL}/payment-error")
        
        if '?' in error_url:
            final_url = f"{error_url}&error={error_message}"
        else:
            final_url = f"{error_url}?error={error_message}"
        
        logger.error(f"❌ Redirecting with error: {final_url}")
        return redirect(final_url)
