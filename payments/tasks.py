"""
Background Payment Auto-Completion Tasks

These tasks automatically complete payments without frontend intervention.
"""

import logging
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
from .models import PaymentOrder
from .services import PaymentService, WebhookService
from booking.models import Booking

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def auto_complete_pending_payments(self):
    """
    Celery task to automatically check and complete pending payments
    Runs every 2 minutes to check for payments that need completion
    """
    try:
        logger.info("🔄 Auto-completion task started")
        
        # Get payments that are INITIATED and older than 3 minutes
        cutoff_time = timezone.now() - timedelta(minutes=3)
        
        pending_payments = PaymentOrder.objects.filter(
            status='INITIATED',
            created_at__lt=cutoff_time
        ).order_by('-created_at')[:5]  # Check latest 5 only
        
        if not pending_payments.exists():
            logger.info("📝 No pending payments found")
            return "No pending payments"
        
        logger.info(f"📋 Found {pending_payments.count()} pending payments")
        
        payment_service = PaymentService()
        webhook_service = WebhookService()
        completed_count = 0
        
        for payment in pending_payments:
            try:
                logger.info(f"🔍 Auto-checking: {payment.merchant_order_id}")
                
                # Check actual status with PhonePe
                result = payment_service.check_payment_status(payment.merchant_order_id)
                
                if result.get('success') and result.get('payment_order'):
                    updated_payment = result['payment_order']
                    
                    if updated_payment.status == 'SUCCESS':
                        # Check if booking already exists
                        existing_booking = Booking.objects.filter(cart_id=payment.cart_id).first()
                        
                        if not existing_booking:
                            # Auto-create booking
                            booking = webhook_service._create_booking_from_cart(updated_payment)
                            
                            if booking:
                                logger.info(f"✅ Auto-created booking: {booking.book_id}")
                                completed_count += 1
                                
                                # Send email notifications
                                try:
                                    from core.tasks import send_booking_confirmation
                                    send_booking_confirmation.delay(booking.id)
                                    logger.info(f"📧 Email queued: {booking.book_id}")
                                except Exception as e:
                                    logger.error(f"Email error: {e}")
                            else:
                                logger.error(f"❌ Booking creation failed: {payment.merchant_order_id}")
                        else:
                            logger.info(f"📋 Booking exists: {existing_booking.book_id}")
                            
                    elif updated_payment.status in ['FAILED', 'CANCELLED']:
                        logger.info(f"❌ Payment {updated_payment.status}: {payment.merchant_order_id}")
                    else:
                        logger.info(f"⏳ Still {updated_payment.status}: {payment.merchant_order_id}")
                        
            except Exception as e:
                logger.error(f"❌ Error checking {payment.merchant_order_id}: {e}")
        
        result_message = f"Auto-completion completed: {completed_count} payments processed"
        logger.info(f"✅ {result_message}")
        return result_message
        
    except Exception as e:
        logger.error(f"❌ Auto-completion task failed: {e}")
        raise self.retry(countdown=60, exc=e)


@shared_task
def check_single_payment(merchant_order_id):
    """
    Check and complete a single payment immediately
    Used for real-time completion after payment creation
    """
    try:
        logger.info(f"🔍 Single payment check: {merchant_order_id}")
        
        payment = PaymentOrder.objects.filter(merchant_order_id=merchant_order_id).first()
        if not payment:
            logger.error(f"❌ Payment not found: {merchant_order_id}")
            return "Payment not found"
        
        if payment.status != 'INITIATED':
            logger.info(f"📝 Payment already processed: {payment.status}")
            return f"Already {payment.status}"
        
        # Check with PhonePe
        payment_service = PaymentService()
        result = payment_service.check_payment_status(merchant_order_id)
        
        if result.get('success') and result.get('payment_order'):
            updated_payment = result['payment_order']
            
            if updated_payment.status == 'SUCCESS':
                # Check if booking exists
                existing_booking = Booking.objects.filter(cart_id=payment.cart_id).first()
                
                if not existing_booking:
                    # Create booking
                    webhook_service = WebhookService()
                    booking = webhook_service._create_booking_from_cart(updated_payment)
                    
                    if booking:
                        logger.info(f"✅ Single payment completed: {booking.book_id}")
                        
                        # Send email
                        try:
                            from core.tasks import send_booking_confirmation
                            send_booking_confirmation.delay(booking.id)
                        except Exception as e:
                            logger.error(f"Email error: {e}")
                        
                        return f"Booking created: {booking.book_id}"
                    else:
                        logger.error(f"❌ Booking creation failed")
                        return "Booking creation failed"
                else:
                    logger.info(f"📋 Booking already exists: {existing_booking.book_id}")
                    return f"Booking exists: {existing_booking.book_id}"
            else:
                logger.info(f"⏳ Payment status: {updated_payment.status}")
                return f"Payment {updated_payment.status}"
        else:
            logger.warning(f"⚠️ Could not verify payment")
            return "Verification failed"
            
    except Exception as e:
        logger.error(f"❌ Single payment check failed: {e}")
        return f"Error: {str(e)}"
