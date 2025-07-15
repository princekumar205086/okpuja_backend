import logging
from uuid import uuid4
from django.conf import settings
from django.urls import reverse
from django.utils import timezone
from phonepe.sdk.pg.payments.v2.standard_checkout_client import StandardCheckoutClient
from phonepe.sdk.pg.payments.v2.models.request.standard_checkout_pay_request import StandardCheckoutPayRequest
from phonepe.sdk.pg.env import Env

logger = logging.getLogger(__name__)

# Define a custom PhonePe exception if the official one is not available
class PhonePeException(Exception):
    """Custom PhonePe exception for error handling"""
    pass

logger = logging.getLogger(__name__)

class PhonePeGateway:
    def __init__(self):
        """Initialize PhonePe Gateway with latest SDK"""
        self.client_id = settings.PHONEPE_CLIENT_ID
        self.client_secret = settings.PHONEPE_CLIENT_SECRET
        self.client_version = settings.PHONEPE_CLIENT_VERSION
        
        # Set environment (UAT for testing, PRODUCTION for live)
        self.env = Env.SANDBOX if settings.PHONEPE_ENV == 'UAT' else Env.PRODUCTION
        
        # Initialize the PhonePe client
        self.client = StandardCheckoutClient.get_instance(
            client_id=self.client_id,
            client_secret=self.client_secret,
            client_version=self.client_version,
            env=self.env
        )
        
        self.callback_username = settings.PHONEPE_CALLBACK_USERNAME
        self.callback_password = settings.PHONEPE_CALLBACK_PASSWORD

    def initiate_payment(self, payment):
        """
        Initiate payment using PhonePe's latest SDK
        
        Args:
            payment: Payment model instance
            
        Returns:
            dict: Response containing checkout URL and payment details
        """
        try:
            # Use merchant_transaction_id as unique order ID
            unique_order_id = payment.merchant_transaction_id
            
            # Amount in paise (multiply by 100 as PhonePe expects paise)
            amount_in_paise = int(payment.amount * 100)
            
            # Set redirect URL (where user goes after payment)
            ui_redirect_url = payment.redirect_url or settings.PHONEPE_SUCCESS_REDIRECT_URL
            
            # Build the payment request
            standard_pay_request = StandardCheckoutPayRequest.build_request(
                merchant_order_id=unique_order_id,
                amount=amount_in_paise,
                redirect_url=ui_redirect_url
            )
            
            # Initiate payment
            standard_pay_response = self.client.pay(standard_pay_request)
            
            # Extract checkout URL
            checkout_page_url = standard_pay_response.redirect_url
            
            # Update payment with PhonePe response
            payment.gateway_response = {
                'checkout_url': checkout_page_url,
                'merchant_order_id': unique_order_id,
                'amount': amount_in_paise,
                'redirect_url': ui_redirect_url,
                'response_data': standard_pay_response.__dict__ if hasattr(standard_pay_response, '__dict__') else str(standard_pay_response)
            }
            payment.save()
            
            logger.info(f"PhonePe payment initiated successfully for order: {unique_order_id}")
            
            return {
                'success': True,
                'checkout_url': checkout_page_url,
                'merchant_order_id': unique_order_id,
                'amount': payment.amount,
                'currency': payment.currency
            }
            
        except PhonePeException as e:
            logger.error(f"PhonePe payment initiation failed: {str(e)}")
            raise Exception(f"PhonePe payment failed: {str(e)}")
        except Exception as e:
            logger.error(f"Payment initiation error: {str(e)}")
            raise Exception(f"Payment initiation failed: {str(e)}")

    def check_payment_status(self, merchant_order_id):
        """
        Check payment status using PhonePe's latest SDK
        
        Args:
            merchant_order_id: Unique order identifier
            
        Returns:
            dict: Payment status response
        """
        try:
            # Get order status from PhonePe
            order_status_response = self.client.get_order_status(merchant_order_id=merchant_order_id)
            
            # Extract order state
            order_state = order_status_response.state
            
            logger.info(f"PhonePe status check for order {merchant_order_id}: {order_state}")
            
            return {
                'success': True,
                'status': order_state,
                'merchant_order_id': merchant_order_id,
                'response_data': order_status_response.__dict__ if hasattr(order_status_response, '__dict__') else str(order_status_response)
            }
            
        except PhonePeException as e:
            logger.error(f"PhonePe status check failed: {str(e)}")
            raise Exception(f"Status check failed: {str(e)}")
        except Exception as e:
            logger.error(f"Status check error: {str(e)}")
            raise Exception(f"Status check failed: {str(e)}")

    def process_webhook(self, authorization_header, callback_body_string):
        """
        Process PhonePe webhook callback using latest SDK
        
        Args:
            authorization_header: Authorization header from PhonePe
            callback_body_string: Raw callback body as string
            
        Returns:
            Payment: Updated payment object
        """
        from .models import Payment, PaymentStatus
        
        try:
            # Validate callback using PhonePe SDK
            callback_response = self.client.validate_callback(
                username=self.callback_username,
                password=self.callback_password,
                callback_header_data=authorization_header,
                callback_response_data=callback_body_string
            )
            
            # Extract order details
            order_id = callback_response.order_id
            state = callback_response.state
            
            # Find payment by merchant_transaction_id
            try:
                payment = Payment.objects.get(merchant_transaction_id=order_id)
            except Payment.DoesNotExist:
                logger.error(f"Payment not found for order ID: {order_id}")
                raise Exception(f"Payment not found for order ID: {order_id}")
            
            # Map PhonePe states to our payment statuses
            status_mapping = {
                'CHECKOUT_ORDER_COMPLETED': PaymentStatus.SUCCESS,
                'CHECKOUT_ORDER_FAILED': PaymentStatus.FAILED,
                'CHECKOUT_TRANSACTION_ATTEMPT_FAILED': PaymentStatus.FAILED,
            }
            
            # Update payment status
            old_status = payment.status
            payment.status = status_mapping.get(state, PaymentStatus.PENDING)
            
            # Update gateway response with callback data
            payment.gateway_response = payment.gateway_response or {}
            payment.gateway_response.update({
                'webhook_callback': {
                    'order_id': order_id,
                    'state': state,
                    'callback_response': callback_response.__dict__ if hasattr(callback_response, '__dict__') else str(callback_response),
                    'timestamp': str(timezone.now())
                }
            })
            
            payment.save()
            
            # Create booking if payment is successful and no booking exists yet
            if payment.status == PaymentStatus.SUCCESS and not payment.booking:
                try:
                    booking = payment.create_booking_from_cart()
                    logger.info(f"Booking {booking.book_id} created successfully for payment {payment.transaction_id}")
                except Exception as e:
                    logger.error(f"Failed to create booking from payment {payment.transaction_id}: {str(e)}")
            
            # Send notification if status changed
            if old_status != payment.status:
                payment.send_notification()
            
            logger.info(f"PhonePe webhook processed successfully for order: {order_id}, status: {state}")
            
            return payment
            
        except PhonePeException as e:
            logger.error(f"PhonePe webhook validation failed: {str(e)}")
            raise Exception(f"Invalid webhook callback: {str(e)}")
        except Exception as e:
            logger.error(f"Webhook processing failed: {str(e)}")
            raise Exception(f"Webhook processing failed: {str(e)}")

    def initiate_refund(self, refund):
        """
        Initiate refund using PhonePe (if supported by SDK)
        Note: Check PhonePe documentation for refund API availability
        
        Args:
            refund: Refund model instance
            
        Returns:
            dict: Refund response
        """
        # Note: As of the current SDK documentation, refund functionality 
        # might need to be implemented separately or through PhonePe's merchant dashboard
        logger.warning("Refund functionality needs to be implemented based on PhonePe's refund API")
        
        return {
            'success': False,
            'message': 'Refund needs to be processed through PhonePe merchant dashboard',
            'refund_id': refund.refund_id
        }


def get_payment_gateway(name='phonepe'):
    """
    Factory function to get payment gateway instance
    
    Args:
        name: Gateway name (default: 'phonepe')
        
    Returns:
        Gateway instance
    """
    gateways = {
        'phonepe': PhonePeGateway,
    }
    
    gateway_class = gateways.get(name.lower())
    if not gateway_class:
        raise ValueError(f"Unsupported payment gateway: {name}")
    
    return gateway_class()