"""
PhonePe V2 Webhook Handler - Official Implementation
Handles all webhook events as per PhonePe V2 documentation
"""
import json
import logging
import hashlib
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .models import Payment, Refund, PaymentStatus
from .phonepe_v2_corrected import PhonePeV2ClientCorrected

logger = logging.getLogger(__name__)

class PhonePeV2WebhookView(APIView):
    """
    PhonePe V2 Webhook Handler
    Handles all webhook events as per official documentation:
    - checkout.order.completed
    - checkout.order.failed
    - pg.refund.accepted
    - pg.refund.completed
    - pg.refund.failed
    """
    
    def __init__(self):
        super().__init__()
        self.client = PhonePeV2ClientCorrected(env="sandbox")
        # ✅ Webhook credentials as per documentation
        self.webhook_username = getattr(settings, 'PHONEPE_WEBHOOK_USERNAME', 'webhook_user')
        self.webhook_password = getattr(settings, 'PHONEPE_WEBHOOK_PASSWORD', 'webhook_pass')
    
    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        """
        Handle PhonePe V2 webhook POST requests
        """
        try:
            # Step 1: Extract Authorization header
            auth_header = request.META.get('HTTP_AUTHORIZATION', '')
            logger.info(f"Webhook received with auth: {auth_header}")
            
            # Step 2: Validate authorization as per documentation
            # PhonePe sends: Authorization: SHA256(username:password)
            is_valid_auth = self.client.validate_webhook_authorization(
                auth_header, self.webhook_username, self.webhook_password
            )
            
            if not is_valid_auth:
                logger.warning(f"Invalid webhook authorization: {auth_header}")
                return Response({
                    'success': False,
                    'error': 'Invalid authorization'
                }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Step 3: Parse webhook payload
            try:
                payload = json.loads(request.body.decode('utf-8'))
                logger.info(f"Webhook payload: {json.dumps(payload, indent=2)}")
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON payload: {str(e)}")
                return Response({
                    'success': False,
                    'error': 'Invalid JSON payload'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Step 4: Process webhook using client
            webhook_info = self.client.process_webhook_payload(payload)
            
            if not webhook_info.get('valid'):
                logger.error(f"Invalid webhook payload: {webhook_info.get('error')}")
                return Response({
                    'success': False,
                    'error': 'Invalid webhook payload'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Step 5: Handle different webhook events
            event = webhook_info.get('event')
            state = webhook_info.get('state')
            
            logger.info(f"Processing webhook event: {event} with state: {state}")
            
            if event in ['checkout.order.completed', 'checkout.order.failed']:
                result = self._handle_payment_webhook(webhook_info)
            elif event in ['pg.refund.accepted', 'pg.refund.completed', 'pg.refund.failed']:
                result = self._handle_refund_webhook(webhook_info)
            else:
                logger.warning(f"Unknown webhook event: {event}")
                result = {'success': False, 'error': f'Unknown event: {event}'}
            
            # Step 6: Return response
            if result.get('success'):
                logger.info(f"Webhook processed successfully: {event}")
                return Response({
                    'success': True,
                    'message': 'Webhook processed successfully'
                }, status=status.HTTP_200_OK)
            else:
                logger.error(f"Webhook processing failed: {result.get('error')}")
                return Response({
                    'success': False,
                    'error': result.get('error', 'Processing failed')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Webhook handling error: {str(e)}")
            return Response({
                'success': False,
                'error': 'Internal server error'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _handle_payment_webhook(self, webhook_info):
        """
        Handle payment webhooks (order.completed/failed)
        ✅ Rely only on root level 'payload.state' as per documentation
        """
        try:
            merchant_order_id = webhook_info.get('merchant_order_id')
            state = webhook_info.get('state')  # ✅ Root level state
            
            if not merchant_order_id:
                return {'success': False, 'error': 'Missing merchant_order_id'}
            
            # Find payment by merchant transaction ID
            try:
                payment = Payment.objects.get(merchant_transaction_id=merchant_order_id)
            except Payment.DoesNotExist:
                logger.warning(f"Payment not found for merchant_order_id: {merchant_order_id}")
                return {'success': False, 'error': 'Payment not found'}
            
            # ✅ Update payment status based on root level state
            if state == 'COMPLETED':
                payment.status = PaymentStatus.COMPLETED
                payment.phonepe_order_id = webhook_info.get('order_id')
                logger.info(f"Payment {payment.id} marked as COMPLETED")
                
                # Process successful payment (create booking, etc.)
                self._process_successful_payment(payment, webhook_info)
                
            elif state == 'FAILED':
                payment.status = PaymentStatus.FAILED
                logger.info(f"Payment {payment.id} marked as FAILED")
                
                # Process failed payment
                self._process_failed_payment(payment, webhook_info)
            
            payment.save()
            
            return {'success': True, 'payment_updated': payment.id}
            
        except Exception as e:
            logger.error(f"Payment webhook handling error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _handle_refund_webhook(self, webhook_info):
        """
        Handle refund webhooks (refund.accepted/completed/failed)
        ✅ Rely only on root level 'payload.state' as per documentation
        """
        try:
            merchant_refund_id = webhook_info.get('merchant_refund_id')
            state = webhook_info.get('state')  # ✅ Root level state
            
            if not merchant_refund_id:
                return {'success': False, 'error': 'Missing merchant_refund_id'}
            
            # Find or create refund record
            try:
                refund = Refund.objects.get(merchant_refund_id=merchant_refund_id)
            except Refund.DoesNotExist:
                # Create refund record if not exists
                original_order_id = webhook_info.get('original_merchant_order_id')
                try:
                    payment = Payment.objects.get(merchant_transaction_id=original_order_id)
                    refund = Refund.objects.create(
                        payment=payment,
                        merchant_refund_id=merchant_refund_id,
                        phonepe_refund_id=webhook_info.get('refund_id'),
                        amount=webhook_info.get('amount', 0) / 100,  # Convert from paisa
                        status=PaymentStatus.PENDING
                    )
                except Payment.DoesNotExist:
                    logger.warning(f"Payment not found for refund: {original_order_id}")
                    return {'success': False, 'error': 'Original payment not found'}
            
            # ✅ Update refund status based on root level state
            if state == 'CONFIRMED':
                refund.status = PaymentStatus.SUCCESS
                logger.info(f"Refund {refund.id} marked as CONFIRMED")
                
            elif state == 'COMPLETED':
                refund.status = PaymentStatus.SUCCESS
                refund.phonepe_refund_id = webhook_info.get('refund_id')
                logger.info(f"Refund {refund.id} marked as COMPLETED")
                
                # Process successful refund
                self._process_successful_refund(refund, webhook_info)
                
            elif state == 'FAILED':
                refund.status = PaymentStatus.FAILED
                refund.error_code = webhook_info.get('error_code')
                refund.error_message = webhook_info.get('detailed_error_code')
                logger.info(f"Refund {refund.id} marked as FAILED")
                
                # Process failed refund
                self._process_failed_refund(refund, webhook_info)
            
            refund.save()
            
            return {'success': True, 'refund_updated': refund.id}
            
        except Exception as e:
            logger.error(f"Refund webhook handling error: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _process_successful_payment(self, payment, webhook_info):
        """Process successful payment (create booking, send notifications, etc.)"""
        try:
            # Create booking from cart if exists
            if hasattr(payment, 'cart') and payment.cart:
                from booking.models import Booking
                booking = Booking.objects.create(
                    user=payment.user,
                    cart=payment.cart,
                    payment=payment,
                    total_amount=payment.amount,
                    status='confirmed'
                )
                logger.info(f"Booking created: {booking.id} for payment: {payment.id}")
            
            # Send success notifications, emails, etc.
            # self._send_payment_success_notification(payment)
            
        except Exception as e:
            logger.error(f"Post-payment processing error: {str(e)}")
    
    def _process_failed_payment(self, payment, webhook_info):
        """Process failed payment (send notifications, etc.)"""
        try:
            # Send failure notifications
            # self._send_payment_failure_notification(payment)
            logger.info(f"Payment {payment.id} processing for failure completed")
            
        except Exception as e:
            logger.error(f"Failed payment processing error: {str(e)}")
    
    def _process_successful_refund(self, refund, webhook_info):
        """Process successful refund (update booking, send notifications, etc.)"""
        try:
            # Update related booking status if needed
            # Send refund success notifications
            logger.info(f"Refund {refund.id} processing for success completed")
            
        except Exception as e:
            logger.error(f"Successful refund processing error: {str(e)}")
    
    def _process_failed_refund(self, refund, webhook_info):
        """Process failed refund (send notifications, etc.)"""
        try:
            # Send refund failure notifications
            logger.info(f"Refund {refund.id} processing for failure completed")
            
        except Exception as e:
            logger.error(f"Failed refund processing error: {str(e)}")

# Function-based webhook view for simpler integration
@csrf_exempt
@require_http_methods(["POST"])
def phonepe_v2_webhook(request):
    """
    Simple function-based webhook handler
    """
    try:
        webhook_view = PhonePeV2WebhookView()
        return webhook_view.post(request)
    except Exception as e:
        logger.error(f"Webhook function error: {str(e)}")
        return JsonResponse({
            'success': False,
            'error': 'Internal server error'
        }, status=500)
