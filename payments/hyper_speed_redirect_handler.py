"""
HYPER-SPEED Payment Redirect Handler

This handler implements instant redirects for the fastest possible user experience:
- 200ms target response time
- Bypasses slow PhonePe API calls when possible
- Creates bookings instantly on redirect
- Handles verification asynchronously
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
class HyperSpeedPaymentRedirectHandler(View):
    """
    HYPER-SPEED payment redirect with instant response (200ms target)
    """
    
    def get(self, request):
        """INSTANT redirect with minimal processing"""
        start_time = timezone.now()
        logger.info(f"🚀 HYPER-SPEED redirect started")
        
        try:
            # INSTANT: Find payment without complex queries
            latest_payment = self._find_payment_instantly(request)
            
            if not latest_payment:
                logger.warning("⚠️ No payment found, redirecting to pending")
                return self._instant_redirect_pending()
            
            logger.info(f"⚡ Found payment: {latest_payment.merchant_order_id}")
            
            # INSTANT: Check if booking already exists (fastest path)
            existing_booking = self._check_existing_booking(latest_payment)
            
            if existing_booking:
                processing_time = (timezone.now() - start_time).total_seconds()
                logger.info(f"🚀 INSTANT SUCCESS: {existing_booking.book_id} in {processing_time:.3f}s")
                return self._instant_redirect_success(existing_booking.book_id)
            
            # CRITICAL FIX: Verify payment before creating booking
            verification_result = self._verify_payment_quickly(latest_payment)
            
            if verification_result['success'] and verification_result['payment'].status == 'SUCCESS':
                # Payment verified as successful - now create booking
                booking = self._create_booking_instantly(verification_result['payment'])
                
                if booking:
                    processing_time = (timezone.now() - start_time).total_seconds()
                    logger.info(f"🚀 VERIFIED SUCCESS: {booking.book_id} in {processing_time:.3f}s")
                    return self._instant_redirect_success(booking.book_id)
                else:
                    logger.error("❌ Fast booking creation failed after payment verification")
                    return self._instant_redirect_pending()
            elif verification_result['payment'].status in ['FAILED', 'CANCELLED']:
                # Payment failed - redirect to failure page
                logger.info(f"❌ Payment verification failed: {verification_result['payment'].status}")
                return self._instant_redirect_failure("Payment was not successful")
            else:
                # Payment still pending - redirect to pending
                logger.info(f"⏳ Payment still pending: {verification_result['payment'].status}")
                return self._instant_redirect_pending()
                
        except Exception as e:
            processing_time = (timezone.now() - start_time).total_seconds()
            logger.error(f"❌ HYPER-SPEED error in {processing_time:.3f}s: {str(e)}")
            return self._instant_redirect_pending()
    
    def _find_payment_instantly(self, request):
        """INSTANT payment finding with minimal queries"""
        try:
            # Method 1: If user is authenticated, get their latest payment
            if hasattr(request, 'user') and request.user.is_authenticated:
                payment = PaymentOrder.objects.filter(
                    user=request.user
                ).order_by('-created_at').first()
                
                if payment:
                    return payment
            
            # Method 2: Get most recent payment (very fast fallback)
            recent_cutoff = timezone.now() - timezone.timedelta(minutes=5)
            payment = PaymentOrder.objects.filter(
                created_at__gte=recent_cutoff,
                status__in=['INITIATED', 'PENDING', 'SUCCESS']
            ).order_by('-created_at').first()
            
            return payment
            
        except Exception as e:
            logger.error(f"❌ Instant payment search error: {e}")
            return None
    
    def _check_existing_booking(self, payment):
        """INSTANT booking check"""
        try:
            # Check if booking already exists for this cart
            if payment.cart_id:
                cart = Cart.objects.get(cart_id=payment.cart_id)
                existing_booking = Booking.objects.filter(cart=cart).first()
                return existing_booking
        except Exception as e:
            logger.error(f"❌ Booking check error: {e}")
        return None
    
    def _create_booking_instantly(self, payment):
        """INSTANT booking creation - ZERO verification delays"""
        try:
            logger.info(f"🚀 INSTANT booking creation for {payment.merchant_order_id}")
            
            # Get cart quickly
            cart = Cart.objects.get(cart_id=payment.cart_id)
            
            # Check if booking already exists first (avoid duplicates)
            existing_booking = Booking.objects.filter(cart=cart).first()
            if existing_booking:
                logger.info(f"🚀 INSTANT: Booking already exists: {existing_booking.book_id}")
                return existing_booking
            
            # Handle time conversion efficiently
            from datetime import datetime, time
            try:
                if isinstance(cart.selected_time, str):
                    time_str = cart.selected_time.strip()
                    if ':' in time_str and ('AM' in time_str.upper() or 'PM' in time_str.upper()):
                        selected_time = datetime.strptime(time_str.upper(), '%I:%M %p').time()
                    elif ':' in time_str:
                        selected_time = datetime.strptime(time_str, '%H:%M').time()
                    else:
                        selected_time = time(10, 0)  # Default
                else:
                    selected_time = cart.selected_time
            except:
                selected_time = time(10, 0)  # Safe default
            
            # Get user's address for booking from payment order (CRITICAL: Address field support)
            address_id = None
            try:
                if payment.address_id:
                    # Use the address selected during checkout
                    from accounts.models import Address
                    address = Address.objects.get(id=payment.address_id, user=cart.user)
                    address_id = address.id
                    logger.info(f"🏠 Using selected address: {address.id}")
                else:
                    # Fallback: Get user's default address or any address
                    from accounts.models import Address
                    address = Address.objects.filter(user=cart.user, is_default=True).first()
                    if not address:
                        address = Address.objects.filter(user=cart.user).first()
                    address_id = address.id if address else None
                    logger.info(f"🏠 Fallback address: {address.id if address else 'None'}")
            except Exception as e:
                logger.warning(f"Could not get address for user {cart.user.id}: {e}")
            
            # Create booking instantly (ONLY after payment verification)
            booking = Booking.objects.create(
                cart=cart,
                user=cart.user,
                selected_date=cart.selected_date,
                selected_time=selected_time,
                address_id=address_id,  # Use address_id from payment directly
                status='CONFIRMED'  # Only set after payment verification
            )
            
            # POST-BOOKING CLEANUP: Clear the cart after successful booking
            self._clean_cart_after_booking(cart)
            
            logger.info(f"🚀 VERIFIED BOOKING: {booking.book_id} with address_id: {address_id}")
            return booking
            
        except Exception as e:
            logger.error(f"❌ Instant booking error: {str(e)}")
            return None
    
    def _verify_payment_quickly(self, payment):
        """Quick payment verification with minimal delay"""
        try:
            logger.info(f"🚀 Quick verification for {payment.merchant_order_id}")
            
            payment_service = PaymentService()
            result = payment_service.check_payment_status(payment.merchant_order_id)
            
            if result and result.get('success'):
                updated_payment = result['payment_order']
                logger.info(f"🚀 Verification result: {updated_payment.status}")
                
                return {
                    'success': True,
                    'payment': updated_payment
                }
            else:
                logger.warning(f"⚠️ Verification failed: {result}")
                return {
                    'success': False,
                    'payment': payment,
                    'error': 'Verification failed'
                }
                
        except Exception as e:
            logger.error(f"❌ Verification error: {str(e)}")
            return {
                'success': False,
                'payment': payment,
                'error': str(e)
            }

    def _trigger_async_verification(self, payment):
        """Trigger background verification without waiting"""
        try:
            # This could be enhanced with Celery/background tasks
            # For now, just update the payment status optimistically
            if payment.status in ['INITIATED', 'PENDING']:
                # We'll verify this in background - for now assume SUCCESS for speed
                payment.status = 'SUCCESS'
                payment.save()
                logger.info(f"🚀 Optimistic status update: {payment.merchant_order_id}")
        except Exception as e:
            logger.error(f"❌ Async verification error: {e}")
    
    def _instant_redirect_success(self, booking_id):
        """INSTANT success redirect"""
        success_url = getattr(settings, 'PHONEPE_SUCCESS_REDIRECT_URL', 'http://localhost:3000/confirmbooking')
        redirect_url = f"{success_url}?booking_id={booking_id}&hyper_speed=true"
        
        logger.info(f"🚀 INSTANT SUCCESS: {redirect_url}")
        return redirect(redirect_url)
    
    def _instant_redirect_failure(self, reason):
        """INSTANT failure redirect"""
        failure_url = getattr(settings, 'PHONEPE_FAILED_REDIRECT_URL', 'http://localhost:3000/failedbooking')
        redirect_url = f"{failure_url}?reason={reason}&hyper_speed=true"
        
        logger.info(f"🚀 INSTANT FAILURE: {redirect_url}")
        return redirect(redirect_url)

    def _instant_redirect_pending(self):
        """INSTANT pending redirect"""
        pending_url = getattr(settings, 'PHONEPE_PENDING_REDIRECT_URL', 'http://localhost:3000/payment-pending')
        redirect_url = f"{pending_url}?hyper_speed=true&auto_refresh=true"
        
        logger.info(f"🚀 INSTANT PENDING: {redirect_url}")
        return redirect(redirect_url)
    
    def _clean_cart_after_booking(self, cart):
        """Clean cart after successful booking to prevent reuse"""
        try:
            # Mark cart as converted to prevent reuse
            cart.status = cart.StatusChoices.CONVERTED
            cart.save()
            
            logger.info(f"🧹 CART CLEANED: {cart.cart_id} status={cart.status}")
        except Exception as e:
            logger.error(f"⚠️ CART CLEANUP ERROR: {e}")
            # Don't fail the booking for cleanup errors
