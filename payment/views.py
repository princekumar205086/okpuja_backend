from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
import logging

from .models import Payment, Refund, PaymentMethod, PaymentStatus
from .serializers import (
    PaymentCreateSerializer,
    PaymentDetailSerializer,
    PaymentListSerializer,
    RefundRequestSerializer,
    RefundDetailSerializer,
    PaymentInitiationResponseSerializer,
    PaymentStatusResponseSerializer,
    RefundResponseSerializer,
    PaymentWebhookSerializer
)
from .gateways import get_payment_gateway
from core.tasks import (
    send_payment_initiated_notification,
    send_payment_status_notification,
    send_refund_initiated_notification
)
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.conf import settings

logger = logging.getLogger(__name__)

class PaymentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for payment operations
    """
    queryset = Payment.objects.select_related(
        'booking', 'booking__user'
    ).prefetch_related(
        'refunds'
    ).order_by('-created_at')
    
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'method']
    search_fields = ['transaction_id', 'merchant_transaction_id', 'booking__book_id']

    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentCreateSerializer
        elif self.action == 'list':
            return PaymentListSerializer
        return PaymentDetailSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return self.queryset.none()
        return self.queryset.filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Create a new payment and initiate payment gateway process
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                payment = serializer.save()
                
                # Get PhonePe gateway
                gateway = get_payment_gateway('phonepe')
                
                # Initiate payment with gateway
                response = gateway.initiate_payment(payment)
                
                # Send payment initiated notification
                send_payment_initiated_notification.delay(payment.id)
                
                # Prepare response
                response_serializer = PaymentInitiationResponseSerializer({
                    'success': True,
                    'payment_id': payment.id,
                    'merchant_transaction_id': payment.merchant_transaction_id,
                    'transaction_id': payment.transaction_id,
                    'amount': payment.amount,
                    'currency': payment.currency,
                    'payment_url': response.get('checkout_url'),
                    'status': payment.status
                })
                
                return Response(
                    response_serializer.data,
                    status=status.HTTP_201_CREATED
                )
                
        except Exception as e:
            logger.error(f"Payment initiation failed: {str(e)}")
            return Response(
                {'error': 'Payment initiation failed', 'details': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'])
    def status(self, request, pk=None):
        """
        Check current payment status with payment gateway
        """
        payment = self.get_object()
        
        try:
            gateway = get_payment_gateway('phonepe')
            status_response = gateway.check_payment_status(payment.merchant_transaction_id)
            
            # Update payment status if changed
            new_status = status_response.get('status')
            if new_status and new_status != payment.status:
                status_mapping = {
                    'CHECKOUT_ORDER_COMPLETED': PaymentStatus.SUCCESS,
                    'CHECKOUT_ORDER_FAILED': PaymentStatus.FAILED,
                    'CHECKOUT_TRANSACTION_ATTEMPT_FAILED': PaymentStatus.FAILED,
                }
                payment.status = status_mapping.get(new_status, payment.status)
                payment.gateway_response = payment.gateway_response or {}
                payment.gateway_response.update({'status_check': status_response})
                payment.save()
                send_payment_status_notification.delay(payment.id)
            
            response_serializer = PaymentStatusResponseSerializer({
                'success': True,
                'code': 'STATUS_CHECKED',
                'message': 'Payment status checked successfully',
                'transaction_id': payment.transaction_id,
                'merchant_transaction_id': payment.merchant_transaction_id,
                'amount': payment.amount,
                'currency': payment.currency,
                'status': payment.status,
                'payment_method': payment.method
            })
            
            return Response(response_serializer.data)
            
        except Exception as e:
            logger.error(f"Payment status check failed: {str(e)}")
            return Response(
                {'error': 'Status check failed', 'details': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['post'])
    def refund(self, request, pk=None):
        """
        Initiate a refund for this payment
        """
        payment = self.get_object()
        
        if not payment.is_refundable:
            return Response(
                {'error': 'Payment is not refundable'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = RefundRequestSerializer(
            data=request.data,
            context={'payment': payment}
        )
        serializer.is_valid(raise_exception=True)
        
        try:
            with transaction.atomic():
                # Create refund record
                refund = Refund.objects.create(
                    payment=payment,
                    amount=serializer.validated_data['amount'],
                    reason=serializer.validated_data['reason'],
                    notes=serializer.validated_data.get('notes'),
                    processed_by=request.user if request.user.is_staff else None
                )
                
                # Process refund through gateway
                gateway = get_payment_gateway(payment.method.lower())
                if hasattr(gateway, 'initiate_refund'):
                    refund_response = gateway.initiate_refund(
                        payment.merchant_transaction_id,
                        refund.amount
                    )
                    refund.gateway_response = refund_response
                    refund.status = PaymentStatus.SUCCESS
                    refund.save()
                
                # Send notification
                send_refund_initiated_notification.delay(refund.id)
                
                # Prepare response
                response_serializer = RefundResponseSerializer({
                    'success': True,
                    'refund_id': refund.refund_id,
                    'payment_id': payment.id,
                    'amount': refund.amount,
                    'status': refund.status
                })
                
                return Response(
                    response_serializer.data,
                    status=status.HTTP_201_CREATED
                )
                
        except Exception as e:
            logger.error(f"Refund initiation failed: {str(e)}")
            return Response(
                {'error': 'Refund initiation failed', 'details': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['post'], url_path='process-cart')
    def process_cart_payment(self, request):
        """
        Process payment for cart items - main endpoint for payment-first flow
        Request: { "cart_id": 123, "method": "PHONEPE" }
        Response: { "success": True, "payment_url": "...", "payment_id": 456 }
        """
        from cart.models import Cart
        
        try:
            cart_id = request.data.get('cart_id')
            if not cart_id:
                return Response(
                    {'error': 'cart_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate cart
            try:
                cart = Cart.objects.get(
                    id=cart_id,
                    user=request.user,
                    status='ACTIVE'
                )
            except Cart.DoesNotExist:
                return Response(
                    {'error': 'Active cart not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Create payment data
            payment_data = {
                'cart_id': cart_id,
                'amount': cart.total_price,
                'method': request.data.get('method', 'PHONEPE'),
                'currency': 'INR'
            }
            
            # Create payment using serializer
            serializer = PaymentCreateSerializer(
                data=payment_data,
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            
            with transaction.atomic():
                payment = serializer.save()
                
                # Get PhonePe gateway
                gateway = get_payment_gateway('phonepe')
                
                # Initiate payment with gateway
                gateway_response = gateway.initiate_payment(payment)
                
                # Send payment initiated notification
                send_payment_initiated_notification.delay(payment.id)
                
                return Response({
                    'success': True,
                    'payment_id': payment.id,
                    'transaction_id': payment.transaction_id,
                    'merchant_transaction_id': payment.merchant_transaction_id,
                    'amount': payment.amount,
                    'currency': payment.currency,
                    'payment_url': gateway_response.get('checkout_url'),
                    'status': payment.status,
                    'cart_id': cart.id
                }, status=status.HTTP_201_CREATED)
                
        except Exception as e:
            logger.error(f"Cart payment processing failed: {str(e)}")
            return Response(
                {'error': 'Payment processing failed', 'details': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=True, methods=['get'], url_path='check-booking')
    def check_booking_status(self, request, pk=None):
        """
        Check if payment has resulted in booking creation
        Returns booking details if payment was successful and booking created
        """
        payment = self.get_object()
        
        if payment.status == PaymentStatus.SUCCESS and payment.booking:
            from booking.serializers import BookingSerializer
            booking_serializer = BookingSerializer(payment.booking)
            return Response({
                'success': True,
                'payment_status': payment.status,
                'booking_created': True,
                'booking': booking_serializer.data
            })
        elif payment.status == PaymentStatus.SUCCESS and not payment.booking:
            return Response({
                'success': True,
                'payment_status': payment.status,
                'booking_created': False,
                'message': 'Payment successful but booking creation pending'
            })
        else:
            return Response({
                'success': False,
                'payment_status': payment.status,
                'booking_created': False,
                'message': f'Payment status: {payment.get_status_display()}'
            })

    @action(detail=True, methods=['post'], url_path='simulate-success')
    def simulate_payment_success(self, request, pk=None):
        """
        DEVELOPMENT ONLY: Simulate payment success to test booking creation
        This endpoint manually marks payment as successful and creates booking
        """
        from django.conf import settings
        
        # Only allow in development/debug mode
        if not settings.DEBUG:
            return Response(
                {'error': 'This endpoint is only available in development mode'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        payment = self.get_object()
        
        if payment.status != PaymentStatus.PENDING:
            return Response(
                {'error': f'Payment status is {payment.status}, can only simulate success for PENDING payments'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            with transaction.atomic():
                # Update payment status to SUCCESS
                old_status = payment.status
                payment.status = PaymentStatus.SUCCESS
                
                # Add simulation info to gateway response
                payment.gateway_response = payment.gateway_response or {}
                payment.gateway_response.update({
                    'simulation': {
                        'simulated_at': str(timezone.now()),
                        'simulated_by': request.user.email,
                        'note': 'Payment success simulated for development testing'
                    }
                })
                payment.save()
                
                # Create booking if no booking exists yet
                booking = None
                if not payment.booking:
                    booking = payment.create_booking_from_cart()
                    logger.info(f"Booking {booking.book_id} created via simulation for payment {payment.transaction_id}")
                
                # Send notifications
                if old_status != payment.status:
                    send_payment_status_notification.delay(payment.id)
                
                response_data = {
                    'success': True,
                    'message': 'Payment success simulated successfully',
                    'payment_id': payment.id,
                    'transaction_id': payment.transaction_id,
                    'status': payment.status,
                    'booking_created': booking is not None
                }
                
                if booking:
                    response_data.update({
                        'booking_id': booking.id,
                        'booking_reference': booking.book_id
                    })
                
                return Response(response_data, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Payment simulation failed: {str(e)}")
            return Response(
                {'error': 'Payment simulation failed', 'details': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

class PaymentWebhookView(APIView):
    """
    Handle payment gateway webhook callbacks
    """
    permission_classes = []  # Public endpoint for gateway callbacks

    def post(self, request, gateway_name):
        """
        Handle PhonePe webhook callback
        """
        try:
            # Get authorization header
            authorization_header = request.headers.get('Authorization', '')
            
            # Get raw callback body as string
            callback_body_string = request.body.decode('utf-8')
            
            # Process with PhonePe gateway
            gateway = get_payment_gateway(gateway_name)
            payment = gateway.process_webhook(authorization_header, callback_body_string)
            
            return Response(
                {
                    'success': True,
                    'message': 'Webhook processed successfully',
                    'payment_id': payment.id,
                    'status': payment.status
                },
                status=status.HTTP_200_OK
            )
            
        except Exception as e:
            logger.error(f"Webhook processing failed: {str(e)}")
            return Response(
                {'error': str(e), 'success': False},
                status=status.HTTP_400_BAD_REQUEST
            )

class AdminPaymentViewSet(viewsets.ModelViewSet):
    """
    Admin API endpoint for payment operations
    """
    queryset = Payment.objects.select_related(
        'booking', 'booking__user'
    ).prefetch_related(
        'refunds'
    ).order_by('-created_at')
    
    serializer_class = PaymentDetailSerializer
    permission_classes = [IsAdminUser]
    filterset_fields = ['status', 'method', 'booking__user']
    search_fields = ['transaction_id', 'merchant_transaction_id', 'booking__book_id']

    @action(detail=True, methods=['post'])
    def capture(self, request, pk=None):
        """
        Manually capture a pending payment (admin only)
        """
        payment = self.get_object()
        
        if payment.status != PaymentStatus.PENDING:
            return Response(
                {'error': 'Only pending payments can be captured'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment.status = PaymentStatus.SUCCESS
        payment.save()
        send_payment_status_notification.delay(payment.id)
        
        return Response(
            PaymentDetailSerializer(payment).data,
            status=status.HTTP_200_OK
        )

    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """
        Manually cancel a payment (admin only)
        """
        payment = self.get_object()
        
        if payment.status not in [PaymentStatus.PENDING, PaymentStatus.SUCCESS]:
            return Response(
                {'error': 'Only pending or successful payments can be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        payment.status = PaymentStatus.CANCELLED
        payment.save()
        send_payment_status_notification.delay(payment.id)
        
        return Response(
            PaymentDetailSerializer(payment).data,
            status=status.HTTP_200_OK
        )