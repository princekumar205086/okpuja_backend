"""
Payment Service Layer for PhonePe V2 Integration
Handles the complete payment flow from cart to booking
✅ Updated to use the corrected PhonePe V2 client
"""
import logging
from django.db import transaction
from django.conf import settings
from django.utils import timezone
from .models import Payment, PaymentStatus, PaymentMethod, Refund
from .phonepe_v2_corrected import PhonePeV2ClientCorrected, PhonePeV2Exception
from cart.models import Cart

logger = logging.getLogger(__name__)

class PaymentService:
    """Service class for handling payment operations"""
    
    def __init__(self):
        self.phonepe_client = PhonePeV2ClientCorrected(env=getattr(settings, 'PHONEPE_ENV', 'sandbox').lower())
    
    def create_payment_from_cart(self, cart, user):
        """
        Create payment from cart
        
        Args:
            cart: Cart instance
            user: User instance
            
        Returns:
            Payment: Created payment instance
        """
        with transaction.atomic():
            # Calculate total amount from cart
            total_amount = cart.total_price
            
            if total_amount <= 0:
                raise ValueError("Invalid cart total")
            
            # Create payment record
            payment = Payment.objects.create(
                user=user,
                cart=cart,
                amount=total_amount,
                currency='INR',
                method=PaymentMethod.PHONEPE,
                status=PaymentStatus.PENDING
            )
            
            logger.info(f"Created payment {payment.id} for cart {cart.id}")
            return payment
    
    def initiate_payment(self, payment):
        """
        Initiate payment with PhonePe V2 (Corrected Implementation)
        
        Args:
            payment: Payment instance
            
        Returns:
            dict: Payment initiation response
        """
        try:
            logger.info(f"Initiating payment {payment.id} with PhonePe V2")
            
            # ✅ Use corrected V2 client to initiate payment
            response = self.phonepe_client.initiate_payment(
                merchant_transaction_id=payment.merchant_transaction_id,
                amount=payment.amount,
                merchant_user_id=str(payment.user.id),
                redirect_url=f"{settings.FRONTEND_URL}/payment/callback/",
                callback_url=f"{settings.BACKEND_URL}/api/payment/webhook/phonepe/v2/"
            )
            
            if response.get('success'):
                # Update payment with gateway response
                payment.gateway_response = response.get('data', {})
                payment.save()
                
                logger.info(f"Payment {payment.id} initiated successfully")
                return response
            else:
                raise PhonePeV2Exception(f"Payment initiation failed: {response.get('error')}")
                
        except PhonePeV2Exception as e:
            logger.error(f"PhonePe error for payment {payment.id}: {str(e)}")
            payment.status = PaymentStatus.FAILED
            payment.save()
            raise
        except Exception as e:
            logger.error(f"Payment initiation error for payment {payment.id}: {str(e)}")
            payment.status = PaymentStatus.FAILED
            payment.save()
            raise PhonePeV2Exception(f"Payment initiation failed: {str(e)}")
    
    def verify_payment(self, merchant_transaction_id):
        """
        Verify payment status with PhonePe V2 (Corrected Implementation)
        
        Args:
            merchant_transaction_id: Merchant transaction ID
            
        Returns:
            dict: Payment verification response
        """
        try:
            logger.info(f"Verifying payment: {merchant_transaction_id}")
            
            # Get payment from database
            payment = Payment.objects.get(merchant_transaction_id=merchant_transaction_id)
            
            # ✅ Check status with corrected V2 client
            response = self.phonepe_client.check_payment_status(merchant_transaction_id)
            
            if response.get('success'):
                # Update payment status based on response
                self._update_payment_status(payment, response.get('data', {}))
                
                # Create booking if payment is successful
                if payment.status == PaymentStatus.SUCCESS and not hasattr(payment, 'booking'):
                    self._create_booking_from_payment(payment)
                
                return response
            else:
                logger.error(f"Payment verification failed: {response.get('error')}")
                return response
                
        except Payment.DoesNotExist:
            logger.error(f"Payment not found: {merchant_transaction_id}")
            return {
                'success': False,
                'error': 'Payment not found'
            }
        except Exception as e:
            logger.error(f"Payment verification error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def process_webhook(self, webhook_data):
        """
        Process PhonePe V2 webhook (Legacy method - use webhook_handler_v2.py for new implementation)
        
        Args:
            webhook_data: Webhook payload
            
        Returns:
            dict: Processing result
        """
        try:
            logger.info("Processing PhonePe V2 webhook (legacy method)")
            
            # ✅ Process webhook with corrected V2 client
            response = self.phonepe_client.process_webhook_payload(webhook_data)
            
            if response.get('valid'):
                # Extract merchant transaction ID
                merchant_transaction_id = response.get('merchant_order_id')
                
                if merchant_transaction_id:
                    # Get payment and update status
                    payment = Payment.objects.get(merchant_transaction_id=merchant_transaction_id)
                    
                    # Update status based on webhook state
                    state = response.get('state')
                    if state == 'COMPLETED':
                        payment.status = PaymentStatus.SUCCESS
                        payment.phonepe_order_id = response.get('order_id')
                    elif state == 'FAILED':
                        payment.status = PaymentStatus.FAILED
                    
                    payment.save()
                    
                    # Create booking if payment successful
                    if payment.status == PaymentStatus.SUCCESS and not hasattr(payment, 'booking'):
                        self._create_booking_from_payment(payment)
                    
                    return {
                        'success': True,
                        'payment_id': payment.id,
                        'status': payment.status
                    }
                else:
                    logger.error("No merchant transaction ID in webhook")
                    return {
                        'success': False,
                        'error': 'No merchant transaction ID'
                    }
            else:
                logger.error(f"Webhook processing failed: {response.get('error')}")
                return {
                    'success': False,
                    'error': response.get('error', 'Invalid webhook')
                }
                
        except Payment.DoesNotExist:
            logger.error("Payment not found for webhook")
            return {
                'success': False,
                'error': 'Payment not found'
            }
        except Exception as e:
            logger.error(f"Webhook processing error: {str(e)}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _update_payment_status(self, payment, response_data):
        """Update payment status based on V2 gateway response"""
        old_status = payment.status
        
        # ✅ Extract status from V2 response format
        state = response_data.get('state')
        
        # Map PhonePe V2 state to our status
        if state == 'COMPLETED':
            payment.status = PaymentStatus.SUCCESS
            payment.phonepe_order_id = response_data.get('orderId')
        elif state == 'FAILED':
            payment.status = PaymentStatus.FAILED
        elif state == 'PENDING':
            payment.status = PaymentStatus.PENDING
        
        # Update gateway response
        payment.gateway_response = payment.gateway_response or {}
        payment.gateway_response.update({
            'latest_response': response_data,
            'status_updated_at': str(timezone.now())
        })
        
        payment.save()
        
        logger.info(f"Payment {payment.id} status updated: {old_status} -> {payment.status}")
    
    def _create_booking_from_payment(self, payment):
        """Create booking from successful payment"""
        try:
            from booking.models import Booking
            
            with transaction.atomic():
                # Get cart details
                cart = payment.cart
                if not cart:
                    logger.error(f"No cart found for payment {payment.id}")
                    return None
                
                # Create booking
                booking = Booking.objects.create(
                    user=payment.user,
                    cart=cart,
                    selected_date=cart.selected_date,
                    selected_time=cart.selected_time
                )
                
                # Link payment to booking
                payment.booking = booking
                payment.save()
                
                # Deactivate cart
                cart.status = 'CONVERTED'
                cart.save()
                
                logger.info(f"Created booking {booking.id} from payment {payment.id}")
                return booking
                
        except Exception as e:
            logger.error(f"Booking creation failed for payment {payment.id}: {str(e)}")
            return None
    
    def initiate_refund(self, payment, amount=None, reason=None):
        """
        Initiate refund for a payment using PhonePe V2 (Corrected Implementation)
        
        Args:
            payment: Payment instance
            amount: Refund amount (None for full refund)
            reason: Refund reason
            
        Returns:
            dict: Refund response
        """
        try:
            if payment.status != PaymentStatus.SUCCESS:
                raise ValueError("Cannot refund non-completed payment")
            
            refund_amount = amount or payment.amount
            
            if refund_amount > payment.amount:
                raise ValueError("Refund amount cannot exceed payment amount")
            
            # Create refund record
            refund = Refund.objects.create(
                payment=payment,
                amount=refund_amount,
                reason=reason or "Customer requested refund",
                status=PaymentStatus.PENDING
            )
            
            # ✅ Initiate refund with corrected V2 client
            response = self.phonepe_client.initiate_refund(
                merchant_refund_id=refund.merchant_refund_id,
                original_merchant_order_id=payment.merchant_transaction_id,
                amount=refund_amount
            )
            
            if response.get('success'):
                refund.phonepe_refund_id = response.get('data', {}).get('refund_id')
                refund.gateway_response = response.get('data', {})
                refund.save()
                
                logger.info(f"Refund {refund.id} initiated successfully")
                return response
            else:
                refund.delete()  # Remove failed refund record
                raise PhonePeV2Exception(f"Refund initiation failed: {response.get('error')}")
                
        except Exception as e:
            logger.error(f"Refund initiation error: {str(e)}")
            raise
    
    def get_payment_methods(self):
        """Get available payment methods"""
        return [
            {
                'code': 'PHONEPE',
                'name': 'PhonePe',
                'description': 'Pay using PhonePe UPI, Cards, Net Banking',
                'icon': 'phonepe-icon.png',
                'min_amount': 10.00,
                'max_amount': 100000.00
            }
        ]
