"""
Payment Services
Clean business logic layer
"""

import uuid
import logging
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from django.db import models
from .models import PaymentOrder, PaymentRefund
from .phonepe_client import PhonePePaymentClient

logger = logging.getLogger(__name__)


class PaymentService:
    """Clean Payment Service Class"""
    
    def __init__(self, environment=None):
        """Initialize payment service"""
        # Get environment from settings, default to UAT
        env_setting = getattr(settings, 'PHONEPE_ENV', 'uat').lower()
        self.environment = environment or env_setting
        
        # Ensure environment is properly formatted
        if self.environment.upper() == 'PRODUCTION':
            self.environment = 'production'
        else:
            self.environment = 'uat'
            
        self.client = PhonePePaymentClient(environment=self.environment)
        logger.info(f"PaymentService initialized with environment: {self.environment}")
    
    def create_payment_order(self, user, amount, redirect_url, description=None, metadata=None, cart_id=None, address_id=None):
        """
        Create a new payment order
        
        Args:
            user: Django User instance
            amount: Amount in paisa (₹1 = 100 paisa)
            redirect_url: URL to redirect after payment
            description: Optional payment description
            metadata: Optional metadata dict
            cart_id: Optional cart ID for cart-based payments
            address_id: Optional address ID for delivery/service
        
        Returns:
            dict: Payment order creation result
        """
        try:
            # Generate unique merchant order ID
            if cart_id:
                merchant_order_id = f"CART_{cart_id}_{uuid.uuid4().hex[:8].upper()}"
            else:
                merchant_order_id = f"OKPUJA_{uuid.uuid4().hex[:12].upper()}"
            
            # Create payment order in database
            payment_order = PaymentOrder.objects.create(
                merchant_order_id=merchant_order_id,
                user=user,
                cart_id=cart_id,
                address_id=address_id,  
                amount=amount,
                description=description or f"Payment for ₹{amount/100}",
                redirect_url=redirect_url,
                metadata=metadata or {},
                expires_at=timezone.now() + timedelta(minutes=20)  # 20 minute expiry
            )
            
            # Create payment URL with PhonePe
            payment_result = self.client.create_payment_url(
                merchant_order_id=merchant_order_id,
                amount=amount,
                redirect_url=redirect_url,
                payment_message=description
            )
            
            if payment_result['success']:
                # Update payment order with PhonePe URL
                payment_order.phonepe_payment_url = payment_result['payment_url']
                payment_order.status = 'INITIATED'
                payment_order.phonepe_response = payment_result['data']
                payment_order.save()
                
                logger.info(f"Payment order created successfully: {merchant_order_id}")
                
                return {
                    'success': True,
                    'payment_order': payment_order,
                    'payment_url': payment_result['payment_url'],
                    'merchant_order_id': merchant_order_id
                }
            else:
                # Mark as failed
                payment_order.status = 'FAILED'
                payment_order.save()
                
                logger.error(f"Failed to create PhonePe payment URL: {payment_result['error']}")
                
                return {
                    'success': False,
                    'error': payment_result['error'],
                    'payment_order': payment_order
                }
                
        except Exception as e:
            logger.error(f"Payment order creation failed: {e}")
            return {
                'success': False,
                'error': f"Failed to create payment order: {str(e)}"
            }
    
    def check_payment_status(self, merchant_order_id):
        """
        Check payment status with PhonePe and update local record
        
        Args:
            merchant_order_id: Order ID to check
        
        Returns:
            dict: Payment status result
        """
        try:
            # Get payment order from database
            payment_order = PaymentOrder.objects.get(merchant_order_id=merchant_order_id)
            
            # Check status with PhonePe
            status_result = self.client.check_payment_status(merchant_order_id)
            
            if status_result['success']:
                # Extract status from PhonePe response
                phonepe_data = status_result['data']
                
                # Update payment order based on PhonePe response
                # PhonePe returns 'state' field, not 'status'
                payment_state = phonepe_data.get('state', '').upper()
                
                if payment_state == 'COMPLETED':
                    payment_order.mark_success(
                        phonepe_transaction_id=phonepe_data.get('transactionId'),
                        phonepe_response=phonepe_data
                    )
                        
                elif payment_state in ['FAILED', 'CANCELLED']:
                    payment_order.mark_failed(phonepe_response=phonepe_data)
                
                logger.info(f"Payment status updated: {merchant_order_id} - {payment_order.status}")
                
                return {
                    'success': True,
                    'payment_order': payment_order,
                    'phonepe_data': phonepe_data
                }
            else:
                logger.error(f"Failed to check payment status: {status_result['error']}")
                return {
                    'success': False,
                    'error': status_result['error'],
                    'payment_order': payment_order
                }
                
        except PaymentOrder.DoesNotExist:
            logger.error(f"Payment order not found: {merchant_order_id}")
            return {
                'success': False,
                'error': 'Payment order not found'
            }
        except Exception as e:
            logger.error(f"Payment status check failed: {e}")
            return {
                'success': False,
                'error': f"Failed to check payment status: {str(e)}"
            }
    
    def create_refund(self, payment_order, amount, reason=None):
        """
        Create a refund for a payment order
        
        Args:
            payment_order: PaymentOrder instance
            amount: Refund amount in paisa
            reason: Optional refund reason
        
        Returns:
            dict: Refund creation result
        """
        try:
            # Validate refund eligibility
            if payment_order.status != 'SUCCESS':
                return {
                    'success': False,
                    'error': 'Can only refund successful payments'
                }
            
            if amount > payment_order.amount:
                return {
                    'success': False,
                    'error': 'Refund amount cannot exceed payment amount'
                }
            
            # Generate unique refund ID
            merchant_refund_id = f"REFUND_{uuid.uuid4().hex[:12].upper()}"
            
            # Create refund record
            refund = PaymentRefund.objects.create(
                merchant_refund_id=merchant_refund_id,
                payment_order=payment_order,
                amount=amount,
                reason=reason or 'Customer requested refund'
            )
            
            # Create refund with PhonePe
            refund_result = self.client.create_refund(
                merchant_refund_id=merchant_refund_id,
                original_merchant_order_id=payment_order.merchant_order_id,
                amount=amount
            )
            
            if refund_result['success']:
                refund.status = 'PROCESSING'
                refund.phonepe_response = refund_result['data']
                refund.save()
                
                logger.info(f"Refund created successfully: {merchant_refund_id}")
                
                return {
                    'success': True,
                    'refund': refund,
                    'phonepe_data': refund_result['data']
                }
            else:
                refund.mark_failed(phonepe_response={'error': refund_result['error']})
                
                logger.error(f"Failed to create PhonePe refund: {refund_result['error']}")
                
                return {
                    'success': False,
                    'error': refund_result['error'],
                    'refund': refund
                }
                
        except Exception as e:
            logger.error(f"Refund creation failed: {e}")
            return {
                'success': False,
                'error': f"Failed to create refund: {str(e)}"
            }
    
    def check_refund_status(self, merchant_refund_id):
        """
        Check refund status with PhonePe
        
        Args:
            merchant_refund_id: Refund ID to check
        
        Returns:
            dict: Refund status result
        """
        try:
            # Get refund from database
            refund = PaymentRefund.objects.get(merchant_refund_id=merchant_refund_id)
            
            # Check status with PhonePe
            status_result = self.client.check_refund_status(merchant_refund_id)
            
            if status_result['success']:
                phonepe_data = status_result['data']
                
                # Update refund status based on PhonePe response
                if phonepe_data.get('status') == 'SUCCESS':
                    refund.mark_success(
                        phonepe_refund_id=phonepe_data.get('refundId'),
                        phonepe_response=phonepe_data
                    )
                elif phonepe_data.get('status') == 'FAILED':
                    refund.mark_failed(phonepe_response=phonepe_data)
                
                logger.info(f"Refund status updated: {merchant_refund_id} - {refund.status}")
                
                return {
                    'success': True,
                    'refund': refund,
                    'phonepe_data': phonepe_data
                }
            else:
                logger.error(f"Failed to check refund status: {status_result['error']}")
                return {
                    'success': False,
                    'error': status_result['error'],
                    'refund': refund
                }
                
        except PaymentRefund.DoesNotExist:
            logger.error(f"Refund not found: {merchant_refund_id}")
            return {
                'success': False,
                'error': 'Refund not found'
            }
        except Exception as e:
            logger.error(f"Refund status check failed: {e}")
            return {
                'success': False,
                'error': f"Failed to check refund status: {str(e)}"
            }


