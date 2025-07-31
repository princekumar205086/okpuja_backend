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
    
    def create_payment_order(self, user, amount, redirect_url, description=None, metadata=None):
        """
        Create a new payment order
        
        Args:
            user: Django User instance
            amount: Amount in paisa (₹1 = 100 paisa)
            redirect_url: URL to redirect after payment
            description: Optional payment description
            metadata: Optional metadata dict
        
        Returns:
            dict: Payment order creation result
        """
        try:
            # Generate unique merchant order ID
            merchant_order_id = f"OKPUJA_{uuid.uuid4().hex[:12].upper()}"
            
            # Create payment order in database
            payment_order = PaymentOrder.objects.create(
                merchant_order_id=merchant_order_id,
                user=user,
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
            merchant_order_id = webhook_data.get('merchantOrderId')
            
            if not merchant_order_id:
                return {
                    'success': False,
                    'error': 'No merchant order ID in webhook data'
                }
            
            # Get payment order
            payment_order = PaymentOrder.objects.get(merchant_order_id=merchant_order_id)
            
            # Process based on webhook event
            event_type = webhook_data.get('eventType', 'UNKNOWN')
            
            if event_type == 'PAYMENT_SUCCESS':
                payment_order.mark_success(
                    phonepe_transaction_id=webhook_data.get('transactionId'),
                    phonepe_response=webhook_data
                )
            elif event_type == 'PAYMENT_FAILED':
                payment_order.mark_failed(phonepe_response=webhook_data)
            
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
