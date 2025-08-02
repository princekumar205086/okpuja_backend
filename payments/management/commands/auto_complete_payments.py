"""
Automatic Payment Completion Service

This service automatically checks and completes INITIATED payments
that have been successful on PhonePe but haven't received webhooks.
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
    """
    Automatically check and complete pending payments
    """
    
    def __init__(self):
        self.payment_service = PaymentService()
        self.webhook_service = WebhookService()
    
    def check_and_complete_pending_payments(self):
        """
        Find all INITIATED payments older than 2 minutes and check their status
        """
        logger.info("🔄 Starting automatic payment completion check...")
        
        # Get payments that are INITIATED and older than 2 minutes
        cutoff_time = timezone.now() - timedelta(minutes=2)
        
        pending_payments = PaymentOrder.objects.filter(
            status='INITIATED',
            created_at__lt=cutoff_time
        ).order_by('-created_at')[:10]  # Check latest 10 only
        
        logger.info(f"📋 Found {pending_payments.count()} pending payments to check")
        
        completed_count = 0
        
        for payment in pending_payments:
            try:
                logger.info(f"🔍 Checking payment: {payment.merchant_order_id}")
                
                # Check with PhonePe for actual status
                result = self.payment_service.check_payment_status(payment.merchant_order_id)
                
                if result.get('success') and result.get('payment_order'):
                    updated_payment = result['payment_order']
                    
                    if updated_payment.status == 'SUCCESS':
                        logger.info(f"✅ Payment confirmed as SUCCESS: {payment.merchant_order_id}")
                        
                        # Check if booking already exists
                        existing_booking = Booking.objects.filter(cart_id=payment.cart_id).first()
                        
                        if not existing_booking:
                            # Create booking automatically
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
                                    logger.error(f"Failed to queue email: {e}")
                            else:
                                logger.error(f"❌ Failed to create booking for payment: {payment.merchant_order_id}")
                        else:
                            logger.info(f"📋 Booking already exists: {existing_booking.book_id}")
                            
                    elif updated_payment.status in ['FAILED', 'CANCELLED']:
                        logger.info(f"❌ Payment failed/cancelled: {payment.merchant_order_id} - {updated_payment.status}")
                    else:
                        logger.info(f"⏳ Payment still pending: {payment.merchant_order_id} - {updated_payment.status}")
                else:
                    logger.warning(f"⚠️ Could not verify payment status: {payment.merchant_order_id}")
                    
            except Exception as e:
                logger.error(f"❌ Error checking payment {payment.merchant_order_id}: {e}")
        
        logger.info(f"✅ Completed automatic payment check. {completed_count} payments completed.")
        return completed_count


class Command(BaseCommand):
    """
    Django management command to run payment auto-completion
    """
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
            default=60,
            help='Interval in seconds for continuous mode (default: 60)',
        )
    
    def handle(self, *args, **options):
        auto_completer = PaymentAutoCompleter()
        
        if options['continuous']:
            self.stdout.write(
                self.style.SUCCESS(f"🚀 Starting continuous payment auto-completion (interval: {options['interval']}s)")
            )
            
            while True:
                try:
                    completed = auto_completer.check_and_complete_pending_payments()
                    self.stdout.write(
                        self.style.SUCCESS(f"✅ Check completed. {completed} payments processed.")
                    )
                    time.sleep(options['interval'])
                except KeyboardInterrupt:
                    self.stdout.write(self.style.WARNING("🛑 Stopping continuous mode..."))
                    break
                except Exception as e:
                    self.stdout.write(self.style.ERROR(f"❌ Error in continuous mode: {e}"))
                    time.sleep(options['interval'])
        else:
            completed = auto_completer.check_and_complete_pending_payments()
            self.stdout.write(
                self.style.SUCCESS(f"✅ Single check completed. {completed} payments processed.")
            )
