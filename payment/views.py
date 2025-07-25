from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from django.db import transaction
from django.utils import timezone
import logging
import json

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
        Create a new payment and initiate payment gateway process with enhanced error handling
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            with transaction.atomic():
                payment = serializer.save()
                
                logger.info(f"🎯 Starting payment creation for payment ID: {payment.id}")
                logger.info(f"💰 Amount: ₹{payment.amount}")
                logger.info(f"👤 User: {request.user.email} (ID: {request.user.id})")
                logger.info(f"🔗 Transaction ID: {payment.transaction_id}")
                
                # Enhanced PhonePe processing with comprehensive error handling
                try:
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
                        'payment_url': response.get('payment_url') or response.get('checkout_url'),
                        'status': payment.status
                    })
                    
                    logger.info(f"✅ Payment created and initiated successfully!")
                    
                    return Response(
                        response_serializer.data,
                        status=status.HTTP_201_CREATED
                    )
                    
                except Exception as gateway_error:
                    # Enhanced error categorization and response
                    error_str = str(gateway_error)
                    error_type = type(gateway_error).__name__
                    
                    logger.error(f"❌ PhonePe Gateway Error in create: {error_str}")
                    logger.error(f"🔍 Error Type: {error_type}")
                    
                    # Categorize the error for better user feedback
                    if '[Errno 111] Connection refused' in error_str:
                        error_category = 'CONNECTION_REFUSED'
                        user_message = 'Unable to connect to payment gateway. Our technical team has been notified.'
                        admin_message = 'PhonePe API connection refused - network connectivity issue detected.'
                    elif 'Timeout' in error_str or 'timeout' in error_str.lower():
                        error_category = 'TIMEOUT'
                        user_message = 'Payment gateway is temporarily slow. Please try again.'
                        admin_message = 'PhonePe API timeout - network latency issue.'
                    elif 'SSL' in error_str or 'ssl' in error_str.lower():
                        error_category = 'SSL_ERROR'
                        user_message = 'Secure connection error. Please try again.'
                        admin_message = 'SSL/TLS error connecting to PhonePe API.'
                    elif 'DNS' in error_str or 'Name or service not known' in error_str:
                        error_category = 'DNS_ERROR'
                        user_message = 'Unable to reach payment gateway. Please check your connection.'
                        admin_message = 'DNS resolution failed for PhonePe API.'
                    else:
                        error_category = 'UNKNOWN_ERROR'
                        user_message = 'Payment initiation failed. Please try again or contact support.'
                        admin_message = f'Unexpected payment error: {error_str}'
                    
                    # Detailed error response
                    error_response = {
                        'error': 'Payment initiation failed',
                        'error_category': error_category,
                        'user_message': user_message,
                        'payment_id': payment.id,
                        'transaction_id': payment.transaction_id,
                        'debug_info': {
                            'error_type': error_type,
                            'admin_message': admin_message,
                            'timestamp': timezone.now().isoformat()
                        }
                    }
                    
                    # In debug mode, add more debugging info
                    if settings.DEBUG:
                        error_response['debug_info']['full_error'] = error_str
                        error_response['debug_options'] = {
                            'simulate_payment_url': f'/api/payments/payments/{payment.id}/simulate-success/',
                            'debug_connectivity_url': '/api/payments/payments/debug-connectivity/',
                        }
                    
                    return Response(error_response, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"💥 Critical error in payment creation: {str(e)}")
            logger.error(f"🔍 Error Type: {type(e).__name__}")
            
            return Response({
                'error': 'Critical payment system error',
                'user_message': 'Unable to create payment. Please try again later.',
                'debug_info': {
                    'error_type': type(e).__name__,
                    'error_details': str(e),
                    'timestamp': timezone.now().isoformat()
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
        Process payment for cart items - main endpoint for payment-first flow with enhanced error handling
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
            
            # Validate cart total
            if cart.total_price <= 0:
                return Response(
                    {'error': f'Invalid cart total: ₹{cart.total_price}. Please check cart items and packages.'},
                    status=status.HTTP_400_BAD_REQUEST
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
                
                logger.info(f"🎯 Starting payment processing for cart {cart_id}")
                logger.info(f"💰 Amount: ₹{payment.amount}")
                logger.info(f"👤 User: {request.user.email} (ID: {request.user.id})")
                logger.info(f"🆔 Payment ID: {payment.id}")
                logger.info(f"🔗 Transaction ID: {payment.transaction_id}")
                
                # Enhanced PhonePe processing with comprehensive error handling
                try:
                    # Get PhonePe gateway
                    gateway = get_payment_gateway('phonepe')
                    
                    # Initiate payment with gateway
                    gateway_response = gateway.initiate_payment(payment)
                    
                    # Send payment initiated notification
                    send_payment_initiated_notification.delay(payment.id)
                    
                    logger.info(f"✅ Payment processed successfully!")
                    logger.info(f"🔗 Payment URL: {gateway_response.get('payment_url', 'N/A')}")
                    
                    return Response({
                        'success': True,
                        'payment_id': payment.id,
                        'transaction_id': payment.transaction_id,
                        'merchant_transaction_id': payment.merchant_transaction_id,
                        'amount': payment.amount,
                        'currency': payment.currency,
                        'payment_url': gateway_response.get('payment_url'),
                        'checkout_url': gateway_response.get('checkout_url'),
                        'status': payment.status,
                        'cart_id': cart.id,
                        'phonepe_transaction_id': gateway_response.get('phonepe_transaction_id'),
                        'message': 'Payment initiated successfully'
                    }, status=status.HTTP_201_CREATED)
                    
                except Exception as gateway_error:
                    # Enhanced error categorization and fallback handling
                    error_str = str(gateway_error)
                    error_type = type(gateway_error).__name__
                    
                    logger.error(f"❌ PhonePe Gateway Error: {error_str}")
                    logger.error(f"🔍 Error Type: {error_type}")
                    
                    # Categorize the error for better user feedback
                    if '[Errno 111] Connection refused' in error_str:
                        error_category = 'CONNECTION_REFUSED'
                        user_message = 'Unable to connect to payment gateway. Please try again in a few moments.'
                        admin_message = 'PhonePe API connection refused - check network connectivity, firewall rules, or contact hosting provider.'
                    elif 'Timeout' in error_str or 'timeout' in error_str.lower():
                        error_category = 'TIMEOUT'
                        user_message = 'Payment gateway is taking too long to respond. Please try again.'
                        admin_message = 'PhonePe API timeout - increase timeout settings or check network latency.'
                    elif 'SSL' in error_str or 'ssl' in error_str.lower():
                        error_category = 'SSL_ERROR'
                        user_message = 'Secure connection to payment gateway failed. Please try again.'
                        admin_message = 'SSL/TLS error connecting to PhonePe API - check certificates and SSL settings.'
                    elif 'DNS' in error_str or 'Name or service not known' in error_str:
                        error_category = 'DNS_ERROR'
                        user_message = 'Unable to reach payment gateway. Please check your internet connection.'
                        admin_message = 'DNS resolution failed for PhonePe API - check DNS settings.'
                    elif 'Invalid' in error_str or 'Bad Request' in error_str:
                        error_category = 'INVALID_REQUEST'
                        user_message = 'Payment request is invalid. Please try again or contact support.'
                        admin_message = f'Invalid payment request: {error_str}'
                    else:
                        error_category = 'UNKNOWN_ERROR'
                        user_message = 'Payment processing failed. Please try again or contact support.'
                        admin_message = f'Unknown payment error: {error_str}'
                    
                    # Log detailed error information for debugging
                    logger.error(f"🏷️  Error Category: {error_category}")
                    logger.error(f"👥 User Message: {user_message}")
                    logger.error(f"🔧 Admin Message: {admin_message}")
                    
                    # For development/testing: offer payment simulation option
                    response_data = {
                        'error': 'Payment processing failed',
                        'error_category': error_category,
                        'user_message': user_message,
                        'payment_id': payment.id,
                        'transaction_id': payment.transaction_id,
                        'cart_id': cart.id,
                        'debug_info': {
                            'error_type': error_type,
                            'error_details': error_str,
                            'admin_message': admin_message,
                            'timestamp': timezone.now().isoformat()
                        }
                    }
                    
                    # In debug mode, offer simulation endpoint
                    if settings.DEBUG:
                        response_data['debug_options'] = {
                            'simulate_payment_url': f'/api/payments/payments/{payment.id}/simulate-success/',
                            'debug_connectivity_url': '/api/payments/payments/debug-connectivity/',
                            'message': 'Development mode: Use simulate-success endpoint to complete payment for testing'
                        }
                    
                    return Response(response_data, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"💥 Critical error in cart payment processing: {str(e)}")
            logger.error(f"🔍 Error Type: {type(e).__name__}")
            
            return Response({
                'error': 'Critical payment system error',
                'user_message': 'Unable to process payment. Please try again later or contact support.',
                'debug_info': {
                    'error_type': type(e).__name__,
                    'error_details': str(e),
                    'timestamp': timezone.now().isoformat()
                }
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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
                
                # Create booking if cart exists and no booking exists yet
                booking = None
                if hasattr(payment, 'cart') and payment.cart and not hasattr(payment, 'booking'):
                    try:
                        # Try to create booking using payment model method if it exists
                        if hasattr(payment, 'create_booking_from_cart'):
                            booking = payment.create_booking_from_cart()
                            logger.info(f"Booking {booking.book_id} created via payment model method for payment {payment.transaction_id}")
                        else:
                            # Alternative: Create booking manually if method doesn't exist
                            from booking.models import Booking
                            booking = Booking.objects.create(
                                user=payment.user,
                                payment=payment,
                                # Add other required fields as needed based on your Booking model
                            )
                            logger.info(f"Booking {booking.id} created manually for payment {payment.transaction_id}")
                    except Exception as booking_error:
                        logger.error(f"Failed to create booking for payment {payment.transaction_id}: {str(booking_error)}")
                        # Don't fail the payment simulation if booking creation fails
                
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
                        'booking_reference': getattr(booking, 'book_id', booking.id)
                    })
                
                return Response(response_data, status=status.HTTP_200_OK)
                
        except Exception as e:
            logger.error(f"Payment simulation failed: {str(e)}")
            return Response(
                {'error': 'Payment simulation failed', 'details': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=['get', 'post'], url_path='debug-connectivity', permission_classes=[])
    def debug_connectivity(self, request):
        """
        Debug PhonePe connectivity from production server with comprehensive testing
        Use POST with {"test_payment": true} to test actual payment initiation
        """
        try:
            import requests
            import socket
            from urllib.parse import urlparse
            
            debug_info = {
                'timestamp': timezone.now().isoformat(),
                'server_info': {},
                'network_tests': {},
                'phonepe_config': {},
                'api_test': {},
                'payment_simulation': {}
            }
            
            # 1. Server information
            try:
                debug_info['server_info'] = {
                    'hostname': socket.gethostname(),
                    'fqdn': socket.getfqdn(),
                }
            except Exception as e:
                debug_info['server_info']['error'] = str(e)
            
            # 2. PhonePe configuration (mask sensitive data)
            debug_info['phonepe_config'] = {
                'merchant_id': getattr(settings, 'PHONEPE_MERCHANT_ID', 'NOT_SET')[:10] + '...' if getattr(settings, 'PHONEPE_MERCHANT_ID', None) else 'NOT_SET',
                'base_url': getattr(settings, 'PHONEPE_BASE_URL', 'NOT_SET'),
                'salt_index': getattr(settings, 'PHONEPE_SALT_INDEX', 'NOT_SET'),
                'timeout': getattr(settings, 'PHONEPE_TIMEOUT', 'NOT_SET'),
                'max_retries': getattr(settings, 'PHONEPE_MAX_RETRIES', 'NOT_SET'),
                'ssl_verify': getattr(settings, 'PHONEPE_SSL_VERIFY', 'NOT_SET'),
                'production_server': getattr(settings, 'PRODUCTION_SERVER', False),
            }
            
            # 3. Network connectivity tests
            test_urls = [
                'https://google.com',
                'https://api.phonepe.com',
                'https://api.phonepe.com/apis/hermes',
                'https://api-preprod.phonepe.com/apis/hermes',
                'https://httpbin.org/status/200'
            ]
            
            for url in test_urls:
                try:
                    parsed_url = urlparse(url)
                    
                    # Test DNS resolution
                    ip = socket.gethostbyname(parsed_url.hostname)
                    
                    # Test HTTP connectivity
                    get_response = requests.get(url, timeout=15, verify=True)
                    
                    debug_info['network_tests'][url] = {
                        'dns_ip': ip,
                        'status_code': get_response.status_code,
                        'reachable': True,
                        'response_time_ms': round(get_response.elapsed.total_seconds() * 1000, 2)
                    }
                    
                except Exception as e:
                    debug_info['network_tests'][url] = {
                        'error': str(e),
                        'error_type': type(e).__name__,
                        'reachable': False
                    }
            
            # 4. Test PhonePe gateway initialization
            try:
                from payment.gateways import PhonePeGateway
                gateway = PhonePeGateway()
                debug_info['api_test']['gateway_init'] = 'SUCCESS'
                debug_info['api_test']['gateway_config'] = {
                    'timeout': gateway.timeout,
                    'max_retries': gateway.max_retries,
                    'ssl_verify': gateway.ssl_verify,
                    'is_production': getattr(gateway, 'is_production', False)
                }
                
                # 5. Test payment simulation if POST request with test data
                if request.method == 'POST' and request.data.get('test_payment'):
                    try:
                        from payment.models import Payment, PaymentStatus
                        from django.contrib.auth import get_user_model
                        User = get_user_model()
                        
                        # Use the requesting user or get the first user
                        test_user = request.user if request.user.is_authenticated else User.objects.first()
                        
                        if test_user:
                            # Create mock payment data (don't save to database)
                            import uuid
                            test_payment_data = {
                                'user': test_user,
                                'amount': 10.00,  # Test with ₹10
                                'transaction_id': f"TEST_{uuid.uuid4().hex[:8].upper()}",
                                'merchant_transaction_id': f"MERCH_TEST_{uuid.uuid4().hex[:8].upper()}",
                                'status': PaymentStatus.PENDING
                            }
                            
                            # Mock payment object for testing
                            class MockPayment:
                                def __init__(self, data):
                                    for key, value in data.items():
                                        setattr(self, key, value)
                                    self.id = 999999  # Test ID
                                
                                def save(self):
                                    pass  # Don't actually save
                            
                            mock_payment = MockPayment(test_payment_data)
                            
                            # Test the payment initiation without saving
                            try:
                                result = gateway.initiate_payment(mock_payment)
                                debug_info['payment_simulation'] = {
                                    'status': 'SUCCESS',
                                    'payment_url': result.get('payment_url', 'N/A'),
                                    'test_amount': test_payment_data['amount'],
                                    'test_transaction_id': test_payment_data['transaction_id']
                                }
                            except Exception as payment_e:
                                debug_info['payment_simulation'] = {
                                    'status': 'FAILED',
                                    'error': str(payment_e),
                                    'error_type': type(payment_e).__name__,
                                    'test_amount': test_payment_data['amount'],
                                    'test_transaction_id': test_payment_data['transaction_id']
                                }
                        else:
                            debug_info['payment_simulation']['error'] = 'No user available for testing'
                    
                    except Exception as sim_e:
                        debug_info['payment_simulation'] = {
                            'status': 'ERROR',
                            'error': str(sim_e),
                            'error_type': type(sim_e).__name__
                        }
                
            except Exception as e:
                debug_info['api_test']['gateway_init'] = f'FAILED: {str(e)}'
                debug_info['api_test']['error_type'] = type(e).__name__
            
            # 6. Generate recommendations
            recommendations = []
            phonepe_reachable = any(
                test.get('reachable', False) 
                for url, test in debug_info['network_tests'].items() 
                if 'phonepe.com' in url
            )
            
            if phonepe_reachable:
                recommendations.append("✅ PhonePe API is reachable")
            else:
                recommendations.append("❌ PhonePe API is not reachable - check firewall/proxy settings")
            
            if debug_info['api_test'].get('gateway_init') == 'SUCCESS':
                recommendations.append("✅ PhonePe Gateway initialized successfully")
            else:
                recommendations.append("❌ PhonePe Gateway initialization failed - check configuration")
            
            # Check payment simulation results
            if 'payment_simulation' in debug_info:
                if debug_info['payment_simulation'].get('status') == 'SUCCESS':
                    recommendations.append("✅ Payment simulation successful - PhonePe integration working")
                elif debug_info['payment_simulation'].get('status') == 'FAILED':
                    error_type = debug_info['payment_simulation'].get('error_type', 'Unknown')
                    if 'Connection' in error_type:
                        recommendations.append("❌ Payment simulation failed due to connection issues")
                    else:
                        recommendations.append(f"❌ Payment simulation failed: {error_type}")
            
            debug_info['recommendations'] = recommendations
            debug_info['test_summary'] = {
                'total_endpoints_tested': len(debug_info['network_tests']),
                'reachable_endpoints': sum(1 for test in debug_info['network_tests'].values() if test.get('reachable', False)),
                'gateway_working': debug_info['api_test'].get('gateway_init') == 'SUCCESS'
            }
            
            return Response(debug_info, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({
                'error': 'Debug endpoint failed',
                'details': str(e),
                'type': type(e).__name__,
                'recommendations': [
                    "❌ Debug endpoint itself failed - check server logs",
                    "Try running basic connectivity tests manually"
                ]
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class PaymentWebhookView(APIView):
    """
    Handle payment gateway webhook callbacks with enhanced error handling
    """
    permission_classes = []  # Public endpoint for gateway callbacks

    def post(self, request, gateway_name):
        """
        Handle PhonePe webhook callback with enhanced error handling
        FIXED: Better handling of empty request bodies and JSON parsing
        """
        try:
            logger.info(f"🔔 Webhook received for gateway: {gateway_name}")
            logger.info(f"📋 Headers: {dict(request.headers)}")
            logger.info(f"📝 Raw body length: {len(request.body) if request.body else 0}")
            logger.info(f"📄 Content type: {request.content_type}")
            
            # Handle empty request body - FIXED
            if not request.body:
                logger.warning("⚠️ Empty webhook request body received")
                
                # For development/testing: return helpful message
                if settings.DEBUG:
                    return Response(
                        {
                            'error': 'Empty webhook request body',
                            'success': False,
                            'message': 'No data received in webhook callback',
                            'help': 'This usually means PhonePe is not sending data to the webhook. Check PhonePe dashboard configuration.',
                            'webhook_url': request.build_absolute_uri(),
                            'expected_format': {
                                'response': 'base64_encoded_response',
                                'merchantId': 'your_merchant_id',
                                'merchantTransactionId': 'transaction_id'
                            }
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                else:
                    # For production: simpler response
                    return Response(
                        {
                            'error': 'Empty webhook request body',
                            'success': False
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Get raw callback body as string
            try:
                callback_body_string = request.body.decode('utf-8')
                logger.info(f"✅ Decoded request body successfully: {len(callback_body_string)} characters")
                
                # FIXED: Handle empty string after decoding
                if not callback_body_string.strip():
                    logger.warning("⚠️ Empty webhook callback body after decoding")
                    return Response(
                        {
                            'error': 'Empty webhook callback body after decoding',
                            'success': False,
                            'message': 'Webhook body is empty after UTF-8 decoding',
                            'help': 'PhonePe might be sending empty data or wrong encoding'
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )
                
                # FIXED: Handle both JSON and URL-encoded data
                parsed_data = None
                
                # Try JSON first
                try:
                    parsed_data = json.loads(callback_body_string)
                    logger.info(f"✅ Valid JSON received with keys: {list(parsed_data.keys()) if isinstance(parsed_data, dict) else 'non-dict'}")
                except json.JSONDecodeError as json_err:
                    logger.warning(f"⚠️ Not JSON format, trying URL-encoded: {str(json_err)}")
                    
                    # Try URL-encoded form data (PhonePe sometimes sends this)
                    try:
                        from urllib.parse import parse_qs
                        
                        # Check if it looks like form data
                        if '=' in callback_body_string and '&' in callback_body_string:
                            form_data = parse_qs(callback_body_string)
                            # Convert single-item lists to strings
                            parsed_data = {k: v[0] if len(v) == 1 else v for k, v in form_data.items()}
                            logger.info(f"✅ URL-encoded data parsed with keys: {list(parsed_data.keys())}")
                        else:
                            # Not JSON or form data
                            logger.error(f"❌ Data is neither JSON nor URL-encoded form")
                            logger.error(f"📝 Raw body: {callback_body_string[:200]}...")
                            
                            return Response(
                                {
                                    'error': f'Invalid webhook body format: {str(json_err)}',
                                    'success': False,
                                    'json_error': str(json_err),
                                    'body_preview': callback_body_string[:100],
                                    'help': 'Webhook body must be JSON or URL-encoded form data. Check PhonePe webhook configuration.',
                                    'received_format': 'unknown'
                                },
                                status=status.HTTP_400_BAD_REQUEST
                            )
                    except Exception as parse_err:
                        logger.error(f"❌ Failed to parse as URL-encoded data: {str(parse_err)}")
                        
                        return Response(
                            {
                                'error': f'Unable to parse webhook body: {str(parse_err)}',
                                'success': False,
                                'json_error': str(json_err),
                                'parse_error': str(parse_err),
                                'body_preview': callback_body_string[:100],
                                'help': 'Check PhonePe webhook configuration and data format.'
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )
                    
            except UnicodeDecodeError as e:
                logger.error(f"❌ Failed to decode request body: {str(e)}")
                return Response(
                    {
                        'error': 'Invalid request body encoding',
                        'success': False,
                        'details': str(e),
                        'help': 'Request body is not UTF-8 encoded'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get authorization header (X-VERIFY from PhonePe)
            authorization_header = request.headers.get('X-VERIFY', '')
            if not authorization_header:
                # Try alternative header names
                authorization_header = (
                    request.headers.get('Authorization', '') or
                    request.headers.get('x-verify', '') or
                    request.headers.get('verify', '')
                )
                
                if not authorization_header:
                    logger.warning("⚠️ Missing X-VERIFY header")
                    if not settings.DEBUG:
                        return Response(
                            {
                                'error': 'Missing X-VERIFY header for webhook authentication',
                                'success': False,
                                'available_headers': list(request.headers.keys())
                            },
                            status=status.HTTP_401_UNAUTHORIZED
                        )
            
            # Process with PhonePe gateway
            try:
                gateway = get_payment_gateway(gateway_name)
                logger.info(f"✅ Got {gateway_name} gateway instance")
                
                # Pass parsed data to gateway - supports both JSON and form data
                if isinstance(parsed_data, dict):
                    # Convert parsed data back to JSON format for gateway processing
                    gateway_data = json.dumps(parsed_data)
                    logger.info(f"✅ Using parsed data for gateway processing")
                else:
                    # Fallback to original string
                    gateway_data = callback_body_string
                    logger.warning(f"⚠️ Using original string for gateway processing")
                
                payment = gateway.process_webhook(request.headers, gateway_data)
                logger.info(f"✅ Webhook processed successfully for payment {payment.id}")
                
                return Response(
                    {
                        'success': True,
                        'message': 'Webhook processed successfully',
                        'payment_id': payment.id,
                        'transaction_id': payment.transaction_id,
                        'merchant_transaction_id': payment.merchant_transaction_id,
                        'status': payment.status,
                        'data_format': 'json' if callback_body_string.strip().startswith('{') else 'form'
                    },
                    status=status.HTTP_200_OK
                )
                
            except Exception as gateway_error:
                logger.error(f"❌ Gateway processing failed: {str(gateway_error)}")
                logger.error(f"🔍 Gateway error type: {type(gateway_error).__name__}")
                
                return Response(
                    {
                        'error': f'Gateway processing failed: {str(gateway_error)}',
                        'success': False,
                        'gateway': gateway_name,
                        'error_type': type(gateway_error).__name__,
                        'help': 'Check payment exists and webhook data is valid'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
        except Exception as e:
            logger.error(f"💥 Critical webhook processing error: {str(e)}")
            logger.error(f"🔍 Error type: {type(e).__name__}")
            import traceback
            logger.error(f"📚 Traceback: {traceback.format_exc()}")
            
            return Response(
                {
                    'error': f'Webhook processing failed: {str(e)}',
                    'success': False,
                    'error_type': type(e).__name__
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    def get(self, request, gateway_name):
        """
        Handle GET requests to webhook endpoint (for testing)
        """
        return Response(
            {
                'message': f'Webhook endpoint for {gateway_name} is active',
                'method': 'GET',
                'expected_method': 'POST',
                'url': request.build_absolute_uri(),
                'timestamp': timezone.now().isoformat()
            },
            status=status.HTTP_200_OK
        )


class WebhookDebugView(APIView):
    """
    Debug endpoint to test webhook without processing
    URL: /api/payments/webhook/debug/
    """
    permission_classes = []  # Public endpoint for testing

    @swagger_auto_schema(
        operation_description="Get debug webhook endpoint information",
        responses={
            200: openapi.Response(description="Debug information returned")
        }
    )
    def get(self, request):
        """Get webhook debug information"""
        return Response({
            'message': 'PhonePe Webhook Debug Endpoint',
            'timestamp': timezone.now().isoformat(),
            'webhook_url': '/api/payments/webhook/phonepe/',
            'test_instructions': {
                'step1': 'POST to this endpoint with sample PhonePe webhook data',
                'step2': 'Check response and logs for debugging',
                'step3': 'Test actual webhook endpoint once debugging is complete'
            },
            'sample_request': {
                'method': 'POST',
                'headers': {
                    'Content-Type': 'application/json',
                    'X-VERIFY': 'signature_from_phonepe'
                },
                'body': {
                    'response': 'base64_encoded_phonepe_response',
                    'merchantId': 'your_merchant_id',
                    'merchantTransactionId': 'your_transaction_id'
                }
            }
        })

    @swagger_auto_schema(
        operation_description="Debug webhook endpoint for testing PhonePe webhook integration",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'response': openapi.Schema(type=openapi.TYPE_STRING, description='Base64 encoded response'),
                'merchantId': openapi.Schema(type=openapi.TYPE_STRING, description='Merchant ID'),
                'merchantTransactionId': openapi.Schema(type=openapi.TYPE_STRING, description='Transaction ID')
            }
        ),
        responses={
            200: openapi.Response(description="Debug information returned"),
            400: openapi.Response(description="Invalid request")
        }
    )
    def post(self, request):
        """Debug POST requests to webhook"""
        try:
            logger.info("🔍 DEBUG WEBHOOK TEST")
            logger.info(f"Headers: {dict(request.headers)}")
            logger.info(f"Body: {request.body}")
            logger.info(f"Content-Type: {request.content_type}")
            
            if not request.body:
                return Response({
                    'debug': 'empty_body',
                    'message': 'No request body received',
                    'help': 'PhonePe webhooks should include JSON body with response, merchantId, and merchantTransactionId',
                    'status': 'error'
                })
            
            try:
                body_str = request.body.decode('utf-8')
                parsed_json = json.loads(body_str)
                
                # Check for required PhonePe fields
                required_fields = ['response', 'merchantId', 'merchantTransactionId']
                missing_fields = [field for field in required_fields if field not in parsed_json]
                
                debug_info = {
                    'debug': 'success',
                    'message': 'Valid JSON received',
                    'body_length': len(body_str),
                    'json_keys': list(parsed_json.keys()) if isinstance(parsed_json, dict) else 'not_dict',
                    'has_required_fields': len(missing_fields) == 0,
                    'missing_fields': missing_fields,
                    'status': 'success' if len(missing_fields) == 0 else 'warning'
                }
                
                # Try to decode the response field if it exists
                if 'response' in parsed_json:
                    try:
                        import base64
                        decoded_response = json.loads(base64.b64decode(parsed_json['response']).decode('utf-8'))
                        debug_info['decoded_response_keys'] = list(decoded_response.keys()) if isinstance(decoded_response, dict) else 'not_dict'
                        debug_info['response_decode'] = 'success'
                    except Exception as decode_err:
                        debug_info['response_decode'] = f'failed: {str(decode_err)}'
                
                return Response(debug_info)
                
            except json.JSONDecodeError as e:
                return Response({
                    'debug': 'json_error',
                    'message': f'Invalid JSON: {str(e)}',
                    'body_preview': body_str[:100] if 'body_str' in locals() else 'decode_failed',
                    'status': 'error'
                })
                
        except Exception as e:
            return Response({
                'debug': 'error',
                'message': f'Debug failed: {str(e)}',
                'status': 'error'
            })


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