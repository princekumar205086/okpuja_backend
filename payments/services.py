"""
Payment Services
Clean business logic layer
"""

import uuid
import logging
from datetime import timedelta
from django.utils import timezone
from django.conf import settings
from .models import PaymentOrder, PaymentRefund
from .phonepe_client import PhonePePaymentClient

logger = logging.getLogger(__name__)


class PaymentService:
    """Clean Payment Service Class"""
    
    def __init__(self, environment=None):
        """Initialize payment service"""
        self.environment = environment or getattr(settings, 'PHONEPE_ENV', 'uat').lower()
        self.client = PhonePePaymentClient(environment=self.environment)
    
    def create_payment_order(self, user, amount, redirect_url, description=None, metadata=None, cart_id=None):
        """
        Create a new payment order
        
        Args:
            user: Django User instance
            amount: Amount in paisa (₹1 = 100 paisa)
            redirect_url: URL to redirect after payment
            description: Optional payment description
            metadata: Optional metadata dict
            cart_id: Optional cart ID for cart-based payments
        
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
                # Note: Actual status mapping depends on PhonePe response format
                if phonepe_data.get('status') == 'SUCCESS':
                    payment_order.mark_success(
                        phonepe_transaction_id=phonepe_data.get('transactionId'),
                        phonepe_response=phonepe_data
                    )
                    
                    # Auto-create booking if cart_id is present and payment just became successful
                    if payment_order.cart_id and payment_order.status == 'SUCCESS':
                        self._create_booking_from_cart(payment_order)
                        
                elif phonepe_data.get('status') in ['FAILED', 'CANCELLED']:
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
        Process payment webhook from PhonePe
        
        Args:
            webhook_data: Webhook payload
            headers: Request headers
        
        Returns:
            dict: Processing result
        """
        try:
            # Log webhook data for debugging
            logger.info(f"Webhook received: {webhook_data}")
            
            merchant_order_id = webhook_data.get('merchantOrderId')
            
            if not merchant_order_id:
                return {
                    'success': False,
                    'error': 'No merchant order ID in webhook data'
                }
            
            # Get payment order
            payment_order = PaymentOrder.objects.get(merchant_order_id=merchant_order_id)
            
            # Process based on webhook event - check multiple possible field names
            event_type = (
                webhook_data.get('eventType') or 
                webhook_data.get('state') or 
                webhook_data.get('status') or
                webhook_data.get('responseCode') or
                'UNKNOWN'
            )
            
            # Map different status values to our internal statuses
            success_statuses = ['PAYMENT_SUCCESS', 'SUCCESS', 'COMPLETED', 'PAID']
            failed_statuses = ['PAYMENT_FAILED', 'FAILED', 'CANCELLED', 'EXPIRED']
            
            if event_type in success_statuses or webhook_data.get('state') == 'COMPLETED':
                payment_order.mark_success(
                    phonepe_transaction_id=webhook_data.get('transactionId'),
                    phonepe_response=webhook_data
                )
                
                # Auto-create booking if cart_id is present
                if payment_order.cart_id:
                    booking = self._create_booking_from_cart(payment_order)
                    logger.info(f"Booking created via webhook: {booking.book_id if booking else 'FAILED'}")
                    
            elif event_type in failed_statuses:
                payment_order.mark_failed(phonepe_response=webhook_data)
            else:
                # Log unknown status for debugging
                logger.warning(f"Unknown webhook status: {event_type} for order {merchant_order_id}")
            
            logger.info(f"Webhook processed: {merchant_order_id} - {event_type}")
            
            return {
                'success': True,
                'payment_order': payment_order,
                'event_type': event_type
            }
            
        except PaymentOrder.DoesNotExist:
            logger.error(f"Payment order not found for webhook: {merchant_order_id}")
            return {
                'success': False,
                'error': 'Payment order not found'
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
                # Before deleting cart, set booking cart reference to NULL
                bookings = Booking.objects.filter(cart=cart)
                for booking in bookings:
                    booking.cart = None
                    booking.save()
                
                # Now delete the cart safely
                cart.delete()
                logger.info(f"Cleaned up old cart: {cart.cart_id}")
                
            except Exception as e:
                logger.warning(f"Failed to cleanup cart {cart.cart_id}: {e}")
        
        if carts_to_cleanup:
            logger.info(f"Cart cleanup complete: removed {len(carts_to_cleanup)} old carts")
