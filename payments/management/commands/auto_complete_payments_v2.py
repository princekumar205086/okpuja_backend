"""
Automatic Payment Completion Service - IMPROVED VERSION

This service automatically checks and completes INITIATED payments
with proper rate limiting and retry logic to avoid API limits.
"""

import logging
import time
import random
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from payments.models import PaymentOrder
from payments.services import PaymentService, WebhookService
from cart.models import Cart
from booking.models import Booking

logger = logging.getLogger(__name__)


class PaymentAutoCompleter:
    """Enhanced payment auto-completion with rate limiting"""
    
    def __init__(self):
        self.payment_service = PaymentService()
        self.webhook_service = WebhookService()
    
    def verify_payment_with_retry(self, payment, max_retries=3):
        """Verify payment with exponential backoff and rate limiting"""
        for attempt in range(max_retries):
            try:
                # Add random delay to avoid hitting rate limits
                if attempt > 0:
                    delay = (2 ** attempt) + random.uniform(0, 1)  # Exponential backoff with jitter
                    logger.info(f"Retrying payment verification for {payment.merchant_order_id} after {delay:.2f}s (attempt {attempt + 1})")
                    time.sleep(delay)
                
                # Check payment status
                result = self.payment_service.check_payment_status(payment.merchant_order_id)
                
                if result and result.get('success'):
                    return result
                else:
                    logger.warning(f"Payment check returned no success for {payment.merchant_order_id}: {result}")
                    
            except Exception as e:
                error_msg = str(e)
                if '429' in error_msg or 'Too Many Requests' in error_msg:
                    logger.warning(f"Rate limit hit for {payment.merchant_order_id}, attempt {attempt + 1}/{max_retries}")
                    if attempt == max_retries - 1:
                        logger.error(f"Max retries reached for {payment.merchant_order_id} due to rate limits")
                        return None
                    continue
                else:
                    logger.error(f"Error verifying payment {payment.merchant_order_id}: {error_msg}")
                    return None
        
        return None
    
    def check_and_complete_pending_payments(self):
        """Check and complete pending payments with improved rate limiting"""
        try:
            # Find INITIATED payments older than 2 minutes
            cutoff_time = timezone.now() - timedelta(minutes=2)
            pending_payments = PaymentOrder.objects.filter(
                status='INITIATED',
                created_at__lt=cutoff_time
            ).order_by('created_at')[:3]  # Limit to 3 payments per run to avoid rate limits
            
            total_payments = pending_payments.count()
            
            if total_payments == 0:
                return 0
                
            logger.info(f"📋 Found {total_payments} pending payments to check")
            completed_count = 0
            
            for i, payment in enumerate(pending_payments):
                logger.info(f"🔍 Checking payment {i+1}/{total_payments}: {payment.merchant_order_id}")
                
                # Add delay between API calls to avoid rate limits
                if i > 0:
                    delay = random.uniform(5, 8)  # Random delay between 5-8 seconds
                    logger.info(f"⏳ Rate limiting: waiting {delay:.2f}s before next check")
                    time.sleep(delay)
                
                # Verify payment with retry logic
                result = self.verify_payment_with_retry(payment)
                
                if result and result.get('success') and result.get('payment_order'):
                    updated_payment = result['payment_order']
                    
                    if updated_payment.status == 'SUCCESS':
                        logger.info(f"✅ Payment confirmed as SUCCESS: {payment.merchant_order_id}")
                        
                        # Check if booking already exists using cart object
                        try:
                            cart = Cart.objects.get(cart_id=payment.cart_id)
                            existing_booking = Booking.objects.filter(cart=cart).first()
                        except Cart.DoesNotExist:
                            logger.error(f"❌ Cart not found for payment {payment.merchant_order_id}: {payment.cart_id}")
                            continue
                        
                        if not existing_booking:
                            # Create booking automatically
                            try:
                                booking = self.webhook_service._create_booking_from_cart(updated_payment)
                                
                                if booking:
                                    logger.info(f"📋 Auto-created booking: {booking.book_id}")
                                    completed_count += 1
                                    
                                    # Send email notifications
                                    try:
                                        from core.tasks import send_booking_confirmation
                                        send_booking_confirmation.delay(booking.id)
                                        logger.info(f"📧 Email queued for booking: {booking.book_id}")
                                    except Exception as e:
                                        logger.warning(f"Failed to queue email: {e}")
                                else:
                                    logger.error(f"❌ Failed to create booking for payment: {payment.merchant_order_id}")
                            except Exception as booking_error:
                                logger.error(f"❌ Exception creating booking: {str(booking_error)}")
                        else:
                            logger.info(f"📋 Booking already exists: {existing_booking.book_id}")
                            completed_count += 1
                            
                    elif updated_payment.status in ['FAILED', 'CANCELLED']:
                        logger.info(f"❌ Payment failed/cancelled: {payment.merchant_order_id} - {updated_payment.status}")
                    else:
                        logger.info(f"⏳ Payment still pending: {payment.merchant_order_id} - {updated_payment.status}")
                else:
                    logger.warning(f"⚠️ Could not verify payment status: {payment.merchant_order_id}")
            
            logger.info(f"✅ Check completed. {completed_count} payments processed.")
            return completed_count
            
        except Exception as e:
            logger.error(f"❌ Error in check_and_complete_pending_payments: {str(e)}")
            return 0


class Command(BaseCommand):
    """Django management command for automatic payment completion"""
    
    help = 'Automatically check and complete pending payments'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--continuous',
            action='store_true',
            help='Run continuously with interval checks',
        )
        parser.add_argument(
            '--interval',
            type=int,
            default=120,  # Increased to 2 minutes to reduce API calls
            help='Interval in seconds for continuous mode (default: 120)',
        )
    
    def handle(self, *args, **options):
        auto_completer = PaymentAutoCompleter()
        
        if options['continuous']:
            interval = options['interval']
            logger.info(f"🚀 Starting continuous payment auto-completion (interval: {interval}s)")
            
            try:
                while True:
                    completed = auto_completer.check_and_complete_pending_payments()
                    
                    if completed > 0:
                        self.stdout.write(
                            self.style.SUCCESS(f'✅ Completed {completed} payments')
                        )
                    else:
                        self.stdout.write('✅ Check completed. 0 payments processed.')
                    
                    time.sleep(interval)
                    
            except KeyboardInterrupt:
                logger.info("🛑 Stopping continuous payment auto-completion")
                self.stdout.write(self.style.WARNING('Stopped by user'))
        else:
            # Single run
            completed = auto_completer.check_and_complete_pending_payments()
            
            if completed > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'✅ Single check completed. {completed} payments processed.')
                )
            else:
                self.stdout.write('✅ Single check completed. 0 payments processed.')