class WebhookService:
    """Webhook processing service"""
    
    def process_payment_webhook(self, webhook_data, headers=None):
        """
        Process payment webhook from PhonePe V2
        
        According to PhonePe V2 docs, webhook payload structure:
        {
            "event": "checkout.order.completed",
            "payload": {
                "orderId": "OMO2403282020198641071317",
                "merchantId": "merchantId",
                "merchantOrderId": "merchantOrderId", 
                "state": "COMPLETED",
                "amount": 10000,
                ...
            }
        }
        
        Args:
            webhook_data: Webhook payload
            headers: Request headers
        
        Returns:
            dict: Processing result
        """
        try:
            # Log webhook data for debugging
            logger.info(f"PhonePe V2 webhook received: {webhook_data}")
            
            # Extract event and payload according to V2 structure
            event = webhook_data.get('event')
            payload = webhook_data.get('payload', {})
            
            # Get merchant order ID from payload
            merchant_order_id = payload.get('merchantOrderId')
            
            if not merchant_order_id:
                # Fallback for old webhook format
                merchant_order_id = webhook_data.get('merchantOrderId')
                
            if not merchant_order_id:
                logger.error("No merchant order ID found in webhook payload")
                return {
                    'success': False,
                    'error': 'No merchant order ID in webhook data'
                }
            
            # Get payment order
            try:
                payment_order = PaymentOrder.objects.get(merchant_order_id=merchant_order_id)
            except PaymentOrder.DoesNotExist:
                logger.error(f"Payment order not found for webhook: {merchant_order_id}")
                return {
                    'success': False,
                    'error': 'Payment order not found'
                }
            
            # Process based on V2 webhook event type and payload state
            payment_state = payload.get('state', '').upper()
            event_type = event or 'UNKNOWN'
            
            logger.info(f"Processing webhook - Event: {event_type}, State: {payment_state}, Order: {merchant_order_id}")
            
            # Handle checkout.order.completed
            if event_type == 'checkout.order.completed' and payment_state == 'COMPLETED':
                # Extract transaction details
                transaction_id = None
                payment_details = payload.get('paymentDetails', [])
                if payment_details:
                    transaction_id = payment_details[0].get('transactionId')
                
                # Mark payment as successful
                payment_order.mark_success(
                    phonepe_transaction_id=transaction_id or payload.get('orderId'),
                    phonepe_response=webhook_data
                )
                
                # Auto-create booking if cart_id is present
                if payment_order.cart_id:
                    booking = self._create_booking_from_cart(payment_order)
                    if booking:
                        logger.info(f"Booking created via webhook: {booking.book_id}")
                        
                        # Send email notifications
                        try:
                            from core.tasks import send_booking_confirmation
                            send_booking_confirmation.delay(booking.id)
                            logger.info(f"Email notification queued for booking {booking.book_id}")
                        except Exception as e:
                            logger.error(f"Failed to queue email notification: {e}")
                    else:
                        logger.error("Failed to create booking from cart")
                
                # Handle astrology booking confirmation
                elif payment_order.metadata.get('booking_type') == 'astrology':
                    success = self._confirm_astrology_booking(payment_order)
                    if success:
                        logger.info(f"Astrology booking confirmed via webhook: {payment_order.metadata.get('booking_id')}")
                    else:
                        logger.error(f"Failed to confirm astrology booking: {payment_order.metadata.get('booking_id')}")
                        
            # Handle checkout.order.failed
            elif event_type == 'checkout.order.failed' and payment_state == 'FAILED':
                error_details = payload.get('paymentDetails', [])
                error_info = {}
                if error_details:
                    error_info = {
                        'errorCode': error_details[0].get('errorCode'),
                        'detailedErrorCode': error_details[0].get('detailedErrorCode')
                    }
                
                # Mark payment as failed
                payment_order.mark_failed(phonepe_response=webhook_data)
                logger.info(f"Payment marked as failed: {merchant_order_id} - {error_info}")
                
            else:
                # Log unknown or unhandled webhook events
                logger.warning(f"Unhandled webhook event: {event_type} with state: {payment_state} for order {merchant_order_id}")
                # Still return success to avoid PhonePe retries for unknown events
            
            logger.info(f"Webhook processed successfully: {merchant_order_id} - {event_type}")
            
            return {
                'success': True,
                'payment_order': payment_order,
                'event_type': event_type,
                'state': payment_state
            }
            
        except Exception as e:
            logger.error(f"Webhook processing failed: {e}")
            return {
                'success': False,
                'error': f"Webhook processing failed: {str(e)}"
            }
    
    def _create_booking_from_cart(self, payment_order):
        """Create booking from cart after successful payment"""
        try:
            from cart.models import Cart
            from booking.models import Booking
            from accounts.models import Address
            from datetime import datetime
            
            # Get cart
            cart = Cart.objects.get(cart_id=payment_order.cart_id)
            
            # Parse time from various formats
            selected_time = None
            time_str = cart.selected_time
            
            # Try different time formats
            time_formats = [
                "%I:%M %p",     # 12-hour format with AM/PM (e.g., "01:00 AM")
                "%H:%M",        # 24-hour format (e.g., "01:00")
                "%I:%M%p",      # 12-hour format without space (e.g., "01:00AM")
                "%H:%M:%S",     # 24-hour format with seconds (e.g., "01:00:00")
            ]
            
            for fmt in time_formats:
                try:
                    parsed_time = datetime.strptime(time_str, fmt)
                    selected_time = parsed_time.time()
                    break
                except ValueError:
                    continue
            
            if not selected_time:
                # If all parsing fails, create a default time
                logger.warning(f"Could not parse time '{time_str}', using default 09:00")
                selected_time = datetime.strptime("09:00", "%H:%M").time()
            
            # Get user's default address or use None
            address = None
            try:
                address = Address.objects.filter(user=payment_order.user, is_default=True).first()
                if not address:
                    # If no default address, get any address for this user
                    address = Address.objects.filter(user=payment_order.user).first()
            except Exception as e:
                logger.warning(f"Could not get address for user {payment_order.user.id}: {e}")
            
            # Convert cart to booking
            booking = Booking.objects.create(
                user=payment_order.user,
                cart=cart,
                payment_order_id=payment_order.merchant_order_id,  # Link payment to booking
                selected_date=cart.selected_date,
                selected_time=selected_time,
                address=address,  # Can be None
                status='CONFIRMED'  # Use string value directly
            )
            
            # Mark cart as converted
            cart.status = Cart.StatusChoices.CONVERTED
            cart.save()
            
            logger.info(f"Booking created from cart {cart.cart_id}: {booking.book_id}")
            
            # Auto-cleanup old converted carts to keep database clean
            try:
                self._cleanup_old_carts(payment_order.user)
            except Exception as e:
                logger.warning(f"Failed to cleanup old carts: {e}")
            
            # Send booking confirmation email (trigger Celery task)
            try:
                from core.tasks import send_booking_confirmation
                send_booking_confirmation.delay(booking.id)  # Use booking.id not book_id
                logger.info(f"Booking confirmation email queued for {booking.book_id}")
            except Exception as e:
                logger.error(f"Failed to queue booking confirmation email: {e}")
            
            return booking
            
        except Exception as e:
            logger.error(f"Failed to create booking from cart {payment_order.cart_id}: {e}")
            return None
    
    def _cleanup_old_carts(self, user):
        """Clean up old converted carts, keeping only the latest 3"""
        from cart.models import Cart
        from booking.models import Booking
        from django.db import connection, transaction
        
        # Find all converted carts for this user
        converted_carts = Cart.objects.filter(
            user=user, 
            status=Cart.StatusChoices.CONVERTED
        ).order_by('-created_at')
        
        # Keep only the latest 3, mark older ones for cleanup
        carts_to_keep = converted_carts[:3]
        carts_to_cleanup = converted_carts[3:]
        
        for cart in carts_to_cleanup:
            try:
                with transaction.atomic():
                    # Before deleting cart, set booking cart reference to NULL
                    bookings = Booking.objects.filter(cart=cart)
                    for booking in bookings:
                        booking.cart = None
                        booking.save()
                    
                    # Handle payment order references
                    from .models import PaymentOrder
                    payments = PaymentOrder.objects.filter(cart_id=cart.cart_id)
                    for payment in payments:
                        payment.cart_id = None
                        payment.save()
                    
                    # Use raw SQL to safely delete cart with foreign key constraint handling
                    cursor = connection.cursor()
                    try:
                        # Temporarily disable foreign key constraints for this delete
                        cursor.execute("PRAGMA foreign_keys = OFF")
                        cart.delete()
                        cursor.execute("PRAGMA foreign_keys = ON")
                        logger.info(f"Cleaned up old cart: {cart.cart_id}")
                    except Exception as sql_error:
                        # Re-enable foreign keys even if delete failed
                        cursor.execute("PRAGMA foreign_keys = ON")
                        raise sql_error
                
            except Exception as e:
                logger.warning(f"Failed to cleanup cart {cart.cart_id}: {e}")
        
        if carts_to_cleanup:
            logger.info(f"Cart cleanup complete: removed {len(carts_to_cleanup)} old carts")

    def _confirm_astrology_booking(self, payment_order):
        """Confirm astrology booking after successful payment"""
        try:
            booking_id = payment_order.metadata.get('booking_id')
            if not booking_id:
                logger.error("No booking_id found in payment metadata")
                return False
            
            # Import here to avoid circular imports
            from astrology.models import AstrologyBooking
            
            # Get the booking
            try:
                booking = AstrologyBooking.objects.get(id=booking_id)
            except AstrologyBooking.DoesNotExist:
                logger.error(f"Astrology booking not found: {booking_id}")
                return False
            
            # Update booking status to CONFIRMED
            booking.status = 'CONFIRMED'
            
            # Update booking metadata with payment details
            booking.metadata.update({
                'payment_confirmed': True,
                'payment_order_id': str(payment_order.id),
                'merchant_order_id': payment_order.merchant_order_id,
                'payment_amount': payment_order.amount,
                'payment_completed_at': payment_order.completed_at.isoformat() if payment_order.completed_at else None,
                'phonepe_transaction_id': payment_order.phonepe_transaction_id
            })
            
            booking.save()
            
            logger.info(f"Astrology booking {booking_id} confirmed successfully after payment")
            
            # Send confirmation email to customer
            try:
                booking.send_booking_confirmation()
                logger.info(f"Confirmation email sent for astrology booking {booking_id}")
            except Exception as e:
                logger.error(f"Failed to send confirmation email for astrology booking {booking_id}: {e}")
            
            # Send notification to admin
            try:
                self._send_admin_notification_astrology(booking)
                logger.info(f"Admin notification sent for astrology booking {booking_id}")
            except Exception as e:
                logger.error(f"Failed to send admin notification for astrology booking {booking_id}: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to confirm astrology booking: {e}")
            return False

    def _send_admin_notification_astrology(self, booking):
        """Send admin notification for new astrology booking"""
        try:
            from django.contrib.auth import get_user_model
            from django.core.mail import send_mail
            from django.conf import settings
            
            User = get_user_model()
            
            # Get admin users
            admin_users = User.objects.filter(
                models.Q(is_staff=True) | models.Q(role='ADMIN'),
                is_active=True,
                email__isnull=False
            ).exclude(email='')
            
            admin_emails = [admin.email for admin in admin_users]
            
            if admin_emails:
                subject = f"🔮 New Astrology Booking - #{booking.id} - {booking.service.title}"
                
                message = f"""
📋 NEW ASTROLOGY BOOKING RECEIVED

Booking Details:
• Booking ID: #{booking.id}
• Service: {booking.service.title}
• Amount: ₹{booking.service.price}
• Status: {booking.get_status_display()}
• Duration: {booking.service.duration_minutes} minutes

Customer Information:
• Name: Customer (via {booking.contact_email})
• Email: {booking.contact_email}
• Phone: {booking.contact_phone}

Session Details:
• Preferred Date: {booking.preferred_date.strftime('%B %d, %Y')}
• Preferred Time: {booking.preferred_time.strftime('%I:%M %p')}
• Language: {booking.language}

Birth Information:
• Birth Place: {booking.birth_place}
• Birth Date: {booking.birth_date.strftime('%B %d, %Y')}
• Birth Time: {booking.birth_time.strftime('%I:%M %p')}
• Gender: {booking.get_gender_display()}

Customer Questions:
{booking.questions if booking.questions else 'No specific questions provided.'}

Payment Information:
• Payment Status: Confirmed ✅
• Amount Paid: ₹{booking.service.price}
• Payment Method: PhonePe

Next Steps:
1. Review customer's birth details and questions
2. Prepare consultation materials
3. Contact customer before the session
4. Ensure you're available at the scheduled time

Admin Panel: http://localhost:8000/admin/astrology/astrologybooking/{booking.id}/

---
This is an automated notification from OKPUJA Astrology System.
                """
                
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    admin_emails,
                    fail_silently=False,
                )
                
                logger.info(f"Admin notification sent to {len(admin_emails)} administrators")
            else:
                logger.warning("No admin email addresses found for astrology booking notification")
                
        except Exception as e:
            logger.error(f"Failed to send admin notification: {e}")
            raise
