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
        """Handle payment redirect with ULTRA-FAST verification and booking creation"""
        try:
            # Log redirect parameters
            all_params = dict(request.GET.items())
            logger.info(f"⚡ LIGHTNING payment redirect: {all_params}")
            
            # Check if this is a duplicate/manual click (user clicked "click here")
            user_agent = request.headers.get('User-Agent', '').lower()
            referer = request.headers.get('Referer', '')
            
            if 'phonepe' in referer.lower():
                logger.info(f"🔄 Direct redirect from PhonePe - ULTRA-FAST processing")
            else:
                logger.info(f"👆 User may have clicked manual redirect - handling gracefully")
            
            # Find the user's latest payment with optimized query
            latest_payment = self._find_latest_payment(request)
            
            if not latest_payment:
                logger.error("❌ No payment found for redirect")
                return self._redirect_with_error("No payment found")
            
            logger.info(f"⚡ Found payment: {latest_payment.merchant_order_id} (Status: {latest_payment.status})")
            
            # ULTRA-FAST verification for any non-SUCCESS status
            if latest_payment.status in ['INITIATED', 'PENDING']:
                logger.info(f"⚡ LIGHTNING verification for {latest_payment.merchant_order_id}")
                
                # Ultra-fast verification with minimal retries
                verification_result = self._verify_payment_immediately(latest_payment)
                
                if verification_result['success']:
                    latest_payment = verification_result['payment']
                    logger.info(f"⚡ INSTANT verification: {latest_payment.status}")
                else:
                    logger.warning(f"⚠️ Quick verification inconclusive: {verification_result['error']}")
            
            # Handle based on final payment status
            if latest_payment.status == 'SUCCESS':
                # ULTRA-FAST booking creation
                booking = self._ensure_booking_exists(latest_payment)
                
                if booking:
                    logger.info(f"⚡ LIGHTNING SUCCESS: {booking.book_id}")
                    return self._redirect_to_success(booking.book_id)
                else:
                    logger.error(f"❌ Speed booking failed for {latest_payment.merchant_order_id}")
                    return self._redirect_with_error("Booking creation failed")
                    
            elif latest_payment.status in ['FAILED', 'CANCELLED']:
                logger.info(f"❌ Payment failed: {latest_payment.status}")
                return self._redirect_to_failure("Payment was not successful")
                
            else:
                logger.warning(f"⏳ Payment still processing: {latest_payment.status}")
                # For very fast processing, redirect to a smart pending page
                return self._redirect_to_smart_pending(latest_payment.merchant_order_id)
                
        except Exception as e:
            logger.error(f"❌ SPEED redirect error: {str(e)}")
            return self._redirect_with_error(f"System error: {str(e)}")
    
    def _find_latest_payment(self, request):
        """SPEED-OPTIMIZED payment finding"""
        try:
            logger.info(f"⚡ FAST payment search")
            
            # If user is authenticated, find their latest payment (optimized query)
            if hasattr(request, 'user') and request.user.is_authenticated:
                payment = PaymentOrder.objects.select_related('user').filter(
                    user=request.user
                ).order_by('-created_at').first()
                
                if payment:
                    logger.info(f"⚡ FOUND user payment: {payment.merchant_order_id}")
                    return payment
            
            # Fallback: Find most recent payment (within last 10 minutes for speed)
            recent_cutoff = timezone.now() - timezone.timedelta(minutes=10)
            payment = PaymentOrder.objects.filter(
                created_at__gte=recent_cutoff
            ).order_by('-created_at').first()
            
            if payment:
                logger.info(f"⚡ FOUND recent payment: {payment.merchant_order_id}")
            
            return payment
            
        except Exception as e:
            logger.error(f"❌ Speed payment search error: {e}")
            return None
    
    def _detect_manual_redirect(self, request):
        """
        🖱️ DETECT MANUAL vs AUTOMATIC REDIRECT
        Determines if user clicked "click here" manually or automatic redirect
        """
        # Check for manual redirect indicators
        manual_indicators = [
            'manual' in request.GET,
            'click' in request.GET,
            request.headers.get('User-Agent', '').lower().count('click') > 0,
            request.META.get('HTTP_REFERER', '').endswith('/click')
        ]
        
        is_manual = any(manual_indicators)
        
        if is_manual:
            logger.info(f"🖱️ Manual redirect detected for {request.GET.get('merchantTransactionId', 'unknown')}")
        else:
            logger.info(f"⚡ Automatic redirect detected for {request.GET.get('merchantTransactionId', 'unknown')}")
            
        return is_manual

    def _verify_payment_immediately(self, payment):
        """ULTRA-FAST payment verification - optimized for speed"""
        max_retries = 2  # Reduced for ultra-fast processing
        logger.info(f"⚡ ULTRA-FAST verification for {payment.merchant_order_id}")
        
        for attempt in range(max_retries):
            try:
                # No delay on first attempt - immediate verification
                logger.info(f"⚡ Lightning verification attempt {attempt + 1}/{max_retries}")
                
                payment_service = PaymentService()
                result = payment_service.check_payment_status(payment.merchant_order_id)
                
                if result and result.get('success'):
                    updated_payment = result['payment_order']
                    logger.info(f"⚡ INSTANT verification successful: {updated_payment.status}")
                    
                    return {
                        'success': True,
                        'payment': updated_payment
                    }
                else:
                    logger.warning(f"⚠️ Quick retry {attempt + 1}: {result}")
                    
                # Minimal delay only on retry (0.5 seconds instead of 1)
                if attempt < max_retries - 1:
                    time.sleep(0.5)
                    
            except Exception as e:
                logger.error(f"❌ Fast verification attempt {attempt + 1} error: {str(e)}")
                
                # Quick retry with minimal delay
                if attempt < max_retries - 1:
                    time.sleep(0.5)
        
        return {
            'success': False,
            'error': 'Ultra-fast verification failed - payment may still be processing'
        }
    
    def _ensure_booking_exists(self, payment):
        """ULTRA-FAST booking creation - optimized for speed"""
        try:
            logger.info(f"⚡ SPEED-OPTIMIZED booking check for {payment.merchant_order_id}")
            
            # Get cart with minimal database queries
            cart = Cart.objects.select_related('user').get(cart_id=payment.cart_id)
            
            # Quick check if booking already exists
            existing_booking = Booking.objects.filter(cart=cart).first()
            
            if existing_booking:
                logger.info(f"⚡ INSTANT: Booking already exists: {existing_booking.book_id}")
                return existing_booking
            
            # ULTRA-FAST booking creation
            logger.info(f"⚡ SPEED-CREATING new booking for cart {cart.cart_id}")
            
            # Create booking with minimal validation
            booking = Booking.objects.create(
                cart=cart,
                user=cart.user,
                total_amount=payment.amount,
                payment_status='PAID',
                booking_status='CONFIRMED',
                payment_id=payment.merchant_order_id
            )
            
            logger.info(f"⚡ LIGHTNING BOOKING CREATED: {booking.book_id}")
            return booking
            
        except Exception as e:
            logger.error(f"❌ Speed booking error: {str(e)}")
            return None
    
    def _redirect_to_success(self, booking_id):
        """ULTRA-FAST success redirect"""
        success_url = getattr(settings, 'PHONEPE_SUCCESS_REDIRECT_URL', 'http://localhost:3000/confirmbooking')
        redirect_url = f"{success_url}?booking_id={booking_id}&ultra_fast=true"
        
        logger.info(f"✅ SPEED SUCCESS redirect: {redirect_url}")
        return redirect(redirect_url)
    
    def _redirect_to_failure(self, message):
        """ULTRA-FAST failure redirect"""
        error_url = getattr(settings, 'PHONEPE_ERROR_REDIRECT_URL', 'http://localhost:3000/payment-error')
        redirect_url = f"{error_url}?error={message}"
        
        logger.info(f"❌ SPEED FAILURE redirect: {redirect_url}")
        return redirect(redirect_url)
    
    def _redirect_with_error(self, error_message):
        """ULTRA-FAST error redirect"""
        logger.error(f"❌ Redirecting with error: {error_message}")
        
        error_url = getattr(settings, 'PHONEPE_ERROR_REDIRECT_URL', 'http://localhost:3000/payment-error')
        redirect_url = f"{error_url}?error={error_message}"
        
        logger.info(f"❌ ERROR redirect: {redirect_url}")
        return redirect(redirect_url)
    
    def _redirect_to_smart_pending(self, merchant_order_id):
        """ULTRA-FAST smart pending redirect with auto-refresh"""
        pending_url = getattr(settings, 'PHONEPE_PENDING_REDIRECT_URL', 'http://localhost:3000/payment-pending')
        redirect_url = f"{pending_url}?payment_id={merchant_order_id}&auto_refresh=true"
        
        logger.info(f"⏳ SMART PENDING redirect: {redirect_url}")
        return redirect(redirect_url)
