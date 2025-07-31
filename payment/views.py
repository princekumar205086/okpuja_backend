"""
Clean Payment Views for PhonePe V2 Integration
Simplified and working implementation
"""
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
import logging
import json

from .models import Payment, Refund, PaymentMethod, PaymentStatus
from .serializers_v2 import (
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
from .services import PaymentService
from .phonepe_v2_corrected import PhonePeV2Exception
from cart.models import Cart
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.conf import settings

logger = logging.getLogger(__name__)

class PaymentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for payment operations following PhonePe V2 Standard Checkout
    """
    queryset = Payment.objects.select_related(
        'user', 'cart', 'booking'
    ).prefetch_related(
        'refunds'
    ).order_by('-created_at')
    
    permission_classes = [IsAuthenticated]
    filterset_fields = ['status', 'method']
    search_fields = ['transaction_id', 'merchant_transaction_id']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.payment_service = PaymentService()

    def get_serializer_class(self):
        if self.action == 'create':
            return PaymentCreateSerializer
        elif self.action == 'list':
            return PaymentListSerializer
        return PaymentDetailSerializer

    def get_queryset(self):
        if getattr(self, 'swagger_fake_view', False) or not self.request.user.is_authenticated:
            return self.queryset.none()
        
        # Users can only see their own payments
        if self.request.user.is_staff:
            return self.queryset
        return self.queryset.filter(user=self.request.user)

    @swagger_auto_schema(
        operation_description="Create payment from cart and initiate PhonePe checkout",
        responses={
            201: PaymentInitiationResponseSerializer,
            400: "Bad Request - Invalid cart or payment data"
        }
    )
    def create(self, request, *args, **kwargs):
        """Create payment from cart and initiate PhonePe V2 Standard Checkout"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                # Get cart
                cart_id = serializer.validated_data['cart_id']
                cart = get_object_or_404(Cart, id=cart_id, user=request.user, status='ACTIVE')
                
                logger.info(f"Creating payment for cart {cart_id} by user {request.user.id}")
                
                # Create payment from cart
                payment = self.payment_service.create_payment_from_cart(cart, request.user)
                
                # Initiate payment with PhonePe
                response = self.payment_service.initiate_payment(payment)
                
                if response.get('success'):
                    response_data = {
                        'success': True,
                        'payment_id': payment.id,
                        'merchant_transaction_id': payment.merchant_transaction_id,
                        'transaction_id': payment.transaction_id,
                        'amount': payment.amount,
                        'currency': payment.currency,
                        'payment_url': response.get('payment_url'),
                        'status': payment.status
                    }
                    
                    logger.info(f"Payment {payment.id} created and initiated successfully")
                    return Response(response_data, status=status.HTTP_201_CREATED)
                else:
                    logger.error(f"Payment initiation failed: {response.get('error')}")
                    return Response({
                        'error': 'Payment initiation failed',
                        'message': response.get('error', 'Unknown error'),
                        'payment_id': payment.id
                    }, status=status.HTTP_400_BAD_REQUEST)
                    
        except PhonePeV2Exception as e:
            logger.error(f"PhonePe error: {str(e)}")
            return Response({
                'error': 'Payment gateway error',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Payment creation error: {str(e)}")
            return Response({
                'error': 'Payment creation failed',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Verify payment status with PhonePe",
        responses={200: PaymentStatusResponseSerializer}
    )
    @action(detail=True, methods=['post'], url_path='verify')
    def verify_payment(self, request, pk=None):
        """Verify payment status with PhonePe"""
        payment = self.get_object()
        
        try:
            response = self.payment_service.verify_payment(payment.merchant_transaction_id)
            
            # Refresh payment from database
            payment.refresh_from_db()
            
            return Response({
                'success': response.get('success', False),
                'payment_id': payment.id,
                'status': payment.status,
                'merchant_transaction_id': payment.merchant_transaction_id,
                'verification_data': response.get('data', {})
            })
            
        except Exception as e:
            logger.error(f"Payment verification error: {str(e)}")
            return Response({
                'error': 'Verification failed',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Initiate refund for a payment",
        request_body=RefundRequestSerializer,
        responses={200: RefundResponseSerializer}
    )
    @action(detail=True, methods=['post'], url_path='refund')
    def initiate_refund(self, request, pk=None):
        """Initiate refund for a payment"""
        payment = self.get_object()
        serializer = RefundRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            amount = serializer.validated_data.get('amount')
            reason = serializer.validated_data.get('reason')
            
            response = self.payment_service.initiate_refund(payment, amount, reason)
            
            if response.get('success'):
                return Response({
                    'success': True,
                    'message': 'Refund initiated successfully',
                    'refund_id': response.get('refund_id'),
                    'payment_id': payment.id
                })
            else:
                return Response({
                    'error': 'Refund initiation failed',
                    'message': response.get('error')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Refund initiation error: {str(e)}")
            return Response({
                'error': 'Refund failed',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        operation_description="Get available payment methods",
        responses={200: "List of available payment methods"}
    )
    @action(detail=False, methods=['get'], url_path='methods')
    def payment_methods(self, request):
        """Get available payment methods"""
        methods = self.payment_service.get_payment_methods()
        return Response({
            'success': True,
            'methods': methods
        })

    @swagger_auto_schema(
        operation_description="Test connectivity to payment gateway",
        responses={200: "Connectivity test results"}
    )
    @action(detail=False, methods=['get'], url_path='test-connectivity', permission_classes=[])
    def test_connectivity(self, request):
        """Test connectivity to PhonePe API"""
        try:
            results = self.payment_service.phonepe_client.test_connectivity()
            return Response({
                'success': True,
                'connectivity_results': results
            })
        except Exception as e:
            return Response({
                'success': False,
                'error': str(e)
            })

    @swagger_auto_schema(
        operation_description="Get payment statistics for user",
        responses={200: "Payment statistics"}
    )
    @action(detail=False, methods=['get'], url_path='stats')
    def payment_stats(self, request):
        """Get payment statistics for the current user"""
        user_payments = self.get_queryset()
        
        stats = {
            'total_payments': user_payments.count(),
            'successful_payments': user_payments.filter(status=PaymentStatus.SUCCESS).count(),
            'failed_payments': user_payments.filter(status=PaymentStatus.FAILED).count(),
            'pending_payments': user_payments.filter(status=PaymentStatus.PENDING).count(),
            'total_amount': sum(p.amount for p in user_payments.filter(status=PaymentStatus.SUCCESS)),
        }
        
        return Response({
            'success': True,
            'stats': stats
        })


@method_decorator(csrf_exempt, name='dispatch')
class PaymentWebhookView(APIView):
    """
    Handle PhonePe V2 Standard Checkout webhook callbacks
    """
    permission_classes = []
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.payment_service = PaymentService()

    @swagger_auto_schema(
        operation_description="Handle PhonePe webhook callback",
        request_body=PaymentWebhookSerializer,
        responses={200: "Webhook processed successfully"}
    )
    def post(self, request, gateway_name, *args, **kwargs):
        """Handle PhonePe webhook POST callback"""
        if gateway_name.lower() != 'phonepe':
            return Response({
                'error': f'Unsupported gateway: {gateway_name}'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            logger.info(f"Received PhonePe webhook: {request.data}")
            
            # Process webhook with payment service
            response = self.payment_service.process_webhook(request.data)
            
            if response.get('success'):
                logger.info(f"Webhook processed successfully for payment {response.get('payment_id')}")
                return Response({
                    'success': True,
                    'message': 'Webhook processed successfully',
                    'payment_id': response.get('payment_id'),
                    'status': response.get('status')
                })
            else:
                logger.error(f"Webhook processing failed: {response.get('error')}")
                return Response({
                    'error': 'Webhook processing failed',
                    'message': response.get('error')
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Webhook error: {str(e)}")
            return Response({
                'error': 'Webhook processing error',
                'message': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def get(self, request, gateway_name, *args, **kwargs):
        """Handle PhonePe webhook GET callback (redirect)"""
        try:
            # Extract payment information from query parameters
            payment_id = request.GET.get('payment_id')
            merchant_transaction_id = request.GET.get('transaction_id')
            
            if not payment_id and not merchant_transaction_id:
                return Response({
                    'error': 'Missing payment information'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Verify payment status
            if merchant_transaction_id:
                response = self.payment_service.verify_payment(merchant_transaction_id)
            else:
                payment = get_object_or_404(Payment, id=payment_id)
                response = self.payment_service.verify_payment(payment.merchant_transaction_id)
            
            return Response({
                'success': True,
                'message': 'Payment status verified',
                'verification_result': response
            })
            
        except Exception as e:
            logger.error(f"Webhook GET error: {str(e)}")
            return Response({
                'error': 'Payment verification failed',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class WebhookDebugView(APIView):
    """Debug webhook for testing"""
    permission_classes = []
    
    def post(self, request):
        """Debug webhook endpoint"""
        logger.info(f"Debug webhook received: {request.data}")
        logger.info(f"Headers: {dict(request.headers)}")
        
        return Response({
            'success': True,
            'message': 'Debug webhook received',
            'data': request.data,
            'headers': dict(request.headers)
        })


class AdminPaymentViewSet(viewsets.ModelViewSet):
    """Admin view for managing all payments"""
    queryset = Payment.objects.select_related(
        'user', 'cart', 'booking'
    ).prefetch_related(
        'refunds'
    ).order_by('-created_at')
    
    permission_classes = [IsAdminUser]
    serializer_class = PaymentDetailSerializer
    filterset_fields = ['status', 'method', 'user']
    search_fields = ['transaction_id', 'merchant_transaction_id', 'user__email']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.payment_service = PaymentService()

    @action(detail=True, methods=['post'], url_path='force-verify')
    def force_verify_payment(self, request, pk=None):
        """Force verify payment status (Admin only)"""
        payment = self.get_object()
        
        try:
            response = self.payment_service.verify_payment(payment.merchant_transaction_id)
            payment.refresh_from_db()
            
            return Response({
                'success': True,
                'payment_id': payment.id,
                'old_status': payment.status,
                'new_status': payment.status,
                'verification_data': response
            })
            
        except Exception as e:
            logger.error(f"Force verification error: {str(e)}")
            return Response({
                'error': 'Force verification failed',
                'message': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='dashboard')
    def payment_dashboard(self, request):
        """Get payment dashboard statistics"""
        total_payments = self.queryset.count()
        successful_payments = self.queryset.filter(status=PaymentStatus.SUCCESS).count()
        failed_payments = self.queryset.filter(status=PaymentStatus.FAILED).count()
        pending_payments = self.queryset.filter(status=PaymentStatus.PENDING).count()
        
        total_revenue = sum(
            p.amount for p in self.queryset.filter(status=PaymentStatus.SUCCESS)
        )
        
        return Response({
            'success': True,
            'dashboard': {
                'total_payments': total_payments,
                'successful_payments': successful_payments,
                'failed_payments': failed_payments,
                'pending_payments': pending_payments,
                'total_revenue': total_revenue,
                'success_rate': (successful_payments / total_payments * 100) if total_payments > 0 else 0
            }
        })
